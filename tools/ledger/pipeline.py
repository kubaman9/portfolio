#!/usr/bin/env python3
"""The ledger pipeline: the bookkeeping half of the betting agent, run by
.github/workflows/ledger-pipeline.yml so the daily Claude run spends its time on
picks instead of arithmetic.

  MONGODB_URI=... python3 tools/ledger/pipeline.py grade close audit summary
  MONGODB_URI=... python3 tools/ledger/pipeline.py prekick   (needs SHARPAPI_KEY)

grade    OPEN picks whose games are final -> result, units, legs, final_score,
         written to picks AND to that day's dashboard_days entry.
close    ESPN closing line + CLV for graded single game-level picks with clv null.
audit    re-grade picks graded in the last 7 days; disagreements go to grade_audit
         (the daily run must apply them) -- nothing graded is silently rewritten.
summary  exact record/units/CLV/calibration plus the anchor-vs-model Brier test,
         written to ledger_summary/current for the run and the dashboard.
prekick  near-kickoff prices for open player props from SharpAPI (props have no
         ESPN close), saved as odds_snapshots kind "pre_kick".

Every write is tagged graded_by/clv_source "pipeline" so the run can tell them apart.
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from espn import norm, find_event, competitors, event_state  # noqa: E402
from grade import grade_pick, closing_for, parse, event_for_key  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)
ISO = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
FIRST_LIVE_DAY = "2026-08-31"  # first day of the ledger; everything since is counted


def log(*a):
    print(*a, flush=True)


def connect():
    from pymongo import MongoClient
    uri = (os.environ.get("MONGODB_URI") or "").strip().strip('"').strip("'")
    if not uri.startswith(("mongodb+srv://", "mongodb://")):
        log("PIPELINE REFUSED: MONGODB_URI missing or not a connection string")
        sys.exit(1)
    try:
        db = MongoClient(uri, serverSelectionTimeoutMS=20000)["betting_agent"]
        db.command("ping")
        return db
    except Exception as e:
        log(f"PIPELINE REFUSED: cannot reach Mongo ({type(e).__name__})")
        sys.exit(1)


# ---------------------------------------------------------------- dashboard write-back
def _words(s):
    return [w for w in norm(s).split() if len(w) > 1 or w.isdigit()]


def write_back(db, pick, upd):
    """Mirror a pick's grade into dashboard_days/<date> (picks[] or slips[])."""
    day = db.dashboard_days.find_one({"_id": pick.get("date")}, {"picks": 1, "slips": 1})
    if not day:
        return False
    changed = False
    if pick.get("legs"):
        want = [w for leg in pick["legs"] for w in _words(re.sub(r"\(.*?\)", "", leg.get("selection", "")))]
        for s in day.get("slips") or []:
            hay = set(_words(re.sub(r"\(.*?\)", " ", (s.get("legs") or "") + " " + (s.get("shape") or ""))))
            if want and all(w in hay for w in want):
                s["result"], s["units"] = upd["result"], upd["units"]
                if "clv" in upd:
                    s["clv"] = upd["clv"]
                for ld in s.get("legs_detail") or []:
                    for leg in upd.get("legs", []):
                        if set(_words(leg.get("selection"))) <= set(_words(ld.get("selection"))):
                            ld["status"] = leg.get("status")
                changed = True
                break
    else:
        for p in day.get("picks") or []:
            if norm(p.get("bet")) == norm(pick.get("bet")):
                p["result"], p["units"] = upd["result"], upd["units"]
                for k in ("final_score", "clv", "close"):
                    if k in upd:
                        p[k] = upd[k]
                changed = True
    if changed:
        db.dashboard_days.update_one({"_id": day["_id"]}, {"$set": {"picks": day.get("picks") or [], "slips": day.get("slips") or []}})
    return changed


# ---------------------------------------------------------------- steps
def step_grade(db):
    n = g = 0
    for p in db.picks.find({"result": "OPEN", "date": {"$gte": FIRST_LIVE_DAY, "$lt": NOW.date().isoformat()}}):
        n += 1
        try:
            upd = grade_pick(p)
        except Exception as e:
            log(f"  grade error on {p.get('bet')!r}: {type(e).__name__}: {e}")
            continue
        if not upd:
            continue
        upd.pop("_espn", None)
        if "result" in upd:
            upd.update({"graded_by": "pipeline", "graded_at": ISO, "updated_at": ISO})
            g += 1
            log(f"  graded {p['date']} {p.get('bet')!r}: {upd['result']} {upd['units']:+}u")
        db.picks.update_one({"_id": p["_id"]}, {"$set": upd})
        if "result" in upd:
            write_back(db, p, upd)
    # today's games that already finished (early kickoffs) too
    for p in db.picks.find({"result": "OPEN", "date": NOW.date().isoformat()}):
        try:
            upd = grade_pick(p)
        except Exception:
            continue
        if upd and "result" in upd:
            upd.pop("_espn", None)
            upd.update({"graded_by": "pipeline", "graded_at": ISO, "updated_at": ISO})
            db.picks.update_one({"_id": p["_id"]}, {"$set": upd})
            write_back(db, p, upd)
            g += 1
            log(f"  graded {p['date']} {p.get('bet')!r}: {upd['result']} {upd['units']:+}u")
    log(f"grade: {g} graded of {n} open past-dated picks")


def step_close(db):
    done = 0
    q = {"result": {"$in": ["WIN", "LOSS", "PUSH"]}, "clv": None, "legs": {"$exists": False},
         "date": {"$gte": (NOW - dt.timedelta(days=10)).date().isoformat()}}
    for p in db.picks.find(q):
        spec = parse(p.get("bet"), None, p.get("bet_type"), p.get("sport"))
        if not spec or spec["kind"] == "prop":
            continue
        found = find_event(p.get("sport"), p.get("date"), p.get("matchup"))
        if not found:
            continue
        sk, lg, ev = found
        try:
            upd = closing_for(p, sk, lg, ev["id"], competitors(ev))
        except Exception as e:
            log(f"  close error on {p.get('bet')!r}: {type(e).__name__}")
            continue
        if not upd:
            continue
        upd["updated_at"] = ISO
        db.picks.update_one({"_id": p["_id"]}, {"$set": upd})
        db.odds_snapshots.insert_one({"captured_at": ISO, "kind": "close", "game_key": p.get("game_key"),
                                      "market": spec["kind"], "selection": p.get("bet"),
                                      "point": upd.get("closing_point"), "book": "draftkings",
                                      "source": "espn_core_pipeline", "note": upd.get("closing_line")})
        if "clv" in upd:
            write_back(db, p, {"result": p["result"], "units": p["units"], "clv": upd["clv"], "close": upd.get("closing_line")})
        done += 1
        log(f"  close {p['date']} {p.get('bet')!r}: {upd.get('closing_line')} clv={upd.get('clv')}")
    # Parlays: CLV = product of leg multipliers, only when EVERY leg has a comparable close
    q = {"result": {"$in": ["WIN", "LOSS", "PUSH"]}, "clv": None, "legs.0": {"$exists": True},
         "date": {"$gte": (NOW - dt.timedelta(days=10)).date().isoformat()}}
    for p in db.picks.find(q):
        if (p.get("clv_note") or "").startswith("pipeline:"):
            continue  # already tried; closes do not appear later
        mult, ok, notes = 1.0, 0, []
        for leg in p["legs"]:
            mk = norm(leg.get("market") or "")
            if not any(w in mk for w in ("spread", "total", "moneyline", "run line", "run_line")):
                notes.append("prop/other leg")
                continue
            found = event_for_key(p.get("sport"), leg.get("game_key"), leg.get("selection"))
            dec = leg.get("price_decimal")
            if not found or not dec:
                notes.append("leg event not found")
                continue
            bt = "Moneyline" if "moneyline" in mk else ("Total Under" if "under" in norm(leg.get("selection")) else "Total Over") if "total" in mk else "Spread"
            pseudo = {"bet": leg.get("selection"), "bet_type": bt, "sport": p.get("sport"), "price_decimal": dec}
            try:
                u = closing_for(pseudo, found[0], found[1], found[2]["id"], competitors(found[2]))
            except Exception:
                u = None
            if u and "clv" in u:
                mult *= 1 + u["clv"] / 100
                ok += 1
            else:
                notes.append("point moved or no close")
        n = len(p["legs"])
        if ok == n:
            upd = {"clv": round((mult - 1) * 100, 2), "clv_source": "espn_core_pipeline (product of legs)", "updated_at": ISO}
            write_back(db, p, {"result": p["result"], "units": p["units"], "clv": upd["clv"]})
            log(f"  parlay clv {p['date']} {p.get('bet')!r}: {upd['clv']}%")
        else:
            upd = {"clv_note": f"pipeline: {ok} of {n} legs have a comparable close ({'; '.join(sorted(set(notes)))})", "updated_at": ISO}
        db.picks.update_one({"_id": p["_id"]}, {"$set": upd})


def step_audit(db):
    since = (NOW - dt.timedelta(days=7)).date().isoformat()
    found = 0
    for p in db.picks.find({"result": {"$in": ["WIN", "LOSS", "PUSH"]}, "date": {"$gte": since},
                            "graded_by": {"$ne": "pipeline"}, "audit_ok": {"$ne": True}}):
        probe = dict(p)
        probe["result"] = "OPEN"
        if probe.get("legs"):
            probe["legs"] = [dict(l, status="OPEN") for l in probe["legs"]]
        try:
            upd = grade_pick(probe)
        except Exception:
            continue
        if not upd or "result" not in upd:
            continue
        if upd["result"] == p["result"]:
            db.picks.update_one({"_id": p["_id"]}, {"$set": {"audit_ok": True}})
            continue
        found += 1
        doc = {"pick_id": p["_id"], "date": p.get("date"), "bet": p.get("bet"),
               "ledger_result": p["result"], "ledger_units": p.get("units"),
               "espn_result": upd["result"], "espn_units": upd["units"],
               "evidence": upd.get("final_score") or upd.get("grade_note"),
               "legs": upd.get("legs"), "status": "open", "found_at": ISO}
        db.grade_audit.update_one({"pick_id": p["_id"]}, {"$setOnInsert": doc}, upsert=True)
        log(f"  AUDIT {p['date']} {p.get('bet')!r}: ledger {p['result']} vs ESPN {upd['result']}")
    log(f"audit: {found} disagreements written to grade_audit")


def wilson(w, n, z=1.96):
    if not n:
        return None, None
    p = w / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5
    return round(100 * (c - m) / d, 1), round(100 * (c + m) / d, 1)


def flags_for(groups):
    """Segment gates the daily run reads (playbook module auto_gates). Tighten-only:
    'tighten' when even the optimistic end of the hit-rate interval is below the
    break-even the segment's prices require; 'watch' when CLV says the prices were
    bad; 'strength' is informational and never loosens anything."""
    out = []
    for gname, segs in groups.items():
        for k, x in segs.items():
            n = x["W"] + x["L"]
            if x.get("be") is not None and n >= 25 and x["wilson_hi"] is not None and x["wilson_hi"] < x["be"]:
                out.append({"flag": "tighten", "segment": f"{gname}:{k}", "n": n, "record": f"{x['W']}-{x['L']}",
                            "units": x["units"], "hit_ci": [x["wilson_lo"], x["wilson_hi"]], "breakeven": x["be"],
                            "why": f"best case {x['wilson_hi']}% < break-even {x['be']}%"})
            elif x.get("n_clv", 0) >= 10 and x.get("mean_clv") is not None and x["mean_clv"] <= -1.0:
                out.append({"flag": "watch", "segment": f"{gname}:{k}", "n": n, "record": f"{x['W']}-{x['L']}",
                            "units": x["units"], "mean_clv": x["mean_clv"], "why": f"mean CLV {x['mean_clv']}% on {x['n_clv']} priced rows"})
            elif x.get("n_clv", 0) >= 15 and (x.get("mean_clv") or 0) >= 1.0 and x["beat_close"] / x["n_clv"] >= 0.55:
                out.append({"flag": "strength", "segment": f"{gname}:{k}", "n": n, "record": f"{x['W']}-{x['L']}",
                            "units": x["units"], "mean_clv": x["mean_clv"], "why": "beats the close consistently"})
    order = {"tighten": 0, "watch": 1, "strength": 2}
    return sorted(out, key=lambda f: (order[f["flag"]], -f["n"]))


def _band(conf):
    if conf is None:
        return None
    return "<50%" if conf < 50 else "50-54%" if conf < 55 else "55-59%" if conf < 60 else "60%+"


def step_summary(db):
    rows = list(db.picks.find({"date": {"$gte": FIRST_LIVE_DAY}}, {
        "date": 1, "sport": 1, "bet_type": 1, "result": 1, "units": 1, "stake_units": 1, "clv": 1,
        "confidence": 1, "anchor_prob": 1, "model_prob": 1, "legs": 1, "slip_type": 1, "tags": 1,
        "anchor_quality": 1, "thesis_quality": 1, "ev_pct": 1, "price_decimal": 1}))
    graded = [r for r in rows if r.get("result") in ("WIN", "LOSS", "PUSH")]

    def seg(items):
        W = sum(r["result"] == "WIN" for r in items)
        L = sum(r["result"] == "LOSS" for r in items)
        P = sum(r["result"] == "PUSH" for r in items)
        u = round(sum(r.get("units") or 0 for r in items), 3)
        st = sum(r.get("stake_units") or (-(r.get("units") or 0) if r["result"] == "LOSS" else 0.5) for r in items)
        clvs = [r["clv"] for r in items if isinstance(r.get("clv"), (int, float))]
        decs = [r["price_decimal"] for r in items if isinstance(r.get("price_decimal"), (int, float)) and r["price_decimal"] > 1]
        lo, hi = wilson(W, W + L)
        return {"W": W, "L": L, "P": P, "units": u, "hit": round(100 * W / (W + L), 1) if W + L else None,
                "wilson_lo": lo, "wilson_hi": hi, "be": round(100 * sum(1 / d for d in decs) / len(decs), 1) if decs else None,
                "roi": round(100 * u / st, 1) if st else None, "n_clv": len(clvs),
                "mean_clv": round(sum(clvs) / len(clvs), 2) if clvs else None,
                "beat_close": sum(c > 0 for c in clvs)}

    def by(key):
        out = {}
        for r in graded:
            k = key(r)
            if k:
                out.setdefault(k, []).append(r)
        return {k: seg(v) for k, v in sorted(out.items())}

    singles = [r for r in graded if not r.get("legs")]
    # Does the model's adjustment beat the market anchor it started from?
    bt = [r for r in singles if r["result"] in ("WIN", "LOSS") and isinstance(r.get("anchor_prob"), (int, float))
          and isinstance(r.get("model_prob"), (int, float))]

    def brier(items):
        if not items:
            return None
        a = sum((r["anchor_prob"] - (r["result"] == "WIN")) ** 2 for r in items) / len(items)
        m = sum((r["model_prob"] - (r["result"] == "WIN")) ** 2 for r in items) / len(items)
        return {"n": len(items), "brier_anchor": round(a, 4), "brier_model": round(m, 4),
                "verdict": "adjustments helped" if m < a else "adjustments hurt" if m > a else "no difference",
                "mean_adjustment_pts": round(100 * sum(r["model_prob"] - r["anchor_prob"] for r in items) / len(items), 2)}

    by_sport_bt = {}
    for r in bt:
        by_sport_bt.setdefault(r.get("sport") or "?", []).append(r)
    stated = [r for r in singles if r["result"] in ("WIN", "LOSS") and isinstance(r.get("confidence"), (int, float))]
    doc = {
        "_id": "current", "updated_at": ISO, "basis": f"picks dated {FIRST_LIVE_DAY} onward, graded rows",
        "overall": seg(graded), "singles": seg(singles), "parlays": seg([r for r in graded if r.get("legs")]),
        "by_sport": by(lambda r: r.get("sport")), "by_bet_type": by(lambda r: r.get("bet_type")),
        "by_slip_type": by(lambda r: r.get("slip_type") if r.get("legs") else None),
        "by_conf_band": by(lambda r: _band(r.get("confidence")) if not r.get("legs") else None),
        "by_anchor_quality": by(lambda r: r.get("anchor_quality")),
        "by_thesis_quality": by(lambda r: r.get("thesis_quality")),
        "calibration": {"n": len(stated),
                        "stated_mean": round(sum(r["confidence"] for r in stated) / len(stated), 1) if stated else None,
                        "hit_rate": round(100 * sum(r["result"] == "WIN" for r in stated) / len(stated), 1) if stated else None},
        "adjustment_test": {"all": brier(bt), "by_sport": {k: brier(v) for k, v in by_sport_bt.items()}},
        "clv_coverage": {"graded": len(graded), "with_clv": sum(isinstance(r.get("clv"), (int, float)) for r in graded)},
        "open": {"tickets": sum(r.get("result") == "OPEN" for r in rows),
                 "units_at_risk": round(sum(r.get("stake_units") or 0 for r in rows if r.get("result") == "OPEN"), 2)},
        "open_audits": db.grade_audit.count_documents({"status": "open"}),
    }
    tag_groups = {}
    for r in graded:
        for t in set(r.get("tags") or []):
            tag_groups.setdefault(str(t).lower(), []).append(r)
    doc["by_tag"] = {k: seg(v) for k, v in sorted(tag_groups.items()) if len(v) >= 5}
    sport_type = by(lambda r: f"{r.get('sport')}/{r.get('bet_type')}" if not r.get("legs") else None)
    doc["by_sport_bet_type"] = sport_type
    doc["flags"] = flags_for({"sport": doc["by_sport"], "bet_type": doc["by_bet_type"], "slip_type": doc["by_slip_type"],
                              "conf_band": doc["by_conf_band"], "sport_bet_type": sport_type, "tag": doc["by_tag"],
                              "structure": {"singles": doc["singles"], "parlays": doc["parlays"]}})
    db.ledger_summary.replace_one({"_id": "current"}, doc, upsert=True)
    db.ledger_summary.replace_one({"_id": NOW.date().isoformat()}, dict(doc, _id=NOW.date().isoformat()), upsert=True)
    o = doc["overall"]
    log(f"summary: {o['W']}-{o['L']}-{o['P']} {o['units']:+}u, adjustment test {doc['adjustment_test']['all']}")


# ---------------------------------------------------------------- SharpAPI pre-kick (props)
def sharp_get(path, key):
    req = urllib.request.Request("https://api.sharpapi.io/api/v1" + path,
                                 headers={"X-API-Key": key, "User-Agent": "curl/8.5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        remaining = r.headers.get("x-ratelimit-remaining")
        body = json.loads(r.read().decode("utf-8"))
    if remaining is not None and int(remaining) <= 1:
        time.sleep(6)
    return body


def step_prekick(db):
    key = os.environ.get("SHARPAPI_KEY")
    if not key:
        log("prekick: SHARPAPI_KEY not set, skipped")
        return
    horizon = NOW + dt.timedelta(minutes=75)
    open_rows = list(db.picks.find({"result": "OPEN", "date": {"$gte": (NOW - dt.timedelta(days=1)).date().isoformat()}}))
    calls = saved = 0
    for p in open_rows:
        legs = p.get("legs") or [{"game_key": p.get("game_key"), "market": p.get("bet_type"), "selection": p.get("bet")}]
        for leg in legs:
            spec = parse(leg.get("selection"), leg.get("market"), p.get("bet_type") if not p.get("legs") else None, p.get("sport"))
            if not spec or spec["kind"] != "prop":
                continue
            snap = db.odds_snapshots.find_one({"game_key": leg.get("game_key"), "selection": {"$regex": re.escape(spec["player"])},
                                               "source": {"$regex": "event_id="}}, sort=[("captured_at", -1)])
            m = re.search(r"event_id=([\w\-]+)", (snap or {}).get("source", ""))
            mk = re.search(r"market_type=(\w+)", (snap or {}).get("source", ""))
            if not m or not mk:
                continue
            ev = event_for_key(p.get("sport"), leg.get("game_key"), p.get("matchup"))
            if not ev:
                continue
            start = dt.datetime.fromisoformat(event_state(ev[2])["start"].replace("Z", "+00:00"))
            if not (NOW <= start <= horizon):
                continue  # only spend a SharpAPI call inside the last 75 minutes before kickoff
            recent = db.odds_snapshots.find_one({"game_key": leg.get("game_key"), "kind": "pre_kick", "selection": leg.get("selection"),
                                                 "captured_at": {"$gte": (NOW - dt.timedelta(minutes=50)).strftime("%Y-%m-%dT%H:%M:%SZ")}})
            if recent:
                continue
            try:
                calls += 1
                data = sharp_get(f"/odds?event_id={m.group(1)}&market_type={mk.group(1)}", key)
            except (urllib.error.URLError, ValueError) as e:
                log(f"  sharpapi error: {type(e).__name__}")
                continue
            rows = data.get("data") if isinstance(data, dict) else data
            best = None
            for r in rows or []:
                start = r.get("event_start_time")
                if start and dt.datetime.fromisoformat(start.replace("Z", "+00:00")) > horizon:
                    best = "later"
                    break
                if not r.get("is_player_prop") or r.get("is_live") or r.get("is_active") is False:
                    continue
                who = norm(r.get("player_name") or r.get("selection") or "")
                if norm(spec["player"]) not in who:
                    continue
                if r.get("line") is not None and float(r["line"]) != spec["line"]:
                    continue
                side = norm(r.get("selection_type") or r.get("selection") or "")
                if spec["side"] not in side:
                    continue
                if best is None or (r.get("sportsbook") or "").lower() == "draftkings":
                    best = r
            if best in (None, "later"):
                continue
            db.odds_snapshots.insert_one({"captured_at": ISO, "kind": "pre_kick", "game_key": leg.get("game_key"),
                                          "market": mk.group(1), "selection": leg.get("selection"), "point": spec["line"],
                                          "book": best.get("sportsbook"), "price_american": best.get("odds_american"),
                                          "price_decimal": best.get("odds_decimal"), "source": f"sharpapi pipeline event_id={m.group(1)}"})
            saved += 1
    db.api_budget.update_one({"_id": f"sharpapi:{NOW.strftime('%Y-%m')}"},
                             {"$inc": {"pipeline_calls": calls}, "$set": {"last_checked": ISO}}, upsert=True)
    log(f"prekick: {saved} prop prices saved, {calls} SharpAPI calls")


def step_enrich(db):
    """Fill dashboard fields the run left empty from the pick documents it wrote:
    wrong_if (stored on picks as falsifier) and line_gap_thesis / reasoning."""
    since = (NOW - dt.timedelta(days=21)).date().isoformat()
    filled = 0
    for day in db.dashboard_days.find({"_id": {"$gte": since}}, {"picks": 1}):
        picks = day.get("picks") or []
        need = [p for p in picks if not p.get("wrong_if") or not (p.get("line_gap_thesis") or p.get("why"))]
        if not need:
            continue
        src = {norm(x.get("bet")): x for x in db.picks.find({"date": day["_id"]}, {"bet": 1, "falsifier": 1, "wrong_if": 1, "line_gap_thesis": 1, "reasoning": 1})}
        changed = False
        for p in need:
            x = src.get(norm(p.get("bet")))
            if not x:
                continue
            w = x.get("wrong_if") or x.get("falsifier")
            if w and not p.get("wrong_if"):
                p["wrong_if"] = w
                changed = True
                filled += 1
            t = x.get("line_gap_thesis") or x.get("reasoning")
            if t and not (p.get("line_gap_thesis") or p.get("why")):
                p["line_gap_thesis"] = t
                changed = True
        if changed:
            db.dashboard_days.update_one({"_id": day["_id"]}, {"$set": {"picks": picks}})
    log(f"enrich: {filled} missing wrong_if filled from the pick documents")


STEPS = {"enrich": step_enrich, "grade": step_grade, "close": step_close, "audit": step_audit, "summary": step_summary, "prekick": step_prekick}


def main():
    steps = sys.argv[1:] or ["grade", "close", "audit", "enrich", "summary"]
    bad = [s for s in steps if s not in STEPS]
    if bad:
        log(f"unknown step(s): {bad}; choose from {list(STEPS)}")
        sys.exit(2)
    db = connect()
    for s in steps:
        t = time.time()
        try:
            STEPS[s](db)
        except Exception as e:  # one failed step must not stop the others
            log(f"{s}: FAILED {type(e).__name__}: {e}")
        log(f"  ({s} took {time.time() - t:.1f}s)")
    db.source_health.update_one({"_id": "ledger_pipeline"}, {"$set": {"last_run": ISO, "steps": steps}}, upsert=True)


if __name__ == "__main__":
    main()

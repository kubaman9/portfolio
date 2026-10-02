#!/usr/bin/env python3
"""The ledger pipeline: the bookkeeping half of the betting agent, run by
.github/workflows/ledger-pipeline.yml so the daily Claude run spends its time on
picks instead of arithmetic.

  MONGODB_URI=... python3 tools/ledger/pipeline.py grade sync close audit enrich summary
  MONGODB_URI=... python3 tools/ledger/pipeline.py --watch-until 07:20 grade sync ...
  MONGODB_URI=... python3 tools/ledger/pipeline.py prekick   (needs SHARPAPI_KEY)

grade    OPEN picks whose games are final -> result, units, legs, final_score,
         written to picks AND to that day's dashboard_days entry.
sync     grades the daily run wrote to picks itself -> that day's dashboard_days rows.
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
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from espn import norm, find_event, competitors, event_state  # noqa: E402
from grade import grade_pick, closing_for, parse, event_for_key, fair_prob, xev_pct, price_decimal  # noqa: E402

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

    def put(row, k, v):
        nonlocal changed
        if row.get(k) != v:
            row[k] = v
            changed = True

    if pick.get("legs"):
        want = [w for leg in pick["legs"] for w in _words(re.sub(r"\(.*?\)", "", leg.get("selection", "")))]
        for s in day.get("slips") or []:
            hay = set(_words(re.sub(r"\(.*?\)", " ", (s.get("legs") or "") + " " + (s.get("shape") or ""))))
            if want and all(w in hay for w in want):
                put(s, "result", upd["result"])
                put(s, "units", upd["units"])
                if "clv" in upd:
                    put(s, "clv", upd["clv"])
                for ld in s.get("legs_detail") or []:
                    for leg in upd.get("legs", []):
                        if set(_words(leg.get("selection"))) <= set(_words(ld.get("selection"))):
                            put(ld, "status", leg.get("status"))
                break
    else:
        for p in day.get("picks") or []:
            if norm(p.get("bet")) == norm(pick.get("bet")):
                put(p, "result", upd["result"])
                put(p, "units", upd["units"])
                for k in ("final_score", "clv", "close"):
                    if k in upd:
                        put(p, k, upd[k])
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


def step_sync(db):
    """Mirror grades the daily run wrote to picks (graded_by agent_*) into that day's
    dashboard_days rows, so a day's own page and the history never show a settled
    ticket as OPEN. write_back only writes when a value actually differs."""
    since = (NOW - dt.timedelta(days=21)).date().isoformat()
    n = 0
    for p in db.picks.find({"result": {"$in": ["WIN", "LOSS", "PUSH"]}, "date": {"$gte": since}}):
        upd = {"result": p["result"], "units": p.get("units")}
        for k in ("final_score", "clv", "legs"):
            if p.get(k) is not None:
                upd[k] = p[k]
        if p.get("closing_line"):
            upd["close"] = p["closing_line"]
        if write_back(db, p, upd):
            n += 1
            log(f"  synced {p['date']} {p.get('bet')!r}: {p['result']}")
    log(f"sync: {n} dashboard rows updated from graded picks")


def prekick_close(db, game_key, selection, spec, dec_pick):
    """CLV and fair-price EV for a player prop from the last pre-kick price (props have
    no ESPN close). Only comparable when the line is unchanged."""
    snap = db.odds_snapshots.find_one({"kind": "pre_kick", "game_key": game_key, "selection": selection},
                                      sort=[("captured_at", -1)])
    if not snap or not snap.get("price_decimal") or not dec_pick:
        return None
    if snap.get("point") is not None and float(snap["point"]) != spec["line"]:
        return {"note": f"prop line moved to {snap['point']}"}
    out = {"clv": round((float(dec_pick) / float(snap["price_decimal"]) - 1) * 100, 2),
           "close": f"{selection} {snap.get('price_american')} ({snap.get('book')} pre-kick, SharpAPI)"}
    fair = fair_prob(snap["price_decimal"], [snap.get("other_price_decimal")])
    if fair is not None:
        out["fair"] = round(fair, 4)
        out["xev"] = xev_pct(dec_pick, fair)
    return out


def step_close(db):
    """Closing line, CLV and fair-price EV (xev) for graded picks. Each pick is tried
    once (xev_tried); picks that already carry a run-written CLV keep it and only gain
    the fair-price fields."""
    done = 0
    since = (NOW - dt.timedelta(days=30)).date().isoformat()
    q = {"result": {"$in": ["WIN", "LOSS", "PUSH"]}, "legs": {"$exists": False}, "xev_tried": {"$ne": True},
         "date": {"$gte": since}}
    for p in db.picks.find(q):
        spec = parse(p.get("bet"), None, p.get("bet_type"), p.get("sport"))
        upd = None
        if spec and spec["kind"] == "prop":
            c = prekick_close(db, p.get("game_key"), p.get("bet"), spec, price_decimal(p))
            if c and "clv" in c:
                upd = {"closing_line": c["close"], "clv_source": "sharpapi_prekick_pipeline"}
                if p.get("clv") is None:
                    upd["clv"] = c["clv"]
                if "xev" in c:
                    upd.update({"close_fair_prob": c["fair"], "xev": c["xev"]})
            elif c is None and p.get("date", "") >= (NOW - dt.timedelta(days=2)).date().isoformat():
                continue  # a pre-kick price may still be saved for a late game: try again later
        elif spec:
            found = find_event(p.get("sport"), p.get("date"), p.get("matchup")) or \
                event_for_key(p.get("sport"), p.get("game_key"), p.get("bet"))
            if found:
                sk, lg, ev = found
                try:
                    upd = closing_for(p, sk, lg, ev["id"], competitors(ev))
                except Exception as e:
                    log(f"  close error on {p.get('bet')!r}: {type(e).__name__}")
                    continue
                if upd and p.get("clv") is not None:  # keep the run's own CLV and close
                    for k in ("clv", "closing_line", "clv_source", "closing_point"):
                        upd.pop(k, None)
        upd = dict(upd or {}, xev_tried=True, updated_at=ISO)
        db.picks.update_one({"_id": p["_id"]}, {"$set": upd})
        if "closing_line" in upd and spec and spec["kind"] != "prop":
            db.odds_snapshots.insert_one({"captured_at": ISO, "kind": "close", "game_key": p.get("game_key"),
                                          "market": spec["kind"], "selection": p.get("bet"),
                                          "point": upd.get("closing_point"), "book": "draftkings",
                                          "source": "espn_core_pipeline", "note": upd.get("closing_line")})
        if "clv" in upd:
            write_back(db, p, {"result": p["result"], "units": p["units"], "clv": upd["clv"], "close": upd.get("closing_line")})
        if "clv" in upd or "xev" in upd:
            done += 1
            log(f"  close {p['date']} {p.get('bet')!r}: clv={upd.get('clv', p.get('clv'))} xev={upd.get('xev')}")
    # Parlays: CLV = product of leg multipliers, only when EVERY leg has a comparable close.
    # xev = parlay price x product of the legs' fair probabilities - 1 (independent legs, so
    # not computed for same-game parlays, whose legs are correlated by design).
    q = {"result": {"$in": ["WIN", "LOSS", "PUSH"]}, "legs.0": {"$exists": True}, "xev_tried": {"$ne": True},
         "date": {"$gte": since}}
    for p in db.picks.find(q):
        try:
            done += close_parlay(db, p)
        except Exception as e:  # one odd row must not stop the rest
            log(f"  parlay close error on {p.get('bet')!r}: {type(e).__name__}: {e}")
            db.picks.update_one({"_id": p["_id"]}, {"$set": {"xev_tried": True}})
    log(f"close: {done} picks priced against the close")


def close_parlay(db, p):
    """One parlay against the close; returns 1 when it was handled."""
    since2 = (NOW - dt.timedelta(days=2)).date().isoformat()
    mult, fair_all, ok, notes = 1.0, 1.0, 0, []
    for leg in p["legs"]:
        mk = norm(leg.get("market") or "")
        dec = leg.get("price_decimal") or (leg.get("price_american") and price_decimal(leg))
        spec = parse(leg.get("selection"), leg.get("market"), None, p.get("sport"))
        u = None
        if spec and spec["kind"] == "prop":
            c = prekick_close(db, leg.get("game_key"), leg.get("selection"), spec, dec)
            u = {"clv": c["clv"], "fair": c.get("fair")} if c and "clv" in c else None
            if not u:
                notes.append("prop leg without a pre-kick price")
        elif any(w in mk for w in ("spread", "total", "moneyline", "run line", "run_line")):
            found = event_for_key(p.get("sport"), leg.get("game_key"), leg.get("selection"))
            if found and dec:
                bt = "Moneyline" if "moneyline" in mk else ("Total Under" if "under" in norm(leg.get("selection")) else "Total Over") if "total" in mk else "Spread"
                pseudo = {"bet": leg.get("selection"), "bet_type": bt, "sport": p.get("sport"), "price_decimal": dec}
                try:
                    c = closing_for(pseudo, found[0], found[1], found[2]["id"], competitors(found[2]))
                except Exception:
                    c = None
                u = {"clv": c["clv"], "fair": c.get("close_fair_prob")} if c and "clv" in c else None
                if not u:
                    notes.append("point moved or no close")
            else:
                notes.append("leg event not found")
        else:
            notes.append("other leg")
        if u:
            mult *= 1 + u["clv"] / 100
            fair_all = fair_all * u["fair"] if (u.get("fair") and fair_all is not None) else None
            ok += 1
    n = len(p["legs"])
    upd = {"xev_tried": True, "updated_at": ISO}
    if ok == n:
        if p.get("clv") is None:
            upd.update({"clv": round((mult - 1) * 100, 2), "clv_source": "espn_core_pipeline (product of legs)"})
        if fair_all is not None and p.get("slip_type") != "sgp" and price_decimal(p):
            upd.update({"close_fair_prob": round(fair_all, 4), "xev": xev_pct(price_decimal(p), fair_all)})
        if "clv" in upd:
            write_back(db, p, {"result": p["result"], "units": p["units"], "clv": upd["clv"]})
        log(f"  parlay close {p['date']} {p.get('bet')!r}: clv={upd.get('clv', p.get('clv'))} xev={upd.get('xev')}")
    else:
        upd["clv_note"] = f"pipeline: {ok} of {n} legs have a comparable close ({'; '.join(sorted(set(notes)))})"
        if any("pre-kick" in x for x in notes) and p.get("date", "") >= since2:
            upd.pop("xev_tried")  # a pre-kick price may still land; retry for two days
    db.picks.update_one({"_id": p["_id"]}, {"$set": upd})
    return 1


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
            elif x.get("n_xev", 0) >= 12 and x.get("exp_roi") is not None and x["exp_roi"] <= -3.0:
                out.append({"flag": "watch", "segment": f"{gname}:{k}", "n": n, "record": f"{x['W']}-{x['L']}",
                            "units": x["units"], "exp_roi": x["exp_roi"],
                            "why": f"worth {x['exp_roi']}% per unit at the fair close on {x['n_xev']} priced rows (vig is eating it)"})
            elif x.get("n_clv", 0) >= 10 and x.get("mean_clv") is not None and x["mean_clv"] <= -1.0:
                out.append({"flag": "watch", "segment": f"{gname}:{k}", "n": n, "record": f"{x['W']}-{x['L']}",
                            "units": x["units"], "mean_clv": x["mean_clv"], "why": f"mean CLV {x['mean_clv']}% on {x['n_clv']} priced rows"})
            elif x.get("n_clv", 0) >= 15 and (x.get("mean_clv") or 0) >= 1.0 and x["beat_close"] / x["n_clv"] >= 0.55 \
                    and (x.get("exp_roi") is None or x["exp_roi"] > 0):
                out.append({"flag": "strength", "segment": f"{gname}:{k}", "n": n, "record": f"{x['W']}-{x['L']}",
                            "units": x["units"], "mean_clv": x["mean_clv"], "why": "beats the close consistently"})
    order = {"tighten": 0, "watch": 1, "strength": 2}
    return sorted(out, key=lambda f: (order[f["flag"]], -f["n"]))


def _band(conf):
    if conf is None:
        return None
    return "<50%" if conf < 50 else "50-54%" if conf < 55 else "55-59%" if conf < 60 else "60%+"


SINGLE_REQUIRED = ["confidence", "ev_pct", "anchor_prob", "model_prob", "anchor_quality", "thesis_quality",
                   "stake_units", "book", "bet_type"]


def quality_check(db):
    """Fields v16 requires on every new pick. Lists what is missing so the run fixes
    it and the site can show it; never edits a pick."""
    since = (NOW - dt.timedelta(days=3)).date().isoformat()
    missing = []
    n = 0
    for p in db.picks.find({"date": {"$gte": since}}):
        n += 1
        gaps = []
        if p.get("legs"):
            if not p.get("slip_type"):
                gaps.append("slip_type")
            if any(not (l.get("price_decimal") or l.get("price_american")) for l in p["legs"]):
                gaps.append("leg prices")
            if not p.get("stake_units"):
                gaps.append("stake_units")
        else:
            gaps += [f for f in SINGLE_REQUIRED if p.get(f) in (None, "", [])]
            if not (p.get("price_american") or p.get("price_decimal")):
                gaps.append("price")
            if not (p.get("falsifier") or p.get("wrong_if")):
                gaps.append("wrong_if/falsifier")
            if not (p.get("line_gap_thesis") or p.get("reasoning")):
                gaps.append("reasoning")
        if gaps:
            missing.append({"date": p.get("date"), "bet": p.get("bet"), "fields": gaps})
    return {"checked": n, "since": since, "complete": n - len(missing), "missing": missing[:40]}


def step_summary(db):
    rows = list(db.picks.find({"date": {"$gte": FIRST_LIVE_DAY}}, {
        "date": 1, "sport": 1, "bet_type": 1, "result": 1, "units": 1, "stake_units": 1, "clv": 1,
        "confidence": 1, "anchor_prob": 1, "model_prob": 1, "legs": 1, "slip_type": 1, "tags": 1,
        "anchor_quality": 1, "thesis_quality": 1, "ev_pct": 1, "price_decimal": 1, "xev": 1}))
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
        # fair-price EV at the close: what the bets were worth, independent of how they landed
        xr = [r for r in items if isinstance(r.get("xev"), (int, float))]
        xst = sum(r.get("stake_units") or 0.5 for r in xr)
        return {"W": W, "L": L, "P": P, "units": u, "hit": round(100 * W / (W + L), 1) if W + L else None,
                "wilson_lo": lo, "wilson_hi": hi, "be": round(100 * sum(1 / d for d in decs) / len(decs), 1) if decs else None,
                "roi": round(100 * u / st, 1) if st else None, "n_clv": len(clvs),
                "mean_clv": round(sum(clvs) / len(clvs), 2) if clvs else None,
                "beat_close": sum(c > 0 for c in clvs),
                "n_xev": len(xr), "mean_xev": round(sum(r["xev"] for r in xr) / len(xr), 2) if xr else None,
                "exp_units": round(sum((r.get("stake_units") or 0.5) * r["xev"] / 100 for r in xr), 3) if xr else None,
                "exp_roi": round(100 * sum((r.get("stake_units") or 0.5) * r["xev"] / 100 for r in xr) / xst, 2) if xst else None}

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
        "clv_coverage": {"graded": len(graded), "with_clv": sum(isinstance(r.get("clv"), (int, float)) for r in graded),
                         "with_xev": sum(isinstance(r.get("xev"), (int, float)) for r in graded)},
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
    doc["quality"] = quality_check(db)
    db.ledger_summary.replace_one({"_id": "current"}, doc, upsert=True)
    db.ledger_summary.replace_one({"_id": NOW.date().isoformat()}, dict(doc, _id=NOW.date().isoformat()), upsert=True)
    o = doc["overall"]
    log(f"summary: {o['W']}-{o['L']}-{o['P']} {o['units']:+}u, fair-close EV {o.get('exp_roi')}% on {o.get('n_xev')} priced, "
        f"adjustment test {doc['adjustment_test']['all']}")


# ---------------------------------------------------------------- SharpAPI pre-kick (props)
def sharp_get(path, key):
    req = urllib.request.Request("https://api.sharpapi.io/api/v1" + path,
                                 headers={"X-API-Key": key, "User-Agent": "curl/8.5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        remaining = r.headers.get("x-ratelimit-remaining")
        body = json.loads(r.read().decode("utf-8"))
    if remaining is not None and int(remaining) <= 1:
        time.sleep(6)  # free tier: 12 requests a minute
    return body


# our parsed stat -> substring of SharpAPI's market_type (player_total_bases, player_strikeouts, ...)
PROP_MARKET = {("batting", "TB"): "total_bases", ("pitching", "K"): "strikeouts", ("pitching", "IP"): "outs",
               ("pitching", "H"): "hits_allowed", ("pitching", "ER"): "earned_runs", ("batting", "HR"): "home_runs",
               ("batting", "RBI"): "rbi", ("batting", "R"): "runs", ("batting", "H"): "hits",
               ("passing", "YDS"): "passing_yards", ("rushing", "YDS"): "rushing_yards", ("receiving", "YDS"): "receiving_yards",
               ("receiving", "REC"): "receptions", ("rushing", "CAR"): "rushing_attempts", ("passing", "TD"): "passing_touchdowns",
               ("passing", "C/ATT"): "completions", (None, "PTS"): "points", (None, "REB"): "rebounds", (None, "AST"): "assists",
               (None, "3PT"): "three", (None, "SOG"): "shots_on_goal", (None, "SV"): "saves", (None, "BS"): "blocked",
               (None, "G"): "goals", (None, "STL"): "steals", (None, "BLK"): "blocks"}
BOOK_ORDER = ["draftkings", "fanduel"]  # free tier carries these two; DraftKings matches the ESPN closes


def prop_market_key(spec):
    st = spec["stat"]
    if isinstance(st, list):  # combos: points+rebounds+assists etc.
        return "_".join(PROP_MARKET.get(x, "") for x in st)
    return PROP_MARKET.get(st)


def pick_prop_rows(rows, spec, mkey, start):
    """The Over/Under pair for this player, market and line from one book, or None."""
    want = {}
    for r in rows or []:
        if r.get("is_live") or r.get("is_active") is False or not r.get("is_player_prop", True):
            continue
        if (r.get("market_segment") or "full_game") != "full_game":
            continue
        mt = norm(r.get("market_type") or "").replace(" ", "_")
        if mkey not in mt or (mkey == "hits" and "allowed" in mt) or (mkey == "runs" and "earned" in mt):
            continue
        if r.get("line") is None or float(r["line"]) != spec["line"]:
            continue
        if norm(r.get("player_name")) != norm(spec["player"]):
            continue
        st = r.get("event_start_time")
        if st and start and abs((dt.datetime.fromisoformat(st.replace("Z", "+00:00")) - start).total_seconds()) > 3 * 3600:
            continue  # another game of this player's
        side = norm(r.get("selection_type") or r.get("selection") or "")
        side = "over" if "over" in side else "under" if "under" in side else None
        book = (r.get("sportsbook") or "").lower()
        if side and book:
            want.setdefault(book, {})[side] = r
    for book in BOOK_ORDER + sorted(set(want) - set(BOOK_ORDER)):
        pair = want.get(book) or {}
        if spec["side"] in pair:
            other = pair.get("under" if spec["side"] == "over" else "over")
            return book, pair[spec["side"]], other
    return None


def step_prekick(db):
    """Near-kickoff prices for open player props (singles and parlay legs), found by
    player name: one SharpAPI call per player, only inside the last 75 minutes before
    the game. Both sides are saved so the close step can de-vig them (prop CLV + xev)."""
    key = os.environ.get("SHARPAPI_KEY")
    if not key:
        log("prekick: SHARPAPI_KEY not set, skipped")
        return
    horizon = NOW + dt.timedelta(minutes=75)
    open_rows = list(db.picks.find({"result": "OPEN", "date": {"$gte": (NOW - dt.timedelta(days=1)).date().isoformat()}}))
    calls = saved = 0
    fetched = {}
    for p in open_rows:
        legs = p.get("legs") or [{"game_key": p.get("game_key"), "market": p.get("bet_type"), "selection": p.get("bet")}]
        for leg in legs:
            if leg.get("status") in ("WIN", "LOSS", "PUSH"):
                continue
            spec = parse(leg.get("selection"), leg.get("market"), p.get("bet_type") if not p.get("legs") else None, p.get("sport"))
            if not spec or spec["kind"] != "prop":
                continue
            mkey = prop_market_key(spec)
            ev = event_for_key(p.get("sport"), leg.get("game_key"), p.get("matchup"))
            if not mkey or not ev:
                continue
            start = dt.datetime.fromisoformat(event_state(ev[2])["start"].replace("Z", "+00:00"))
            if not (NOW <= start <= horizon):
                continue  # only spend a SharpAPI call inside the last 75 minutes before kickoff
            recent = db.odds_snapshots.find_one({"game_key": leg.get("game_key"), "kind": "pre_kick", "selection": leg.get("selection"),
                                                 "captured_at": {"$gte": (NOW - dt.timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")}})
            if recent:
                continue
            who = spec["player"]
            if who not in fetched:
                try:
                    calls += 1
                    q = urllib.parse.urlencode({"player_name": who, "is_live": "false", "market": "props", "limit": 200})
                    data = sharp_get(f"/odds?{q}", key)
                    fetched[who] = data.get("data") if isinstance(data, dict) else data
                except (urllib.error.URLError, ValueError) as e:
                    log(f"  sharpapi error for {who}: {type(e).__name__}")
                    fetched[who] = None
            got = pick_prop_rows(fetched[who], spec, mkey, start)
            if not got:
                log(f"  prekick: no {mkey} {spec['line']} line for {who}")
                continue
            book, row, other = got
            db.odds_snapshots.insert_one({"captured_at": ISO, "kind": "pre_kick", "game_key": leg.get("game_key"),
                                          "market": row.get("market_type"), "selection": leg.get("selection"), "point": spec["line"],
                                          "book": book, "price_american": row.get("odds_american"), "price_decimal": row.get("odds_decimal"),
                                          "other_price_decimal": (other or {}).get("odds_decimal"),
                                          "source": f"sharpapi pipeline event_id={row.get('event_id')}"})
            saved += 1
            log(f"  prekick {leg.get('selection')!r}: {book} {row.get('odds_american')} (other side {(other or {}).get('odds_american')})")
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


STEPS = {"enrich": step_enrich, "grade": step_grade, "sync": step_sync, "close": step_close, "audit": step_audit,
         "summary": step_summary, "prekick": step_prekick}
DEFAULT = ["grade", "sync", "close", "audit", "enrich", "summary"]


def run_steps(db, steps):
    for s in steps:
        t = time.time()
        try:
            STEPS[s](db)
        except Exception as e:  # one failed step must not stop the others
            log(f"{s}: FAILED {type(e).__name__}: {e}")
        log(f"  ({s} took {time.time() - t:.1f}s)")
    db.source_health.update_one({"_id": "ledger_pipeline"}, {"$set": {"last_run": ISO, "steps": steps}}, upsert=True)


def tick():
    """Fresh clock and fresh ESPN data for the next pass of a watch loop."""
    global NOW, ISO
    NOW = dt.datetime.now(dt.timezone.utc)
    ISO = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
    import espn
    espn._cache.clear()


def open_past(db):
    return db.picks.count_documents({"result": "OPEN", "date": {"$gte": FIRST_LIVE_DAY, "$lt": NOW.date().isoformat()}})


def main():
    """--watch-until HH:MM (UTC) keeps re-running the steps every --every minutes until
    then, or until no past-dated pick is left OPEN. GitHub drops most scheduled runs,
    so whichever overnight run does start stays alive through the gap between the last
    final whistle and the 3am ET daily run instead of grading once and leaving."""
    args = sys.argv[1:]
    until, every = None, 10
    if "--watch-until" in args:
        i = args.index("--watch-until")
        hh, mm = (int(x) for x in args[i + 1].split(":"))
        until = NOW.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if until <= NOW:
            until = None  # window already over: a single pass
        del args[i:i + 2]
    if "--every" in args:
        i = args.index("--every")
        every = float(args[i + 1])
        del args[i:i + 2]
    steps = args or DEFAULT
    bad = [s for s in steps if s not in STEPS]
    if bad:
        log(f"unknown step(s): {bad}; choose from {list(STEPS)}")
        sys.exit(2)
    db = connect()
    run_steps(db, steps)
    while until:
        left = open_past(db)
        if not left:
            log("watch: nothing past-dated is OPEN, done")
            break
        wait = min(every * 60, (until - dt.datetime.now(dt.timezone.utc)).total_seconds())
        if wait <= 0:
            log(f"watch: window over with {left} past-dated pick(s) still OPEN (left for the daily run)")
            break
        log(f"watch: {left} past-dated pick(s) still OPEN, next pass in {wait / 60:.0f} min")
        time.sleep(wait)
        tick()
        run_steps(db, steps)


if __name__ == "__main__":
    main()

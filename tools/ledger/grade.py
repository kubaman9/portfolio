"""Pure grading and CLV logic. No database access here, so it can be tested
against exported picks. Every function returns None when it is not sure; the
pipeline then leaves the row for the daily run instead of guessing."""
import re

from espn import (norm, find_event, event_state, competitors, score_of, team_names,
                  summary, core_odds, player_stat, scoreboard, LEAGUES)

FOOTBALL = {"NFL", "CFB"}
PROP_STATS = [  # (regex on text/market, (box score group, label))
    (r"pass(ing)?[ _]?(yds|yards)", ("passing", "YDS")),
    (r"rush(ing)?[ _]?(yds|yards)", ("rushing", "YDS")),
    (r"(rec|receiving)[ _]?(yds|yards)", ("receiving", "YDS")),
    (r"receptions", ("receiving", "REC")),
    (r"rush(ing)?[ _]?attempts|carries", ("rushing", "CAR")),
    (r"pass(ing)?[ _]?(td|tds|touchdowns)", ("passing", "TD")),
    (r"completions", ("passing", "C/ATT")),
]


def dec_from_american(a):
    a = float(a)
    return 1 + (a / 100 if a > 0 else 100 / -a)


def price_decimal(p):
    if p.get("price_decimal"):
        return float(p["price_decimal"])
    if p.get("price_american") not in (None, ""):
        return dec_from_american(p["price_american"])
    return None


def units_for(result, stake, dec):
    if result == "WIN":
        return round(stake * (dec - 1), 4)
    if result == "LOSS":
        return round(-stake, 4)
    return 0.0


def team_in_text(text, comps):
    """Index of the single competitor named in text, else None."""
    t = " " + norm(text) + " "
    hits = []
    for i, c in enumerate(comps):
        names = sorted(team_names(c), key=len, reverse=True)
        for n in names:
            if len(n) >= 3 and (" " + n + " ") in t:
                hits.append((len(n), i))
                break
    if not hits:
        return None
    hits.sort(reverse=True)
    if len(hits) > 1 and hits[0][0] == hits[1][0] and hits[0][1] != hits[1][1]:
        return None  # ambiguous
    return hits[0][1]


def signed_point(text):
    t = norm(text)
    m = re.findall(r"(?<![\w.])([+-]\d+(?:\.\d+)?)(?![\w.])", t)
    return float(m[-1]) if m else None


def parse(text, market, bet_type, sport):
    """-> dict(kind=..., ...) or None"""
    t = norm(text)
    mk = norm(market or "").replace("_", " ")
    bt = norm(bet_type or "")
    ou = re.search(r"\b(over|under)\s*(\d+(?:\.\d+)?)", t)
    is_prop = "player" in mk or bt == "player prop" or any(re.search(rx, t) or re.search(rx, mk) for rx, _ in PROP_STATS)
    if is_prop:
        if sport not in FOOTBALL or not ou:
            return None
        stat = next((s for rx, s in PROP_STATS if re.search(rx, mk) or re.search(rx, t)), None)
        player = re.split(r"\s+(?:over|under)\s+", text, flags=re.I)[0].strip()
        if not stat or not player:
            return None
        return {"kind": "prop", "player": player, "stat": stat, "side": ou.group(1), "line": float(ou.group(2))}
    if bt.startswith("total") or "total" in mk or re.match(r"^(total\s+)?(over|under)\b", t):
        if not ou:
            return None
        return {"kind": "total", "side": ou.group(1), "line": float(ou.group(2))}
    if "moneyline" in mk or bt == "moneyline" or re.search(r"\b(ml|moneyline)\b", t):
        return {"kind": "ml", "text": text}
    if bt in ("spread", "run line", "run line fav", "run line dog", "puck line") or "spread" in mk or signed_point(t) is not None:
        pt = signed_point(t)
        return {"kind": "spread", "text": text, "point": pt} if pt is not None else None
    return None


def outcome(spec, ev, sport, sport_key, league):
    """WIN/LOSS/PUSH for one parsed selection on a final event, or None."""
    comps = competitors(ev)
    if spec["kind"] == "prop":
        summ = summary(sport_key, league, ev["id"])
        val = player_stat(summ, spec["player"], spec["stat"])
        if val is None:
            return None  # DNP / name mismatch: leave it for a human-grade
        if val == spec["line"]:
            return "PUSH"
        over = val > spec["line"]
        return "WIN" if over == (spec["side"] == "over") else "LOSS"
    scores = [score_of(c) for c in comps]
    if None in scores:
        return None
    if spec["kind"] == "total":
        tot = sum(scores)
        if tot == spec["line"]:
            return "PUSH"
        return "WIN" if (tot > spec["line"]) == (spec["side"] == "over") else "LOSS"
    i = team_in_text(spec["text"], comps)
    if i is None:
        return None
    mine, theirs = scores[i], scores[1 - i]
    if spec["kind"] == "ml":
        if mine == theirs:
            return "LOSS" if sport == "Soccer" else "PUSH"
        return "WIN" if mine > theirs else "LOSS"
    margin = mine + spec["point"] - theirs
    return "PUSH" if margin == 0 else ("WIN" if margin > 0 else "LOSS")


def event_for_key(sport, game_key, hint):
    """Resolve a leg's game from its game_key codes or a team named in hint."""
    if not game_key or "|" not in game_key:
        return None
    date, codes = game_key.split("|", 1)
    codes = {norm(c) for c in codes.split("-")}
    import datetime as _dt
    base = _dt.date.fromisoformat(date)
    for delta in (0, 1, -1):
        day = (base + _dt.timedelta(days=delta)).isoformat()
        for sk, lg, extra in LEAGUES.get(sport, []):
            try:
                events = scoreboard(sk, lg, day, extra)
            except RuntimeError:
                continue
            for ev in events:
                comps = competitors(ev)
                abbrs = {norm(c.get("team", {}).get("abbreviation")) for c in comps}
                if codes <= abbrs or (hint and team_in_text(hint, comps) is not None and codes & abbrs):
                    return sk, lg, ev
    return None


def final_score_text(ev):
    c = competitors(ev)
    away = next((x for x in c if x.get("homeAway") == "away"), c[0])
    home = next((x for x in c if x.get("homeAway") == "home"), c[1])
    return f"{away['team'].get('abbreviation')} {away.get('score')} @ {home['team'].get('abbreviation')} {home.get('score')} (final, ESPN)"


def grade_pick(p):
    """Return an update dict for a pick, or None when it cannot be graded safely."""
    sport = p.get("sport")
    stake = p.get("stake_units")
    dec = price_decimal(p)
    if stake in (None, 0) or not dec:
        return None
    if p.get("legs"):
        statuses, dec_wins, notes = [], 1.0, []
        new_legs = []
        for leg in p["legs"]:
            leg = dict(leg)
            if leg.get("status") in ("WIN", "LOSS", "PUSH"):
                st = leg["status"]
            else:
                spec = parse(leg.get("selection"), leg.get("market"), None, sport)
                found = event_for_key(sport, leg.get("game_key"), leg.get("selection") if spec and spec["kind"] != "prop" else p.get("matchup"))
                st = None
                if spec and found and event_state(found[2])["final"]:
                    st = outcome(spec, found[2], sport, found[0], found[1])
                if st:
                    leg["status"] = st
                    notes.append(f"{leg.get('selection')}: {st}")
            statuses.append(leg.get("status"))
            if leg.get("status") == "WIN":
                dec_wins *= float(leg.get("price_decimal") or dec_from_american(leg.get("price_american")))
            new_legs.append(leg)
        if "LOSS" in statuses:
            res, units = "LOSS", round(-stake, 4)
        elif all(s in ("WIN", "PUSH") for s in statuses):
            res = "PUSH" if all(s == "PUSH" for s in statuses) else "WIN"
            units = 0.0 if res == "PUSH" else round(stake * (dec_wins - 1), 4)
        else:
            changed = new_legs != p["legs"]
            return {"legs": new_legs} if changed else None  # partial: record legs, keep OPEN
        return {"result": res, "units": units, "legs": new_legs,
                "grade_note": "pipeline: " + "; ".join(notes) if notes else "pipeline"}
    spec = parse(p.get("bet"), None, p.get("bet_type"), sport)
    if not spec:
        return None
    found = find_event(sport, p.get("date"), p.get("matchup"))
    if not found:
        return None
    sk, lg, ev = found
    if not event_state(ev)["final"]:
        return None
    res = outcome(spec, ev, sport, sk, lg)
    if not res:
        return None
    return {"result": res, "units": units_for(res, stake, dec), "final_score": final_score_text(ev),
            "_espn": (sk, lg, ev["id"])}


def _american_str(v):
    try:
        return int(float(str(v).replace("+", "")))
    except (TypeError, ValueError):
        return None


def closing_for(p, sk, lg, ev_id, comps_by_index):
    """CLV from the ESPN close for single game-level picks. Returns update or None."""
    spec = parse(p.get("bet"), None, p.get("bet_type"), p.get("sport"))
    if not spec or spec["kind"] == "prop":
        return None
    it = core_odds(sk, lg, ev_id)
    if not it:
        return None
    dec_pick = price_decimal(p)
    close_dec, close_point, label = None, None, None
    if spec["kind"] == "total":
        cl = (it.get("close") or {})
        side = cl.get(spec["side"]) or {}
        close_dec = side.get("decimal")
        tot = (cl.get("total") or {}).get("american")
        close_point = float(tot) if tot not in (None, "") else None
        label = f"{spec['side'].title()} {close_point} ({side.get('american')}, {it.get('provider', {}).get('name')} via ESPN Core)"
        same_point = close_point == spec["line"]
        # + = we got a better number than the close (a higher Under, a lower Over)
        move = None if close_point is None else (spec["line"] - close_point) * (1 if spec["side"] == "under" else -1)
    else:
        i = team_in_text(spec["text"], comps_by_index)
        if i is None:
            return None
        side_key = "homeTeamOdds" if comps_by_index[i].get("homeAway") == "home" else "awayTeamOdds"
        cl = (it.get(side_key) or {}).get("close") or {}
        abbr = comps_by_index[i]["team"].get("abbreviation")
        if spec["kind"] == "ml":
            ml = cl.get("moneyLine") or {}
            close_dec = ml.get("decimal")
            label = f"{abbr} ML {ml.get('american')} ({it.get('provider', {}).get('name')} via ESPN Core)"
            same_point, move = True, None
        else:
            ps = (cl.get("pointSpread") or {}).get("american")
            sp = cl.get("spread") or {}
            close_point = float(ps) if ps not in (None, "") else None
            close_dec = sp.get("decimal")
            label = f"{abbr} {ps} ({sp.get('american')}, {it.get('provider', {}).get('name')} via ESPN Core)"
            same_point = close_point == spec["point"]
            move = None if close_point is None else spec["point"] - close_point  # + = we got more points than the close
    if not close_dec or not dec_pick:
        return None
    upd = {"closing_line": label, "clv_source": "espn_core_pipeline", "closing_point": close_point}
    if same_point:
        upd["clv"] = round((dec_pick / float(close_dec) - 1) * 100, 2)
    if move is not None:
        upd["point_move"] = round(move, 2)
    return upd

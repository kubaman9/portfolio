"""Pure grading and CLV logic. No database access here, so it can be tested
against exported picks. Every function returns None when it is not sure; the
pipeline then leaves the row for the daily run instead of guessing."""
import re

from espn import (norm, find_event, event_state, competitors, score_of, team_names,
                  summary, core_odds, player_stat, total_bases, anytime_td, scoreboard, LEAGUES)

FOOTBALL = {"NFL", "CFB"}
BASEBALL = {"MLB"}
BASKETBALL = {"NBA", "WNBA", "CBB", "NCAAB"}
HOCKEY = {"NHL"}
# (regex on the selection text or market, stat key); first match wins, so combos come first
PROP_STATS = {
    "football": [
        (r"pass(ing)?[ _]?(yds|yards)", ("passing", "YDS")),
        (r"rush(ing)?[ _]?(yds|yards)", ("rushing", "YDS")),
        (r"(rec|receiving)[ _]?(yds|yards)", ("receiving", "YDS")),
        (r"receptions", ("receiving", "REC")),
        (r"rush(ing)?[ _]?attempts|carries", ("rushing", "CAR")),
        (r"pass(ing)?[ _]?(td|tds|touchdowns)", ("passing", "TD")),
        (r"completions", ("passing", "C/ATT")),
    ],
    "baseball": [
        (r"total bases|\btb\b", ("batting", "TB")),  # counted from plays, see espn.total_bases
        (r"hits ?\+ ?runs ?\+ ?rbis?|h ?\+ ?r ?\+ ?rbi", [("batting", "H"), ("batting", "R"), ("batting", "RBI")]),
        (r"strikeouts|pitcher[ _]k|\bks\b", ("pitching", "K")),
        (r"outs recorded|pitching outs|\bouts\b", ("pitching", "IP")),
        (r"hits allowed", ("pitching", "H")),
        (r"earned runs", ("pitching", "ER")),
        (r"home runs?|\bhrs?\b", ("batting", "HR")),
        (r"\brbis?\b", ("batting", "RBI")),
        (r"runs scored|batter[ _]runs", ("batting", "R")),
        (r"\bhits\b|batter[ _]hits", ("batting", "H")),
    ],
    "hockey": [
        (r"points|\bpts\b", [(None, "G"), (None, "A")]),
        (r"shots on goal|\bsog\b|\bshots\b", (None, "SOG")),
        (r"saves", (None, "SV")),
        (r"blocked shots|blocks", (None, "BS")),
        (r"assists", (None, "A")),
        (r"goals", (None, "G")),
    ],
    "basketball": [
        (r"pts ?\+ ?reb ?\+ ?ast|points ?\+ ?rebounds ?\+ ?assists|\bpra\b", [(None, "PTS"), (None, "REB"), (None, "AST")]),
        (r"pts ?\+ ?reb|points ?\+ ?rebounds", [(None, "PTS"), (None, "REB")]),
        (r"pts ?\+ ?ast|points ?\+ ?assists", [(None, "PTS"), (None, "AST")]),
        (r"threes|3[ -]?pointers|3pt|three[ -]point", (None, "3PT")),
        (r"points|\bpts\b", (None, "PTS")),
        (r"rebounds|\breb\b", (None, "REB")),
        (r"assists|\bast\b", (None, "AST")),
        (r"steals", (None, "STL")),
        (r"blocks", (None, "BLK")),
    ],
}


def family(sport):
    return ("football" if sport in FOOTBALL else "baseball" if sport in BASEBALL else
            "basketball" if sport in BASKETBALL else "hockey" if sport in HOCKEY else None)


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


FB_TD_RX = r"anytime (td|touchdown)|to score a (td|touchdown)|anytime[ _]td"
SCORER_RX = r"anytime (goal ?scorer|scorer|goalscorer|to score)|to score anytime|anytime goal|to score\b"
ASSIST_RX = r"anytime assist|to assist|to record an assist"


def parse(text, market, bet_type, sport):
    """-> dict(kind=..., ...) or None"""
    t = norm(text)
    mk = norm(market or "").replace("_", " ")
    bt = norm(bet_type or "")
    if sport == "Soccer" and (re.search(SCORER_RX, t) or re.search(SCORER_RX, mk) or re.search(ASSIST_RX, t) or re.search(ASSIST_RX, mk)):
        kind = "assist" if (re.search(ASSIST_RX, t) or re.search(ASSIST_RX, mk)) else "scorer"
        player = re.split(r"\s+(?:anytime|to score|to assist|to record)", text, flags=re.I)[0].strip()
        return {"kind": kind, "player": player} if player else None
    ou = re.search(r"\b(over|under)\s*(\d+(?:\.\d+)?)", t)
    fam = family(sport)
    if fam == "hockey" and (re.search(SCORER_RX, t) or re.search(SCORER_RX, mk)):
        player = re.split(r"\s+(?:anytime|to score)", text, flags=re.I)[0].strip()
        return {"kind": "prop", "player": player, "stat": (None, "G"), "side": "over", "line": 0.5} if player else None
    if fam == "football" and (re.search(FB_TD_RX, t) or re.search(FB_TD_RX, mk)):
        player = re.split(r"\s+(?:anytime|to score|1st|first)", text, flags=re.I)[0].strip()
        player = re.sub(r"\s+(yes|no)$", "", player, flags=re.I).strip()  # "Charlie Becker Yes" (book's Yes/No side)
        return {"kind": "prop", "player": player, "stat": "ANYTD", "side": "over", "line": 0.5} if player else None
    table = PROP_STATS.get(fam, [])
    is_prop = "player" in mk or "pitcher" in mk or "batter" in mk or bt == "player prop" or any(re.search(rx, t) or re.search(rx, mk) for rx, _ in table)
    if is_prop:
        if not fam or not ou:
            return None
        stat = next((s for rx, s in table if re.search(rx, mk) or re.search(rx, t)), None)
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
    if spec["kind"] in ("scorer", "assist"):
        summ = summary(sport_key, league, ev["id"])
        who = norm(spec["player"])
        played = False
        for team in summ.get("rosters") or []:
            for r in team.get("roster") or []:
                if norm((r.get("athlete") or {}).get("displayName")) == who and (r.get("starter") or r.get("subbedIn")):
                    played = True
        idx = 0 if spec["kind"] == "scorer" else 1
        for k in summ.get("keyEvents") or []:
            typ = norm(((k.get("type") or {}).get("type")) or "")
            if typ != "goal":  # own goals and penalties-in-shootout do not count
                continue
            parts = k.get("participants") or []
            if len(parts) > idx and norm((parts[idx].get("athlete") or {}).get("displayName")) == who:
                return "WIN"
        return "LOSS" if played else None  # did not play: void, leave for the run
    if spec["kind"] == "prop":
        summ = summary(sport_key, league, ev["id"])
        if spec["stat"] == ("batting", "TB"):
            val = total_bases(summ, spec["player"])
        elif spec["stat"] == "ANYTD":
            val = anytime_td(summ, spec["player"])
        else:
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
    try:
        base = _dt.date.fromisoformat(date)
    except ValueError:  # e.g. "legacy|..." keys on early-September rows
        return None
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
                # runs write codes as abbreviations (IU-RUTG) or as names (INDIANA-RUTGERS)
                by_name = all(any(code in team_names(c) for c in comps) for code in codes) and \
                    len({i for code in codes for i, c in enumerate(comps) if code in team_names(c)}) == len(codes)
                if codes <= abbrs or by_name or (hint and team_in_text(hint, comps) is not None and codes & abbrs):
                    return sk, lg, ev
    return None


def final_score_text(ev):
    c = competitors(ev)
    away = next((x for x in c if x.get("homeAway") == "away"), c[0])
    home = next((x for x in c if x.get("homeAway") == "home"), c[1])
    return f"{away['team'].get('abbreviation')} {away.get('score')} @ {home['team'].get('abbreviation')} {home.get('score')} (final, ESPN)"


FIGHT_SPORTS = {"UFC", "MMA"}


def fight_result(fighter, date):
    """WIN/LOSS for a UFC fighter's bout on date (+/- 1 day) from ESPN; None if unsure
    (not found, not final, draw or no contest)."""
    import datetime as _dt
    want = norm(re.sub(r"\b(moneyline|ml|to win|fight winner)\b", " ", fighter, flags=re.I))
    base = _dt.date.fromisoformat(date)
    for delta in (0, 1, -1):
        day = (base + _dt.timedelta(days=delta)).isoformat()
        try:
            events = scoreboard("mma", "ufc", day)
        except RuntimeError:
            continue
        for ev in events:
            for comp in ev.get("competitions", []):
                names = [norm(c.get("athlete", {}).get("displayName")) for c in comp.get("competitors", [])]
                if want not in names:
                    continue
                st = comp.get("status", {}).get("type", {})
                if not (st.get("completed") and st.get("state") == "post"):
                    return None
                me = comp["competitors"][names.index(want)]
                other = [c for c in comp["competitors"] if c is not me]
                if me.get("winner") is True:
                    return "WIN"
                if other and other[0].get("winner") is True:
                    return "LOSS"
                return None  # draw / no contest: leave for the run
    return None


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
            elif norm(leg.get("market")) in ("fight winner", "fight_winner", "moneyline") and (sport in FIGHT_SPORTS or "ufc" in norm(leg.get("game_key"))):
                st = fight_result(leg.get("selection") or "", (leg.get("game_key") or p.get("date", "")).split("|")[0])
                if st:
                    leg["status"] = st
                    notes.append(f"{leg.get('selection')}: {st}")
            else:
                spec = parse(leg.get("selection"), leg.get("market"), None, sport)
                # sides name a team in the selection; totals and props do not, so use the matchup
                hint = leg.get("selection") if spec and spec["kind"] in ("ml", "spread") else p.get("matchup")
                found = event_for_key(sport, leg.get("game_key"), hint)
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
    if sport in FIGHT_SPORTS and not p.get("legs"):
        if norm(p.get("bet_type")) not in ("fight winner", "moneyline") and not re.search(r"\b(moneyline|ml)\b", norm(p.get("bet"))):
            return None  # method / round markets stay with the run
        res = fight_result(p.get("bet") or "", p.get("date"))
        if not res:
            return None
        return {"result": res, "units": units_for(res, stake, dec), "final_score": "ESPN UFC result"}
    spec = parse(p.get("bet"), None, p.get("bet_type"), sport)
    if not spec:
        return None
    found = find_event(sport, p.get("date"), p.get("matchup"))
    if not found and spec["kind"] != "prop":
        # free-text matchup did not resolve ("Greece @ Netherlands... (venue note)"):
        # fall back to the game_key team codes, confirmed by the team named in the bet
        found = event_for_key(sport, p.get("game_key"), p.get("bet"))
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


def fair_prob(mine, others):
    """No-vig probability of an outcome from the closing decimals of every outcome
    (multiplicative de-vig). None unless every price is there."""
    prices = [mine] + list(others)
    if not others or any(not x or float(x) <= 1 for x in prices):
        return None
    inv = [1 / float(x) for x in prices]
    return inv[0] / sum(inv)


def xev_pct(dec_pick, fair):
    """Expected return of the bet at the fair closing price, in percent. This is the
    best single-bet estimate of whether a pick was +EV, long before W/L settles it."""
    return round((float(dec_pick) * fair - 1) * 100, 2)


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
    others = []  # closing decimals of the other outcome(s), for the no-vig fair price
    if spec["kind"] == "total":
        cl = (it.get("close") or {})
        side = cl.get(spec["side"]) or {}
        close_dec = side.get("decimal")
        others = [(cl.get("under" if spec["side"] == "over" else "over") or {}).get("decimal")]
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
        other_key = "awayTeamOdds" if side_key == "homeTeamOdds" else "homeTeamOdds"
        cl = (it.get(side_key) or {}).get("close") or {}
        ocl = (it.get(other_key) or {}).get("close") or {}
        abbr = comps_by_index[i]["team"].get("abbreviation")
        if spec["kind"] == "ml":
            ml = cl.get("moneyLine") or {}
            close_dec = ml.get("decimal")
            others = [(ocl.get("moneyLine") or {}).get("decimal")]
            if p.get("sport") == "Soccer":  # three-way market: the draw is the third outcome
                draw = (it.get("drawOdds") or {}).get("moneyLine")
                others.append(dec_from_american(draw) if draw not in (None, "") else None)
            label = f"{abbr} ML {ml.get('american')} ({it.get('provider', {}).get('name')} via ESPN Core)"
            same_point, move = True, None
        else:
            ps = (cl.get("pointSpread") or {}).get("american")
            sp = cl.get("spread") or {}
            close_point = float(ps) if ps not in (None, "") else None
            close_dec = sp.get("decimal")
            others = [(ocl.get("spread") or {}).get("decimal")]
            label = f"{abbr} {ps} ({sp.get('american')}, {it.get('provider', {}).get('name')} via ESPN Core)"
            same_point = close_point == spec["point"]
            move = None if close_point is None else spec["point"] - close_point  # + = we got more points than the close
    if not close_dec or not dec_pick:
        return None
    upd = {"closing_line": label, "clv_source": "espn_core_pipeline", "closing_point": close_point}
    if same_point:
        upd["clv"] = round((dec_pick / float(close_dec) - 1) * 100, 2)
        fair = fair_prob(close_dec, others)
        if fair is not None:
            upd["close_fair_prob"] = round(fair, 4)
            upd["xev"] = round((dec_pick * fair - 1) * 100, 2)
    if move is not None:
        upd["point_move"] = round(move, 2)
    return upd

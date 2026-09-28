"""ESPN public APIs: scoreboards, box scores and the core odds feed (open/close).

Keyless and free. Everything here is read-only and cached per process so a
pipeline pass makes at most one call per (league, date) and per event.
"""
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request

SITE = "https://site.api.espn.com/apis/site/v2/sports"
CORE = "https://sports.core.api.espn.com/v2/sports"

# sport label used in picks -> list of (espn sport, league, extra scoreboard params)
LEAGUES = {
    "NFL": [("football", "nfl", "")],
    "CFB": [("football", "college-football", "&groups=80&limit=400")],
    "MLB": [("baseball", "mlb", "")],
    "NBA": [("basketball", "nba", "")],
    "WNBA": [("basketball", "wnba", "")],
    "CBB": [("basketball", "mens-college-basketball", "&groups=50&limit=400")],
    "NCAAB": [("basketball", "mens-college-basketball", "&groups=50&limit=400")],
    "NHL": [("hockey", "nhl", "")],
    "Soccer": [("soccer", lg, "") for lg in (
        "uefa.nations", "fifa.worldq.uefa", "fifa.friendly", "fifa.worldq.conmebol",
        "fifa.worldq.concacaf", "fifa.worldq.afc", "fifa.worldq.caf", "fifa.world",
        "uefa.euro", "conmebol.america", "concacaf.gold", "caf.nations", "fifa.cwc",
        "eng.1", "esp.1", "ita.1", "ger.1", "fra.1", "usa.1", "uefa.champions",
        "uefa.europa", "uefa.europa.conf", "mex.1", "por.1", "ned.1")],
}

ALIASES = {"turkey": "turkiye", "usa": "united states", "korea republic": "south korea",
           "ivory coast": "cote d ivoire", "czech republic": "czechia"}

_cache = {}


def get(url, tries=3):
    if url in _cache:
        return _cache[url]
    last = None
    for i in range(tries):
        try:
            # ESPN's edge rejects unfamiliar user agents with 403; a plain curl UA is accepted.
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8"))
            _cache[url] = data
            return data
        except urllib.error.HTTPError as e:
            if e.code < 500:  # 4xx will not fix itself on retry
                _cache[url] = {}
                return {}
            last = e
            time.sleep(1.5 * (i + 1))
        except Exception as e:  # network hiccup, bad JSON
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"ESPN fetch failed: {url} ({type(last).__name__})")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    s = s.lower().replace("−", "-")
    s = re.sub(r"[^a-z0-9+\-. ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return ALIASES.get(s, s)


def scoreboard(sport, league, date, extra=""):
    ymd = date.replace("-", "")
    return get(f"{SITE}/{sport}/{league}/scoreboard?dates={ymd}{extra}").get("events", [])


def team_names(comp):
    t = comp.get("team", {})
    names = {norm(t.get(k)) for k in ("displayName", "shortDisplayName", "name", "location", "abbreviation", "nickname")}
    names.discard("")
    return names


def side_matches(side, comp):
    side = norm(side)
    if not side:
        return False
    names = team_names(comp)
    if side in names:
        return True
    disp = norm(comp.get("team", {}).get("displayName"))
    # "Los Angeles Rams" vs "Rams", "Mississippi State" vs "Mississippi State Bulldogs"
    return disp.startswith(side + " ") or disp.endswith(" " + side) or side.startswith(disp + " ")


def split_matchup(matchup):
    m = re.sub(r"\(.*?\)", " ", str(matchup or ""))
    m = re.split(r"\s+SGP\b|:", m)[0] if "SGP" in m else m
    parts = re.split(r"\s+(?:@|vs\.?|v\.?|at)\s+", m.strip(), flags=re.I)
    return [p.strip(" -") for p in parts] if len(parts) == 2 else None


def find_event(sport_label, date, matchup):
    """Return (sport, league, event) for a matchup on date (+/- 1 day), or None."""
    sides = split_matchup(matchup)
    if not sides:
        return None
    leagues = LEAGUES.get(sport_label) or []
    y, mo, d = (int(x) for x in date.split("-"))
    import datetime as _dt
    base = _dt.date(y, mo, d)
    for delta in (0, 1, -1):
        day = (base + _dt.timedelta(days=delta)).isoformat()
        for sport, league, extra in leagues:
            try:
                events = scoreboard(sport, league, day, extra)
            except RuntimeError:
                continue
            for ev in events:
                comps = ev.get("competitions", [{}])[0].get("competitors", [])
                if len(comps) != 2:
                    continue
                a = [i for i, c in enumerate(comps) if side_matches(sides[0], c)]
                b = [i for i, c in enumerate(comps) if side_matches(sides[1], c)]
                if a and b and set(a) != set(b):
                    return sport, league, ev
    return None


def event_state(ev):
    c = ev["competitions"][0]
    st = c.get("status", {}).get("type", {})
    return {
        # postponed/cancelled games are "post" but not completed, so they stay open
        "final": bool(st.get("completed")) and st.get("state") == "post",
        "state": st.get("state"),  # pre / in / post
        "name": st.get("name"),
        "start": c.get("date") or ev.get("date"),
    }


def competitors(ev):
    return ev["competitions"][0]["competitors"]


def score_of(comp):
    try:
        return float(comp.get("score"))
    except (TypeError, ValueError):
        return None


def summary(sport, league, event_id):
    return get(f"{SITE}/{sport}/{league}/summary?event={event_id}")


def core_odds(sport, league, event_id):
    try:
        d = get(f"{CORE}/{sport}/leagues/{league}/events/{event_id}/competitions/{event_id}/odds")
    except RuntimeError:
        return None
    items = d.get("items") or []
    if not items:
        return None
    items.sort(key=lambda it: (0 if "draftkings" in norm(it.get("provider", {}).get("name")) else 1,
                               it.get("provider", {}).get("priority", 99)))
    return items[0]


def player_stat(summ, player, stat_key):
    """stat_key like ('passing','YDS'). Returns float or None if the player is not in the box score."""
    group, label = stat_key
    pn = norm(player)
    for team in (summ.get("boxscore") or {}).get("players", []):
        for st in team.get("statistics", []):
            if st.get("name") != group:
                continue
            labels = st.get("labels", [])
            if label not in labels:
                continue
            idx = labels.index(label)
            for a in st.get("athletes", []):
                if norm(a.get("athlete", {}).get("displayName")) == pn:
                    try:
                        return float(str(a["stats"][idx]).split("/")[0])
                    except (ValueError, IndexError):
                        return None
    return None

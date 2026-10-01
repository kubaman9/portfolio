"""End-to-end test of the pipeline steps on an in-memory Mongo (mongomock) seeded
with real 9/27 picks, using live ESPN data. Needs network + mongomock.

  pip install pymongo mongomock && python3 tools/ledger/test_pipeline.py
"""
import os
import sys

import mongomock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline  # noqa: E402

db = mongomock.MongoClient()["betting_agent"]
D = "2026-09-27"
db.picks.insert_many([
    dict(date=D, sport="NFL", matchup="Cincinnati Bengals @ Pittsburgh Steelers", bet="Cincinnati Bengals -3.5",
         bet_type="Spread", stake_units=0.5, price_american=-104, price_decimal=1.9615, result="OPEN", units=None, clv=None,
         anchor_prob=0.4911, model_prob=0.5211, confidence=52, game_key="2026-09-27|CIN-PIT"),
    dict(date=D, sport="NFL", matchup="Arizona Cardinals @ San Francisco 49ers", bet="Arizona Cardinals +7.5",
         bet_type="Spread", stake_units=0.5, price_american=-110, price_decimal=1.9091, result="OPEN", units=None, clv=None,
         anchor_prob=0.5022, model_prob=0.5372, confidence=54, game_key="2026-09-27|ARI-SF"),
    dict(date=D, sport="Soccer", matchup="Norway @ Portugal (UEFA Nations League A)", bet="Portugal Moneyline",
         bet_type="Moneyline", stake_units=0.5, price_american=170, price_decimal=2.7, result="OPEN", units=None, clv=None,
         anchor_prob=0.35325, model_prob=0.40325, confidence=40, game_key="2026-09-27|POR-NOR"),
    # already graded (wrongly) as a WIN: the audit must flag it
    dict(date=D, sport="NFL", matchup="Denver Broncos @ Los Angeles Rams (SNF, SGP)",
         bet="Kyren Williams Over 54.5 rushing yards + Courtland Sutton Under 36.5 receiving yards", bet_type="Parlay",
         slip_type="sgp", stake_units=0.5, price_american=255, price_decimal=3.553, result="WIN", units=1.2766, clv=None,
         legs=[dict(game_key="2026-09-27|DEN-LAR", market="player_rushing_yards", selection="Kyren Williams Over 54.5", price_decimal=1.885, status="WIN"),
               dict(game_key="2026-09-27|DEN-LAR", market="player_receiving_yards", selection="Courtland Sutton Under 36.5", price_decimal=1.885, status="WIN")]),
    # open parlay graded from its legs
    dict(date=D, sport="NFL", matchup="NFL cross-game parlay", bet="Parlay: Arizona Cardinals +7.5 + Denver Broncos +2.5",
         bet_type="Parlay", slip_type="cross_game", stake_units=0.5, price_decimal=3.5694, result="OPEN", units=None, clv=None,
         legs=[dict(game_key="2026-09-27|ARI-SF", market="spread", selection="Arizona Cardinals +7.5", price_decimal=1.9091, status="OPEN"),
               dict(game_key="2026-09-27|LAR-DEN", market="spread", selection="Denver Broncos +2.5", price_decimal=1.8696, status="OPEN")]),
])
db.dashboard_days.insert_one({"_id": D, "picks": [
    {"bet": "Cincinnati Bengals -3.5", "result": "OPEN", "units": None},
    {"bet": "Arizona Cardinals +7.5", "result": "OPEN", "units": None},
    {"bet": "Portugal Moneyline", "result": "OPEN", "units": None}],
    "slips": [{"shape": "NFL cross-game parlay: Arizona +7.5 + Denver +2.5", "result": "OPEN", "units": None,
               "legs": "Arizona Cardinals +7.5 (-110) + Denver Broncos +2.5 (-115)",
               "legs_detail": [{"selection": "Arizona Cardinals +7.5", "status": "OPEN"}, {"selection": "Denver Broncos +2.5", "status": "OPEN"}]}]})

import datetime as _dt
# a fresh pick missing its wrong_if/anchor fields, for the quality check (which looks back 3 days)
db.picks.insert_one(dict(date=_dt.date.today().isoformat(), sport="NFL", matchup="A @ B", bet="A +3.5", bet_type="Spread",
                         stake_units=0.5, price_decimal=1.91, result="OPEN", confidence=53, ev_pct=1.0, book="fanduel"))
for step in ("grade", "close", "audit", "summary"):
    pipeline.STEPS[step](db)

fails = []
def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

g = {p["bet"]: p for p in db.picks.find()}
check(g["Cincinnati Bengals -3.5"]["result"] == "LOSS" and g["Cincinnati Bengals -3.5"]["units"] == -0.5, "Bengals -3.5 graded LOSS -0.5u")
check(g["Arizona Cardinals +7.5"]["result"] == "WIN", "Cardinals +7.5 graded WIN")
check(g["Portugal Moneyline"]["result"] == "WIN" and abs(g["Portugal Moneyline"]["units"] - 0.85) < 1e-6, "Portugal ML WIN +0.85u")
par = g["Parlay: Arizona Cardinals +7.5 + Denver Broncos +2.5"]
check(par["result"] == "WIN" and all(l["status"] == "WIN" for l in par["legs"]), "cross-game parlay WIN from its legs")
check(isinstance(g["Cincinnati Bengals -3.5"].get("clv"), float), f"Bengals got a CLV ({g['Cincinnati Bengals -3.5'].get('clv')}, ledger had 1.83)")
day = db.dashboard_days.find_one({"_id": D})
check([p["result"] for p in day["picks"]] == ["LOSS", "WIN", "WIN"], "dashboard_days picks mirrored")
check(day["slips"][0]["result"] == "WIN" and day["slips"][0]["legs_detail"][1]["status"] == "WIN", "dashboard_days slip + legs mirrored")
par = db.picks.find_one({"bet": "Parlay: Arizona Cardinals +7.5 + Denver Broncos +2.5"})
check((par.get("clv_note") or "").startswith("pipeline: 1 of 2"), f"parlay CLV withheld when a leg's point moved ({par.get('clv_note')})")
audit = list(db.grade_audit.find())
check(len(audit) == 1 and audit[0]["espn_result"] == "LOSS", "audit caught the Sutton SGP misgrade")
s = db.ledger_summary.find_one({"_id": "current"})
check(s and s["adjustment_test"]["all"]["n"] == 3, f"summary adjustment test n=3 ({(s or {}).get('adjustment_test')})")
q = s.get("quality") or {}
gaps = {m["bet"]: m["fields"] for m in (q.get("missing") or [])}
check("A +3.5" in gaps and "wrong_if/falsifier" in gaps["A +3.5"] and "anchor_prob" in gaps["A +3.5"], f"quality check flags the fresh pick's missing fields ({gaps.get('A +3.5')})")
print(f"\n{len(fails)} failures")
sys.exit(1 if fails else 0)

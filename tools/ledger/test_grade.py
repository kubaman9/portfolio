"""Regression test: re-grade picks whose results are already known (from the
ledger) using live ESPN data, and check the pipeline agrees. Needs network.

  python3 tools/ledger/test_grade.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import grade_pick  # noqa: E402

S = lambda date, sport, matchup, bet, bt, exp, stake=0.5, dec=1.909: dict(
    date=date, sport=sport, matchup=matchup, bet=bet, bet_type=bt, stake_units=stake, price_decimal=dec, result="OPEN", _exp=exp)
L = lambda gk, market, sel, dec=1.909: dict(game_key=gk, market=market, selection=sel, price_decimal=dec, status="OPEN")

CASES = [
    S("2026-09-27", "NFL", "Cincinnati Bengals @ Pittsburgh Steelers", "Cincinnati Bengals -3.5", "Spread", "LOSS"),
    S("2026-09-27", "NFL", "Dallas Cowboys @ Baltimore Ravens (International Series, Rio de Janeiro; Dallas designated home)", "Baltimore Ravens -3.5", "Spread", "LOSS"),
    S("2026-09-27", "NFL", "Arizona Cardinals @ San Francisco 49ers", "Arizona Cardinals +7.5", "Spread", "WIN"),
    S("2026-09-27", "NFL", "Los Angeles Rams @ Denver Broncos (SNF)", "Denver Broncos +2.5", "Spread", "WIN"),
    S("2026-09-27", "Soccer", "Norway @ Portugal (UEFA Nations League A, Ullevaal Stadion, Oslo)", "Portugal Moneyline", "Moneyline", "WIN", dec=2.7),
    S("2026-09-26", "CFB", "Texas Longhorns @ Tennessee Volunteers", "Texas -4.5", "Spread", "LOSS"),
    S("2026-09-26", "CFB", "Oregon Ducks @ USC Trojans", "USC +3.5", "Spread", "LOSS"),
    S("2026-09-26", "CFB", "Wisconsin Badgers @ Penn State Nittany Lions", "Penn State -9.5", "Spread", "LOSS"),
    S("2026-09-26", "CFB", "Oklahoma Sooners @ Georgia Bulldogs", "Georgia -13.5", "Spread", "WIN"),
    S("2026-09-26", "CFB", "Missouri Tigers @ Mississippi State Bulldogs", "Mississippi State -4.5", "Spread", "WIN"),
    S("2026-09-26", "CFB", "Ole Miss Rebels @ Florida Gators", "Florida -3.5", "Spread", "WIN"),
    S("2026-09-25", "CFB", "Northwestern Wildcats @ Indiana Hoosiers", "Indiana -20.5", "Spread", "LOSS"),
    S("2026-09-24", "NFL", "Atlanta Falcons @ Green Bay Packers", "Michael Penix Jr. Under 207.5 Passing Yards", "Player Prop", "LOSS"),
    S("2026-09-24", "NFL", "Atlanta Falcons @ Green Bay Packers", "Kaleb Johnson Under 38.5 Rushing Yards", "Player Prop", "WIN"),
    S("2026-09-24", "NFL", "Atlanta Falcons @ Green Bay Packers", "Christian Watson Over 71.5 Receiving Yards", "Player Prop", "WIN"),
    S("2026-09-20", "NFL", "Minnesota Vikings @ Chicago Bears", "Chicago Bears -4.5", "Spread", "LOSS", stake=1),
    S("2026-09-20", "NFL", "Indianapolis Colts @ Kansas City Chiefs", "Total Under 46.5", "Total Under", "LOSS", stake=1),
    S("2026-09-20", "NFL", "Minnesota Vikings @ Chicago Bears", "Caleb Williams Under 230.5 Passing Yards", "Player Prop", "WIN"),
    S("2026-09-20", "NFL", "Green Bay Packers @ New York Jets", "New York Jets +3.5", "Spread", "WIN", stake=1),
    S("2026-09-19", "CFB", "Virginia @ West Virginia", "Total Under 53.5", "Total Under", "LOSS", stake=1),
    S("2026-09-19", "CFB", "New Mexico @ Oklahoma", "New Mexico +21.5", "Spread", "WIN", stake=1),
    S("2026-09-19", "CFB", "LSU Tigers @ Ole Miss Rebels", "Ole Miss +2.5", "Spread", "WIN", stake=1),
    S("2026-09-17", "MLB", "San Diego Padres @ Colorado Rockies", "Over 11 (total)", "Total Over", "PUSH", stake=1),
    S("2026-09-16", "MLB", "Detroit Tigers @ Toronto Blue Jays", "Detroit Tigers Moneyline", "Moneyline", "LOSS", stake=1),
    S("2026-09-16", "MLB", "Chicago White Sox @ Cleveland Guardians", "Cleveland Guardians -1.5 Run Line", "Run Line", "WIN", stake=1),
    S("2026-09-13", "NFL", "Chicago Bears @ Carolina Panthers", "D'Andre Swift Over 62.5 Rush Yards", "Player Prop", "WIN", stake=1),
]
p1 = S("2026-09-27", "NFL", "Arizona +7.5 + Denver +2.5", "Parlay: Arizona Cardinals +7.5 + Denver Broncos +2.5", "Parlay", "WIN", dec=3.5694)
p1["legs"] = [L("2026-09-27|ARI-SF", "spread", "Arizona Cardinals +7.5"), L("2026-09-27|LAR-DEN", "spread", "Denver Broncos +2.5", 1.8696)]
p2 = S("2026-09-27", "NFL", "Denver Broncos @ Los Angeles Rams (SNF, SGP)", "Kyren Williams Over 54.5 rushing yards + Courtland Sutton Under 36.5 receiving yards", "Parlay", "LOSS", dec=3.553)
# ^ the ledger originally said WIN; the box score (Sutton 3-46) makes it a LOSS. Corrected 9/28.
p2["legs"] = [L("2026-09-27|DEN-LAR", "player_rushing_yards", "Kyren Williams Over 54.5", 1.885), L("2026-09-27|DEN-LAR", "player_receiving_yards", "Courtland Sutton Under 36.5", 1.885)]
p3 = S("2026-09-27", "NFL", "Cincinnati Bengals @ Pittsburgh Steelers (SGP)", "Chase Brown Over 63.5 rushing yards + Aaron Rodgers Under 224.5 passing yards", "Parlay", "LOSS", dec=3.553)
p3["legs"] = [L("2026-09-27|CIN-PIT", "player_rushing_yards", "Chase Brown Over 63.5", 1.885), L("2026-09-27|CIN-PIT", "player_passing_yards", "Aaron Rodgers Under 224.5", 1.885)]
p4 = S("2026-09-26", "CFB", "CFB cross-game parlay", "Parlay: Penn State -9.5 + Mississippi State -4.5", "Parlay", "LOSS", dec=3.5)
p4["legs"] = [L("2026-09-26|WISC-PSU", "spread", "Penn State -9.5", 1.8333), L("2026-09-26|MIZ-MSST", "spread", "Mississippi State -4.5")]
p5 = S("2026-09-26", "UFC", "UFC Vegas 121 cross-fight parlay", "Parlay: Montel Jackson ML + Rodolfo Vieira ML", "Parlay", "WIN", dec=2.426)
p5["legs"] = [L("2026-09-26|UFC-SIMON-JACKSON", "fight_winner", "Montel Jackson", 1.5), L("2026-09-26|UFC-VIEIRA-BRYCZEK", "fight_winner", "Rodolfo Vieira", 1.6173)]
CASES += [p1, p2, p3, p4, p5,
          S("2026-09-26", "UFC", "Ricky Simon vs Montel Jackson (UFC Vegas 121)", "Montel Jackson Moneyline", "Fight Winner", "WIN", dec=1.5),
          S("2026-09-26", "UFC", "Raul Rosas Jr. vs Raoni Barcelos (UFC Vegas 121, main event)", "Raoni Barcelos Moneyline", "Fight Winner", "LOSS", stake=0.25, dec=2.36),
          S("2026-09-19", "UFC", "Joshua Van vs Alexandre Pantoja (UFC 331 Main Event)", "Alexandre Pantoja Moneyline", "Fight Winner", "LOSS", dec=2.14),
          # MLB props against the 9/26 Mets @ Nationals box score (Tong 5.0 IP, 9 K; Lindor 0-4)
          S("2026-09-26", "MLB", "New York Mets @ Washington Nationals", "Jonah Tong Over 7.5 Strikeouts", "Player Prop", "WIN", dec=1.9),
          S("2026-09-26", "MLB", "New York Mets @ Washington Nationals", "Jonah Tong Over 15.5 Outs Recorded", "Player Prop", "LOSS", dec=1.9),
          S("2026-09-26", "MLB", "New York Mets @ Washington Nationals", "Francisco Lindor Over 0.5 Hits", "Player Prop", "LOSS", dec=1.9),
          # soccer scorer/assist props against the 9/27 Norway-Portugal match report
          S("2026-09-27", "Soccer", "Norway @ Portugal (UEFA Nations League A)", "João Félix Anytime Goalscorer", "Player Prop", "WIN", dec=2.5),
          S("2026-09-27", "Soccer", "Norway @ Portugal (UEFA Nations League A)", "Pedro Neto Anytime Assist", "Player Prop", "WIN", dec=2.5),
          # NHL props, 4/12 Penguins @ Capitals (Brazeau 2 shots, both missed: 0 SOG; Skinner 24 saves)
          S("2026-04-12", "NHL", "Pittsburgh Penguins @ Washington Capitals", "Justin Brazeau Over 1.5 Shots on Goal", "Player Prop", "LOSS", dec=1.9),
          S("2026-04-12", "NHL", "Pittsburgh Penguins @ Washington Capitals", "Stuart Skinner Over 25.5 Saves", "Player Prop", "LOSS", dec=1.9)]


def main():
    ok = bad = skipped = 0
    for c in CASES:
        exp = c.pop("_exp")
        try:
            u = grade_pick(c)
        except Exception as e:  # network trouble shows as a skip, not a pass
            u = None
            print(f"ERROR {c['bet']}: {e}")
        got = (u or {}).get("result")
        if got is None:
            skipped += 1
            print(f"SKIP  {c['date']} {c['bet']}")
        elif got == exp:
            ok += 1
            print(f"ok    {c['date']} {c['bet']} -> {got} {u.get('units')}")
        else:
            bad += 1
            print(f"WRONG {c['date']} {c['bet']} -> {got}, ledger says {exp}")
    print(f"\n{ok} agree, {bad} disagree, {skipped} not graded (left for the run)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

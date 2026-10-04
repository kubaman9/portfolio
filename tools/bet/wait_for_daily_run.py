#!/usr/bin/env python3
"""Block until today's daily Claude run has finished writing the card, so the site is
published once per morning instead of rebuilding all day.

  MONGODB_URI=... python3 tools/bet/wait_for_daily_run.py [--until-et 07:30] [--every 120] [--check]

"Finished" = a runs document dated today (ET) with status "completed" that is not the
weekly review. Exits 0 when it sees one, or when the deadline passes (the site then
publishes whatever Mongo holds, so a slow or failed run never blocks the morning page).
"""
import argparse
import datetime as dt
import os
import sys
import time
from zoneinfo import ZoneInfo

from pymongo import MongoClient

ET = ZoneInfo("America/New_York")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--until-et", default="07:30", help="give up waiting at this ET time (HH:MM)")
    ap.add_argument("--every", type=int, default=120, help="seconds between checks")
    ap.add_argument("--check", action="store_true",
                    help="no waiting: exit 0 if today's run finished (or the deadline passed), else exit 3")
    a = ap.parse_args()
    uri = (os.environ.get("MONGODB_URI") or "").strip().strip('"').strip("'")
    db = MongoClient(uri, serverSelectionTimeoutMS=20000)["betting_agent"]
    now = dt.datetime.now(ET)
    hh, mm = (int(x) for x in a.until_et.split(":"))
    deadline = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    today = now.date().isoformat()
    while True:
        run = db.runs.find_one({"date": today, "status": "completed", "kind": {"$ne": "weekly_review"}},
                               {"run_id": 1, "completed_at": 1})
        if run:
            print(f"daily run finished: {run.get('run_id') or run['_id']} (completed_at {run.get('completed_at')})")
            return
        if dt.datetime.now(ET) >= deadline:
            print(f"::warning::no completed daily run for {today} by {a.until_et} ET; publishing what Mongo holds")
            return
        if a.check:
            print(f"{dt.datetime.now(ET):%H:%M} ET: today's daily run has not finished yet")
            sys.exit(3)
        print(f"{dt.datetime.now(ET):%H:%M} ET: waiting for today's daily run to finish")
        sys.stdout.flush()
        time.sleep(a.every)


if __name__ == "__main__":
    main()

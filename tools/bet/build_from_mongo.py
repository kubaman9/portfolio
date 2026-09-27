#!/usr/bin/env python3
"""Export the dashboard from Mongo and build bet/index.html with make_bet.py.

Used by .github/workflows/build-bet.yml so the daily Claude run only has to write
Mongo -- it never needs git access to this repo.

  MONGODB_URI=... python3 tools/bet/build_from_mongo.py --out bet/index.html \
      [--existing path/to/current/index.html]

Passphrase: BET_PAGE_PASSPHRASE from the environment if set, otherwise
betting_agent.site_config.current.page_passphrase.

With --existing, the build is skipped (exit 0, prints "unchanged") when the
content hash matches the page already published, so a frequent cron only
commits when the data actually changed.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

from pymongo import MongoClient

HERE = os.path.dirname(os.path.abspath(__file__))


def src_hash_of(path):
    try:
        m = re.search(r'<meta name="bet-src" content="([0-9a-f]+)">', open(path, encoding="utf-8").read())
        return m.group(1) if m else None
    except FileNotFoundError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--existing", default=None)
    args = ap.parse_args()

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        print("BUILD REFUSED: MONGODB_URI is not set", file=sys.stderr)
        sys.exit(1)

    db = MongoClient(uri, serverSelectionTimeoutMS=20000)["betting_agent"]
    tpl = db.dashboard_template.find_one({"_id": "current"})
    index = db.dashboard_index.find_one({"_id": "meta"})
    cfg = db.site_config.find_one({"_id": "current"}) or {}
    if not tpl or not index:
        print("BUILD REFUSED: dashboard_template/current or dashboard_index/meta missing", file=sys.stderr)
        sys.exit(1)

    days = {}
    for d in db.dashboard_days.find({"superseded": {"$ne": True}}):
        date = d.pop("_id")
        days[str(date)] = d
    index.pop("_id", None)

    passphrase = os.environ.get("BET_PAGE_PASSPHRASE") or cfg.get("page_passphrase")
    if not passphrase:
        print("BUILD REFUSED: no passphrase in env or site_config.page_passphrase", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        shell_p = os.path.join(tmp, "shell.html")
        arch_p = os.path.join(tmp, "archive.json")
        out_p = os.path.join(tmp, "index.html")
        open(shell_p, "w", encoding="utf-8").write(tpl["html_shell"])
        json.dump({"index": index, "days": days}, open(arch_p, "w", encoding="utf-8"),
                  ensure_ascii=False, default=str)

        env = dict(os.environ, BET_PAGE_PASSPHRASE=passphrase)
        r = subprocess.run([sys.executable, os.path.join(HERE, "make_bet.py"),
                            "--template", shell_p, "--archive", arch_p, "--out", out_p], env=env)
        if r.returncode != 0:
            sys.exit(r.returncode)

        if args.existing and src_hash_of(args.existing) == src_hash_of(out_p):
            print("unchanged")
            return

        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(out_p, encoding="utf-8") as src, open(args.out, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    print(f"built {args.out} with {len(days)} days, latest={index.get('latest_day')}")


if __name__ == "__main__":
    main()

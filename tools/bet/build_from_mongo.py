#!/usr/bin/env python3
"""Export the dashboard from Mongo and build bet/index.html with make_bet.py.

Used by .github/workflows/build-bet.yml so the daily Claude run only has to write
Mongo -- it never needs git access to this repo.

  MONGODB_URI=... python3 tools/bet/build_from_mongo.py --out bet/index.html \
      [--existing path/to/current/index.html]

Passphrase: BET_PAGE_PASSPHRASE from the environment if set, otherwise
betting_agent.site_config.current.page_passphrase.

Design (dashboard_template/current.html_shell) can be changed from two places:
  - the daily run edits html_shell in Mongo when it decides the page needs work;
  - a person edits tools/bet/template.html in the repo (--template-file).
The repo file wins only when it has changed since the last sync (tracked by
repo_hash), so a run's Mongo edit is not overwritten by an untouched repo copy.
Before building, the chosen shell is checked (placeholder exactly once, and the
inline JavaScript parses with `node --check`). If the Mongo shell fails that check
or the build, the repo file is used instead so the site never breaks, and the error
is written to dashboard_template/current.last_build for the next run to fix.

With --existing, the build is skipped (exit 0, prints "unchanged") when the
content hash matches the page already published, so a frequent cron only
commits when the data actually changed.
"""
import argparse
import datetime
import hashlib
import shutil
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


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def shell_problem(shell):
    """Cheap pre-build checks for a template; returns an error string or None."""
    if not shell:
        return "html_shell is empty"
    if shell.count("__ARCHIVE_JSON__") != 1:
        return "__ARCHIVE_JSON__ must appear exactly once"
    node = shutil.which("node")
    if node:
        js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", shell, re.S)).replace("__ARCHIVE_JSON__", "{}", 1)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
            path = f.name
        r = subprocess.run([node, "--check", path], capture_output=True, text=True)
        os.unlink(path)
        if r.returncode != 0:
            lines = [l for l in (r.stderr or "").splitlines() if "Error" in l]
            return "JavaScript syntax error: " + (lines[0] if lines else "node --check failed")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--existing", default=None)
    ap.add_argument("--template-file", default=None)
    args = ap.parse_args()

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        print("BUILD REFUSED: MONGODB_URI is not set", file=sys.stderr)
        sys.exit(1)

    uri = uri.strip().strip('"').strip("'")
    if not uri.startswith(("mongodb+srv://", "mongodb://")) or "@" not in uri:
        # Never echo the value: the Actions log is public.
        print("BUILD REFUSED: MONGODB_URI must be the full connection string "
              "(mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/...), not just a password",
              file=sys.stderr)
        sys.exit(1)

    try:
        db = MongoClient(uri, serverSelectionTimeoutMS=20000)["betting_agent"]
        tpl = db.dashboard_template.find_one({"_id": "current"})
    except Exception as e:
        # Driver errors can include hosts or credentials, so only print the error class.
        print(f"BUILD REFUSED: could not read Mongo ({type(e).__name__}) -- check the "
              "MONGODB_URI user/password and Atlas Network Access", file=sys.stderr)
        sys.exit(1)
    repo_shell = None
    if args.template_file and os.path.exists(args.template_file):
        repo_shell = open(args.template_file, encoding="utf-8").read()
    tpl = tpl or {}
    shell, used = tpl.get("html_shell"), tpl.get("source") or "mongo"
    if repo_shell is not None and tpl.get("repo_hash") != sha(repo_shell) and not shell_problem(repo_shell):
        # The repo copy was edited by a person since the last sync (or this is the
        # first sync): it replaces the Mongo design, keeping the old one for rollback.
        update = {"html_shell": repo_shell, "repo_hash": sha(repo_shell), "source": "repo",
                  "updated_at": now_iso()}
        if shell and shell != repo_shell:
            update["previous_html_shell"] = shell
        db.dashboard_template.update_one({"_id": "current"}, {"$set": update}, upsert=True)
        print("template synced from repo into dashboard_template/current", file=sys.stderr)
        shell, used = repo_shell, "repo"
    fallback_reason = shell_problem(shell)
    if fallback_reason and repo_shell and shell != repo_shell:
        print(f"WARNING: Mongo template rejected ({fallback_reason}); building from the repo copy", file=sys.stderr)
        shell, used = repo_shell, "repo (fallback)"
    elif fallback_reason:
        print(f"BUILD REFUSED: template unusable ({fallback_reason})", file=sys.stderr)
        sys.exit(1)
    else:
        fallback_reason = None
    tpl = {"html_shell": shell}
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
    ledger = db.ledger_summary.find_one({"_id": "current"})
    if ledger:  # exact numbers from tools/ledger/pipeline.py for the page
        ledger.pop("_id", None)
        index["ledger"] = ledger

    public = cfg.get("public_page") is True or os.environ.get("BET_PUBLIC") == "1"
    passphrase = os.environ.get("BET_PAGE_PASSPHRASE") or cfg.get("page_passphrase")
    if not passphrase and not public:
        print("BUILD REFUSED: no passphrase in env or site_config.page_passphrase", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        shell_p = os.path.join(tmp, "shell.html")
        arch_p = os.path.join(tmp, "archive.json")
        out_p = os.path.join(tmp, "index.html")
        open(shell_p, "w", encoding="utf-8").write(tpl["html_shell"])
        json.dump({"index": index, "days": days}, open(arch_p, "w", encoding="utf-8"),
                  ensure_ascii=False, default=str)

        env = dict(os.environ, BET_PAGE_PASSPHRASE=passphrase or "")
        cmd = [sys.executable, os.path.join(HERE, "make_bet.py"), "--template", shell_p, "--archive", arch_p, "--out", out_p]
        if public:
            cmd.append("--public")
        run = lambda: subprocess.run(cmd, env=env)
        r = run()
        if r.returncode != 0 and repo_shell and used != "repo" and not used.startswith("repo (") and tpl["html_shell"] != repo_shell:
            fallback_reason = "make_bet.py refused the Mongo template"
            print(f"WARNING: {fallback_reason}; building from the repo copy", file=sys.stderr)
            open(shell_p, "w", encoding="utf-8").write(repo_shell)
            used = "repo (fallback)"
            r = run()
        db.dashboard_template.update_one({"_id": "current"}, {"$set": {"last_build": {
            "at": now_iso(), "ok": r.returncode == 0, "used": used, "error": fallback_reason}}})
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

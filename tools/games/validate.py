#!/usr/bin/env python3
"""Check public/games/games.json before it is published.

Usage: python3 tools/games/validate.py [path] [--check-links]
Exits nonzero with a message on the first problem it finds.
"""
import json, re, sys, urllib.request

ALLOWED_TAGS = {"top10", "rarity", "draft", "sports", "geo", "connections", "sporcle", "estimate", "daily"}
REQUIRED = ("id", "name", "url", "blurb", "tags", "added", "source")


def fail(msg):
    print(f"games.json invalid: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else "public/games/games.json"
    try:
        data = json.load(open(path))
    except Exception as e:
        fail(f"cannot parse {path}: {e}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data.get("updated", ""))):
        fail("'updated' must be YYYY-MM-DD")
    games = data.get("games")
    if not isinstance(games, list) or len(games) < 5:
        fail("'games' must be a list with at least 5 entries (refusing a near-empty list)")
    ids, urls = set(), set()
    for i, g in enumerate(games):
        where = f"games[{i}] ({g.get('name', '?')})"
        for k in REQUIRED:
            if not g.get(k):
                fail(f"{where} is missing '{k}'")
        if g["id"] in ids:
            fail(f"{where} duplicate id {g['id']}")
        ids.add(g["id"])
        if not re.fullmatch(r"[a-z0-9-]+", g["id"]):
            fail(f"{where} id must be lowercase letters, digits and dashes")
        if not g["url"].startswith("https://"):
            fail(f"{where} url must be https")
        key = g["url"].rstrip("/").lower()
        if key in urls:
            fail(f"{where} duplicate url {g['url']}")
        urls.add(key)
        bad = set(g["tags"]) - ALLOWED_TAGS
        if bad:
            fail(f"{where} unknown tags {sorted(bad)} (allowed: {sorted(ALLOWED_TAGS)})")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", g["added"]):
            fail(f"{where} 'added' must be YYYY-MM-DD")
        if len(g["blurb"]) > 140:
            fail(f"{where} blurb is over 140 characters")
        if re.search(r"<|>", json.dumps(g)):
            fail(f"{where} contains angle brackets")

    if "--check-links" in sys.argv:
        dead = []
        for g in games:
            if g.get("needsLink"):
                continue
            try:
                req = urllib.request.Request(g["url"], headers={"User-Agent": "Mozilla/5.0 (games-link-check)"})
                code = urllib.request.urlopen(req, timeout=15).status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception as e:
                code = type(e).__name__
            # 403/429 usually means bot protection (Sporcle, Cloudflare), not a dead site.
            if code not in (200, 403, 429):
                dead.append(f"{g['name']}: {code}")
        if dead:
            print("possibly dead links:\n  " + "\n  ".join(dead))
    print(f"ok: {len(games)} games")


if __name__ == "__main__":
    main()

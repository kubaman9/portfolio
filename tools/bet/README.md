# /bet — betting dashboard

`bet/index.html` (served at `/bet/` on gh-pages, mirrored into `public/bet/`
on `main`) is **generated output**. Do not hand-edit it — the next build
overwrites it.

## Where things actually live

Everything is in MongoDB Atlas, project **BettingBot**, cluster `Cluster0`,
database `betting_agent`:

- **`dashboard_template`** (`_id: "current"`) — the page's HTML/CSS/JS, doctype
  through `</html>`, containing the literal token `__ARCHIVE_JSON__`. This is
  the source of truth for how the dashboard looks and behaves. **Edit the
  dashboard here, not in this repo.**
- **`dashboard_days`** (`_id: "YYYY-MM-DD"`) — one snapshot per run.
- **`dashboard_index`** (`_id: "meta"`) — the rolled-up stats Home renders
  from: KPI tiles, EV/thesis/anchor bands, per-bet-type and per-sport
  breakdowns, and the archive day list.
- **`site_config`** (`_id: "current"`) — repo/branch/push-mode bookkeeping.
  Never holds secrets.

## Build

```
export BET_PAGE_PASSPHRASE=...   # never commit this, never write it to Mongo
python3 tools/bet/make_bet.py --template shell.html --archive archive.json --out bet/index.html
```

`shell.html` and `archive.json` are local files the daily run exports from
Mongo before calling this script — `make_bet.py` itself needs no DB
credentials, only those two files and the passphrase.

The build refuses (loud, nonzero exit) if: the passphrase is unset, the
`__ARCHIVE_JSON__` placeholder is missing or wasn't substituted, the archive
has zero days, the output is unrealistically small, the password form or
ciphertext blob is missing from the output, or any known matchup/team name or
the word "units" is found in the final file **outside** the ciphertext. That
last check is the one that matters — it's what stops a substitution bug from
publishing the whole ledger in plaintext to a public repo, permanently, in
git history.

## Publish

**Automatic (recommended):** `.github/workflows/build-bet.yml` rebuilds from Mongo
on a schedule (every 10 min after the 3am and 4pm ET runs, hourly otherwise) via
`tools/bet/build_from_mongo.py` and publishes only when the content hash changed.
The daily Claude run then only has to write Mongo and never needs git access.
It needs one repo secret, `MONGODB_URI`, for a read-only user on `betting_agent`,
and the Atlas network access list has to allow GitHub's runners. Until the secret
exists, the workflow logs a warning and exits cleanly.

The secret must be the full driver string, not the `mongosh` command Atlas shows:
`mongodb+srv://USER:PASSWORD@cluster0.xn5vg0j.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
(URL-encode `@ : / ? # %` in the password, or use a letters-and-digits password).
`OperationFailure` in the log means the user/password was rejected; a timeout
means the host is wrong or Network Access is blocking the runner.

**Design:** the page design lives in `dashboard_template/current.html_shell` and can
be changed two ways. The daily run may edit it in Mongo when it thinks the page
needs work (it keeps the old one in `previous_html_shell`). Editing
`tools/bet/template.html` in the repo also works: the Action pushes that file into
Mongo whenever the file changes (tracked by `repo_hash`), and otherwise leaves the
run's edits alone. Every build checks the template first (placeholder present, inline
JS parses); a broken Mongo design falls back to the repo copy so the site stays up, and
`dashboard_template/current.last_build` records what was used and why.

The two paths below are fallbacks.


Two paths, both mirror into `public/bet/index.html` on `main` (so a later
`npm run deploy`, which rebuilds `dist/` from `main` and republishes
`gh-pages`, doesn't wipe `/bet`):

- **Staging** (`.github/workflows/publish-bet.yml`) — push `bet/index.html`
  to `claude/bet-data`; the Action copies it onto `gh-pages` and mirrors it
  into `main`. This is what the daily scheduled run uses, since Routines can
  only push to `claude/*` branches by default.
- **Direct** — if the pushing session has unrestricted branch access, write
  both branches directly instead and set `site_config.push_mode` to
  `"direct"`.

## Honest limits

The password gate stops search engines and casual visitors. It is **not**
access control: the ciphertext ships to every visitor's browser and can be
attacked offline, and a short passphrase falls in well under a second. Fine
for picks and a running record; pick the passphrase length accordingly.

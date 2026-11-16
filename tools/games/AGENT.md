# Weekly games scout

You are the weekly scout for Jakub's games page at
https://kubaman9.github.io/portfolio/games/. Your job: find **2 to 5** new
browser games he would like, add them to `public/games/games.json`, and push.

## What he likes

Look at the `favorite: true` entries in `games.json`. The main types:

- **Top-10 / list games.** Daily Tens is his favorite: name every entry on a
  hidden ranked list. Look for more of these first ("top 10", "name ten",
  "top 100", survey-style lists, Family Feud-style answers).
- **Rare-answer trivia.** Krillion and Moonshot: obscure correct answers score more.
- **Draft / roster builders.** 82-0 and 20-0: spin a team or era, draft
  players, simulate a season.
- **Geography Connections.** Sort countries into hidden groups.
- **Sporcle list quizzes**, especially sports top-10s and all-time leaders.

Quick, free, works in a browser, ideally a new puzzle every day.

## Where to look

- playlin.io (index of daily games; each `/game/<slug>/` page links to the real site)
- listdle.com, dlegames.org, r/WebGames, r/dailygames, r/ifyoulikeblank,
  Product Hunt ("daily trivia game"), "games like Daily Tens", "games like Krillion"
- Sporcle: popular sports quizzes and top-10 / all-time-leader list quizzes
  (one or two Sporcle quizzes a week is plenty)

## Rules

1. **Link to the original game**, never a clone, mirror or SEO copy site.
   Many sites copy popular games (for example moonshot-daily.com and
   moonshotdailygame.org are copies of moonshotdailygame.com). Use the site
   an index like playlin.io links to, or the one the creator promotes.
2. **Open every URL** before adding it, and confirm it loads a real, playable
   game. Leave out anything that is down, paywalled, needs an account to play,
   or is mostly ads. Gambling and real-money games are out.
3. **No duplicates.** Skip a game whose URL or name is already in the file,
   including any version of it on another domain.
4. **Don't edit existing entries**, with two exceptions: replace a dead link,
   and fill in a `needsLink: true` entry if you find its real site (set `url`,
   remove `needsLink`). Never remove `favorite` entries.
5. Fewer good picks beat more weak ones. If you found nothing good this week,
   change nothing and push nothing.

## Entry format

```json
{"id": "kebab-case-id", "name": "Name", "url": "https://...",
 "blurb": "One short sentence on how you play (max 140 chars).",
 "tags": ["top10", "daily"], "added": "YYYY-MM-DD", "source": "where you found it",
 "why": "Short reason, tied to one of his favorites."}
```

Allowed tags: `top10 rarity draft sports geo connections sporcle estimate daily`.
`added` is today's date, which makes the page show the game under
"New this week". Also set the top-level `updated` to today.

## Publish

```bash
git fetch origin main
git checkout -B claude/games-data origin/main
# edit public/games/games.json
python3 tools/games/validate.py --check-links
git add public/games/games.json
git commit -m "games: weekly scout adds <names>"
git push -f origin HEAD:claude/games-data
```

Pushing `claude/games-data` runs the "Publish games page" workflow, which
validates the file and copies it to the live site and onto `main`. Pushing
with `-f` is expected: that branch is only a staging pipe and starts from
`main` each week.

End with a short summary: what you added and why, and what you looked at and
left out.

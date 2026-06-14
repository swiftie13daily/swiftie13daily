# Swiftie13Daily — automated daily quiz bot

An unofficial Taylor Swift fan page bot: posts one quiz card to Instagram
every day, with the answer revealed in the next day's caption.

## Folder layout
- `content/queue.json` — upcoming quizzes. Only items with `"approved": true` get posted.
- `content/history.json` — auto-created; everything already posted.
- `main.py` — daily orchestrator (`--render-only` / `--publish-only` flags).
- `render_card.py` — turns a quiz item into a branded 1080x1080 PNG (era color palettes).
- `generate_content.py` — batch-generates new quizzes with the Claude API (`python generate_content.py 30`).
- `post_instagram.py` — publishes via the official Instagram API (GitHub Actions route only).
- `.github/workflows/daily_post.yml` — fully unattended daily posting via GitHub Actions.
- `PROJECT.md` — add this yourself: project context + rules for Claude Cowork.

## Route A — Claude Cowork (easiest, no developer setup)
1. Create the Instagram account (@swiftie13daily), switch to a Creator
   account, enable two-factor auth.
2. Log into the account in Chrome and install the Claude in Chrome extension.
3. Put this folder at `~/Documents/swiftie13daily` and add your PROJECT.md.
4. Test locally once: `pip install -r requirements.txt` then
   `python main.py --render-only` — check the card in `output/posts/`.
5. In Claude Cowork, create the daily posting task and the weekly content
   refill task, and /schedule them.

Cowork uses the browser to post, so the API modules and GitHub workflow are
not needed for this route — but keep them; they're your upgrade path.

## Route B — GitHub Actions (unattended, runs even when your laptop is off)
1. Create a PUBLIC GitHub repo and push this folder to it. (Public is needed
   because Instagram fetches the rendered image from the repo's raw URL.
   Never commit tokens — they live only in repo Secrets.)
2. Instagram side: convert the account to a professional account, create a
   Meta developer app, and get a long-lived access token plus your numeric
   IG user ID. Follow Meta's current "Instagram Platform / content
   publishing" docs — the exact permission names change over time. Either
   the Instagram-Login route (no Facebook Page) or the Facebook-Page route
   works; set GRAPH_HOST accordingly.
3. In the repo: Settings → Secrets and variables → Actions. Add secrets:
   `ANTHROPIC_API_KEY`, `IG_USER_ID`, `IG_ACCESS_TOKEN`.
4. Generate content: `python generate_content.py 30`, review the new items
   in `content/queue.json`, set `"approved": true` on the good ones, commit.
5. The workflow posts daily at 16:00 UTC (edit the cron in
   `.github/workflows/daily_post.yml`). Trigger a test run from the
   Actions tab with "Run workflow".

Note: long-lived Instagram tokens expire (~60 days) — refresh per Meta's
docs and update the secret. Set a calendar reminder.

## Costs
- GitHub Actions: free tier is more than enough.
- Claude API: a batch of 30 quizzes costs cents.
- Everything else: free.

## Content rules baked in
No song lyrics, no official photos, facts only, respectful tone, and an
"unofficial fan page" disclaimer. Keep it that way — it's what keeps a fan
page safe.

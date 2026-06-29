# Using a Google Sheet as the vote database (one-off)

This wires the live site to a Google Sheet via a small Apps Script web app. No
server or paid database — good enough to collect votes from many people for a
while. If traffic gets heavy, switch to Postgres (just set `POSTGRES_URL`
instead; everything else is identical).

**How it fits together:** browser → your Vercel site (`/api/*`) → Apps Script
web app → Google Sheet. The secret token lives only in Vercel's environment, so
visitors never see it.

## 1. Create the Sheet

1. New Google Sheet (name it e.g. "FF6 Coliseum Votes").
2. You can leave it empty — the script creates a **Votes** tab with headers
   (`ts, voter, name, winner, loser`) on first write.

## 2. Add the Apps Script

1. In the Sheet: **Extensions → Apps Script**.
2. Delete the placeholder, paste the contents of [`Code.gs`](Code.gs), **Save**.
3. Set the shared secret: **Project Settings (gear) → Script Properties → Add
   property**: name `TOKEN`, value = a random string (e.g. from a password
   generator). Save. *(Keep this value — Vercel needs the same one.)*

## 3. Deploy as a Web App

1. **Deploy → New deployment → ⚙ → Web app**.
2. Description: anything. **Execute as: Me**. **Who has access: Anyone**.
   *(“Anyone” lets your server call it; the `TOKEN` is what actually guards
   writes.)*
3. **Deploy**, authorize when prompted, and copy the **Web app URL** — it ends
   in `/exec`.

> Re-deploying after code edits: use **Manage deployments → edit → Version: New
> version** so the URL stays the same.

## 4. Point Vercel at it

In your Vercel project: **Settings → Environment Variables**, add:

| Name | Value |
|---|---|
| `SHEETS_WEBAPP_URL` | the `…/exec` URL from step 3 |
| `SHEETS_TOKEN` | the same `TOKEN` string from step 2 |

Optionally `SHEETS_TTL` (seconds the server caches the vote log; default `15`).

**Redeploy** the Vercel project (env-var changes need a new deployment). Done —
votes now land in your Sheet, and the live tier list / leaderboard are computed
from it.

## Verify / troubleshoot

Open **`https://your-site/api/health`** — it tells you exactly what's wrong:

- `"backend": "SQLiteStore"` → the env vars didn't reach this deployment. Make
  sure `SHEETS_WEBAPP_URL` is set for the **Production** environment and that you
  **redeployed** after adding it. (`"backend": "SheetsStore"` is what you want.)
- `"can_read": false` with an `error` mentioning **HTML** → the web app's
  "Who has access" isn't **Anyone**; redeploy it that way.
- `error` mentioning **token** → `SHEETS_TOKEN` (Vercel) ≠ `TOKEN` (Script
  Property). Make them identical.
- `"can_read": true` → reads work. Then hit
  **`/api/health?write=1`**: it appends a `healthcheck` row. If `can_write` is
  true a row should appear in the sheet (delete it after); if false, the `error`
  explains why.

Once healthy:
- Cast a vote on the site → a new row appears in the **Votes** tab.
- `https://your-site/api/stats` shows the rising `total_votes`.
- `https://your-site/api/leaderboard` lists voters once some have 10+ votes.

## Notes

- **Privacy:** rows store an anonymous random `voter` id and whatever optional
  display name people type — no accounts, no PII.
- **Scale:** the server reads the whole sheet (cached for `SHEETS_TTL`s) and
  replays it. Fine for thousands of votes; tens of thousands is the point to
  move to Postgres.
- **Reset:** to start fresh, clear the Votes tab (keep the header row).
- **Tally offline:** `File → Download → CSV`, or run
  `python tools/build_tier_list.py` locally with `SHEETS_WEBAPP_URL` /
  `SHEETS_TOKEN` set in your shell to export the tier list.

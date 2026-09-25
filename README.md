# Deep Vein — Telegram Tap-to-Mine Mini App

A production-ready starter for a Telegram Mini App "mining" game:
tap to earn coins, referral bonuses, a 7-day daily streak, and a leaderboard.

```
telegram-mining-app/
  backend/    FastAPI + SQLAlchemy API (SQLite by default, Postgres-ready)
  frontend/   Plain HTML/CSS/JS Telegram Mini App
```

## 1. Create your bot

1. Open Telegram, message **@BotFather**, run `/newbot`, follow the prompts.
2. Save the **bot token** it gives you — it goes in `backend/.env` as `BOT_TOKEN`.
3. Run `/newapp` (or `/mybots` → your bot → **Bot Settings** → **Mini App**) and set the
   Mini App URL to wherever you host the `frontend/` folder (step 3 below).
4. Note your bot's `@username` — you'll need it in `frontend/app.js`.

## 2. Run the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and paste your BOT_TOKEN
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

This uses SQLite (`mining.db`, created automatically) so there's nothing else to install
locally. For real traffic, set `DATABASE_URL` in `.env` to a Postgres connection string —
no code changes needed, SQLAlchemy handles both.

Deploy the backend anywhere that runs Python (Railway, Render, Fly.io, a VPS + `gunicorn`).
It must be reachable over **HTTPS** — Telegram Mini Apps refuse plain HTTP.

## 3. Host the frontend

The `frontend/` folder is static — deploy it to any static host (Vercel, Netlify, GitHub
Pages, Cloudflare Pages), also over HTTPS.

Before deploying, edit the top of `frontend/app.js`:

```js
const API_BASE = "https://your-backend-domain.com"; // your backend from step 2
const BOT_USERNAME = "your_bot_username";            // no @
```

Paste the resulting frontend URL into BotFather's Mini App URL setting from step 1.

## 4. Try it

Open your bot in Telegram and tap the Mini App button (or its menu button). Tapping the
rock spends energy and adds coins; energy regenerates over time; the Daily tab pays out
a streak bonus every 24 hours; the Invite tab gives you a link that credits you 500 ORE
the first time each friend opens it; the Ranks tab shows the top 50 balances.

## How the pieces fit together

- **Security**: every API call is verified in `backend/auth.py` against Telegram's HMAC
  signature for `initData`. Without a valid `BOT_TOKEN`, requests are rejected — this is
  what stops someone from calling your API pretending to be another user.
- **Energy & mining**: `backend/models.py` holds the tunable constants (max energy, coins
  per tap, referral bonus, daily reward). Energy regenerates server-side based on elapsed
  time, so it can't be reset by refreshing the page.
- **Referrals**: a Mini App link like `https://t.me/yourbot?startapp=CODE` passes `CODE`
  through as `start_param`; the backend credits the referrer the first time the new user
  is created.
- **Anti-abuse**: taps are clamped per request and coins/energy are only ever changed
  server-side — the frontend's instant feedback is just a local guess that gets corrected
  on the next sync.

## Reasonable next steps

- Add upgrades (e.g. coins-per-tap or max-energy boosts bought with coins).
- Add Telegram Stars or a payment provider if you want real monetization.
- Put the backend behind a rate limiter (e.g. `slowapi`) in front of `/api/tap`.
- Swap SQLite for Postgres before real user volume — see `backend/database.py`.


## Render deployment
See `RENDER_DEPLOY.md` and `render.yaml`. Production should use Render PostgreSQL rather than SQLite.

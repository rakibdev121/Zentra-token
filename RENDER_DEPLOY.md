# Render deployment

## Backend Web Service
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health Check: `/api/health`

Required environment variables:
- `BOT_TOKEN` = Telegram bot token from BotFather
- `DATABASE_URL` = Render Postgres connection string
- `CORS_ORIGINS` = frontend Render URL, e.g. `https://raki-mining-frontend.onrender.com`

## Database
Use Render PostgreSQL for production. Do not rely on the local SQLite database because a Render service filesystem is not persistent across deploys/restarts.

## Frontend
After the backend URL is known, edit `frontend/app.js`:
`API_BASE = "https://YOUR-RENDER-BACKEND.onrender.com"`

Also replace:
`BOT_USERNAME = "YOUR_BOT_USERNAME"`

Then push to GitHub and redeploy the static site.

## Important
This project is still the original mining starter app. It does NOT yet include the RAKI token wallet/withdraw/admin system.

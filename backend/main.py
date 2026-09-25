import math
import secrets
import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_telegram_user
from database import Base, SessionLocal, engine, get_db
from models import (
    DAILY_BASE_REWARD,
    DAILY_STREAK_CAP,
    ENERGY_REGEN_PER_SEC,
    MAX_ENERGY,
    REFERRAL_BONUS_COINS,
    User,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Telegram Mining Mini App")

# Comma-separated frontend origins. Keep "*" only for temporary testing.
cors_origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- helpers ----------

def _sync_energy(user: User) -> None:
    """Regenerate energy based on elapsed real time, capped at MAX_ENERGY."""
    now = datetime.utcnow()
    elapsed = (now - user.last_energy_update).total_seconds()
    if elapsed > 0:
        user.energy = min(MAX_ENERGY, user.energy + elapsed * ENERGY_REGEN_PER_SEC)
        user.last_energy_update = now


def _user_out(user: User) -> dict:
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "coins": round(user.coins, 2),
        "energy": math.floor(user.energy),
        "max_energy": MAX_ENERGY,
        "referral_code": user.referral_code,
        "referral_count": user.referral_count,
        "daily_streak": user.daily_streak,
        "can_claim_daily": _can_claim_daily(user),
    }


def _can_claim_daily(user: User) -> bool:
    if user.last_daily_claim is None:
        return True
    return (datetime.utcnow() - user.last_daily_claim).total_seconds() >= 24 * 3600


def _get_or_create_user(db: Session, tg_user: dict) -> User:
    telegram_id = tg_user["id"]
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        return user

    user = User(
        telegram_id=telegram_id,
        username=tg_user.get("username"),
        first_name=tg_user.get("first_name"),
        referral_code=secrets.token_hex(4),
    )

    start_param = tg_user.get("_start_param")
    if start_param:
        referrer = db.query(User).filter(User.referral_code == start_param).first()
        if referrer and referrer.telegram_id != telegram_id:
            user.referred_by_id = referrer.id
            referrer.coins += REFERRAL_BONUS_COINS
            referrer.referral_count += 1
            db.add(referrer)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- schemas ----------

class TapRequest(BaseModel):
    taps: int = 1


# ---------- routes ----------

@app.get("/api/me")
def me(tg_user: dict = Depends(get_telegram_user), db: Session = Depends(get_db)):
    user = _get_or_create_user(db, tg_user)
    _sync_energy(user)
    db.commit()
    return _user_out(user)


@app.post("/api/tap")
def tap(body: TapRequest, tg_user: dict = Depends(get_telegram_user), db: Session = Depends(get_db)):
    user = _get_or_create_user(db, tg_user)
    _sync_energy(user)

    taps = max(1, min(body.taps, 50))  # simple anti-abuse clamp per request
    if user.energy < taps:
        raise HTTPException(400, "Not enough energy")

    from models import COINS_PER_TAP
    user.energy -= taps
    user.coins += taps * COINS_PER_TAP

    db.commit()
    return _user_out(user)


@app.post("/api/daily-bonus")
def claim_daily(tg_user: dict = Depends(get_telegram_user), db: Session = Depends(get_db)):
    user = _get_or_create_user(db, tg_user)
    if not _can_claim_daily(user):
        raise HTTPException(400, "Already claimed today")

    now = datetime.utcnow()
    if user.last_daily_claim and (now - user.last_daily_claim).total_seconds() < 48 * 3600:
        user.daily_streak = min(user.daily_streak + 1, DAILY_STREAK_CAP)
    else:
        user.daily_streak = 1

    reward = DAILY_BASE_REWARD * user.daily_streak
    user.coins += reward
    user.last_daily_claim = now

    db.commit()
    out = _user_out(user)
    out["reward"] = reward
    return out


@app.get("/api/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    top = db.query(User).order_by(User.coins.desc()).limit(50).all()
    return [
        {
            "rank": i + 1,
            "name": u.first_name or u.username or f"Miner {u.telegram_id}",
            "coins": round(u.coins, 2),
        }
        for i, u in enumerate(top)
    ]


@app.get("/api/health")
def health():
    return {"status": "ok"}

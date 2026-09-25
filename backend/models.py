from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# --- Game balance constants (tune these freely) ---
MAX_ENERGY = 1000
ENERGY_REGEN_PER_SEC = 1 / 3        # 1 energy every 3 seconds
COINS_PER_TAP = 1
REFERRAL_BONUS_COINS = 500          # paid to the referrer
DAILY_BASE_REWARD = 100             # coins on day 1 of a streak
DAILY_STREAK_CAP = 7                # reward stops growing after day 7


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)

    coins = Column(Float, default=0)
    energy = Column(Float, default=MAX_ENERGY)
    last_energy_update = Column(DateTime, default=datetime.utcnow)

    referral_code = Column(String, unique=True, index=True)
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)

    daily_streak = Column(Integer, default=0)
    last_daily_claim = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("User", remote_side=[id])

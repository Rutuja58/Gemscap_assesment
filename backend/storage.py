from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import threading

DATABASE_URL = "sqlite:///data/market.db"

engine = create_engine(
    DATABASE_URL,
    # This argument sets the SQLite timeout to 30 seconds
    connect_args={"check_same_thread": False, "timeout": 30}, 
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

db_lock = threading.Lock()  # <--- add lock


class Tick(Base):
    __tablename__ = "ticks"
    # Note: timestamp is part of the composite primary key
    timestamp = Column(DateTime, primary_key=True) 
    symbol = Column(String, primary_key=True)
    price = Column(Float)
    size = Column(Float)


def init_db():
    Base.metadata.create_all(bind=engine)


# FIX: Changed 'ts' to 'timestamp' to match the keyword being passed from ingestion.py
def store_tick(symbol: str, price: float, size: float, timestamp: datetime): 
    """Thread-safe DB write"""
    with db_lock:  # ensures only one write at a time
        db = SessionLocal()
        tick = Tick(
            timestamp=timestamp, # Use the new, clear variable name
            symbol=symbol,
            price=price,
            size=size,
        )
        # merge is used to handle potential identical composite keys from the stream
        db.merge(tick) 
        db.commit()
        db.close()
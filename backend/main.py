import asyncio
from fastapi import FastAPI
from backend.ingestion import start_ingestion
from backend.storage import init_db
from datetime import datetime, timedelta

app = FastAPI(title="Gemscap Analytics Backend")
SYMBOLS = ["btcusdt", "ethusdt"]

@app.on_event("startup")
async def startup_event():
    init_db()
    # safe async task
    asyncio.create_task(start_ingestion(SYMBOLS))

@app.get("/health")
def health():
    return {"status": "ok"}

# FINAL FIX: Change endpoint to query by time window (5 minutes) instead of limit (5000)
# CRITICAL FIX: Added try/finally block to guarantee connection release (db.close()), 
# preventing the 'database is locked' error.
@app.get("/latest-ticks")
def latest_ticks(minutes: int = 5):
    from backend.storage import SessionLocal, Tick
    
    db = SessionLocal() # Acquire database session
    try:
        # Calculate timestamp 5 minutes ago
        since = datetime.utcnow() - timedelta(minutes=minutes) 
        
        ticks = (
            db.query(Tick)
            # Filter for data points within the last 'minutes' window
            .filter(Tick.timestamp >= since) 
            .order_by(Tick.timestamp)
            .all()
        )
        
        # Prepare the response data before releasing the connection
        response_data = [
            {
                "timestamp": t.timestamp.isoformat(),
                "symbol": t.symbol,
                "price": t.price,
                "size": t.size,
            }
            for t in ticks
        ]
        
        return response_data
        
    finally:
        # ABSOLUTELY CRITICAL: Ensure the connection is closed immediately after reading
        db.close()
import asyncio
import json
from datetime import datetime

import websockets

from backend.storage import store_tick

# Binance Futures trade stream (more stable than spot)
BINANCE_WS_URL = "wss://fstream.binance.com/ws/{}@trade"


async def consume_symbol(symbol: str):
    """
    Consume trade data for a single symbol with auto-reconnect.
    """
    symbol = symbol.lower()

    while True:
        try:
            ws_url = BINANCE_WS_URL.format(symbol)
            print(f"[WS CONNECTING] {symbol} → {ws_url}")

            async with websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
            ) as ws:
                print(f"[WS CONNECTED] {symbol}")

                async for message in ws:
                    data = json.loads(message)

                    price = float(data["p"])
                    size = float(data["q"])
                    timestamp = datetime.fromtimestamp(data["T"] / 1000)

                    store_tick(
                        symbol=symbol,
                        price=price,
                        size=size,
                        timestamp=timestamp,
                    )

        except asyncio.CancelledError:
            print(f"[WS CANCELLED] {symbol}")
            break

        except Exception as e:
            print(f"[WS ERROR] {symbol}: {e}")
            print(f"[WS RETRYING] {symbol} in 5 seconds...")
            await asyncio.sleep(5)


async def start_ingestion(symbols: list[str]):
    """
    Start ingestion tasks for all symbols.
    """
    print("[INGESTION STARTED]")
    tasks = []

    for symbol in symbols:
        task = asyncio.create_task(consume_symbol(symbol))
        tasks.append(task)
        await asyncio.sleep(1)  # stagger connections (important)

    await asyncio.gather(*tasks)

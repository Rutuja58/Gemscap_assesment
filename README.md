# Gemscap Quant Analytics Dashboard

## Overview
This project is a Quantitative Analytics Dashboard built to ingest real-time tick data from Binance, process it, compute key analytics, and visualize results interactively. The system demonstrates end-to-end capabilities from data ingestion, storage, analytics computation, to frontend visualization.

## Features
- Real-time data ingestion from Binance WebSocket streams
- Storage and resampling (1s, 1m, 5m) in SQLite
- Analytics:
  - Price statistics
  - Hedge ratio via OLS regression
  - Spread and z-score
  - Rolling correlation
  - Augmented Dickey-Fuller (ADF) test
- Interactive frontend dashboard using Streamlit:
  - Price charts, spread & z-score, correlation plots
  - Symbol selection, timeframe, rolling window controls
  - Alerts (user-defined thresholds, e.g., z-score > 2)
  - CSV export of processed data
- OHLC upload support for historical analysis




<img width="962" height="844" alt="image" src="https://github.com/user-attachments/assets/2c9daa4d-7309-488d-a947-3403118a2d31" />
<img width="1919" height="963" alt="image" src="https://github.com/user-attachments/assets/22b29e49-098c-4f70-aca2-2ae4fe26fbb3" />
<img width="1900" height="968" alt="image" src="https://github.com/user-attachments/assets/a892bfa3-f594-412f-8441-79578d124868" />
<img width="1917" height="967" alt="image" src="https://github.com/user-attachments/assets/9c5b61c2-a557-4cf6-a13d-1247b7e78222" />

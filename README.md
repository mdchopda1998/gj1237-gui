# GJ1237

A beginner-friendly Streamlit stock-analysis prototype inspired by trading-terminal layouts.

## Features

- NSE watchlist
- Yahoo Finance market data
- Candlestick chart
- SMA 20 / SMA 50
- RSI
- Basic trend classification
- Prototype trade score
- Recent OHLCV table

## Run online

1. Put this repository on GitHub.
2. Open Streamlit Community Cloud: https://share.streamlit.io/
3. Sign in with GitHub.
4. Click **Create app**.
5. Select this repository, branch `main`, and `app.py`.
6. Deploy.

No local Python installation is required if you use GitHub's browser editor/Codespaces.

## Important

This is a prototype for software development and visualization. It is not investment advice.

The current trade score is deliberately simple and should be replaced with your actual backend logic.

## Project structure

```text
stock-market-gui/
├── app.py
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── analysis.py
│   └── market_data.py
└── frontend/
    ├── __init__.py
    ├── components.py
    └── chart.py
```

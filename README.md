# SMC Trading Terminal — Frontend V2

This version improves the Streamlit frontend while preserving the supplied backend modules unchanged.

## Important
The SMC calculation/backtest logic is not changed by this frontend update. Frontend chart controls operate on already-computed DataFrames.

## Chart filter controls
Filters are now placed prominently at the top of **Charts & Filters**, not hidden inside a secondary expander:
- Minimum base candles
- Demand / Supply
- Reversal / Continuous
- Minimum trade score
- Minimum strength
- Fresh zones only
- Visible bars
- SMA
- Volume
- Swing points
- BOS
- Liquidity sweeps
- Order blocks
- HTF zones

Changing these controls redraws the chart without clicking Run Analysis.

## Run
`streamlit run app.py`

For Streamlit Cloud, select `app.py` as the entry point.

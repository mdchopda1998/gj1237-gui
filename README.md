# SMC Scanner & Backtester (Streamlit)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Status: real backend is now wired in

This is no longer a placeholder. `smc_backend.py` is your actual
`my_backend.py`, library portion only (every function verbatim - see the
docstring at the top of that file for the exact, minimal edits made:
optional-import guards, nothing behavioral). Zone detection, backtesting,
and metrics all run your real code:

```
data_loading.py                 CSV-first / live yfinance / synthetic-fallback OHLC
        |
ratio_config.py                  your real ratio defaults + presets
        |
zone_identification_multibase.py  ADAPTER: orchestrates the above, calls...
        |
smc_backend.py                    ...your real identity_zones_with_multibase,
                                    run_strategy_for_ticker, evaluate_strategy_metrics,
                                    calculate_composite_score
        |
ui/tabs/*.py                     render zones / metrics / trade log
```

### Two things worth knowing about your real code, found while integrating

1. **`run_strategy_for_ticker` ignores the `ticker` argument for ratio
   lookup.** It calls `identity_zones_with_multibase(data[ticker][interval],
   ratio['GEN.NS'][interval])` unconditionally - so even though your `ratio`
   dict has room for ticker-specific entries (e.g. `'ORG.NS'`), only
   `ratio['GEN.NS']` ever has any effect today. The sidebar's ratio controls
   edit `ratio['GEN.NS']` accordingly - see `ratio_config.py`'s docstring.
   If you want per-ticker ratios to actually take effect, that lookup line
   in `smc_backend.py` would need to change to something like
   `ratio.get(ticker, ratio['GEN.NS'])[interval]`.

2. **`run_risk_management_simulation()` drops `'Outcome'` and
   `'Date Created'`**, columns `evaluate_strategy_metrics()` requires, even
   though they exist one step earlier in `backtest_zones()`'s output
   (`df_bt`) and share the same index. Confirmed empirically: `df_bt` and
   `df_rm` share the same `DatetimeIndex` (zone creation date), and `df_rm`
   is just a row-subset of `df_bt`. The adapter
   (`zone_identification_multibase.py`, see the "BRIDGE FIX" comment)
   rejoins those two columns from `df_bt` onto `df_rm` by index before
   calling `evaluate_strategy_metrics()`, rather than editing your real
   function. Worth fixing at the source eventually so any other caller of
   `run_risk_management_simulation()` doesn't hit the same gap.

### Nifty (^NSEI) benchmark

Computed the same way your driver script did it: OHLC loaded via the same
CSV-first/live-fallback path as the main ticker, then
`identity_zones_with_multibase(nifty_ohlc, ratio['GEN.NS'][interval])` per
timeframe, fed into `calculate_trade_score`'s HTF-support checks.

### Data loading (CSV-first, live fallback, synthetic last resort)

For each of the three timeframes (1d/1wk/1mo), and for both the main
ticker and `^NSEI`, `data_loading.py` resolves data in this order:

1. **Saved CSV** at `<data folder>/<TICKER_with_.->_>_<interval>.csv`
   (e.g. `data/SAIL_NS_1d.csv`) - matches your `load_data()` naming.
2. **Live yfinance fetch** if no CSV is found.
3. **Synthetic placeholder** only if both fail (no network, bad ticker,
   delisted index symbol, etc.) - so the app never crashes; a caption
   under each chart says which source was actually used.

Set the folder in the sidebar's "Data source" expander (defaults to
`data/`).

### Ratio config & sidebar

`ratio_config.py` ships your real `ratio` dict defaults (`'GEN.NS'` /
`'ORG.NS'`) and your `test_scenarios` as four one-click daily presets
(`Standard`, `Aggressive_Explosive`, `Tight_Base`, plus `SAIL_Backtested` -
the ratio we grid-searched and validated on `SAIL_NS_1d.csv` earlier in
this project). An "Advanced" expander exposes raw TR/ATR and Body/TR
sliders per candle type per timeframe.

### Known rough edges to expect

- Your backend's SMC enrichments (BOS, order blocks, volume z-score,
  choppiness, swing points) all run on every request - this can be slow on
  first load per ticker/date-range combo. `@st.cache_data` means repeat
  runs with identical inputs are instant.
- If a request errors (e.g. an edge case in one of the enrichment
  functions on unusual data), the adapter catches it and surfaces
  `results.error` as a banner instead of crashing the app - check that
  banner first if a run looks empty.
- Charts are built by our own lightweight Plotly function, not your
  `plot_stock_zones`/`plot_stock_zones_monthly` (those call `fig.show()`
  internally instead of returning `fig`, so they can't be embedded in
  Streamlit without a small edit on your end).

## Structure

```
app.py                              entry point: page config, sidebar, tab router, error banner
state.py                             session_state key helpers
data_loading.py                      CSV-first, yfinance-fallback OHLC loading (cached)
ratio_config.py                      your real ratio defaults + presets + GEN.NS resolution
data_access.py                       cached wrapper around the adapter
zone_identification_multibase.py     ADAPTER: data prep, Nifty benchmark, bridge fix, error handling
smc_backend.py                       your real backend logic (library-only extract)
ui/sidebar.py                        sidebar inputs incl. ratio controls -> config dict
ui/tabs/charts_tab.py                Plotly chart rendering, per-timeframe sub-tabs (1D/1W/1M)
ui/tabs/metrics_tab.py                KPI cards from evaluate_strategy_metrics + composite score
ui/tabs/trade_log_tab.py              filterable trade-by-trade dataframe
```

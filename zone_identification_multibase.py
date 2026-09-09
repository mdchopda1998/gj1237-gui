"""
Adapter between the Streamlit UI and your REAL backend (smc_backend.py).

This is now real integration, not a placeholder - zone detection,
backtesting, and metrics all run your actual functions. What THIS file
does is exactly the "orchestration" work your Colab driver script used to
do by hand: load OHLC (CSV-first/live-fallback), build the Nifty benchmark
zones, then call your real run_strategy_for_ticker().

One bridging fix applied HERE (not inside smc_backend.py - see the comment
at BRIDGE FIX below): your real run_risk_management_simulation() drops the
'Outcome' and 'Date Created' columns that evaluate_strategy_metrics()
requires, even though they're present one step earlier in df_bt (backtest_zones
output) and share the same index. Confirmed empirically: df_bt and df_rm
share the same DatetimeIndex (zone creation date), df_rm is a row-subset of
df_bt (rows where a trade was never triggered are dropped). So we rejoin
those two columns from df_bt onto df_rm by index before calling
evaluate_strategy_metrics(). This is a workaround at the integration layer;
the cleaner long-term fix is for run_risk_management_simulation() to carry
those columns through itself.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import smc_backend as be
from data_loading import load_multi_interval
from ratio_config import default_ratio, resolve_gen_ratio

NIFTY_TICKER = "^NSEI"
TIMEFRAMES = {"1d": "Daily", "1wk": "Weekly", "1mo": "Monthly"}


def _synthetic_ohlc(ticker: str, start: date, end: date) -> pd.DataFrame:
    """Last-resort fallback: used only if neither a saved CSV nor a live
    yfinance fetch produced data (e.g. no network, bad ticker)."""
    idx = pd.date_range(start, end, freq="B")
    rng = np.random.default_rng(abs(hash(ticker)) % (2**32))
    price = 100 + np.cumsum(rng.normal(0, 1.5, len(idx)))
    df = pd.DataFrame(index=idx)
    df.index.name = "Date"
    df["Open"] = price + rng.normal(0, 0.5, len(idx))
    df["Close"] = price
    df["High"] = df[["Open", "Close"]].max(axis=1) + rng.uniform(0, 1, len(idx))
    df["Low"] = df[["Open", "Close"]].min(axis=1) - rng.uniform(0, 1, len(idx))
    df["Volume"] = rng.integers(1_000, 100_000, len(idx))
    return df


def _ensure_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Several of your real functions (compute_volume_zscore, etc.) expect
    a Volume column - some saved CSVs may not have one."""
    if "Volume" not in df.columns:
        df = df.copy()
        df["Volume"] = 0
    return df


def _load_ticker_across_timeframes(ticker: str, start_date, end_date, data_dir: str):
    """Returns ({interval: df}, {interval: source}) for one ticker."""
    loaded = load_multi_interval(ticker, start_date, end_date, data_dir=data_dir,
                                  intervals=tuple(TIMEFRAMES.keys()))
    dfs, sources = {}, {}
    for tf, (df, source) in loaded.items():
        if df is None:
            df = _synthetic_ohlc(f"{ticker}-{tf}", start_date, end_date)
            source = "synthetic"
        dfs[tf] = _ensure_volume(df)
        sources[tf] = source
    return dfs, sources


def _build_price_figure(zone_df: pd.DataFrame, ticker: str, timeframe_label: str) -> go.Figure:
    """
    Our own lightweight chart (not your plot_stock_zones/plot_stock_zones_monthly -
    those call fig.show() internally rather than returning fig, so they
    can't be used directly in Streamlit). Reads the REAL column names your
    identity_zones_with_multibase produces: Zone_Created, 'Is Demand',
    Proximal, Distal, Target.
    """
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=zone_df.index, open=zone_df["Open"], high=zone_df["High"],
        low=zone_df["Low"], close=zone_df["Close"], name=ticker,
    ))
    if "Zone_Created" in zone_df.columns:
        zones = zone_df[zone_df["Zone_Created"] == True]  # noqa: E712
        for zdate, zone in zones.iterrows():
            is_demand = bool(zone["Is Demand"])
            color = "rgba(0,180,0,0.15)" if is_demand else "rgba(200,0,0,0.15)"
            fig.add_shape(
                type="rect", x0=zdate, x1=zone_df.index[-1],
                y0=zone["Distal"], y1=zone["Proximal"],
                fillcolor=color, line=dict(width=0), layer="below",
            )
    fig.update_layout(
        title=f"{ticker} - {timeframe_label} zones",
        xaxis_rangeslider_visible=False, height=520,
    )
    return fig


def _build_nifty_zone_dfs(start_date, end_date, data_dir: str, ratio: dict):
    """
    Mirrors your driver script's:
        nifty_1d_df = identity_zones_with_multibase(data['^NSEI']['1d'], ratio['GEN.NS']['1d'])
    Returns (dict_of_dfs, dict_of_sources); any timeframe that errors out
    is set to None (calculate_trade_score already handles None gracefully).
    """
    dfs, sources = _load_ticker_across_timeframes(NIFTY_TICKER, start_date, end_date, data_dir)
    nifty_zones = {}
    for tf in TIMEFRAMES:
        try:
            nifty_zones[tf] = be.identity_zones_with_multibase(dfs[tf].copy(), resolve_gen_ratio(tf, ratio))
        except Exception:
            nifty_zones[tf] = None
    return nifty_zones, sources


@dataclass
class StrategyResults:
    ticker: str
    zones: dict                          # {'1d': df, '1wk': df, '1mo': df} - real columns
    figures: dict                        # {'1d': go.Figure, ...}
    trade_log: pd.DataFrame              # df_rm, bridged with Outcome/Date Created
    data_sources: dict = field(default_factory=dict)       # ticker OHLC sources
    nifty_data_sources: dict = field(default_factory=dict)  # nifty OHLC sources
    metrics: dict = field(default_factory=dict)
    error: Optional[str] = None          # set if the real backend raised


def run_strategy_for_ticker(ticker: str, start_date: date, end_date: date,
                             risk_pct: float, initial_capital: float,
                             data_dir: str = "data", ratio: dict = None) -> StrategyResults:
    """
    Real integration: loads OHLC (CSV-first/live-fallback/synthetic-last-resort)
    for both `ticker` and the Nifty benchmark, then calls your actual
    smc_backend.run_strategy_for_ticker(). Any exception from your backend
    is caught and returned via StrategyResults.error rather than crashing
    the app, since this is the first end-to-end run of code with many
    moving parts (BOS/order-block/volume/choppiness detectors etc.) against
    whatever data the sidebar happens to produce.
    """
    ratio = ratio or default_ratio()

    ticker_dfs, ticker_sources = _load_ticker_across_timeframes(ticker, start_date, end_date, data_dir)
    nifty_zones, nifty_sources = _build_nifty_zone_dfs(start_date, end_date, data_dir, ratio)

    data = {ticker: ticker_dfs}

    try:
        out = be.run_strategy_for_ticker(
            ticker, data, ratio,
            nifty_zones.get("1d"), nifty_zones.get("1wk"), nifty_zones.get("1mo"),
            C=initial_capital, risk=risk_pct,
        )
    except Exception as e:
        return StrategyResults(
            ticker=ticker, zones={}, figures={}, trade_log=pd.DataFrame(),
            data_sources=ticker_sources, nifty_data_sources=nifty_sources,
            error=f"Backend raised {type(e).__name__}: {e}",
        )

    zones = out.get("zones") or {}
    if not zones or zones.get("1d") is None:
        return StrategyResults(
            ticker=ticker, zones={}, figures={}, trade_log=pd.DataFrame(),
            data_sources=ticker_sources, nifty_data_sources=nifty_sources,
            error=f"No zones were identified for {ticker} with the current ratio settings.",
        )

    figures = {
        tf: _build_price_figure(zones[tf], ticker, label)
        for tf, label in TIMEFRAMES.items() if zones.get(tf) is not None
    }

    df_bt = out.get("anal", {}).get("bt")
    df_rm = out.get("anal", {}).get("rm")

    metrics = {}
    trade_log = pd.DataFrame()
    if df_rm is not None and not df_rm.empty:
        trade_log = df_rm.copy()

        # --- BRIDGE FIX: rejoin columns your real run_risk_management_simulation drops ---
        if "Outcome" not in trade_log.columns and df_bt is not None and "Outcome" in df_bt.columns:
            trade_log["Outcome"] = df_bt.loc[trade_log.index, "Outcome"]
        if "Date Created" not in trade_log.columns:
            trade_log["Date Created"] = trade_log.index
        if "Zone_Type" not in trade_log.columns and "Zone_Type" in (df_bt.columns if df_bt is not None else []):
            trade_log["Zone_Type"] = df_bt.loc[trade_log.index, "Zone_Type"]
        # --- end bridge fix ---

        try:
            metrics = be.evaluate_strategy_metrics(trade_log.copy())
            metrics["Composite Score"] = be.calculate_composite_score(metrics)
        except Exception as e:
            metrics = {}
            trade_log.attrs["metrics_error"] = f"{type(e).__name__}: {e}"

    return StrategyResults(
        ticker=ticker, zones=zones, figures=figures, trade_log=trade_log,
        data_sources=ticker_sources, nifty_data_sources=nifty_sources,
        metrics=metrics,
    )

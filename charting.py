"""
Pure plotting - takes already-computed zone/trade-score data and renders a
figure. Deliberately has ZERO dependency on smc_backend.py or
data_loading.py: nothing in here re-runs zone detection, backtesting, or
scoring. Call this as many times as you like (e.g. every time a filter
widget changes) without touching the cached analysis in data_access.py.
"""
import pandas as pd
import plotly.graph_objects as go


def filter_zones(zone_df: pd.DataFrame, min_base_count: int = 1,
                  zone_types=("Demand", "Supply"), trade_score: pd.DataFrame = None,
                  min_strength: int = None, fresh_only: bool = False) -> pd.DataFrame:
    """
    Returns the subset of zone_df's Zone_Created rows matching the given
    filters. `trade_score` (your df_ts / out['anal']['ts']) is only
    available for the daily timeframe in your real backend - min_strength
    and fresh_only are silently ignored if it's None/empty, or for zones
    that were never scored (e.g. weekly/monthly).
    """
    if zone_df is None or zone_df.empty or "Zone_Created" not in zone_df.columns:
        return pd.DataFrame()

    zones = zone_df[zone_df["Zone_Created"] == True].copy()  # noqa: E712

    if "Base Count" in zones.columns:
        zones = zones[zones["Base Count"] >= min_base_count]

    if "Is Demand" in zones.columns and zone_types:
        wanted_is_demand = {"Demand": True, "Supply": False}
        allowed = {wanted_is_demand[z] for z in zone_types if z in wanted_is_demand}
        zones = zones[zones["Is Demand"].isin(allowed)]

    if trade_score is not None and not trade_score.empty:
        if min_strength is not None:
            strength = zones.index.map(trade_score["Strength"]).to_series(index=zones.index)
            zones = zones[strength.fillna(-1) >= min_strength]
        if fresh_only:
            fresh = zones.index.map(trade_score["Freshness"]).to_series(index=zones.index)
            zones = zones[fresh.fillna(False) == True]  # noqa: E712

    return zones


def build_zone_figure(zone_df: pd.DataFrame, ticker: str, timeframe_label: str,
                       filtered_zones: pd.DataFrame = None) -> go.Figure:
    """
    Candlestick + shaded rectangles for whichever zones are in
    `filtered_zones` (pass the output of filter_zones()). If not given,
    plots every Zone_Created row unfiltered.
    """
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=zone_df.index, open=zone_df["Open"], high=zone_df["High"],
        low=zone_df["Low"], close=zone_df["Close"], name=ticker,
    ))

    zones = filtered_zones if filtered_zones is not None else \
        zone_df[zone_df.get("Zone_Created", pd.Series(dtype=bool)) == True]  # noqa: E712

    for zdate, zone in zones.iterrows():
        is_demand = bool(zone["Is Demand"])
        color = "rgba(0,180,0,0.15)" if is_demand else "rgba(200,0,0,0.15)"
        fig.add_shape(
            type="rect", x0=zdate, x1=zone_df.index[-1],
            y0=zone["Distal"], y1=zone["Proximal"],
            fillcolor=color, line=dict(width=0), layer="below",
        )

    fig.update_layout(
        title=f"{ticker} - {timeframe_label} zones ({len(zones)} shown)",
        xaxis_rangeslider_visible=False, height=520,
    )
    return fig

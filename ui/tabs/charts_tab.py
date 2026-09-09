import streamlit as st

from charting import filter_zones, build_zone_figure

TF_LABELS = {"1d": "Daily", "1wk": "Weekly", "1mo": "Monthly"}
SOURCE_NOTES = {
    "csv": "local saved CSV",
    "live": "live yfinance fetch",
    "synthetic": "synthetic placeholder - no CSV found and live fetch failed",
}


def render(config: dict, results):
    if results is None:
        st.info("Set your parameters and click **Run Analysis** to see charts.")
        return
    if getattr(results, "error", None) or not results.zones:
        st.info("No charts to show - see the error above, or try different settings.")
        return

    st.subheader(f"{config['ticker']} - Zones & Price Action")
    st.caption(
        "These filters only change what's plotted - they don't re-run zone "
        "detection, the backtest, or scoring. Metrics/Trade Log tabs always "
        "reflect the full, unfiltered analysis."
    )

    # Filters applied across all three timeframe tabs
    f1, f2 = st.columns([2, 2])
    with f1:
        min_base_count = st.slider("Min Base Count", 1, 10, 1, key="min_base_count")
    with f2:
        zone_types = st.multiselect(
            "Zone Type", ["Demand", "Supply"], default=["Demand", "Supply"], key="zone_types"
        )

    # Extra filters that only apply where trade_score (df_ts) data exists -
    # your real backend only scores the daily timeframe.
    has_trade_score = results.trade_score is not None and not results.trade_score.empty
    min_strength, fresh_only = None, False
    if has_trade_score:
        with st.expander("Daily-only filters (from trade scoring: Strength, Freshness)", expanded=False):
            use_strength = st.checkbox("Filter by minimum Strength", value=False, key="use_strength")
            if use_strength:
                max_strength = int(results.trade_score["Strength"].max())
                min_strength = st.slider("Min Strength", 0, max(max_strength, 1), 0, key="min_strength")
            fresh_only = st.checkbox("Fresh zones only", value=False, key="fresh_only")

    tf_tabs = st.tabs(list(TF_LABELS.values()))
    for (tf_key, tf_label), tf_tab in zip(TF_LABELS.items(), tf_tabs):
        with tf_tab:
            zone_df = results.zones.get(tf_key)
            if zone_df is None or zone_df.empty:
                st.info(f"No {tf_label.lower()} data available.")
                continue

            # Strength/Freshness only apply to the daily tab, since that's
            # the only timeframe your backend actually scores.
            apply_strength = min_strength if tf_key == "1d" else None
            apply_fresh = fresh_only if tf_key == "1d" else False
            score_df = results.trade_score if tf_key == "1d" else None

            filtered = filter_zones(
                zone_df, min_base_count=min_base_count, zone_types=tuple(zone_types),
                trade_score=score_df, min_strength=apply_strength, fresh_only=apply_fresh,
            )
            fig = build_zone_figure(zone_df, config["ticker"], tf_label, filtered_zones=filtered)
            st.plotly_chart(fig, use_container_width=True)

            total_zones = int(zone_df["Zone_Created"].sum()) if "Zone_Created" in zone_df.columns else 0
            source = results.data_sources.get(tf_key, "unknown")
            source_note = SOURCE_NOTES.get(source, source)
            st.caption(
                f"{len(filtered)} of {total_zones} zone(s) shown after filters "
                f"\u00b7 data source: {source_note}"
            )

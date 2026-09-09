import streamlit as st

from charting import filter_zones, filter_trade_log
from zone_identification_multibase import recompute_metrics_for_subset


def _render_metric_cards(m: dict):
    top = st.columns(4)
    top[0].metric("Composite Score", m.get("Composite Score"))
    top[1].metric("Win Rate", f"{m.get('Win Rate', 0):.1f}%")
    top[2].metric("Profit Factor", round(m.get("Profit Factor"), 2) if m.get("Profit Factor") not in (None, float("inf")) else "∞")
    top[3].metric("System Expectancy", round(m.get("System Expectancy", 0), 2))

    mid = st.columns(4)
    mid[0].metric("Total Trades", m.get("Total Trades"))
    mid[1].metric("Demand Zones", m.get("Demand Zones"))
    mid[2].metric("Supply Zones", m.get("Supply Zones"))
    mid[3].metric("Net PNL", round(m.get("Net PNL", 0), 2))

    with st.expander("Timing, fill-quality & scaled expectancy detail"):
        st.write(
            {
                "Winning Trades": m.get("Winning Trades"),
                "Avg PnL / Trade": m.get("Avg PnL"),
                "Expectancy Score (annualized)": m.get("Expectancy Score"),
                "Avg Days: Zone Creation -> Entry": m.get("Avg Time Creation_Entry"),
                "Avg Hold Time (Profitable, days)": m.get("Avg Hold Time (Profitable)"),
                "Avg Hold Time (Losing, days)": m.get("Avg Hold Time (Losing)"),
                "Avg Piercing %": m.get("Avg Piercing %"),
                "Profitable Demand Zones": m.get("Profitable Demand Zones"),
                "Profitable Supply Zones": m.get("Profitable Supply Zones"),
            }
        )


def render(config: dict, results):
    if results is None:
        st.info("Run an analysis to see backtest metrics.")
        return
    if getattr(results, "error", None):
        st.info("No metrics to show - see the error above.")
        return

    m = results.metrics
    if not m:
        metrics_error = results.trade_log.attrs.get("metrics_error") if hasattr(results.trade_log, "attrs") else None
        if metrics_error:
            st.warning(f"Trades were taken but metrics couldn't be computed: {metrics_error}")
        else:
            st.warning("No resolved trades to compute metrics from.")
        return

    st.subheader("Backtest Metrics")
    if results.analysis_timestamp:
        st.caption(f"Analysis last computed: {results.analysis_timestamp}")

    use_filtered = st.checkbox(
        "Compute metrics for currently filtered zones only (mirrors Chart Filters tab)",
        value=False, key="metrics_use_filtered",
    )

    if not use_filtered:
        _render_metric_cards(m)
        return

    # Mirror the exact same filter state the Charts tab set in session_state -
    # this is a re-slice + re-aggregate of the existing trade_log, not a
    # re-run of zone detection/backtest/scoring.
    zones_1d = results.zones.get("1d")
    if zones_1d is None or zones_1d.empty:
        st.info("No daily zone data available to filter against.")
        return

    min_base_count = st.session_state.get("min_base_count", 1)
    zone_types = tuple(st.session_state.get("zone_types", ["Demand", "Supply"]))
    min_strength = st.session_state.get("min_strength") if st.session_state.get("use_strength") else None
    fresh_only = st.session_state.get("fresh_only", False)

    filtered_zones = filter_zones(
        zones_1d, min_base_count=min_base_count, zone_types=zone_types,
        trade_score=results.trade_score, min_strength=min_strength, fresh_only=fresh_only,
    )
    filtered_trade_log = filter_trade_log(results.trade_log, filtered_zones.index)

    st.caption(
        f"Filters currently set on the Charts tab: Min Base Count \u2265 {min_base_count}, "
        f"Zone Type in {list(zone_types)}"
        + (f", Min Strength \u2265 {min_strength}" if min_strength is not None else "")
        + (", Fresh only" if fresh_only else "")
        + f" \u2192 {len(filtered_trade_log)} of {len(results.trade_log)} trades match."
    )

    if filtered_trade_log.empty:
        st.warning("No trades match the current chart filters.")
        return

    filtered_metrics = recompute_metrics_for_subset(filtered_trade_log)
    if "_error" in filtered_metrics:
        st.warning(f"Couldn't compute filtered metrics: {filtered_metrics['_error']}")
        return

    _render_metric_cards(filtered_metrics)

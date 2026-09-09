import streamlit as st


def _safe_options(series):
    """Sorted unique values as strings, NaN mapped to 'Unknown' - avoids
    TypeError: '<' not supported between float (NaN) and str when a
    column has mixed real values and NaN (seen in real Zone_Type data)."""
    filled = series.fillna("Unknown").astype(str)
    return sorted(filled.unique()), filled


def render(config: dict, results):
    if results is None:
        st.info("Run an analysis to see trade-by-trade logs.")
        return
    if getattr(results, "error", None):
        st.info("No trade log to show - see the error above.")
        return

    st.subheader("Trade Log")

    trade_log = results.trade_log
    if trade_log is None or trade_log.empty:
        st.warning("No trades were taken for the selected parameters.")
        return

    outcome_options, outcome_filled = _safe_options(trade_log["Outcome"])
    zone_options, zone_filled = _safe_options(trade_log["Zone_Type"])

    outcome_filter = st.multiselect("Outcome", options=outcome_options, default=outcome_options)
    zone_filter = st.multiselect("Zone type", options=zone_options, default=zone_options)

    filtered = trade_log[
        outcome_filled.isin(outcome_filter) & zone_filled.isin(zone_filter)
    ]

    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.caption(f"{len(filtered)} of {len(trade_log)} trades shown.")

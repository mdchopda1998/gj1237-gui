import streamlit as st


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

    outcome_filter = st.multiselect(
        "Outcome", options=sorted(trade_log["Outcome"].unique()),
        default=list(trade_log["Outcome"].unique()),
    )
    zone_filter = st.multiselect(
        "Zone type", options=sorted(trade_log["Zone_Type"].unique()),
        default=list(trade_log["Zone_Type"].unique()),
    )

    filtered = trade_log[
        trade_log["Outcome"].isin(outcome_filter) & trade_log["Zone_Type"].isin(zone_filter)
    ]
    if not filtered.empty:

        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption(f"{len(filtered)} of {len(trade_log)} trades shown.")
    else:
        st.info('No zones detected.')

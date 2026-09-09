import streamlit as st


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

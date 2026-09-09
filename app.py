"""
SMC Scanner & Backtester - Streamlit entry point.

Run with:
    streamlit run app.py
"""
import streamlit as st

from data_access import get_strategy_results
from ui.sidebar import render_sidebar
from ui.tabs import charts_tab, metrics_tab, trade_log_tab

st.set_page_config(page_title="SMC Scanner & Backtester", layout="wide")

# Bump this on every delivered zip. If this string doesn't match what you
# expect to see under the title, you're running stale files - re-unzip
# and replace the WHOLE folder rather than copying individual files over.
APP_BUILD = "2026-09-09-chart-filters-v1"


def main():
    st.title("Supply & Demand Scanner")
    st.caption(f"Build: {APP_BUILD} \u00b7 Streamlit {st.__version__}")

    config = render_sidebar()
    run_clicked = st.sidebar.button("Run Analysis", type="primary")

    if run_clicked:
        if not config["ticker"]:
            st.sidebar.error("Enter a ticker first.")
        else:
            with st.spinner("Fetching data and computing zones..."):
                try:
                    results = get_strategy_results(
                        config["ticker"],
                        config["start_date"],
                        config["end_date"],
                        config["risk_pct"],
                        config["initial_capital"],
                        config["data_dir"],
                        config["ratio"],
                    )
                    st.session_state["results"] = results
                    st.session_state["config"] = config
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    results = st.session_state.get("results")
    active_config = st.session_state.get("config", config)

    st.caption(
        f"Debug: results loaded = {results is not None}"
        + (f" for {results.ticker}" if results is not None else "")
        + (f" (error: {results.error})" if results is not None and getattr(results, "error", None) else "")
    )

    if results is not None and getattr(results, "error", None):
        st.error(f"Backend error for {results.ticker}: {results.error}")

    tab_charts, tab_metrics, tab_logs = st.tabs(
        ["Charts", "Backtest Metrics", "Trade Logs"]
    )

    with tab_charts:
        charts_tab.render(active_config, results)

    with tab_metrics:
        metrics_tab.render(active_config, results)

    with tab_logs:
        trade_log_tab.render(active_config, results)


if __name__ == "__main__":
    main()

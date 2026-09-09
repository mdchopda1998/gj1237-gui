
import streamlit as st
from data_access import get_strategy_results
from ui.sidebar import render_sidebar
from ui.tabs import charts_tab,metrics_tab,trade_log_tab

st.set_page_config(page_title="SMC Trading Terminal",page_icon="📊",layout="wide",
                   initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:.8rem;max-width:1800px}
[data-testid="stSidebar"]{min-width:275px;max-width:310px}
div[data-testid="stMetric"]{padding:.5rem;border:1px solid rgba(128,128,128,.18);border-radius:10px}
</style>""",unsafe_allow_html=True)
APP_BUILD="2026-09-09-frontend-v2"

def main():
    # Header
    h1,h2=st.columns([5,1])
    with h1:
        st.title("📊 SMC Trading Terminal")
        st.caption("Supply · Demand · Structure · Liquidity · Backtest · Risk")
    with h2:
        st.metric("Status","READY" if "results" in st.session_state else "IDLE")
    config=render_sidebar()
    run=st.sidebar.button("🚀 Run Analysis",type="primary",use_container_width=True)
    if run:
        if not config["ticker"]: st.sidebar.error("Enter a ticker.")
        else:
            with st.spinner("Running the existing backend — no frontend filters are applied here..."):
                try:
                    st.session_state.results=get_strategy_results(config["ticker"],config["start_date"],config["end_date"],
                        config["risk_pct"],config["initial_capital"],config["data_dir"],config["ratio"])
                    st.session_state.config=config
                except Exception as e: st.error(f"Analysis failed: {type(e).__name__}: {e}")
    results=st.session_state.get("results")
    active=st.session_state.get("config",config)
    if results is None:
        st.info("👈 Configure the analysis and click **Run Analysis**. After results load, chart filters appear directly above the charts.")
        return
    if getattr(results,"error",None): st.error(results.error)
    m=results.metrics or {}
    k=st.columns(6)
    k[0].metric("Instrument",results.ticker)
    k[1].metric("Zones",int(results.zones.get("1d",[]).shape[0]) if results.zones.get("1d") is not None else 0)
    k[2].metric("Trades",m.get("Total Trades",0))
    k[3].metric("Win Rate",f"{m.get('Win Rate',0):.1f}%")
    k[4].metric("Profit Factor","∞" if m.get("Profit Factor")==float("inf") else f"{m.get('Profit Factor',0):.2f}")
    k[5].metric("Composite",f"{m.get('Composite Score',0):.2f}")
    st.caption(f"Backend analysis computed: {results.analysis_timestamp or '—'} · Build {APP_BUILD}")
    t1,t2,t3=st.tabs(["📈 Charts & Filters","📊 Backtest Metrics","📒 Trade Logs"])
    with t1: charts_tab.render(active,results)
    with t2: metrics_tab.render(active,results)
    with t3: trade_log_tab.render(active,results)
if __name__=="__main__": main()

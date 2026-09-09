
import streamlit as st
from charting import filter_zones,filter_trade_log
from zone_identification_multibase import recompute_metrics_for_subset

def _cards(m):
    a,b,c,d,e=st.columns(5)
    a.metric("Composite Score",f"{m.get('Composite Score',0):.2f}")
    b.metric("Win Rate",f"{m.get('Win Rate',0):.1f}%")
    pf=m.get("Profit Factor",0); b2="∞" if pf==float("inf") else f"{pf:.2f}"
    c.metric("Profit Factor",b2)
    d.metric("Expectancy",f"{m.get('System Expectancy',0):,.2f}")
    e.metric("Net PNL",f"{m.get('Net PNL',0):,.2f}")
    a,b,c,d=st.columns(4)
    a.metric("Total Trades",m.get("Total Trades",0)); b.metric("Winning",m.get("Winning Trades",0))
    c.metric("Demand Zones",m.get("Demand Zones",0)); d.metric("Supply Zones",m.get("Supply Zones",0))

def render(config,results):
    if results is None: st.info("Run Analysis first."); return
    if getattr(results,"error",None): return
    st.subheader("📊 Backtest & Strategy Performance")
    _cards(results.metrics)
    st.divider()
    use=st.checkbox("Recalculate metrics for the current chart-filtered daily zones",False)
    m=results.metrics
    if use:
        z=results.zones.get("1d")
        if z is not None and not z.empty:
            ft=filter_zones(z,st.session_state.get("min_base",1),
                            tuple(st.session_state.get("zone_types",["Demand","Supply"])),
                            results.trade_score)
            tl=filter_trade_log(results.trade_log,ft.index)
            fm=recompute_metrics_for_subset(tl) if not tl.empty else {}
            if fm and "_error" not in fm: _cards(fm)
            else: st.info("No matching trades.")
    with st.expander("Detailed metrics",expanded=True):
        st.json(results.metrics)
    if results.trade_log is not None and not results.trade_log.empty:
        # Risk-management equity curve is already computed by the backend.
        rm=results.trade_log
        if "Capital_After_Trade" in rm:
            st.subheader("Equity Curve")
            eq=rm[["Entry Date","Capital_After_Trade"]].dropna().copy()
            if not eq.empty:
                st.line_chart(eq.set_index("Entry Date"))

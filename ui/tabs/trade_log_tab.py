
import streamlit as st
import pandas as pd
def render(config,results):
    if results is None: st.info("Run Analysis first."); return
    if getattr(results,"error",None): return
    df=results.trade_log
    st.subheader("📒 Trade Log")
    if df is None or df.empty: st.warning("No resolved trades for this analysis."); return
    a,b,c=st.columns(3)
    outcomes=sorted(df["Outcome"].fillna("Unknown").astype(str).unique()) if "Outcome" in df else []
    zones=sorted(df["Zone_Type"].fillna("Unknown").astype(str).unique()) if "Zone_Type" in df else []
    with a: of=st.multiselect("Outcome",outcomes,outcomes)
    with b: zf=st.multiselect("Zone type",zones,zones)
    with c: minr=st.number_input("Minimum R-multiple",-20.0,20.0,-20.0,.25)
    x=df.copy()
    if "Outcome" in x: x=x[x["Outcome"].fillna("Unknown").astype(str).isin(of)]
    if "Zone_Type" in x: x=x[x["Zone_Type"].fillna("Unknown").astype(str).isin(zf)]
    if "R-Multiple" in x: x=x[x["R-Multiple"].fillna(-999)>=minr]
    st.caption(f"{len(x)} of {len(df)} trades shown")
    st.dataframe(x,use_container_width=True)
    st.download_button("⬇ Download CSV",x.to_csv(index=True),"smc_trade_log.csv","text/csv")

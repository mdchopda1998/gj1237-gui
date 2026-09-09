
import streamlit as st
from datetime import date,timedelta
from ratio_config import default_ratio, resolve_gen_ratio, DAILY_PRESETS

def render_sidebar():
    st.sidebar.header("⚙ Analysis Controls")
    ticker=st.sidebar.text_input("Ticker",value=st.session_state.get("ticker","SAIL.NS")).strip().upper()
    dr=st.sidebar.date_input("Backtest range",(date.today()-timedelta(days=365*3),date.today()))
    start_date,end_date=(dr if len(dr)==2 else (None,None))
    risk_pct=st.sidebar.slider("Risk per trade (%)",0.1,5.0,1.0,0.1)/100
    capital=st.sidebar.number_input("Initial capital (₹)",10000,100000000,500000,10000)
    with st.sidebar.expander("Data source"):
        data_dir=st.text_input("Local CSV folder","data")
    with st.sidebar.expander("Zone Detection Ratios"):
        ratio=default_ratio()
        preset=st.selectbox("Daily preset",["Custom"]+list(DAILY_PRESETS),index=1)
        if preset!="Custom": ratio["GEN.NS"]["1d"]={k:dict(v) for k,v in DAILY_PRESETS[preset].items()}
        for tf,label in [("1d","Daily"),("1wk","Weekly"),("1mo","Monthly")]:
            with st.expander(label):
                rr=resolve_gen_ratio(tf,ratio)
                for typ in ["Exciting","Base","Explosive"]:
                    c1,c2=st.columns(2)
                    with c1:
                        a=st.number_input(f"{typ} TR/ATR",.1,2.,float(rr[typ]["TR_ATR"]),.1,key=f"ratio_{tf}_{typ}_a")
                    with c2:
                        b=st.number_input(f"{typ} Body/TR",.1,1.,float(rr[typ]["BS_TR"]),.05,key=f"ratio_{tf}_{typ}_b")
                    ratio["GEN.NS"][tf][typ]={"TR_ATR":a,"BS_TR":b}
    return dict(ticker=ticker,start_date=start_date,end_date=end_date,risk_pct=risk_pct,
                initial_capital=capital,data_dir=data_dir,ratio=ratio)

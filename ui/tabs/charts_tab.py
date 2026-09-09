
import streamlit as st
from charting import filter_zones,build_zone_figure

def render(config,results):
    if results is None:
        st.info("Run Analysis from the sidebar.")
        return
    if getattr(results,"error",None):
        st.error(results.error); return
    st.subheader("📈 Price Action & SMC Map")
    st.caption("All controls below are frontend-only: changing them does not rerun your backend.")
    f=st.container(border=True)
    with f:
        st.markdown("### 🔎 Chart Filters")
        c1,c2,c3,c4=st.columns(4)
        with c1: min_base=st.slider("Minimum base candles",1,10,1)
        with c2: types=st.multiselect("Zone type",["Demand","Supply"],["Demand","Supply"])
        with c3: continuous=st.selectbox("Zone structure",["All","Reversal","Continuous"])
        with c4: bars=st.select_slider("Visible bars",[60,120,250,500,1000],value=250)
        s1,s2,s3,s4=st.columns(4)
        with s1: min_score=st.slider("Minimum trade score",0.0,10.0,0.0,.5)
        with s2: use_strength=st.checkbox("Use minimum strength",False)
        with s3: min_strength=st.number_input("Min strength",0,20,0,1,disabled=not use_strength)
        with s4: fresh=st.checkbox("Fresh zones only",False)
        st.markdown("**Overlays**")
        o1,o2,o3,o4,o5,o6,o7=st.columns(7)
        sma=o1.checkbox("SMA",True); vol=o2.checkbox("Volume",False); sw=o3.checkbox("Swings",False)
        bos=o4.checkbox("BOS",False); sweep=o5.checkbox("Sweeps",False); ob=o6.checkbox("OB",False); htf=o7.checkbox("HTF",False)
    zone_struct=None if continuous=="All" else continuous=="Continuous"
    tabs=st.tabs(["Daily","Weekly","Monthly"])
    for (tf,tab) in zip(["1d","1wk","1mo"],tabs):
        with tab:
            df=results.zones.get(tf)
            if df is None or df.empty:
                st.info("No data available."); continue
            score=results.trade_score if tf=="1d" else None
            filtered=filter_zones(df,min_base,tuple(types),score,
                                  min_strength if tf=="1d" and use_strength else None,
                                  fresh if tf=="1d" else False,
                                  min_score if tf=="1d" and min_score>0 else None,
                                  zone_struct)
            htf_df=results.zones.get("1wk") if tf=="1d" else results.zones.get("1mo") if tf=="1wk" else None
            fig=build_zone_figure(df,config["ticker"],{"1d":"Daily","1wk":"Weekly","1mo":"Monthly"}[tf],
                                  filtered,sma,vol,sw,bos,sweep,ob,htf,htf_df,bars)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":True,"displaylogo":False})
            total=int(df["Zone_Created"].sum()) if "Zone_Created" in df else 0
            st.caption(f"Showing {len(filtered)} of {total} detected zones · {len(df)} candles loaded")
            if tf=="1d" and not filtered.empty:
                cols=[c for c in ["Proximal","Distal","Target","Base Count","Is Demand","Is Continuous"] if c in filtered]
                st.dataframe(filtered[cols].sort_index(ascending=False),use_container_width=True,hide_index=False)

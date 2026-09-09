
"""Pure frontend chart utilities. Does not modify or execute SMC backend logic."""
import pandas as pd
import plotly.graph_objects as go

def filter_zones(zone_df, min_base_count=1, zone_types=("Demand","Supply"),
                 trade_score=None, min_strength=None, fresh_only=False,
                 min_score=None, continuous=None):
    if zone_df is None or zone_df.empty or "Zone_Created" not in zone_df:
        return pd.DataFrame()
    z=zone_df[zone_df["Zone_Created"]==True].copy()
    if "Base Count" in z: z=z[z["Base Count"].fillna(0)>=min_base_count]
    if "Is Demand" in z and zone_types:
        allowed={"Demand":True,"Supply":False}
        vals={allowed[x] for x in zone_types if x in allowed}
        z=z[z["Is Demand"].isin(vals)]
    if continuous is not None and "Is Continuous" in z:
        z=z[z["Is Continuous"]==continuous]
    if trade_score is not None and not trade_score.empty:
        ts=trade_score.reindex(z.index)
        if min_strength is not None and "Strength" in ts:
            z=z[ts["Strength"].fillna(-1)>=min_strength]
        if fresh_only and "Freshness" in ts:
            z=z[ts["Freshness"].fillna(False)==True]
        if min_score is not None and "Trade Score" in ts:
            z=z[ts["Trade Score"].fillna(-1)>=min_score]
    return z

def filter_trade_log(trade_log, filtered_zone_dates):
    if trade_log is None or trade_log.empty: return pd.DataFrame()
    return trade_log[trade_log.index.isin(filtered_zone_dates)]

def build_zone_figure(zone_df, ticker, timeframe_label, filtered_zones=None,
                      show_sma=True, show_volume=False, show_swings=False,
                      show_bos=False, show_sweeps=False, show_ob=False,
                      show_htf=False, htf_df=None, visible_bars=None):
    fig=go.Figure()
    plot_df=zone_df.tail(visible_bars) if visible_bars else zone_df
    fig.add_trace(go.Candlestick(x=plot_df.index,open=plot_df["Open"],high=plot_df["High"],
                                 low=plot_df["Low"],close=plot_df["Close"],name="Price"))
    if show_sma:
        if "SMA20" in plot_df:
            fig.add_trace(go.Scatter(x=plot_df.index,y=plot_df["SMA20"],name="SMA 20",mode="lines"))
        if "SMA50" in plot_df:
            fig.add_trace(go.Scatter(x=plot_df.index,y=plot_df["SMA50"],name="SMA 50",mode="lines"))
    zones=filtered_zones if filtered_zones is not None else zone_df[zone_df["Zone_Created"]==True]
    for zdate,z in zones.iterrows():
        color="rgba(0,190,100,.16)" if bool(z["Is Demand"]) else "rgba(220,60,60,.16)"
        fig.add_shape(type="rect",x0=zdate,x1=plot_df.index[-1],y0=z["Distal"],y1=z["Proximal"],
                      fillcolor=color,line=dict(width=1),layer="below")
    if show_htf and htf_df is not None and not htf_df.empty and "Zone_Created" in htf_df:
        for zd,z in htf_df[htf_df["Zone_Created"]==True].iterrows():
            if pd.isna(z.get("Proximal")) or pd.isna(z.get("Distal")): continue
            fig.add_shape(type="rect",x0=zd,x1=plot_df.index[-1],y0=z["Distal"],y1=z["Proximal"],
                          fillcolor="rgba(120,120,220,.08)",line=dict(width=1,dash="dot"),layer="below")
    if show_swings:
        if "Swing_High" in plot_df:
            x=plot_df[plot_df["Swing_High"]]
            fig.add_trace(go.Scatter(x=x.index,y=x.High,mode="markers",name="Swing High",marker_symbol="triangle-up"))
        if "Swing_Low" in plot_df:
            x=plot_df[plot_df["Swing_Low"]]
            fig.add_trace(go.Scatter(x=x.index,y=x.Low,mode="markers",name="Swing Low",marker_symbol="triangle-down"))
    if show_bos:
        for col,name,sym in [("BOS_Bull","BOS Bull","star"),("BOS_Bear","BOS Bear","star")]:
            if col in plot_df:
                x=plot_df[plot_df[col]]
                fig.add_trace(go.Scatter(x=x.index,y=x.Close,mode="markers",name=name,marker_symbol=sym))
    if show_sweeps:
        for col,name in [("Sweep_High","Sweep High"),("Sweep_Low","Sweep Low")]:
            if col in plot_df:
                x=plot_df[plot_df[col]]
                fig.add_trace(go.Scatter(x=x.index,y=x.Close,mode="markers",name=name,marker_symbol="diamond"))
    if show_ob and "OB" in plot_df:
        x=plot_df[plot_df["OB"]==True]
        fig.add_trace(go.Scatter(x=x.index,y=x.Close,mode="markers",name="Order Block",marker_symbol="square"))
    if show_volume:
        fig.add_trace(go.Bar(x=plot_df.index,y=plot_df["Volume"],name="Volume",yaxis="y2",opacity=.25))
        fig.update_layout(yaxis2=dict(overlaying="y",side="right",showgrid=False,title="Volume"))
    fig.update_layout(
        title=f"{ticker} · {timeframe_label} · {len(zones)} zones",
        height=650, xaxis_rangeslider_visible=True,
        hovermode="x unified", margin=dict(l=10,r=10,t=45,b=10),
        legend=dict(orientation="h",y=1.02,x=0)
    )
    return fig

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Terminal", page_icon="📈", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 230px; max-width: 260px; }
.metric-box {
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 10px;
    padding: 12px;
    text-align: center;
}
.small-muted { color: #888; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

WATCHLIST = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
}

@st.cache_data(ttl=300)
def get_data(symbol, period, interval):
    df = yf.download(
        symbol, period=period, interval=interval,
        auto_adjust=False, progress=False
    )
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna(how="all")

def indicators(df):
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def trade_score(df):
    x = df.iloc[-1]
    score = 50
    if pd.notna(x["SMA20"]) and x["Close"] > x["SMA20"]:
        score += 10
    else:
        score -= 10
    if pd.notna(x["SMA50"]) and x["SMA20"] > x["SMA50"]:
        score += 15
    else:
        score -= 15
    if pd.notna(x["RSI"]):
        if 50 < x["RSI"] < 70:
            score += 10
        elif x["RSI"] > 70:
            score -= 5
        elif x["RSI"] < 30:
            score += 5
    return max(0, min(100, int(score)))

st.title("📈 Stock Terminal")
st.caption("Zerodha-inspired local/prototype trading dashboard • Yahoo Finance data")

with st.sidebar:
    st.header("Watchlist")
    selected = st.radio("Select stock", list(WATCHLIST.keys()))
    st.divider()
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
    interval = st.selectbox("Interval", ["1d", "1h"], index=0)
    st.divider()
    st.caption("Data: Yahoo Finance")
    st.caption("Prototype — not investment advice")

symbol = WATCHLIST[selected]
df = get_data(symbol, period, interval)

if df.empty:
    st.error("No data returned. Try another stock or period.")
    st.stop()

df = indicators(df)
latest = df.iloc[-1]
price = float(latest["Close"])
prev = float(df["Close"].iloc[-2]) if len(df) > 1 else price
change = price - prev
pct = (change / prev * 100) if prev else 0
score = trade_score(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric(selected, f"₹{price:,.2f}", f"{change:+,.2f} ({pct:+.2f}%)")
trend = "BULLISH" if pd.notna(latest["SMA20"]) and pd.notna(latest["SMA50"]) and latest["SMA20"] > latest["SMA50"] else "BEARISH"
c2.metric("Trend", trend)
c3.metric("Trade Score", f"{score}/100")
c4.metric("RSI", f"{latest['RSI']:.1f}" if pd.notna(latest["RSI"]) else "—")

st.subheader(f"{selected} • Price Chart")

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"], name="Price"
))
fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20", mode="lines"))
fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50", mode="lines"))
fig.update_layout(
    height=560, xaxis_rangeslider_visible=False,
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h")
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Analysis")
a, b, c, d = st.columns(4)
a.metric("SMA 20", f"₹{latest['SMA20']:,.2f}" if pd.notna(latest["SMA20"]) else "—")
b.metric("SMA 50", f"₹{latest['SMA50']:,.2f}" if pd.notna(latest["SMA50"]) else "—")
d.metric("Volume", f"{int(latest['Volume']):,}")

with st.expander("Show recent data"):
    st.dataframe(df.tail(50), use_container_width=True)

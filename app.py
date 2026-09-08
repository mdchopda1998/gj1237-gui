import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="TradeDesk", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 255px; max-width: 275px; }
[data-testid="stSidebarContent"] { padding-top: 1.5rem; }
.block-container { padding: 1.5rem 2.25rem 2.5rem; max-width: 1600px; }
.terminal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: .25rem; }
.brand { font-size: 1.4rem; font-weight: 700; letter-spacing: -.03em; color: #e8edf2; }
.brand span { color: #23c88b; }
.status { color: #8c99a6; font-size: .78rem; }
.section-label { color: #80909c; font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; margin: .8rem 0 .35rem; }
.quote-strip { border: 1px solid #26343d; background: #111a20; border-radius: 6px; padding: 1rem 1.15rem; }
.quote-name { color: #9aa8b2; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
.quote-price { color: #f1f5f7; font-size: 1.65rem; font-weight: 700; line-height: 1.2; }
.positive { color: #25c78a; }
.negative { color: #f06f6f; }
[data-testid="stMetric"] { background: #111a20; border: 1px solid #26343d; padding: .8rem 1rem; border-radius: 6px; }
[data-testid="stMetricLabel"] { color: #8b9aa5; }
[data-testid="stMetricValue"] { font-size: 1.2rem; }
div[data-testid="stTabs"] button { font-size: .82rem; }
button[kind="primary"] { background: #159a69; border-color: #159a69; }
.stDataFrame { border: 1px solid #26343d; }
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

if "orders" not in st.session_state:
    st.session_state.orders = []

st.markdown('<div class="terminal-header"><div class="brand"><span>●</span> TradeDesk</div><div class="status">NSE · Market data via Yahoo Finance · Prototype</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="section-label">Market watch</div>', unsafe_allow_html=True)
    selected = st.radio("Select stock", list(WATCHLIST.keys()))
    st.divider()
    st.markdown('<div class="section-label">Chart controls</div>', unsafe_allow_html=True)
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2, label_visibility="collapsed")
    interval = st.selectbox("Interval", ["1d", "1h"], index=0, label_visibility="collapsed")
    st.divider()
    st.markdown('<div class="section-label">Account</div>', unsafe_allow_html=True)
    st.metric("Available margin", "₹1,00,000", "₹0 today")
    st.caption("Paper trading mode · Orders are local only")

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

st.markdown(f'<div class="quote-strip"><div class="quote-name">NSE / {selected}</div><div class="quote-price">₹{price:,.2f} <span class="{"positive" if change >= 0 else "negative"}" style="font-size:.9rem; font-weight:600;">{change:+,.2f} ({pct:+.2f}%)</span></div></div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Open", f"₹{float(latest['Open']):,.2f}")
c2.metric("Day high", f"₹{float(latest['High']):,.2f}")
c3.metric("Day low", f"₹{float(latest['Low']):,.2f}")
trend = "BULLISH" if pd.notna(latest["SMA20"]) and pd.notna(latest["SMA50"]) and latest["SMA20"] > latest["SMA50"] else "BEARISH"
c4.metric("Volume", f"{int(latest['Volume']):,}")

chart_col, order_col = st.columns([2.25, 1], gap="large")

with chart_col:
    st.markdown('<div class="section-label">Price chart</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20", mode="lines", line=dict(color="#f0b35b", width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50", mode="lines", line=dict(color="#6aa9e9", width=1.5)))
    fig.update_layout(height=510, xaxis_rangeslider_visible=False, margin=dict(l=5, r=5, t=10, b=5), legend=dict(orientation="h"), template="plotly_dark", paper_bgcolor="#111a20", plot_bgcolor="#111a20", font=dict(color="#9aa8b2"))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#233039", side="right")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})

with order_col:
    st.markdown('<div class="section-label">Place order · paper mode</div>', unsafe_allow_html=True)
    with st.container(border=True):
        side = st.radio("Side", ["BUY", "SELL"], horizontal=True, label_visibility="collapsed")
        order_type = st.selectbox("Order type", ["Market", "Limit"])
        quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
        limit_price = st.number_input("Price", min_value=0.01, value=round(price, 2), step=0.05, disabled=order_type == "Market")
        if st.button(f"{side} {selected}", type="primary", use_container_width=True):
            st.session_state.orders.insert(0, {"Time": datetime.now().strftime("%H:%M:%S"), "Symbol": selected, "Side": side, "Qty": quantity, "Type": order_type, "Price": round(price if order_type == "Market" else limit_price, 2), "Status": "PENDING"})
            st.success("Paper order placed")
        st.caption(f"Estimated value · ₹{quantity * (price if order_type == 'Market' else limit_price):,.2f}")

    st.markdown('<div class="section-label">Signal snapshot</div>', unsafe_allow_html=True)
    st.metric("Trend", trend, "Above SMA 20/50" if trend == "BULLISH" else "Below SMA 20/50")
    st.metric("Trade score", f"{score}/100")
    st.metric("RSI", f"{latest['RSI']:.1f}" if pd.notna(latest["RSI"]) else "—")

st.markdown('<div class="section-label">Portfolio</div>', unsafe_allow_html=True)
positions = pd.DataFrame([
    {"Instrument": "RELIANCE", "Qty": 12, "Avg. price": "₹2,841.20", "LTP": "₹2,912.40", "P&L": "+₹854.40", "Return": "+2.51%"},
    {"Instrument": "INFY", "Qty": 20, "Avg. price": "₹1,462.10", "LTP": "₹1,438.65", "P&L": "-₹469.00", "Return": "-1.60%"},
])
st.dataframe(positions, hide_index=True, use_container_width=True, height=110)

tab_orders, tab_data = st.tabs(["Orders", "Recent market data"])
with tab_orders:
    if st.session_state.orders:
        st.dataframe(pd.DataFrame(st.session_state.orders), hide_index=True, use_container_width=True)
    else:
        st.caption("No paper orders placed in this session.")

with tab_data:
    st.dataframe(df.tail(50), use_container_width=True)

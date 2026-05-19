import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")
st.title("🚀 Crypto Smart AI PRO++")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("⚙️ Setting")

coin_input = st.sidebar.text_input(
    "Multi Coin (pisahkan koma)",
    "BTCUSDT,ETHUSDT"
)

symbols = [x.strip().upper() for x in coin_input.split(",")]

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1m","5m","15m","1h","4h","1d"]
)

limit = st.sidebar.slider(
    "Jumlah Candle",
    50,
    200,
    120
)

refresh = st.sidebar.slider(
    "Auto Refresh (detik)",
    1,
    10,
    3
)

st.sidebar.markdown("---")
st.sidebar.write("🚀 Crypto AI Settings")

# =========================
# AUTO REFRESH (HALUS)
# =========================
st_autorefresh(interval=refresh * 1000, key="refresh")

# =========================
# DATA TOKOCRYPTO
# =========================
@st.cache_data(ttl=5)
def get_data(symbol, timeframe, limit):

    url = f"https://www.tokocrypto.site/api/v3/klines?symbol={symbol}&interval={timeframe}&limit={limit}"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        if not isinstance(data, list):
            return None

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "ct","qv","nt","tb","tq","ig"
        ])

        df["time"] = (
            pd.to_datetime(df["time"], unit="ms")
            .dt.tz_localize("UTC")
            .dt.tz_convert("Asia/Jakarta")
        )

        for col in ["open","high","low","close","volume"]:
            df[col] = df[col].astype(float)

        return df

    except:
        return None

# =========================
# LOOP MULTI COIN
# =========================
for symbol in symbols:

    st.subheader(f"📊 {symbol}")

    df = get_data(symbol, timeframe, limit)

    if df is None or len(df) < 50:
        st.warning(f"{symbol} data tidak tersedia")
        continue

    # =========================
    # INDIKATOR
    # =========================
    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100/(1+rs))

    # =========================
    # SUPPORT RESISTANCE
    # =========================
    levels = sorted(df["close"].tail(100))

    s1 = np.percentile(levels, 10)
    s2 = np.percentile(levels, 20)
    s3 = np.percentile(levels, 30)

    r1 = np.percentile(levels, 70)
    r2 = np.percentile(levels, 80)
    r3 = np.percentile(levels, 90)

    price = df["close"].iloc[-1]
    rsi = df["RSI"].iloc[-1]
    ema20 = df["EMA20"].iloc[-1]
    ema50 = df["EMA50"].iloc[-1]

    volume_now = df["volume"].iloc[-1]
    volume_avg = df["volume"].tail(20).mean()

    # =========================
    # AI SIGNAL
    # =========================
    signal = "WAIT"
    entry = None

    if price > r1 and volume_now > volume_avg and ema20 > ema50:
        signal = "🚀 STRONG BUY"
        entry = price

    elif price <= s1 and rsi < 35:
        signal = "🟢 BUY AREA"
        entry = s1

    elif price < ema20 and ema20 < ema50:
        signal = "🔴 SELL"

    # =========================
    # METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Price", f"{price:.2f}")
    col2.metric("📊 RSI", f"{rsi:.2f}")
    col3.metric("📈 Volume", f"{volume_now:.2f}")

    st.write(f"🤖 Signal: {signal}")

    # =========================
    # CHART
    # =========================
    fig = go.Figure()

    # Candle
    fig.add_trace(go.Candlestick(
        x=df["time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Candle"
    ))

    # EMA
    fig.add_trace(go.Scatter(
        x=df["time"], y=df["EMA20"],
        name="EMA20", line=dict(color="blue")
    ))

    fig.add_trace(go.Scatter(
        x=df["time"], y=df["EMA50"],
        name="EMA50", line=dict(color="orange")
    ))

    # Support
    for lvl in [s1, s2, s3]:
        fig.add_hline(y=lvl, line_color="green", line_dash="dot")

    # Resistance
    for lvl in [r1, r2, r3]:
        fig.add_hline(y=lvl, line_color="red", line_dash="dot")

    # Entry marker
    if entry:
        fig.add_trace(go.Scatter(
            x=[df["time"].iloc[-1]],
            y=[entry],
            mode="markers",
            marker=dict(size=12, color="yellow"),
            name="ENTRY"
        ))

    # Volume
    fig.add_trace(go.Bar(
        x=df["time"],
        y=df["volume"],
        name="Volume",
        opacity=0.3,
        yaxis="y2"
    ))

    fig.update_layout(
        height=400,
        xaxis_rangeslider_visible=False,
        yaxis2=dict(overlaying="y", side="right")
    )

    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # ALERT
    # =========================
    if signal == "🚀 STRONG BUY":
        st.success("🔥 BREAKOUT TERDETEKSI!")

    elif signal == "🟢 BUY AREA":
        st.info("🟢 AREA BELI TERDETEKSI")

    elif signal == "🔴 SELL":
        st.warning("⚠️ TREND TURUN")

    st.divider()

# =========================
# FOOTER
# =========================
st.caption("⚡ Auto refresh aktif | Multi Coin Mode ON")

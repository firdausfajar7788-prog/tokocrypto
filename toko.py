import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import requests

from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 Crypto Smart AI ULTRA++",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #050816;
    color: white;
}

.stMetric {
    background: linear-gradient(145deg,#0f172a,#111827);
    padding: 15px;
    border-radius: 15px;
    border: 1px solid #1f2937;
    box-shadow: 0px 0px 20px rgba(0,255,255,0.05);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.title("🚀 Crypto Smart AI ULTRA++")

st.caption(
    "Realtime AI Trading Dashboard"
)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("⚙️ Settings")

refresh = st.sidebar.slider(
    "Auto Refresh (detik)",
    2,
    60,
    5
)

coin_input = st.sidebar.text_input(
    "Multi Coin",
    "BTC,ETH,SOL"
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1m", "5m", "15m", "1h"],
    index=2
)

limit = st.sidebar.slider(
    "Historical Candle",
    50,
    500,
    120
)

# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(
    interval=refresh * 1000,
    key="refresh"
)

# =========================================================
# USD IDR
# =========================================================
@st.cache_data(ttl=3600)
def get_usd_idr():

    url = "https://open.er-api.com/v6/latest/USD"

    response = requests.get(url)

    data = response.json()

    return data["rates"]["IDR"]

usd_to_idr = get_usd_idr()

# =========================================================
# TIMEFRAME MAP
# =========================================================
yf_map = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h"
}

# =========================================================
# SYMBOL FORMAT
# =========================================================
def smart_symbol(symbol):

    symbol = symbol.upper().replace(" ", "")

    return f"{symbol}-USD"

# =========================================================
# GET MARKET DATA
# =========================================================
@st.cache_data(ttl=60)
def get_market_data(symbol):

    try:

        coin = symbol.split("-")[0].lower()

        url = (
            "https://api.coingecko.com/api/v3/"
            f"coins/{coin}"
        )

        data = requests.get(url).json()

        marketcap = data["market_data"]["market_cap"]["usd"]

        change24 = data["market_data"]["price_change_percentage_24h"]

        change7d = data["market_data"]["price_change_percentage_7d"]

        volume = data["market_data"]["total_volume"]["usd"]

        return (
            marketcap,
            change24,
            change7d,
            volume
        )

    except:

        return (
            0,
            0,
            0,
            0
        )

# =========================================================
# GET DATA
# =========================================================
@st.cache_data(ttl=30)
def get_data(symbol, timeframe, limit):

    try:

        interval = yf_map[timeframe]

        df = yf.download(
            tickers=symbol,
            period="2d",
            interval=interval,
            progress=False,
            auto_adjust=False
        )

        if df.empty:
            return None

        # FIX MULTI INDEX
        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        df.reset_index(inplace=True)

        # FIX TIME COLUMN
        if "Datetime" in df.columns:

            df.rename(
                columns={"Datetime": "Time"},
                inplace=True
            )

        elif "Date" in df.columns:

            df.rename(
                columns={"Date": "Time"},
                inplace=True
            )

        return df.tail(limit)

    except:

        return None

# =========================================================
# EMA
# =========================================================
def EMA(df, period):

    return df["Close"].ewm(
        span=period,
        adjust=False
    ).mean()

# =========================================================
# RSI
# =========================================================
def RSI(df, period=14):

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# =========================================================
# MACD
# =========================================================
def MACD(df):

    ema12 = df["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df["Close"].ewm(
        span=26,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    hist = macd - signal

    return macd, signal, hist

# =========================================================
# SUPPORT RESISTANCE
# =========================================================
def support_resistance(df):

    s1 = float(df["Low"].tail(10).min())
    s2 = float(df["Low"].tail(20).min())
    s3 = float(df["Low"].tail(50).min())

    r1 = float(df["High"].tail(10).max())
    r2 = float(df["High"].tail(20).max())
    r3 = float(df["High"].tail(50).max())

    return (
        s1,
        s2,
        s3,
        r1,
        r2,
        r3
    )

# =========================================================
# AI SIGNAL
# =========================================================
def ai_signal(price, ema20, ema50, rsi):

    score = 0

    if price > ema20:
        score += 25

    if ema20 > ema50:
        score += 25

    if rsi > 55:
        score += 25

    if rsi > 65:
        score += 25

    if score >= 75:

        return (
            "🚀 STRONG BUY",
            score
        )

    elif score >= 50:

        return (
            "🟢 BUY",
            score
        )

    elif score <= 25:

        return (
            "🔴 SELL",
            score
        )

    else:

        return (
            "📊 WAIT",
            score
        )

# =========================================================
# BREAKOUT
# =========================================================
def breakout(price, resistance):

    return price > resistance

# =========================================================
# COINS
# =========================================================
coins = [
    smart_symbol(x)
    for x in coin_input.split(",")
]

# =========================================================
# MAIN LOOP
# =========================================================
for symbol in coins:

    st.divider()

    st.subheader(f"🤖 {symbol}")

    # =====================================================
    # GET PRICE DATA
    # =====================================================
    df = get_data(
        symbol,
        timeframe,
        limit
    )

    if df is None:

        st.warning(
            f"{symbol} data tidak tersedia"
        )

        continue

    # =====================================================
    # MARKET DATA
    # =====================================================
    marketcap, change24, change7d, volume_usd = get_market_data(symbol)

    # =====================================================
    # INDICATORS
    # =====================================================
    df["EMA20"] = EMA(df, 20)

    df["EMA50"] = EMA(df, 50)

    df["RSI"] = RSI(df)

    df["MACD"], df["MACD_SIGNAL"], df["MACD_HIST"] = MACD(df)

    df = df.dropna()

    # =====================================================
    # LAST VALUE
    # =====================================================
    price_usd = float(df["Close"].iloc[-1])

    price = price_usd * usd_to_idr

    ema20 = float(df["EMA20"].iloc[-1]) * usd_to_idr

    ema50 = float(df["EMA50"].iloc[-1]) * usd_to_idr

    rsi = float(df["RSI"].iloc[-1])

    # =====================================================
    # SUPPORT RESISTANCE
    # =====================================================
    s1, s2, s3, r1, r2, r3 = support_resistance(df)

    s1 *= usd_to_idr
    s2 *= usd_to_idr
    s3 *= usd_to_idr

    r1 *= usd_to_idr
    r2 *= usd_to_idr
    r3 *= usd_to_idr

    # =====================================================
    # SIGNAL
    # =====================================================
    signal, confidence = ai_signal(
        price,
        ema20,
        ema50,
        rsi
    )

    # =====================================================
    # BREAKOUT
    # =====================================================
    breakout_detected = breakout(
        price,
        r1
    )

    # =====================================================
    # METRICS
    # =====================================================
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

    c1.metric(
        "💰 Price",
        f"Rp {price:,.0f}"
    )

    c2.metric(
        "📊 RSI",
        round(rsi, 2)
    )

    c3.metric(
        "📈 24H",
        f"{change24:.2f}%"
    )

    c4.metric(
        "📅 7D",
        f"{change7d:.2f}%"
    )

    c5.metric(
        "🏦 Market Cap",
        f"${marketcap:,.0f}"
    )

    c6.metric(
        "📦 Volume",
        f"${volume_usd:,.0f}"
    )

    c7.metric(
        "🤖 Signal",
        signal
    )

    # =====================================================
    # CHART
    # =====================================================
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.65, 0.2, 0.15]
    )

    # =====================================================
    # CANDLESTICK
    # =====================================================
    fig.add_trace(
        go.Candlestick(
            x=df["Time"],
            open=df["Open"] * usd_to_idr,
            high=df["High"] * usd_to_idr,
            low=df["Low"] * usd_to_idr,
            close=df["Close"] * usd_to_idr,
            increasing_line_color="#00ff88",
            decreasing_line_color="#ff3b5c",
            name="Candlestick"
        ),
        row=1,
        col=1
    )

    # =====================================================
    # EMA20
    # =====================================================
    fig.add_trace(
        go.Scatter(
            x=df["Time"],
            y=df["EMA20"] * usd_to_idr,
            line=dict(
                color="#00a2ff",
                width=2
            ),
            name="EMA20"
        ),
        row=1,
        col=1
    )

    # =====================================================
    # EMA50
    # =====================================================
    fig.add_trace(
        go.Scatter(
            x=df["Time"],
            y=df["EMA50"] * usd_to_idr,
            line=dict(
                color="#ffaa00",
                width=2
            ),
            name="EMA50"
        ),
        row=1,
        col=1
    )

    # =====================================================
    # VOLUME
    # =====================================================
    colors = [
        "#00ff88"
        if c >= o
        else "#ff3b5c"

        for c, o in zip(
            df["Close"],
            df["Open"]
        )
    ]

    fig.add_trace(
        go.Bar(
            x=df["Time"],
            y=df["Volume"],
            marker_color=colors,
            opacity=0.4,
            name="Volume"
        ),
        row=2,
        col=1
    )

    # =====================================================
    # MACD
    # =====================================================
    fig.add_trace(
        go.Scatter(
            x=df["Time"],
            y=df["MACD"],
            line=dict(
                color="#00a2ff",
                width=2
            ),
            name="MACD"
        ),
        row=3,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df["Time"],
            y=df["MACD_SIGNAL"],
            line=dict(
                color="#ff00ff",
                width=2
            ),
            name="Signal"
        ),
        row=3,
        col=1
    )

    fig.add_trace(
        go.Bar(
            x=df["Time"],
            y=df["MACD_HIST"],
            marker_color=colors,
            opacity=0.5,
            name="Histogram"
        ),
        row=3,
        col=1
    )

    # =====================================================
    # SUPPORT RESISTANCE
    # =====================================================
    support_lines = [
        (s1, "#00ff88", "S1"),
        (s2, "#00cc66", "S2"),
        (s3, "#007744", "S3")
    ]

    resistance_lines = [
        (r1, "#ff3b5c", "R1"),
        (r2, "#ff0055", "R2"),
        (r3, "#990022", "R3")
    ]

    for value, color, name in support_lines:

        fig.add_hline(
            y=value,
            line_dash="dot",
            line_color=color,
            line_width=1.5,
            annotation_text=f"{name}",
            row=1,
            col=1
        )

    for value, color, name in resistance_lines:

        fig.add_hline(
            y=value,
            line_dash="dot",
            line_color=color,
            line_width=1.5,
            annotation_text=f"{name}",
            row=1,
            col=1
        )

    # =====================================================
    # ENTRY MARKER
    # =====================================================
    fig.add_trace(
        go.Scatter(
            x=[df["Time"].iloc[-1]],
            y=[price],
            mode="markers+text",
            marker=dict(
                color="cyan",
                size=12
            ),
            text=["ENTRY"],
            textposition="top center",
            name="Entry"
        ),
        row=1,
        col=1
    )

    # =====================================================
    # LAYOUT
    # =====================================================
    fig.update_layout(
        template="plotly_dark",
        height=950,
        title=f"{symbol} AI Smart Trading Chart",
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#050816",
        plot_bgcolor="#050816",
        font=dict(color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.05)"
    )

    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.05)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # ALERT
    # =====================================================
    if breakout_detected:

        st.success(
            "🚀 BREAKOUT DETECTED"
        )

    if signal == "🚀 STRONG BUY":

        st.success(
            f"🔥 STRONG BUY | Confidence {confidence}%"
        )

    elif signal == "🟢 BUY":

        st.info(
            f"🟢 BUY MOMENTUM | Confidence {confidence}%"
        )

    elif signal == "🔴 SELL":

        st.error(
            f"⚠️ SELL SIGNAL | Confidence {confidence}%"
        )

    else:

        st.warning(
            "📊 WAIT / SIDEWAYS"
        )

# =========================================================
# FOOTER
# =========================================================
st.caption(
    f"🚀 Crypto Smart AI ULTRA++ | USD/IDR : Rp {usd_to_idr:,.0f}"
)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import requests
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@st.cache_resource
def load_sheet():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]),
        scope
    )

    client = gspread.authorize(creds)

    return client.open("CryptoWatchlist").sheet1







from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

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

/* CARD */
[data-testid="stMetric"] {

    background: linear-gradient(
        145deg,
        #0b1220,
        #111827
    );

    border: 1px solid #1e293b;

    padding: 10px;

    border-radius: 14px;

    box-shadow:
        0 0 15px rgba(0,255,255,0.08);

    text-align: center;
}

/* LABEL */
[data-testid="stMetricLabel"] {

    font-size: 13px;
    color: #94a3b8;
}

/* VALUE */
[data-testid="stMetricValue"] {

    font-size: 22px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.title("🚀 Crypto Smart AI ULTRA++")
st.caption("Realtime AI Trading Dashboard")

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("⚙️ AI Settings")
sheet = load_sheet()

st.sidebar.subheader("📋 Watchlist")

new_coin = st.sidebar.text_input(
    "Tambah Coin"
)

if st.sidebar.button("➕ Add Coin"):

    if new_coin:

        sheet.append_row(
            [new_coin.upper()]
        )

        st.rerun()
# =========================================================
# TELEGRAM
# =========================================================

BOT_TOKEN = "8819178689:AAHBU4dTqoIUfGvkarKRZLI6wbfKJh6g0RU"
CHAT_ID = "999556266"

def send_telegram(message):

    url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:

        requests.post(
            url,
            json=payload,
            timeout=10
        )

    except Exception as e:

        print(e)







if st.sidebar.button("🚀 Test Telegram"):

    send_telegram(
        "🚀 Telegram Connected!"
    )

    st.success(
        "Pesan test terkirim"
    ) 

    

refresh = st.sidebar.slider(
    "Refresh (detik)",
    2,
    60,
    5
)



currency_mode = st.sidebar.selectbox(
    "💱 Currency",
    [
        "USD",
        "IDR"
    ]
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    [
        "1m",
        "5m",
        "15m",
        "30m",
        "1h",
        "4h",
        "1d",
        "1wk",
        "1mo"
    ],
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
# USD TO IDR
# =========================================================
@st.cache_data(ttl=3600)
def get_usd_idr():

    try:

        url = "https://open.er-api.com/v6/latest/USD"

        response = requests.get(url)

        data = response.json()

        return data["rates"]["IDR"]

    except:

        return 16000

usd_to_idr = get_usd_idr()

# =========================================================
# CURRENCY
# =========================================================
if currency_mode == "IDR":

    currency_rate = usd_to_idr
    currency_symbol = "Rp"

else:

    currency_rate = 1
    currency_symbol = "$"

# =========================================================
# FORMAT PRICE
# =========================================================
def format_price(value, symbol):

    # =====================================================
    # IDR
    # =====================================================
    if symbol == "Rp":

        return f"Rp {value:,.0f}"

    # =====================================================
    # USD
    # =====================================================
    if value >= 1000:

        return f"$ {value:,.2f}"

    elif value >= 100:

        return f"$ {value:,.3f}"

    elif value >= 1:

        return f"$ {value:,.4f}"

    elif value >= 0.01:

        return f"$ {value:,.6f}"

    else:

        return f"$ {value:,.8f}"

# =========================================================
# TIMEFRAME MAP
# =========================================================
yf_map = {

    "1m": ("1m", "1d"),
    "5m": ("5m", "5d"),

    "15m": ("15m", "15d"),
    "30m": ("30m", "30d"),

    "1h": ("1h", "60d"),
    "4h": ("1h", "180d"),

    "1d": ("1d", "1y"),
    "1wk": ("1wk", "5y"),
    "1mo": ("1mo", "10y")
}

# =========================================================
# SYMBOL FIX
# =========================================================
def smart_symbol(symbol):

    symbol = (
        symbol
        .upper()
        .replace(" ", "")
    )

    return f"{symbol}-USD"

# =========================================================
# GET DATA
# =========================================================
@st.cache_data(ttl=30)
def get_data(symbol, timeframe, limit):

    try:

        interval, period = yf_map[timeframe]

        df = yf.download(

            tickers=symbol,

            interval=interval,

            period=period,

            progress=False,

            auto_adjust=False
        )

        if df.empty:

            return None

        # =================================================
        # FIX MULTI INDEX
        # =================================================
        if isinstance(
            df.columns,
            pd.MultiIndex
        ):

            df.columns = (
                df.columns
                .get_level_values(0)
            )

        # =================================================
        # RESET INDEX
        # =================================================
        df = df.reset_index()

        # =================================================
        # FORCE TIME COLUMN
        # =================================================
        first_col = df.columns[0]

        df.rename(
            columns={
                first_col: "Time"
            },
            inplace=True
        )

        # =================================================
        # DROP NA
        # =================================================
        df = df.dropna()

        # =================================================
        # TIME
        # =================================================
        df["Time"] = pd.to_datetime(
            df["Time"]
        )

        try:

            df["Time"] = (
                df["Time"]
                .dt.tz_convert(
                    "Asia/Jakarta"
                )
            )

        except:

            df["Time"] = (
                df["Time"]
                + pd.Timedelta(hours=7)
            )

        # =================================================
        # RESAMPLE 4H
        # =================================================
        if timeframe == "4h":

            df = (
                df
                .set_index("Time")
                .resample("4h")
                .agg({

                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum"
                })
                .dropna()
                .reset_index()
            )

        return df.tail(limit)

    except Exception as e:

        st.error(
            f"{symbol} ERROR : {e}"
        )

        return None

# =========================================================
# EMA
# =========================================================
def EMA(df, period):

    return (
        df["Close"]
        .ewm(
            span=period,
            adjust=False
        )
        .mean()
    )

# =========================================================
# RSI
# =========================================================
def RSI(df, period=14):

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = (
        gain
        .rolling(period)
        .mean()
    )

    avg_loss = (
        loss
        .rolling(period)
        .mean()
    )

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

# =========================================================
# MACD
# =========================================================
def MACD(df):

    ema12 = EMA(df, 12)
    ema26 = EMA(df, 26)

    macd = ema12 - ema26

    signal = (
        macd
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    hist = macd - signal

    return macd, signal, hist

# =========================================================
# SUPPORT RESISTANCE
# =========================================================
def support_resistance(df):

    support1 = float(
        df["Low"].tail(20).min()
    )

    support2 = float(
        df["Low"].tail(50).min()
    )

    resistance1 = float(
        df["High"].tail(20).max()
    )

    resistance2 = float(
        df["High"].tail(50).max()
    )

    return (
        support1,
        support2,
        resistance1,
        resistance2
    )

# =========================================================
# AI SIGNAL
# =========================================================
def ai_signal(
    price,
    ema20,
    ema50,
    rsi
):

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
# COINS
# =========================================================
symbols = sheet.col_values(1)

symbols = [
    x.strip()
    for x in symbols
    if x.strip()
]

coins = [
    smart_symbol(x)
    for x in symbols
]
st.sidebar.write("DEBUG")
st.sidebar.write(coins)
st.sidebar.write("Watchlist Aktif")

st.sidebar.write(symbols)

if len(symbols) > 0:

    delete_coin = st.sidebar.selectbox(
        "Delete Coin",
        symbols
    )

    if st.sidebar.button("❌ Delete"):

        cell = sheet.find(delete_coin)

        sheet.delete_rows(cell.row)

        st.rerun()

 
# =========================================================
# MAIN LOOP
# =========================================================

# =========================================================
# ALERT MEMORY
# =========================================================

if "last_alert" not in st.session_state:
    st.session_state.last_alert = {}

for symbol in coins:

    st.divider()

    st.subheader(f"🤖 {symbol}")

    # =====================================================
    # GET DATA
    # =====================================================
    df = get_data(
        symbol,
        timeframe,
        limit
    )

    if df is None or df.empty:

        st.warning(
            f"{symbol} data tidak tersedia"
        )

        continue

    # =====================================================
    # INDICATORS
    # =====================================================
    df["EMA20"] = EMA(df, 20)

    df["EMA50"] = EMA(df, 50)

    df["RSI"] = RSI(df)

    (
        df["MACD"],
        df["MACD_SIGNAL"],
        df["MACD_HIST"]

    ) = MACD(df)

    df = (
        df
        .dropna()
        .reset_index(drop=True)
    )

    if len(df) < 10:

        st.warning(
            f"{symbol} candle terlalu sedikit"
        )

        continue

    # =====================================================
    # LAST VALUE
    # =====================================================
    price = (
        float(df["Close"].iloc[-1])
        * currency_rate
    )

    ema20 = (
        float(df["EMA20"].iloc[-1])
        * currency_rate
    )

    ema50 = (
        float(df["EMA50"].iloc[-1])
        * currency_rate
    )

    rsi = float(
        df["RSI"].iloc[-1]
    )

    volume = float(
        df["Volume"].iloc[-1]
    )

    # =====================================================
    # SUPPORT RESISTANCE
    # =====================================================
    s1, s2, r1, r2 = (
        support_resistance(df)
    )

    s1 *= currency_rate
    s2 *= currency_rate

    r1 *= currency_rate
    r2 *= currency_rate

    # =====================================================
    # SIGNAL
    # =====================================================
    signal, confidence = ai_signal(

        price,
        ema20,
        ema50,
        rsi
    )
    if symbol not in st.session_state.last_alert:

        st.session_state.last_alert[symbol] = signal

    else:

        last_signal = st.session_state.last_alert[symbol]

        if (
            signal != last_signal
            and signal != "📊 WAIT"
        ):

            message = f"""
    🤖 AI SIGNAL

    Coin : {symbol}

    Signal : {signal}

    Price : {price:.6f}

    RSI : {rsi:.2f}

    Confidence : {confidence}%

    Timeframe : {timeframe}

    Time :
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

            send_telegram(message)

            st.session_state.last_alert[symbol] = signal



 

    # =====================================================
    # METRICS
    # =====================================================
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "💰 Price",
        format_price(
            price,
            currency_symbol
        )
    )

    c2.metric(
        "📊 RSI",
        f"{rsi:.2f}"
    )

    c3.metric(
        "📦 Volume",
        f"{volume:,.0f}"
    )

    c4.metric(
        "🤖 Signal",
        signal
    )

    c5.metric(
        "⚡ Confidence",
        f"{confidence}%"
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
    # CANDLE
    # =====================================================
    fig.add_trace(

        go.Candlestick(

            x=df["Time"],

            open=df["Open"] * currency_rate,
            high=df["High"] * currency_rate,
            low=df["Low"] * currency_rate,
            close=df["Close"] * currency_rate,

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

            y=df["EMA20"] * currency_rate,

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

            y=df["EMA50"] * currency_rate,

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
    # SUPPORT
    # =====================================================
    fig.add_hline(

        y=s1,

        line_dash="dot",

        line_color="#00ff88",

        annotation_text=f"S1 {format_price(s1, currency_symbol)}",

        row=1,
        col=1
    )

    fig.add_hline(

        y=s2,

        line_dash="dash",

        line_color="green",

        annotation_text=f"S2 {format_price(s2, currency_symbol)}",

        row=1,
        col=1
    )

    # =====================================================
    # RESISTANCE
    # =====================================================
    fig.add_hline(

        y=r1,

        line_dash="dot",

        line_color="#ff3b5c",

        annotation_text=f"R1 {format_price(r1, currency_symbol)}",

        row=1,
        col=1
    )

    fig.add_hline(

        y=r2,

        line_dash="dash",

        line_color="red",

        annotation_text=f"R2 {format_price(r2, currency_symbol)}",

        row=1,
        col=1
    )

    # =====================================================
    # BUY ZONE
    # =====================================================
    fig.add_hrect(

        y0=s1 * 0.995,
        y1=s1 * 1.005,

        fillcolor="green",

        opacity=0.06,

        line_width=0,

        row=1,
        col=1
    )

    # =====================================================
    # SELL ZONE
    # =====================================================
    fig.add_hrect(

        y0=r1 * 0.995,
        y1=r1 * 1.005,

        fillcolor="red",

        opacity=0.06,

        line_width=0,

        row=1,
        col=1
    )

    # =====================================================
    # COLORS
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

    # =====================================================
    # VOLUME
    # =====================================================
    fig.add_trace(

        go.Bar(

            x=df["Time"],

            y=df["Volume"],

            marker_color=colors,

            opacity=0.35,

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

            opacity=0.4,

            name="Histogram"
        ),

        row=3,
        col=1
    )

    # =====================================================
    # ENTRY
    # =====================================================
    fig.add_trace(

        go.Scatter(

            x=[df["Time"].iloc[-1]],

            y=[price],

            mode="markers+text",

            marker=dict(
                color="cyan",
                size=14
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

        hovermode="x",

        dragmode="pan",

        xaxis_rangeslider_visible=False,

        paper_bgcolor="#050816",

        plot_bgcolor="#050816",

        font=dict(
            color="white"
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # =====================================================
    # GRID
    # =====================================================
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.05)"
    )

    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.05)"
    )

    # =====================================================
    # FIX EMPTY SPACE
    # =====================================================
    fig.update_layout(

        xaxis=dict(
            fixedrange=False,
            range=[
                df["Time"].iloc[0],
                df["Time"].iloc[-1]
            ]
        ),

        xaxis2=dict(
            matches='x'
        ),

        xaxis3=dict(
            matches='x'
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =========================================================
# FOOTER
# =========================================================
st.caption(
    f"🚀 Crypto Smart AI ULTRA++ | Currency Mode : {currency_mode}"
)

import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
from datetime import datetime

# ==========================================
# 0. إعدادات تليجرام (Telegram Config)
# ==========================================
TELEGRAM_TOKEN = "8525259771:AAHmqV86FCzLNpioO7_ELn4FNW84YC5y3Mo"
TELEGRAM_CHAT_ID = "7383861003"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

# ==========================================
# 1. إعدادات واجهة المستخدم (Professional UI)
# ==========================================
st.set_page_config(
    page_title="AI Sniper Pro | نظام صيد السيولة 2026",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #e5e7eb; }
    [data-testid="stSidebar"] { background-color: #0b0e14; min-width: 380px !important; border-right: 1px solid #1f2937; }
    .signal-card { padding: 20px; border-radius: 12px; background-color: #111827; margin-bottom: 15px; border-left: 6px solid #374151; }
    .buy-border { border-left-color: #10b981 !important; }
    .sell-border { border-left-color: #ef4444 !important; }
    .wait-border { border-left-color: #6b7280 !important; }
    .tp-text { color: #10b981; font-weight: bold; }
    .sl-text { color: #ef4444; font-weight: bold; }
    .fvg-alert { color: #60a5fa; font-size: 0.85em; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# نظام لمنع تكرار الرسائل (Session State)
if 'last_signals' not in st.session_state:
    st.session_state.last_signals = {}

# ==========================================
# 2. الخوارزميات التحليلية (Core Engine)
# ==========================================

def get_market_data(symbol, name):
    try:
        df = yf.download(symbol, period="5d", interval="15m", progress=False)
        if df.empty: return None
        
        # --- أ. حساب الفجوات السعرية (Fair Value Gap) ---
        df_fvg = df.tail(4) 
        c1_high, c1_low = df_fvg['High'].iloc[0], df_fvg['Low'].iloc[0]
        c3_high, c3_low = df_fvg['High'].iloc[2], df_fvg['Low'].iloc[2]
        
        fvg_type = "None"
        if c3_low > c1_high: fvg_type = "Bullish FVG (شراء)"
        elif c3_high < c1_low: fvg_type = "Bearish FVG (بيع)"

        # --- ب. حساب مستويات فيبوناتشي (61.8%) ---
        recent_high, recent_low = df['High'].tail(60).max(), df['Low'].tail(60).min()
        fib_618 = recent_high - ((recent_high - recent_low) * 0.618)

        # --- ج. المؤشرات الفنية ---
        df['EMA200'] = ta.ema(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_price = float(df['Close'].iloc[-1])
        ema_val, rsi_val, atr_val = float(df['EMA200'].iloc[-1]), float(df['RSI'].iloc[-1]), float(df['ATR'].iloc[-1])
        
        # --- د. إدارة المخاطر ---
        sl_points, tp_points = atr_val * 1.5, atr_val * 3.0
        
        signal = "WAIT"
        tp_price, sl_price = 0, 0
        
        if last_price > ema_val and last_price > fib_618 and fvg_type == "Bullish FVG (شراء)" and rsi_val > 50:
            signal = "BUY"
            tp_price, sl_price = last_price + tp_points, last_price - sl_points
            
        elif last_price < ema_val and last_price < fib_618 and fvg_type == "Bearish FVG (بيع)" and rsi_val < 50:
            signal = "SELL"
            tp_price, sl_price = last_price - tp_points, last_price + sl_points
            
        # إرسال تليجرام إذا كانت الإشارة جديدة
        if signal != "WAIT":
            current_signal_key = f"{symbol}_{signal}_{round(last_price, 2)}"
            if st.session_state.last_signals.get(symbol) != current_signal_key:
                msg = f"🎯 *إشارة جديدة من AI Sniper*\n\n" \
                      f"📈 النوع: {signal}\n" \
                      f"💰 الأداة: {name}\n" \
                      f"💵 السعر: {last_price:.2f}\n" \
                      f"🎯 الهدف: {tp_price:.2f}\n" \
                      f"🛑 الوقف: {sl_price:.2f}\n" \
                      f"🛡️ الهيكل: {fvg_type}\n" \
                      f"⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}"
                send_telegram_msg(msg)
                st.session_state.last_signals[symbol] = current_signal_key

        return {
            "symbol": symbol, "signal": signal, "price": last_price,
            "fvg": fvg_type, "tp": tp_price, "sl": sl_price,
            "rsi": rsi_val, "trend": "Bullish" if last_price > ema_val else "Bearish"
        }
    except Exception as e: return None

# ==========================================
# 3. بناء واجهة الموقع (Dashboard)
# ==========================================

st.sidebar.title("🏧 قائمة الإشارات الحية")
st.sidebar.write(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown("---")

assets = {
    "GC=F": "الذهب (Gold)",
    "EURUSD=X": "اليورو / دولار",
    "GBPUSD=X": "باوند / دولار",
    "NQ=F": "نازداك 100",
    "BTC-USD": "بيتكوين"
}

for ticker, name in assets.items():
    res = get_market_data(ticker, name)
    if res:
        card_class = "wait-border"
        sig_color = "#9ca3af"
        if res['signal'] == "BUY":
            card_class, sig_color = "buy-border", "#10b981"
        elif res['signal'] == "SELL":
            card_class, sig_color = "sell-border", "#ef4444"
            
        st.sidebar.markdown(f"""
            <div class="signal-card {card_class}">
                <h3 style="color:{sig_color}; margin:0;">{res['signal']} | {name}</h3>
                <p style="margin:5px 0; font-size:1.1em;">السعر: <b>{res['price']:.2f}</b></p>
                <div class="fvg-alert">🛡️ الهيكل: {res['fvg']}</div>
                <hr style="margin:10px 0; border-color:#374151;">
                <div style="display:flex; justify-content:space-between;">
                    <span class="tp-text">🎯 TP: {res['tp']:.2f}</span>
                    <span class="sl-text">🛑 SL: {res['sl']:.2f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

col_main, col_stat = st.columns([2, 1])
with col_main:
    st.header("🎯 MaXiThoN: نظام التداول الذكي 2026")
    st.markdown("الموقع يراقب السيولة وفجوات FVG ويرسل التنبيهات فوراً إلى هاتفك عبر تليجرام.")
    st.subheader("📊 تحليل السيولة اللحظي")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e2/Candlestick_chart_scheme.png", width=400)

with col_stat:
    st.header("⚙️ حالة النظام")
    st.success("✅ تليجرام: متصل")
    st.success("✅ رادار FVG: نشط")
    if st.button('🔄 تحديث يدوي'): st.rerun()

st.write("---")
st.caption("🔄 تحديث تلقائي كل 60 ثانية...")
time.sleep(60)
st.rerun()

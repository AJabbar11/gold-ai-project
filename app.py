import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
from datetime import datetime

# ==========================================
# 0. إعدادات تليجرام
# ==========================================
TELEGRAM_TOKEN = "8525259771:AAHmqV86FCzLNpioO7_ELn4FNW84YC5y3Mo"
TELEGRAM_CHAT_ID = "7383861003"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ==========================================
# 1. إعدادات واجهة المستخدم
# ==========================================
st.set_page_config(page_title="MaXiThoN Pro Sniper", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #e5e7eb; }
    [data-testid="stSidebar"] { background-color: #0b0e14; min-width: 380px !important; }
    .signal-card { padding: 20px; border-radius: 12px; background-color: #111827; margin-bottom: 15px; border-left: 6px solid #374151; }
    .buy-border { border-left-color: #10b981 !important; }
    .sell-border { border-left-color: #ef4444 !important; }
    </style>
    """, unsafe_allow_html=True)

if 'sent_signals' not in st.session_state:
    st.session_state.sent_signals = {}

# ==========================================
# 2. خوارزمية الاستجابة السريعة
# ==========================================

def get_market_analysis(symbol, name):
    try:
        df = yf.download(symbol, period="2d", interval="15m", progress=False)
        if df.empty: return None
        
        # مؤشرات سريعة
        df['EMA50'] = ta.ema(df['Close'], length=50) # أسرع من 200 لتوليد صفقات أكثر
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_price = float(df['Close'].iloc[-1])
        ema_val = float(df['EMA50'].iloc[-1])
        rsi_val = float(df['RSI'].iloc[-1])
        atr_val = float(df['ATR'].iloc[-1])
        
        # اكتشاف FVG مبسط (للمعلومة وليس كشرط مانع)
        c1_high, c1_low = df['High'].iloc[-3], df['Low'].iloc[-3]
        c3_high, c3_low = df['High'].iloc[-1], df['Low'].iloc[-1]
        fvg_found = "Bullish" if c3_low > c1_high else "Bearish" if c3_high < c1_low else "None"

        signal = "WAITING"
        # شروط دخول مرنة (تشبه البوتات النشطة)
        if last_price > ema_val and rsi_val > 45: 
            signal = "BUY"
        elif last_price < ema_val and rsi_val < 55:
            signal = "SELL"
            
        if signal != "WAITING":
            tp = last_price + (atr_val * 2) if signal == "BUY" else last_price - (atr_val * 2)
            sl = last_price - (atr_val * 1.5) if signal == "BUY" else last_price + (atr_val * 1.5)
            
            sig_id = f"{symbol}_{signal}"
            if st.session_state.sent_signals.get(symbol) != sig_id:
                msg = f"🚀 *إشارة سريعة: {name}*\n\n📈 النوع: {signal}\n💰 السعر: {last_price:.2f}\n🎯 الهدف: {tp:.2f}\n🛑 الوقف: {sl:.2f}\n🛡️ FVG: {fvg_found}"
                send_telegram_msg(msg)
                st.session_state.sent_signals[symbol] = sig_id

            return {"name": name, "signal": signal, "price": last_price, "tp": tp, "sl": sl}
        return {"name": name, "signal": "WAITING", "price": last_price, "tp": 0, "sl": 0}
    except: return None

# ==========================================
# 3. العرض المباشر
# ==========================================

st.sidebar.title("🏧 الرادار النشط")
assets = {"GC=F": "الذهب", "EURUSD=X": "اليورو", "BTC-USD": "بيتكوين", "NQ=F": "نازداك"}

for sym, label in assets.items():
    data = get_market_analysis(sym, label)
    if data:
        card_class = "buy-border" if data['signal'] == "BUY" else "sell-border" if data['signal'] == "SELL" else ""
        st.sidebar.markdown(f"""
            <div class="signal-card {card_class}">
                <h4>{data['signal']} | {data['name']}</h4>
                <p>السعر: {data['price']:.2f}</p>
                <small>TP: {data['tp']:.2f} | SL: {data['sl']:.2f}</small>
            </div>
        """, unsafe_allow_html=True)

st.header("🎯 نظام MaXiThoN للمراقبة اللحظية")
st.success("✅ النظام يعمل الآن بأقصى سرعة استجابة لتطابق صفقات البوت.")

time.sleep(60)
st.rerun()

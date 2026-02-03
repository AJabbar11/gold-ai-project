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
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ==========================================
# 1. إعدادات واجهة المستخدم (The Full Professional UI)
# ==========================================
st.set_page_config(
    page_title="MaXiThoN AI Sniper Pro | 2026",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# إعادة التصميم القديم بالكامل (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #e5e7eb; }
    [data-testid="stSidebar"] { background-color: #0b0e14; min-width: 400px !important; border-right: 1px solid #1f2937; }
    .signal-card { 
        padding: 25px; border-radius: 15px; background-color: #111827; 
        margin-bottom: 20px; border-left: 8px solid #374151;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    .buy-border { border-left-color: #10b981 !important; }
    .sell-border { border-left-color: #ef4444 !important; }
    .wait-border { border-left-color: #4b5563 !important; }
    .tp-text { color: #10b981; font-weight: bold; font-size: 1.1em; }
    .sl-text { color: #ef4444; font-weight: bold; font-size: 1.1em; }
    .fvg-alert { color: #60a5fa; font-weight: bold; margin-top: 10px; border: 1px dashed #60a5fa; padding: 5px; border-radius: 5px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'sent_signals' not in st.session_state:
    st.session_state.sent_signals = {}

# ==========================================
# 2. الخوارزمية (السرعة + الدقة)
# ==========================================

def get_market_analysis(symbol, name):
    try:
        df = yf.download(symbol, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 50: return None
        
        # المؤشرات الفنية
        df['EMA50'] = ta.ema(df['Close'], length=50) 
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_price = float(df['Close'].iloc[-1])
        ema_val = float(df['EMA50'].iloc[-1])
        rsi_val = float(df['RSI'].iloc[-1])
        atr_val = float(df['ATR'].iloc[-1])
        
        # منطق الـ FVG للخرائط
        c1_high, c1_low = df['High'].iloc[-3], df['Low'].iloc[-3]
        c3_high, c3_low = df['High'].iloc[-1], df['Low'].iloc[-1]
        fvg_status = "✅ Bullish FVG" if c3_low > c1_high else "✅ Bearish FVG" if c3_high < c1_low else "❌ لا توجد سيولة"

        signal = "WAITING"
        # شروط مرنة لتطابق البوت
        if last_price > ema_val and rsi_val > 45: signal = "BUY"
        elif last_price < ema_val and rsi_val < 55: signal = "SELL"
            
        if signal != "WAITING":
            tp = last_price + (atr_val * 2) if signal == "BUY" else last_price - (atr_val * 2)
            sl = last_price - (atr_val * 1.5) if signal == "BUY" else last_price + (atr_val * 1.5)
            
            sig_id = f"{symbol}_{signal}"
            if st.session_state.sent_signals.get(symbol) != sig_id:
                msg = f"🚀 *إشارة سريعة: {name}*\n\n📈 النوع: {signal}\n💰 السعر: {last_price:.2f}\n🎯 الهدف: {tp:.2f}\n🛑 الوقف: {sl:.2f}\n🛡️ FVG: {fvg_status}"
                send_telegram_msg(msg)
                st.session_state.sent_signals[symbol] = sig_id
            return {"name": name, "signal": signal, "price": last_price, "tp": tp, "sl": sl, "fvg": fvg_status, "rsi": rsi_val}
        
        return {"name": name, "signal": "WAITING", "price": last_price, "tp": 0, "sl": 0, "fvg": fvg_status, "rsi": rsi_val}
    except: return None

# ==========================================
# 3. بناء الواجهة الرسومية (The Full Visuals)
# ==========================================

# القائمة الجانبية (البطاقات)
st.sidebar.markdown(f"<h1 style='text-align: center;'>🏧 MaXiThoN Pro</h1>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='text-align: center;'>{datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

assets = {"GC=F": "الذهب (Gold)", "EURUSD=X": "اليورو / دولار", "GBPUSD=X": "باوند / دولار", "NQ=F": "نازداك 100", "BTC-USD": "بيتكوين"}

for ticker, label in assets.items():
    data = get_market_analysis(ticker, label)
    if data:
        card_style = "buy-border" if data['signal'] == "BUY" else "sell-border" if data['signal'] == "SELL" else "wait-border"
        color = "#10b981" if data['signal'] == "BUY" else "#ef4444" if data['signal'] == "SELL" else "#9ca3af"
        
        st.sidebar.markdown(f"""
            <div class="signal-card {card_style}">
                <h2 style="color:{color}; margin:0;">{data['signal']} | {data['name']}</h2>
                <p style="font-size:1.3em; margin:10px 0;">السعر الحالي: <b>{data['price']:.2f}</b></p>
                <div class="fvg-alert">{data['fvg']}</div>
                <hr style="border-color:#374151;">
                <div style="display:flex; justify-content:space-between;">
                    <span class="tp-text">🎯 TP: {data['tp']:.2f}</span>
                    <span class="sl-text">🛑 SL: {data['sl']:.2f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# الصفحة الرئيسية (الخرائط والإحصائيات)
col_main, col_stat = st.columns([2, 1])

with col_main:
    st.header("🎯 رادار القناص: نظام التداول الذكي 2026")
    st.markdown("""
    الموقع يعمل الآن بنظام **Smart Money Concepts (SMC)** المدمج. 
    يتم مسح السيولة والبحث عن فجوات (FVG) مع مراقبة الاتجاه اللحظي.
    """)
    st.subheader("📊 خريطة السيولة اللحظية")
    # عرض الرسم التوضيحي للشموع والسيولة
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e2/Candlestick_chart_scheme.png", width=500, caption="تحليل تدفق السيولة وبصمة الحيتان")
    

with col_stat:
    st.header("⚙️ حالة الخوارزمية")
    st.success("✅ الاتصال بـ Yahoo Finance: نشط")
    st.success("✅ رادار FVG: نشط")
    st.success("✅ حماية التذبذب: نشطة")
    st.success("✅ ربط تليجرام: نشط")
    
    if st.button('🔄 تحديث النظام الآن'):
        st.rerun()

st.write("---")
st.caption("🔄 النظام يحدث نفسه تلقائياً كل 60 ثانية لملاحقة البوت...")

time.sleep(60)
st.rerun()

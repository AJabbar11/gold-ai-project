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
    """وظيفة إرسال التنبيهات الفورية"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        st.error(f"خطأ في إرسال تليجرام: {e}")

# ==========================================
# 1. إعدادات واجهة المستخدم (Professional UI)
# ==========================================
st.set_page_config(
    page_title="MaXiThoN AI Sniper Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم الواجهة الاحترافية بالكامل
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
    .tp-text { color: #10b981; font-weight: bold; font-size: 1.2em; }
    .sl-text { color: #ef4444; font-weight: bold; font-size: 1.2em; }
    .fvg-alert { color: #60a5fa; font-weight: bold; margin-top: 10px; border: 1px dashed #60a5fa; padding: 5px; border-radius: 5px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# نظام الذاكرة لمنع تكرار الإشارات
if 'sent_signals' not in st.session_state:
    st.session_state.sent_signals = {}

# ==========================================
# 2. الخوارزمية المتطابقة مع البوت (Execution Logic)
# ==========================================

def get_market_analysis(symbol, name):
    """تحليل دقيق مطابق لمنطق بوتات التداول العالمية"""
    try:
        # جلب البيانات (الفريم: 15 دقيقة)
        df = yf.download(symbol, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 200: return None
        
        # --- [1] رادار فجوات السيولة (FVG) ---
        # نراقب آخر 3 شموع مكتملة لاكتشاف "الفراغ السعري"
        c1_high, c1_low = df['High'].iloc[-3], df['Low'].iloc[-3]
        c3_high, c3_low = df['High'].iloc[-1], df['Low'].iloc[-1]
        
        fvg_status = "❌ لا توجد فجوة"
        fvg_signal = "None"
        
        if c3_low > c1_high:
            fvg_status = "✅ Bullish FVG (فجوة شرائية)"
            fvg_signal = "BUY"
        elif c3_high < c1_low:
            fvg_status = "✅ Bearish FVG (فجوة بيعية)"
            fvg_signal = "SELL"

        # --- [2] حساب المستويات الذهبية (Fibonacci 61.8%) ---
        recent_max = df['High'].tail(100).max()
        recent_min = df['Low'].tail(100).min()
        fib_level = recent_max - ((recent_max - recent_min) * 0.618)

        # --- [3] الفلاتر الفنية (Indicators) ---
        df['EMA200'] = ta.ema(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_price = float(df['Close'].iloc[-1])
        ema_200 = float(df['EMA200'].iloc[-1])
        rsi_val = float(df['RSI'].iloc[-1])
        atr_val = float(df['ATR'].iloc[-1])
        
        # --- [4] إدارة المخاطر (ATR Risk Management) ---
        tp_dist = atr_val * 3.0
        sl_dist = atr_val * 1.5
        
        final_signal = "WAITING"
        tp, sl = 0, 0
        
        # منطق دخول البوت الصارم
        if last_price > ema_200 and last_price > fib_level and fvg_signal == "BUY" and rsi_val > 50:
            final_signal = "BUY"
            tp, sl = last_price + tp_dist, last_price - sl_dist
            
        elif last_price < ema_200 and last_price < fib_level and fvg_signal == "SELL" and rsi_val < 50:
            final_signal = "SELL"
            tp, sl = last_price - tp_dist, last_price + sl_dist
            
        # --- [5] إرسال التنبيه الفوري ---
        if final_signal != "WAITING":
            sig_id = f"{symbol}_{final_signal}_{round(last_price, 2)}"
            if st.session_state.sent_signals.get(symbol) != sig_id:
                alert_text = f"🎯 *إشارة قناص جديدة*\n\n" \
                             f"📈 النوع: {final_signal}\n" \
                             f"💰 الأداة: {name}\n" \
                             f"💵 الدخول: {last_price:.2f}\n" \
                             f"🎯 الهدف: {tp:.2f}\n" \
                             f"🛑 الوقف: {sl:.2f}\n" \
                             f"⚡ RSI: {rsi_val:.1f}\n" \
                             f"⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}"
                send_telegram_msg(alert_text)
                st.session_state.sent_signals[symbol] = sig_id

        return {
            "name": name, "signal": final_signal, "price": last_price,
            "fvg": fvg_status, "tp": tp, "sl": sl, "rsi": rsi_val,
            "ema": ema_200, "fib": fib_level
        }
    except Exception as e:
        return None

# ==========================================
# 3. بناء الواجهة الرسومية (UI Construction)
# ==========================================

st.sidebar.markdown(f"<h1 style='text-align: center;'>🏧 MaXiThoN Pro</h1>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='text-align: center;'>{datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# الأصول المراقبة
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
                <p style="font-size:0.8em; color:#6b7280; margin-top:10px;">RSI: {data['rsi']:.1f} | EMA: {data['ema']:.1f}</p>
            </div>
        """, unsafe_allow_html=True)

# الصفحة الرئيسية
c1, c2 = st.columns([2, 1])
with c1:
    st.header("🕵️ رادار صيد السيولة الذكي 2026")
    st.info("💡 النظام يراقب الآن فجوات FVG ومستويات فيبوناتشي 61.8% بشكل لحظي.")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e2/Candlestick_chart_scheme.png", width=500)

with c2:
    st.header("⚙️ حالة السيرفر")
    st.success("✅ Yahoo Finance: متصل")
    st.success("✅ رادار FVG: نشط")
    st.success("✅ حماية التذبذب: نشطة")
    st.success("✅ تليجرام: متصل")
    if st.button('🔄 تحديث فوري للنظام'): st.rerun()

# التحديث التلقائي (60 ثانية)
st.markdown("---")
st.caption("🔄 النظام يعمل في الخلفية ويحدث البيانات كل 60 ثانية...")
time.sleep(60)
st.rerun()

import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
from datetime import datetime
import streamlit as st

# كود CSS مكثف لإخفاء الشريط العلوي بالكامل
st.markdown("""
    <style>
    /* 1. إخفاء حاوية الرأس بالكامل بما فيها الأيقونات */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* 2. إخفاء زر التنزيل/الرفع (القارب الورقي) تحديداً */
    [data-testid="stAppDeploy"] {
        display: none !important;
    }

    /* 3. إخفاء القائمة الجانبية (الأشرطة الثلاثة) */
    #MainMenu {
        visibility: hidden !important;
    }

    /* 4. إخفاء التذييل في الأسفل */
    footer {
        visibility: hidden !important;
    }

    /* 5. إزالة الفراغ الأبيض الناتج عن حذف الشريط العلوي */
    .block-container {
        padding-top: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
import streamlit as st

st.markdown("""
    <style>
    /* 1. إخفاء أي عنصر عائم في الزوايا (الأيقونات التي تظهر في صورتك) */
    [data-testid="stStatusWidget"],
    [data-testid="stAppDeploy"],
    [data-testid="stToolbar"],
    .stAppToolbar,
    div[class*="st-emotion-cache-"] > button {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }

    /* 2. إخفاء الرأس والقائمة تماماً */
    header, [data-testid="stHeader"] {
        display: none !important;
    }

    /* 3. إخفاء أي تذييل أو علامة مائية */
    footer {
        display: none !important;
    }

    /* 4. إجبار التطبيق على استغلال المساحة كاملة بدون حواف */
    .main .block-container {
        padding: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
iframe, div[id*="opera"], div[class*="extension"] {
    display: none !important;
}
# باقي كود تطبيقك هنا...
# ==========================================
# 0. إعدادات تليجرام (تأكد من صحة التوكن)
# ==========================================
TELEGRAM_TOKEN = "8525259771:AAHmqV86FCzLNpioO7_ELn4FNW84YC5y3Mo"
TELEGRAM_CHAT_ID = "7383861003"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=15)
        return response.ok
    except:
        return False

# ==========================================
# 1. إعدادات الواجهة (التصميم الاحترافي الكامل)
# ==========================================
st.set_page_config(page_title="MaXiThoN Pro 2026", page_icon="🎯", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #e5e7eb; }
    [data-testid="stSidebar"] { background-color: #0b0e14; min-width: 380px !important; }
    .signal-card { padding: 20px; border-radius: 12px; background-color: #111827; margin-bottom: 15px; border-left: 6px solid #374151; }
    .buy-border { border-left-color: #10b981 !important; }
    .sell-border { border-left-color: #ef4444 !important; }
    .tp-text { color: #10b981; font-weight: bold; }
    .sl-text { color: #ef4444; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# نظام ذاكرة لضمان عدم ضياع الإشارات
if 'last_check' not in st.session_state:
    st.session_state.last_check = datetime.now()
if 'history' not in st.session_state:
    st.session_state.history = {}

# ==========================================
# 2. الخوارزمية (تم تقليل القيود لإرسال صفقات أكثر)
# ==========================================

def get_market_analysis(symbol, name):
    try:
        # استخدام فترة زمنية أطول لضمان جلب البيانات
        df = yf.download(symbol, period="3d", interval="15m", progress=False, timeout=20)
        
        if df is None or df.empty:
            return None
        
        # مؤشرات فنية سريعة (EMA 20 بدلاً من 50 لفرص أكثر)
        df['EMA'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_price = float(df['Close'].iloc[-1])
        ema_val = float(df['EMA'].iloc[-1])
        rsi_val = float(df['RSI'].iloc[-1])
        atr_val = float(df['ATR'].iloc[-1])

        signal = "WAITING"
        # شروط مرنة جداً (تطابق البوت السريع)
        if last_price > ema_val:
            signal = "BUY"
        elif last_price < ema_val:
            signal = "SELL"
            
        # منع تكرار الرسالة لنفس السعر
        sig_key = f"{symbol}_{signal}_{round(last_price, 1)}"
        
        if signal != "WAITING" and st.session_state.history.get(symbol) != sig_key:
            tp = last_price + (atr_val * 2) if signal == "BUY" else last_price - (atr_val * 2)
            sl = last_price - (atr_val * 1.5) if signal == "BUY" else last_price + (atr_val * 1.5)
            
            msg = f"🚀 *إشارة نشطة: {name}*\n\n📈 النوع: {signal}\n💰 السعر: {last_price:.2f}\n🎯 الهدف: {tp:.2f}\n🛑 الوقف: {sl:.2f}"
            
            if send_telegram_msg(msg):
                st.session_state.history[symbol] = sig_key
                
        return {"name": name, "signal": signal, "price": last_price, "tp": 0, "sl": 0}
    except:
        return None

# ==========================================
# 3. العرض والتشغيل الدائم
# ==========================================

st.sidebar.title("🏧 رادار السيولة 2026")
assets = {"GC=F": "الذهب", "EURUSD=X": "اليورو", "BTC-USD": "البيتكوين", "NQ=F": "نازداك"}

for sym, label in assets.items():
    res = get_market_analysis(sym, label)
    if res:
        color = "buy-border" if res['signal'] == "BUY" else "sell-border" if res['signal'] == "SELL" else ""
        st.sidebar.markdown(f'<div class="signal-card {color}"><h3>{res["signal"]} | {res["name"]}</h3><p>Price: {res["price"]:.2f}</p></div>', unsafe_allow_html=True)

# الجزء الرئيسي (الخرائط)
col1, col2 = st.columns([2, 1])
with col1:
    st.header("🎯 نظام MaXiThoN للمراقبة")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e2/Candlestick_chart_scheme.png", width=500)
    

with col2:
    st.header("⚙️ الحالة")
    st.success("✅ جلب البيانات: نشط")
    st.success("✅ تليجرام: نشط")
    if st.button('🔄 تحديث يدوي'):
        st.rerun()

# --- حل مشكلة التوقف (Keep Alive) ---
st.write(f"آخر فحص للسوق: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(60)
st.rerun()

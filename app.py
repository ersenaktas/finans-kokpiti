import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföyü", layout="wide", page_icon="🚀")

st.title("🚀 Finansal Özgürlük Kokpiti")

# --- 1. PİYASA NABZI (YENİ EKLENEN BÖLÜM) ---
# Burası "Dışarıda hava nasıl?" sorusunun cevabıdır.
@st.cache_data(ttl=60)
def get_market_pulse():
    # XU100.IS = Bist 100
    # NQ=F = Nasdaq 100 (YAY için)
    # GC=F = Altın Ons
    # TRY=X = Dolar/TL
    tickers = ["XU100.IS", "NQ=F", "GC=F", "TRY=X"]
    
    try:
        data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
        return data
    except:
        return None

market_data = get_market_pulse()

st.subheader("📊 Piyasa Durumu (Canlı)")
m1, m2, m3, m4 = st.columns(4)

if market_data is not None:
    # BIST 100
    bist_now = market_data['XU100.IS']['Close'].iloc[-1]
    bist_prev = market_data['XU100.IS']['Close'].iloc[-2]
    bist_delta = ((bist_now - bist_prev) / bist_prev) * 100
    m1.metric("BIST 100 (YAS)", f"{bist_now:,.0f}", f"%{bist_delta:.2f}")

    # NASDAQ
    nas_now = market_data['NQ=F']['Close'].iloc[-1]
    nas_prev = market_data['NQ=F']['Close'].iloc[-2]
    nas_delta = ((nas_now - nas_prev) / nas_prev) * 100
    m2.metric("NASDAQ (YAY)", f"{nas_now:,.0f}", f"%{nas_delta:.2f}")

    # DOLAR
    usd_now = market_data['TRY=X']['Close'].iloc[-1]
    usd_prev = market_data['TRY=X']['Close'].iloc[-2]
    usd_delta = ((usd_now - usd_prev) / usd_prev) * 100
    m3.metric("Dolar/TL", f"{usd_now:.2f}", f"%{usd_delta:.2f}")

    # ONS ALTIN
    ons_now = market_data['GC=F']['Close'].iloc[-1]
    ons_prev = market_data['GC=F']['Close'].iloc[-2]
    ons_delta = ((ons_now - ons_prev) / ons_prev) * 100
    m4.metric("Ons Altın", f"${ons_now:,.0f}", f"%{ons_delta:.2f}")

st.markdown("---")

# --- 2. KAYSERİ'DEN VERİ ÇEKME ---
@st.cache_data(ttl=900) 
def get_kayseri_ziynet():
    url = "https://www.kaysarder.org.tr/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    prices = {"ceyrek": 0.0, "tam": 0.0, "bilezik22": 0.0, "status": False, "source": "Manuel"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.find_all("tr")
            for row in rows:
                text = row.get_text().upper().strip()
                cols = row.find_all("td")
                if len(cols) >= 2:
                    try:
                        price_text = cols[-1].get_text().replace(".", "").replace(",", ".").replace("₺", "").strip()
                        price = float(price_text)
                        if "25" in text and "ZİYNET" in text: prices["ceyrek"] = price
                        elif "25" in text and prices["ceyrek"] == 0: prices["ceyrek"] = price
                        if "100" in text or "TAM" in text:
                            if "2.5" not in text: prices["tam"] = price
                        if "22" in text and "BİLEZİK" in text: prices["bilezik22"] = price
                    except: continue
            if prices["ceyrek"] > 0:
                prices["status"] = True
                prices["source"] = "Kayseri Sarraf (Oto)"
    except: pass
    return prices

kayseri_data = get_kayseri_ziynet()

# --- 3. GLOBAL HİSSE VERİLERİ ---
@st.cache_data(ttl=60)
def get_stock_prices():
    try:
        tickers = ["FROTO.IS", "THYAO.IS", "TUPRS.IS"]
        data = yf.download(tickers, period="1d", group_by='ticker', progress=False)
        vals = {}
        for t in tickers:
            try: vals[t] = float(data[t]['Close'].iloc[-1])
            except: vals[t] = 0.0
        return vals
    except: return {}

stock_vals = get_stock_prices()

# --- YAN MENÜ ---
st.sidebar.header("💰 Varlık Girişleri")

# ALTIN
st.sidebar.subheader("🥇 Altın Varlıkları")
banka_gram = st.sidebar.number_input("Banka Altın (24 Ayar Gram)", value=130, step=5)
st.sidebar.caption(f"Veri Kaynağı: {kayseri_data['source']}")

def_ceyrek = kayseri_data["ceyrek"] if kayseri_data["ceyrek"] > 0 else 5100.0
def_tam = kayseri_data["tam"] if kayseri_data["tam"] > 0 else 20400.0
def_bilezik = kayseri_data["bilezik22"] if kayseri_data["bilezik22"] > 0 else 2900.0

col_z1, col_z2 = st.sidebar.columns(2)
ceyrek_adet = col_z1.number_input("Çeyrek Adet", value=0)
tam_adet = col_z2.number_input("Tam Adet", value=0)

with st.sidebar.expander("Fiyatları Düzenle (Manuel)"):
    guncel_ceyrek_fiyat = st.number_input("Çeyrek Fiyat", value=def_ceyrek)
    guncel_tam_fiyat = st.number_input("Tam Fiyat", value=def_tam)
    guncel_22ayar_gram = st.number_input("22 Ayar Bilezik Fiyat", value=def_bilezik)

bilezik_gram = st.sidebar.number_input("Bilezik (22 Ayar Gram)", value=0, step=5)

# DÖVİZ
st.sidebar.subheader("💶 Döviz & Fon")
euro_amount = st.sidebar.number_input("Euro Varlığı (€)", value=10000, step=100)
total_funds = st.sidebar.number_input("Toplam Fon Değeri", value=75000, step=1000)
ylb_cash = st.sidebar.number_input("Sadece YLB (Nakit)", value=55000, step=1000)
cc_debt = st.sidebar.number_input("Kredi Kartı Borcu", value=34321, step=500)

# --- HESAPLAMALAR ---
# Gram altın (Global ONS üzerinden)
if market_data is not None:
    ons = market_data['GC=F']['Close'].iloc[-1]
    usd = market_data['TRY=X']['Close'].iloc[-1]
    gram_tl = (ons * usd) / 31.10
    euro_tl = market_data['TRY=X']['Close'].iloc[-1] * 1.05 # Yaklaşık parite
else:
    gram_tl = 3000
    euro_tl = 37

val_banka = banka_gram * gram_tl
val_ziynet = (ceyrek_adet * guncel_ceyrek_fiyat) + (tam_adet * guncel_tam_fiyat)
val_bilezik = bilezik_gram * guncel_22ayar_gram
total_gold = val_banka + val_ziynet + val_bilezik
total_euro = euro_amount * euro_tl
net_worth = total_gold + total_euro + total_funds

# --- GÖSTERGE PANELİ ---
c1, c2, c3 = st.columns(3)
c1.metric("Toplam Servet", f"{net_worth:,.0f} TL")
c2.metric("Toplam Altın", f"{total_gold:,.0f} TL")
c3.metric("Euro Varlığı", f"{total_euro:,.0f} TL")

st.markdown("---")

col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("💳 Arbitraj Durumu")
    margin = ylb_cash - cc_debt
    per = (ylb_cash / cc_debt) * 100 if cc_debt > 0 else 100
    prog = int(per) if int(per) < 100 else 100
    st.progress(prog)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Borç", f"{cc_debt:,.0f} TL")
    k2.metric("Nakit", f"{ylb_cash:,.0f} TL")
    if margin < 0:
        k3.metric("Durum", "RİSKLİ", f"{margin:,.0f} TL", delta_color="inverse")
    else:
        k3.metric("Durum", "GÜVENLİ", f"{margin:,.0f} TL")

with col_right:
    st.subheader("👶 Junior Hisse")
    f_lot = st.number_input("FROTO", value=2)
    t_lot = st.number_input("THYAO", value=5)
    p_lot = st.number_input("TUPRS", value=30)
    
    jr_val = (f_lot * stock_vals.get("FROTO.IS", 0)) + \
             (t_lot * stock_vals.get("THYAO.IS", 0)) + \
             (p_lot * stock_vals.get("TUPRS.IS", 0))
    st.metric("Çocuk Portföyü", f"{jr_val:,.0f} TL")

st.markdown("---")
st.caption("Veriler Yahoo Finance ve Kayseri Sarraf Derneği üzerinden canlı alınmaktadır.")

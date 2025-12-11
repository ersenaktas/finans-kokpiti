import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import math

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföyü", layout="wide", page_icon="🚀")
st.title("🚀 Finansal Özgürlük Kokpiti")

# --- 1. VERİ AVCI ROBOTU (KAYSERİ) ---
@st.cache_data(ttl=900)
def get_kayseri_smart():
    url = "https://www.kaysarder.org.tr/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    prices = {"ceyrek": 0.0, "tam": 0.0, "bilezik22": 0.0, "status": False}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            clean_text = soup.get_text(" ", strip=True) 
            
            match_ceyrek = re.search(r'25\s*ZİYNET.*?(\d+[\.,]\d+)', clean_text, re.IGNORECASE)
            if match_ceyrek: prices["ceyrek"] = float(match_ceyrek.group(1).replace('.', '').replace(',', '.'))

            match_tam = re.search(r'100\s*ZİYNET.*?(\d+[\.,]\d+)', clean_text, re.IGNORECASE)
            if match_tam: prices["tam"] = float(match_tam.group(1).replace('.', '').replace(',', '.'))
            
            match_bilezik = re.search(r'22\s*AYAR.*?(\d+[\.,]\d+)', clean_text, re.IGNORECASE)
            if match_bilezik: prices["bilezik22"] = float(match_bilezik.group(1).replace('.', '').replace(',', '.'))

            if prices["ceyrek"] > 0: prices["status"] = True
    except: pass
    return prices

kayseri_data = get_kayseri_smart()

# --- 2. GLOBAL VERİLER (HATA KORUMALI) ---
try:
    tickers = ["XU100.IS", "NQ=F", "GC=F", "TRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS", 
               "YAS.IS", "YAY.IS", "YLB.IS"]
    market_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
except: market_data = None

# Yardımcı Fonksiyon: Veri yoksa 0 döndür
def safe_get_price(ticker):
    try:
        if market_data is not None and ticker in market_data:
            val = market_data[ticker]['Close'].iloc[-1]
            if pd.isna(val): return 0.0
            return float(val)
        return 0.0
    except: return 0.0

# --- 3. REFERANS FİYATLAR (İSTEDİĞİNİZ YENİ BÖLÜM) ---
st.subheader("🏷️ Güncel Piyasa Fiyatları")

# Verileri hazırla
dolar_tl = safe_get_price('TRY=X')
ons_dolar = safe_get_price('GC=F')
# Has Altın (Gram 24k) Hesabı
if dolar_tl > 0 and ons_dolar > 0:
    has_altin_tl = (ons_dolar * dolar_tl) / 31.10
else:
    has_altin_tl = 0

euro_tl = dolar_tl * 1.05 # Parite yaklaşık

# Kayseri Verileri (Varsayılanlar)
p_ceyrek = kayseri_data["ceyrek"] if kayseri_data["ceyrek"] > 0 else 0
p_bilezik = kayseri_data["bilezik22"] if kayseri_data["bilezik22"] > 0 else 0

# Fiyatları Göster (5 Kolon)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Gram Altın (Has)", f"{has_altin_tl:,.2f} TL")
k2.metric("Çeyrek Altın", f"{p_ceyrek:,.2f} TL", "Kayseri")
k3.metric("22 Ayar Bilezik", f"{p_bilezik:,.2f} TL", "Gram Fiyatı")
k4.metric("Euro/TL", f"{euro_tl:.2f} TL")
k5.metric("Dolar/TL", f"{dolar_tl:.2f} TL")

st.markdown("---")

# --- 4. GİRİŞLER (SOL MENÜ) ---
st.sidebar.header("💰 Varlık Girişleri")

# --- FONLAR ---
st.sidebar.subheader("📈 Fon Portföyü")

# Fiyatları al (Hata varsa 0 gelir)
price_yas = safe_get_price('YAS.IS')
price_yay = safe_get_price('YAY.IS')
price_ylb = safe_get_price('YLB.IS')

# Eğer Yahoo fiyat veremezse MANUEL GİRİŞ aç (Güvenlik Önlemi)
if price_yas == 0: price_yas = st.sidebar.number_input("YAS Fiyatı (Manuel)", value=5.0)
if price_yay == 0: price_yay = st.sidebar.number_input("YAY Fiyatı (Manuel)", value=4.0)
if price_ylb == 0: price_ylb = st.sidebar.number_input("YLB Fiyatı (Manuel)", value=55.0) # YLB genelde yüksektir

yas_adet = st.sidebar.number_input("YAS Adedi", value=10000, step=100)
yay_adet = st.sidebar.number_input("YAY Adedi", value=5000, step=100)
ylb_adet = st.sidebar.number_input("YLB Adedi", value=1000, step=100)

val_yas = yas_adet * price_yas
val_yay = yay_adet * price_yay
val_ylb = ylb_adet * price_ylb 

# ALTIN BÖLÜMÜ
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altın Varlıkları")
banka_gram = st.sidebar.number_input("Banka Altın (24 Ayar Gram)", value=130, step=5)

v_ceyrek = p_ceyrek if p_ceyrek > 0 else 9600.0
v_tam = kayseri_data["tam"] if kayseri_data["tam"] > 0 else 38400.0
v_bilezik = p_bilezik if p_bilezik > 0 else 5600.0

ceyrek_adet = st.sidebar.number_input("Çeyrek Adet", value=53)
guncel_ceyrek_fiyat = st.sidebar.number_input("Çeyrek Fiyatı", value=v_ceyrek)

tam_adet = st.sidebar.number_input("Tam Adet", value=0)
guncel_tam_fiyat = st.sidebar.number_input("Tam Fiyatı", value=v_tam)

bilezik_gram = st.sidebar.number_input("Bilezik Gram", value=0)
guncel_22ayar_gram = st.sidebar.number_input("22 Ayar Fiyatı", value=v_bilezik)

# DÖVİZ & BORÇ
st.sidebar.markdown("---")
st.sidebar.subheader("💶 Döviz & Borç")
euro_amount = st.sidebar.number_input("Euro Miktarı (€)", value=10410, step=100)
cc_debt = st.sidebar.number_input("Kredi Kartı Borcu", value=34321, step=500)

# --- SONUÇ HESAPLAMA ---
val_banka = banka_gram * has_altin_tl
val_ziynet = (ceyrek_adet * guncel_ceyrek_fiyat) + (tam_adet * guncel_tam_fiyat)
val_bilezik = bilezik_gram * guncel_22ayar_gram
total_gold = val_banka + val_ziynet + val_bilezik

total_euro = euro_amount * euro_tl
total_funds = val_yas + val_yay + val_ylb
net_worth = total_gold + total_euro + total_funds

# --- ANA EKRAN ---
# 1. BÜYÜK RAKAMLAR
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net_worth:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{total_gold:,.0f} TL")
c3.metric("TOPLAM FON", f"{total_funds:,.0f} TL")

st.markdown("---")

# 2. FON DETAYLARI
st.subheader("📈 Fon Portföy Detayı")
f1, f2, f3 = st.columns(3)
f1.metric("YAS (Koç)", f"{val_yas:,.0f} TL", f"{price_yas:.2f} TL x {yas_adet}")
f2.metric("YAY (Teknoloji)", f"{val_yay:,.0f} TL", f"{price_yay:.2f} TL x {yay_adet}")
f3.metric("YLB (Nakit)", f"{val_ylb:,.0f} TL", f"{price_ylb:.2f} TL x {ylb_adet}")

st.markdown("---")

# 3. ARBİTRAJ (HATA DÜZELTİLMİŞ KISIM)
col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("💳 Arbitraj Durumu")
    
    # Hata korumalı hesaplama
    if cc_debt > 0 and val_ylb > 0:
        per = (val_ylb / cc_debt) * 100
    elif cc_debt == 0:
        per = 100
    else:
        per = 0
        
    # Sonsuz veya NaN kontrolü
    if math.isnan(per) or math.isinf(per):
        per = 0
        
    prog = int(per) if int(per) < 100 else 100
    margin = val_ylb - cc_debt
    
    st.progress(prog)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Borç", f"{cc_debt:,.0f} TL")
    k2.metric("Nakit Gücü (YLB)", f"{val_ylb:,.0f} TL")
    
    status_color = "inverse" if margin < 0 else "normal"
    status_text = "RİSKLİ" if margin < 0 else "GÜVENLİ"
    k3.metric("Durum", status_text, f"{margin:,.0f} TL", delta_color=status_color)

with col_right:
    st.subheader("👶 Junior Hisse")
    f_lot = st.number_input("FROTO Lot", value=2)
    t_lot = st.number_input("THYAO Lot", value=5)
    p_lot = st.number_input("TUPRS Lot", value=30)
    
    # Güvenli fiyat çekme
    vf = safe_get_price('FROTO.IS')
    vt = safe_get_price('THYAO.IS')
    vp = safe_get_price('TUPRS.IS')
    
    jr_val = (f_lot * vf) + (t_lot * vt) + (p_lot * vp)
    st.metric("Çocuk Portföyü", f"{jr_val:,.0f} TL")

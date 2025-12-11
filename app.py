import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföyü", layout="wide", page_icon="🚀")
st.title("🚀 Finansal Özgürlük Kokpiti")

# --- 1. VERİ AVCI ROBOTU (KAYSERİ ALTIN) ---
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
            
            # Regex ile verileri avla
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

# --- 2. GLOBAL VERİLER (FONLAR DAHİL) ---
# YAS.IS, YAY.IS, YLB.IS -> Yahoo Finance üzerinden çekiyoruz
try:
    tickers = ["XU100.IS", "NQ=F", "GC=F", "TRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS", 
               "YAS.IS", "YAY.IS", "YLB.IS"]
    market_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
except: market_data = None

# --- 3. PİYASA PANOSU (EN ÜST) ---
st.subheader("📊 Piyasa ve Fon Fiyatları (Canlı)")
m1, m2, m3, m4 = st.columns(4)

if market_data is not None:
    try:
        # BIST 100
        b_now = market_data['XU100.IS']['Close'].iloc[-1]
        b_delta = ((b_now - market_data['XU100.IS']['Close'].iloc[-2])/market_data['XU100.IS']['Close'].iloc[-2])*100
        m1.metric("BIST 100 (YAS)", f"{b_now:,.0f}", f"%{b_delta:.2f}")
        
        # NASDAQ
        n_now = market_data['NQ=F']['Close'].iloc[-1]
        n_delta = ((n_now - market_data['NQ=F']['Close'].iloc[-2])/market_data['NQ=F']['Close'].iloc[-2])*100
        m2.metric("NASDAQ (YAY)", f"{n_now:,.0f}", f"%{n_delta:.2f}")
        
        # DOLAR
        d_now = market_data['TRY=X']['Close'].iloc[-1]
        m3.metric("Dolar/TL", f"{d_now:.2f} TL")
        
        # ONS ALTIN
        o_now = market_data['GC=F']['Close'].iloc[-1]
        m4.metric("Ons Altın", f"${o_now:,.0f}")

        # Fon Fiyatlarını Hazırla
        price_yas = market_data['YAS.IS']['Close'].iloc[-1]
        price_yay = market_data['YAY.IS']['Close'].iloc[-1]
        price_ylb = market_data['YLB.IS']['Close'].iloc[-1]
        
        # Has Altın ve Euro Kuru
        has_altin_tl = (o_now * d_now) / 31.10
        euro_tl = market_data['TRY=X']['Close'].iloc[-1] * 1.05
    except:
        price_yas=1.0; price_yay=1.0; price_ylb=1.0; has_altin_tl=3000; euro_tl=37
else:
    price_yas=1.0; price_yay=1.0; price_ylb=1.0; has_altin_tl=3000; euro_tl=37

st.markdown("---")

# --- 4. GİRİŞLER (SOL MENÜ) ---
st.sidebar.header("💰 Varlık Girişleri")

# --- FONLAR (ADET GİRİŞLİ YENİ SİSTEM) ---
st.sidebar.subheader("📈 Fon Portföyü (Adet Girin)")
st.sidebar.caption("Pazartesi alım yaptıkça buradaki adetleri artırın.")

# YAS GİRİŞİ
yas_adet = st.sidebar.number_input("YAS Adedi (Lot)", value=10000, step=100)
st.sidebar.info(f"YAS Fiyat: {price_yas:.4f} TL")

# YAY GİRİŞİ
yay_adet = st.sidebar.number_input("YAY Adedi (Lot)", value=5000, step=100)
st.sidebar.info(f"YAY Fiyat: {price_yay:.4f} TL")

# YLB GİRİŞİ
ylb_adet = st.sidebar.number_input("YLB Adedi (Lot)", value=1000, step=100)
st.sidebar.info(f"YLB Fiyat: {price_ylb:.4f} TL")

# Toplam Fon Değerini Hesapla
val_yas = yas_adet * price_yas
val_yay = yay_adet * price_yay
val_ylb = ylb_adet * price_ylb # Bu aynı zamanda nakit gücümüz

# ALTIN BÖLÜMÜ
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altın Varlıkları")
banka_gram = st.sidebar.number_input("Banka Altın (24 Ayar Gram)", value=130, step=5)

source_msg = "Kayseri (OTO)" if kayseri_data["status"] else "Manuel"
st.sidebar.caption(f"👇 Ziynet Fiyatları ({source_msg})")

v_ceyrek = kayseri_data["ceyrek"] if kayseri_data["ceyrek"] > 0 else 9600.0
v_tam = kayseri_data["tam"] if kayseri_data["tam"] > 0 else 38400.0
v_bilezik = kayseri_data["bilezik22"] if kayseri_data["bilezik22"] > 0 else 5600.0

ceyrek_adet = st.sidebar.number_input("Çeyrek Altın (Adet)", value=53)
guncel_ceyrek_fiyat = st.sidebar.number_input("Çeyrek Fiyatı (TL)", value=v_ceyrek, step=50.0)

tam_adet = st.sidebar.number_input("Tam Altın (Adet)", value=0)
guncel_tam_fiyat = st.sidebar.number_input("Tam Fiyatı (TL)", value=v_tam, step=100.0)

bilezik_gram = st.sidebar.number_input("Bilezik (22 Ayar Gram)", value=0)
guncel_22ayar_gram = st.sidebar.number_input("22 Ayar Gram Fiyatı (TL)", value=v_bilezik, step=10.0)

# DÖVİZ & BORÇ
st.sidebar.markdown("---")
st.sidebar.subheader("💶 Döviz & Borç")
euro_amount = st.sidebar.number_input("Euro Varlığı (€)", value=10410, step=100)
cc_debt = st.sidebar.number_input("Kredi Kartı Borcu", value=34321, step=500)

# --- SONUÇ HESAPLAMA ---
val_banka = banka_gram * has_altin_tl
val_ziynet = (ceyrek_adet * guncel_ceyrek_fiyat) + (tam_adet * guncel_tam_fiyat)
val_bilezik = bilezik_gram * guncel_22ayar_gram
total_gold = val_banka + val_ziynet + val_bilezik

total_euro = euro_amount * euro_tl
total_funds = val_yas + val_yay + val_ylb
net_worth = total_gold + total_euro + total_funds

# --- EKRAN GÖSTERİMİ ---

# 1. SATIR: ANA VARLIKLAR
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net_worth:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{total_gold:,.0f} TL")
c3.metric("TOPLAM FON", f"{total_funds:,.0f} TL")

st.markdown("---")

# 2. SATIR: FON DETAYLARI (YENİ)
st.subheader("📈 Fon Portföy Detayı")
f1, f2, f3 = st.columns(3)
f1.metric("YAS (Koç)", f"{val_yas:,.0f} TL", f"{yas_adet} Adet")
f2.metric("YAY (Teknoloji)", f"{val_yay:,.0f} TL", f"{yay_adet} Adet")
f3.metric("YLB (Nakit)", f"{val_ylb:,.0f} TL", f"{ylb_adet} Adet")

st.markdown("---")

# 3. SATIR: ARBİTRAJ VE ÇOCUK
col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("💳 Arbitraj Durumu")
    margin = val_ylb - cc_debt
    per = (val_ylb / cc_debt) * 100 if cc_debt > 0 else 100
    prog = int(per) if int(per) < 100 else 100
    st.progress(prog)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Borç", f"{cc_debt:,.0f} TL")
    k2.metric("Nakit Gücü (YLB)", f"{val_ylb:,.0f} TL")
    if margin < 0:
        k3.metric("Durum", "RİSKLİ", f"{margin:,.0f} TL", delta_color="inverse")
    else:
        k3.metric("Durum", "GÜVENLİ", f"{margin:,.0f} TL")

with col_right:
    st.subheader("👶 Junior Hisse")
    f_lot = st.number_input("FROTO Lot", value=2)
    t_lot = st.number_input("THYAO Lot", value=5)
    p_lot = st.number_input("TUPRS Lot", value=30)
    
    if market_data is not None:
        try:
            val_f = market_data['FROTO.IS']['Close'].iloc[-1]
            val_t = market_data['THYAO.IS']['Close'].iloc[-1]
            val_p = market_data['TUPRS.IS']['Close'].iloc[-1]
            jr_val = (f_lot * val_f) + (t_lot * val_t) + (p_lot * val_p)
        except: jr_val = 0
    else: jr_val = 0
    
    st.metric("Çocuk Portföyü", f"{jr_val:,.0f} TL")

import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import pytz

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföyü", layout="wide", page_icon="🚀")

# ---------------------------------------------------------
# 1. HAFIZA BAŞLATMA
# ---------------------------------------------------------
if 'init' not in st.session_state:
    # YAS
    st.session_state['yas_val'] = 13.43
    st.session_state['yas_cost'] = 13.43
    st.session_state['yas_src'] = "Başlangıç"
    
    # YAY
    st.session_state['yay_val'] = 1283.30
    st.session_state['yay_cost'] = 1283.30
    st.session_state['yay_src'] = "Başlangıç"
    
    # YLB
    st.session_state['ylb_val'] = 1.40
    st.session_state['ylb_cost'] = 1.40
    st.session_state['ylb_src'] = "Başlangıç"
    
    st.session_state['last_update'] = "Henüz Yapılmadı"
    st.session_state['init'] = True

# ---------------------------------------------------------
# 2. VERİ ÇEKME MOTORU
# ---------------------------------------------------------
def fetch_fund_data(fund_code):
    # 1. TEFAS
    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://www.google.com/'
        }
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.content, "html.parser")
        val = soup.select_one(".top-list > li:nth-child(1) > span").text
        return float(val.replace(",", ".")), "TEFAS"
    except: pass
    
    # 2. FINTABLES
    try:
        url = f"https://fintables.com/fonlar/{fund_code}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
        match = re.search(r'Son Fiyat\s*[:\s]*([\d\.]+,\d+)', text)
        if match:
             return float(match.group(1).replace('.', '').replace(',', '.')), "Fintables"
    except: pass
    
    return None, None

@st.cache_data(ttl=900)
def get_kayseri_gold():
    prices = {"ceyrek": 0, "bilezik": 0, "tam":0, "src": "Manuel"}
    try:
        url = "https://www.kaysarder.org.tr/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=8)
        text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
        
        mc = re.search(r'25\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
        mt = re.search(r'100\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
        mb = re.search(r'22\s*AYAR.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
        
        if mc: prices["ceyrek"] = float(mc.group(1).replace('.', '').replace(',', '.'))
        if mt: prices["tam"] = float(mt.group(1).replace('.', '').replace(',', '.'))
        if mb: prices["bilezik"] = float(mb.group(1).replace('.', '').replace(',', '.'))
        if prices["ceyrek"] > 0: prices["src"] = "Kayseri"
    except: pass
    return prices

# ---------------------------------------------------------
# 3. GÜNCELLEME BUTONU
# ---------------------------------------------------------
st.sidebar.header("🕹️ Komuta Merkezi")
if st.sidebar.button("🔄 Piyasayı GÜNCELLE"):
    with st.spinner('Veri kaynaklarına bağlanılıyor...'):
        # Fonlar
        for code in ["YAS", "YAY", "YLB"]:
            p, s = fetch_fund_data(code)
            if p:
                st.session_state[f'{code.lower()}_val'] = p
                st.session_state[f'{code.lower()}_src'] = s
        
        # Zaman
        tz = pytz.timezone("Turkey")
        st.session_state['last_update'] = datetime.now(tz).strftime("%H:%M:%S")
        st.cache_data.clear()

st.sidebar.caption(f"Son Güncelleme: {st.session_state['last_update']}")

# ---------------------------------------------------------
# 4. VERİ GİRİŞLERİ
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🎛️ Portföy Girişi")

# --- FONLAR ---
st.sidebar.subheader("📈 Fonlar (Adet & Maliyet)")

with st.sidebar.expander("YAS (Koç)", expanded=True):
    in_yas_fiyat = st.number_input("YAS Fiyat", value=st.session_state['yas_val'], format="%.4f")
    in_yas_adet = st.number_input("YAS Adet", value=734)
    in_yas_maliyet = st.number_input("YAS Maliyet", value=st.session_state['yas_cost'], format="%.4f")

with st.sidebar.expander("YAY (Teknoloji)", expanded=True):
    in_yay_fiyat = st.number_input("YAY Fiyat", value=st.session_state['yay_val'], format="%.4f")
    in_yay_adet = st.number_input("YAY Adet", value=7)
    in_yay_maliyet = st.number_input("YAY Maliyet", value=st.session_state['yay_cost'], format="%.4f")

with st.sidebar.expander("YLB (Nakit)", expanded=False):
    in_ylb_fiyat = st.number_input("YLB Fiyat", value=st.session_state['ylb_val'], format="%.4f")
    in_ylb_adet = st.number_input("YLB Adet", value=39400)
    in_ylb_maliyet = st.number_input("YLB Maliyet", value=st.session_state['ylb_cost'], format="%.4f")

# --- ALTINLAR ---
kayseri = get_kayseri_gold()
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altınlar")

banka_gr = st.sidebar.number_input("Banka Altın (Gr)", value=130)

def_c = kayseri["ceyrek"] if kayseri["ceyrek"] > 0 else 9600.0
in_c_fiyat = st.sidebar.number_input("Çeyrek Fiyat", value=def_c)
in_c_adet = st.sidebar.number_input("Çeyrek Adet", value=53)

def_b = kayseri["bilezik"] if kayseri["bilezik"] > 0 else 5600.0
in_b_fiyat = st.sidebar.number_input("Bilezik Gr Fiyatı", value=def_b)
in_b_gr = st.sidebar.number_input("Bilezik Gram", value=10)

def_t = kayseri["tam"] if kayseri["tam"] > 0 else 38400.0
in_t_fiyat = st.sidebar.number_input("Tam Fiyat", value=def_t)
in_t_adet = st.sidebar.number_input("Tam Adet", value=0)

# --- DÖVİZ ---
try:
    tickers = ["TRY=X", "GC=F", "EURTRY=X"]
    m_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    def get_yf(t):
        v = m_data[t]['Close'].iloc[-1]
        return float(v) if not pd.isna(v) else 0.0
    usd_tl = get_yf("TRY=X")
    eur_tl = get_yf("EURTRY=X")
    ons = get_yf("GC=F")
except:
    usd_tl, eur_tl, ons = 0, 0, 0

# Euro maliyet varsayılan
def_eur_cost = eur_tl if eur_tl > 0 else 49.97

st.sidebar.markdown("---")
st.sidebar.subheader("💶 Döviz & Borç")
in_eur_kur = st.sidebar.number_input("Euro Kuru (Canlı)", value=def_eur_cost)
in_eur_adet = st.sidebar.number_input("Euro Miktarı", value=10410)
in_eur_maliyet = st.sidebar.number_input("Euro Ort. Maliyet", value=in_eur_kur)

in_borc = st.sidebar.number_input("Kredi Kartı Borcu", value=34321)

# ---------------------------------------------------------
# 5. HESAPLAMALAR
# ---------------------------------------------------------
def calc_profit(adet, guncel, maliyet):
    toplam_deger = adet * guncel
    toplam_maliyet = adet * maliyet
    kar_tl = toplam_deger - toplam_maliyet
    kar_yuzde = (kar_tl / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
    return toplam_deger, kar_tl, kar_yuzde

# Fon Hesapları
val_yas, kar_yas_tl, kar_yas_pct = calc_profit(in_yas_adet, in_yas_fiyat, in_yas_maliyet)
val_yay, kar_yay_tl, kar_yay_pct = calc_profit(in_yay_adet, in_yay_fiyat, in_yay_maliyet)
val_ylb, kar_ylb_tl, kar_ylb_pct = calc_profit(in_ylb_adet, in_ylb_fiyat, in_ylb_maliyet)
t_fon = val_yas + val_yay + val_ylb

# Euro
val_eur, kar_eur_tl, kar_eur_pct = calc_profit(in_eur_adet, in_eur_kur, in_eur_maliyet)

# Altın Hesabı
safe_has = (ons * usd_tl) / 31.10 if (ons>0 and usd_tl>0) else 3100.0
v_banka = banka_gr * safe_has
v_ziynet = (in_c_adet * in_c_fiyat) + (in_t_adet * in_t_fiyat)
v_bilezik = in_b_gr * in_b_fiyat
t_gold = v_banka + v_ziynet + v_bilezik

net = t_fon + t_gold + val_eur

# ---------------------------------------------------------
# 6. EKRAN GÖSTERİMİ
# ---------------------------------------------------------
st.title("🚀 Finansal Özgürlük Kokpiti")

# --- BÖLÜM 1: DÖVİZ VE ALTIN PİYASASI ---
st.subheader("🌍 Döviz ve Altın Piyasası")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Euro/TL", f"{in_eur_kur:.2f}", "Canlı")
k2.metric("Dolar/TL", f"{usd_tl:.2f}", "Canlı")
k3.metric("Has Altın (Gr)", f"{safe_has:,.0f} TL", "Global")
k4.metric("Çeyrek Altın", f"{in_c_fiyat:,.0f} TL", f"Kaynak: {kayseri['src']}")
k5.metric("Bilezik (22 Ayar)", f"{in_b_fiyat:,.0f} TL", f"Kaynak: {kayseri['src']}")

# --- BÖLÜM 2: FON PİYASASI ---
st.subheader("📈 Fon Fiyatları")
f1, f2, f3 = st.columns(3)
f1.metric("YAS Fiyat", f"{in_yas_fiyat:.4f}", f"Kaynak: {st.session_state['yas_src']}")
f2.metric("YAY Fiyat", f"{in_yay_fiyat:.4f}", f"Kaynak: {st.session_state['yay_src']}")
f3.metric("YLB Fiyat", f"{in_ylb_fiyat:.4f}", f"Kaynak: {st.session_state['ylb_src']}")

st.markdown("---")

# ANA VARLIKLAR
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{t_gold:,.0f} TL")
c3.metric("TOPLAM FON", f"{t_fon:,.0f} TL")

st.markdown("---")

# KÂR/ZARAR ANALİZİ
st.subheader("📊 Kâr / Zarar Analizi")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info(f"**YAS (Koç)**\n\nDeğer: {val_yas:,.0f} TL")
    st.metric("Net Kâr", f"{kar_yas_tl:,.0f} TL", f"%{kar_yas_pct:.1f}")

with col2:
    st.info(f"**YAY (Tekn)**\n\nDeğer: {val_yay:,.0f} TL")
    st.metric("Net Kâr", f"{kar_yay_tl:,.0f} TL", f"%{kar_yay_pct:.1f}")

with col3:
    st.info(f"**YLB (Nakit)**\n\nDeğer: {val_ylb:,.0f} TL")
    st.metric("Net Kâr", f"{kar_ylb_tl:,.0f} TL", f"%{kar_ylb_pct:.1f}")
    
with col4:
    st.warning(f"**EURO (€)**\n\nDeğer: {val_eur:,.0f} TL")
    st.metric("Kur Farkı", f"{kar_eur_tl:,.0f} TL", f"%{kar_eur_pct:.1f}")

st.markdown("---")

# GÜVENLİK BARI
st.subheader("💳 Güvenlik ve Arbitraj Durumu")
if in_borc > 0: oran = (val_ylb / in_borc) * 100
elif val_ylb > 0: oran = 100
else: oran = 0

st.progress(min(int(oran), 100))

b1, b2, b3 = st.columns(3)
b1.metric("Kredi Kartı Borcu", f"{in_borc:,.0f} TL")
b2.metric("Nakit Gücü (YLB)", f"{val_ylb:,.0f} TL")

fark = val_ylb - in_borc
durum = "GÜVENLİ ✅" if fark >= 0 else "RİSKLİ ⚠️"
renk = "normal" if fark >= 0 else "inverse"
b3.metric("Durum", durum, f"{fark:,.0f} TL", delta_color=renk)

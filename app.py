import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import math
from datetime import datetime
import pytz

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföyü", layout="wide", page_icon="🚀")

# --- HAFIZA (SESSION STATE) ---
if 'yas_fiyat' not in st.session_state: st.session_state['yas_fiyat'] = 13.43
if 'yay_fiyat' not in st.session_state: st.session_state['yay_fiyat'] = 1283.30
if 'ylb_fiyat' not in st.session_state: st.session_state['ylb_fiyat'] = 1.40
if 'last_update' not in st.session_state: st.session_state['last_update'] = "Henüz Yapılmadı"

# ---------------------------------------------------------
# 1. ÖZEL FONKSİYON: TEFAS CIMBIZLAYICI 🔍
# ---------------------------------------------------------
def fetch_fund_price(fund_code):
    """
    TEFAS sitesindeki 'Son Fiyat' kutusunu hedefler.
    Resimdeki en soldaki kutuyu okur.
    """
    # 1. TEFAS (Devlet Sitesi)
    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        # Tarayıcı gibi davran (Chrome/Windows)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            
            # TEFAS'taki o "Son Fiyat" kutusu HTML'de ".top-list" içindeki İLK elemandır.
            # Resimdeki: 13,436836 yazan yer.
            price_text = soup.select_one(".top-list > li:nth-child(1) > span").text
            
            # Virgülü noktaya çevirip sayı yap
            return float(price_text.replace(",", "."))
    except Exception as e:
        print(f"TEFAS Hatası ({fund_code}): {e}")

    # 2. YEDEK: FINTABLES
    try:
        url = f"https://fintables.com/fonlar/{fund_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
        # "Son Fiyat 1.283,29" yapısını ara
        match = re.search(r'Son Fiyat\s*[:\s]*([\d\.]+,\d+)', text)
        if match:
             return float(match.group(1).replace('.', '').replace(',', '.'))
    except:
        pass

    return None # Hiçbiri çalışmazsa None dön (Sıfırlama!)

@st.cache_data(ttl=900)
def get_kayseri_gold():
    prices = {"ceyrek": 0, "tam": 0, "bilezik": 0, "src": "Manuel"}
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
# 2. GÜNCELLEME BUTONU
# ---------------------------------------------------------
st.sidebar.header("🕹️ Komuta Merkezi")

if st.sidebar.button("🔄 Fiyatları GÜNCELLE"):
    with st.spinner('TEFAS ve Kayseri taranıyor...'):
        # YAS
        new_yas = fetch_fund_price("YAS")
        if new_yas: st.session_state['yas_fiyat'] = new_yas
        
        # YAY
        new_yay = fetch_fund_price("YAY")
        if new_yay: st.session_state['yay_fiyat'] = new_yay
        
        # YLB
        new_ylb = fetch_fund_price("YLB")
        if new_ylb: st.session_state['ylb_fiyat'] = new_ylb
        
        # Zaman
        tz = pytz.timezone("Turkey")
        st.session_state['last_update'] = datetime.now(tz).strftime("%H:%M:%S")
        st.cache_data.clear()

st.sidebar.caption(f"Son İşlem: {st.session_state['last_update']}")

# ---------------------------------------------------------
# 3. VERİ GİRİŞLERİ
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🎛️ Veri Girişi")

# FONLAR
st.sidebar.subheader("📈 Fonlar")
in_yas_fiyat = st.sidebar.number_input("YAS Fiyatı", value=st.session_state['yas_fiyat'], format="%.4f")
in_yas_adet = st.sidebar.number_input("YAS Adet", value=734)

in_yay_fiyat = st.sidebar.number_input("YAY Fiyatı", value=st.session_state['yay_fiyat'], format="%.4f")
in_yay_adet = st.sidebar.number_input("YAY Adet", value=7)

in_ylb_fiyat = st.sidebar.number_input("YLB Fiyatı", value=st.session_state['ylb_fiyat'], format="%.4f")
in_ylb_adet = st.sidebar.number_input("YLB Adet", value=39400)

# ALTINLAR
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

# DİĞER
try:
    tickers = ["TRY=X", "GC=F", "EURTRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
    m_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    def get_yf(t):
        v = m_data[t]['Close'].iloc[-1]
        return float(v) if not pd.isna(v) else 0.0
    usd_tl = get_yf("TRY=X")
    eur_tl = get_yf("EURTRY=X")
    ons = get_yf("GC=F")
except:
    usd_tl, eur_tl, ons = 0, 0, 0

st.sidebar.markdown("---")
st.sidebar.subheader("💶 Diğer")
def_eur = eur_tl if eur_tl > 0 else 49.97
in_eur_kur = st.sidebar.number_input("Euro Kuru", value=def_eur)
in_eur_miktar = st.sidebar.number_input("Euro Miktarı", value=10410)
in_borc = st.sidebar.number_input("Kredi Kartı Borcu", value=34321)

# ---------------------------------------------------------
# 4. HESAPLAMALAR
# ---------------------------------------------------------
v_yas = in_yas_fiyat * in_yas_adet
v_yay = in_yay_fiyat * in_yay_adet
v_ylb = in_ylb_fiyat * in_ylb_adet
t_fon = v_yas + v_yay + v_ylb

safe_has = (ons * usd_tl) / 31.10 if (ons>0 and usd_tl>0) else 3100.0
v_banka = banka_gr * safe_has
v_ziynet = (in_c_adet * in_c_fiyat) + (in_t_adet * in_t_fiyat)
v_bilezik = in_b_gr * in_b_fiyat
t_gold = v_banka + v_ziynet + v_bilezik

t_euro = in_eur_miktar * in_eur_kur
net = t_fon + t_gold + t_euro

# ---------------------------------------------------------
# 5. EKRAN GÖSTERİMİ
# ---------------------------------------------------------
st.title("🚀 Finansal Özgürlük Kokpiti")

st.markdown(f"""
<small>Son Güncelleme: {st.session_state['last_update']}</small>
""", unsafe_allow_html=True)

st.subheader("🏷️ Canlı Piyasa")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Gram Has", f"{safe_has:,.0f} TL")
k2.metric("Dolar/TL", f"{usd_tl:.2f}")
k3.metric("Euro/TL", f"{in_eur_kur:.2f}")
k4.metric("YAS Fiyat", f"{in_yas_fiyat:.4f}")
k5.metric("YAY Fiyat", f"{in_yay_fiyat:.4f}")

st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{t_gold:,.0f} TL")
c3.metric("TOPLAM FON", f"{t_fon:,.0f} TL")

st.markdown("---")
st.subheader("📊 Fon Portföyü")
f1, f2, f3 = st.columns(3)
f1.metric("YAS (Koç)", f"{v_yas:,.0f} TL", f"{in_yas_adet} Adet")
f2.metric("YAY (Tekn)", f"{v_yay:,.0f} TL", f"{in_yay_adet} Adet")
f3.metric("YLB (Nakit)", f"{v_ylb:,.0f} TL", f"{in_ylb_adet} Adet")

st.markdown("---")
l_col, r_col = st.columns([2, 1])

with l_col:
    st.subheader("💳 Güvenlik Barı")
    if in_borc > 0: oran = (v_ylb / in_borc) * 100
    elif v_ylb > 0: oran = 100
    else: oran = 0
    st.progress(min(int(oran), 100))
    m1, m2, m3 = st.columns(3)
    m1.metric("Borç", f"{in_borc:,.0f}")
    m2.metric("Nakit", f"{v_ylb:,.0f}")
    m3.metric("Durum", "GÜVENLİ" if (v_ylb-in_borc)>=0 else "RİSKLİ", f"{v_ylb-in_borc:,.0f}")

with r_col:
    st.subheader("👶 Çocuk")
    vf=get_yf("FROTO.IS"); vt=get_yf("THYAO.IS"); vp=get_yf("TUPRS.IS")
    lf=st.number_input("FROTO",2); lt=st.number_input("THYAO",5); lp=st.number_input("TUPRS",30)
    st.metric("Değer", f"{(lf*vf)+(lt*vt)+(lp*vp):,.0f} TL")

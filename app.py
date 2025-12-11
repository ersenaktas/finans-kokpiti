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

# ---------------------------------------------------------
# 1. HAFIZA BAŞLATMA (SESSION STATE)
# ---------------------------------------------------------
# Burada hem güncel fiyatı hem de "Eski Fiyatı" (Prev) tutuyoruz.
# Böylece değişim (Delta) hesaplayabiliriz.

if 'init' not in st.session_state:
    # YAS
    st.session_state['yas_val'] = 13.43
    st.session_state['yas_old'] = 13.43
    st.session_state['yas_src'] = "Başlangıç"
    
    # YAY
    st.session_state['yay_val'] = 1283.30
    st.session_state['yay_old'] = 1283.30
    st.session_state['yay_src'] = "Başlangıç"
    
    # YLB
    st.session_state['ylb_val'] = 1.40
    st.session_state['ylb_old'] = 1.40
    st.session_state['ylb_src'] = "Başlangıç"
    
    st.session_state['last_update'] = "-"
    st.session_state['init'] = True

# ---------------------------------------------------------
# 2. VERİ ÇEKME FONKSİYONLARI (KAYNAK İSMİ İLE)
# ---------------------------------------------------------
def fetch_fund_data(fund_code):
    """
    Hem Fiyatı hem de Kaynağı döner: (Fiyat, "Kaynak İsmi")
    """
    # 1. DENEME: TEFAS (Devlet)
    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://www.google.com/'
        }
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            val = soup.select_one(".top-list > li:nth-child(1) > span").text
            price = float(val.replace(",", "."))
            return price, "TEFAS"
    except: pass

    # 2. DENEME: FINTABLES
    try:
        url = f"https://fintables.com/fonlar/{fund_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
        match = re.search(r'Son Fiyat\s*[:\s]*([\d\.]+,\d+)', text)
        if match:
             price = float(match.group(1).replace('.', '').replace(',', '.'))
             return price, "Fintables"
    except: pass

    return None, None # Başarısız

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
# 3. GÜNCELLEME BUTONU (DEĞİŞİM MANTIĞI)
# ---------------------------------------------------------
st.sidebar.header("🕹️ Komuta Merkezi")

if st.sidebar.button("🔄 Piyasayı Tara ve Güncelle"):
    with st.spinner('TEFAS, Fintables ve Kayseri taranıyor...'):
        
        # YAS GÜNCELLEME
        p, s = fetch_fund_data("YAS")
        if p:
            st.session_state['yas_old'] = st.session_state['yas_val'] # Eskiyi sakla
            st.session_state['yas_val'] = p # Yeniyi yaz
            st.session_state['yas_src'] = s # Kaynağı yaz
            
        # YAY GÜNCELLEME
        p, s = fetch_fund_data("YAY")
        if p:
            st.session_state['yay_old'] = st.session_state['yay_val']
            st.session_state['yay_val'] = p
            st.session_state['yay_src'] = s
            
        # YLB GÜNCELLEME
        p, s = fetch_fund_data("YLB")
        if p:
            st.session_state['ylb_old'] = st.session_state['ylb_val']
            st.session_state['ylb_val'] = p
            st.session_state['ylb_src'] = s
            
        # ZAMAN
        tz = pytz.timezone("Turkey")
        st.session_state['last_update'] = datetime.now(tz).strftime("%H:%M:%S")
        
        st.cache_data.clear()

st.sidebar.caption(f"Son Tarama: {st.session_state['last_update']}")

# ---------------------------------------------------------
# 4. VERİ GİRİŞLERİ (SESSION STATE BAĞLANTILI)
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🎛️ Veri Girişi")

# FONLAR
st.sidebar.subheader("📈 Fonlar")
# Burada value=st.session_state[...] diyerek otomatik güncellenen değeri kutuya koyuyoruz
in_yas_fiyat = st.sidebar.number_input("YAS Fiyat", value=st.session_state['yas_val'], format="%.4f")
in_yas_adet = st.sidebar.number_input("YAS Adet", value=734)

in_yay_fiyat = st.sidebar.number_input("YAY Fiyat", value=st.session_state['yay_val'], format="%.4f")
in_yay_adet = st.sidebar.number_input("YAY Adet", value=7)

in_ylb_fiyat = st.sidebar.number_input("YLB Fiyat", value=st.session_state['ylb_val'], format="%.4f")
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
# 5. HESAPLAMALAR
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
# 6. EKRAN GÖSTERİMİ (DELTA VE KAYNAK BİLGİSİ)
# ---------------------------------------------------------
st.title("🚀 Finansal Özgürlük Kokpiti")

st.markdown(f"""
<small>Veriler <b>{st.session_state['last_update']}</b> saatinde çekilmiştir.</small>
""", unsafe_allow_html=True)

# ÜST PİYASA BANDI
st.subheader("🏷️ Canlı Piyasa & Değişimler")
k1, k2, k3, k4, k5 = st.columns(5)

# DELTA HESAPLARI
# Eğer fiyat yeni güncellendiyse (Old != Val), farkı gösterir.
# Fark yoksa 0.00 yazar.
delta_yas = st.session_state['yas_val'] - st.session_state['yas_old']
delta_yay = st.session_state['yay_val'] - st.session_state['yay_old']
delta_ylb = st.session_state['ylb_val'] - st.session_state['ylb_old']

# Metric Kullanımı: label="İsim (Kaynak)", value="Fiyat", delta="Değişim"
k1.metric(f"YAS ({st.session_state['yas_src']})", f"{in_yas_fiyat:.4f}", f"{delta_yas:+.4f}")
k2.metric(f"YAY ({st.session_state['yay_src']})", f"{in_yay_fiyat:.4f}", f"{delta_yay:+.4f}")
k3.metric(f"YLB ({st.session_state['ylb_src']})", f"{in_ylb_fiyat:.4f}", f"{delta_ylb:+.4f}")
k4.metric("Dolar/TL (Yahoo)", f"{usd_tl:.2f}")
k5.metric("Has Altın (Ons)", f"{safe_has:,.0f} TL")

# ALTINLAR
m1, m2 = st.columns(2)
m1.metric(f"Çeyrek ({kayseri['src']})", f"{in_c_fiyat:,.0f} TL")
m2.metric(f"Bilezik ({kayseri['src']})", f"{in_b_fiyat:,.0f} TL")

st.markdown("---")

# ANA KARTLAR
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{t_gold:,.0f} TL")
c3.metric("TOPLAM FON", f"{t_fon:,.0f} TL")

st.markdown("---")

# DETAYLAR
st.subheader("📊 Portföy Dağılımı")
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
    x1, x2, x3 = st.columns(3)
    x1.metric("Borç", f"{in_borc:,.0f}")
    x2.metric("Nakit", f"{v_ylb:,.0f}")
    x3.metric("Durum", "GÜVENLİ" if (v_ylb-in_borc)>=0 else "RİSKLİ", f"{v_ylb-in_borc:,.0f}")

with r_col:
    st.subheader("👶 Çocuk")
    vf=get_yf("FROTO.IS"); vt=get_yf("THYAO.IS"); vp=get_yf("TUPRS.IS")
    lf=st.number_input("FROTO",2); lt=st.number_input("THYAO",5); lp=st.number_input("TUPRS",30)
    st.metric("Değer", f"{(lf*vf)+(lt*vt)+(lp*vp):,.0f} TL")

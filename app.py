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

# --- BAŞLANGIÇ AYARLARI (SESSION STATE) ---
# Burası "Hafıza" bölümüdür. Sayfa yenilense bile değerleri tutar.
if 'yas_fiyat' not in st.session_state: st.session_state['yas_fiyat'] = 13.43
if 'yay_fiyat' not in st.session_state: st.session_state['yay_fiyat'] = 1283.30 # Güncel Fiyat
if 'ylb_fiyat' not in st.session_state: st.session_state['ylb_fiyat'] = 1.40
if 'last_update' not in st.session_state: st.session_state['last_update'] = "Henüz Yapılmadı"

# ---------------------------------------------------------
# 1. VERİ ÇEKME FONKSİYONLARI
# ---------------------------------------------------------
def fetch_fund_price(fund_code):
    """
    Fiyat çekmeyi dener. Başarısız olursa 'None' döner (0 dönmez).
    Böylece mevcut fiyatı bozmayız.
    """
    # 1. Deneme: TEFAS
    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.content, "html.parser")
        val = soup.select_one(".top-list > li:nth-child(1) > span").text
        return float(val.replace(",", "."))
    except:
        pass
        
    # 2. Deneme: FINTABLES
    try:
        url = f"https://fintables.com/fonlar/{fund_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
        match = re.search(r'Son Fiyat\s*[:\s]*([\d\.]+,\d+)', text)
        if match:
             return float(match.group(1).replace('.', '').replace(',', '.'))
    except:
        pass

    return None # Başarısız olursa None dön

@st.cache_data(ttl=900)
def get_kayseri_gold():
    prices = {"ceyrek": 0, "tam": 0, "bilezik": 0, "src": "Manuel"}
    try:
        url = "https://www.kaysarder.org.tr/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
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
# 2. GÜNCELLEME BUTONU MANTIĞI
# ---------------------------------------------------------
st.sidebar.header("🕹️ Komuta Merkezi")

if st.sidebar.button("🔄 Fiyatları Güncelle"):
    with st.spinner('Fiyatlar çekiliyor...'):
        # YAS
        new_yas = fetch_fund_price("YAS")
        if new_yas: st.session_state['yas_fiyat'] = new_yas
        
        # YAY
        new_yay = fetch_fund_price("YAY")
        if new_yay: st.session_state['yay_fiyat'] = new_yay
        
        # YLB
        new_ylb = fetch_fund_price("YLB")
        if new_ylb: st.session_state['ylb_fiyat'] = new_ylb
        
        # Zaman Damgası
        tz = pytz.timezone("Turkey")
        st.session_state['last_update'] = datetime.now(tz).strftime("%H:%M:%S")
        
        st.cache_data.clear() # Cache'i temizle

st.sidebar.caption(f"Son İşlem: {st.session_state['last_update']}")

# ---------------------------------------------------------
# 3. VERİ GİRİŞLERİ (SESSION STATE KULLANIR)
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🎛️ Veri Girişi")

# FONLAR (Değerleri session_state'den alır, yani hafızadan)
st.sidebar.subheader("📈 Fonlar")
# Burada 'value' yerine 'key' kullanmıyoruz çünkü manuel değişikliğin session'a yazılmasını istiyoruz ama
# aynı zamanda kodun da oraya yazabilmesini istiyoruz. En güvenlisi value atamak.

in_yas_fiyat = st.sidebar.number_input("YAS Fiyatı", value=st.session_state['yas_fiyat'], format="%.4f")
in_yas_adet = st.sidebar.number_input("YAS Adet", value=734)

in_yay_fiyat = st.sidebar.number_input("YAY Fiyatı", value=st.session_state['yay_fiyat'], format="%.4f")
in_yay_adet = st.sidebar.number_input("YAY Adet", value=7)

in_ylb_fiyat = st.sidebar.number_input("YLB Fiyatı", value=st.session_state['ylb_fiyat'], format="%.4f")
in_ylb_adet = st.sidebar.number_input("YLB Adet", value=39400)

# ALTINLAR
kayseri = get_kayseri_gold() # Altınlar genelde sorunsuz ama yine de koruyalım

st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altınlar")
banka_gr = st.sidebar.number_input("Banka Altın (Gr)", value=130)

# Çeyrek (Otomatik gelirse al, gelmezse manuel kalır)
def_c = kayseri["ceyrek"] if kayseri["ceyrek"] > 0 else 9600.0
in_c_fiyat = st.sidebar.number_input("Çeyrek Fiyat", value=def_c)
in_c_adet = st.sidebar.number_input("Çeyrek Adet", value=53)

# Bilezik
def_b = kayseri["bilezik"] if kayseri["bilezik"] > 0 else 5600.0
in_b_fiyat = st.sidebar.number_input("Bilezik Gr Fiyatı", value=def_b)
in_b_gr = st.sidebar.number_input("Bilezik Gram", value=10)

# Tam
def_t = kayseri["tam"] if kayseri["tam"] > 0 else 38400.0
in_t_fiyat = st.sidebar.number_input("Tam Fiyat", value=def_t)
in_t_adet = st.sidebar.number_input("Tam Adet", value=0)

# DİĞER
# Yahoo Finance verileri
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

# Has Altın Hesabı
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

# Kaynak linkleri ekleyelim ki kontrol edebilin
st.markdown("""
<small>Fiyat Kontrol Linkleri: 
<a href='https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod=YAS' target='_blank'>YAS (TEFAS)</a> | 
<a href='https://fintables.com/fonlar/YAY' target='_blank'>YAY (Fintables)</a> | 
<a href='https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod=YLB' target='_blank'>YLB (TEFAS)</a>
</small>
""", unsafe_allow_html=True)

st.subheader("🏷️ Piyasa Göstergeleri")
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

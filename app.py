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

# ---------------------------------------------------------
# 1. AKILLI FONKSİYONLAR (HEM FİYAT HEM KAYNAK DÖNER)
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_fund_data(fund_code):
    """
    Önce Fintables'ı dener, olmazsa TEFAS'ı dener.
    Geriye (Fiyat, Kaynakİsmi) döner.
    """
    # 1. DENEME: FINTABLES
    url_fin = f"https://fintables.com/fonlar/{fund_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url_fin, headers=headers, timeout=5)
        if r.status_code == 200:
            text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
            match = re.search(r'Son Fiyat\s*[:\s]*([\d\.]+,\d+)', text)
            if match:
                price = float(match.group(1).replace('.', '').replace(',', '.'))
                return price, "Fintables"
    except: pass

    # 2. DENEME: TEFAS
    url_tefas = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    try:
        r = requests.get(url_tefas, headers=headers, timeout=5)
        soup = BeautifulSoup(r.content, "html.parser")
        val = soup.select_one(".top-list > li:nth-child(1) > span").text
        price = float(val.replace(",", "."))
        return price, "TEFAS"
    except: pass

    # 3. BAŞARISIZ
    return 0.0, "Manuel"

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
# 2. VERİLERİ ÇEK
# ---------------------------------------------------------

# FONLAR (Fiyat ve Kaynak bilgisi beraber gelir)
p_yas, src_yas = get_fund_data("YAS")
p_yay, src_yay = get_fund_data("YAY")
p_ylb, src_ylb = get_fund_data("YLB")

# PİYASA (Yahoo)
try:
    tickers = ["TRY=X", "GC=F", "EURTRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
    m_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
except: m_data = None

def get_yf(t):
    try:
        if m_data is not None:
            v = m_data[t]['Close'].iloc[-1]
            return float(v) if not pd.isna(v) else 0.0
    except: return 0.0
    return 0.0

usd_tl = get_yf("TRY=X")
eur_tl = get_yf("EURTRY=X")
ons = get_yf("GC=F")
has_gram = (ons * usd_tl) / 31.10 if (usd_tl > 0 and ons > 0) else 0

kayseri = get_kayseri_gold()

# ---------------------------------------------------------
# 3. YAN MENÜ (HAFIZALI GİRİŞLER)
# ---------------------------------------------------------
st.sidebar.header("🎛️ Veri Girişi")

# FONLAR
st.sidebar.subheader("📈 Fonlar")

# YAS
def_yas = p_yas if p_yas > 0 else 13.43
in_yas_fiyat = st.sidebar.number_input("YAS Fiyat", value=def_yas, format="%.4f")
in_yas_adet = st.sidebar.number_input("YAS Adet", value=734) 

# YAY
def_yay = p_yay if p_yay > 0 else 5.00 # Düzeltilmiş tahmin
in_yay_fiyat = st.sidebar.number_input("YAY Fiyat", value=def_yay, format="%.4f")
in_yay_adet = st.sidebar.number_input("YAY Adet", value=7) 

# YLB
def_ylb = p_ylb if p_ylb > 0 else 1.40
in_ylb_fiyat = st.sidebar.number_input("YLB Fiyat", value=def_ylb, format="%.4f")
in_ylb_adet = st.sidebar.number_input("YLB Adet", value=39400) 

# ALTINLAR
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altınlar")
banka_gr = st.sidebar.number_input("Banka Altın (Gr)", value=130)

# Çeyrek
def_c = kayseri["ceyrek"] if kayseri["ceyrek"] > 0 else 9600.0
in_c_fiyat = st.sidebar.number_input("Çeyrek Fiyat", value=def_c)
in_c_adet = st.sidebar.number_input("Çeyrek Adet", value=53)

# Bilezik
def_b = kayseri["bilezik"] if kayseri["bilezik"] > 0 else 5600.0
in_b_fiyat = st.sidebar.number_input("Bilezik Fiyat", value=def_b)
in_b_gr = st.sidebar.number_input("Bilezik Gram", value=10)

# Tam
def_t = kayseri["tam"] if kayseri["tam"] > 0 else 38400.0
in_t_fiyat = st.sidebar.number_input("Tam Fiyat", value=def_t)
in_t_adet = st.sidebar.number_input("Tam Adet", value=0)

# DİĞER
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

safe_has = has_gram if has_gram > 0 else 3100.0
v_banka = banka_gr * safe_has
v_ziynet = (in_c_adet * in_c_fiyat) + (in_t_adet * in_t_fiyat)
v_bilezik = in_b_gr * in_b_fiyat
t_gold = v_banka + v_ziynet + v_bilezik

t_euro = in_eur_miktar * in_eur_kur
net = t_fon + t_gold + t_euro

# ---------------------------------------------------------
# 5. EKRAN GÖSTERİMİ
# ---------------------------------------------------------

# PİYASA VE KAYNAK GÖSTERGELERİ (İSTEDİĞİNİZ KISIM)
st.subheader("🏷️ Canlı Fiyatlar & Kaynaklar")

k1, k2, k3, k4, k5, k6 = st.columns(6)

# Metric içinde "delta" parametresini kaynak göstermek için kullanıyoruz
k1.metric("YAS Fiyat", f"{in_yas_fiyat:.4f}", f"Kaynak: {src_yas}")
k2.metric("YAY Fiyat", f"{in_yay_fiyat:.4f}", f"Kaynak: {src_yay}")
k3.metric("YLB Fiyat", f"{in_ylb_fiyat:.4f}", f"Kaynak: {src_ylb}")
k4.metric("Dolar/TL", f"{usd_tl:.2f}", "Yahoo")
k5.metric("Euro/TL", f"{in_eur_kur:.2f}", "Yahoo/Manuel")
k6.metric("Has Altın", f"{safe_has:,.0f}", "Global Ons")

# Kayseri Verileri
m1, m2 = st.columns(2)
m1.metric("Çeyrek Altın", f"{in_c_fiyat:,.0f} TL", f"Kaynak: {kayseri['src']}")
m2.metric("Bilezik (22k)", f"{in_b_fiyat:,.0f} TL", f"Kaynak: {kayseri['src']}")

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

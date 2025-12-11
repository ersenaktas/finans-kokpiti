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
# 1. ÖZEL FONKSİYON: FINTABLES FİYAT AVCISI
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def get_fintables_price(fund_code):
    """
    Fintables.com üzerinden fon fiyatını çeker.
    Reklamlara takılmadan HTML içinden veriyi bulur.
    """
    url = f"https://fintables.com/fonlar/{fund_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Yöntem 1: Sayfa başlığındaki veya meta etiketlerdeki fiyatı ara
            # Genelde Fintables HTML yapısında fiyat belirgin bir class'tadır ama değişebilir.
            # En güvenli yöntem: Tüm metni alıp 'Fiyat' kelimesinin yanındaki sayıyı bulmak.
            
            text = soup.get_text(" ", strip=True)
            
            # Regex: "1.283,29" veya "13,4368" gibi Türkçe formatı yakalar
            # "Son Fiyat" yazısından sonra gelen sayıyı arar
            # Örnek metin: "YAY Son Fiyat: 1.283,29 TL"
            match = re.search(r'Son Fiyat\s*[:\s]*([\d\.]+,\d+)', text)
            
            if match:
                price_str = match.group(1)
                # Türkçe formatı (1.283,29) -> Python formatına (1283.29) çevir
                price_float = float(price_str.replace('.', '').replace(',', '.'))
                return price_float
            
            # Yöntem 2: Eğer "Son Fiyat" yazmıyorsa, sayfanın başındaki büyük rakamı ara
            # Fintables'ta genelde sol üstte fon kodu ve yanında fiyat yazar.
            # Sayfadaki ilk anlamlı para birimini bulmayı deneyebiliriz.
            # (Bu kısım yedek, yukarıdaki genelde çalışır)
            
    except Exception as e:
        print(f"Hata ({fund_code}): {e}")
        
    return 0.0

# ---------------------------------------------------------
# 2. YEDEK FONKSİYON: TEFAS (Devlet)
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def get_tefas_price(fund_code):
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.content, "html.parser")
        val = soup.select_one(".top-list > li:nth-child(1) > span").text
        return float(val.replace(",", "."))
    except:
        return 0.0

# ---------------------------------------------------------
# 3. KAYSERİ ALTIN (Tablo/Reklam Korumalı)
# ---------------------------------------------------------
@st.cache_data(ttl=900)
def get_kayseri_gold():
    prices = {"ceyrek": 0, "tam": 0, "bilezik": 0}
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
    except: pass
    return prices

# ---------------------------------------------------------
# 4. VERİLERİ ÇEK
# ---------------------------------------------------------

# FONLAR (Önce Fintables, Olmazsa TEFAS)
p_yas = get_fintables_price("YAS")
if p_yas == 0: p_yas = get_tefas_price("YAS")

p_yay = get_fintables_price("YAY")
if p_yay == 0: p_yay = get_tefas_price("YAY")

p_ylb = get_fintables_price("YLB")
if p_ylb == 0: p_ylb = get_tefas_price("YLB")

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
if usd_tl > 0 and ons > 0: has_gram = (ons * usd_tl) / 31.10
else: has_gram = 0

kayseri = get_kayseri_gold()

# ---------------------------------------------------------
# 5. YAN MENÜ (MANUEL/OTO GİRİŞ)
# ---------------------------------------------------------
st.sidebar.header("🎛️ Veri Girişi")

# FONLAR
st.sidebar.subheader("📈 Fonlar")
# YAS
def_yas = p_yas if p_yas > 0 else 13.43 # Tahmini son fiyat
in_yas_fiyat = st.sidebar.number_input("YAS Fiyatı", value=def_yas, format="%.4f")
in_yas_adet = st.sidebar.number_input("YAS Adet", value=734) # Sizin adet

# YAY
def_yay = p_yay if p_yay > 0 else 1283.00 # Tahmini son fiyat
in_yay_fiyat = st.sidebar.number_input("YAY Fiyatı", value=def_yay, format="%.4f")
in_yay_adet = st.sidebar.number_input("YAY Adet", value=7) # Sizin adet

# YLB
def_ylb = p_ylb if p_ylb > 0 else 1.4017 # Tahmini son fiyat
in_ylb_fiyat = st.sidebar.number_input("YLB Fiyatı", value=def_ylb, format="%.4f")
in_ylb_adet = st.sidebar.number_input("YLB Adet", value=39400) # Sizin adet

# ALTINLAR
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altınlar")
banka_gr = st.sidebar.number_input("Banka Altın (Gr)", value=130)

def_c = kayseri["ceyrek"] if kayseri["ceyrek"] > 0 else 9600.0
def_b = kayseri["bilezik"] if kayseri["bilezik"] > 0 else 5600.0
def_t = kayseri["tam"] if kayseri["tam"] > 0 else 38400.0

in_c_fiyat = st.sidebar.number_input("Çeyrek Fiyat", value=def_c)
in_c_adet = st.sidebar.number_input("Çeyrek Adet", value=53)

in_b_fiyat = st.sidebar.number_input("Bilezik Fiyat", value=def_b)
in_b_gr = st.sidebar.number_input("Bilezik Gram", value=10)

in_t_fiyat = st.sidebar.number_input("Tam Fiyat", value=def_t)
in_t_adet = st.sidebar.number_input("Tam Adet", value=0)

# DÖVİZ
st.sidebar.markdown("---")
st.sidebar.subheader("💶 Diğer")
def_eur = eur_tl if eur_tl > 0 else 49.97
in_eur_kur = st.sidebar.number_input("Euro Kuru", value=def_eur)
in_eur_miktar = st.sidebar.number_input("Euro Miktarı", value=10410)
in_borc = st.sidebar.number_input("Kredi Kartı Borcu", value=34321)

# ---------------------------------------------------------
# 6. HESAPLAMALAR
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
# 7. EKRAN
# ---------------------------------------------------------
st.subheader("🏷️ Piyasa (Canlı)")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Has Altın", f"{safe_has:,.0f} TL")
c2.metric("Çeyrek", f"{in_c_fiyat:,.0f} TL")
c3.metric("Dolar", f"{usd_tl:.2f}")
c4.metric("YAS Fiyat", f"{in_yas_fiyat:.4f}")
c5.metric("YAY Fiyat", f"{in_yay_fiyat:.4f}")

st.markdown("---")

k1, k2, k3 = st.columns(3)
k1.metric("TOPLAM SERVET", f"{net:,.0f} TL")
k2.metric("TOPLAM ALTIN", f"{t_gold:,.0f} TL")
k3.metric("TOPLAM FON", f"{t_fon:,.0f} TL")

st.markdown("---")

st.subheader("📊 Fon Detayı")
f1, f2, f3 = st.columns(3)
f1.metric("YAS", f"{v_yas:,.0f} TL", f"{in_yas_adet} Adet")
f2.metric("YAY", f"{v_yay:,.0f} TL", f"{in_yay_adet} Adet")
f3.metric("YLB", f"{v_ylb:,.0f} TL", f"{in_ylb_adet} Adet")

st.markdown("---")

l_col, r_col = st.columns([2, 1])
with l_col:
    st.subheader("💳 Güvenlik")
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

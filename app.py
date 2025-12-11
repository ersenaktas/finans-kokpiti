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
# 1. VERİ KAYNAĞI: FONLAR (TEFAS -> FINTABLES -> MANUEL)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def get_fund_price_tefas(fund_code):
    # Öncelik 1: TEFAS (Resmi Devlet Sitesi)
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        # TEFAS'ta fiyat genelde ".top-list" içindeki ilk span'dadır
        # Liste: Son Fiyat, Günlük Getiri, Pay (Adet)
        price_text = soup.select_one(".top-list > li:nth-child(1) > span").text
        price = float(price_text.replace(",", "."))
        return price
    except:
        # Öncelik 2: Fintables (Yedek)
        return get_fund_price_fintables(fund_code)

def get_fund_price_fintables(fund_code):
    url = f"https://fintables.com/fonlar/{fund_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(" ", strip=True)
        match = re.search(r'Son Fiyat.*?(\d+[\.,]\d+)', text)
        if match:
            return float(match.group(1).replace('.', '').replace(',', '.'))
    except:
        return 0.0
    return 0.0

# Fiyatları Çek
p_yas = get_fund_price_tefas("YAS")
p_yay = get_fund_price_tefas("YAY")
p_ylb = get_fund_price_tefas("YLB")

# ---------------------------------------------------------
# 2. VERİ KAYNAĞI: ALTIN (KAYSERİ -> ALTINKAYNAK -> MANUEL)
# ---------------------------------------------------------
@st.cache_data(ttl=900)
def get_gold_prices():
    prices = {"ceyrek": 0.0, "tam": 0.0, "bilezik22": 0.0, "gram_has": 0.0, "dolar": 0.0, "euro": 0.0, "src": "Manuel"}
    
    # 1. KAYNAK: KAYSERİ SARRAFLAR
    try:
        url = "https://www.kaysarder.org.tr/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            text = soup.get_text(" ", strip=True)
            
            m_ceyrek = re.search(r'25\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
            m_tam = re.search(r'100\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
            m_bilezik = re.search(r'22\s*AYAR.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
            
            if m_ceyrek: prices["ceyrek"] = float(m_ceyrek.group(1).replace('.', '').replace(',', '.'))
            if m_tam: prices["tam"] = float(m_tam.group(1).replace('.', '').replace(',', '.'))
            if m_bilezik: prices["bilezik22"] = float(m_bilezik.group(1).replace('.', '').replace(',', '.'))
            
            if prices["ceyrek"] > 0:
                prices["src"] = "Kayseri"
                return prices
    except: pass

    # 2. KAYNAK: ALTINKAYNAK (YEDEK)
    # Kayseri çalışmazsa genel piyasa verisini çekelim ki "0" görünmesin
    try:
        url2 = "http://data.altinkaynak.com/DataService.asmx?op=GetGold" # XML Servisi veya Scraping
        # Basitlik için Harem Altın veya benzeri bir yerden scraping deneyebiliriz
        # Veya Yahoo Finance'den hesaplayabiliriz.
        pass
    except: pass
    
    return prices

gold_data = get_gold_prices()

# ---------------------------------------------------------
# 3. VERİ KAYNAĞI: HİSSE VE DÖVİZ (YAHOO)
# ---------------------------------------------------------
try:
    tickers = ["XU100.IS", "NQ=F", "GC=F", "TRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
    market_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
except: market_data = None

def get_yfinance(ticker):
    try:
        if market_data is not None and ticker in market_data:
            val = market_data[ticker]['Close'].iloc[-1]
            if pd.isna(val): return 0.0
            return float(val)
        return 0.0
    except: return 0.0

dolar_tl = get_yfinance('TRY=X')
ons_altin = get_yfinance('GC=F')
# Has Altın ve Euro Hesabı
if dolar_tl > 0 and ons_altin > 0:
    has_altin_tl = (ons_altin * dolar_tl) / 31.10
else:
    # Yahoo çalışmazsa manuel fallback
    has_altin_tl = 0 

euro_tl = dolar_tl * 1.05

# ---------------------------------------------------------
# EKRAN YERLEŞİMİ (DASHBOARD)
# ---------------------------------------------------------

# A) PİYASA ÖZETİ (FONLAR BURADA!)
st.subheader("📊 Piyasa & Fon Fiyatları (Canlı)")

# 6 Kolonlu Üst Bar
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("YAS (Koç)", f"{p_yas:.4f}", "TEFAS" if p_yas > 0 else "Yok")
m2.metric("YAY (Tekn)", f"{p_yay:.4f}", "TEFAS" if p_yay > 0 else "Yok")
m3.metric("YLB (Nakit)", f"{p_ylb:.4f}", "TEFAS" if p_ylb > 0 else "Yok")
m4.metric("Dolar/TL", f"{dolar_tl:.2f}")
m5.metric("Euro/TL", f"{euro_tl:.2f}")
m6.metric("Gram Has", f"{has_altin_tl:,.0f}")

# Kayseri Verileri (Çeyrek / Bilezik)
k1, k2, k3 = st.columns(3)

# Veri varsa göster, yoksa manuel iste
val_ceyrek_src = gold_data["ceyrek"] if gold_data["ceyrek"] > 0 else 0
val_bilezik_src = gold_data["bilezik22"] if gold_data["bilezik22"] > 0 else 0

k1.metric("Çeyrek Altın", f"{val_ceyrek_src:,.0f} TL", gold_data["src"])
k2.metric("22 Ayar Bilezik", f"{val_bilezik_src:,.0f} TL", gold_data["src"])
k3.metric("Tam Altın", f"{gold_data.get('tam',0):,.0f} TL", gold_data["src"])

st.markdown("---")

# SOL MENÜ (GİRİŞLER)
st.sidebar.header("💰 Varlık Girişleri")

# 1. FON GİRİŞİ (Fiyatlar otomatik gelirse kilitli gibi durur, ama değiştirilebilir)
st.sidebar.subheader("📈 Fon Adetleri")
yas_adet = st.sidebar.number_input("YAS Adet", value=10000)
# Eğer fiyat çekilemediyse manuel girmeye izin ver
in_yas_fiyat = p_yas if p_yas > 0 else st.sidebar.number_input("YAS Fiyat (Manuel)", value=5.0)

yay_adet = st.sidebar.number_input("YAY Adet", value=5000)
in_yay_fiyat = p_yay if p_yay > 0 else st.sidebar.number_input("YAY Fiyat (Manuel)", value=4.0)

ylb_adet = st.sidebar.number_input("YLB Adet", value=1000)
in_ylb_fiyat = p_ylb if p_ylb > 0 else st.sidebar.number_input("YLB Fiyat (Manuel)", value=55.0)

# Değer Hesapları
v_yas = yas_adet * in_yas_fiyat
v_yay = yay_adet * in_yay_fiyat
v_ylb = ylb_adet * in_ylb_fiyat

# 2. ALTIN GİRİŞİ
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altın Varlıkları")
banka_gram = st.sidebar.number_input("Banka Altın (Gr)", value=130)

# Fiyatlar otomatik gelmediyse manuel sor
def_c = val_ceyrek_src if val_ceyrek_src > 0 else 9600
def_b = val_bilezik_src if val_bilezik_src > 0 else 5600
def_t = gold_data["tam"] if gold_data["tam"] > 0 else 38400

ceyrek_adet = st.sidebar.number_input("Çeyrek Adet", value=53)
in_ceyrek_fiyat = st.sidebar.number_input("Çeyrek Fiyat", value=def_c)

bilezik_gram = st.sidebar.number_input("Bilezik Gram", value=0)
in_bilezik_fiyat = st.sidebar.number_input("Bilezik Fiyat", value=def_b)

tam_adet = st.sidebar.number_input("Tam Adet", value=0)
in_tam_fiyat = st.sidebar.number_input("Tam Fiyat", value=def_t)

# 3. DİĞER
st.sidebar.markdown("---")
st.sidebar.subheader("💶 Diğer")
euro_miktar = st.sidebar.number_input("Euro Miktarı", value=10410)
borc = st.sidebar.number_input("Kredi Kartı Borcu", value=34321)

# TOPLAMLAR
toplam_altin = (banka_gram * has_altin_tl) + (ceyrek_adet * in_ceyrek_fiyat) + (tam_adet * in_tam_fiyat) + (bilezik_gram * in_bilezik_fiyat)
toplam_fon = v_yas + v_yay + v_ylb
toplam_euro = euro_miktar * euro_tl
net_servet = toplam_altin + toplam_fon + toplam_euro

# GÖSTERGE
col1, col2, col3 = st.columns(3)
col1.metric("TOPLAM SERVET", f"{net_servet:,.0f} TL")
col2.metric("TOPLAM ALTIN", f"{toplam_altin:,.0f} TL")
col3.metric("TOPLAM FON", f"{toplam_fon:,.0f} TL")

st.markdown("---")

# DETAYLAR
st.subheader("🔍 Portföy Detayı")
c1, c2, c3 = st.columns(3)
c1.metric("YAS Değeri", f"{v_yas:,.0f} TL")
c2.metric("YAY Değeri", f"{v_yay:,.0f} TL")
c3.metric("YLB (Nakit)", f"{v_ylb:,.0f} TL")

# ARBİTRAJ & ÇOCUK
l_col, r_col = st.columns([2, 1])
with l_col:
    st.subheader("💳 Güvenlik Barı")
    margin = v_ylb - borc
    ratio = (v_ylb / borc) * 100 if borc > 0 else 100
    if math.isnan(ratio) or math.isinf(ratio): ratio = 0
    
    st.progress(min(int(ratio), 100))
    k1, k2, k3 = st.columns(3)
    k1.metric("Borç", f"{borc:,.0f}")
    k2.metric("Nakit", f"{v_ylb:,.0f}")
    k3.metric("Durum", "GÜVENLİ" if margin >=0 else "RİSKLİ", f"{margin:,.0f}")

with r_col:
    st.subheader("👶 Çocuk")
    # Hisse fiyatlarını çek
    p_f = get_yfinance('FROTO.IS')
    p_t = get_yfinance('THYAO.IS')
    p_p = get_yfinance('TUPRS.IS')
    
    l_f = st.number_input("FROTO", value=2)
    l_t = st.number_input("THYAO", value=5)
    l_p = st.number_input("TUPRS", value=30)
    
    c_val = (l_f*p_f) + (l_t*p_t) + (l_p*p_p)
    st.metric("Değer", f"{c_val:,.0f} TL")

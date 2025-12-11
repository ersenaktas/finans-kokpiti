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
# 1. FONKSİYONLAR: VERİ ÇEKME (HATA KORUMALI)
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_tefas_price(fund_code):
    """TEFAS'tan fiyat çeker, bulamazsa 0 döner"""
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.content, "html.parser")
        # TEFAS genelde ilk 'top-list' iteminde fiyatı verir
        val = soup.select_one(".top-list > li:nth-child(1) > span").text
        return float(val.replace(",", "."))
    except:
        return 0.0

@st.cache_data(ttl=900)
def get_kayseri_gold():
    """Kayseri Sarraflar'dan veri dener"""
    prices = {"ceyrek": 0, "tam": 0, "bilezik": 0}
    try:
        url = "https://www.kaysarder.org.tr/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
        
        # Regex ile Avlama
        mc = re.search(r'25\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
        mt = re.search(r'100\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
        mb = re.search(r'22\s*AYAR.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
        
        if mc: prices["ceyrek"] = float(mc.group(1).replace('.', '').replace(',', '.'))
        if mt: prices["tam"] = float(mt.group(1).replace('.', '').replace(',', '.'))
        if mb: prices["bilezik"] = float(mb.group(1).replace('.', '').replace(',', '.'))
    except: pass
    return prices

# ---------------------------------------------------------
# 2. VERİLERİ TOPLA (CANLI)
# ---------------------------------------------------------

# A) FONLAR (Otomatik Çek)
auto_yas = get_tefas_price("YAS")
auto_yay = get_tefas_price("YAY")
auto_ylb = get_tefas_price("YLB")

# B) PİYASA (Yahoo - Daha Güvenilir)
try:
    tickers = ["TRY=X", "GC=F", "EURTRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
    m_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
except: m_data = None

def get_yf_val(ticker):
    try:
        if m_data is not None:
            v = m_data[ticker]['Close'].iloc[-1]
            return float(v) if not pd.isna(v) else 0.0
    except: return 0.0
    return 0.0

usd_tl = get_yf_val("TRY=X")
eur_tl = get_yf_val("EURTRY=X")
ons = get_yf_val("GC=F")

# Has Altın (Matematiksel Hesap - En Güvenilir Yöntem)
if usd_tl > 0 and ons > 0:
    has_gram = (ons * usd_tl) / 31.10
else:
    has_gram = 0

# C) KAYSERİ ALTIN
kayseri = get_kayseri_gold()

# ---------------------------------------------------------
# 3. YAN MENÜ (BURASI ARTIK KONTROL MERKEZİ)
# ---------------------------------------------------------
st.sidebar.header("🎛️ Kontrol Paneli")

# --- FONLAR ---
st.sidebar.subheader("📈 Fonlar (Fiyat & Adet)")

# MANTIK: Eğer otomatik fiyat (auto_yas) > 0 ise onu varsayılan yap.
# Değilse, kullanıcının en son bildiği veya manuel girdiği fiyatı koru.

# YAS
def_yas = auto_yas if auto_yas > 0 else 5.20 # Fallback değer
in_yas_fiyat = st.sidebar.number_input("YAS Fiyatı", value=def_yas, format="%.4f")
in_yas_adet = st.sidebar.number_input("YAS Adet", value=10000)

# YAY
def_yay = auto_yay if auto_yay > 0 else 4.10
in_yay_fiyat = st.sidebar.number_input("YAY Fiyatı", value=def_yay, format="%.4f")
in_yay_adet = st.sidebar.number_input("YAY Adet", value=5000)

# YLB
def_ylb = auto_ylb if auto_ylb > 0 else 55.50
in_ylb_fiyat = st.sidebar.number_input("YLB Fiyatı", value=def_ylb, format="%.4f")
in_ylb_adet = st.sidebar.number_input("YLB Adet", value=1000)

# --- ALTINLAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altınlar")

banka_gr = st.sidebar.number_input("Banka Altın (Gr)", value=130)

# Çeyrek (Otomatik gelirse yaz, gelmezse manuel bırak)
def_ceyrek = kayseri["ceyrek"] if kayseri["ceyrek"] > 0 else 9600.0
in_ceyrek_fiyat = st.sidebar.number_input("Çeyrek Fiyatı", value=def_ceyrek)
in_ceyrek_adet = st.sidebar.number_input("Çeyrek Adet", value=53)

# Bilezik
def_bilezik = kayseri["bilezik"] if kayseri["bilezik"] > 0 else 5600.0
in_bilezik_fiyat = st.sidebar.number_input("Bilezik Gr Fiyatı", value=def_bilezik)
in_bilezik_gr = st.sidebar.number_input("Bilezik Gramı

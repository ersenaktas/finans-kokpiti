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
in_bilezik_gr = st.sidebar.number_input("Bilezik Gramı", value=0)

# Tam
def_tam = kayseri["tam"] if kayseri["tam"] > 0 else 38400.0
in_tam_fiyat = st.sidebar.number_input("Tam Altın Fiyatı", value=def_tam)
in_tam_adet = st.sidebar.number_input("Tam Adet", value=0)

# --- DÖVİZ & BORÇ ---
st.sidebar.markdown("---")
st.sidebar.subheader("💶 Diğer")
# Eğer Yahoo çalışmazsa manuel kur girilsin
def_eur = eur_tl if eur_tl > 0 else 44.50
in_eur_kur = st.sidebar.number_input("Euro Kuru", value=def_eur)
in_eur_miktar = st.sidebar.number_input("Euro Miktarı", value=10410)

in_borc = st.sidebar.number_input("Kredi Kartı Borcu", value=34321)


# ---------------------------------------------------------
# 4. HESAPLAMALAR (SADECE MANUEL GİRİŞLERİ KULLANIR)
# ---------------------------------------------------------
# Sistem artık "in_" ile başlayan değişkenleri kullanır.
# Bu değişkenler otomatik dolduysa otomatiktir, dolmadıysa manueldir.
# Böylece ASLA 0 çıkmaz.

val_yas = in_yas_fiyat * in_yas_adet
val_yay = in_yay_fiyat * in_yay_adet
val_ylb = in_ylb_fiyat * in_ylb_adet
total_fon = val_yas + val_yay + val_ylb

# Altın Hesabı
# Banka altını için Has Gram (Otomatik hesaplanan) kullanılır
# Eğer o da 0 ise manuel bir değer atayalım
safe_has_gram = has_gram if has_gram > 0 else 5800.0

val_banka = banka_gr * safe_has_gram
val_ziynet = (in_ceyrek_adet * in_ceyrek_fiyat) + (in_tam_adet * in_tam_fiyat)
val_bilezik = in_bilezik_gr * in_bilezik_fiyat
total_gold = val_banka + val_ziynet + val_bilezik

total_euro = in_eur_miktar * in_eur_kur
net_worth = total_fon + total_gold + total_euro

# ---------------------------------------------------------
# 5. EKRAN GÖSTERİMİ
# ---------------------------------------------------------

# ÜST PİYASA BANDI
st.subheader("🏷️ Piyasa Göstergeleri")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Gram Has", f"{safe_has_gram:,.0f} TL")
k2.metric("Dolar/TL", f"{usd_tl:.2f}")
k3.metric("Euro/TL", f"{in_eur_kur:.2f}")
# Fon fiyatlarını gösterirken kaynağı belirt
src_yas = "TEFAS" if auto_yas > 0 else "Manuel"
src_ceyrek = "Kayseri" if kayseri["ceyrek"] > 0 else "Manuel"
k4.metric("YAS Fiyat", f"{in_yas_fiyat:.4f}", src_yas)
k5.metric("Çeyrek Fiyat", f"{in_ceyrek_fiyat:,.0f}", src_ceyrek)

st.markdown("---")

# ANA SERVET KARTLARI
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net_worth:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{total_gold:,.0f} TL")
c3.metric("TOPLAM FON", f"{total_fon:,.0f} TL")

st.markdown("---")

# FON DETAYLARI
st.subheader("📊 Fon Portföyü")
f1, f2, f3 = st.columns(3)
f1.metric("YAS (Koç)", f"{val_yas:,.0f} TL", f"{in_yas_adet} Adet")
f2.metric("YAY (Tekn)", f"{val_yay:,.0f} TL", f"{in_yay_adet} Adet")
f3.metric("YLB (Nakit)", f"{val_ylb:,.0f} TL", f"{in_ylb_adet} Adet")

st.markdown("---")

# GÜVENLİK & ÇOCUK
l_col, r_col = st.columns([2, 1])

with l_col:
    st.subheader("💳 Güvenlik Barı")
    # Bölme hatası (ZeroDivision) önlemi
    if in_borc > 0:
        oran = (val_ylb / in_borc) * 100
    elif val_ylb > 0:
        oran = 100
    else:
        oran = 0
    
    st.progress(min(int(oran), 100))
    m1, m2, m3 = st.columns(3)
    m1.metric("Borç", f"{in_borc:,.0f}")
    m2.metric("Nakit", f"{val_ylb:,.0f}")
    
    fark = val_ylb - in_borc
    durum = "GÜVENLİ" if fark >= 0 else "RİSKLİ"
    m3.metric("Durum", durum, f"{fark:,.0f} TL", delta_color="normal" if fark>=0 else "inverse")

with r_col:
    st.subheader("👶 Çocuk Portföyü")
    # Hisse fiyatları da 0 gelirse diye manuel kontrol
    vf = get_yf_val("FROTO.IS"); vf = vf if vf > 0 else 1000
    vt = get_yf_val("THYAO.IS"); vt = vt if vt > 0 else 300
    vp = get_yf_val("TUPRS.IS"); vp = vp if vp > 0 else 150
    
    lf = st.number_input("FROTO", value=2)
    lt = st.number_input("THYAO", value=5)
    lp = st.number_input("TUPRS", value=30)
    
    cv = (lf*vf) + (lt*vt) + (lp*vp)
    st.metric("Toplam", f"{cv:,.0f} TL")

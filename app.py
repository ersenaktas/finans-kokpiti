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
# 1. VERİ KAYNAĞI: KAYSERİ SARRAFLAR (ALTIN)
# ---------------------------------------------------------
@st.cache_data(ttl=900)
def get_kayseri_gold():
    url = "https://www.kaysarder.org.tr/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    prices = {"ceyrek": 0.0, "tam": 0.0, "bilezik22": 0.0, "status": False}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(" ", strip=True)
            
            # Regex ile Fiyat Avlama
            # Çeyrek (25 Ziynet)
            m_ceyrek = re.search(r'25\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
            if m_ceyrek: prices["ceyrek"] = float(m_ceyrek.group(1).replace('.', '').replace(',', '.'))

            # Tam (100 Ziynet)
            m_tam = re.search(r'100\s*ZİYNET.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
            if m_tam: prices["tam"] = float(m_tam.group(1).replace('.', '').replace(',', '.'))
            
            # Bilezik (22 Ayar)
            m_bilezik = re.search(r'22\s*AYAR.*?(\d+[\.,]\d+)', text, re.IGNORECASE)
            if m_bilezik: prices["bilezik22"] = float(m_bilezik.group(1).replace('.', '').replace(',', '.'))

            if prices["ceyrek"] > 0: prices["status"] = True
    except: pass
    return prices

kayseri_data = get_kayseri_gold()

# ---------------------------------------------------------
# 2. VERİ KAYNAĞI: FINTABLES (FONLAR) - YENİ! 🚀
# ---------------------------------------------------------
@st.cache_data(ttl=1800) # 30 dakikada bir çek
def get_fund_price(fund_code):
    # Fintables üzerinden fon fiyatı çekme
    url = f"https://fintables.com/fonlar/{fund_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Fintables'ta fiyat genelde büyük bir rakam olarak yazar.
            # Sayfa başlığında veya meta etiketlerde de olabilir ama en garantisi text araması.
            # "Son Fiyat" yazısından sonraki rakamı arayalım veya direkt class yapısı.
            # Basit Regex yöntemi: "TRY" öncesindeki rakamı veya sayfadaki ilk büyük fiyatı bul.
            
            text = soup.get_text(" ", strip=True)
            # Genellikle "Son Fiyat 5.1234" gibi yazar.
            # Regex: Bir sayı, nokta veya virgül içeriyor, hemen yanında % işareti OLMAYAN (değişim oranı değil fiyat lazım)
            
            # Fintables'a özel yapı: <span class="value">5,1234</span> gibi olabilir.
            # Biz direkt sayfadaki "Son Fiyat" etiketini arayalım.
            
            match = re.search(r'Son Fiyat.*?(\d+[\.,]\d+)', text)
            if match:
                price = float(match.group(1).replace('.', '').replace(',', '.'))
                return price
            
            # Bulamazsa alternatif: Sayfadaki en belirgin para birimi formatını dene
            # Bu kısım biraz deneme yanılma gerektirir ama genelde çalışır.
            return 0.0
    except:
        return 0.0
    return 0.0

# ---------------------------------------------------------
# 3. VERİ KAYNAĞI: YAHOO FINANCE (HİSSE + DÖVİZ)
# ---------------------------------------------------------
try:
    # Fonları (YAS, YAY) buradan ÇIKARDIK. Sadece hisse ve döviz kaldı.
    tickers = ["XU100.IS", "NQ=F", "GC=F", "TRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
    market_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
except: market_data = None

def get_yfinance_price(ticker):
    try:
        if market_data is not None and ticker in market_data:
            val = market_data[ticker]['Close'].iloc[-1]
            if pd.isna(val): return 0.0
            return float(val)
        return 0.0
    except: return 0.0

# ---------------------------------------------------------
# 4. FİYATLARI TOPARLA
# ---------------------------------------------------------

# Fon Fiyatları (Fintables'tan Dene, Olmazsa Manuel)
p_yas = get_fund_price("YAS")
p_yay = get_fund_price("YAY")
p_ylb = get_fund_price("YLB")

# Hisse Fiyatları (Yahoo)
p_froto = get_yfinance_price('FROTO.IS')
p_thyao = get_yfinance_price('THYAO.IS')
p_tuprs = get_yfinance_price('TUPRS.IS')

# Piyasa Verileri
dolar_tl = get_yfinance_price('TRY=X')
ons_altin = get_yfinance_price('GC=F')
bist100 = get_yfinance_price('XU100.IS')
nasdaq = get_yfinance_price('NQ=F')

# Has Altın ve Euro
if dolar_tl > 0 and ons_altin > 0:
    has_altin_tl = (ons_altin * dolar_tl) / 31.10
else:
    has_altin_tl = 3000 # Fallback
euro_tl = dolar_tl * 1.05

# Kayseri Verileri
k_ceyrek = kayseri_data["ceyrek"] if kayseri_data["ceyrek"] > 0 else 0
k_tam = kayseri_data["tam"] if kayseri_data["tam"] > 0 else 0
k_bilezik = kayseri_data["bilezik22"] if kayseri_data["bilezik22"] > 0 else 0

# ---------------------------------------------------------
# EKRAN TASARIMI
# ---------------------------------------------------------

# ÜST BİLGİ PANELİ
st.subheader("🏷️ Piyasa Göstergeleri")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Gram Altın (Has)", f"{has_altin_tl:,.0f} TL")
k2.metric("Çeyrek (Kayseri)", f"{k_ceyrek:,.0f} TL")
k3.metric("Bilezik (Gr)", f"{k_bilezik:,.0f} TL")
k4.metric("Dolar/TL", f"{dolar_tl:.2f}")
k5.metric("Euro/TL", f"{euro_tl:.2f}")

st.markdown("---")

# SOL MENÜ (GİRİŞLER)
st.sidebar.header("💰 Varlık Girişleri")

# FONLAR
st.sidebar.subheader("📈 Fon Adetleri")
# Eğer Fintables'tan fiyat çekemediysek (0 geldiyse), kullanıcıya manuel giriş aç
yas_fiyat_input = st.sidebar.number_input("YAS Fiyatı", value=p_yas if p_yas > 0 else 5.0, format="%.4f")
yas_adet = st.sidebar.number_input("YAS Adet", value=10000)

yay_fiyat_input = st.sidebar.number_input("YAY Fiyatı", value=p_yay if p_yay > 0 else 4.0, format="%.4f")
yay_adet = st.sidebar.number_input("YAY Adet", value=5000)

ylb_fiyat_input = st.sidebar.number_input("YLB Fiyatı", value=p_ylb if p_ylb > 0 else 55.0, format="%.4f")
ylb_adet = st.sidebar.number_input("YLB Adet", value=1000)

# Hesaplama (Inputtan gelen fiyatı kullan)
val_yas = yas_adet * yas_fiyat_input
val_yay = yay_adet * yay_fiyat_input
val_ylb = ylb_adet * ylb_fiyat_input

# ALTINLAR
st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altın Varlıkları")
banka_gram = st.sidebar.number_input("Banka Altın (Gr)", value=130)

# Varsayılan değerler Kayseri'den, yoksa manuel
def_ceyrek = k_ceyrek if k_ceyrek > 0 else 9600
def_tam = k_tam if k_tam > 0 else 38400
def_bilezik = k_bilezik if k_bilezik > 0 else 5600

ceyrek_adet = st.sidebar.number_input("Çeyrek Adet", value=53)
ceyrek_fiyat_in = st.sidebar.number_input("Çeyrek Fiyat", value=def_ceyrek)

tam_adet = st.sidebar.number_input("Tam Adet", value=0)
tam_fiyat_in = st.sidebar.number_input("Tam Fiyat", value=def_tam)

bilezik_gram = st.sidebar.number_input("Bilezik Gram", value=0)
bilezik_fiyat_in = st.sidebar.number_input("Bilezik Fiyat", value=def_bilezik)

# DÖVİZ & BORÇ
st.sidebar.markdown("---")
st.sidebar.subheader("💶 Diğer")
euro_miktar = st.sidebar.number_input("Euro Miktarı", value=10410)
borc = st.sidebar.number_input("Kredi Kartı Borcu", value=34321)

# GENEL TOPLAM HESABI
toplam_altin = (banka_gram * has_altin_tl) + (ceyrek_adet * ceyrek_fiyat_in) + (tam_adet * tam_fiyat_in) + (bilezik_gram * bilezik_fiyat_in)
toplam_euro = euro_miktar * euro_tl
toplam_fon = val_yas + val_yay + val_ylb
net_servet = toplam_altin + toplam_fon + toplam_euro

# GÖSTERGE PANELİ
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net_servet:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{toplam_altin:,.0f} TL")
c3.metric("TOPLAM FON", f"{toplam_fon:,.0f} TL")

st.markdown("---")

# FON DETAYLARI
st.subheader("📊 Fon Dağılımı")
f1, f2, f3 = st.columns(3)
f1.metric("YAS (Koç)", f"{val_yas:,.0f} TL", f"{yas_fiyat_input:.4f} x {yas_adet}")
f2.metric("YAY (Teknoloji)", f"{val_yay:,.0f} TL", f"{yay_fiyat_input:.4f} x {yay_adet}")
f3.metric("YLB (Nakit)", f"{val_ylb:,.0f} TL", f"{ylb_fiyat_input:.4f} x {ylb_adet}")

st.markdown("---")

# ARBİTRAJ VE ÇOCUK
l_col, r_col = st.columns([2, 1])
with l_col:
    st.subheader("💳 Arbitraj & Güvenlik")
    # Hata korumalı bar çubuğu
    if borc > 0:
        oran = (val_ylb / borc) * 100
    elif val_ylb > 0:
        oran = 100
    else:
        oran = 0
    
    # NaN kontrolü
    if math.isnan(oran) or math.isinf(oran): oran = 0
    bar_val = int(oran) if int(oran) < 100 else 100
    
    st.progress(bar_val)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Borç", f"{borc:,.0f} TL")
    k2.metric("Nakit (YLB)", f"{val_ylb:,.0f} TL")
    fark = val_ylb - borc
    durum = "GÜVENLİ" if fark >= 0 else "RİSKLİ"
    renk = "normal" if fark >= 0 else "inverse"
    k3.metric("Durum", durum, f"{fark:,.0f} TL", delta_color=renk)

with r_col:
    st.subheader("👶 Çocuk Portföyü")
    c_froto = st.number_input("FROTO", value=2)
    c_thyao = st.number_input("THYAO", value=5)
    c_tuprs = st.number_input("TUPRS", value=30)
    
    cocuk_toplam = (c_froto * p_froto) + (c_thyao * p_thyao) + (c_tuprs * p_tuprs)
    st.metric("Toplam Değer", f"{cocuk_toplam:,.0f} TL")

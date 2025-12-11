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
    st.session_state['yas_src'] = "-"
    
    # YAY
    st.session_state['yay_val'] = 1283.30
    st.session_state['yay_cost'] = 1283.30
    st.session_state['yay_src'] = "-"
    
    # YLB
    st.session_state['ylb_val'] = 1.40
    st.session_state['ylb_cost'] = 1.40
    st.session_state['ylb_src'] = "-"
    
    st.session_state['last_update'] = "Henüz Yapılmadı"
    st.session_state['init'] = True

# ---------------------------------------------------------
# 2. VERİ ÇEKME MOTORU (ALTINKAYNAK EKLENDİ)
# ---------------------------------------------------------
def fetch_fund_data(fund_code):
    # 1. TEFAS
    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
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

@st.cache_data(ttl=600)
def get_altinkaynak_data():
    """Altınkaynak.com sitesinden Güncel Altın ve Döviz verilerini çeker"""
    data = {"ceyrek": 0, "bilezik": 0, "tam": 0, "has": 0, "dolar": 0, "euro": 0, "src": "Manuel"}
    
    try:
        url = "https://www.altinkaynak.com/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            text = BeautifulSoup(r.content, "html.parser").get_text(" ", strip=True)
            
            # Regex ile veri avlama (Altınkaynak yapısına uygun)
            # Genelde: "Çeyrek Altın 9.200 9.600" gibi yazar. İkinci (büyük) rakamı Satış olarak alıyoruz.
            
            def get_price(label):
                # Etiketten sonra gelen sayıları bul (örn: 5.800,50)
                matches = re.findall(rf'{label}.*?(\d{{1,3}}(?:[.,]\d{{3}})*[.,]\d{{2}})', text, re.IGNORECASE)
                if matches:
                    # Bulunanların içinden en büyük olanı (Satış Fiyatı) al
                    values = []
                    for m in matches[:2]: # İlk 2 eşleşmeye bak (Alış/Satış)
                        clean = m.replace('.', '').replace(',', '.')
                        values.append(float(clean))
                    return max(values) if values else 0
                return 0

            data["has"] = get_price("Has Altın")
            data["ceyrek"] = get_price("Çeyrek Altın")
            data["bilezik"] = get_price("22 Ayar") # 22 Ayar Bilezik/Gram
            data["tam"] = get_price("Ata Cumhuriyet") # Veya Tam Altın
            
            # Dövizleri de buradan çekebiliriz (Yedek)
            data["dolar"] = get_price("Dolar")
            data["euro"] = get_price("Euro")
            
            if data["has"] > 0:
                data["src"] = "Altınkaynak"
                
    except Exception as e:
        print(f"Hata: {e}")
        pass
        
    return data

# ---------------------------------------------------------
# 3. GÜNCELLEME BUTONU
# ---------------------------------------------------------
st.sidebar.header("🕹️ Komuta Merkezi")
if st.sidebar.button("🔄 Piyasayı GÜNCELLE"):
    with st.spinner('Altınkaynak, TEFAS ve Fintables taranıyor...'):
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
    in_yas_maliyet = st.number_input("YAS Ort. Maliyet", value=st.session_state['yas_cost'], format="%.4f")

with st.sidebar.expander("YAY (Teknoloji)", expanded=True):
    in_yay_fiyat = st.number_input("YAY Fiyat", value=st.session_state['yay_val'], format="%.4f")
    in_yay_adet = st.number_input("YAY Adet", value=7)
    in_yay_maliyet = st.number_input("YAY Ort. Maliyet", value=st.session_state['yay_cost'], format="%.4f")

with st.sidebar.expander("YLB (Nakit)", expanded=False):
    in_ylb_fiyat = st.number_input("YLB Fiyat", value=st.session_state['ylb_val'], format="%.4f")
    in_ylb_adet = st.number_input("YLB Adet", value=39400)
    in_ylb_maliyet = st.number_input("YLB Ort. Maliyet", value=st.session_state['ylb_cost'], format="%.4f")

# --- ALTINLAR (ALTINKAYNAK) ---
market_data = get_altinkaynak_data() # Verileri çek

st.sidebar.markdown("---")
st.sidebar.subheader("🥇 Altınlar")

banka_gr = st.sidebar.number_input("Banka Altın (Gr)", value=130)

# Otomatik gelirse kullan, gelmezse 0 veya eski değer
def_c = market_data["ceyrek"] if market_data["ceyrek"] > 0 else 9600.0
def_b = market_data["bilezik"] if market_data["bilezik"] > 0 else 5600.0
def_t = market_data["tam"] if market_data["tam"] > 0 else 38400.0
def_h = market_data["has"] if market_data["has"] > 0 else 3100.0

in_c_fiyat = st.sidebar.number_input("Çeyrek Fiyat", value=def_c)
in_c_adet = st.sidebar.number_input("Çeyrek Adet", value=53)

in_b_fiyat = st.sidebar.number_input("Bilezik Gr Fiyatı", value=def_b)
in_b_gr = st.sidebar.number_input("Bilezik Gram", value=10)

in_t_fiyat = st.sidebar.number_input("Tam Fiyat", value=def_t)
in_t_adet = st.sidebar.number_input("Tam Adet", value=0)

# --- DÖVİZ ---
# Altınkaynak'tan gelen dolar/euro varsa onu kullan, yoksa Yahoo
st.sidebar.markdown("---")
st.sidebar.subheader("💶 Döviz & Borç")

# Dolar/Euro kontrolü
val_dolar = market_data["dolar"] if market_data["dolar"] > 0 else 35.0
val_euro = market_data["euro"] if market_data["euro"] > 0 else 49.97
src_doviz = "Altınkaynak" if market_data["dolar"] > 0 else "Manuel/Yahoo"

in_eur_kur = st.sidebar.number_input("Euro Kuru (Canlı)", value=val_euro)
in_eur_adet = st.sidebar.number_input("Euro Miktarı", value=10410)
in_eur_maliyet = st.sidebar.number_input("Euro Ort. Maliyet", value=in_eur_kur) # Varsayılan maliyet = anlık kur

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

# Altın Hesabı (Has Fiyatını Kullan)
# Banka altını için Has fiyatı kullanılır
v_banka = banka_gr * def_h
v_ziynet = (in_c_adet * in_c_fiyat) + (in_t_adet * in_t_fiyat)
v_bilezik = in_b_gr * in_b_fiyat
t_gold = v_banka + v_ziynet + v_bilezik

net = t_fon + t_gold + val_eur

# ---------------------------------------------------------
# 6. EKRAN GÖSTERİMİ
# ---------------------------------------------------------
st.title("🚀 Finansal Özgürlük Kokpiti")

# CANLI PİYASA
st.subheader("🌍 Canlı Piyasa ve Kaynaklar")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Euro/TL", f"{in_eur_kur:.2f}", f"Kaynak: {src_doviz}")
k2.metric("Dolar/TL", f"{val_dolar:.2f}", f"Kaynak: {src_doviz}")
k3.metric("Has Altın (Gr)", f"{def_h:,.0f} TL", f"Kaynak: {market_data['src']}")
k4.metric("Çeyrek Altın", f"{in_c_fiyat:,.0f} TL", f"Kaynak: {market_data['src']}")
k5.metric("Bilezik (22 Ayar)", f"{in_b_fiyat:,.0f} TL", f"Kaynak: {market_data['src']}")

# FONLAR (ALT SATIR)
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

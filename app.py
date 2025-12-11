import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re  # Yazı avcısı kütüphane

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföyü", layout="wide", page_icon="🚀")
st.title("🚀 Finansal Özgürlük Kokpiti")

# --- 1. AKILLI VERİ ÇEKME (REGEX İLE) ---
@st.cache_data(ttl=900)
def get_kayseri_smart():
    url = "https://www.kaysarder.org.tr/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    prices = {"ceyrek": 0.0, "tam": 0.0, "bilezik22": 0.0, "status": False}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Sitenin tüm metnini düz yazıya çevir
            soup = BeautifulSoup(response.content, "html.parser")
            clean_text = soup.get_text(" ", strip=True) # Tüm HTML'i temizle, boşluk bırak
            
            # --- REGEX (YAZI AVRAMA) MANTIĞI ---
            # Sitede "25 ZİYNET | 9600,00 TL" yazıyor.
            # Bunu yakalayacak formül: "25 ZİYNET" + (arada ne varsa) + (Sayı)
            
            # 1. ÇEYREK (25 ZİYNET) BULMA
            # Desen: 25 ZİYNET kelimesini bul, sonrasındaki ilk parasal değeri al
            match_ceyrek = re.search(r'25\s*ZİYNET.*?(\d+[\.,]\d+)', clean_text, re.IGNORECASE)
            if match_ceyrek:
                # Bulduğu sayıyı (Örn: 9.600,00 veya 9600,00) temizle
                price_str = match_ceyrek.group(1).replace('.', '').replace(',', '.')
                prices["ceyrek"] = float(price_str)

            # 2. TAM ALTIN (100 ZİYNET veya TAM) BULMA
            match_tam = re.search(r'100\s*ZİYNET.*?(\d+[\.,]\d+)', clean_text, re.IGNORECASE)
            if match_tam:
                price_str = match_tam.group(1).replace('.', '').replace(',', '.')
                prices["tam"] = float(price_str)
            
            # 3. 22 AYAR BİLEZİK BULMA
            # Desen: "22 AYAR" kelimesinden sonraki sayıyı al
            match_bilezik = re.search(r'22\s*AYAR.*?(\d+[\.,]\d+)', clean_text, re.IGNORECASE)
            if match_bilezik:
                price_str = match_bilezik.group(1).replace('.', '').replace(',', '.')
                prices["bilezik22"] = float(price_str)

            if prices["ceyrek"] > 0:
                prices["status"] = True
                
    except Exception as e:
        print(f"Hata: {e}")
        
    return prices

# Verileri Çek
kayseri_data = get_kayseri_smart()
market_data = None # Global veriler için placeholder

# --- 2. GLOBAL VERİLER (YAS/YAY/DOLAR) ---
try:
    tickers = ["XU100.IS", "NQ=F", "GC=F", "TRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
    market_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
except:
    pass

# --- 3. PİYASA PANOSU ---
st.subheader("📊 Piyasa Durumu")
m1, m2, m3, m4 = st.columns(4)

if market_data is not None:
    try:
        # BIST
        b_now = market_data['XU100.IS']['Close'].iloc[-1]
        b_delta = ((b_now - market_data['XU100.IS']['Close'].iloc[-2])/market_data['XU100.IS']['Close'].iloc[-2])*100
        m1.metric("BIST 100", f"{b_now:,.0f}", f"%{b_delta:.2f}")
        
        # NASDAQ
        n_now = market_data['NQ=F']['Close'].iloc[-1]
        n_delta = ((n_now - market_data['NQ=F']['Close'].iloc[-2])/market_data['NQ=F']['Close'].iloc[-2])*100
        m2.metric("NASDAQ", f"{n_now:,.0f}", f"%{n_delta:.2f}")
        
        # DOLAR
        d_now = market_data['TRY=X']['Close'].iloc[-1]
        m3.metric("Dolar/TL", f"{d_now:.2f} TL")
        
        # ONS
        o_now = market_data['GC=F']['Close'].iloc[-1]
        m4.metric("Ons Altın", f"${o_now:,.0f}")
        
        # Global Gram TL (Has Altın) Hesabı
        has_altin_tl = (o_now * d_now) / 31.10
        euro_tl = market_data['TRY=X']['Close'].iloc[-1] * 1.05 # Yaklaşık
    except:
        has_altin_tl = 3000
        euro_tl = 37
else:
    m1.error("Veri Yok")
    has_altin_tl = 3000
    euro_tl = 37

st.markdown("---")

# --- 4. SOL MENÜ VE HESAPLAMALAR ---
st.sidebar.header("💰 Varlık Girişleri")

# ALTIN BÖLÜMÜ
st.sidebar.subheader("🥇 Altın Varlıkları")
banka_gram = st.sidebar.number_input("Banka Altın (24 Ayar Gram)", value=130, step=5)

st.sidebar.markdown("---")
# KAYSERİ FİYATLARI
kaynak_text = "Kayseri (OTO)" if kayseri_data["status"] else "Manuel Giriş"
st.sidebar.caption(f"👇 Ziynet Fiyatları ({kaynak_text})")

# Eğer otomatik çekildiyse o fiyatı getir, yoksa varsayılanı kullan
val_ceyrek_default = kayseri_data["ceyrek"] if kayseri_data["ceyrek"] > 0 else 9600.0
val_tam_default = kayseri_data["tam"] if kayseri_data["tam"] > 0 else 38400.0
val_bilezik_default = kayseri_data["bilezik22"] if kayseri_data["bilezik22"] > 0 else 5600.0

ceyrek_adet = st.sidebar.number_input("Çeyrek Altın (Adet)", value=53)
guncel_ceyrek_fiyat = st.sidebar.number_input("Çeyrek Fiyatı (TL)", value=val_ceyrek_default, step=50.0)

tam_adet = st.sidebar.number_input("Tam Altın (Adet)", value=0)
guncel_tam_fiyat = st.sidebar.number_input("Tam Fiyatı (TL)", value=val_tam_default, step=100.0)

st.sidebar.markdown("---")
bilezik_gram = st.sidebar.number_input("Bilezik (22 Ayar Gram)", value=0)
guncel_22ayar_gram = st.sidebar.number_input("22 Ayar Gram Fiyatı (TL)", value=val_bilezik_default, step=10.0)

# DİĞER VARLIKLAR
st.sidebar.subheader("💶 Döviz & Fon")
euro_amount = st.sidebar.number_input("Euro Varlığı (€)", value=10410, step=100)
total_funds = st.sidebar.number_input("Toplam Fon Değeri", value=75000, step=1000)
ylb_cash = st.sidebar.number_input("Sadece YLB (Nakit)", value=55000, step=1000)
cc_debt = st.sidebar.number_input("Kredi Kartı Borcu", value=34321, step=500)

# --- SONUÇ HESAPLAMA ---
val_banka = banka_gram * has_altin_tl
val_ziynet = (ceyrek_adet * guncel_ceyrek_fiyat) + (tam_adet * guncel_tam_fiyat)
val_bilezik = bilezik_gram * guncel_22ayar_gram

total_gold = val_banka + val_ziynet + val_bilezik
total_euro = euro_amount * euro_tl
net_worth = total_gold + total_euro + total_funds

# --- EKRAN GÖSTERİMİ ---
c1, c2, c3 = st.columns(3)
c1.metric("TOPLAM SERVET", f"{net_worth:,.0f} TL")
c2.metric("TOPLAM ALTIN", f"{total_gold:,.0f} TL")
c3.metric("EURO VARLIĞI", f"{total_euro:,.0f} TL")

st.markdown("---")

col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("💳 Arbitraj Durumu")
    margin = ylb_cash - cc_debt
    per = (ylb_cash / cc_debt) * 100 if cc_debt > 0 else 100
    prog = int(per) if int(per) < 100 else 100
    st.progress(prog)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Borç", f"{cc_debt:,.0f} TL")
    k2.metric("Nakit", f"{ylb_cash:,.0f} TL")
    if margin < 0:
        k3.metric("Durum", "RİSKLİ", f"{margin:,.0f} TL", delta_color="inverse")
    else:
        k3.metric("Durum", "GÜVENLİ", f"{margin:,.0f} TL")

with col_right:
    st.subheader("👶 Junior Hisse")
    f_lot = st.number_input("FROTO Lot", value=2)
    t_lot = st.number_input("THYAO Lot", value=5)
    p_lot = st.number_input("TUPRS Lot", value=30)
    
    if market_data is not None:
        try:
            val_f = market_data['FROTO.IS']['Close'].iloc[-1]
            val_t = market_data['THYAO.IS']['Close'].iloc[-1]
            val_p = market_data['TUPRS.IS']['Close'].iloc[-1]
            jr_val = (f_lot * val_f) + (t_lot * val_t) + (p_lot * val_p)
        except: jr_val = 0
    else: jr_val = 0
    
    st.metric("Çocuk Portföyü", f"{jr_val:,.0f} TL")

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföy Yönetimi", layout="wide")

st.title("🚀 Finansal Özgürlük Kokpiti")
st.markdown("---")

# --- 1. KAYSERİ'DEN VERİ ÇEKME (ÇEYREK ve TAM İÇİN) ---
@st.cache_data(ttl=900) # 15 dakikada bir yenile
def get_kayseri_ziynet():
    url = "https://www.kaysarder.org.tr/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    prices = {
        "ceyrek": 0.0,
        "tam": 0.0,
        "bilezik22": 0.0,
        "status": False,
        "source": "Manuel"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Tüm tablo satırlarını bul
            rows = soup.find_all("tr")
            
            for row in rows:
                text = row.get_text().upper().strip()
                cols = row.find_all("td")
                
                # Fiyat genelde son sütunlarda olur (Alış - Satış)
                # Satış fiyatını (daha yüksek olanı) almaya çalışacağız
                if len(cols) >= 2:
                    try:
                        # Fiyat temizleme fonksiyonu (Örn: "5.100,50" -> 5100.50)
                        price_text = cols[-1].get_text().replace(".", "").replace(",", ".").replace("₺", "").strip()
                        price = float(price_text)
                        
                        # "25" kodu genellikle Çeyrek Altın (Ziynet) için kullanılır
                        if "25" in text and "ZİYNET" in text: 
                            prices["ceyrek"] = price
                        elif "25" in text: # Sadece 25 yazıyorsa da al (Yedek)
                             if prices["ceyrek"] == 0: prices["ceyrek"] = price

                        # "100" veya "TAM" kodu Tam Altın için
                        if "100" in text or "TAM" in text:
                            # 2.5 luk (Gremse) ile karışmasın diye kontrol
                            if "2.5" not in text: 
                                prices["tam"] = price
                        
                        # 22 Ayar Bilezik
                        if "22" in text and "BİLEZİK" in text:
                            prices["bilezik22"] = price
                            
                    except:
                        continue
            
            if prices["ceyrek"] > 0:
                prices["status"] = True
                prices["source"] = "Kayseri Sarraf (Oto)"
                
    except Exception as e:
        print(f"Hata: {e}")
        
    return prices

# Kayseri verisini çek
kayseri_data = get_kayseri_ziynet()

# --- 2. GLOBAL VERİ ÇEKME (GRAM ALTIN & EURO İÇİN) ---
@st.cache_data(ttl=60) # 1 dakikada bir yenile
def get_global_data():
    try:
        tickers = ["GC=F", "EURTRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS", "TRY=X"]
        data = yf.download(tickers, period="1d", group_by='ticker')
        
        vals = {}
        for t in tickers:
            try:
                vals[t] = float(data[t]['Close'].iloc[-1])
            except:
                vals[t] = 0.0
        return vals
    except:
        return None

global_vals = get_global_data()

# Varsayılan Global Değerler
ons_price = 2600.0
usd_try = 35.0
euro_price = 37.0
if global_vals:
    ons_price = global_vals.get("GC=F", 2600.0)
    usd_try = global_vals.get("TRY=X", 35.0)
    euro_price = global_vals.get("EURTRY=X", 37.0)

# Gram Altın Hesabı (Global ONS üzerinden)
# Formül: (Ons * Dolar) / 31.10
global_gram_tl = (ons_price * usd_try) / 31.10

# --- YAN MENÜ (GİRİŞLER) ---
st.sidebar.header("💰 Varlık Girişleri")

# 1. ALTIN (ZİYNETLER KAYSERİ'DEN, GRAM GLOBALDEN)
st.sidebar.subheader("🥇 Altın Varlıkları")

# Banka altını (Global Gram Fiyatından)
banka_gram = st.sidebar.number_input("Banka Altın (24 Ayar Gram)", value=130, step=5)

st.sidebar.markdown("---")
st.sidebar.caption(f"👇 Ziynet Adetleri (Kaynak: {kayseri_data['source']})")

# Kayseri'den çekilen fiyatları varsayılan yap, çekemezse manuel bırak
def_ceyrek = kayseri_data["ceyrek"] if kayseri_data["ceyrek"] > 0 else 5100.0
def_tam = kayseri_data["tam"] if kayseri_data["tam"] > 0 else 20400.0
def_bilezik = kayseri_data["bilezik22"] if kayseri_data["bilezik22"] > 0 else 2900.0

ceyrek_adet = st.sidebar.number_input("Çeyrek Altın (Adet)", value=0, step=1)
guncel_ceyrek_fiyat = st.sidebar.number_input("Çeyrek Fiyatı (TL)", value=def_ceyrek, step=50.0)

tam_adet = st.sidebar.number_input("Tam Altın (Adet)", value=0, step=1)
guncel_tam_fiyat = st.sidebar.number_input("Tam Fiyatı (TL)", value=def_tam, step=100.0)

st.sidebar.markdown("---")
bilezik_gram = st.sidebar.number_input("Bilezik (22 Ayar Gram)", value=0, step=5)
guncel_22ayar_gram = st.sidebar.number_input("22 Ayar Gram Fiyatı (TL)", value=def_bilezik, step=10.0)

# 2. DÖVİZ (GLOBAL KAYNAK)
st.sidebar.subheader("💶 Döviz")
st.sidebar.caption(f"Euro Kuru: {euro_price:.2f} TL (Global)")
euro_amount = st.sidebar.number_input("Euro Varlığı (€)", value=10000, step=100)

# 3. FONLAR
st.sidebar.subheader("📈 Fonlar")
total_funds = st.sidebar.number_input("Toplam Fon Değeri", value=75000, step=1000)
ylb_cash = st.sidebar.number_input("Sadece YLB (Nakit)", value=55000, step=1000)

# 4. BORÇ
st.sidebar.subheader("💳 Borçlar")
cc_debt = st.sidebar.number_input("Kredi Kartı Borcu", value=34321, step=500)


# --- HESAPLAMALAR ---
# 1. Banka Altını (Global Gram Fiyatı ile)
val_banka = banka_gram * global_gram_tl

# 2. Ziynetler (Kayseri Fiyatı ile)
val_ziynet = (ceyrek_adet * guncel_ceyrek_fiyat) + (tam_adet * guncel_tam_fiyat)

# 3. Bilezik (Kayseri 22 Ayar Fiyatı ile)
val_bilezik = bilezik_gram * guncel_22ayar_gram

total_gold_value = val_banka + val_ziynet + val_bilezik
total_euro_value = euro_amount * euro_price
net_worth = total_gold_value + total_euro_value + total_funds

# --- GÖSTERGE PANELİ ---
col1, col2, col3 = st.columns(3)
col1.metric("Toplam Servet", f"{net_worth:,.0f} TL")
col2.metric("Toplam Altın", f"{total_gold_value:,.0f} TL", f"Gram (Has): {global_gram_tl:.0f} TL")
col3.metric("Euro Varlığı", f"{total_euro_value:,.0f} TL", f"Kur: {euro_price:.2f} TL")

st.markdown("---")

c1, c2 = st.columns([2, 1])
with c1:
    st.subheader("💳 Arbitraj Durumu")
    margin = ylb_cash - cc_debt
    per = (ylb_cash / cc_debt) * 100 if cc_debt > 0 else 100
    prog = int(per) if int(per) < 100 else 100
    st.progress(prog)
    k1, k2, k3 = st.columns(3)
    k1.metric("Borç", f"{cc_debt:,.0f} TL")
    k2.metric("Nakit", f"{ylb_cash:,.0f} TL")
    k3.metric("Güvenlik", f"{margin:,.0f} TL")

with c2:
    st.subheader("👶 Junior Portföy")
    f_lot = st.number_input("FROTO Lot", value=2)
    t_lot = st.number_input("THYAO Lot", value=5)
    p_lot = st.number_input("TUPRS Lot", value=30)
    
    if global_vals:
        jr_val = (f_lot * global_vals.get("FROTO.IS",0)) + \
                 (t_lot * global_vals.get("THYAO.IS",0)) + \
                 (p_lot * global_vals.get("TUPRS.IS",0))
    else:
        jr_val = 0
        
    st.metric("Çocuk Birikimi", f"{jr_val:,.0f} TL")

st.markdown("---")
st.subheader("🎯 50 Yaş Hedefi")
prog_target = net_worth / 15000000.0
if prog_target > 1.0: prog_target = 1.0
st.progress(prog_target)
st.write(f"Hedef: %{prog_target*100:.2f}")

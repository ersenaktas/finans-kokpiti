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

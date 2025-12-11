import streamlit as st
import yfinance as yf
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföy Yönetimi", layout="wide")

st.title("🚀 Finansal Özgürlük Kokpiti")
st.markdown("---")

# --- YAN MENÜ (MANUEL GİRİŞLER) ---
st.sidebar.header("💰 Varlık Girişleri")

# 1. Sabit Varlıklar
gold_gram = st.sidebar.number_input("Fiziki + Banka Altın (Gram)", value=730, step=10) # Örn: 130 + 600
euro_amount = st.sidebar.number_input("Euro Varlığı (€)", value=10000, step=100)

# 2. Fon Durumu (TEFAS verisi manuel girilir çünkü API değişkendir)
total_funds = st.sidebar.number_input("Toplam Fon Değeri (YAS+YAY+YLB)", value=75000, step=1000)
ylb_cash = st.sidebar.number_input("Sadece YLB (Nakit) Miktarı", value=55000, step=1000)

# 3. Borç Durumu
cc_debt = st.sidebar.number_input("Güncel Kredi Kartı Borcu", value=34321, step=500)

# --- CANLI VERİ ÇEKME (YAHOO FINANCE) ---
@st.cache_data
def get_market_data():
    tickers = ["GC=F", "EURTRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
    data = yf.download(tickers, period="1d")['Close'].iloc[-1]
    return data

try:
    market_data = get_market_data()
    # Altın Ons Fiyatından Gram TL Tahmini (Yaklaşık)
    ons_price = market_data['GC=F']
    usd_try = yf.download("TRY=X", period="1d")['Close'].iloc[-1] # Dolar Kuru
    # Ons -> Gram TL Formülü: (Ons * Dolar) / 31.1
    gold_price_try = (ons_price * usd_try) / 31.10 
    
    euro_price = market_data['EURTRY=X']
    
except:
    st.error("Piyasa verileri çekilemedi. İnternet bağlantısını kontrol edin.")
    gold_price_try = 3000 # Fallback
    euro_price = 35 # Fallback

# --- HESAPLAMALAR ---
total_gold_value = gold_gram * gold_price_try
total_euro_value = euro_amount * euro_price
net_worth = total_gold_value + total_euro_value + total_funds

# --- GÖSTERGE PANELİ (DASHBOARD) ---

# 1. SATIR: ANA VARLIKLAR
col1, col2, col3 = st.columns(3)
col1.metric("Toplam Servet", f"{net_worth:,.0f} TL", delta_color="normal")
col2.metric("Altın Değeri", f"{total_gold_value:,.0f} TL", f"{gold_gram} Gram")
col3.metric("Euro Değeri", f"{total_euro_value:,.0f} TL", f"Kur: {euro_price:.2f}")

st.markdown("---")

# 2. SATIR: ARBİTRAJ VE JUNIOR
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("💳 Arbitraj Güvenlik Radarı")
    st.info("Kredi Kartı Borcu vs. YLB Nakit Gücü")
    
    # Güvenlik Marjı Hesabı
    margin = ylb_cash - cc_debt
    percent_covered = (ylb_cash / cc_debt) * 100 if cc_debt > 0 else 100
    
    st.progress(min(int(percent_covered), 100))
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Kredi Kartı Borcu", f"{cc_debt:,.0f} TL", delta_color="inverse")
    k2.metric("YLB (Nakit)", f"{ylb_cash:,.0f} TL")
    k3.metric("Güvenlik Marjı", f"{margin:,.0f} TL", delta=f"%{percent_covered:.1f} Karşılama")

    if margin < 0:
        st.error("⚠️ DİKKAT! Nakit, borcu karşılamıyor. Acil YLB ekle!")
    else:
        st.success("✅ GÜVENLİ. Borç yönetilebilir seviyede.")

with c2:
    st.subheader("👶 Junior Portföy (Tahmini)")
    # Örnek Lot Sayıları (Her ay 5k alım varsayımıyla)
    froto_lot = st.number_input("FROTO Lot", value=2)
    thyao_lot = st.number_input("THYAO Lot", value=5)
    tuprs_lot = st.number_input("TUPRS Lot", value=30)
    
    jr_val = (froto_lot * market_data['FROTO.IS']) + \
             (thyao_lot * market_data['THYAO.IS']) + \
             (tuprs_lot * market_data['TUPRS.IS'])
             
    st.metric("Çocuğun Birikimi", f"{jr_val:,.2f} TL")
    st.write(f"FROTO: {market_data['FROTO.IS']:.2f} TL")
    st.write(f"THYAO: {market_data['THYAO.IS']:.2f} TL")

# --- 3. SATIR: HEDEF TAKİBİ ---
st.markdown("---")
st.subheader("🎯 50 Yaş (Erken Emeklilik) Hedefi")

target_wealth = 15000000 # 15 Milyon TL Hedef
progress = (net_worth / target_wealth) 
st.progress(progress)
st.write(f"Hedefe Ulaşma Oranı: **%{progress*100:.2f}**")
st.caption(f"Hedef: {target_wealth:,.0f} TL | Kalan: {(target_wealth - net_worth):,.0f} TL")

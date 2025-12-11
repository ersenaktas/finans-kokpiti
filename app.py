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

# 2. Fon Durumu (TEFAS verisi manuel girilir)
total_funds = st.sidebar.number_input("Toplam Fon Değeri (YAS+YAY+YLB)", value=75000, step=1000)
ylb_cash = st.sidebar.number_input("Sadece YLB (Nakit) Miktarı", value=55000, step=1000)

# 3. Borç Durumu
cc_debt = st.sidebar.number_input("Güncel Kredi Kartı Borcu", value=34321, step=500)

# --- CANLI VERİ ÇEKME (YAHOO FINANCE) ---
@st.cache_data
def get_market_data():
    try:
        # Ticker listesi
        tickers = ["GC=F", "EURTRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
        # Group_by='ticker' ile veriyi garanti altına alıyoruz
        data = yf.download(tickers, period="1d", group_by='ticker')
        
        # Son kapanış fiyatlarını alalım
        market_values = {}
        for t in tickers:
            # Her hisse için son değeri float (sayı) olarak çek
            try:
                price = data[t]['Close'].iloc[-1]
                market_values[t] = float(price)
            except:
                market_values[t] = 0.0 # Veri gelmezse 0 kabul et
                
        return market_values
    except Exception as e:
        return None

# Piyasa verilerini çek
market_vals = get_market_data()

# Dolar kurunu ayrıca çekelim (Ons hesaplamak için)
try:
    usd_data = yf.download("TRY=X", period="1d")
    usd_try = float(usd_data['Close'].iloc[-1])
except:
    usd_try = 35.0 # Hata olursa varsayılan

# Veriler geldiyse ata, gelmediyse varsayılan kullan
if market_vals:
    ons_price = market_vals.get("GC=F", 2600.0)
    euro_price = market_vals.get("EURTRY=X", 37.0)
    froto_price = market_vals.get("FROTO.IS", 0)
    thyao_price = market_vals.get("THYAO.IS", 0)
    tuprs_price = market_vals.get("TUPRS.IS", 0)
    
    # Ons -> Gram TL Formülü: (Ons * Dolar) / 31.1
    gold_price_try = (ons_price * usd_try) / 31.10 
else:
    st.error("Veriler çekilemedi, manuel mod devrede.")
    gold_price_try = 3000
    euro_price = 37.0
    froto_price = 0
    thyao_price = 0
    tuprs_price = 0

# --- HESAPLAMALAR ---
# Hepsinin sayı (float) olduğundan eminiz artık
total_gold_value = float(gold_gram) * float(gold_price_try)
total_euro_value = float(euro_amount) * float(euro_price)
net_worth = total_gold_value + total_euro_value + float(total_funds)

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
    
    # Bar çubuğu hatasını önlemek için 0-100 arası sınırla
    progress_val = int(percent_covered)
    if progress_val > 100: progress_val = 100
    if progress_val < 0: progress_val = 0
    
    st.progress(progress_val)
    
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
    # Örnek Lot Sayıları
    froto_lot = st.number_input("FROTO Lot", value=2)
    thyao_lot = st.number_input("THYAO Lot", value=5)
    tuprs_lot = st.number_input("TUPRS Lot", value=30)
    
    jr_val = (froto_lot * froto_price) + \
             (thyao_lot * thyao_price) + \
             (tuprs_lot * tuprs_price)
             
    st.metric("Çocuğun Birikimi", f"{jr_val:,.2f} TL")
    st.caption(f"FROTO: {froto_price:.1f} | THY: {thyao_price:.1f}")

# --- 3. SATIR: HEDEF TAKİBİ ---
st.markdown("---")
st.subheader("🎯 50 Yaş (Erken Emeklilik) Hedefi")

target_wealth = 15000000.0 # 15 Milyon TL Hedef
progress = (net_worth / target_wealth) 
if progress > 1.0: progress = 1.0

st.progress(progress)
st.write(f"Hedefe Ulaşma Oranı: **%{progress*100:.2f}**")
st.caption(f"Hedef: {target_wealth:,.0f} TL | Kalan: {(target_wealth - net_worth):,.0f} TL")

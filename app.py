import streamlit as st
import yfinance as yf
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis Portföy Yönetimi", layout="wide")

st.title("🚀 Finansal Özgürlük Kokpiti")
st.markdown("---")

# --- YAN MENÜ (MANUEL GİRİŞLER) ---
st.sidebar.header("💰 Varlık Girişleri")

# 1. ALTIN DETAYLARI (YENİ EKLENEN KISIM)
st.sidebar.subheader("🥇 Altın Varlıkları")
banka_gram = st.sidebar.number_input("Banka Altın (24 Ayar Gram)", value=130, step=5)
ceyrek_adet = st.sidebar.number_input("Çeyrek Altın (Adet)", value=0, step=1)
tam_adet = st.sidebar.number_input("Tam Altın (Adet)", value=0, step=1)
bilezik_gram = st.sidebar.number_input("Bilezik (22 Ayar Gram)", value=0, step=5)
# Diğer fiziki gram altınlar (külçe vs)
diger_gram = st.sidebar.number_input("Diğer Fiziki Gram (24 Ayar)", value=0, step=10)

# 2. DÖVİZ
st.sidebar.subheader("💶 Döviz")
euro_amount = st.sidebar.number_input("Euro Varlığı (€)", value=10000, step=100)

# 3. FON DURUMU
st.sidebar.subheader("📈 Fonlar")
total_funds = st.sidebar.number_input("Toplam Fon Değeri (YAS+YAY+YLB)", value=75000, step=1000)
ylb_cash = st.sidebar.number_input("Sadece YLB (Nakit) Miktarı", value=55000, step=1000)

# 4. BORÇ
st.sidebar.subheader("💳 Borçlar")
cc_debt = st.sidebar.number_input("Güncel Kredi Kartı Borcu", value=34321, step=500)

# --- CANLI VERİ ÇEKME ---
@st.cache_data
def get_market_data():
    try:
        tickers = ["GC=F", "EURTRY=X", "FROTO.IS", "THYAO.IS", "TUPRS.IS"]
        data = yf.download(tickers, period="1d", group_by='ticker')
        
        market_values = {}
        for t in tickers:
            try:
                price = data[t]['Close'].iloc[-1]
                market_values[t] = float(price)
            except:
                market_values[t] = 0.0
        return market_values
    except:
        return None

market_vals = get_market_data()

try:
    usd_data = yf.download("TRY=X", period="1d")
    usd_try = float(usd_data['Close'].iloc[-1])
except:
    usd_try = 35.0 

if market_vals:
    ons_price = market_vals.get("GC=F", 2600.0)
    euro_price = market_vals.get("EURTRY=X", 37.0)
    froto_price = market_vals.get("FROTO.IS", 0)
    thyao_price = market_vals.get("THYAO.IS", 0)
    tuprs_price = market_vals.get("TUPRS.IS", 0)
    # 24 Ayar Gram Altın Fiyatı
    gold_price_24k = (ons_price * usd_try) / 31.10 
else:
    st.error("Veriler çekilemedi, manuel mod.")
    gold_price_24k = 3000
    euro_price = 37.0
    froto_price = 0
    thyao_price = 0
    tuprs_price = 0

# --- HAS ALTIN (SAF) DÖNÜŞÜM HESAPLAMALARI ---
# Çeyrek (22k) -> Saf (24k) katsayısı: 1.75g * 0.916 = ~1.61g
# Tam (22k) -> Saf (24k) katsayısı: 7.00g * 0.916 = ~6.42g
# Bilezik (22k) -> Saf (24k) katsayısı: Gram * 0.916

saf_gram_ceyrek = ceyrek_adet * 1.61
saf_gram_tam = tam_adet * 6.42
saf_gram_bilezik = bilezik_gram * 0.916
# Banka ve diğerleri zaten 24 ayar kabul edilir
total_saf_gold_gram = banka_gram + diger_gram + saf_gram_ceyrek + saf_gram_tam + saf_gram_bilezik

total_gold_value = total_saf_gold_gram * gold_price_24k
total_euro_value = float(euro_amount) * float(euro_price)
net_worth = total_gold_value + total_euro_value + float(total_funds)

# --- GÖSTERGE PANELİ ---

# 1. SATIR
col1, col2, col3 = st.columns(3)
col1.metric("Toplam Servet", f"{net_worth:,.0f} TL")
col2.metric("Toplam Altın Değeri", f"{total_gold_value:,.0f} TL", f"{total_saf_gold_gram:.1f} Gram (Saf)")
col3.metric("Euro Değeri", f"{total_euro_value:,.0f} TL", f"Kur: {euro_price:.2f}")

st.markdown("---")

# 2. SATIR
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("💳 Arbitraj Durumu")
    margin = ylb_cash - cc_debt
    percent = (ylb_cash / cc_debt) * 100 if cc_debt > 0 else 100
    prog = int(percent) if int(percent) < 100 else 100
    if prog < 0: prog = 0
    
    st.progress(prog)
    k1, k2, k3 = st.columns(3)
    k1.metric("Kart Borcu", f"{cc_debt:,.0f} TL")
    k2.metric("Nakit (YLB)", f"{ylb_cash:,.0f} TL")
    k3.metric("Fark", f"{margin:,.0f} TL")
    
    if margin < 0: st.error("⚠️ Nakit yetersiz!")
    else: st.success("✅ Güvendesiniz")

with c2:
    st.subheader("👶 Junior Portföy")
    f_lot = st.number_input("FROTO", value=2)
    t_lot = st.number_input("THYAO", value=5)
    p_lot = st.number_input("TUPRS", value=30)
    
    jr_val = (f_lot*froto_price) + (t_lot*thyao_price) + (p_lot*tuprs_price)
    st.metric("Çocuk Birikimi", f"{jr_val:,.0f} TL")

st.markdown("---")
st.subheader("🎯 50 Yaş Hedefi")
target = 15000000.0
prog_target = net_worth / target
if prog_target > 1.0: prog_target = 1.0
st.progress(prog_target)
st.write(f"Hedefe Ulaşma: **%{prog_target*100:.2f}**")

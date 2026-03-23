import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Kripto Gerçekçi Backtest",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e2433;
        border: 1px solid #2d3548;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-label { font-size: 12px; color: #8b95a8; margin-bottom: 4px; }
    .metric-value { font-size: 24px; font-weight: 700; }
    .metric-pos { color: #22c55e; }
    .metric-neg { color: #ef4444; }
    .metric-neu { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# ─── KRİPTO LİSTELERİ ─────────────────────────────────────────────────────────
# ─── KRİPTO LİSTELERİ ─────────────────────────────────────────────────────────
TOP_KRIPTO = {
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
    "ADA-USD", "AVAX-USD", "DOT-USD", "MATIC-USD", "LINK-USD",
    "LTC-USD", "ATOM-USD", "UNI-USD", "NEAR-USD", "APT-USD",
    "OP-USD",  "ARB-USD",  "INJ-USD", "SUI-USD",  "TIA-USD",
}

def usdt_goster(sembol):
    """BTC-USD → BTCUSDT görüntüleme formatı"""
    return sembol.replace("-USD", "USDT")

KRIPTOLAR = [
    # ── Layer 1 / Büyük Cap ──────────────────────────────────────────────────
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
    "ADA-USD", "AVAX-USD", "DOT-USD", "TRX-USD", "TON-USD",
    "MATIC-USD", "LTC-USD", "ATOM-USD", "NEAR-USD", "APT-USD",
    "ICP-USD", "HBAR-USD", "FIL-USD", "ETC-USD", "BCH-USD",
    "XLM-USD", "ALGO-USD", "VET-USD", "EGLD-USD", "FTM-USD",
    "ONE-USD", "ZIL-USD", "ICX-USD", "WAVES-USD", "KAVA-USD",
    "CELO-USD", "FLOW-USD", "MINA-USD", "KSM-USD", "CSPR-USD",
    # ── Layer 2 / Ölçeklendirme ──────────────────────────────────────────────
    "OP-USD", "ARB-USD", "IMX-USD", "LRC-USD", "METIS-USD",
    "BOBA-USD", "SYS-USD", "STRK-USD",
    # ── DeFi ─────────────────────────────────────────────────────────────────
    "LINK-USD", "UNI-USD", "AAVE-USD", "MKR-USD", "SNX-USD",
    "COMP-USD", "CRV-USD", "LDO-USD", "GRT-USD", "1INCH-USD",
    "DYDX-USD", "GMX-USD", "BAL-USD", "SUSHI-USD", "YFI-USD",
    "CAKE-USD", "RUNE-USD", "OSMO-USD", "INJ-USD", "PENDLE-USD",
    "JOE-USD", "SPELL-USD", "CVX-USD", "FXS-USD", "FRAX-USD",
    "ANKR-USD", "BAND-USD", "NMR-USD", "KNC-USD", "ZRX-USD",
    # ── Yapay Zeka / Veri ────────────────────────────────────────────────────
    "FET-USD", "OCEAN-USD", "AGIX-USD", "RLC-USD",
    "TAO-USD", "RNDR-USD", "WLD-USD", "ARKM-USD", "CTXC-USD",
    # ── Oyun / Metaverse / NFT ───────────────────────────────────────────────
    "SAND-USD", "MANA-USD", "AXS-USD", "ENJ-USD", "CHZ-USD",
    "GALA-USD", "BLUR-USD", "APE-USD", "ILV-USD", "GODS-USD",
    "SLP-USD", "ALICE-USD", "TLM-USD", "PYR-USD", "SUPER-USD",
    "HERO-USD", "SKILL-USD",
    # ── Altyapı / Depolama / Ağ ──────────────────────────────────────────────
    "AR-USD", "SC-USD", "STORJ-USD", "HNT-USD", "POWR-USD",
    "GLM-USD", "REQ-USD", "DIA-USD", "API3-USD", "TRB-USD",
    "UMA-USD", "CELR-USD", "SKL-USD",
    # ── Gizlilik ─────────────────────────────────────────────────────────────
    "XMR-USD", "ZEC-USD", "DASH-USD", "SCRT-USD", "ROSE-USD",
    # ── Borsalar / CeFi ──────────────────────────────────────────────────────
    "CRO-USD", "OKB-USD", "HT-USD", "KCS-USD",
    # ── Solana Ekosistemi ────────────────────────────────────────────────────
    "SUI-USD", "SEI-USD", "TIA-USD", "BONK-USD", "JTO-USD",
    "PYTH-USD", "WIF-USD", "BOME-USD",
    # ── RWA / Stablecoin Altyapısı ───────────────────────────────────────────
    "ONDO-USD", "TRU-USD",
    # ── Köprü / Birlikte Çalışabilirlik ──────────────────────────────────────
    "REN-USD", "STG-USD", "SYN-USD",
    # ── Meme ─────────────────────────────────────────────────────────────────
    "DOGE-USD", "SHIB-USD", "FLOKI-USD", "PEPE-USD",
    "BONK-USD", "WIF-USD", "BOME-USD", "MEME-USD",
    "TURBO-USD", "LADYS-USD", "BABYDOGE-USD",
    # ── Diğer Önemli ─────────────────────────────────────────────────────────
    "XTZ-USD", "EOS-USD", "THETA-USD", "AXL-USD", "PYTH-USD",
    "JUP-USD", "W-USD", "ALT-USD", "ETHFI-USD",
    "RENDER-USD", "ZETA-USD", "ZK-USD", "IO-USD", "ZRO-USD",
    "PORTAL-USD", "OMNI-USD", "SAGA-USD", "REZ-USD", "LISTA-USD",
    # ── Ek Coinler (200+ hedefi) ─────────────────────────────────────────────
    "JASMY-USD", "ACH-USD", "DENT-USD", "HOT-USD",
    "IOTA-USD", "QTUM-USD", "ONT-USD", "ZEN-USD", "RVN-USD",
    "BTT-USD", "WIN-USD", "SXP-USD", "ORN-USD",
    "RAD-USD", "OGN-USD", "POLS-USD", "QUICK-USD",
    "SFP-USD", "TWT-USD", "ALPHA-USD", "DODO-USD",
    "CHESS-USD", "AUCTION-USD", "FIDA-USD", "MAPS-USD",
    "OXY-USD", "MEDIA-USD", "STEP-USD", "SLIM-USD",
    "MNGO-USD", "RAY-USD", "SRM-USD", "COPE-USD",
]

# Tekrarları kaldır, sırayı koru
KRIPTOLAR = list(dict.fromkeys(KRIPTOLAR))

# ─── ZAMAN ARALIĞI AYARLARI ───────────────────────────────────────────────────
INTERVAL_SECENEKLER = {
    "1 Saatlik (1h)":   {"interval": "1h",  "lookback_days": 60,  "min_bar": 100},
    "4 Saatlik (4h)":   {"interval": "4h",  "lookback_days": 180, "min_bar": 80},
    "Günlük (1d)":      {"interval": "1d",  "lookback_days": 365, "min_bar": 60},
    "Haftalık (1w)":    {"interval": "1wk", "lookback_days": 730, "min_bar": 40},
}

# ─── YARDIMCI FONKSİYONLAR ────────────────────────────────────────────────────
def to_series(x):
    """DataFrame veya MultiIndex sütununu güvenli şekilde 1-boyutlu Series'e çevirir."""
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    if hasattr(x, "squeeze"):
        x = x.squeeze()
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    return x.astype(float)

def squeeze(s):
    return to_series(s)

def ema(seri, periyot):
    return to_series(seri).ewm(span=periyot, adjust=False).mean()

def hesapla_ind(df, atr_per, macd_h, macd_y, macd_s):
    c = to_series(df["Close"])
    h = to_series(df["High"])
    l = to_series(df["Low"])
    for p in [20, 50, 100, 200]:
        df[f"EMA{p}"] = c.ewm(span=p, adjust=False).mean()
    ema_h          = c.ewm(span=macd_h, adjust=False).mean()
    ema_y          = c.ewm(span=macd_y, adjust=False).mean()
    df["MACD"]     = ema_h - ema_y
    df["MACD_SIG"] = to_series(df["MACD"]).ewm(span=macd_s, adjust=False).mean()
    df["MACD_HIS"] = df["MACD"] - df["MACD_SIG"]
    hl = h - l
    hc = (h - c.shift(1)).abs()
    lc = (l - c.shift(1)).abs()
    df["TR"]  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["ATR"] = df["TR"].rolling(atr_per).mean()
    return df

def veri_cek(ticker, bas, bit, interval_cfg):
    """
    Kripto verisi çeker.
    bas/bit: datetime.date
    yfinance 1h için max 60 günlük veri verir, 4h için ~180 gün.
    """
    try:
        interval     = interval_cfg["interval"]
        lookback_days = interval_cfg["lookback_days"]
        min_bar      = interval_cfg["min_bar"]

        # Warm-up için başlangıçtan geriye ekstra veri al (EMA200 için)
        veri_bas = (pd.Timestamp(bas) - pd.DateOffset(days=lookback_days)).date()

        df = yf.download(
            ticker,
            start=str(veri_bas),
            end=str(bit + timedelta(days=2)),
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
        if df.empty or len(df) < min_bar:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        for col in df.columns:
            df[col] = to_series(df[col])
        # Timezone normalize et
        if hasattr(df.index, "tz") and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return None

def btc_filtre_olustur(bas, bit, interval_cfg):
    """BTC'nin her bar'da EMA200 üzerinde olup olmadığını döndürür."""
    try:
        interval      = interval_cfg["interval"]
        lookback_days = interval_cfg["lookback_days"]
        veri_bas = (pd.Timestamp(bas) - pd.DateOffset(days=lookback_days)).date()

        df = yf.download(
            "BTC-USD",
            start=str(veri_bas),
            end=str(bit + timedelta(days=2)),
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
        if df.empty:
            return {}
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if hasattr(df.index, "tz") and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df["EMA200"] = to_series(df["Close"]).ewm(span=200, adjust=False).mean()
        df.dropna(subset=["EMA200"], inplace=True)
        # 1h/4h için timestamp, 1d/1w için date kullan
        if interval in ("1h", "4h"):
            return {row.Index: float(row.Close) > float(row.EMA200)
                    for row in df.itertuples()}
        else:
            return {row.Index.date(): float(row.Close) > float(row.EMA200)
                    for row in df.itertuples()}
    except Exception:
        return {}

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Backtest Ayarları")

st.sidebar.markdown("### ⏱️ Zaman Aralığı")
interval_key = st.sidebar.selectbox(
    "Zaman Dilimi",
    options=list(INTERVAL_SECENEKLER.keys()),
    index=1,   # Varsayılan: 4 Saatlik
    help="Backtest için kullanılacak mum aralığı"
)
interval_cfg = INTERVAL_SECENEKLER[interval_key]

# 1h verisi yfinance'de max 60 gün geriye gidiyor — uyarı ver
if interval_cfg["interval"] == "1h":
    st.sidebar.warning("⚠️ 1h verisi Yahoo Finance'de max ~60 gün geriye gider.")

st.sidebar.markdown("### 📅 Tarih Aralığı")
col1, col2 = st.sidebar.columns(2)

# 1h limitine göre min tarih
min_bas = date(2018, 1, 1)
if interval_cfg["interval"] == "1h":
    min_bas = (date.today() - timedelta(days=58))

bas_tarih = col1.date_input("Başlangıç", value=date(2022, 1, 1),
                             min_value=min_bas, max_value=date.today())
bit_tarih = col2.date_input("Bitiş", value=date.today(),
                             min_value=min_bas, max_value=date.today())

st.sidebar.markdown("### 💰 Sermaye & Pozisyon")
portfoy      = st.sidebar.number_input("Başlangıç Sermaye (USD)", min_value=100,
                                        max_value=100_000_000, value=10_000, step=100)
max_pozisyon = st.sidebar.slider("Max Eş Zamanlı Pozisyon", 1, 20, 5, 1)
poz_yuzde    = st.sidebar.slider("Pozisyon Büyüklüğü (%)", 5.0, 50.0,
                                  round(100 / max_pozisyon, 1), 5.0)

st.sidebar.markdown("### 📐 R:R & Stop")
rr_kat  = st.sidebar.select_slider("R:R Katsayısı",
           options=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], value=3.0)
atr_kat = st.sidebar.slider("ATR Katsayısı (Stop)", 0.5, 3.0, 1.5, 0.5)
atr_per = st.sidebar.slider("ATR Periyodu", 7, 21, 14, 1)

st.sidebar.markdown("### 📊 MACD")
macd_h = st.sidebar.slider("MACD Hızlı EMA", 5,  20, 12, 1)
macd_y = st.sidebar.slider("MACD Yavaş EMA", 10, 50, 26, 1)
macd_s = st.sidebar.slider("MACD Sinyal",    5,  20,  9, 1)

st.sidebar.markdown("### 🔍 Filtreler")
btc_filtre_aktif = st.sidebar.checkbox(
    "BTC Trend Filtresi (BTC > EMA200)", value=True,
    help="Sadece BTC EMA200 üzerindeyken işlem aç."
)

# ─── BAŞLIK ───────────────────────────────────────────────────────────────────
st.title("📊 Kripto Gerçekçi Backtest")
st.caption(f"Pozisyon Yönetimli | MACD Strateji | Max {max_pozisyon} Pozisyon | R:R 1:{rr_kat:.0f} | {interval_key}")

# ─── INFO ─────────────────────────────────────────────────────────────────────
st.info(f"""
**Gerçekçi Backtest Kuralları:**
- Aynı anda maksimum **{max_pozisyon}** pozisyon açık olabilir
- Her pozisyon güncel portföyün **%{poz_yuzde:.0f}'i** kadardır (~${portfoy*poz_yuzde/100:,.0f})
- Kripto piyasası **7/24** açık — tüm barlar (gece/hafta sonu) dahil
- Tüm slotlar dolunca yeni sinyaller beklemeye alınır
- Pozisyon kapanınca slot açılır, sıradaki sinyal değerlendirilir
- **Bileşik getiri** — kazanç arttıkça pozisyon büyüklüğü de artar
""")

# ─── BACKTEST BUTONU ──────────────────────────────────────────────────────────
if st.button("🚀 Backtest Çalıştır", use_container_width=True, type="primary"):

    bas_ts = pd.Timestamp(bas_tarih)
    bit_ts = pd.Timestamp(bit_tarih)

    # BTC trend filtresi
    btc_f = {}
    if btc_filtre_aktif:
        with st.spinner("BTC trend verisi indiriliyor..."):
            btc_f = btc_filtre_olustur(bas_tarih, bit_tarih, interval_cfg)

    # Veri indir
    kripto_verileri = {}
    progress = st.progress(0, text="Veriler indiriliyor...")
    for hi, sembol in enumerate(KRIPTOLAR):
        progress.progress(
            (hi + 1) / len(KRIPTOLAR),
            text=f"İndiriliyor: {sembol} ({hi+1}/{len(KRIPTOLAR)})"
        )
        df_raw = veri_cek(sembol, bas_tarih, bit_tarih, interval_cfg)
        if df_raw is None:
            continue
        try:
            df = df_raw.copy()
            df = hesapla_ind(df, atr_per, macd_h, macd_y, macd_s)
            df.dropna(subset=["EMA200", "MACD_HIS", "ATR"], inplace=True)
            min_bar = interval_cfg["min_bar"]
            if len(df) >= min_bar:
                kripto_verileri[sembol] = df
        except Exception:
            continue
    progress.empty()

    if not kripto_verileri:
        st.error("Hiçbir kriptodan yeterli veri alınamadı. Tarih aralığını veya zaman dilimini değiştirin.")
        st.stop()

    # Günlük/saatlik sinyaller üret
    with st.spinner("Sinyaller hesaplanıyor..."):
        bar_sinyaller = {}
        for sembol, df in kripto_verileri.items():
            for i in range(1, len(df)):
                son    = df.iloc[i]
                onceki = df.iloc[i - 1]
                tarih  = son.name

                if tarih < bas_ts or tarih > bit_ts:
                    continue

                # BTC filtresi — 1h/4h için timestamp, 1d/1w için date
                if btc_filtre_aktif and btc_f:
                    if interval_cfg["interval"] in ("1h", "4h"):
                        # En yakın timestamp'i bul
                        gecti = btc_f.get(tarih, True)
                    else:
                        gecti = btc_f.get(tarih.date(), True)
                    if not gecti:
                        continue

                # Trend filtresi
                if not (float(son["EMA20"]) > float(son["EMA50"]) >
                        float(son["EMA100"]) > float(son["EMA200"])):
                    continue
                # MACD dönüşü
                if not (float(onceki["MACD_HIS"]) < 0 and float(son["MACD_HIS"]) > 0):
                    continue

                giris  = float(son["Close"])
                atr_v  = float(son["ATR"])
                stop   = giris - atr_v * atr_kat
                hedef  = giris + (giris - stop) * rr_kat
                if giris - stop <= 0:
                    continue

                if tarih not in bar_sinyaller:
                    bar_sinyaller[tarih] = []
                bar_sinyaller[tarih].append({
                    "sembol": sembol,
                    "giris" : giris,
                    "stop"  : stop,
                    "hedef" : hedef,
                    "top"   : sembol in TOP_KRIPTO,
                })

    # Gerçekçi backtest simülasyonu
    with st.spinner("Pozisyon yönetimi simüle ediliyor..."):
        portfoy_s    = float(portfoy)
        acik_pozlar  = []
        kapali_islem = []
        atlanan      = 0

        tum_tarihler = sorted(set(
            d for df in kripto_verileri.values()
            for d in df.index
            if bas_ts <= d <= bit_ts
        ))

        for tarih in tum_tarihler:
            # Açık pozisyonları kontrol et (stop / hedef)
            kapalanlar = []
            for poz in acik_pozlar:
                sembol = poz["sembol"]
                if sembol not in kripto_verileri:
                    continue
                df     = kripto_verileri[sembol]
                gunluk = df[df.index == tarih]
                if gunluk.empty:
                    continue
                gun_low  = float(gunluk.iloc[0]["Low"])
                gun_high = float(gunluk.iloc[0]["High"])
                sonuc    = None
                if gun_low <= poz["stop"]:
                    sonuc = "stop"; cikis = poz["stop"]
                elif gun_high >= poz["hedef"]:
                    sonuc = "hedef"; cikis = poz["hedef"]
                if sonuc:
                    kaz = (cikis - poz["giris"]) * poz["miktar"]
                    portfoy_s += kaz
                    kapali_islem.append({
                        "Açılış"  : poz["acilis"].strftime("%d.%m.%Y %H:%M"),
                        "Kapanış" : tarih.strftime("%d.%m.%Y %H:%M"),
                        "Kripto"  : usdt_goster(sembol),
                        "⭐"      : "⭐" if poz["top"] else "",
                        "Giriş"   : round(poz["giris"], 6),
                        "Çıkış"   : round(cikis, 6),
                        "Sonuç"   : "✅ Hedef" if sonuc == "hedef" else "❌ Stop",
                        "K/Z (USD)": round(kaz, 2),
                        "Portföy" : round(portfoy_s, 2),
                    })
                    kapalanlar.append(poz)
            for k in kapalanlar:
                acik_pozlar.remove(k)

            # Yeni sinyaller
            if tarih in bar_sinyaller:
                sinyaller_bugun = sorted(
                    bar_sinyaller[tarih],
                    key=lambda x: (not x["top"])   # TOP kripto önce
                )
                for sinyal in sinyaller_bugun:
                    if any(p["sembol"] == sinyal["sembol"] for p in acik_pozlar):
                        continue
                    if len(acik_pozlar) >= max_pozisyon:
                        atlanan += 1
                        continue
                    poz_usd = portfoy_s * (poz_yuzde / 100)
                    miktar  = poz_usd / sinyal["giris"]
                    acik_pozlar.append({
                        "sembol" : sinyal["sembol"],
                        "acilis" : tarih,
                        "giris"  : sinyal["giris"],
                        "stop"   : sinyal["stop"],
                        "hedef"  : sinyal["hedef"],
                        "miktar" : miktar,
                        "top"    : sinyal["top"],
                    })

        # Kalan açık pozisyonları son fiyatla kapat
        for poz in acik_pozlar:
            sembol = poz["sembol"]
            if sembol not in kripto_verileri:
                continue
            df  = kripto_verileri[sembol]
            son = df.iloc[-1]
            cikis = float(son["Close"])
            kaz   = (cikis - poz["giris"]) * poz["miktar"]
            portfoy_s += kaz
            kapali_islem.append({
                "Açılış"  : poz["acilis"].strftime("%d.%m.%Y %H:%M"),
                "Kapanış" : son.name.strftime("%d.%m.%Y %H:%M"),
                "Kripto"  : usdt_goster(sembol),
                "⭐"      : "⭐" if poz["top"] else "",
                "Giriş"   : round(poz["giris"], 6),
                "Çıkış"   : round(cikis, 6),
                "Sonuç"   : "⏳ Açık",
                "K/Z (USD)": round(kaz, 2),
                "Portföy" : round(portfoy_s, 2),
            })

    st.session_state["kapali"]      = kapali_islem
    st.session_state["portfoy_s"]   = portfoy_s
    st.session_state["portfoy0"]    = portfoy
    st.session_state["atlanan"]     = atlanan
    st.session_state["interval_key"]= interval_key
    st.session_state["bas_ts"]      = bas_ts
    st.session_state["bit_ts"]      = bit_ts

# ─── SONUÇLAR ─────────────────────────────────────────────────────────────────
if "kapali" in st.session_state:
    kapali       = st.session_state["kapali"]
    portfoy_s    = st.session_state["portfoy_s"]
    portfoy0     = st.session_state["portfoy0"]
    atlanan      = st.session_state["atlanan"]
    son_interval = st.session_state.get("interval_key", interval_key)

    if not kapali:
        st.warning("Bu dönemde sinyal bulunamadı. Tarih aralığını veya parametreleri değiştirin.")
        st.stop()

    df_i     = pd.DataFrame(kapali)
    tamam    = df_i[df_i["Sonuç"].str.contains("Hedef|Stop")]
    kazanan  = df_i[df_i["Sonuç"] == "✅ Hedef"]
    kaybeden = df_i[df_i["Sonuç"] == "❌ Stop"]
    toplam   = len(tamam)
    wr       = len(kazanan) / toplam * 100 if toplam > 0 else 0
    getiri   = (portfoy_s - portfoy0) / portfoy0 * 100
    kz_usd   = portfoy_s - portfoy0

    g_renk = "metric-pos" if getiri >= 0 else "metric-neg"
    k_renk = "metric-pos" if kz_usd  >= 0 else "metric-neg"

    # Metrik kartları
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, lbl, val, renk in [
        (c1, "Başlangıç",      f"${portfoy0:,.2f}",  "metric-neu"),
        (c2, "Bitiş",          f"${portfoy_s:,.2f}", g_renk),
        (c3, "Toplam K/Z",     f"${kz_usd:+,.2f}",  k_renk),
        (c4, "Getiri",         f"{getiri:+.1f}%",     g_renk),
        (c5, "Win Rate",       f"{wr:.1f}%",          "metric-neu"),
        (c6, "Atlanan Sinyal", str(atlanan),          "metric-neu"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{lbl}</div>
            <div class="metric-value {renk}">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    c7, c8, c9 = st.columns(3)
    for col, lbl, val, renk in [
        (c7, "Toplam İşlem",    str(toplam),        "metric-neu"),
        (c8, "Kazanan (Hedef)", str(len(kazanan)),  "metric-pos"),
        (c9, "Kaybeden (Stop)", str(len(kaybeden)), "metric-neg"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{lbl}</div>
            <div class="metric-value {renk}">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Sekmeler
    tab1, tab2, tab3 = st.tabs(["💰 Portföy Eğrisi", "📅 Aylık Performans", "📋 İşlem Listesi"])

    with tab1:
        df_i["Kapanış_dt"] = pd.to_datetime(df_i["Kapanış"], format="%d.%m.%Y %H:%M")
        df_sorted = df_i.sort_values("Kapanış_dt")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sorted["Kapanış_dt"], y=df_sorted["Portföy"],
            fill="tozeroy", line=dict(color="#38bdf8", width=2),
            fillcolor="rgba(56,189,248,0.08)", name="Portföy"
        ))
        fig.add_hline(y=portfoy0, line_dash="dash",
                      line_color="#64748b", line_width=1,
                      annotation_text=f"Başlangıç: ${portfoy0:,.2f}")
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="#0d0f14",
            plot_bgcolor="#0d0f14", height=400,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis=dict(gridcolor="#1e293b", tickformat=",.2f", tickprefix="$"),
            xaxis=dict(gridcolor="#1e293b"),
            showlegend=False,
            title=dict(text=f"Portföy Eğrisi — {son_interval}", font=dict(size=13)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_i["Ay"] = df_i["Kapanış_dt"].dt.to_period("M")
        aylik = df_i.groupby("Ay")["K/Z (USD)"].sum().reset_index()
        aylik["Kümülatif"] = portfoy0 + aylik["K/Z (USD)"].cumsum()

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=aylik["Ay"].astype(str), y=aylik["K/Z (USD)"],
            marker_color=[("#3fb950" if v >= 0 else "#ef4444") for v in aylik["K/Z (USD)"]],
            name="Aylık K/Z",
            text=[f"${v:+,.2f}" for v in aylik["K/Z (USD)"]],
            textposition="outside"
        ))
        fig2.update_layout(
            template="plotly_dark", paper_bgcolor="#0d0f14",
            plot_bgcolor="#0d0f14", height=350,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis=dict(gridcolor="#1e293b", tickformat=",.2f", tickprefix="$"),
            xaxis=dict(gridcolor="#1e293b"),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

        aylik_goster = aylik.copy()
        aylik_goster["Ay"] = aylik_goster["Ay"].astype(str)
        aylik_goster["K/Z (USD)"] = aylik_goster["K/Z (USD)"].apply(lambda x: f"${x:+,.2f}")
        aylik_goster["Kümülatif"] = aylik_goster["Kümülatif"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(aylik_goster, use_container_width=True, hide_index=True)

    with tab3:
        df_goster = df_i.drop(columns=["Kapanış_dt", "Ay"], errors="ignore").copy()
        df_goster["K/Z (USD)"] = df_goster["K/Z (USD)"].apply(lambda x: f"${x:+,.2f}")
        df_goster["Portföy"]   = df_goster["Portföy"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_goster, use_container_width=True, hide_index=True)

        csv = df_i.drop(columns=["Kapanış_dt", "Ay"], errors="ignore").to_csv(
            index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ CSV İndir", data=csv,
            file_name=f"kripto_backtest_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    st.markdown("---")
    st.caption("⚠️ Bu analiz yatırım tavsiyesi değildir. Kripto piyasaları yüksek risk içerir.")

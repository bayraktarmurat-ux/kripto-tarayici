import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kripto Sinyal Tarayıcı",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── KRİPTO LİSTELERİ ─────────────────────────────────────────────────────────
# yfinance sembol formatı: BTC-USD (içsel), görüntüleme: BTCUSDT
# Tüm semboller "-USD" suffix'i ile tanımlanır, TradingView linklerinde USDT'ye çevrilir.

# Yüksek hacimli / güvenilir büyük kriptolar (TOP tier)
TOP_KRIPTO = {
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
    "ADA-USD", "AVAX-USD", "DOT-USD", "MATIC-USD", "LINK-USD",
    "LTC-USD", "ATOM-USD", "UNI-USD", "NEAR-USD", "APT-USD",
    "OP-USD",  "ARB-USD",  "INJ-USD", "SUI-USD",  "TIA-USD",
}

def usdt_goster(sembol):
    """BTC-USD → BTCUSDT görüntüleme formatı"""
    return sembol.replace("-USD", "USDT")

def tv_link(sembol):
    """TradingView linki için USDT formatına çevir"""
    return f"https://tr.tradingview.com/chart/?symbol={usdt_goster(sembol)}"

# Taranacak tüm kripto listesi (~210 coin, yfinance'de çalışan semboller)
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
    "FET-USD", "OCEAN-USD", "AGIX-USD", "NMR-USD", "RLC-USD",
    "TAO-USD", "RNDR-USD", "WLD-USD", "ARKM-USD", "CTXC-USD",

    # ── Oyun / Metaverse / NFT ───────────────────────────────────────────────
    "SAND-USD", "MANA-USD", "AXS-USD", "ENJ-USD", "CHZ-USD",
    "GALA-USD", "BLUR-USD", "APE-USD", "ILV-USD", "GODS-USD",
    "SLP-USD", "ALICE-USD", "TLM-USD", "PYR-USD", "SUPER-USD",
    "HERO-USD", "SKILL-USD",

    # ── Altyapı / Depolama / Ağ ──────────────────────────────────────────────
    "AR-USD", "SC-USD", "STORJ-USD", "HNT-USD", "POWR-USD",
    "GLM-USD", "REQ-USD", "DIA-USD", "API3-USD", "TRB-USD",
    "UMA-USD", "CELR-USD", "SKL-USD", "KEEP-USD", "NU-USD",

    # ── Gizlilik ─────────────────────────────────────────────────────────────
    "XMR-USD", "ZEC-USD", "DASH-USD", "SCRT-USD", "ROSE-USD",

    # ── Borsalar / CeFi ──────────────────────────────────────────────────────
    "CRO-USD", "OKB-USD", "GT-USD", "HT-USD", "KCS-USD",
    "MX-USD", "BGB-USD",

    # ── Cosmos Ekosistemi ────────────────────────────────────────────────────
    "OSMO-USD", "JUNO-USD", "EVMOS-USD", "STARS-USD", "CMDX-USD",

    # ── Solana Ekosistemi ────────────────────────────────────────────────────
    "SUI-USD", "SEI-USD", "TIA-USD", "BONK-USD", "JTO-USD",
    "PYTH-USD", "WIF-USD", "BOME-USD", "POPCAT-USD",

    # ── Yeni Nesil L1 ────────────────────────────────────────────────────────
    "SUI-USD", "APT-USD", "SEI-USD", "MONAD-USD", "BERACHAIN-USD",

    # ── Stablecoin Altyapısı / RWA ───────────────────────────────────────────
    "ONDO-USD", "CFG-USD", "MPL-USD", "TRU-USD", "CREDIT-USD",

    # ── Köprü / Birlikte Çalışabilirlik ──────────────────────────────────────
    "REN-USD", "MULTI-USD", "STG-USD", "SYN-USD", "HOP-USD",

    # ── Oracle ───────────────────────────────────────────────────────────────
    "LINK-USD", "BAND-USD", "TRB-USD", "API3-USD", "DIA-USD",

    # ── Meme ─────────────────────────────────────────────────────────────────
    "DOGE-USD", "SHIB-USD", "FLOKI-USD", "PEPE-USD",
    "BONK-USD", "WIF-USD", "BOME-USD", "MEME-USD",
    "TURBO-USD", "LADYS-USD", "BABYDOGE-USD",

    # ── Diğer Önemli ─────────────────────────────────────────────────────────
    "XTZ-USD", "EOS-USD", "THETA-USD", "AXL-USD", "PYTH-USD",
    "JUP-USD", "W-USD", "PORTAL-USD", "ALT-USD", "ETHFI-USD",
    "REZ-USD", "OMNI-USD", "SAGA-USD", "ZK-USD", "ZETA-USD",
    "IO-USD", "ZRO-USD", "LISTA-USD", "RENDER-USD",
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
    "1 Saatlik (1h)":   {"interval": "1h",  "period": "60d",  "min_bar": 100},
    "4 Saatlik (4h)":   {"interval": "4h",  "period": "180d", "min_bar": 80},
    "Günlük (1d)":      {"interval": "1d",  "period": "365d", "min_bar": 60},
    "Haftalık (1w)":    {"interval": "1wk", "period": "730d", "min_bar": 40},
}

# ─── YARDIMCI FONKSİYONLAR ────────────────────────────────────────────────────
def ema(seri, periyot):
    if hasattr(seri, "squeeze"):
        seri = seri.squeeze()
    return seri.ewm(span=periyot, adjust=False).mean()

def atr_hesapla(df, periyot=14):
    close = df["Close"].squeeze() if hasattr(df["Close"], "squeeze") else df["Close"]
    high  = df["High"].squeeze()  if hasattr(df["High"],  "squeeze") else df["High"]
    low   = df["Low"].squeeze()   if hasattr(df["Low"],   "squeeze") else df["Low"]
    hl = high - low
    hc = (high - close.shift(1)).abs()
    lc = (low  - close.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=periyot, adjust=False).mean()

def veri_cek(ticker, interval_cfg):
    """Kripto verisi çeker — semboller zaten BTC-USD formatında"""
    try:
        interval = interval_cfg["interval"]
        period   = interval_cfg["period"]
        min_bar  = interval_cfg["min_bar"]

        df = yf.download(
            ticker,
            period=period,
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
            df[col] = df[col].squeeze() if hasattr(df[col], "squeeze") else df[col]
        # Timezone kaldır (bazı aralıklarda tz-aware gelir)
        if hasattr(df.index, "tz") and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return None

# ─── PAZAR FİLTRESİ (BTC Trend) ──────────────────────────────────────────────
@st.cache_data(ttl=3600)
def pazar_kontrol(interval_key):
    """BTC son kapanış > EMA200 mi kontrol eder. 1 saat cache'ler."""
    try:
        cfg = INTERVAL_SECENEKLER[interval_key]
        df  = yf.download(
            "BTC-USD",
            period=cfg["period"],
            interval=cfg["interval"],
            progress=False,
            auto_adjust=True,
        )
        if df.empty:
            return None, None, None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
        df.dropna(subset=["EMA200"], inplace=True)
        son      = df.iloc[-1]
        kapanis  = float(son["Close"])
        ema200   = float(son["EMA200"])
        aktif    = kapanis > ema200
        fark_pct = (kapanis - ema200) / ema200 * 100
        return aktif, kapanis, ema200, fark_pct
    except Exception:
        return None, None, None, None

# ─── SİNYAL TARAMA (MACD STRATEJİSİ) ─────────────────────────────────────────
def sinyal_tara(df, params):
    """
    Strateji: Trend (EMA20 > EMA50 > EMA100 > EMA200) + MACD histogram negatiften pozitife dönüş
    """
    atr_per    = params["atr_periyot"]
    atr_kat    = params["atr_katsayi"]
    rr         = params["rr_katsayi"]
    macd_hizli = params["macd_hizli"]
    macd_yavas = params["macd_yavas"]
    macd_sinyal= params["macd_sinyal"]

    df = df.copy()
    for col in ["Open","High","Low","Close","Volume"]:
        if col in df.columns:
            df[col] = df[col].squeeze() if hasattr(df[col], "squeeze") else df[col]

    close = df["Close"]
    df["EMA20"]  = ema(close, 20)
    df["EMA50"]  = ema(close, 50)
    df["EMA100"] = ema(close, 100)
    df["EMA200"] = ema(close, 200)
    df["ATR"]    = atr_hesapla(df, atr_per)

    # MACD
    ema_h          = close.ewm(span=macd_hizli,  adjust=False).mean()
    ema_y          = close.ewm(span=macd_yavas,  adjust=False).mean()
    df["MACD"]     = ema_h - ema_y
    df["MACD_SIG"] = df["MACD"].ewm(span=macd_sinyal, adjust=False).mean()
    df["MACD_HIS"] = df["MACD"] - df["MACD_SIG"]

    son    = df.iloc[-1]
    onceki = df.iloc[-2]

    # ── 1. TREND FİLTRESİ ─────────────────────────────────────────────────────
    if not (float(son["EMA20"]) > float(son["EMA50"]) >
            float(son["EMA100"]) > float(son["EMA200"])):
        return None

    # ── 2. MACD: Histogram negatiften pozitife döndü ──────────────────────────
    if not (float(onceki["MACD_HIS"]) < 0 and float(son["MACD_HIS"]) > 0):
        return None

    # ── İŞLEM DETAYLARI ───────────────────────────────────────────────────────
    kapanis = float(son["Close"])
    atr_val = float(son["ATR"])
    stop    = round(kapanis - atr_kat * atr_val, 6)
    hedef   = round(kapanis + rr * atr_kat * atr_val, 6)

    return {
        "Son Kapanis": round(kapanis, 6),
        "MACD_HIS"   : round(float(son["MACD_HIS"]), 6),
        "MACD"       : round(float(son["MACD"]), 6),
        "Stop"       : stop,
        "Stop%"      : round((kapanis - stop) / kapanis * 100, 2),
        "Hedef"      : hedef,
        "Hedef%"     : round((hedef - kapanis) / kapanis * 100, 2),
        "ATR"        : round(atr_val, 6),
    }

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Ayarlar")

st.sidebar.markdown("### ⏱️ Zaman Aralığı")
interval_key = st.sidebar.selectbox(
    "Zaman Dilimi",
    options=list(INTERVAL_SECENEKLER.keys()),
    index=1,   # Varsayılan: 4 Saatlik
    help="Tarama ve grafik için kullanılacak mum aralığı"
)
interval_cfg = INTERVAL_SECENEKLER[interval_key]

st.sidebar.markdown("### 💰 Portföy")
portfoy = st.sidebar.number_input(
    "Portföy (USD)", min_value=100, max_value=10_000_000,
    value=10_000, step=100
)
risk_yuzde = st.sidebar.slider(
    "Risk %", min_value=0.5, max_value=5.0, value=1.0, step=0.5
)
rr_katsayi = st.sidebar.slider(
    "R:R Katsayısı", min_value=1.0, max_value=5.0, value=3.0, step=0.5
)
atr_katsayi = st.sidebar.slider(
    "ATR Katsayısı", min_value=0.5, max_value=3.0, value=1.5, step=0.5
)
atr_periyot = st.sidebar.slider(
    "ATR Periyodu", min_value=7, max_value=21, value=14, step=1
)

st.sidebar.markdown("### 📊 MACD")
macd_hizli  = st.sidebar.slider("MACD Hızlı EMA", min_value=5,  max_value=20, value=12, step=1)
macd_yavas  = st.sidebar.slider("MACD Yavaş EMA", min_value=10, max_value=50, value=26, step=1)
macd_sinyal = st.sidebar.slider("MACD Sinyal",    min_value=5,  max_value=20, value=9,  step=1)

params = {
    "atr_periyot" : atr_periyot,
    "atr_katsayi" : atr_katsayi,
    "rr_katsayi"  : rr_katsayi,
    "macd_hizli"  : macd_hizli,
    "macd_yavas"  : macd_yavas,
    "macd_sinyal" : macd_sinyal,
}

# ─── ANA SAYFA ────────────────────────────────────────────────────────────────
st.title("🪙 Kripto Sinyal Tarayıcı")
st.caption(f"BTC Trend Filtreli | EMA Trend | MACD Histogram Dönüşü | R:R 1:{rr_katsayi:.0f} | {interval_key}")

# ─── PAZAR DURUMU (BTC FİLTRESİ) ──────────────────────────────────────────────
pazar_sonuc = pazar_kontrol(interval_key)
aktif       = pazar_sonuc[0]
btc_fiyat   = pazar_sonuc[1]
btc_ema200  = pazar_sonuc[2]
btc_fark    = pazar_sonuc[3]

if aktif is None:
    st.warning("⚠️ BTC verisi alınamadı — pazar filtresi devre dışı.")
    pazar_gecti = True
elif aktif:
    st.success(
        f"✅ **BTC Boğa Trendi** ({interval_key}) — "
        f"BTC: ${btc_fiyat:,.2f}  |  EMA200: ${btc_ema200:,.2f}  |  "
        f"Fark: **+{btc_fark:.1f}%** — Strateji aktif, tarama yapılabilir."
    )
    pazar_gecti = True
else:
    st.error(
        f"🚫 **BTC EMA200 Altında** ({interval_key}) — "
        f"BTC: ${btc_fiyat:,.2f}  |  EMA200: ${btc_ema200:,.2f}  |  "
        f"Fark: **{btc_fark:.1f}%** — Strateji pasif, işlem önerilmez."
    )
    pazar_gecti = False

st.markdown("---")

# ─── BYPASS & TARA ────────────────────────────────────────────────────────────
pazar_bypass = st.sidebar.checkbox(
    "⚠️ Pazar filtresini atla", value=False,
    help="BTC EMA200 altında olsa bile tarama yapılmasına izin verir."
)
tara_disabled = not pazar_gecti
if pazar_bypass:
    tara_disabled = False
    st.warning("⚠️ Pazar filtresi devre dışı bırakıldı.")

if st.button("🔍 Tara", use_container_width=True, type="primary",
             disabled=tara_disabled):
    risk_tl   = portfoy * risk_yuzde / 100
    sinyaller = []
    hatalar   = []

    progress = st.progress(0, text="Tarama başlıyor...")
    toplam   = len(KRIPTOLAR)

    for i, kripto in enumerate(KRIPTOLAR):
        progress.progress(
            (i + 1) / toplam,
            text=f"Taraniyor: {kripto} ({i+1}/{toplam})"
        )
        df = veri_cek(kripto, interval_cfg)
        if df is None:
            hatalar.append(kripto)
            continue
        sonuc = sinyal_tara(df, params)
        if sonuc is None:
            continue

        kapanis    = sonuc["Son Kapanis"]
        stop       = sonuc["Stop"]
        risk_hisse = kapanis - stop
        if risk_hisse <= 0:
            continue
        # Kripto için lot yerine miktar hesabı
        miktar   = risk_tl / risk_hisse
        giris_usd = round(miktar * kapanis, 2)

        sinyaller.append({
            "⭐"        : "⭐" if kripto in TOP_KRIPTO else "",
            "Kripto"   : kripto,
            "Fiyat"    : kapanis,
            "MACD_HIS" : sonuc["MACD_HIS"],
            "MACD"     : sonuc["MACD"],
            "Stop"     : stop,
            "Stop%"    : sonuc["Stop%"],
            "Hedef"    : sonuc["Hedef"],
            "Hedef%"   : sonuc["Hedef%"],
            "ATR"      : sonuc["ATR"],
            "Miktar"   : round(miktar, 4),
            "Giriş USD": giris_usd,
            "Risk USD" : round(risk_tl, 2),
        })

    progress.empty()
    st.session_state["sinyaller"]    = sinyaller
    st.session_state["hatalar"]      = hatalar
    st.session_state["tarih"]        = datetime.now().strftime("%d.%m.%Y %H:%M")
    st.session_state["interval_key"] = interval_key

# ─── SONUÇLAR ─────────────────────────────────────────────────────────────────
if "sinyaller" in st.session_state:
    sinyaller    = st.session_state["sinyaller"]
    tarih        = st.session_state["tarih"]
    hatalar      = st.session_state.get("hatalar", [])
    son_interval = st.session_state.get("interval_key", interval_key)

    st.markdown(f"### Tarama Sonuçları — {tarih} | {son_interval}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sinyal Sayısı",  len(sinyaller))
    col2.metric("Taranan Kripto", len(KRIPTOLAR))
    col3.metric("Veri Hatası",    len(hatalar))
    col4.metric("Pazar",          "✅ Boğa" if pazar_gecti else "🚫 Ayı")

    if len(hatalar) > 0:
        with st.expander(f"⚠️ Veri alınamayan {len(hatalar)} kripto"):
            st.caption("Yahoo Finance'den veri çekilemedi. Sembol değişimi veya geçici bağlantı sorunu olabilir.")
            cols = st.columns(6)
            for i, k in enumerate(sorted(hatalar)):
                cols[i % 6].markdown(f"[{usdt_goster(k)}]({tv_link(k)})")

    if len(sinyaller) == 0:
        st.warning("Seçilen zaman diliminde kriterlere uyan kripto bulunamadı.")
    else:
        df_sonuc = pd.DataFrame(sinyaller).sort_values(
            by=["⭐", "MACD_HIS"], ascending=[False, False]
        )

        top_var = df_sonuc[df_sonuc["⭐"] == "⭐"]
        if len(top_var) > 0:
            st.success(
                f"⭐ **{len(top_var)} kripto büyük cap listesinde!** "
                f"({', '.join(top_var['Kripto'].apply(usdt_goster).tolist())}) — Yüksek likidite, öncelikli değerlendir."
            )

        df_goster = df_sonuc.copy()
        df_goster["Stop%"]  = df_goster["Stop%"].apply(lambda x: f"-%{x}")
        df_goster["Hedef%"] = df_goster["Hedef%"].apply(lambda x: f"+%{x}")
        # Kripto sütununu USDT formatında göster
        df_goster["Kripto"] = df_goster["Kripto"].apply(usdt_goster)
        df_goster["📈 Grafik"] = df_sonuc["Kripto"].apply(tv_link)

        st.dataframe(
            df_goster,
            use_container_width=True,
            hide_index=True,
            column_config={
                "📈 Grafik": st.column_config.LinkColumn(
                    "📈 Grafik",
                    help="TradingView'da aç",
                    display_text="TradingView →"
                )
            }
        )

        # Özet
        toplam_giris = df_sonuc["Giriş USD"].sum()
        toplam_risk  = df_sonuc["Risk USD"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Toplam Sermaye Kullanımı", f"${toplam_giris:,.2f}")
        c2.metric("Toplam Risk",
                  f"${toplam_risk:,.2f}  (%{toplam_risk/portfoy*100:.1f} portföy)")

        # CSV indir
        csv = df_sonuc.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ CSV İndir",
            data=csv,
            file_name="kripto_sinyaller_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.markdown("### 📊 Grafik")

        # Selectbox: USDT formatında göster, ama iç değer -USD olarak kalsın
        sinyal_map = {usdt_goster(r["Kripto"]): r["Kripto"] for r in sinyaller}
        secili_label = st.selectbox("Kripto seçin:", list(sinyal_map.keys()))
        secili = sinyal_map[secili_label]
        df_grafik = veri_cek(secili, interval_cfg)

        if df_grafik is not None:
            c = df_grafik["Close"].squeeze() if hasattr(df_grafik["Close"], "squeeze") else df_grafik["Close"]
            df_grafik["EMA20"]  = ema(df_grafik["Close"], 20)
            df_grafik["EMA50"]  = ema(df_grafik["Close"], 50)
            df_grafik["EMA100"] = ema(df_grafik["Close"], 100)
            df_grafik["EMA200"] = ema(df_grafik["Close"], 200)
            ema_h = c.ewm(span=macd_hizli, adjust=False).mean()
            ema_y = c.ewm(span=macd_yavas, adjust=False).mean()
            df_grafik["MACD"]     = ema_h - ema_y
            df_grafik["MACD_SIG"] = df_grafik["MACD"].ewm(span=macd_sinyal, adjust=False).mean()
            df_grafik["MACD_HIS"] = df_grafik["MACD"] - df_grafik["MACD_SIG"]

            secili_sinyal = next(r for r in sinyaller if r["Kripto"] == secili)

            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                row_heights=[0.7, 0.3], vertical_spacing=0.04
            )

            # Mum grafik
            fig.add_trace(go.Candlestick(
                x=df_grafik.index,
                open=df_grafik["Open"], high=df_grafik["High"],
                low=df_grafik["Low"],   close=df_grafik["Close"],
                name="Fiyat",
                increasing_line_color="#22c55e",
                decreasing_line_color="#ef4444",
            ), row=1, col=1)

            # EMA çizgileri
            for col_name, renk, genislik in [
                ("EMA20","#38bdf8",1.5), ("EMA50","#f59e0b",1.5),
                ("EMA100","#a78bfa",1),  ("EMA200","#f472b6",1),
            ]:
                fig.add_trace(go.Scatter(
                    x=df_grafik.index, y=df_grafik[col_name],
                    name=col_name, line=dict(color=renk, width=genislik)
                ), row=1, col=1)

            # Stop ve hedef çizgileri
            son_tarih = df_grafik.index[-1]
            # Kripto 7/24 açık — offset olarak timedelta kullan
            interval_map = {"1h": 24, "4h": 6, "1d": 1, "1wk": 1}
            gun_say = interval_map.get(interval_cfg["interval"], 1)
            bitis   = son_tarih + timedelta(hours=24 * gun_say * 5)

            for seviye, renk, isim in [
                (secili_sinyal["Stop"],  "#ef4444", "Stop"),
                (secili_sinyal["Hedef"], "#22c55e", "Hedef"),
            ]:
                fig.add_shape(
                    type="line",
                    x0=son_tarih, x1=bitis, y0=seviye, y1=seviye,
                    line=dict(color=renk, width=1.5, dash="dash"),
                    row=1, col=1
                )
                fig.add_annotation(
                    x=bitis, y=seviye,
                    text=f"{isim} {seviye:.4f}",
                    showarrow=False,
                    font=dict(color=renk, size=11),
                    xanchor="left", row=1, col=1
                )

            # MACD histogram
            colors = ["#3fb950" if v >= 0 else "#ef4444" for v in df_grafik["MACD_HIS"]]
            fig.add_trace(go.Bar(
                x=df_grafik.index, y=df_grafik["MACD_HIS"],
                name="MACD His.", marker_color=colors, opacity=0.7
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=df_grafik.index, y=df_grafik["MACD"],
                name="MACD", line=dict(color="#38bdf8", width=1.5)
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=df_grafik.index, y=df_grafik["MACD_SIG"],
                name="Sinyal", line=dict(color="#f59e0b", width=1.5)
            ), row=2, col=1)
            fig.add_hline(y=0, line_dash="dot", line_color="#64748b", row=2, col=1)

            # Son bar çizgisi
            fig.add_vline(
                x=son_tarih, line_dash="dot",
                line_color="#facc15", line_width=1,
                row="all", col=1
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d0f14",
                plot_bgcolor="#0d0f14",
                height=650,
                showlegend=True,
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=100, t=30, b=10),
                font=dict(family="Consolas", size=11),
                title=dict(text=f"{usdt_goster(secili)} — {son_interval}", font=dict(size=13)),
            )
            fig.update_yaxes(gridcolor="#1e293b")
            fig.update_xaxes(gridcolor="#1e293b")

            st.plotly_chart(fig, use_container_width=True)

            # İşlem özeti
            st.markdown(f"""
| | |
|---|---|
| **Kripto** | {usdt_goster(secili)} |
| **Zaman Dilimi** | {son_interval} |
| **Giriş** | ${secili_sinyal['Fiyat']:.6g} |
| **Stop** | ${secili_sinyal['Stop']:.6g} (-%{secili_sinyal['Stop%']}) |
| **Hedef** | ${secili_sinyal['Hedef']:.6g} (+%{secili_sinyal['Hedef%']}) |
| **R:R** | 1:{rr_katsayi:.0f} |
| **Miktar** | {secili_sinyal['Miktar']:.4f} adet |
| **Giriş Tutarı** | ${secili_sinyal['Giriş USD']:,.2f} |
| **Risk** | ${secili_sinyal['Risk USD']:,.2f} |
""")

        st.markdown("---")
        st.caption("⚠️ Bu analiz yatırım tavsiyesi değildir. Kripto piyasaları yüksek risk içerir.")

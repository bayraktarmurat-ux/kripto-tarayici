import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, date, timedelta
import plotly.graph_objects as go

st.set_page_config(
    page_title="Kripto Gerçekçi Backtest",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.metric-card { background:#1e2433; border:1px solid #2d3548; border-radius:10px;
               padding:16px 20px; text-align:center; }
.metric-label { font-size:12px; color:#8b95a8; margin-bottom:4px; }
.metric-value { font-size:24px; font-weight:700; }
.metric-pos { color:#22c55e; } .metric-neg { color:#ef4444; }
.metric-neu { color:#94a3b8; }
</style>
""", unsafe_allow_html=True)

# ─── KRİPTO LİSTELERİ ─────────────────────────────────────────────────────────
TOP_KRIPTO = {
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD",
    "ADA-USD","AVAX-USD","DOT-USD","MATIC-USD","LINK-USD",
    "LTC-USD","ATOM-USD","UNI-USD","NEAR-USD","APT-USD",
    "OP-USD","ARB-USD","INJ-USD","SUI-USD","TIA-USD",
}

def usdt_goster(sembol):
    return sembol.replace("-USD", "USDT")

KRIPTOLAR = [
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD",
    "ADA-USD","AVAX-USD","DOT-USD","TRX-USD","TON-USD",
    "MATIC-USD","LTC-USD","ATOM-USD","NEAR-USD","APT-USD",
    "ICP-USD","HBAR-USD","FIL-USD","ETC-USD","BCH-USD",
    "XLM-USD","ALGO-USD","VET-USD","EGLD-USD","FTM-USD",
    "ONE-USD","ZIL-USD","KAVA-USD","CELO-USD","FLOW-USD",
    "MINA-USD","KSM-USD","OP-USD","ARB-USD","IMX-USD",
    "LRC-USD","STRK-USD","LINK-USD","UNI-USD","AAVE-USD",
    "MKR-USD","SNX-USD","COMP-USD","CRV-USD","LDO-USD",
    "GRT-USD","1INCH-USD","DYDX-USD","GMX-USD","BAL-USD",
    "SUSHI-USD","RUNE-USD","INJ-USD","PENDLE-USD","CAKE-USD",
    "FET-USD","OCEAN-USD","AGIX-USD","TAO-USD","RNDR-USD",
    "WLD-USD","ARKM-USD","SAND-USD","MANA-USD","AXS-USD",
    "ENJ-USD","CHZ-USD","GALA-USD","BLUR-USD","APE-USD",
    "ILV-USD","SLP-USD","ALICE-USD","AR-USD","STORJ-USD",
    "HNT-USD","GLM-USD","API3-USD","TRB-USD","UMA-USD",
    "XMR-USD","ZEC-USD","DASH-USD","ROSE-USD","CRO-USD",
    "SUI-USD","SEI-USD","TIA-USD","BONK-USD","JTO-USD",
    "PYTH-USD","WIF-USD","BOME-USD","ONDO-USD","STG-USD",
    "DOGE-USD","SHIB-USD","FLOKI-USD","PEPE-USD","MEME-USD",
    "XTZ-USD","EOS-USD","THETA-USD","AXL-USD","JUP-USD",
    "RENDER-USD","ZETA-USD","ZK-USD","IO-USD","ZRO-USD",
    "JASMY-USD","DENT-USD","HOT-USD","IOTA-USD","QTUM-USD",
    "ONT-USD","ZEN-USD","RVN-USD","OGN-USD","QUICK-USD",
    "TWT-USD","ALPHA-USD","DODO-USD","RAY-USD","ANKR-USD",
    "BAND-USD","KNC-USD","ZRX-USD","NMR-USD","YFI-USD",
    "CVX-USD","FXS-USD","OSMO-USD","SCRT-USD","CELR-USD",
]
KRIPTOLAR = list(dict.fromkeys(KRIPTOLAR))

INTERVAL_SECENEKLER = {
    "1 Saatlik (1h)":  {"interval": "1h",  "lookback_days": 60,  "min_bar": 100},
    "4 Saatlik (4h)":  {"interval": "4h",  "lookback_days": 365, "min_bar": 80},
    "Günlük (1d)":     {"interval": "1d",  "lookback_days": 500, "min_bar": 60},
    "Haftalık (1w)":   {"interval": "1wk", "lookback_days": 730, "min_bar": 40},
}

# ─── YARDIMCI FONKSİYONLAR ────────────────────────────────────────────────────
def s(x):
    if isinstance(x, pd.DataFrame): x = x.iloc[:, 0]
    if hasattr(x, "squeeze"):       x = x.squeeze()
    if isinstance(x, pd.DataFrame): x = x.iloc[:, 0]
    return pd.Series(x.values.flatten(), index=x.index, dtype=float)

def ema_s(seri, n):
    x = s(seri)
    return pd.Series(x.ewm(span=n, adjust=False).mean().values.flatten(),
                     index=x.index, dtype=float)

def rsi_hesapla(close_s, n=14):
    cs    = s(close_s)
    delta = cs.diff()
    avg_g = delta.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    avg_l = (-delta).clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    rs    = avg_g / (avg_l + 1e-9)
    return pd.Series((100 - 100/(1+rs)).values.flatten(),
                     index=cs.index, dtype=float)

def atr_s(df_in, n=14):
    c  = s(df_in["Close"]); h = s(df_in["High"]); l = s(df_in["Low"])
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return pd.Series(tr.ewm(span=n, adjust=False).mean().values.flatten(),
                     index=c.index, dtype=float)

def hesapla_ind(df, params):
    df = df.copy()
    for col in ["Open","High","Low","Close","Volume"]:
        if col in df.columns: df[col] = s(df[col])
    c = s(df["Close"]); v = s(df["Volume"])
    df[f"EMA_K"] = ema_s(c, params["ema_kisa"]).values
    df[f"EMA_U"] = ema_s(c, params["ema_uzun"]).values
    df["RSI"]    = rsi_hesapla(c, params["rsi_periyot"]).values
    df["ATR"]    = atr_s(df, params["atr_periyot"]).values
    df["BRK"]    = c.shift(1).rolling(params["breakout_periyot"]).max().values
    df["HAC_ORT"]= v.shift(1).rolling(params["hacim_periyot"]).mean().values
    return df

def veri_cek(ticker, bas, bit, interval_cfg):
    try:
        interval     = interval_cfg["interval"]
        lookback     = interval_cfg["lookback_days"]
        min_bar      = interval_cfg["min_bar"]
        veri_bas     = (pd.Timestamp(bas) - pd.DateOffset(days=lookback)).date()

        df = yf.download(ticker,
                         start=str(veri_bas),
                         end=str(bit + timedelta(days=2)),
                         interval=interval, progress=False, auto_adjust=True)
        if df.empty or len(df) < min_bar: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        for col in df.columns: df[col] = s(df[col])
        if hasattr(df.index, "tz") and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return None

def btc_filtre_olustur(bas, bit, interval_cfg, ema_uzun):
    try:
        interval = interval_cfg["interval"]
        lookback = interval_cfg["lookback_days"]
        veri_bas = (pd.Timestamp(bas) - pd.DateOffset(days=lookback)).date()
        df = yf.download("BTC-USD",
                         start=str(veri_bas),
                         end=str(bit + timedelta(days=2)),
                         interval=interval, progress=False, auto_adjust=True)
        if df.empty: return {}
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if hasattr(df.index, "tz") and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        c = s(df["Close"])
        ema_u = pd.Series(c.ewm(span=ema_uzun, adjust=False).mean().values.flatten(),
                          index=c.index, dtype=float)
        if interval in ("1h", "4h"):
            return {idx: float(c.loc[idx]) > float(ema_u.loc[idx])
                    for idx in c.index}
        else:
            return {idx.date(): float(c.loc[idx]) > float(ema_u.loc[idx])
                    for idx in c.index}
    except Exception:
        return {}

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Backtest Ayarları")

st.sidebar.markdown("### ⏱️ Zaman Aralığı")
interval_key = st.sidebar.selectbox(
    "Zaman Dilimi", options=list(INTERVAL_SECENEKLER.keys()), index=2,
    help="Backtest için mum aralığı"
)
interval_cfg = INTERVAL_SECENEKLER[interval_key]
if interval_cfg["interval"] == "1h":
    st.sidebar.warning("⚠️ 1h verisi Yahoo Finance'de max ~60 gün geriye gider.")

st.sidebar.markdown("### 📅 Tarih Aralığı")
col1, col2 = st.sidebar.columns(2)
min_bas = date(2018, 1, 1)
if interval_cfg["interval"] == "1h":
    min_bas = date.today() - timedelta(days=58)
bas_tarih = col1.date_input("Başlangıç", value=date(2022, 1, 1),
                             min_value=min_bas, max_value=date.today())
bit_tarih = col2.date_input("Bitiş", value=date.today(),
                             min_value=min_bas, max_value=date.today())

st.sidebar.markdown("### 💰 Sermaye & Pozisyon")
portfoy      = st.sidebar.number_input("Başlangıç Sermaye (USD)", min_value=100,
                                        max_value=100_000_000, value=10_000, step=100)
max_pozisyon = st.sidebar.slider("Max Eş Zamanlı Pozisyon", 1, 20, 5, 1)
poz_yuzde    = st.sidebar.slider("Pozisyon Büyüklüğü (%)", 5.0, 50.0,
                                  round(100/max_pozisyon, 1), 5.0)

st.sidebar.markdown("### 📐 R:R & Stop")
rr_kat  = st.sidebar.select_slider("R:R Katsayısı",
           options=[1.0,1.5,2.0,2.5,3.0,3.5,4.0], value=2.0)
atr_kat = st.sidebar.slider("ATR Katsayısı (Stop)", 1.0, 5.0, 2.0, 0.5)
atr_per = st.sidebar.slider("ATR Periyodu", 7, 21, 14, 1)

st.sidebar.markdown("### 📈 EMA Trend")
ema_kisa = st.sidebar.slider("EMA Kısa", 10, 100, 50, 5)
ema_uzun = st.sidebar.slider("EMA Uzun", 50, 300, 200, 10)

st.sidebar.markdown("### 📊 RSI")
rsi_per = st.sidebar.slider("RSI Periyodu", 7, 21, 14, 1)
rsi_min = st.sidebar.slider("RSI Alt Sınır", 20, 60, 40, 5)
rsi_max = st.sidebar.slider("RSI Üst Sınır", 50, 85, 70, 5)

st.sidebar.markdown("### 🚀 Breakout")
brk_per = st.sidebar.slider("Breakout Periyodu (bar)", 5, 50, 20, 5)

st.sidebar.markdown("### 📦 Hacim")
hac_per = st.sidebar.slider("Hacim Ort. Periyodu", 5, 50, 20, 5)
hac_kat = st.sidebar.slider("Hacim Katsayısı", 1.0, 4.0, 1.5, 0.5)

st.sidebar.markdown("### 🔍 Filtreler")
btc_filtre_aktif = st.sidebar.checkbox("BTC Trend Filtresi (BTC > EMA)", value=True)

params = {
    "ema_kisa"         : ema_kisa,
    "ema_uzun"         : ema_uzun,
    "rsi_periyot"      : rsi_per,
    "rsi_min"          : rsi_min,
    "rsi_max"          : rsi_max,
    "breakout_periyot" : brk_per,
    "hacim_periyot"    : hac_per,
    "hacim_katsayi"    : hac_kat,
    "atr_periyot"      : atr_per,
    "atr_katsayi"      : atr_kat,
    "rr_katsayi"       : rr_kat,
}

# ─── BAŞLIK ───────────────────────────────────────────────────────────────────
st.title("📊 Kripto Gerçekçi Backtest")
st.caption(f"RSI + EMA Trend + Hacim Breakout | Max {max_pozisyon} Pozisyon | "
           f"R:R 1:{rr_kat:.0f} | {interval_key}")

st.info(f"""
**Strateji:** EMA{ema_kisa} > EMA{ema_uzun} (trend) + RSI {rsi_min}–{rsi_max} (momentum) + 
Son {brk_per} barın zirvesi kırıldı (breakout) + Hacim {hac_kat}x ortalamanın üzerinde (onay)

**Pozisyon Yönetimi:** Aynı anda max **{max_pozisyon}** pozisyon | 
Portföyün **%{poz_yuzde:.0f}'i** her pozisyon | Bileşik getiri aktif | 7/24 kripto piyasası
""")

# ─── BACKTEST BUTONU ──────────────────────────────────────────────────────────
if st.button("🚀 Backtest Çalıştır", use_container_width=True, type="primary"):

    bas_ts = pd.Timestamp(bas_tarih)
    bit_ts = pd.Timestamp(bit_tarih)

    # BTC filtresi
    btc_f = {}
    if btc_filtre_aktif:
        with st.spinner("BTC trend verisi indiriliyor..."):
            btc_f = btc_filtre_olustur(bas_tarih, bit_tarih, interval_cfg, ema_uzun)

    # Veri indir & indikatörler
    kripto_verileri = {}
    progress = st.progress(0, text="Veriler indiriliyor...")
    for hi, sembol in enumerate(KRIPTOLAR):
        progress.progress((hi+1)/len(KRIPTOLAR),
                          text=f"İndiriliyor: {usdt_goster(sembol)} ({hi+1}/{len(KRIPTOLAR)})")
        df_raw = veri_cek(sembol, bas_tarih, bit_tarih, interval_cfg)
        if df_raw is None: continue
        try:
            df = hesapla_ind(df_raw, params)
            df.dropna(subset=["EMA_K","EMA_U","RSI","ATR","BRK","HAC_ORT"], inplace=True)
            if len(df) >= interval_cfg["min_bar"]:
                kripto_verileri[sembol] = df
        except Exception:
            continue
    progress.empty()

    if not kripto_verileri:
        st.error("Hiçbir kriptodan yeterli veri alınamadı.")
        st.stop()

    # Sinyalleri üret
    with st.spinner("Sinyaller hesaplanıyor..."):
        bar_sinyaller = {}
        for sembol, df in kripto_verileri.items():
            c = s(df["Close"]); v = s(df["Volume"])
            for i in range(1, len(df)):
                tarih = df.index[i]
                if tarih < bas_ts or tarih > bit_ts: continue

                # BTC filtresi
                if btc_filtre_aktif and btc_f:
                    key = tarih if interval_cfg["interval"] in ("1h","4h") else tarih.date()
                    if not btc_f.get(key, True): continue

                row = df.iloc[i]
                son_close   = float(row["Close"])
                son_ema_k   = float(row["EMA_K"])
                son_ema_u   = float(row["EMA_U"])
                son_rsi     = float(row["RSI"])
                son_brk     = float(row["BRK"])
                son_vol     = float(row["Volume"])
                son_hac_ort = float(row["HAC_ORT"])
                son_atr     = float(row["ATR"])

                if any(np.isnan(x) for x in [son_ema_k, son_ema_u, son_rsi,
                                              son_brk, son_hac_ort, son_atr]):
                    continue

                # Strateji koşulları
                if son_ema_k <= son_ema_u:                       continue
                if not (rsi_min < son_rsi < rsi_max):            continue
                if son_close <= son_brk:                         continue
                if son_vol < son_hac_ort * hac_kat:              continue

                stop  = son_close - atr_kat * son_atr
                hedef = son_close + (son_close - stop) * rr_kat
                if son_close - stop <= 0: continue

                if tarih not in bar_sinyaller:
                    bar_sinyaller[tarih] = []
                bar_sinyaller[tarih].append({
                    "sembol": sembol,
                    "giris" : son_close,
                    "stop"  : stop,
                    "hedef" : hedef,
                    "top"   : sembol in TOP_KRIPTO,
                })

    # Simülasyon
    with st.spinner("Pozisyon yönetimi simüle ediliyor..."):
        portfoy_s    = float(portfoy)
        acik_pozlar  = []
        kapali_islem = []
        atlanan      = 0

        tum_tarihler = sorted({
            d for df in kripto_verileri.values()
            for d in df.index if bas_ts <= d <= bit_ts
        })

        for tarih in tum_tarihler:
            # Açık pozisyonları kontrol et
            kapalanlar = []
            for poz in acik_pozlar:
                sembol = poz["sembol"]
                if sembol not in kripto_verileri: continue
                df   = kripto_verileri[sembol]
                satir = df[df.index == tarih]
                if satir.empty: continue
                gun_low  = float(satir.iloc[0]["Low"])
                gun_high = float(satir.iloc[0]["High"])
                sonuc    = None
                if gun_low <= poz["stop"]:
                    sonuc = "stop";  cikis = poz["stop"]
                elif gun_high >= poz["hedef"]:
                    sonuc = "hedef"; cikis = poz["hedef"]
                if sonuc:
                    kaz = (cikis - poz["giris"]) * poz["miktar"]
                    portfoy_s += kaz
                    kapali_islem.append({
                        "Açılış"   : poz["acilis"].strftime("%d.%m.%Y %H:%M"),
                        "Kapanış"  : tarih.strftime("%d.%m.%Y %H:%M"),
                        "Kripto"   : usdt_goster(sembol),
                        "⭐"       : "⭐" if poz["top"] else "",
                        "Giriş"    : round(poz["giris"], 6),
                        "Çıkış"    : round(cikis, 6),
                        "Sonuç"    : "✅ Hedef" if sonuc=="hedef" else "❌ Stop",
                        "K/Z (USD)": round(kaz, 2),
                        "Portföy"  : round(portfoy_s, 2),
                    })
                    kapalanlar.append(poz)
            for k in kapalanlar:
                acik_pozlar.remove(k)

            # Yeni sinyaller
            if tarih in bar_sinyaller:
                for sinyal in sorted(bar_sinyaller[tarih], key=lambda x: not x["top"]):
                    if any(p["sembol"] == sinyal["sembol"] for p in acik_pozlar): continue
                    if len(acik_pozlar) >= max_pozisyon:
                        atlanan += 1; continue
                    poz_usd = portfoy_s * (poz_yuzde / 100)
                    miktar  = poz_usd / sinyal["giris"]
                    acik_pozlar.append({
                        "sembol": sinyal["sembol"], "acilis": tarih,
                        "giris" : sinyal["giris"],  "stop"  : sinyal["stop"],
                        "hedef" : sinyal["hedef"],  "miktar": miktar,
                        "top"   : sinyal["top"],
                    })

        # Açık pozisyonları kapat
        for poz in acik_pozlar:
            sembol = poz["sembol"]
            if sembol not in kripto_verileri: continue
            df    = kripto_verileri[sembol]
            son   = df.iloc[-1]
            cikis = float(son["Close"])
            kaz   = (cikis - poz["giris"]) * poz["miktar"]
            portfoy_s += kaz
            kapali_islem.append({
                "Açılış"   : poz["acilis"].strftime("%d.%m.%Y %H:%M"),
                "Kapanış"  : son.name.strftime("%d.%m.%Y %H:%M"),
                "Kripto"   : usdt_goster(sembol),
                "⭐"       : "⭐" if poz["top"] else "",
                "Giriş"    : round(poz["giris"], 6),
                "Çıkış"    : round(cikis, 6),
                "Sonuç"    : "⏳ Açık",
                "K/Z (USD)": round(kaz, 2),
                "Portföy"  : round(portfoy_s, 2),
            })

    st.session_state.update({
        "kapali"      : kapali_islem,
        "portfoy_s"   : portfoy_s,
        "portfoy0"    : portfoy,
        "atlanan"     : atlanan,
        "interval_key": interval_key,
    })

# ─── SONUÇLAR ─────────────────────────────────────────────────────────────────
if "kapali" in st.session_state:
    kapali       = st.session_state["kapali"]
    portfoy_s    = st.session_state["portfoy_s"]
    portfoy0     = st.session_state["portfoy0"]
    atlanan      = st.session_state["atlanan"]
    son_interval = st.session_state.get("interval_key", interval_key)

    if not kapali:
        st.warning("Bu dönemde sinyal bulunamadı. Parametreleri veya tarih aralığını değiştirin.")
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

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for col, lbl, val, renk in [
        (c1,"Başlangıç",    f"${portfoy0:,.2f}", "metric-neu"),
        (c2,"Bitiş",        f"${portfoy_s:,.2f}", g_renk),
        (c3,"Toplam K/Z",   f"${kz_usd:+,.2f}",  k_renk),
        (c4,"Getiri",       f"{getiri:+.1f}%",    g_renk),
        (c5,"Win Rate",     f"{wr:.1f}%",         "metric-neu"),
        (c6,"Atlanan Sinyal",str(atlanan),         "metric-neu"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{lbl}</div>
            <div class="metric-value {renk}">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    c7,c8,c9 = st.columns(3)
    for col, lbl, val, renk in [
        (c7,"Toplam İşlem",    str(toplam),        "metric-neu"),
        (c8,"Kazanan (Hedef)", str(len(kazanan)),  "metric-pos"),
        (c9,"Kaybeden (Stop)", str(len(kaybeden)), "metric-neg"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{lbl}</div>
            <div class="metric-value {renk}">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

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
        fig.add_hline(y=portfoy0, line_dash="dash", line_color="#64748b",
                      annotation_text=f"Başlangıç: ${portfoy0:,.2f}")
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="#0d0f14",
            plot_bgcolor="#0d0f14", height=400,
            margin=dict(l=10,r=10,t=20,b=10),
            yaxis=dict(gridcolor="#1e293b", tickformat=",.2f", tickprefix="$"),
            xaxis=dict(gridcolor="#1e293b"), showlegend=False,
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
            text=[f"${v:+,.2f}" for v in aylik["K/Z (USD)"]],
            textposition="outside"
        ))
        fig2.update_layout(
            template="plotly_dark", paper_bgcolor="#0d0f14",
            plot_bgcolor="#0d0f14", height=350,
            margin=dict(l=10,r=10,t=20,b=10),
            yaxis=dict(gridcolor="#1e293b", tickformat=",.2f"),
            xaxis=dict(gridcolor="#1e293b"), showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

        aylik_g = aylik.copy()
        aylik_g["Ay"]         = aylik_g["Ay"].astype(str)
        aylik_g["K/Z (USD)"]  = aylik_g["K/Z (USD)"].apply(lambda x: f"${x:+,.2f}")
        aylik_g["Kümülatif"]  = aylik_g["Kümülatif"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(aylik_g, use_container_width=True, hide_index=True)

    with tab3:
        df_g = df_i.drop(columns=["Kapanış_dt","Ay"], errors="ignore").copy()
        df_g["K/Z (USD)"] = df_g["K/Z (USD)"].apply(lambda x: f"${x:+,.2f}")
        df_g["Portföy"]   = df_g["Portföy"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_g, use_container_width=True, hide_index=True)
        csv = df_i.drop(columns=["Kapanış_dt","Ay"], errors="ignore").to_csv(
            index=False).encode("utf-8-sig")
        st.download_button("⬇️ CSV İndir", data=csv,
            file_name=f"kripto_backtest_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv")

    st.markdown("---")
    st.caption("⚠️ Bu analiz yatırım tavsiyesi değildir. Kripto piyasaları yüksek risk içerir.")

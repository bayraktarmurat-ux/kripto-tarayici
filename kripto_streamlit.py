import streamlit as st
import pandas as pd
import numpy as np
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
TOP_KRIPTO = {
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD",
    "ADA-USD","AVAX-USD","DOT-USD","MATIC-USD","LINK-USD",
    "LTC-USD","ATOM-USD","UNI-USD","NEAR-USD","APT-USD",
    "OP-USD","ARB-USD","INJ-USD","SUI-USD","TIA-USD",
}

def usdt_goster(sembol):
    return sembol.replace("-USD", "USDT")

def tv_link(sembol):
    return f"https://tr.tradingview.com/chart/?symbol={usdt_goster(sembol)}"

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

# ─── ZAMAN ARALIĞI ────────────────────────────────────────────────────────────
INTERVAL_SECENEKLER = {
    "1 Saatlik (1h)":  {"interval": "1h",  "period": "60d",  "min_bar": 100},
    "4 Saatlik (4h)":  {"interval": "4h",  "period": "180d", "min_bar": 80},
    "Günlük (1d)":     {"interval": "1d",  "period": "365d", "min_bar": 60},
    "Haftalık (1w)":   {"interval": "1wk", "period": "730d", "min_bar": 40},
}

# ─── YARDIMCI FONKSİYONLAR ────────────────────────────────────────────────────
def s(x):
    """Her türlü yfinance çıktısını düz float Series'e dönüştür."""
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    if hasattr(x, "squeeze"):
        x = x.squeeze()
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    return pd.Series(x.values.flatten(), index=x.index, dtype=float)

def ema_s(seri, n):
    x = s(seri)
    return pd.Series(x.ewm(span=n, adjust=False).mean().values.flatten(),
                     index=x.index, dtype=float)

def rsi_hesapla(close_s, n=14):
    close_s = s(close_s)
    delta   = close_s.diff()
    gain    = delta.clip(lower=0)
    loss    = (-delta).clip(lower=0)
    avg_g   = gain.ewm(alpha=1/n, adjust=False).mean()
    avg_l   = loss.ewm(alpha=1/n, adjust=False).mean()
    rs      = avg_g / (avg_l + 1e-9)
    return pd.Series((100 - 100 / (1 + rs)).values.flatten(),
                     index=close_s.index, dtype=float)

def atr_s(df_in, n=14):
    c  = s(df_in["Close"]); h = s(df_in["High"]); l = s(df_in["Low"])
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return pd.Series(tr.ewm(span=n, adjust=False).mean().values.flatten(),
                     index=c.index, dtype=float)

def veri_cek(ticker, interval_cfg):
    try:
        df = yf.download(ticker, period=interval_cfg["period"],
                         interval=interval_cfg["interval"],
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < interval_cfg["min_bar"]:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        for col in df.columns:
            df[col] = s(df[col])
        if hasattr(df.index, "tz") and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return None

# ─── PAZAR FİLTRESİ ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def pazar_kontrol(interval_key, ema_uzun):
    try:
        cfg = INTERVAL_SECENEKLER[interval_key]
        df  = yf.download("BTC-USD", period=cfg["period"],
                          interval=cfg["interval"], progress=False, auto_adjust=True)
        if df.empty: return None, None, None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        c      = s(df["Close"])
        ema200 = pd.Series(c.ewm(span=ema_uzun, adjust=False).mean().values.flatten(),
                           index=c.index, dtype=float)
        son_c  = float(c.iloc[-1]); son_e = float(ema200.iloc[-1])
        return son_c > son_e, son_c, son_e, (son_c - son_e) / son_e * 100
    except Exception:
        return None, None, None, None

# ─── STRATEJİ: RSI + EMA TREND + HACİM BREAKOUT ──────────────────────────────
def sinyal_tara(df, params):
    """
    4 koşul aynı anda sağlanmalı:
      1. EMA kısa > EMA uzun  → Trend yukarı
      2. RSI_min < RSI < RSI_max → Momentum başlıyor, aşırı alım yok
      3. Kapanış > son N barın en yüksek kapanışı → Breakout
      4. Hacim > N-bar ort * katsayı → Güçlü katılım
    """
    ema_kisa  = params["ema_kisa"];   ema_uzun   = params["ema_uzun"]
    rsi_per   = params["rsi_periyot"]; rsi_min    = params["rsi_min"]
    rsi_max   = params["rsi_max"];    brk_per    = params["breakout_periyot"]
    hac_per   = params["hacim_periyot"]; hac_kat  = params["hacim_katsayi"]
    atr_per   = params["atr_periyot"]; atr_kat   = params["atr_katsayi"]
    rr        = params["rr_katsayi"]

    try:
        df = df.copy()
        for col in ["Open","High","Low","Close","Volume"]:
            if col in df.columns:
                df[col] = s(df[col])

        close  = s(df["Close"])
        volume = s(df["Volume"])

        ema_k = ema_s(close, ema_kisa)
        ema_u = ema_s(close, ema_uzun)
        rsi   = rsi_hesapla(close, rsi_per)
        atr   = atr_s(df, atr_per)

        # Breakout: son N barın en yüksek kapanışı (mevcut bar hariç)
        brk_seviye = close.shift(1).rolling(brk_per).max()
        # Hacim ortalaması (mevcut bar hariç)
        hac_ort    = volume.shift(1).rolling(hac_per).mean()

        if len(df) < max(ema_uzun, brk_per, hac_per) + 5:
            return None

        son_close   = float(close.iloc[-1])
        son_ema_k   = float(ema_k.iloc[-1])
        son_ema_u   = float(ema_u.iloc[-1])
        son_rsi     = float(rsi.iloc[-1])
        son_brk     = float(brk_seviye.iloc[-1])
        son_vol     = float(volume.iloc[-1])
        son_hac_ort = float(hac_ort.iloc[-1])
        son_atr     = float(atr.iloc[-1])

        if any(np.isnan(v) for v in [son_ema_k, son_ema_u, son_rsi,
                                      son_brk, son_hac_ort, son_atr]):
            return None

        # 1. Trend filtresi
        if son_ema_k <= son_ema_u:
            return None
        # 2. RSI bandı
        if not (rsi_min < son_rsi < rsi_max):
            return None
        # 3. Fiyat breakout
        if son_close <= son_brk:
            return None
        # 4. Hacim onayı
        if son_vol < son_hac_ort * hac_kat:
            return None

        stop  = round(son_close - atr_kat * son_atr, 8)
        hedef = round(son_close + rr * atr_kat * son_atr, 8)
        if son_close - stop <= 0:
            return None

        return {
            "Son Kapanis": round(son_close, 8),
            "RSI"        : round(son_rsi, 1),
            "Hacim_Kat"  : round(son_vol / son_hac_ort, 2),
            "EMA_Kisa"   : round(son_ema_k, 8),
            "EMA_Uzun"   : round(son_ema_u, 8),
            "Stop"       : stop,
            "Stop%"      : round((son_close - stop) / son_close * 100, 2),
            "Hedef"      : hedef,
            "Hedef%"     : round((hedef - son_close) / son_close * 100, 2),
            "ATR"        : round(son_atr, 8),
        }
    except Exception:
        return None

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Ayarlar")

st.sidebar.markdown("### ⏱️ Zaman Aralığı")
interval_key = st.sidebar.selectbox(
    "Zaman Dilimi", options=list(INTERVAL_SECENEKLER.keys()), index=1,
    help="Tarama ve grafik için kullanılacak mum aralığı"
)
interval_cfg = INTERVAL_SECENEKLER[interval_key]

st.sidebar.markdown("### 💰 Portföy")
portfoy    = st.sidebar.number_input("Portföy (USD)", min_value=100,
                                      max_value=10_000_000, value=10_000, step=100)
risk_yuzde = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0, 0.5)
rr_katsayi = st.sidebar.slider("R:R Katsayısı", 1.0, 5.0, 2.0, 0.5)

st.sidebar.markdown("### 📈 EMA Trend")
ema_kisa = st.sidebar.slider("EMA Kısa", 10, 100, 50, 5)
ema_uzun = st.sidebar.slider("EMA Uzun", 50, 300, 200, 10)

st.sidebar.markdown("### 📊 RSI")
rsi_periyot = st.sidebar.slider("RSI Periyodu", 7, 21, 14, 1)
rsi_min     = st.sidebar.slider("RSI Alt Sınır", 20, 60, 40, 5,
                                 help="Bu değerin altındaki RSI'lar atlanır")
rsi_max     = st.sidebar.slider("RSI Üst Sınır", 50, 85, 70, 5,
                                 help="Bu değerin üstündeki RSI'lar atlanır (aşırı alım)")

st.sidebar.markdown("### 🚀 Breakout")
breakout_periyot = st.sidebar.slider("Breakout Periyodu (bar)", 5, 50, 20, 5,
                                      help="Kaç barın en yüksek kapanışı kırılmalı?")

st.sidebar.markdown("### 📦 Hacim")
hacim_periyot = st.sidebar.slider("Hacim Ort. Periyodu", 5, 50, 20, 5)
hacim_katsayi = st.sidebar.slider("Hacim Katsayısı", 1.0, 4.0, 1.5, 0.5,
                                   help="Hacim, ortalamanın kaç katı olmalı?")

st.sidebar.markdown("### 🛡️ ATR Stop")
atr_katsayi = st.sidebar.slider("ATR Katsayısı", 1.0, 5.0, 2.0, 0.5,
                                  help="Kripto için 2-3 arası önerilir")
atr_periyot = st.sidebar.slider("ATR Periyodu", 7, 21, 14, 1)

params = {
    "ema_kisa"         : ema_kisa,
    "ema_uzun"         : ema_uzun,
    "rsi_periyot"      : rsi_periyot,
    "rsi_min"          : rsi_min,
    "rsi_max"          : rsi_max,
    "breakout_periyot" : breakout_periyot,
    "hacim_periyot"    : hacim_periyot,
    "hacim_katsayi"    : hacim_katsayi,
    "atr_periyot"      : atr_periyot,
    "atr_katsayi"      : atr_katsayi,
    "rr_katsayi"       : rr_katsayi,
}

# ─── ANA SAYFA ────────────────────────────────────────────────────────────────
st.title("🪙 Kripto Sinyal Tarayıcı")
st.caption(f"RSI + EMA Trend + Hacim Breakout | R:R 1:{rr_katsayi:.0f} | {interval_key}")

with st.expander("ℹ️ Strateji Açıklaması", expanded=False):
    st.markdown(f"""
**RSI + EMA Trend + Hacim Breakout Stratejisi**

Bir kripto aşağıdaki **4 koşulu aynı anda** sağladığında sinyal üretilir:

| Koşul | Parametre | Açıklama |
|---|---|---|
| 📈 **Trend** | EMA{ema_kisa} > EMA{ema_uzun} | Ana trend yukarı yönlü |
| 📊 **Momentum** | RSI {rsi_min}–{rsi_max} | Ne aşırı alım ne aşırı satım |
| 🚀 **Breakout** | Kapanış > son {breakout_periyot} barın zirvesi | Direnç kırıldı |
| 📦 **Hacim** | Hacim > {hacim_katsayi}x ortalama | Güçlü katılım var |

**Stop:** ATR × {atr_katsayi} aşağıda &nbsp;|&nbsp; **Hedef:** Stop mesafesinin {rr_katsayi:.0f}x'i yukarıda
""")

# ─── PAZAR DURUMU ─────────────────────────────────────────────────────────────
aktif, btc_fiyat, btc_ema_val, btc_fark = pazar_kontrol(interval_key, ema_uzun)

if aktif is None:
    st.warning("⚠️ BTC verisi alınamadı — pazar filtresi devre dışı.")
    pazar_gecti = True
elif aktif:
    st.success(
        f"✅ **BTC Boğa Trendi** ({interval_key}) — "
        f"BTC: ${btc_fiyat:,.2f}  |  EMA{ema_uzun}: ${btc_ema_val:,.2f}  |  "
        f"Fark: **+{btc_fark:.1f}%**"
    )
    pazar_gecti = True
else:
    st.error(
        f"🚫 **BTC Ayı Trendi** ({interval_key}) — "
        f"BTC: ${btc_fiyat:,.2f}  |  EMA{ema_uzun}: ${btc_ema_val:,.2f}  |  "
        f"Fark: **{btc_fark:.1f}%** — Strateji pasif."
    )
    pazar_gecti = False

st.markdown("---")

pazar_bypass = st.sidebar.checkbox("⚠️ Pazar filtresini atla", value=False)
tara_disabled = not pazar_gecti
if pazar_bypass:
    tara_disabled = False
    st.warning("⚠️ Pazar filtresi devre dışı bırakıldı.")

if st.button("🔍 Tara", use_container_width=True, type="primary", disabled=tara_disabled):
    risk_usd  = portfoy * risk_yuzde / 100
    sinyaller = []
    hatalar   = []

    progress = st.progress(0, text="Tarama başlıyor...")
    for i, kripto in enumerate(KRIPTOLAR):
        progress.progress((i+1)/len(KRIPTOLAR),
                          text=f"Taraniyor: {usdt_goster(kripto)} ({i+1}/{len(KRIPTOLAR)})")
        df = veri_cek(kripto, interval_cfg)
        if df is None:
            hatalar.append(kripto); continue
        sonuc = sinyal_tara(df, params)
        if sonuc is None: continue

        kapanis    = sonuc["Son Kapanis"]
        stop       = sonuc["Stop"]
        risk_birim = kapanis - stop
        if risk_birim <= 0: continue
        miktar    = risk_usd / risk_birim
        giris_usd = round(miktar * kapanis, 2)

        sinyaller.append({
            "⭐"        : "⭐" if kripto in TOP_KRIPTO else "",
            "Kripto"   : kripto,
            "Fiyat"    : kapanis,
            "RSI"      : sonuc["RSI"],
            "Hac.Kat"  : sonuc["Hacim_Kat"],
            "Stop"     : stop,
            "Stop%"    : sonuc["Stop%"],
            "Hedef"    : sonuc["Hedef"],
            "Hedef%"   : sonuc["Hedef%"],
            "ATR"      : sonuc["ATR"],
            "Miktar"   : round(miktar, 6),
            "Giriş USD": giris_usd,
            "Risk USD" : round(risk_usd, 2),
        })

    progress.empty()
    st.session_state["sinyaller"]    = sinyaller
    st.session_state["hatalar"]      = hatalar
    st.session_state["tarih"]        = datetime.now().strftime("%d.%m.%Y %H:%M")
    st.session_state["interval_key"] = interval_key
    st.session_state["params"]       = params

# ─── SONUÇLAR ─────────────────────────────────────────────────────────────────
if "sinyaller" in st.session_state:
    sinyaller    = st.session_state["sinyaller"]
    tarih        = st.session_state["tarih"]
    hatalar      = st.session_state.get("hatalar", [])
    son_interval = st.session_state.get("interval_key", interval_key)
    p            = st.session_state.get("params", params)

    st.markdown(f"### Tarama Sonuçları — {tarih} | {son_interval}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sinyal Sayısı",  len(sinyaller))
    c2.metric("Taranan Kripto", len(KRIPTOLAR))
    c3.metric("Veri Hatası",    len(hatalar))
    c4.metric("Pazar",          "✅ Boğa" if pazar_gecti else "🚫 Ayı")

    if hatalar:
        with st.expander(f"⚠️ Veri alınamayan {len(hatalar)} kripto"):
            cols = st.columns(6)
            for i, k in enumerate(sorted(hatalar)):
                cols[i % 6].markdown(f"[{usdt_goster(k)}]({tv_link(k)})")

    if not sinyaller:
        st.warning("Seçilen parametrelerle sinyal bulunamadı. "
                   "RSI aralığını genişletmeyi veya Breakout periyodunu azaltmayı deneyin.")
    else:
        df_sonuc = pd.DataFrame(sinyaller).sort_values(
            by=["⭐","Hac.Kat"], ascending=[False, False]
        )

        top_var = df_sonuc[df_sonuc["⭐"] == "⭐"]
        if len(top_var):
            st.success(
                f"⭐ **{len(top_var)} büyük cap!** "
                f"({', '.join(top_var['Kripto'].apply(usdt_goster).tolist())})"
            )

        df_goster = df_sonuc.copy()
        df_goster["Kripto"]    = df_goster["Kripto"].apply(usdt_goster)
        df_goster["Stop%"]     = df_goster["Stop%"].apply(lambda x: f"-%{x}")
        df_goster["Hedef%"]    = df_goster["Hedef%"].apply(lambda x: f"+%{x}")
        df_goster["📈 Grafik"] = df_sonuc["Kripto"].apply(tv_link)

        st.dataframe(df_goster, use_container_width=True, hide_index=True,
                     column_config={"📈 Grafik": st.column_config.LinkColumn(
                         "📈 Grafik", display_text="TradingView →")})

        c1, c2 = st.columns(2)
        c1.metric("Toplam Sermaye Kullanımı", f"${df_sonuc['Giriş USD'].sum():,.2f}")
        c2.metric("Toplam Risk",
                  f"${df_sonuc['Risk USD'].sum():,.2f}  "
                  f"(%{df_sonuc['Risk USD'].sum()/portfoy*100:.1f} portföy)")

        csv = df_sonuc.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ CSV İndir", data=csv,
            file_name=f"kripto_sinyaller_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv")

        st.markdown("---")
        st.markdown("### 📊 Grafik")

        sinyal_map   = {usdt_goster(r["Kripto"]): r["Kripto"] for r in sinyaller}
        secili_label = st.selectbox("Kripto seçin:", list(sinyal_map.keys()))
        secili       = sinyal_map[secili_label]
        df_grafik    = veri_cek(secili, interval_cfg)
        sel_sin      = next(r for r in sinyaller if r["Kripto"] == secili)

        if df_grafik is not None:
            c_g     = s(df_grafik["Close"])
            v_g     = s(df_grafik["Volume"])
            ema_k_g = ema_s(c_g, p["ema_kisa"])
            ema_u_g = ema_s(c_g, p["ema_uzun"])
            rsi_g   = rsi_hesapla(c_g, p["rsi_periyot"])
            hac_g   = v_g.rolling(p["hacim_periyot"]).mean()

            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True,
                row_heights=[0.55, 0.25, 0.20],
                vertical_spacing=0.03,
                subplot_titles=["Fiyat & EMA", "RSI", "Hacim"]
            )

            fig.add_trace(go.Candlestick(
                x=df_grafik.index,
                open=s(df_grafik["Open"]), high=s(df_grafik["High"]),
                low=s(df_grafik["Low"]),   close=c_g,
                name="Fiyat",
                increasing_line_color="#22c55e",
                decreasing_line_color="#ef4444",
            ), row=1, col=1)

            for vals, renk, isim in [
                (ema_k_g, "#38bdf8", f"EMA{p['ema_kisa']}"),
                (ema_u_g, "#f472b6", f"EMA{p['ema_uzun']}"),
            ]:
                fig.add_trace(go.Scatter(x=df_grafik.index, y=vals,
                    name=isim, line=dict(color=renk, width=1.5)), row=1, col=1)

            son_tarih = df_grafik.index[-1]
            off_h = {"1h":24,"4h":6,"1d":1,"1wk":1}.get(interval_cfg["interval"], 1)
            bitis = son_tarih + timedelta(hours=24 * off_h * 5)

            for seviye, renk, isim in [
                (sel_sin["Stop"],  "#ef4444", "Stop"),
                (sel_sin["Hedef"], "#22c55e", "Hedef"),
            ]:
                fig.add_shape(type="line", x0=son_tarih, x1=bitis,
                              y0=seviye, y1=seviye,
                              line=dict(color=renk, width=1.5, dash="dash"), row=1, col=1)
                fig.add_annotation(x=bitis, y=seviye,
                                   text=f"{isim} {seviye:.4g}",
                                   showarrow=False, font=dict(color=renk, size=10),
                                   xanchor="left", row=1, col=1)

            # RSI
            fig.add_trace(go.Scatter(x=df_grafik.index, y=rsi_g,
                name="RSI", line=dict(color="#a78bfa", width=1.5)), row=2, col=1)
            for lvl, clr in [(70,"#ef4444"),(30,"#22c55e"),
                              (p["rsi_min"],"#fbbf24"),(p["rsi_max"],"#fbbf24")]:
                fig.add_hline(y=lvl, line_dash="dot", line_color=clr,
                              line_width=1, row=2, col=1)
            fig.add_trace(go.Scatter(
                x=list(df_grafik.index) + list(df_grafik.index[::-1]),
                y=[p["rsi_max"]]*len(df_grafik) + [p["rsi_min"]]*len(df_grafik),
                fill="toself", fillcolor="rgba(251,191,36,0.08)",
                line=dict(width=0), showlegend=False, name="RSI Bant"
            ), row=2, col=1)

            # Hacim
            vol_colors = ["#22c55e" if float(c_g.iloc[i]) >= float(s(df_grafik["Open"]).iloc[i])
                          else "#ef4444" for i in range(len(df_grafik))]
            fig.add_trace(go.Bar(x=df_grafik.index, y=v_g,
                name="Hacim", marker_color=vol_colors, opacity=0.7), row=3, col=1)
            fig.add_trace(go.Scatter(x=df_grafik.index, y=hac_g,
                name="Hac.Ort", line=dict(color="#f59e0b", width=1.5, dash="dash")),
                row=3, col=1)

            fig.add_vline(x=son_tarih, line_dash="dot",
                          line_color="#facc15", line_width=1, row="all", col=1)
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="#0d0f14",
                plot_bgcolor="#0d0f14", height=750, showlegend=True,
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=120, t=40, b=10),
                font=dict(family="Consolas", size=11),
                title=dict(text=f"{usdt_goster(secili)} — {son_interval}",
                           font=dict(size=14)),
            )
            fig.update_yaxes(gridcolor="#1e293b")
            fig.update_xaxes(gridcolor="#1e293b")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"""
| | |
|---|---|
| **Kripto** | {usdt_goster(secili)} |
| **Zaman Dilimi** | {son_interval} |
| **Giriş** | ${sel_sin['Fiyat']:.6g} |
| **RSI** | {sel_sin['RSI']} |
| **Hacim** | {sel_sin['Hac.Kat']}x ortalama |
| **Stop** | ${sel_sin['Stop']:.6g} (-%{sel_sin['Stop%']}) |
| **Hedef** | ${sel_sin['Hedef']:.6g} (+%{sel_sin['Hedef%']}) |
| **R:R** | 1:{p['rr_katsayi']:.0f} |
| **Miktar** | {sel_sin['Miktar']:.6f} adet |
| **Giriş Tutarı** | ${sel_sin['Giriş USD']:,.2f} |
| **Risk** | ${sel_sin['Risk USD']:,.2f} |
""")

    st.markdown("---")
    st.caption("⚠️ Bu analiz yatırım tavsiyesi değildir. Kripto piyasaları yüksek risk içerir.")

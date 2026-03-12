import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Kripto Sinyal Tarayici",
    page_icon="coin",
    layout="wide",
    initial_sidebar_state="expanded",
)

TOP500_COINLER = [
    "BTC","ETH","BNB","XRP","SOL","DOGE","ADA","TRX","AVAX","SHIB",
    "TON","DOT","LINK","MATIC","LTC","BCH","NEAR","UNI","ICP","APT",
    "XLM","ETC","STX","FIL","HBAR","VET","MKR","ATOM","INJ","OP",
    "ARB","GRT","ALGO","SAND","MANA","AXS","THETA","EGLD","FLOW","XTZ",
    "AAVE","RUNE","QNT","SNX","FTM","CAKE","CHZ","ENJ","1INCH","BAT",
    "ZEC","DASH","NEO","WAVES","IOTA","KAVA","CELO","CRV","COMP","YFI",
    "SUSHI","UMA","BAL","REN","SKL","OCEAN","BAND","NKN","OXT","ANKR",
    "STORJ","CELR","CTSI","MTL","DENT","HOT","WIN","BTT","JST","SUN",
    "TFUEL","ONE","IOTX","ZIL","DGB","SC","RVN","ROSE","CFX","ID",
    "BLUR","APE","GAL","GMT","GST","SLP","LOKA","PLA","ALICE","TLM",
    "DYDX","PERP","BICO","RAD","SPELL","CVX","FXS","LQTY","MASK","AGLD",
    "ENS","BOND","INDEX","BNT","REQ","NMR","RLC","OGN","LPT","GTC",
    "AUDIO","JASMY","RNDR","SUPER","RARE","XYO","ARDR","LSK","HIVE","BEAM",
    "ZRX","KNC","LRC","POWR","DCR","KLAY","BORA","TWT","BNX","XVS",
    "ALPACA","BAKE","DODO","REEF","GALA","ILV","GODS","IMX","YGG","GHST",
    "MOBOX","MBOX","TKO","PROM","TVK","ULTRA","SOLVE","MBL","DOCK","FRONT",
    "HARD","LIT","DEGO","BEL","VITE","TROY","FIRO","AERGO","COTI","ARPA",
    "IRIS","TRB","TORN","BADGER","CREAM","ALPHA","QUICK","ROUTE","PLOT",
    "POLS","ORION","LAYER","LEASH","BONE","FLOKI","ELON","AKITA","GMX",
    "GNS","VELA","KWENTA","LYRA","PREMIA","ACH","AGIX","FET","DIA","UTK",
    "IDEX","ORAI","NANO","XDC","CSPR","MINA","CKB","ONE","QTUM","ONT",
    "ICX","EOS","XEM","ARK","STRAT","PIVX","SYS","NXS","APT","SUI",
    "SEI","TIA","PYTH","JTO","MANTA","ALT","PIXEL","PORTAL","STRK","DYM",
    "AXL","OMNI","REZ","BB","NOT","IO","ZK","LISTA","ZRO","BANANA",
]

seen = set()
COINLER = []
for c in TOP500_COINLER:
    if c not in seen:
        seen.add(c)
        COINLER.append(c)

def veri_cek(symbol, limit=250):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol + "USDT", "interval": "1d", "limit": limit}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            raise Exception("Binance hata")
        data = r.json()
        if not data or len(data) < 60:
            return None
        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qv","trades","tbbav","tbqav","ignore"
        ])
        df["time"]   = pd.to_datetime(df["time"], unit="ms")
        for col in ["open","high","low","close","volume"]:
            df[col] = df[col].astype(float)
        df.set_index("time", inplace=True)
        return df
    except Exception:
        pass
    try:
        import yfinance as yf
        df = yf.download(symbol + "-USD", period="300d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 60:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        df = df[["open","high","low","close","volume"]].dropna()
        return df if len(df) >= 60 else None
    except Exception:
        return None

def ema(seri, periyot):
    return seri.ewm(span=periyot, adjust=False).mean()

def atr_hesapla(df, periyot=14):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift(1)).abs()
    lc = (df["low"]  - df["close"].shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=periyot, adjust=False).mean()

def stokastik_hesapla(df, k=5, d=3, smooth=3):
    ll    = df["low"].rolling(k).min()
    hh    = df["high"].rolling(k).max()
    k_raw = 100 * (df["close"] - ll) / (hh - ll + 1e-9)
    k_sm  = k_raw.rolling(smooth).mean()
    d_sm  = k_sm.rolling(d).mean()
    return k_sm, d_sm

def indikatör_hesapla(df, params):
    df = df.copy()
    df["EMA20"]  = ema(df["close"], 20)
    df["EMA50"]  = ema(df["close"], 50)
    df["EMA100"] = ema(df["close"], 100)
    df["EMA200"] = ema(df["close"], 200)
    df["ATR"]    = atr_hesapla(df, params["atr_periyot"])
    df["K"], df["D"] = stokastik_hesapla(df)
    return df

def alis_sinyali(df, params):
    tolerans  = params["ema_tolerans"] / 100
    atr_kat   = params["atr_katsayi"]
    rr        = params["rr_katsayi"]

    son   = df.iloc[-1]
    once  = df.iloc[-2]
    kapanis = float(son["close"])

    # Yukselis trendi
    if not (son["EMA20"] > son["EMA50"] > son["EMA100"] > son["EMA200"]):
        return None
    # Stokastik asiri satim + yukari kesisim
    if not (float(once["K"]) < float(once["D"]) and
            float(son["K"])  > float(son["D"])  and
            float(son["K"])  < params["stok_esik_alt"]):
        return None

    ema_destek = None
    for col in ["EMA20","EMA50","EMA100","EMA200"]:
        ema_val = float(son[col])
        if abs(kapanis - ema_val) / ema_val <= tolerans:
            ema_destek = col
            break
    if ema_destek is None:
        return None

    atr_val = float(son["ATR"])
    stop    = round(kapanis - atr_kat * atr_val, 6)
    hedef   = round(kapanis + rr * atr_kat * atr_val, 6)

    return {
        "Yon":        "ALIS",
        "Kapanis":    round(kapanis, 6),
        "EMA Destek": ema_destek,
        "K":          round(float(son["K"]), 2),
        "Stop":       stop,
        "Hedef":      hedef,
        "ATR":        round(atr_val, 6),
    }

def satis_sinyali(df, params):
    tolerans  = params["ema_tolerans"] / 100
    atr_kat   = params["atr_katsayi"]
    rr        = params["rr_katsayi"]

    son   = df.iloc[-1]
    once  = df.iloc[-2]
    kapanis = float(son["close"])

    # Dusus trendi
    if not (son["EMA20"] < son["EMA50"] < son["EMA100"] < son["EMA200"]):
        return None
    # Stokastik asiri alim + asagi kesisim
    if not (float(once["K"]) > float(once["D"]) and
            float(son["K"])  < float(son["D"])  and
            float(son["K"])  > params["stok_esik_ust"]):
        return None

    ema_direnc = None
    for col in ["EMA20","EMA50","EMA100","EMA200"]:
        ema_val = float(son[col])
        if abs(kapanis - ema_val) / ema_val <= tolerans:
            ema_direnc = col
            break
    if ema_direnc is None:
        return None

    atr_val = float(son["ATR"])
    stop    = round(kapanis + atr_kat * atr_val, 6)
    hedef   = round(kapanis - rr * atr_kat * atr_val, 6)

    return {
        "Yon":         "SHORT",
        "Kapanis":     round(kapanis, 6),
        "EMA Direnc":  ema_direnc,
        "K":           round(float(son["K"]), 2),
        "Stop":        stop,
        "Hedef":       hedef,
        "ATR":         round(atr_val, 6),
    }

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.title("Ayarlar")
portfoy      = st.sidebar.number_input("Portfolyo (USDT)", min_value=100, max_value=1000000, value=10000, step=100)
risk_yuzde   = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0, 0.5)
rr_katsayi   = st.sidebar.slider("R:R Katsayisi", 1.0, 5.0, 2.5, 0.5)
atr_katsayi  = st.sidebar.slider("ATR Katsayisi", 0.5, 3.0, 1.5, 0.5)
atr_periyot  = st.sidebar.slider("ATR Periyodu", 7, 21, 14, 1)
ema_tolerans = st.sidebar.slider("EMA Tolerans %", 0.5, 5.0, 2.0, 0.5)
stok_esik_alt = st.sidebar.slider("Stokastik Esik (Alis)", 10, 40, 20, 5)
stok_esik_ust = st.sidebar.slider("Stokastik Esik (Short)", 60, 90, 80, 5)

params = {
    "ema_tolerans":  ema_tolerans,
    "stok_esik_alt": stok_esik_alt,
    "stok_esik_ust": stok_esik_ust,
    "atr_periyot":   atr_periyot,
    "atr_katsayi":   atr_katsayi,
    "rr_katsayi":    rr_katsayi,
}

# ─── ANA SAYFA ────────────────────────────────────────────────────────────────
st.title("Kripto Sinyal Tarayici")
st.caption("Alis: EMA20>50>100>200 + Stokastik asiri satim | Short: EMA20<50<100<200 + Stokastik asiri alim")

if st.button("Tara", use_container_width=True, type="primary"):
    risk_usdt   = portfoy * risk_yuzde / 100
    alis_list   = []
    short_list  = []

    progress = st.progress(0, text="Tarama basliyor...")
    toplam = len(COINLER)

    for i, coin in enumerate(COINLER):
        progress.progress((i + 1) / toplam,
                          text="Taraniyor: " + coin + " (" + str(i+1) + "/" + str(toplam) + ")")
        df = veri_cek(coin)
        if df is None:
            continue
        try:
            df = indikatör_hesapla(df, params)
            a  = alis_sinyali(df, params)
            s  = satis_sinyali(df, params)
        except Exception:
            continue

        for sonuc, liste in [(a, alis_list), (s, short_list)]:
            if sonuc is None:
                continue
            kapanis   = sonuc["Kapanis"]
            stop      = sonuc["Stop"]
            risk_coin = abs(kapanis - stop)
            if risk_coin <= 0:
                continue
            miktar     = round(risk_usdt / risk_coin, 6)
            giris_usdt = round(miktar * kapanis, 2)
            row = {
                "Coin":       coin,
                "Yon":        sonuc["Yon"],
                "Fiyat":      kapanis,
                "EMA":        sonuc.get("EMA Destek", sonuc.get("EMA Direnc","")),
                "%K":         sonuc["K"],
                "Stop":       stop,
                "Hedef":      sonuc["Hedef"],
                "Miktar":     miktar,
                "Giris USDT": giris_usdt,
                "Risk USDT":  round(risk_usdt, 2),
            }
            liste.append(row)

    progress.empty()
    st.session_state["alis_list"]  = sorted(alis_list,  key=lambda x: x["%K"])
    st.session_state["short_list"] = sorted(short_list, key=lambda x: x["%K"], reverse=True)
    st.session_state["kripto_tarih"] = datetime.now().strftime("%d.%m.%Y %H:%M")

# ─── SONUCLAR ─────────────────────────────────────────────────────────────────
if "alis_list" in st.session_state:
    alis_list  = st.session_state["alis_list"]
    short_list = st.session_state["short_list"]
    tarih      = st.session_state["kripto_tarih"]

    st.markdown("### Tarama Sonuclari - " + tarih)
    col1, col2, col3 = st.columns(3)
    col1.metric("Alis Sinyali",  len(alis_list),  delta=None)
    col2.metric("Short Sinyali", len(short_list), delta=None)
    col3.metric("Portfolyo",     str(portfoy) + " USDT")

    tab1, tab2 = st.tabs(["Alis Sinyalleri", "Short Sinyalleri"])

    for tab, liste, label in [
        (tab1, alis_list,  "alis"),
        (tab2, short_list, "short"),
    ]:
        with tab:
            if len(liste) == 0:
                st.info("Sinyal bulunamadi.")
            else:
                df_sonuc = pd.DataFrame(liste)
                st.dataframe(df_sonuc, use_container_width=True, hide_index=True)
                csv = df_sonuc.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="CSV Indir",
                    data=csv,
                    file_name="kripto_" + label + "_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv",
                    mime="text/csv",
                    key="csv_" + label,
                )

    tum_liste = alis_list + short_list
    if tum_liste:
        st.markdown("---")
        st.markdown("### Grafik")
        secili = st.selectbox("Coin secin:", [r["Coin"] for r in tum_liste])
        df_grafik = veri_cek(secili, limit=150)

        if df_grafik is not None:
            df_grafik = indikatör_hesapla(df_grafik, params)
            secili_sinyal = next(r for r in tum_liste if r["Coin"] == secili)

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.7, 0.3], vertical_spacing=0.04)

            fig.add_trace(go.Candlestick(
                x=df_grafik.index,
                open=df_grafik["open"], high=df_grafik["high"],
                low=df_grafik["low"],   close=df_grafik["close"],
                name="Fiyat",
                increasing_line_color="#22c55e",
                decreasing_line_color="#ef4444",
            ), row=1, col=1)

            for col_name, renk, gw in [
                ("EMA20","#38bdf8",1.5), ("EMA50","#f59e0b",1.5),
                ("EMA100","#a78bfa",1),  ("EMA200","#f472b6",1),
            ]:
                fig.add_trace(go.Scatter(
                    x=df_grafik.index, y=df_grafik[col_name],
                    name=col_name, line=dict(color=renk, width=gw)
                ), row=1, col=1)

            stop_renk  = "#ef4444" if secili_sinyal["Yon"] == "ALIS" else "#22c55e"
            hedef_renk = "#22c55e" if secili_sinyal["Yon"] == "ALIS" else "#ef4444"

            for seviye, renk, isim in [
                (secili_sinyal["Stop"],  stop_renk,  "Stop"),
                (secili_sinyal["Hedef"], hedef_renk, "Hedef"),
            ]:
                fig.add_hline(y=seviye, line_dash="dash", line_color=renk, row=1, col=1)
                fig.add_annotation(x=df_grafik.index[-1], y=seviye,
                    text=isim + " " + str(seviye),
                    showarrow=False, font=dict(color=renk, size=11),
                    xanchor="left", row=1, col=1)

            fig.add_trace(go.Scatter(x=df_grafik.index, y=df_grafik["K"],
                name="%K", line=dict(color="#38bdf8", width=1.5)), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_grafik.index, y=df_grafik["D"],
                name="%D", line=dict(color="#f59e0b", width=1.5)), row=2, col=1)
            fig.add_hline(y=20, line_dash="dot", line_color="#64748b", row=2, col=1)
            fig.add_hline(y=80, line_dash="dot", line_color="#64748b", row=2, col=1)

            fig.update_layout(
                template="plotly_dark", paper_bgcolor="#0d0f14", plot_bgcolor="#0d0f14",
                height=650, showlegend=True, xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=80, t=30, b=10),
                font=dict(family="Consolas", size=11),
            )
            fig.update_yaxes(gridcolor="#1e293b")
            fig.update_xaxes(gridcolor="#1e293b")
            st.plotly_chart(fig, use_container_width=True)

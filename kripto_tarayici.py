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
    "TFUEL","ONE","IOTX","ZIL","DGB","SC","RVN","ARRR","KMD","ZEN",
    "FLUX","ROSE","CFX","ID","BLUR","APE","GAL","GMT","GST","SLP",
    "LOKA","PLA","ALICE","TLM","DYDX","PERP","BICO","RAD","SPELL","CVX",
    "FXS","FRAX","LQTY","ALCX","TOKE","FORTH","AMP","RLY","TRIBE","MASK",
    "AGLD","ENS","FARM","BOND","INDEX","DPI","MVI","BNT","REQ","NMR",
    "RLC","OGN","LPT","GTC","AUDIO","JASMY","RNDR","VGX","SUPER","RARE",
    "XYO","STRAX","SYS","ARDR","LSK","STEEM","HIVE","BEAM","GRIN","ZRX",
    "KNC","LRC","POWR","WTC","MAID","PIVX","DCR","DIVI","NAV","PART",
    "LBC","XWC","BTCP","ZCL","XSN","COLX","HTML","PPC","NVC","VTC",
    "MONA","GRS","FTC","BLK","UNO","EMC2","NXT","CLAM","XPM","CURE",
    "KLAY","BORA","META","PAXG","WBTC","STETH","RETH","CBETH","WETH","USDC",
    "TUSD","BUSD","DAI","USDP","GUSD","FRXETH","LUSD","SUSD","USDD","USTC",
    "TWT","BNX","XVS","ALPACA","BAKE","BURGER","DODO","WATCH","RAMP","BELT",
    "EPS","RUKN","NAOS","RABBIT","BSCX","SPARTA","SFP","FOR","UNFI","REEF",
    "WAXP","GALA","ILV","GODS","IMX","YGG","GHST","TOWER","REVV","NFTB",
    "HERO","MOBOX","MBOX","TKO","PROM","FORTH","TVK","ULTRA","UFO","LABS",
    "SOLVE","MBL","DOCK","SPARTA","FRONT","HARD","WING","LIT","DEGO","BEL",
    "WING","VITE","TROY","FIRO","AERGO","COTI","FIO","ARPA","IRIS","COCOS",
    "TRB","OXT","PERL","HEGIC","TORN","PERP","BADGER","DIGG","CREAM","COVER",
    "PICKLE","ALPHA","SFI","SWRV","BASED","YAM","PASTA","MEME","CORE","SAFE",
    "SHROOM","TEND","SWFL","KIMCHI","BASED","HAM","YFV","YFII","YFL","YFB",
    "QUICK","DFYN","ROUTE","PLOT","POLS","ORION","BZRX","LAYER","UNCX","SWAP",
    "SATA","LEASH","BONE","RYOSHI","BABYDOGE","FLOKI","ELON","SAMO","KISHU",
    "AKITA","HOGE","HUSKY","MONGREL","PITBULL","KEANU","DOPEX","JONES","GMX",
    "GNS","VELA","CAP","MYCELIUM","KWENTA","LYRA","PREMIA","HEGIC","PODS",
    "ACH","AGIX","FET","OCEAN","NMR","RLC","GRT","API3","BAND","DIA",
    "LINK","TRB","WING","NEST","ONG","DIA","UTK","IDEX","ORAI","EGLD",
    "HBAR","IOTA","NANO","XDC","CSPR","MINA","CKB","CELO","ONE","QTUM",
    "ONT","ZIL","ICX","EOS","TRON","XEM","LSK","ARK","WAVES","STRAT",
    "PIVX","SYS","NXS","BURST","BLOCK","VEIL","ZERO","TENT","MWAT","SUMO",
]

# Tekrarsız liste
seen = set()
COINLER = []
for c in TOP500_COINLER:
    if c not in seen and c not in ["USDC","TUSD","BUSD","DAI","USDP","GUSD",
                                    "LUSD","SUSD","USDD","USTC","FRXETH",
                                    "STETH","RETH","CBETH","WETH","WBTC","PAXG"]:
        seen.add(c)
        COINLER.append(c)

def veri_cek_binance(symbol, interval="1d", limit=250):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol + "USDT", "interval": interval, "limit": limit}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data or len(data) < 60:
            return None
        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qv","trades","tbbav","tbqav","ignore"
        ])
        df["time"]   = pd.to_datetime(df["time"], unit="ms")
        df["open"]   = df["open"].astype(float)
        df["high"]   = df["high"].astype(float)
        df["low"]    = df["low"].astype(float)
        df["close"]  = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        df.set_index("time", inplace=True)
        return df
    except Exception:
        return None

def veri_cek_yfinance(symbol, limit=250):
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

def veri_cek(symbol, limit=250):
    df = veri_cek_binance(symbol, limit=limit)
    if df is None:
        df = veri_cek_yfinance(symbol, limit=limit)
    return df

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

def sinyal_tara(df, params):
    tolerans  = params["ema_tolerans"] / 100
    stok_esik = params["stok_esik"]
    atr_per   = params["atr_periyot"]
    atr_kat   = params["atr_katsayi"]
    rr        = params["rr_katsayi"]

    df = df.copy()
    df["EMA20"]  = ema(df["close"], 20)
    df["EMA50"]  = ema(df["close"], 50)
    df["EMA100"] = ema(df["close"], 100)
    df["EMA200"] = ema(df["close"], 200)
    df["ATR"]    = atr_hesapla(df, atr_per)
    df["K"], df["D"] = stokastik_hesapla(df)

    son   = df.iloc[-1]
    once  = df.iloc[-2]
    kapanis = float(son["close"])

    if not (son["EMA20"] > son["EMA50"] > son["EMA100"] > son["EMA200"]):
        return None
    if not (float(once["K"]) < float(once["D"]) and
            float(son["K"])  > float(son["D"])  and
            float(son["K"])  < stok_esik):
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
        "Kapanis":    round(kapanis, 6),
        "EMA Destek": ema_destek,
        "K":          round(float(son["K"]), 2),
        "D":          round(float(son["D"]), 2),
        "Stop":       stop,
        "Hedef":      hedef,
        "ATR":        round(atr_val, 6),
    }

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.title("Ayarlar")
portfoy     = st.sidebar.number_input("Portfolyo (USDT)", min_value=100, max_value=1000000, value=10000, step=100)
risk_yuzde  = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0, 0.5)
rr_katsayi  = st.sidebar.slider("R:R Katsayisi", 1.0, 5.0, 2.5, 0.5)
atr_katsayi = st.sidebar.slider("ATR Katsayisi", 0.5, 3.0, 1.5, 0.5)
atr_periyot = st.sidebar.slider("ATR Periyodu", 7, 21, 14, 1)
ema_tolerans= st.sidebar.slider("EMA Tolerans %", 0.5, 5.0, 2.0, 0.5)
stok_esik   = st.sidebar.slider("Stokastik Esik", 10, 40, 20, 5)

params = {
    "ema_tolerans": ema_tolerans,
    "stok_esik":    stok_esik,
    "atr_periyot":  atr_periyot,
    "atr_katsayi":  atr_katsayi,
    "rr_katsayi":   rr_katsayi,
}

# ─── ANA SAYFA ────────────────────────────────────────────────────────────────
st.title("Kripto Sinyal Tarayici")
st.caption("EMA20>50>100>200 + Stokastik Kesisim + EMA Destek | Binance/yfinance USDT")

if st.button("Tara", use_container_width=True, type="primary"):
    risk_usdt = portfoy * risk_yuzde / 100
    sinyaller = []

    progress = st.progress(0, text="Tarama basliyor...")
    toplam = len(COINLER)

    for i, coin in enumerate(COINLER):
        progress.progress((i + 1) / toplam, text="Taraniyor: " + coin + " (" + str(i+1) + "/" + str(toplam) + ")")
        df = veri_cek(coin)
        if df is None:
            continue
        try:
            sonuc = sinyal_tara(df, params)
        except Exception:
            continue
        if sonuc is None:
            continue

        kapanis   = sonuc["Kapanis"]
        stop      = sonuc["Stop"]
        risk_coin = kapanis - stop
        if risk_coin <= 0:
            continue
        miktar     = round(risk_usdt / risk_coin, 6)
        giris_usdt = round(miktar * kapanis, 2)

        sinyaller.append({
            "Coin":       coin,
            "Fiyat":      kapanis,
            "EMA Destek": sonuc["EMA Destek"],
            "%K":         sonuc["K"],
            "Stop":       stop,
            "Hedef":      sonuc["Hedef"],
            "Miktar":     miktar,
            "Giris USDT": giris_usdt,
            "Risk USDT":  round(risk_usdt, 2),
        })

    progress.empty()
    st.session_state["kripto_sinyaller"] = sinyaller
    st.session_state["kripto_tarih"]     = datetime.now().strftime("%d.%m.%Y %H:%M")

if "kripto_sinyaller" in st.session_state:
    sinyaller = st.session_state["kripto_sinyaller"]
    tarih     = st.session_state["kripto_tarih"]

    st.markdown("### Tarama Sonuclari - " + tarih)
    col1, col2 = st.columns(2)
    col1.metric("Sinyal Sayisi", len(sinyaller))
    col2.metric("Portfolyo", str(portfoy) + " USDT")

    if len(sinyaller) == 0:
        st.warning("Sinyal bulunamadi.")
    else:
        df_sonuc = pd.DataFrame(sinyaller).sort_values("%K")
        st.dataframe(df_sonuc, use_container_width=True, hide_index=True)

        csv = df_sonuc.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="CSV Indir",
            data=csv,
            file_name="kripto_sinyaller_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.markdown("### Grafik")

        secili = st.selectbox("Coin secin:", [r["Coin"] for r in sinyaller])
        df_grafik = veri_cek(secili, limit=150)

        if df_grafik is not None:
            df_grafik["EMA20"]  = ema(df_grafik["close"], 20)
            df_grafik["EMA50"]  = ema(df_grafik["close"], 50)
            df_grafik["EMA100"] = ema(df_grafik["close"], 100)
            df_grafik["EMA200"] = ema(df_grafik["close"], 200)
            df_grafik["K"], df_grafik["D"] = stokastik_hesapla(df_grafik)

            secili_sinyal = next(r for r in sinyaller if r["Coin"] == secili)

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

            for seviye, renk, isim in [
                (secili_sinyal["Stop"],  "#ef4444", "Stop"),
                (secili_sinyal["Hedef"], "#22c55e", "Hedef"),
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

from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

OUTPUT=Path("output"); OUTPUT.mkdir(exist_ok=True)

def _rsi(s,n=14):
    d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    ag=g.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    al=l.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    return 100-100/(1+ag/al.replace(0,np.nan))

def _index(symbol,name):
    x=yf.download(symbol,period="2y",interval="1d",auto_adjust=False,progress=False)
    if isinstance(x.columns,pd.MultiIndex): x=x.xs(symbol,axis=1,level=-1)
    x=x.dropna(subset=["Close"]).copy()
    for c in ["Open","High","Low","Close","Volume"]: x[c]=pd.to_numeric(x[c],errors="coerce")
    x["sma20"]=x.Close.rolling(20).mean(); x["sma50"]=x.Close.rolling(50).mean()
    x["sma200"]=x.Close.rolling(200).mean(); x["rsi"]=_rsi(x.Close)
    x["atr"]=pd.concat([x.High-x.Low,(x.High-x.Close.shift()).abs(),
                         (x.Low-x.Close.shift()).abs()],axis=1).max(axis=1).rolling(14).mean()
    x["res"]=x.High.shift(1).rolling(20).max(); x["sup"]=x.Low.shift(1).rolling(20).min()
    cur=x.iloc[-1]; prev=x.iloc[-2]
    trend="Bullish" if cur.Close>cur.sma20>cur.sma50>cur.sma200 else "Bearish" if cur.Close<cur.sma20<cur.sma50<cur.sma200 else "Mixed"
    momentum=float(np.clip(50+x.Close.pct_change(20).iloc[-1]*200,0,100))
    score=float(np.clip((50 if cur.Close>cur.sma200 else 25)+(25 if cur.rsi>50 else 10)+(25 if momentum>55 else 10),0,100))
    return {
        "name":name,"price":float(cur.Close),"previous_close":float(prev.Close),
        "daily_return_pct":float((cur.Close/prev.Close-1)*100),
        "sma20":float(cur.sma20),"sma50":float(cur.sma50),"sma200":float(cur.sma200),
        "rsi":float(cur.rsi),"atr":float(cur.atr),"support":float(cur.sup),
        "resistance":float(cur.res),"pivot":float((prev.High+prev.Low+prev.Close)/3),
        "trend":trend,"momentum":round(momentum,2),"score":round(score,2)
    }

def get_market_regime(breadth=None):
    try: nifty=_index("^NSEI","NIFTY 50")
    except Exception: nifty={}
    try: bank=_index("^NSEBANK","BANK NIFTY")
    except Exception: bank={}
    try:
        v=_index("^INDIAVIX","INDIA VIX")
        vix=v.get("price",np.nan)
    except Exception: vix=np.nan

    bscore=float((breadth or {}).get("breadth_score",50))
    nscore=float(nifty.get("score",50))
    score=round(nscore*.55+bscore*.45,2)
    regime="Bullish" if score>=70 else "Constructive" if score>=55 else "Neutral" if score>=45 else "Cautious" if score>=30 else "Bearish"
    scenario="Upside confirmation above resistance" if nifty.get("price",0)>nifty.get("resistance",np.inf) else "Range / confirmation required"
    if not np.isnan(vix):
        scenario += f"; VIX {vix:.2f}"
    data={
        "market_regime":regime,"market_score":score,"nifty":nifty,"bank_nifty":bank,
        "vix":vix,"breadth_score":bscore,
        "equity_environment": "Favourable" if score>=55 else "Selective",
        "swing_environment": "Favourable" if score>=50 else "Defensive",
        "breakout_environment": "Favourable" if score>=60 else "Confirmation Required",
        "intraday_environment": "Favourable" if score>=55 else "Selective",
        "options_environment": "Favourable" if score>=60 else "Risk Elevated",
        "support":nifty.get("support"),"resistance":nifty.get("resistance"),
        "pivot":nifty.get("pivot"),
        "bullish_trigger":nifty.get("resistance"),
        "bearish_trigger":nifty.get("support"),
        "market_scenario":scenario,"market_data_authority":"Yahoo Finance EOD"
    }
    pd.DataFrame([data]).to_csv(OUTPUT/"market_regime.csv",index=False)
    return data

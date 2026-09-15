from pathlib import Path
import json, time
import numpy as np
import pandas as pd
import yfinance as yf

CACHE = Path("data/fundamental_cache")
CACHE.mkdir(parents=True, exist_ok=True)
OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

def _num(v):
    try:
        x=float(v)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan

def _score(row):
    parts=[]
    for col, good in [
        ("ROE", lambda x: np.clip(x/25*100,0,100)),
        ("ROCE", lambda x: np.clip(x/25*100,0,100)),
        ("Revenue_Growth", lambda x: np.clip(50+x*2,0,100)),
        ("Profit_Growth", lambda x: np.clip(50+x*2,0,100)),
        ("Debt_to_Equity", lambda x: np.clip(100-x*20,0,100)),
        ("Operating_Margin", lambda x: np.clip(x*4,0,100)),
    ]:
        v=_num(row.get(col))
        if not np.isnan(v): parts.append(float(good(v)))
    return round(float(np.mean(parts)),2) if parts else np.nan

def _fetch(symbol):
    cache=CACHE/f"{symbol}.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text())
        except Exception:
            pass
    try:
        info=yf.Ticker(symbol+".NS").info
        fields={
            "Company_Name": info.get("longName") or info.get("shortName"),
            "Sector": info.get("sector"),
            "Industry": info.get("industry"),
            "Market_Cap": info.get("marketCap"),
            "Enterprise_Value": info.get("enterpriseValue"),
            "Revenue": info.get("totalRevenue"),
            "Net_Income": info.get("netIncomeToCommon"),
            "EPS": info.get("trailingEps"),
            "Forward_EPS": info.get("forwardEps"),
            "Book_Value": info.get("bookValue"),
            "Total_Debt": info.get("totalDebt"),
            "Total_Cash": info.get("totalCash"),
            "Current_Ratio": info.get("currentRatio"),
            "Quick_Ratio": info.get("quickRatio"),
            "ROE": (info.get("returnOnEquity") or np.nan)*100,
            "ROA": (info.get("returnOnAssets") or np.nan)*100,
            "Operating_Margin": (info.get("operatingMargins") or np.nan)*100,
            "Profit_Margin": (info.get("profitMargins") or np.nan)*100,
            "Debt_to_Equity": info.get("debtToEquity"),
            "PE": info.get("trailingPE"),
            "Forward_PE": info.get("forwardPE"),
            "PB": info.get("priceToBook"),
            "PEG": info.get("pegRatio"),
            "Dividend_Yield": (info.get("dividendYield") or np.nan)*100,
            "Revenue_Growth": (info.get("revenueGrowth") or np.nan)*100,
            "Profit_Growth": (info.get("earningsGrowth") or np.nan)*100,
        }
        fields["Fundamental_Score"]=_score(fields)
        cache.write_text(json.dumps(fields, default=lambda x: None))
        return fields
    except Exception:
        return {}

def get_fundamentals(technical, max_symbols=800):
    """
    To keep GitHub Actions reliable, fundamentals are enriched for the strongest
    technical candidates first. Technical analysis still covers the full NSE universe.
    Set FUNDAMENTAL_MAX_SYMBOLS in the workflow to change the coverage.
    """
    if technical is None or technical.empty:
        return pd.DataFrame()
    x=technical.sort_values("Technical_Score", ascending=False).copy()
    symbols=x.Symbol.dropna().astype(str).unique().tolist()[:max_symbols]
    rows=[]
    print(f"Fundamental enrichment: {len(symbols):,} stocks")
    for i,s in enumerate(symbols,1):
        d=_fetch(s); d["Symbol"]=s; rows.append(d)
        if i%50==0: print(f"Fundamental progress: {i:,}/{len(symbols):,}")
        time.sleep(0.05)
    f=pd.DataFrame(rows)
    if not f.empty: f.to_csv(OUTPUT/"fundamentals.csv",index=False)
    return f

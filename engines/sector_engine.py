import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path

OUTPUT=Path("output"); OUTPUT.mkdir(exist_ok=True)

SECTORS={
"Auto":"^CNXAUTO","Bank":"^NSEBANK","Financial Services":"^CNXFIN",
"FMCG":"^CNXFMCG","IT":"^CNXIT","Pharma":"^CNXPHARMA","Metal":"^CNXMETAL",
"Realty":"^CNXREALTY","Energy":"^CNXENERGY","Infrastructure":"^CNXINFRA",
"PSU Bank":"^CNXPSUBANK","Media":"^CNXMEDIA","PSE":"^CNXPSE"
}

def get_sector_analysis():
    rows=[]
    for name,ticker in SECTORS.items():
        try:
            x=yf.download(ticker,period="1y",progress=False,auto_adjust=False)
            if isinstance(x.columns,pd.MultiIndex): x=x.xs(ticker,axis=1,level=-1)
            c=x["Close"].dropna()
            if len(c)<60: continue
            p=float(c.iloc[-1]); r20=float((p/c.iloc[-21]-1)*100); r60=float((p/c.iloc[-61]-1)*100)
            rows.append({"Sector":name,"Index":ticker,"Price":p,"Return_20D_Pct":r20,
                         "Return_60D_Pct":r60,"Sector_Score":round(np.clip(50+r20*2+r60*.5,0,100),2)})
        except Exception: pass
    df=pd.DataFrame(rows).sort_values("Sector_Score",ascending=False) if rows else pd.DataFrame()
    df.to_csv(OUTPUT/"sector_analysis.csv",index=False)
    return df

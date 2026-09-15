import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT=Path("output")
OUTPUT.mkdir(exist_ok=True)

def get_market_breadth(technical):
    if technical is None or technical.empty:
        return {}, pd.DataFrame()
    x=technical.copy()
    total=len(x)
    above20=int((x.Close>x.SMA20).sum())
    above50=int((x.Close>x.SMA50).sum())
    above200=int((x.Close>x.SMA200).sum())
    highs=int((x.Distance_52W_High_Pct>=-0.5).sum())
    lows=int((x.Distance_52W_High_Pct<=-25).sum())
    breadth_score=round(
        (above20/total*.3+above50/total*.3+above200/total*.25+
         highs/max(lows,1)*.15/(1+highs/max(lows,1)))*100,2
    )
    regime="Strong" if breadth_score>=65 else "Healthy" if breadth_score>=50 else "Weak" if breadth_score>=30 else "Very Weak"
    summary={
        "stocks_analyzed":total,"above_20_dma":above20,"above_50_dma":above50,
        "above_200_dma":above200,"52w_highs":highs,"52w_lows":lows,
        "high_low_ratio":round(highs/max(lows,1),2),"breadth_score":breadth_score,
        "breadth_regime":regime
    }
    x["Above_20DMA"]=x.Close>x.SMA20
    x["Above_50DMA"]=x.Close>x.SMA50
    x.to_csv(OUTPUT/"market_breadth_stocks.csv",index=False)
    pd.DataFrame([summary]).to_csv(OUTPUT/"market_breadth.csv",index=False)
    return summary,x

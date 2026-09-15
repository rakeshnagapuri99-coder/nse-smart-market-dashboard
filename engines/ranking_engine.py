import numpy as np
import pandas as pd

def _num(v,d=np.nan):
    try:
        x=float(v); return x if np.isfinite(x) else d
    except Exception: return d

def _sector_score(row,sectors):
    if sectors is None or sectors.empty or "Sector" not in sectors: return 50
    s=str(row.get("Primary_Sector",""))
    hit=sectors[sectors.Sector.astype(str).str.lower()==s.lower()]
    return _num(hit.iloc[0].get("Sector_Score"),50) if not hit.empty else 50

def _plan(r):
    p=_num(r.get("Close")); atr=_num(r.get("ATR14")); sup=_num(r.get("Support")); res=_num(r.get("Resistance")); score=_num(r.get("Overall_Score"),0)
    if np.isnan(p) or np.isnan(atr) or score<45: return {"Trade_Status":"Confirmation Required","Entry_Zone":"","Entry_Price":np.nan,"Stop_Loss":np.nan,"Target_1":np.nan,"Target_2":np.nan,"Risk_Reward":np.nan}
    entry=p if p<=res else res
    stop=max(sup,entry-1.5*atr) if not np.isnan(sup) else entry-1.5*atr
    if stop>=entry: stop=entry-1.0*atr
    t1=max(res if not np.isnan(res) else entry+2*atr, entry+2*(entry-stop))
    t2=entry+3*(entry-stop)
    rr=(t1-entry)/(entry-stop) if entry>stop else np.nan
    status="Actionable Watch" if rr>=1.5 else "Confirmation Required"
    return {"Trade_Status":status,"Entry_Zone":f"{entry:.2f} or below","Entry_Price":round(entry,2),
            "Stop_Loss":round(stop,2),"Target_1":round(t1,2),"Target_2":round(t2,2),
            "Risk_Reward":round(rr,2) if np.isfinite(rr) else np.nan}

def rank_stocks(technical_data,fundamental_data=None,sector_data=None,market_regime=None):
    if technical_data is None or technical_data.empty: return pd.DataFrame()
    x=technical_data.copy()
    if fundamental_data is not None and not fundamental_data.empty and "Symbol" in fundamental_data:
        f=fundamental_data.copy()
        dup=[c for c in f.columns if c in x.columns and c!="Symbol"]
        f=f.drop(columns=dup)
        x=x.merge(f,on="Symbol",how="left")
    if "Fundamental_Score" not in x: x["Fundamental_Score"]=np.nan
    x["Sector_Score"]=x.apply(lambda r:_sector_score(r,sector_data),axis=1)
    mscore=_num((market_regime or {}).get("market_score"),50)
    x["Market_Adjustment"]=(mscore-50)*.15
    x["Overall_Score"]=np.where(x.Fundamental_Score.notna(),
        x.Technical_Score*.60+x.Fundamental_Score*.40,
        x.Technical_Score)
    x["Overall_Score"]=np.clip(x.Overall_Score+(x.Sector_Score-50)*.10+x.Market_Adjustment,0,100)
    x["Setup"]=x["Setup"].fillna("Neutral Watch")
    plans=x.apply(_plan,axis=1,result_type="expand")
    x=pd.concat([x,plans],axis=1)
    x["Ranking_Quality"]=pd.cut(x.Overall_Score,[-1,45,50,60,70,80,101],
                                labels=["Weak","Watch","Good","Strong","Very Strong","Excellent"]).astype(str)
    return x.sort_values("Overall_Score",ascending=False).reset_index(drop=True)

def create_watchlists(r):
    if r is None or r.empty: return {}
    def top(mask,n=100): return r[mask].head(n).copy()
    return {
      "next_day":top(r.Trade_Status.eq("Actionable Watch")),
      "intraday":top(r.Overall_Score>=60),
      "swing":top((r.Overall_Score>=55)&(r.Close>r.SMA200)),
      "long_term":top((r.Overall_Score>=65)&(r.Fundamental_Score.fillna(0)>=55)),
      "52w_high":top(r.Distance_52W_High_Pct>=-3),
      "dma_recovery":top(r.Near_200DMA & r.Recent_200DMA_Cross_Down),
      "momentum":top(r.Momentum_Score>=70),
      "breakout":top(r.Breakout | r.Near_Breakout),
      "options":top(r.Overall_Score>=60)
    }

def create_setup_summary(r):
    if r is None or r.empty: return pd.DataFrame()
    return r.groupby("Setup",dropna=False).size().reset_index(name="Count").sort_values("Count",ascending=False)

def prepare_export_data(r):
    return r.copy() if r is not None else pd.DataFrame()

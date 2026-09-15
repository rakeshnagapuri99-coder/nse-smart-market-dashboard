#!/usr/bin/env python3
from pathlib import Path
import json, time
import pandas as pd
from engines.nse_universe import get_nse_universe
from engines.technical_engine import calculate_technical_indicators
from engines.fundamental_engine import get_fundamentals
from engines.market_breadth import get_market_breadth
from engines.market_engine import get_market_regime
from engines.sector_engine import get_sector_analysis
from engines.sector_mapping import load_sector_mapping
from engines.ranking_engine import rank_stocks,create_watchlists,create_setup_summary

OUTPUT=Path("output"); EXPORT=OUTPUT/"exports"
OUTPUT.mkdir(exist_ok=True); EXPORT.mkdir(exist_ok=True)

def main():
    started=time.time()
    print("="*60); print("NSE SMART MARKET DASHBOARD V3"); print("="*60)
    print("STEP 1 — NSE UNIVERSE")
    universe=get_nse_universe(); print(f"NSE universe: {len(universe):,} stocks")

    print("STEP 2 — TECHNICAL ANALYSIS")
    technical=calculate_technical_indicators(universe)
    if technical.empty: raise RuntimeError("Technical engine returned no data.")
    print(f"Technical records: {len(technical):,}")

    print("STEP 3 — FUNDAMENTALS")
    fundamentals=get_fundamentals(technical,max_symbols=int(__import__("os").getenv("FUNDAMENTAL_MAX_SYMBOLS","800")))

    print("STEP 4 — MARKET BREADTH")
    breadth,breadth_stocks=get_market_breadth(technical)

    print("STEP 5 — MARKET REGIME")
    market=get_market_regime(breadth)

    print("STEP 6 — SECTORS")
    sectors=get_sector_analysis()

    print("STEP 7 — SECTOR MAPPING")
    mapping=load_sector_mapping()
    if not mapping.empty and "Symbol" in mapping.columns:
        technical=technical.merge(mapping.drop_duplicates("Symbol"),on="Symbol",how="left")

    print("STEP 8 — RANKING")
    ranked=rank_stocks(technical,fundamentals,sectors,market)
    if ranked.empty: raise RuntimeError("Ranking engine returned no data.")
    ranked.to_csv(OUTPUT/"stocks.csv",index=False)

    print("STEP 9 — WATCHLISTS")
    watchlists=create_watchlists(ranked)
    setup=create_setup_summary(ranked)
    setup.to_csv(OUTPUT/"setup_summary.csv",index=False)

    print("STEP 10 — EXPORTS")
    export_cols=[c for c in ranked.columns if c not in []]
    ranked[export_cols].to_csv(EXPORT/"all_stocks.csv",index=False)
    for name,df in watchlists.items(): df.to_csv(EXPORT/f"{name}.csv",index=False)
    with pd.ExcelWriter(EXPORT/"nse_smart_market_dashboard.xlsx",engine="openpyxl") as w:
        ranked.to_excel(w,index=False,sheet_name="All Stocks")
        setup.to_excel(w,index=False,sheet_name="Setup Summary")
        for name,df in watchlists.items(): df.to_excel(w,index=False,sheet_name=name[:31])

    serial_watch={}
    counts={}
    for name,df in watchlists.items():
        serial_watch[name]=df.replace({float("nan"):None}).to_dict(orient="records")
        counts[name]=len(df)

    data={
      "dashboard":"NSE SMART MARKET DASHBOARD","version":"3.0",
      "generated_at":pd.Timestamp.now(tz="Asia/Kolkata").isoformat(),
      "market_data_authority":"Yahoo Finance EOD",
      "market_regime":market,"market":market,
      "market_breadth":breadth,"breadth":breadth,
      "market_breadth_stocks":breadth_stocks.head(500).replace({float("nan"):None}).to_dict(orient="records"),
      "sector_analysis":sectors.replace({float("nan"):None}).to_dict(orient="records") if not sectors.empty else [],
      "sectors":sectors.replace({float("nan"):None}).to_dict(orient="records") if not sectors.empty else [],
      "stocks":ranked.replace({float("nan"):None}).to_dict(orient="records"),
      "stock_count":len(ranked),"watchlists":serial_watch,"watchlist_counts":counts,
      "setup_summary":setup.replace({float("nan"):None}).to_dict(orient="records"),
      "setup_counts":dict(zip(setup.Setup.astype(str),setup.Count.astype(int))) if not setup.empty else {},
      "exports":{"excel":"output/exports/nse_smart_market_dashboard.xlsx"},
      "metadata":{"nse_universe":len(universe),"technical_records":len(technical),
                  "fundamental_records":len(fundamentals),"runtime_seconds":round(time.time()-started,1)}
    }
    (OUTPUT/"dashboard_data.json").write_text(json.dumps(data,allow_nan=False))
    print("="*60); print("SCAN COMPLETE")
    print(f"Stocks: {len(ranked):,} | Runtime: {time.time()-started:.1f}s")
    print("="*60)

if __name__=="__main__":
    main()

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from engines.nse_universe import get_nse_universe, save_universe
from engines.market_breadth import (
    get_market_breadth,
    display_breadth
)
from engines.market_engine import (
    get_market_regime,
    display_market
)
from engines.sector_engine import (
    get_sector_analysis
)
from engines.technical_engine import (
    calculate_technical_indicators
)
from engines.ranking_engine import (
    rank_stocks,
    create_setup_summary,
    create_watchlists
)
from engines.fundamental_engine import (
    get_fundamentals
)


# ============================================================
# NSE SMART MARKET DASHBOARD
# MASTER PRODUCTION SCANNER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

TECHNICAL_FILE = OUTPUT_DIR / "stocks.csv"
MARKET_FILE = OUTPUT_DIR / "market_regime.csv"
BREADTH_FILE = OUTPUT_DIR / "market_breadth.csv"
SECTOR_FILE = OUTPUT_DIR / "sector_analysis.csv"
SUMMARY_FILE = OUTPUT_DIR / "setup_summary.csv"
JSON_FILE = OUTPUT_DIR / "dashboard_data.json"

BATCH_SIZE = 100
DOWNLOAD_PERIOD = "2y"


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_value(value):

    if value is None:
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):

        if np.isnan(value) or np.isinf(value):
            return None

        return float(value)

    if isinstance(value, float):

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    if pd.isna(value):
        return None

    return value


def clean_dataframe(df):

    if df is None or df.empty:
        return df

    df = df.copy()

    for column in df.columns:

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            df[column] = df[column].replace(
                [np.inf, -np.inf],
                np.nan
            )

    return df


# ============================================================
# TECHNICAL BATCH DOWNLOAD
# ============================================================

def download_batch(symbols):

    if not symbols:
        return pd.DataFrame()

    try:

        data = yf.download(
            symbols,
            period=DOWNLOAD_PERIOD,
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True
        )

        return data

    except Exception as e:

        print(
            f"Technical batch download error: {e}"
        )

        return pd.DataFrame()


# ============================================================
# EXTRACT INDIVIDUAL STOCK DATA
# ============================================================

def extract_stock_data(
    batch_data,
    symbol
):

    if (
        batch_data is None
        or batch_data.empty
    ):

        return pd.DataFrame()

    try:

        if isinstance(
            batch_data.columns,
            pd.MultiIndex
        ):

            level_zero = (
                batch_data
                .columns
                .get_level_values(0)
            )

            level_one = (
                batch_data
                .columns
                .get_level_values(1)
            )

            # yfinance can return either:
            #
            # ticker -> OHLCV
            # or
            # OHLCV -> ticker

            if symbol in level_zero:

                data = batch_data[
                    symbol
                ].copy()

            elif symbol in level_one:

                data = (
                    batch_data
                    .xs(
                        symbol,
                        axis=1,
                        level=1
                    )
                    .copy()
                )

            else:

                return pd.DataFrame()

        else:

            data = batch_data.copy()

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for column in required:

            if column not in data.columns:

                return pd.DataFrame()

        data = data[
            required
        ].dropna(
            subset=["Close"]
        )

        return data

    except Exception as e:

        print(
            f"Extraction error {symbol}: {e}"
        )

        return pd.DataFrame()


# ============================================================
# SINGLE STOCK TECHNICAL ANALYSIS
# ============================================================

def analyze_stock(
    data,
    symbol
):

    if (
        data is None
        or data.empty
        or len(data) < 200
    ):

        return None

    try:

        data = calculate_technical_indicators(
            data
        )

        if data.empty:
            return None

        latest = data.iloc[-1]

        result = {

            "symbol":
                symbol,

            "price":
                latest["Close"],

            "previous_close":
                latest["Previous_Close"],

            "daily_return_pct":
                latest["Daily_Return_Pct"],

            "sma20":
                latest["SMA20"],

            "sma50":
                latest["SMA50"],

            "sma100":
                latest["SMA100"],

            "sma200":
                latest["SMA200"],

            "ema9":
                latest["EMA9"],

            "ema20":
                latest["EMA20"],

            "ema50":
                latest["EMA50"],

            "rsi14":
                latest["RSI14"],

            "atr14":
                latest["ATR14"],

            "atr_percent":
                latest["ATR_Percent"],

            "volume":
                latest["Volume"],

            "average_volume_20":
                latest["Average_Volume_20"],

            "volume_ratio":
                latest["Volume_Ratio"],

            "52w_high":
                latest["52W_High"],

            "52w_low":
                latest["52W_Low"],

            "distance_from_52w_high_pct":
                latest[
                    "Distance_From_52W_High_Pct"
                ],

            "distance_from_52w_low_pct":
                latest[
                    "Distance_From_52W_Low_Pct"
                ],

            "distance_from_200dma_pct":
                latest[
                    "Distance_From_200DMA_Pct"
                ],

            "above_200dma":
                latest[
                    "Above_200DMA"
                ],

            "support":
                latest["Support"],

            "resistance":
                latest["Resistance"],

            "trend":
                latest["Trend"],

            "momentum":
                latest["Momentum"],

            "breakout_status":
                latest[
                    "Breakout_Status"
                ]
        }

        return result

    except Exception as e:

        print(
            f"Technical analysis error "
            f"{symbol}: {e}"
        )

        return None


# ============================================================
# FULL NSE TECHNICAL SCAN
# ============================================================

def run_technical_scan(
    universe
):

    if (
        universe is None
        or universe.empty
    ):

        return pd.DataFrame()

    symbols = (
        universe[
            "YAHOO_SYMBOL"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    results = []

    total = len(symbols)

    total_batches = math.ceil(
        total / BATCH_SIZE
    )

    print()
    print("=" * 60)
    print("FULL NSE TECHNICAL SCAN")
    print("=" * 60)
    print(
        f"Total securities: {total}"
    )
    print(
        f"Batch size: {BATCH_SIZE}"
    )
    print("=" * 60)

    for start in range(
        0,
        total,
        BATCH_SIZE
    ):

        batch = symbols[
            start:
            start + BATCH_SIZE
        ]

        batch_number = (
            start // BATCH_SIZE
        ) + 1

        print()
        print(
            f"Batch "
            f"{batch_number}/"
            f"{total_batches}"
        )

        print(
            f"Stocks "
            f"{start + 1}-"
            f"{min(start + BATCH_SIZE, total)}"
        )

        batch_data = download_batch(
            batch
        )

        if (
            batch_data is None
            or batch_data.empty
        ):

            print(
                "No data returned."
            )

            continue

        for symbol in batch:

            data = extract_stock_data(
                batch_data,
                symbol
            )

            result = analyze_stock(
                data,
                symbol
            )

            if result is not None:

                results.append(
                    result
                )

    if not results:

        return pd.DataFrame()

    df = pd.DataFrame(
        results
    )

    df = clean_dataframe(
        df
    )

    print()
    print(
        f"Technical stocks analyzed: "
        f"{len(df)}"
    )

    return df


# ============================================================
# ADD NSE MASTER DATA
# ============================================================

def enrich_with_universe(
    stock_data,
    universe
):

    if (
        stock_data is None
        or stock_data.empty
    ):

        return stock_data

    if (
        universe is None
        or universe.empty
    ):

        return stock_data

    columns = [
        "SYMBOL",
        "YAHOO_SYMBOL"
    ]

    available = [
        column
        for column in columns
        if column in universe.columns
    ]

    if len(available) < 2:

        return stock_data

    mapping = (
        universe[available]
        .drop_duplicates(
            "YAHOO_SYMBOL"
        )
    )

    df = stock_data.merge(
        mapping,
        left_on="symbol",
        right_on="YAHOO_SYMBOL",
        how="left"
    )

    if "SYMBOL" in df.columns:

        df["nse_symbol"] = df[
            "SYMBOL"
        ]

    else:

        df["nse_symbol"] = (
            df["symbol"]
            .str.replace(
                ".NS",
                "",
                regex=False
            )
        )

    return df


# ============================================================
# FUNDAMENTAL SHORTLIST
# ============================================================

def create_fundamental_shortlist(
    ranked
):

    if (
        ranked is None
        or ranked.empty
    ):

        return []

    df = ranked.copy()

    candidates = pd.DataFrame()

    # Top technically ranked stocks
    top_technical = (
        df.sort_values(
            "technical_score",
            ascending=False
        )
        .head(300)
    )

    # Stocks close to 52W high
    high_candidates = df[
        df[
            "distance_from_52w_high_pct"
        ].between(
            -10,
            0
        )
    ].head(150)

    # Stocks around 200 DMA
    dma_candidates = df[
        df[
            "distance_from_200dma_pct"
        ].between(
            -7,
            7
        )
    ].head(150)

    # Momentum candidates
    momentum_candidates = df[
        df[
            "momentum"
        ].isin(
            [
                "Positive",
                "Strong Positive"
            ]
        )
    ].head(150)

    candidates = pd.concat(
        [
            top_technical,
            high_candidates,
            dma_candidates,
            momentum_candidates
        ],
        ignore_index=True
    )

    if candidates.empty:
        return []

    symbols = (
        candidates[
            "symbol"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    # Keep the fundamental request
    # bounded for daily GitHub Actions.
    return symbols[:500]


# ============================================================
# MERGE FUNDAMENTALS
# ============================================================

def merge_fundamentals(
    ranked,
    fundamentals
):

    if (
        ranked is None
        or ranked.empty
    ):

        return ranked

    if (
        fundamentals is None
        or fundamentals.empty
    ):

        ranked[
            "fundamental_score"
        ] = np.nan

        ranked[
            "fundamental_quality"
        ] = "Data Unavailable"

        ranked[
            "fundamental_data_available"
        ] = False

        return ranked

    fundamentals = fundamentals.copy()

    fundamentals = (
        fundamentals
        .drop_duplicates(
            "symbol"
        )
    )

    # Do not duplicate sector columns.
    sector_columns = [
        "sector",
        "industry"
    ]

    columns_to_drop = [
        column
        for column in sector_columns
        if column in ranked.columns
        and column in fundamentals.columns
    ]

    fundamentals = fundamentals.drop(
        columns=columns_to_drop,
        errors="ignore"
    )

    merged = ranked.merge(
        fundamentals,
        on="symbol",
        how="left",
        suffixes=("", "_fundamental")
    )

    # --------------------------------------------------------
    # Recalculate final score now that fundamentals exist.
    # --------------------------------------------------------

    if "fundamental_score" in merged.columns:

        def final_score(row):

            technical = row.get(
                "technical_score",
                np.nan
            )

            fundamental = row.get(
                "fundamental_score",
                np.nan
            )

            sector = row.get(
                "sector_score",
                np.nan
            )

            if pd.isna(technical):

                return np.nan

            # Technical-only if fundamentals unavailable.
            if pd.isna(fundamental):

                adjustment = 0

                if not pd.isna(sector):

                    if sector >= 75:
                        adjustment = 5

                    elif sector >= 60:
                        adjustment = 3

                    elif sector < 30:
                        adjustment = -5

                    elif sector < 45:
                        adjustment = -3

                return round(
                    max(
                        0,
                        min(
                            100,
                            technical
                            + adjustment
                        )
                    ),
                    2
                )

            return round(
                max(
                    0,
                    min(
                        100,
                        technical * 0.60
                        + fundamental * 0.40
                    )
                ),
                2
            )

        merged[
            "overall_rating"
        ] = merged.apply(
            final_score,
            axis=1
        )

        merged[
            "rating"
        ] = merged[
            "overall_rating"
        ]

        merged[
            "total_score"
        ] = merged[
            "overall_rating"
        ]

    if (
        "fundamental_data_available"
        not in merged.columns
    ):

        merged[
            "fundamental_data_available"
        ] = (
            merged[
                "fundamental_score"
            ].notna()
        )

    return merged


# ============================================================
# FINAL RANKING
# ============================================================

def finalize_ranking(
    stock_data,
    sector_data,
    fundamentals
):

    if (
        stock_data is None
        or stock_data.empty
    ):

        return pd.DataFrame()

    ranked = rank_stocks(
        stock_data,
        sector_data=sector_data
    )

    if ranked.empty:

        return ranked

    ranked = merge_fundamentals(
        ranked,
        fundamentals
    )

    ranked = ranked.sort_values(
        [
            "overall_rating",
            "technical_score"
        ],
        ascending=False
    ).reset_index(
        drop=True
    )

    ranked[
        "rank"
    ] = ranked.index + 1

    ranked[
        "technical_rank"
    ] = (
        ranked[
            "technical_score"
        ]
        .rank(
            ascending=False,
            method="min"
        )
        .astype(int)
    )

    return ranked


# ============================================================
# SAVE MAIN OUTPUTS
# ============================================================

def save_csv(
    df,
    filename
):

    if (
        df is None
        or df.empty
    ):

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        OUTPUT_DIR
        / filename
    )

    df.to_csv(
        path,
        index=False
    )

    print(
        f"Saved: {path}"
    )


# ============================================================
# SAVE WATCHLISTS
# ============================================================

def save_watchlists(
    watchlists
):

    if not watchlists:
        return

    filename_map = {

        "next_day":
            "next_day.csv",

        "intraday":
            "intraday.csv",

        "swing":
            "swing.csv",

        "long_term":
            "long_term.csv",

        "52w_high":
            "52w_high.csv",

        "dma_recovery":
            "dma_recovery.csv",

        "options":
            "options.csv",

        "momentum":
            "momentum.csv",

        "breakout":
            "breakout.csv"
    }

    for name, df in watchlists.items():

        filename = filename_map.get(
            name
        )

        if filename:

            save_csv(
                df,
                filename
            )


# ============================================================
# JSON SERIALIZATION
# ============================================================

def dataframe_to_records(
    df
):

    if (
        df is None
        or df.empty
    ):

        return []

    records = []

    for record in df.to_dict(
        orient="records"
    ):

        cleaned = {}

        for key, value in record.items():

            cleaned[
                str(key)
            ] = clean_value(
                value
            )

        records.append(
            cleaned
        )

    return records


# ============================================================
# CREATE DASHBOARD JSON
# ============================================================

def create_dashboard_json(
    market,
    breadth,
    sectors,
    ranked,
    watchlists
):

    data = {

        "generated_at":
            pd.Timestamp.now(
                tz="Asia/Kolkata"
            ).isoformat(),

        "market":
            market or {},

        "breadth":
            breadth or {},

        "sectors":
            dataframe_to_records(
                sectors
            ),

        "stocks":
            dataframe_to_records(
                ranked
            ),

        "watchlists": {}
    }

    for name, df in (
        watchlists or {}
    ).items():

        data[
            "watchlists"
        ][name] = dataframe_to_records(
            df
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        JSON_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            allow_nan=False
        )

    print(
        f"Saved dashboard data: "
        f"{JSON_FILE}"
    )


# ============================================================
# EXCEL EXPORT
# ============================================================

def create_excel_exports(
    ranked,
    watchlists
):

    if (
        ranked is None
        or ranked.empty
    ):

        return

    export_dir = (
        OUTPUT_DIR
        / "exports"
    )

    export_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Complete stock analysis
    # --------------------------------------------------------

    try:

        ranked.to_excel(
            export_dir
            / "all_stocks.xlsx",
            index=False
        )

        print(
            "Created "
            "all_stocks.xlsx"
        )

    except Exception as e:

        print(
            f"Excel export error: {e}"
        )

    # --------------------------------------------------------
    # Individual watchlists
    # --------------------------------------------------------

    for name, df in (
        watchlists or {}
    ).items():

        if (
            df is None
            or df.empty
        ):

            continue

        try:

            df.to_excel(
                export_dir
                / f"{name}.xlsx",
                index=False
            )

        except Exception as e:

            print(
                f"Excel export error "
                f"{name}: {e}"
            )


# ============================================================
# MAIN PRODUCTION PIPELINE
# ============================================================

def main():

    print()
    print("=" * 70)
    print("NSE SMART MARKET DASHBOARD")
    print("PRODUCTION SCANNER")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    # ========================================================
    # STEP 1 — NSE UNIVERSE
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 1 — NSE EQUITY UNIVERSE")
    print("=" * 60)

    universe = get_nse_universe()

    if universe.empty:

        print(
            "NSE universe unavailable."
        )

        return

    save_universe(
        universe
    )

    print(
        f"Universe size: "
        f"{len(universe)}"
    )


    # ========================================================
    # STEP 2 — MARKET BREADTH
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 2 — MARKET BREADTH")
    print("=" * 60)

    breadth = get_market_breadth(
        universe
    )

    display_breadth(
        breadth
    )


    # ========================================================
    # STEP 3 — MARKET REGIME
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 3 — MARKET REGIME")
    print("=" * 60)

    market = get_market_regime(
        breadth
    )

    display_market(
        market
    )

    save_csv(
        pd.DataFrame(
            [market]
        ),
        "market_regime.csv"
    )


    # ========================================================
    # STEP 4 — SECTOR ANALYSIS
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 4 — SECTOR ANALYSIS")
    print("=" * 60)

    sectors = get_sector_analysis()

    if sectors.empty:

        print(
            "Sector analysis unavailable."
        )

    else:

        print(
            f"Sectors analyzed: "
            f"{len(sectors)}"
        )


    # ========================================================
    # STEP 5 — FULL TECHNICAL SCAN
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 5 — FULL NSE TECHNICAL SCAN")
    print("=" * 60)

    technical = run_technical_scan(
        universe
    )

    if technical.empty:

        print(
            "Technical scan failed."
        )

        return

    technical = enrich_with_universe(
        technical,
        universe
    )

    save_csv(
        technical,
        "technical_scan.csv"
    )


    # ========================================================
    # STEP 6 — INITIAL RANKING
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 6 — INITIAL TECHNICAL RANKING")
    print("=" * 60)

    initial_ranked = rank_stocks(
        technical,
        sector_data=sectors
    )

    if initial_ranked.empty:

        print(
            "Ranking failed."
        )

        return


    # ========================================================
    # STEP 7 — FUNDAMENTAL SHORTLIST
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 7 — FUNDAMENTAL SHORTLIST")
    print("=" * 60)

    fundamental_symbols = (
        create_fundamental_shortlist(
            initial_ranked
        )
    )

    print(
        f"Fundamental candidates: "
        f"{len(fundamental_symbols)}"
    )


    # ========================================================
    # STEP 8 — FUNDAMENTAL ANALYSIS
    # ========================================================

    fundamentals = pd.DataFrame()

    if fundamental_symbols:

        fundamentals = get_fundamentals(
            universe,
            symbols=fundamental_symbols
        )

    save_csv(
        fundamentals,
        "fundamentals.csv"
    )


    # ========================================================
    # STEP 9 — FINAL RANKING
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 9 — FINAL RANKING")
    print("=" * 60)

    ranked = finalize_ranking(
        technical,
        sectors,
        fundamentals
    )

    if ranked.empty:

        print(
            "Final ranking unavailable."
        )

        return


    # Main stock file
    save_csv(
        ranked,
        "stocks.csv"
    )


    # ========================================================
    # STEP 10 — SETUP SUMMARY
    # ========================================================

    summary = create_setup_summary(
        ranked
    )

    save_csv(
        summary,
        "setup_summary.csv"
    )


    # ========================================================
    # STEP 11 — WATCHLISTS
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 11 — WATCHLISTS")
    print("=" * 60)

    watchlists = create_watchlists(
        ranked
    )

    save_watchlists(
        watchlists
    )


    # ========================================================
    # STEP 12 — EXCEL EXPORTS
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 12 — EXCEL EXPORTS")
    print("=" * 60)

    create_excel_exports(
        ranked,
        watchlists
    )


    # ========================================================
    # STEP 13 — DASHBOARD JSON
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 13 — DASHBOARD DATA")
    print("=" * 60)

    create_dashboard_json(
        market,
        breadth,
        sectors,
        ranked,
        watchlists
    )


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("PRODUCTION SCAN COMPLETED")
    print("=" * 70)

    print()
    print(
        f"NSE universe       : "
        f"{len(universe)}"
    )

    print(
        f"Technical stocks   : "
        f"{len(technical)}"
    )

    print(
        f"Fundamental stocks : "
        f"{len(fundamentals)}"
    )

    print(
        f"Final ranked       : "
        f"{len(ranked)}"
    )

    print()

    print(
        "Watchlists created:"
    )

    for name, df in (
        watchlists or {}
    ).items():

        print(
            f"  {name:<15} "
            f"{len(df)}"
        )

    print()
    print(
        f"Dashboard file:"
    )

    print(
        f"  {JSON_FILE}"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":

    main()

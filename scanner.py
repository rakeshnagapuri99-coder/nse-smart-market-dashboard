# ============================================================
# NSE SMART MARKET DASHBOARD V2
# MASTER PRODUCTION SCANNER
# Created by Rakesh Nagapuri
# ============================================================

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from engines.nse_universe import get_nse_universe, save_universe
from engines.technical_engine import calculate_technical_indicators
from engines.market_breadth import get_market_breadth
from engines.market_engine import get_market_regime
from engines.sector_engine import get_sector_analysis
from engines.ranking_engine import (
    rank_stocks,
    create_watchlists,
    create_setup_summary
)
from engines.fundamental_engine import get_fundamentals


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = Path("output")
EXPORT_DIR = OUTPUT_DIR / "exports"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

EXPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

BATCH_SIZE = 100
TECHNICAL_PERIOD = "2y"


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):

    try:

        if value is None:
            return np.nan

        value = float(value)

        if not math.isfinite(value):
            return np.nan

        return value

    except (TypeError, ValueError):

        return np.nan


def clean_value(value):

    if value is None:
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):

        if not np.isfinite(value):
            return None

        return float(value)

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return value

    if isinstance(value, bool):
        return value

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    return value


def clean_dataframe_for_json(df):

    if df is None or df.empty:
        return []

    records = []

    for record in df.to_dict(
        orient="records"
    ):

        cleaned = {
            str(key): clean_value(value)
            for key, value in record.items()
        }

        records.append(cleaned)

    return records


def save_csv(df, filename):

    if df is None:
        return

    if df.empty:

        print(
            f"Skipping empty file: {filename}"
        )

        return

    path = OUTPUT_DIR / filename

    df.to_csv(
        path,
        index=False
    )

    print(
        f"Saved: {path}"
    )


# ============================================================
# YAHOO DATA EXTRACTION
# ============================================================

def extract_symbol_data(
    raw_data,
    yahoo_symbol
):

    if raw_data is None or raw_data.empty:
        return None

    try:

        data = raw_data.copy()

        # ----------------------------------------------------
        # MultiIndex handling
        # ----------------------------------------------------

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            level0 = data.columns.get_level_values(0)
            level1 = data.columns.get_level_values(1)

            if yahoo_symbol in level0:

                data = data[
                    yahoo_symbol
                ]

            elif yahoo_symbol in level1:

                data = data.xs(
                    yahoo_symbol,
                    axis=1,
                    level=1
                )

            else:

                # If only one symbol was returned
                if len(
                    set(level0)
                ) == 1:

                    data.columns = level1

                elif len(
                    set(level1)
                ) == 1:

                    data.columns = level0

                else:

                    return None

        # ----------------------------------------------------
        # Standardize columns
        # ----------------------------------------------------

        data.columns = [
            str(column)
            .strip()
            for column in data.columns
        ]

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        if not all(
            column in data.columns
            for column in required
        ):

            return None

        data = data[
            required
        ].copy()

        for column in required:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

        data = data.dropna(
            subset=[
                "Close"
            ]
        )

        return data

    except Exception as error:

        print(
            f"Unable to extract "
            f"{yahoo_symbol}: {error}"
        )

        return None


# ============================================================
# TECHNICAL SCAN
# ============================================================

def scan_technical_data(
    universe
):

    if universe is None or universe.empty:

        return pd.DataFrame()

    if "YAHOO_SYMBOL" not in universe.columns:

        if "SYMBOL" not in universe.columns:
            return pd.DataFrame()

        universe = universe.copy()

        universe["YAHOO_SYMBOL"] = (
            universe["SYMBOL"]
            .astype(str)
            .str.strip()
            .str.upper()
            .apply(
                lambda symbol:
                    f"{symbol}.NS"
            )
        )

    yahoo_symbols = (
        universe[
            "YAHOO_SYMBOL"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    print()
    print(
        "=" * 70
    )

    print(
        "TECHNICAL MARKET SCAN"
    )

    print(
        f"Universe symbols: {len(yahoo_symbols)}"
    )

    print(
        "=" * 70
    )

    results = []

    total_batches = (
        math.ceil(
            len(yahoo_symbols) /
            BATCH_SIZE
        )
    )

    for batch_number, start in enumerate(
        range(
            0,
            len(yahoo_symbols),
            BATCH_SIZE
        ),
        start=1
    ):

        batch = yahoo_symbols[
            start:
            start + BATCH_SIZE
        ]

        print()
        print(
            f"Technical batch "
            f"{batch_number}/{total_batches}"
        )

        try:

            raw = yf.download(
                tickers=batch,
                period=TECHNICAL_PERIOD,
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                progress=False,
                threads=True
            )

        except Exception as error:

            print(
                f"Batch download failed: {error}"
            )

            continue

        for symbol in batch:

            data = extract_symbol_data(
                raw,
                symbol
            )

            if (
                data is None or
                len(data) < 200
            ):
                continue

            try:

                technical =
                    calculate_technical_indicators(
                        data
                    )

                if (
                    technical is None or
                    technical.empty
                ):
                    continue

                latest = technical.iloc[-1]

                if pd.isna(
                    latest.get("SMA200")
                ):
                    continue

                # ------------------------------------------------
                # Preserve latest row as stock record
                # ------------------------------------------------

                record = {
                    "symbol":
                        symbol.replace(
                            ".NS",
                            ""
                        ),
                    "yahoo_symbol":
                        symbol,
                    "date":
                        technical.index[-1]
                }

                for column in technical.columns:

                    record[column] = latest[
                        column
                    ]

                results.append(
                    record
                )

            except Exception as error:

                print(
                    f"Technical calculation failed "
                    f"for {symbol}: {error}"
                )

        print(
            f"Stocks analysed so far: "
            f"{len(results)}"
        )

    if not results:
        return pd.DataFrame()

    result = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Clean duplicate symbols
    # --------------------------------------------------------

    result = result.drop_duplicates(
        subset=[
            "symbol"
        ],
        keep="last"
    )

    result = result.reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Add NSE master information
    # --------------------------------------------------------

    master = universe.copy()

    if "SYMBOL" in master.columns:

        master["SYMBOL"] = (
            master["SYMBOL"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        master = master.rename(
            columns={
                "SYMBOL":
                    "nse_symbol"
            }
        )

        master = master[
            [
                column
                for column in [
                    "nse_symbol",
                    "COMPANY_NAME",
                    "NAME OF COMPANY",
                    "ISIN NUMBER",
                    " SERIES",
                    "SERIES"
                ]
                if column in master.columns
            ]
        ].drop_duplicates(
            subset=[
                "nse_symbol"
            ]
        )

        result = result.merge(
            master,
            left_on="symbol",
            right_on="nse_symbol",
            how="left"
        )

    print()
    print(
        f"Technical scan completed: "
        f"{len(result)} stocks"
    )

    return result


# ============================================================
# FUNDAMENTAL SHORTLIST
# ============================================================

def create_fundamental_shortlist(
    technical_data
):

    if (
        technical_data is None or
        technical_data.empty
    ):
        return []

    data = technical_data.copy()

    selected = set()

    # --------------------------------------------------------
    # Top technical stocks
    # --------------------------------------------------------

    try:

        ranked = data.sort_values(
            by=[
                "technical_score"
            ],
            ascending=False
        )

    except Exception:

        ranked = data

    selected.update(
        ranked.head(
            300
        )[
            "symbol"
        ]
        .dropna()
        .tolist()
    )

    # --------------------------------------------------------
    # Near 52W high
    # --------------------------------------------------------

    if "Distance_From_52W_High_Pct" in data.columns:

        high_candidates = (
            data[
                data[
                    "Distance_From_52W_High_Pct"
                ] >= -10
            ]
            .sort_values(
                by=[
                    "Distance_From_52W_High_Pct"
                ],
                ascending=False
            )
            .head(150)
        )

        selected.update(
            high_candidates[
                "symbol"
            ]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # Around 200 DMA
    # --------------------------------------------------------

    if "Distance_From_200DMA_Pct" in data.columns:

        dma_candidates = (
            data[
                data[
                    "Distance_From_200DMA_Pct"
                ].between(
                    -7,
                    7
                )
            ]
            .sort_values(
                by=[
                    "technical_score"
                ],
                ascending=False
            )
            .head(150)
        )

        selected.update(
            dma_candidates[
                "symbol"
            ]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # Positive momentum
    # --------------------------------------------------------

    if "Momentum" in data.columns:

        momentum_candidates = (
            data[
                data[
                    "Momentum"
                ].astype(str).str.lower().isin(
                    [
                        "positive",
                        "strong positive"
                    ]
                )
            ]
            .sort_values(
                by=[
                    "technical_score"
                ],
                ascending=False
            )
            .head(150)
        )

        selected.update(
            momentum_candidates[
                "symbol"
            ]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # Limit fundamental API load
    # --------------------------------------------------------

    selected = list(
        dict.fromkeys(
            [
                str(symbol)
                .upper()
                .replace(
                    ".NS",
                    ""
                )
                for symbol in selected
            ]
        )
    )

    selected = selected[
        :500
    ]

    print()
    print(
        f"Fundamental shortlist: "
        f"{len(selected)} stocks"
    )

    return selected


# ============================================================
# MERGE FUNDAMENTALS
# ============================================================

def merge_fundamental_data(
    ranked_data,
    fundamentals
):

    if (
        ranked_data is None or
        ranked_data.empty
    ):
        return ranked_data

    if (
        fundamentals is None or
        fundamentals.empty
    ):
        ranked_data = ranked_data.copy()

        ranked_data[
            "fundamental_data_available"
        ] = False

        ranked_data[
            "fundamental_status"
        ] = "Unavailable"

        return ranked_data

    stocks = ranked_data.copy()
    fund = fundamentals.copy()

    if "symbol" not in fund.columns:

        return stocks

    stocks["symbol"] = (
        stocks["symbol"]
        .astype(str)
        .str.upper()
        .str.replace(
            ".NS",
            "",
            regex=False
        )
    )

    fund["symbol"] = (
        fund["symbol"]
        .astype(str)
        .str.upper()
        .str.replace(
            ".NS",
            "",
            regex=False
        )
    )

    # --------------------------------------------------------
    # Remove conflicting columns from previous ranking
    # --------------------------------------------------------

    duplicate_columns = [
        column
        for column in fund.columns
        if (
            column != "symbol" and
            column in stocks.columns
        )
    ]

    # These fundamental columns should replace
    # temporary/empty ranking values.
    for column in duplicate_columns:

        stocks = stocks.drop(
            columns=[
                column
            ]
        )

    stocks = stocks.merge(
        fund,
        on="symbol",
        how="left"
    )

    # --------------------------------------------------------
    # Fundamental availability
    # --------------------------------------------------------

    if "fundamental_data_available" not in stocks.columns:

        stocks[
            "fundamental_data_available"
        ] = (
            ~stocks[
                "fundamental_score"
            ].isna()
        )

    stocks[
        "fundamental_status"
    ] = (
        stocks[
            "fundamental_data_available"
        ]
        .apply(
            lambda value:
                "Available"
                if bool(value)
                else "Unavailable"
        )
    )

    return stocks


# ============================================================
# FINAL RANKING
# ============================================================

def create_final_ranking(
    technical_data,
    fundamentals,
    sector_data,
    market_regime
):

    print()
    print(
        "=" * 70
    )

    print(
        "FINAL STOCK RANKING"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # First ranking with technical data
    # --------------------------------------------------------

    ranked = rank_stocks(
        technical_data,
        fundamental_data=fundamentals,
        sector_data=sector_data,
        market_regime=market_regime
    )

    if ranked.empty:
        return ranked

    # --------------------------------------------------------
    # Ensure fundamentals are fully merged
    # --------------------------------------------------------

    ranked = merge_fundamental_data(
        ranked,
        fundamentals
    )

    # --------------------------------------------------------
    # Recalculate final scores after all data exists
    # --------------------------------------------------------

    ranked = rank_stocks(
        ranked,
        fundamental_data=None,
        sector_data=sector_data,
        market_regime=market_regime
    )

    # --------------------------------------------------------
    # Make sure fundamental score survives if available
    # --------------------------------------------------------

    if (
        fundamentals is not None and
        not fundamentals.empty
    ):

        fund_columns = [
            column
            for column in fundamentals.columns
            if column != "symbol"
        ]

        existing_fundamental_data = (
            fundamentals[
                [
                    "symbol"
                ] +
                [
                    column
                    for column in fund_columns
                    if column not in ranked.columns
                ]
            ]
            if "symbol" in fundamentals.columns
            else pd.DataFrame()
        )

        if (
            not existing_fundamental_data.empty
        ):

            ranked = ranked.merge(
                existing_fundamental_data,
                on="symbol",
                how="left"
            )

    # --------------------------------------------------------
    # If ranking recalculation removed/overwrote
    # fundamental score, calculate it again.
    # --------------------------------------------------------

    if (
        "fundamental_score" not in ranked.columns
    ):

        ranked["fundamental_score"] = np.nan

    # --------------------------------------------------------
    # Final score directly from existing scores
    # --------------------------------------------------------

    technical_score = pd.to_numeric(
        ranked[
            "technical_score"
        ],
        errors="coerce"
    ).fillna(0)

    fundamental_score = pd.to_numeric(
        ranked[
            "fundamental_score"
        ],
        errors="coerce"
    )

    sector_adjustment = pd.to_numeric(
        ranked.get(
            "sector_adjustment",
            0
        ),
        errors="coerce"
    ).fillna(0)

    market_adjustment = pd.to_numeric(
        ranked.get(
            "market_regime_adjustment",
            0
        ),
        errors="coerce"
    ).fillna(0)

    final_score = np.where(
        fundamental_score.notna(),
        (
            technical_score * 0.60 +
            fundamental_score.fillna(0) * 0.40
        ),
        technical_score
    )

    final_score = (
        pd.Series(
            final_score,
            index=ranked.index
        )
        +
        sector_adjustment
        +
        market_adjustment
    )

    ranked[
        "overall_score"
    ] = (
        final_score
        .clip(
            lower=0,
            upper=100
        )
        .round(2)
    )

    # --------------------------------------------------------
    # Final ranking
    # --------------------------------------------------------

    ranked = ranked.sort_values(
        by=[
            "overall_score",
            "technical_score"
        ],
        ascending=False
    ).reset_index(
        drop=True
    )

    ranked[
        "rank"
    ] = np.arange(
        1,
        len(ranked) + 1
    )

    # --------------------------------------------------------
    # Final rating
    # --------------------------------------------------------

    def rating(score):

        score = safe_float(
            score
        )

        if pd.isna(score):
            return "Unrated"

        if score >= 80:
            return "Excellent Setup"

        if score >= 70:
            return "Strong Setup"

        if score >= 60:
            return "Good Setup"

        if score >= 50:
            return "Watch"

        if score >= 40:
            return "Confirmation Required"

        return "Weak / Avoid"

    ranked[
        "rating"
    ] = (
        ranked[
            "overall_score"
        ]
        .apply(rating)
    )

    return ranked


# ============================================================
# EXCEL EXPORT
# ============================================================

def export_excel(
    ranked_data,
    watchlists
):

    print()
    print(
        "=" * 70
    )

    print(
        "EXCEL EXPORT"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # All stocks
    # --------------------------------------------------------

    if (
        ranked_data is not None and
        not ranked_data.empty
    ):

        try:

            path = (
                EXPORT_DIR /
                "all_stocks.xlsx"
            )

            ranked_data.to_excel(
                path,
                index=False
            )

            print(
                f"Saved: {path}"
            )

        except Exception as error:

            print(
                f"Unable to export all stocks: "
                f"{error}"
            )

    # --------------------------------------------------------
    # Watchlists
    # --------------------------------------------------------

    for name, data in (
        watchlists or {}
    ).items():

        if (
            data is None or
            data.empty
        ):
            continue

        path = (
            EXPORT_DIR /
            f"{name}.xlsx"
        )

        try:

            data.to_excel(
                path,
                index=False
            )

            print(
                f"Saved: {path}"
            )

        except Exception as error:

            print(
                f"Unable to export "
                f"{name}: {error}"
            )


# ============================================================
# DASHBOARD JSON
# ============================================================

def create_dashboard_json(
    market,
    breadth,
    sectors,
    ranked_data,
    watchlists
):

    dashboard = {

        "generated_at":
            pd.Timestamp.now(
                tz="Asia/Kolkata"
            ).isoformat(),

        "market":
            market or {},

        "breadth":
            breadth or {},

        "sectors":
            clean_dataframe_for_json(
                sectors
            ),

        "stocks":
            clean_dataframe_for_json(
                ranked_data
            ),

        "watchlists": {
            name:
                clean_dataframe_for_json(
                    data
                )
            for name, data
            in (
                watchlists or {}
            ).items()
        }

    }

    path = (
        OUTPUT_DIR /
        "dashboard_data.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dashboard,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(
        f"Saved dashboard JSON: {path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 70
    )

    print(
        "NSE SMART MARKET DASHBOARD V2"
    )

    print(
        "MASTER PRODUCTION SCANNER"
    )

    print(
        "Created by Rakesh Nagapuri"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # 1. NSE UNIVERSE
    # ========================================================

    print()
    print(
        "STEP 1 — NSE EQUITY UNIVERSE"
    )

    universe = get_nse_universe()

    if universe.empty:

        raise RuntimeError(
            "NSE equity universe could not be loaded."
        )

    save_universe(
        universe
    )

    # ========================================================
    # 2. MARKET BREADTH
    # ========================================================

    print()
    print(
        "STEP 2 — MARKET BREADTH"
    )

    breadth = get_market_breadth(
        universe
    )

    if breadth is None:
        breadth = {}

    # ========================================================
    # 3. MARKET REGIME
    # ========================================================

    print()
    print(
        "STEP 3 — MARKET REGIME"
    )

    market = get_market_regime(
        breadth=breadth
    )

    if market is None:
        market = {}

    # ========================================================
    # 4. SECTOR ANALYSIS
    # ========================================================

    print()
    print(
        "STEP 4 — SECTOR ANALYSIS"
    )

    sector_data = get_sector_analysis()

    if sector_data is None:
        sector_data = pd.DataFrame()

    # ========================================================
    # 5. TECHNICAL SCAN
    # ========================================================

    print()
    print(
        "STEP 5 — FULL TECHNICAL SCAN"
    )

    technical_data = scan_technical_data(
        universe
    )

    if technical_data.empty:

        raise RuntimeError(
            "Technical scan returned no stocks."
        )

    save_csv(
        technical_data,
        "technical_scan.csv"
    )

    # ========================================================
    # 6. INITIAL TECHNICAL RANKING
    # ========================================================

    print()
    print(
        "STEP 6 — INITIAL TECHNICAL RANKING"
    )

    initial_ranking = rank_stocks(
        technical_data,
        fundamental_data=None,
        sector_data=sector_data,
        market_regime=market
    )

    # ========================================================
    # 7. FUNDAMENTAL SHORTLIST
    # ========================================================

    print()
    print(
        "STEP 7 — FUNDAMENTAL SHORTLIST"
    )

    fundamental_symbols = (
        create_fundamental_shortlist(
            initial_ranking
        )
    )

    # ========================================================
    # 8. FUNDAMENTAL ANALYSIS
    # ========================================================

    print()
    print(
        "STEP 8 — FUNDAMENTAL ANALYSIS"
    )

    fundamentals = get_fundamentals(
        universe,
        symbols=fundamental_symbols,
        use_cache=True
    )

    if (
        fundamentals is not None and
        not fundamentals.empty
    ):

        save_csv(
            fundamentals,
            "fundamentals.csv"
        )

    # ========================================================
    # 9. FINAL RANKING
    # ========================================================

    print()
    print(
        "STEP 9 — FINAL RANKING"
    )

    ranked = create_final_ranking(
        technical_data,
        fundamentals,
        sector_data,
        market
    )

    if ranked.empty:

        raise RuntimeError(
            "Final ranking returned no stocks."
        )

    save_csv(
        ranked,
        "stocks.csv"
    )

    # ========================================================
    # 10. WATCHLISTS
    # ========================================================

    print()
    print(
        "STEP 10 — SMART WATCHLISTS"
    )

    watchlists = create_watchlists(
        ranked,
        market_regime=market
    )

    # ========================================================
    # 11. WATCHLIST CSV FILES
    # ========================================================

    for name, data in (
        watchlists.items()
    ):

        save_csv(
            data,
            f"{name}.csv"
        )

    # ========================================================
    # 12. SETUP SUMMARY
    # ========================================================

    print()
    print(
        "STEP 11 — SETUP SUMMARY"
    )

    setup_summary = (
        create_setup_summary(
            ranked
        )
    )

    save_csv(
        setup_summary,
        "setup_summary.csv"
    )

    # ========================================================
    # 13. MARKET FILES
    # ========================================================

    print()
    print(
        "STEP 12 — MARKET OUTPUT FILES"
    )

    if market:

        market_df = pd.DataFrame(
            [
                market
            ]
        )

        save_csv(
            market_df,
            "market_regime.csv"
        )

    # ========================================================
    # 14. EXCEL EXPORT
    # ========================================================

    print()
    print(
        "STEP 13 — EXCEL EXPORT"
    )

    export_excel(
        ranked,
        watchlists
    )

    # ========================================================
    # 15. DASHBOARD JSON
    # ========================================================

    print()
    print(
        "STEP 14 — DASHBOARD JSON"
    )

    create_dashboard_json(
        market,
        breadth,
        sector_data,
        ranked,
        watchlists
    )

    # ========================================================
    # 16. SUMMARY
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "PRODUCTION SCAN COMPLETED"
    )

    print(
        "=" * 70
    )

    print()

    print(
        f"NSE Universe: "
        f"{len(universe)}"
    )

    print(
        f"Technical Stocks: "
        f"{len(technical_data)}"
    )

    print(
        f"Fundamental Stocks: "
        f"{len(fundamentals) if fundamentals is not None else 0}"
    )

    print(
        f"Final Ranked Stocks: "
        f"{len(ranked)}"
    )

    print()

    print(
        "Watchlists:"
    )

    for name, data in (
        watchlists.items()
    ):

        print(
            f"  {name}: "
            f"{len(data)}"
        )

    print()

    print(
        f"Dashboard JSON: "
        f"{OUTPUT_DIR / 'dashboard_data.json'}"
    )

    print(
        f"Excel exports: "
        f"{EXPORT_DIR}"
    )

    print()
    print(
        "=" * 70
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()

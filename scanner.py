"""
NSE SMART MARKET DASHBOARD
MASTER SCANNER / DATA PIPELINE

Pipeline:
1. NSE universe
2. Technical scan
3. Fundamentals
4. Market breadth
5. Market regime
6. Sector analysis
7. Sector mapping
8. Merge stock data
9. Ranking
10. Watchlists
11. Setup summary
12. Compact dashboard JSON
13. Excel exports
14. Output validation
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# =========================================================
# ENGINE IMPORTS
# =========================================================

from engines.nse_universe import get_nse_universe
from engines.technical_engine import calculate_technical_indicators
from engines.market_breadth import get_market_breadth
from engines.market_engine import get_market_regime
from engines.sector_engine import get_sector_analysis
from engines.sector_mapping import load_sector_mapping
from engines.ranking_engine import (
    rank_stocks,
    create_watchlists,
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
EXPORT_DIR = OUTPUT_DIR / "exports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# OUTPUT FILES
# =========================================================

TECHNICAL_OUTPUT = OUTPUT_DIR / "technical_scan.csv"
FUNDAMENTAL_OUTPUT = OUTPUT_DIR / "fundamentals.csv"
STOCK_OUTPUT = OUTPUT_DIR / "stocks.csv"
MARKET_OUTPUT = OUTPUT_DIR / "market_regime.csv"
BREADTH_OUTPUT = OUTPUT_DIR / "market_breadth.csv"
BREADTH_STOCK_OUTPUT = OUTPUT_DIR / "market_breadth_stocks.csv"
SECTOR_OUTPUT = OUTPUT_DIR / "sector_analysis.csv"
SETUP_OUTPUT = OUTPUT_DIR / "setup_summary.csv"
DASHBOARD_OUTPUT = OUTPUT_DIR / "dashboard_data.json"


# =========================================================
# JSON HELPERS
# =========================================================

def clean_value(value: Any) -> Any:
    """Convert pandas/numpy values into JSON-safe values."""

    if value is None:
        return None

    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)

    if isinstance(value, (np.floating, np.float64, np.float32)):
        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            return None

        return value

    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, dict):
        return {
            str(k): clean_value(v)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            clean_value(v)
            for v in value
        ]

    return value


def dataframe_to_records(
    df: pd.DataFrame,
) -> list[dict]:

    if df is None or df.empty:
        return []

    records = []

    for record in df.to_dict(orient="records"):
        records.append(
            {
                str(k): clean_value(v)
                for k, v in record.items()
            }
        )

    return records


def safe_write_json(
    path: Path,
    payload: dict,
) -> None:

    temp_path = path.with_suffix(".tmp")

    with open(
        temp_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            clean_value(payload),
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    os.replace(temp_path, path)


# =========================================================
# COLUMN HELPERS
# =========================================================

def find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    if df is None or df.empty:
        return None

    lookup = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:

        key = str(candidate).strip().lower()

        if key in lookup:
            return lookup[key]

    return None


def rename_if_exists(
    df: pd.DataFrame,
    aliases: dict[str, list[str]],
) -> pd.DataFrame:

    if df is None:
        return df

    rename_map = {}

    for target, candidates in aliases.items():

        source = find_column(
            df,
            candidates,
        )

        if (
            source is not None
            and source != target
        ):
            rename_map[source] = target

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


# =========================================================
# STEP 1 — NSE UNIVERSE
# =========================================================

def build_universe() -> pd.DataFrame:

    print(
        "\n"
        "====================================================\n"
        "STEP 1 — NSE UNIVERSE\n"
        "===================================================="
    )

    universe = get_nse_universe()

    if universe is None:
        raise RuntimeError(
            "NSE universe could not be loaded."
        )

    if not isinstance(
        universe,
        pd.DataFrame,
    ):
        universe = pd.DataFrame(universe)

    if universe.empty:
        raise RuntimeError(
            "NSE universe is empty."
        )

    print(
        f"Universe stocks: {len(universe):,}"
    )

    return universe


# =========================================================
# STEP 2 — TECHNICAL SCAN
# =========================================================

def build_technical_scan(
    universe: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        "====================================================\n"
        "STEP 2 — TECHNICAL SCAN\n"
        "===================================================="
    )

    results = []

    symbol_col = find_column(
        universe,
        [
            "YAHOO_SYMBOL",
            "Yahoo_Symbol",
            "Symbol",
            "SYMBOL",
        ],
    )

    if symbol_col is None:
        raise RuntimeError(
            "Yahoo/NSE symbol column not found."
        )

    total = len(universe)

    for position, (_, row) in enumerate(
        universe.iterrows(),
        start=1,
    ):

        yahoo_symbol = row.get(symbol_col)

        if (
            yahoo_symbol is None
            or str(yahoo_symbol).strip() == ""
        ):
            continue

        symbol = str(
            yahoo_symbol
        ).strip()

        try:

            result = calculate_technical_indicators(
                symbol
            )

            if result is None:
                continue

            if isinstance(
                result,
                pd.DataFrame,
            ):

                if result.empty:
                    continue

                latest = result.iloc[-1].to_dict()

            elif isinstance(
                result,
                dict,
            ):

                latest = result.copy()

            else:
                continue

            latest["Symbol"] = (
                symbol.replace(".NS", "")
            )

            latest["YAHOO_SYMBOL"] = symbol

            for column in universe.columns:

                if column not in latest:
                    latest[column] = row[column]

            results.append(latest)

        except Exception as exc:

            print(
                f"Technical error {symbol}: {exc}"
            )

        if (
            position % 100 == 0
            or position == total
        ):

            print(
                "Technical progress: "
                f"{position:,}/{total:,}"
            )

    technical = pd.DataFrame(results)

    if technical.empty:
        raise RuntimeError(
            "Technical scan returned no data."
        )

    technical = rename_if_exists(
        technical,
        {
            "Symbol": [
                "symbol",
                "SYMBOL",
            ],
            "Close": [
                "close",
                "Price",
                "price",
            ],
        },
    )

    technical.to_csv(
        TECHNICAL_OUTPUT,
        index=False,
    )

    print(
        f"Technical records: {len(technical):,}"
    )

    return technical


# =========================================================
# STEP 3 — FUNDAMENTALS
# =========================================================

def build_fundamentals(
    technical: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        "====================================================\n"
        "STEP 3 — FUNDAMENTALS\n"
        "===================================================="
    )

    try:

        from engines.fundamental_engine import (
            get_fundamentals,
        )

    except ImportError:

        print(
            "Fundamental engine unavailable."
        )

        return pd.DataFrame()

    symbol_col = find_column(
        technical,
        [
            "Symbol",
            "symbol",
            "SYMBOL",
        ],
    )

    if symbol_col is None:
        return pd.DataFrame()

    symbols = (
        technical[symbol_col]
        .dropna()
        .astype(str)
        .str.replace(
            ".NS",
            "",
            regex=False,
        )
        .unique()
        .tolist()
    )

    try:

        fundamentals = get_fundamentals(
            symbols
        )

    except TypeError:

        try:

            fundamentals = get_fundamentals(
                technical
            )

        except Exception as exc:

            print(
                f"Fundamental scan failed: {exc}"
            )

            return pd.DataFrame()

    except Exception as exc:

        print(
            f"Fundamental scan failed: {exc}"
        )

        return pd.DataFrame()

    if fundamentals is None:
        return pd.DataFrame()

    if not isinstance(
        fundamentals,
        pd.DataFrame,
    ):
        fundamentals = pd.DataFrame(
            fundamentals
        )

    if fundamentals.empty:

        print(
            "No fundamental records returned."
        )

        return fundamentals

    fundamentals.to_csv(
        FUNDAMENTAL_OUTPUT,
        index=False,
    )

    print(
        f"Fundamental records: "
        f"{len(fundamentals):,}"
    )

    return fundamentals


# =========================================================
# STEP 4 — MARKET BREADTH
# =========================================================

def build_breadth():

    print(
        "\n"
        "====================================================\n"
        "STEP 4 — MARKET BREADTH\n"
        "===================================================="
    )

    try:

        result = get_market_breadth()

    except Exception as exc:

        print(
            f"Market breadth failed: {exc}"
        )

        return {}, pd.DataFrame()

    summary = {}
    stocks = pd.DataFrame()

    if isinstance(result, tuple):

        if len(result) >= 1:
            summary = result[0]

        if len(result) >= 2:
            stocks = result[1]

    elif isinstance(
        result,
        dict,
    ):

        summary = result

    elif isinstance(
        result,
        pd.DataFrame,
    ):

        stocks = result

    if not isinstance(
        summary,
        dict,
    ):
        summary = {}

    if not isinstance(
        stocks,
        pd.DataFrame,
    ):

        try:
            stocks = pd.DataFrame(stocks)

        except Exception:
            stocks = pd.DataFrame()

    if not stocks.empty:

        stocks.to_csv(
            BREADTH_STOCK_OUTPUT,
            index=False,
        )

    if summary:

        pd.DataFrame(
            [summary]
        ).to_csv(
            BREADTH_OUTPUT,
            index=False,
        )

    print(
        "Breadth completed."
    )

    return summary, stocks


# =========================================================
# STEP 5 — MARKET REGIME
# =========================================================

def build_market_regime(
    breadth_summary,
):

    print(
        "\n"
        "====================================================\n"
        "STEP 5 — MARKET REGIME\n"
        "===================================================="
    )

    market = {}

    try:

        market = get_market_regime(
            breadth_summary
        )

    except TypeError:

        try:

            market = get_market_regime()

        except Exception as exc:

            print(
                f"Market engine failed: {exc}"
            )

    except Exception as exc:

        print(
            f"Market engine failed: {exc}"
        )

    if isinstance(
        market,
        pd.DataFrame,
    ):

        if market.empty:
            market = {}

        else:
            market = (
                market.iloc[-1]
                .to_dict()
            )

    if not isinstance(
        market,
        dict,
    ):
        market = {}

    if isinstance(
        breadth_summary,
        dict,
    ):

        for key, value in breadth_summary.items():

            if key not in market:
                market[key] = value

    pd.DataFrame(
        [market]
    ).to_csv(
        MARKET_OUTPUT,
        index=False,
    )

    regime = market.get(
        "market_regime",
        market.get(
            "Regime",
            "Unavailable",
        ),
    )

    print(
        f"Market regime: {regime}"
    )

    return market


# =========================================================
# STEP 6 — SECTOR ANALYSIS
# =========================================================

def build_sector_analysis():

    print(
        "\n"
        "====================================================\n"
        "STEP 6 — SECTOR ANALYSIS\n"
        "===================================================="
    )

    try:

        sectors = get_sector_analysis()

    except Exception as exc:

        print(
            f"Sector analysis failed: {exc}"
        )

        return pd.DataFrame()

    if sectors is None:
        return pd.DataFrame()

    if not isinstance(
        sectors,
        pd.DataFrame,
    ):
        sectors = pd.DataFrame(sectors)

    if sectors.empty:
        return sectors

    sectors.to_csv(
        SECTOR_OUTPUT,
        index=False,
    )

    print(
        f"Sectors analysed: {len(sectors):,}"
    )

    return sectors


# =========================================================
# STEP 7 — SECTOR MAPPING
# =========================================================

def build_sector_mapping():

    print(
        "\n"
        "====================================================\n"
        "STEP 7 — NSE SECTOR MAPPING\n"
        "===================================================="
    )

    try:

        mapping = load_sector_mapping()

    except Exception as exc:

        print(
            f"Sector mapping failed: {exc}"
        )

        return pd.DataFrame()

    if mapping is None:
        return pd.DataFrame()

    if not isinstance(
        mapping,
        pd.DataFrame,
    ):
        mapping = pd.DataFrame(mapping)

    print(
        f"Sector mappings: {len(mapping):,}"
    )

    return mapping


# =========================================================
# STEP 8 — MERGE STOCK DATA
# =========================================================

def merge_stock_data(
    technical: pd.DataFrame,
    fundamentals: pd.DataFrame,
    sector_mapping: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        "====================================================\n"
        "STEP 8 — MERGE STOCK DATA\n"
        "===================================================="
    )

    stocks = technical.copy()

    stocks = rename_if_exists(
        stocks,
        {
            "Symbol": [
                "symbol",
                "SYMBOL",
            ],
        },
    )

    if "Symbol" not in stocks.columns:

        raise RuntimeError(
            "Technical dataset has no Symbol column."
        )

    stocks["Symbol"] = (
        stocks["Symbol"]
        .astype(str)
        .str.replace(
            ".NS",
            "",
            regex=False,
        )
    )

    # -----------------------------------------------------
    # Fundamentals
    # -----------------------------------------------------

    if (
        fundamentals is not None
        and not fundamentals.empty
    ):

        fundamentals = fundamentals.copy()

        fundamentals = rename_if_exists(
            fundamentals,
            {
                "Symbol": [
                    "symbol",
                    "SYMBOL",
                ],
            },
        )

        if "Symbol" in fundamentals.columns:

            fundamentals["Symbol"] = (
                fundamentals["Symbol"]
                .astype(str)
                .str.replace(
                    ".NS",
                    "",
                    regex=False,
                )
            )

            duplicate_columns = [
                column
                for column in fundamentals.columns
                if (
                    column in stocks.columns
                    and column != "Symbol"
                )
            ]

            if duplicate_columns:

                fundamentals = fundamentals.drop(
                    columns=duplicate_columns
                )

            stocks = stocks.merge(
                fundamentals,
                on="Symbol",
                how="left",
            )

    # -----------------------------------------------------
    # Sector mapping
    # -----------------------------------------------------

    if (
        sector_mapping is not None
        and not sector_mapping.empty
    ):

        mapping = sector_mapping.copy()

        mapping = rename_if_exists(
            mapping,
            {
                "Symbol": [
                    "symbol",
                    "SYMBOL",
                    "NSE_Symbol",
                ],
            },
        )

        if "Symbol" in mapping.columns:

            mapping["Symbol"] = (
                mapping["Symbol"]
                .astype(str)
                .str.replace(
                    ".NS",
                    "",
                    regex=False,
                )
            )

            keep_columns = [
                column
                for column in [
                    "Symbol",
                    "primary_sector",
                    "primary_sector_index",
                    "primary_sector_type",
                    "sector_indices",
                ]
                if column in mapping.columns
            ]

            mapping = (
                mapping[
                    keep_columns
                ]
                .drop_duplicates(
                    "Symbol"
                )
            )

            duplicate_columns = [
                column
                for column in mapping.columns
                if (
                    column in stocks.columns
                    and column != "Symbol"
                )
            ]

            if duplicate_columns:

                stocks = stocks.drop(
                    columns=duplicate_columns
                )

            stocks = stocks.merge(
                mapping,
                on="Symbol",
                how="left",
            )

    # -----------------------------------------------------
    # Standard sector column
    # -----------------------------------------------------

    if "primary_sector" in stocks.columns:

        stocks["Primary_Sector"] = (
            stocks["primary_sector"]
            .fillna("Unknown")
        )

    elif "Sector" in stocks.columns:

        stocks["Primary_Sector"] = (
            stocks["Sector"]
            .fillna("Unknown")
        )

    else:

        stocks["Primary_Sector"] = "Unknown"

    return stocks


# =========================================================
# STEP 9 — RANK STOCKS
# =========================================================

def build_ranked_stocks(
    stocks: pd.DataFrame,
    market_regime,
    sector_analysis,
) -> pd.DataFrame:

    print(
        "\n"
        "====================================================\n"
        "STEP 9 — STOCK RANKING\n"
        "===================================================="
    )

    try:

        ranked = rank_stocks(
            stocks,
            market_regime=market_regime,
            sector_data=sector_analysis,
        )

    except TypeError:

        ranked = rank_stocks(
            stocks,
            None,
            sector_analysis,
            market_regime,
        )

    if ranked is None:

        raise RuntimeError(
            "Ranking engine returned no data."
        )

    if not isinstance(
        ranked,
        pd.DataFrame,
    ):
        ranked = pd.DataFrame(ranked)

    if ranked.empty:

        raise RuntimeError(
            "Ranking engine returned empty data."
        )

    ranked.to_csv(
        STOCK_OUTPUT,
        index=False,
    )

    print(
        f"Ranked stocks: {len(ranked):,}"
    )

    return ranked


# =========================================================
# STEP 10 — WATCHLISTS
# =========================================================

def build_watchlists(
    ranked: pd.DataFrame,
    market_regime,
) -> dict:

    print(
        "\n"
        "====================================================\n"
        "STEP 10 — WATCHLISTS\n"
        "===================================================="
    )

    try:

        result = create_watchlists(
            ranked,
            market_regime=market_regime,
        )

    except TypeError:

        result = create_watchlists(
            ranked,
            market_regime,
        )

    if isinstance(
        result,
        tuple,
    ):
        watchlists = result[0]
    else:
        watchlists = result

    if not isinstance(
        watchlists,
        dict,
    ):
        watchlists = {}

    cleaned = {}

    for name, value in watchlists.items():

        if isinstance(
            value,
            pd.DataFrame,
        ):

            cleaned[name] = dataframe_to_records(
                value
            )

        elif isinstance(
            value,
            list,
        ):

            cleaned[name] = [
                clean_value(item)
                for item in value
            ]

        else:

            cleaned[name] = []

    return cleaned


# =========================================================
# STEP 11 — SETUP SUMMARY
# =========================================================

def build_setup_summary(
    ranked: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        "====================================================\n"
        "STEP 11 — SETUP SUMMARY\n"
        "===================================================="
    )

    try:

        from engines.ranking_engine import (
            create_setup_summary,
        )

    except ImportError:

        return pd.DataFrame()

    try:

        summary = create_setup_summary(
            ranked
        )

    except Exception as exc:

        print(
            f"Setup summary failed: {exc}"
        )

        return pd.DataFrame()

    if summary is None:
        return pd.DataFrame()

    if not isinstance(
        summary,
        pd.DataFrame,
    ):
        summary = pd.DataFrame(summary)

    if not summary.empty:

        summary.to_csv(
            SETUP_OUTPUT,
            index=False,
        )

    return summary


# =========================================================
# COMPACT STOCK RECORD
# =========================================================

def compact_stock_record(
    row: dict,
) -> dict:

    aliases = {

        "symbol": [
            "Symbol",
            "symbol",
            "SYMBOL",
        ],

        "company_name": [
            "company_name",
            "Company_Name",
            "Company",
            "company",
            "longName",
            "name",
        ],

        "price": [
            "Close",
            "close",
            "Price",
            "price",
        ],

        "ltp": [
            "LTP",
            "ltp",
            "Live_Price",
            "live_price",
            "Current_Price",
        ],

        "previous_close": [
            "Previous_Close",
            "previous_close",
            "Prev_Close",
            "prev_close",
        ],

        "daily_return_pct": [
            "Daily_Return_Pct",
            "daily_return_pct",
            "Change_Pct",
            "change_pct",
        ],

        "sma20": [
            "SMA_20",
            "SMA20",
            "sma20",
        ],

        "sma50": [
            "SMA_50",
            "SMA50",
            "sma50",
        ],

        "sma100": [
            "SMA_100",
            "SMA100",
            "sma100",
        ],

        "sma200": [
            "SMA_200",
            "SMA200",
            "sma200",
            "200_DMA",
        ],

        "ema9": [
            "EMA_9",
            "EMA9",
            "ema9",
        ],

        "ema20": [
            "EMA_20",
            "EMA20",
            "ema20",
        ],

        "ema50": [
            "EMA_50",
            "EMA50",
            "ema50",
        ],

        "rsi": [
            "RSI_14",
            "RSI14",
            "RSI",
            "rsi",
        ],

        "atr": [
            "ATR_14",
            "ATR14",
            "ATR",
            "atr",
        ],

        "atr_pct": [
            "ATR_Pct",
            "ATR%",
            "atr_pct",
        ],

        "volume": [
            "Volume",
            "volume",
        ],

        "volume_ratio": [
            "Volume_Ratio",
            "volume_ratio",
        ],

        "high_52w": [
            "52W_High",
            "High_52W",
            "high_52w",
        ],

        "low_52w": [
            "52W_Low",
            "Low_52W",
            "low_52w",
        ],

        "distance_52w_high_pct": [
            "Distance_52W_High_Pct",
            "distance_52w_high_pct",
        ],

        "distance_52w_low_pct": [
            "Distance_52W_Low_Pct",
            "distance_52w_low_pct",
        ],

        "distance_200dma_pct": [
            "Distance_200DMA_Pct",
            "distance_200dma_pct",
            "Distance_From_200DMA",
        ],

        "above_200dma": [
            "Above_200DMA",
            "above_200dma",
        ],

        "support": [
            "Support",
            "support",
        ],

        "resistance": [
            "Resistance",
            "resistance",
        ],

        "trend": [
            "Trend",
            "trend",
        ],

        "momentum": [
            "Momentum",
            "momentum",
        ],

        "breakout": [
            "Breakout",
            "Breakout_Status",
            "breakout",
        ],

        "technical_score": [
            "Technical_Score",
            "technical_score",
        ],

        "fundamental_score": [
            "Fundamental_Score",
            "fundamental_score",
        ],

        "sector_score": [
            "Sector_Score",
            "sector_score",
        ],

        "overall_score": [
            "Overall_Score",
            "overall_score",
            "Score",
            "score",
        ],

        "setup": [
            "Setup",
            "setup",
            "Setup_Type",
            "setup_type",
        ],

        "primary_sector": [
            "Primary_Sector",
            "primary_sector",
            "Sector",
            "sector",
        ],

        "market_adjustment": [
            "Market_Adjustment",
            "market_adjustment",
        ],

        "entry_price": [
            "entry_price",
            "Entry_Price",
            "Entry",
        ],

        "entry_low": [
            "entry_low",
            "Entry_Low",
            "Entry_Zone_Low",
        ],

        "entry_high": [
            "entry_high",
            "Entry_High",
            "Entry_Zone_High",
        ],

        "stop_loss": [
            "stop_loss",
            "Stop_Loss",
            "Stop",
            "SL",
        ],

        "target_1": [
            "target_1",
            "Target_1",
            "T1",
        ],

        "target_2": [
            "target_2",
            "Target_2",
            "T2",
        ],

        "risk_reward_1": [
            "risk_reward_1",
            "Risk_Reward_1",
            "risk_reward",
            "Risk_Reward",
            "RR",
        ],

        "trade_plan_type": [
            "trade_plan_type",
            "Trade_Plan_Type",
        ],

        "trade_plan_status": [
            "trade_plan_status",
            "Trade_Plan_Status",
        ],

        "trade_plan_reason": [
            "trade_plan_reason",
            "Trade_Plan_Reason",
        ],

        "trade_plan_invalidation": [
            "trade_plan_invalidation",
            "Trade_Plan_Invalidation",
            "Invalidation",
        ],

        "trade_plan_quality": [
            "trade_plan_quality",
            "Trade_Plan_Quality",
        ],
    }

    result = {}

    for target, candidates in aliases.items():

        value = None

        for candidate in candidates:

            if candidate in row:

                value = row[candidate]

                if value is not None:

                    try:

                        if pd.isna(value):
                            continue

                    except (
                        TypeError,
                        ValueError,
                    ):
                        pass

                    break

        result[target] = clean_value(value)

    if result.get("symbol"):

        result["symbol"] = (
            str(result["symbol"])
            .replace(".NS", "")
        )

    if not result.get("company_name"):

        result["company_name"] = (
            result.get("symbol")
        )

    # Never treat EOD Close as live LTP.
    if (
        result.get("ltp") is not None
        and result.get("price") is not None
    ):

        try:

            if float(result["ltp"]) == float(
                result["price"]
            ):
                result["ltp"] = None

        except (
            TypeError,
            ValueError,
        ):
            pass

    return result


# =========================================================
# COMPACT WATCHLIST
# =========================================================

def compact_watchlist(
    records,
) -> list:

    output = []

    for record in records:

        if isinstance(
            record,
            dict,
        ):

            output.append(
                compact_stock_record(
                    record
                )
            )

        elif isinstance(
            record,
            str,
        ):

            output.append(
                {
                    "symbol":
                        record.replace(
                            ".NS",
                            "",
                        )
                }
            )

    return output


# =========================================================
# WATCHLIST COUNTS
# =========================================================

def create_watchlist_counts(
    watchlists: dict,
) -> dict:

    return {
        name: len(
            values
            if isinstance(
                values,
                list,
            )
            else []
        )
        for name, values
        in watchlists.items()
    }


# =========================================================
# SETUP COUNTS
# =========================================================

def create_setup_counts(
    ranked: pd.DataFrame,
) -> dict:

    if ranked is None or ranked.empty:
        return {}

    setup_col = find_column(
        ranked,
        [
            "Setup",
            "setup",
            "Setup_Type",
        ],
    )

    if setup_col is None:
        return {}

    values = (
        ranked[setup_col]
        .fillna("Unknown")
        .astype(str)
    )

    counts = values.value_counts()

    return {
        str(key): int(value)
        for key, value in counts.items()
    }


# =========================================================
# COMPACT MARKET
# =========================================================

def compact_market(
    market,
) -> dict:

    if not isinstance(
        market,
        dict,
    ):
        return {}

    important_keys = {

        "market_regime",
        "market_score",

        "nifty_price",
        "nifty_previous_close",
        "nifty_daily_return_pct",
        "nifty_score",
        "nifty_trend",
        "nifty_momentum",
        "nifty_rsi",

        "bank_nifty_price",
        "bank_nifty_previous_close",
        "bank_nifty_daily_return_pct",
        "bank_nifty_score",
        "bank_nifty_trend",
        "bank_nifty_momentum",
        "bank_nifty_rsi",

        "vix",
        "vix_interpretation",

        "equity_environment",
        "swing_environment",
        "breakout_environment",
        "intraday_environment",
        "options_environment",

        "support",
        "resistance",
        "pivot",

        "market_support",
        "market_resistance",
        "market_pivot",

        "bullish_trigger",
        "bearish_trigger",

        "market_scenario",
        "scenario",

        "market_data_authority",
        "data_authority",
        "generated_at",
    }

    result = {}

    for key in important_keys:

        if key in market:

            result[key] = clean_value(
                market[key]
            )

    for key in [
        "nifty",
        "bank_nifty",
        "vix",
    ]:

        if (
            key in market
            and isinstance(
                market[key],
                dict,
            )
        ):

            result[key] = clean_value(
                market[key]
            )

    return result


# =========================================================
# COMPACT BREADTH
# =========================================================

def compact_breadth(
    breadth,
) -> dict:

    if not isinstance(
        breadth,
        dict,
    ):
        return {}

    aliases = {

        "stocks_analyzed": [
            "stocks_analyzed",
            "Stocks_Analyzed",
            "Stocks analyzed",
        ],

        "above_20dma": [
            "above_20dma",
            "Above_20_DMA",
            "Above 20 DMA",
        ],

        "above_50dma": [
            "above_50dma",
            "Above_50_DMA",
            "Above 50 DMA",
        ],

        "above_200dma": [
            "above_200dma",
            "Above_200_DMA",
            "Above 200 DMA",
        ],

        "highs_52w": [
            "highs_52w",
            "52W_Highs",
            "52W Highs",
        ],

        "lows_52w": [
            "lows_52w",
            "52W_Lows",
            "52W Lows",
        ],

        "high_low_ratio": [
            "high_low_ratio",
            "High_Low_Ratio",
            "High/Low Ratio",
        ],

        "breadth_score": [
            "breadth_score",
            "Breadth_Score",
            "Breadth Score",
        ],

        "breadth_regime": [
            "breadth_regime",
            "Breadth_Regime",
            "Breadth Regime",
        ],
    }

    result = {}

    for target, keys in aliases.items():

        value = None

        for key in keys:

            if key in breadth:

                value = breadth[key]
                break

        result[target] = clean_value(
            value
        )

    return result


# =========================================================
# SECTOR RECORDS
# =========================================================

def compact_sectors(
    sectors: pd.DataFrame,
) -> list:

    if sectors is None or sectors.empty:
        return []

    return dataframe_to_records(
        sectors
    )


# =========================================================
# BUILD DASHBOARD JSON
# =========================================================

def build_dashboard_json(
    ranked: pd.DataFrame,
    market: dict,
    breadth: dict,
    sectors: pd.DataFrame,
    watchlists: dict,
    setup_summary: pd.DataFrame,
) -> dict:

    print(
        "\n"
        "====================================================\n"
        "STEP 12 — BUILD DASHBOARD JSON\n"
        "===================================================="
    )

    generated_at = (
        datetime.now()
        .astimezone()
        .isoformat()
    )

    stocks = [
        compact_stock_record(record)
        for record in ranked.to_dict(
            orient="records"
        )
    ]

    setup_records = dataframe_to_records(
        setup_summary
    )

    sector_records = compact_sectors(
        sectors
    )

    compacted_watchlists = {}

    for name, records in watchlists.items():

        compacted_watchlists[name] = (
            compact_watchlist(records)
        )

    watchlist_counts = (
        create_watchlist_counts(
            compacted_watchlists
        )
    )

    setup_counts = create_setup_counts(
        ranked
    )

    market_data_authority = (
        market.get(
            "market_data_authority",
            "Historical / EOD",
        )
        if isinstance(
            market,
            dict,
        )
        else "Historical / EOD"
    )

    live_ltp_available = any(
        stock.get("ltp") is not None
        for stock in stocks
    )

    latest_close_available = any(
        stock.get("price") is not None
        for stock in stocks
    )

    payload = {

        "dashboard": {

            "name":
                "NSE Smart Market Dashboard",

            "version":
                "3.0",

            "description":
                "Market intelligence, technicals, fundamentals and decision-support setups.",

            "created_by":
                "Rakesh Nagapuri",

            "data_type":
                "EOD / latest completed session unless live data is explicitly supplied.",
        },

        "generated_at":
            generated_at,

        "market_regime":
            compact_market(
                market
            ),

        "market_breadth":
            compact_breadth(
                breadth
            ),

        "sector_analysis":
            sector_records,

        "setup_summary":
            setup_records,

        "setup_counts":
            setup_counts,

        "stocks":
            stocks,

        "watchlists":
            compacted_watchlists,

        "watchlist_counts":
            watchlist_counts,

        "data_status": {

            "live_ltp_available":
                live_ltp_available,

            "latest_close_available":
                latest_close_available,

            "market_data_authority":
                market_data_authority,
        },
    }

    safe_write_json(
        DASHBOARD_OUTPUT,
        payload
    )

    size_mb = (
        DASHBOARD_OUTPUT.stat().st_size
        / (1024 * 1024)
    )

    print(
        f"Dashboard JSON written: "
        f"{DASHBOARD_OUTPUT}"
    )

    print(
        f"Dashboard JSON size: "
        f"{size_mb:.2f} MB"
    )

    print(
        f"Dashboard stocks: "
        f"{len(stocks):,}"
    )

    return payload


# =========================================================
# EXCEL EXPORTS
# =========================================================

def build_exports(
    ranked: pd.DataFrame,
    watchlists: dict,
    setup_summary: pd.DataFrame,
) -> None:

    print(
        "\n"
        "====================================================\n"
        "STEP 13 — EXPORT FILES\n"
        "===================================================="
    )

    ranked_path = (
        EXPORT_DIR /
        "all_ranked_stocks.xlsx"
    )

    try:

        ranked.to_excel(
            ranked_path,
            index=False,
        )

        print(
            f"Created: {ranked_path.name}"
        )

    except Exception as exc:

        print(
            f"Ranked Excel export failed: {exc}"
        )

    watchlist_path = (
        EXPORT_DIR /
        "watchlists.xlsx"
    )

    try:

        with pd.ExcelWriter(
            watchlist_path,
            engine="openpyxl",
        ) as writer:

            for name, records in watchlists.items():

                safe_name = (
                    str(name)[:31]
                    or "Watchlist"
                )

                if isinstance(
                    records,
                    list,
                ):
                    df = pd.DataFrame(records)

                elif isinstance(
                    records,
                    pd.DataFrame,
                ):
                    df = records.copy()

                else:
                    df = pd.DataFrame()

                df.to_excel(
                    writer,
                    sheet_name=safe_name,
                    index=False,
                )

        print(
            f"Created: {watchlist_path.name}"
        )

    except Exception as exc:

        print(
            f"Watchlist Excel export failed: {exc}"
        )

    if (
        setup_summary is not None
        and not setup_summary.empty
    ):

        try:

            setup_summary.to_excel(
                EXPORT_DIR /
                "setup_summary.xlsx",
                index=False,
            )

        except Exception as exc:

            print(
                f"Setup export failed: {exc}"
            )


# =========================================================
# VALIDATE OUTPUTS
# =========================================================

def validate_outputs() -> None:

    print(
        "\n"
        "====================================================\n"
        "STEP 14 — VALIDATE OUTPUTS\n"
        "===================================================="
    )

    required_files = [

        TECHNICAL_OUTPUT,
        STOCK_OUTPUT,
        MARKET_OUTPUT,
        BREADTH_OUTPUT,
        SECTOR_OUTPUT,
        DASHBOARD_OUTPUT,

    ]

    for path in required_files:

        if not path.exists():

            raise RuntimeError(
                f"Missing output: {path}"
            )

        if path.stat().st_size <= 0:

            raise RuntimeError(
                f"Empty output: {path}"
            )

    with open(
        DASHBOARD_OUTPUT,
        "r",
        encoding="utf-8",
    ) as file:

        dashboard = json.load(file)

    required_keys = [

        "dashboard",
        "generated_at",
        "market_regime",
        "market_breadth",
        "sector_analysis",
        "stocks",
        "watchlists",
        "watchlist_counts",

    ]

    missing = [
        key
        for key in required_keys
        if key not in dashboard
    ]

    if missing:

        raise RuntimeError(
            "Dashboard JSON missing keys: "
            + ", ".join(missing)
        )

    if not isinstance(
        dashboard["stocks"],
        list,
    ):

        raise RuntimeError(
            "dashboard.stocks is not a list."
        )

    if not isinstance(
        dashboard["watchlists"],
        dict,
    ):

        raise RuntimeError(
            "dashboard.watchlists is not a dictionary."
        )

    print(
        "Output validation: PASSED"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    start = datetime.now()

    print(
        "\n"
        "####################################################\n"
        "#                                                  #\n"
        "#       NSE SMART MARKET DASHBOARD V3             #\n"
        "#                                                  #\n"
        "#       Market • Technical • Fundamental           #\n"
        "#       Ranking • Watchlists • Portfolio            #\n"
        "#                                                  #\n"
        "####################################################"
    )

    print(
        f"\nStarted: "
        f"{start.astimezone().isoformat()}"
    )

    # -----------------------------------------------------
    # 1. Universe
    # -----------------------------------------------------

    universe = build_universe()

    # -----------------------------------------------------
    # 2. Technicals
    # -----------------------------------------------------

    technical = build_technical_scan(
        universe
    )

    # -----------------------------------------------------
    # 3. Fundamentals
    # -----------------------------------------------------

    fundamentals = build_fundamentals(
        technical
    )

    # -----------------------------------------------------
    # 4. Market breadth
    # -----------------------------------------------------

    (
        breadth_summary,
        breadth_stocks,
    ) = build_breadth()

    # -----------------------------------------------------
    # 5. Market regime
    # -----------------------------------------------------

    market = build_market_regime(
        breadth_summary
    )

    # -----------------------------------------------------
    # 6. Sector analysis
    # -----------------------------------------------------

    sectors = build_sector_analysis()

    # -----------------------------------------------------
    # 7. Sector mapping
    # -----------------------------------------------------

    sector_mapping = build_sector_mapping()

    # -----------------------------------------------------
    # 8. Merge
    # -----------------------------------------------------

    stocks = merge_stock_data(
        technical,
        fundamentals,
        sector_mapping,
    )

    # -----------------------------------------------------
    # 9. Ranking
    # -----------------------------------------------------

    ranked = build_ranked_stocks(
        stocks,
        market,
        sectors,
    )

    # -----------------------------------------------------
    # 10. Watchlists
    # -----------------------------------------------------

    watchlists = build_watchlists(
        ranked,
        market,
    )

    # -----------------------------------------------------
    # 11. Setup summary
    # -----------------------------------------------------

    setup_summary = build_setup_summary(
        ranked
    )

    # -----------------------------------------------------
    # 12. Dashboard JSON
    # -----------------------------------------------------

    build_dashboard_json(
        ranked,
        market,
        breadth_summary,
        sectors,
        watchlists,
        setup_summary,
    )

    # -----------------------------------------------------
    # 13. Excel exports
    # -----------------------------------------------------

    build_exports(
        ranked,
        watchlists,
        setup_summary,
    )

    # -----------------------------------------------------
    # 14. Validation
    # -----------------------------------------------------

    validate_outputs()

    end = datetime.now()

    duration = (
        end - start
    ).total_seconds()

    print(
        "\n"
        "===================================================="
    )

    print(
        "NSE SMART MARKET DASHBOARD — COMPLETED"
    )

    print(
        "===================================================="
    )

    print(
        f"Stocks: {len(ranked):,}"
    )

    print(
        f"Watchlists: {len(watchlists):,}"
    )

    print(
        f"Duration: {duration / 60:.2f} minutes"
    )

    print(
        f"Dashboard: {DASHBOARD_OUTPUT}"
    )

    print(
        "====================================================\n"
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

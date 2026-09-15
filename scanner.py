"""
===========================================================
NSE SMART MARKET DASHBOARD
MAIN SCANNER / PIPELINE
===========================================================

Pipeline
--------
1. NSE universe
2. Technical analysis
3. Fundamental analysis
4. Market breadth
5. Market regime
6. Sector analysis
7. Sector mapping
8. Stock ranking
9. Watchlists
10. Setup summary
11. CSV exports
12. Excel export
13. Dashboard JSON

This file is intentionally defensive because the individual
engines may return slightly different dataframe/dict shapes.
===========================================================
"""

from __future__ import annotations

import inspect
import json
import os
import shutil
import time
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
    create_setup_summary,
    prepare_export_data,
    watchlists_to_records,
    get_setup_counts,
    get_watchlist_counts,
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
EXPORT_DIR = OUTPUT_DIR / "exports"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

EXPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# CONSTANTS
# =========================================================

DASHBOARD_VERSION = "3.0"

MAX_DASHBOARD_STOCKS = None

TOP_WATCHLIST_ROWS = 100

EXCEL_FILENAME = (
    "nse_smart_market_dashboard.xlsx"
)


# =========================================================
# GENERAL HELPERS
# =========================================================

def safe_float(
    value: Any,
    default: float | None = None,
) -> float | None:

    if value is None:
        return default

    try:

        if pd.isna(value):
            return default

    except (
        TypeError,
        ValueError,
    ):
        pass

    try:

        result = float(value)

        if not np.isfinite(result):
            return default

        return result

    except (
        TypeError,
        ValueError,
    ):
        return default


def json_safe(
    value: Any,
) -> Any:

    if value is None:
        return None

    if isinstance(
        value,
        (
            np.integer,
        ),
    ):
        return int(value)

    if isinstance(
        value,
        (
            np.floating,
        ),
    ):

        if not np.isfinite(
            float(value)
        ):
            return None

        return float(value)

    if isinstance(
        value,
        (
            np.bool_,
        ),
    ):
        return bool(value)

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        dict,
    ):

        return {
            str(key):
                json_safe(item)
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):

        return [
            json_safe(item)
            for item in value
        ]

    try:

        if pd.isna(value):
            return None

    except (
        TypeError,
        ValueError,
    ):
        pass

    return value


def dataframe_records(
    dataframe: Any,
) -> list[dict]:

    if dataframe is None:
        return []

    if not isinstance(
        dataframe,
        pd.DataFrame,
    ):
        try:
            dataframe = pd.DataFrame(
                dataframe
            )
        except Exception:
            return []

    if dataframe.empty:
        return []

    clean = dataframe.copy()

    clean = clean.replace(
        {
            np.nan: None,
            np.inf: None,
            -np.inf: None,
        }
    )

    records = clean.to_dict(
        orient="records"
    )

    return [
        json_safe(record)
        for record in records
    ]


def ensure_dataframe(
    data: Any,
) -> pd.DataFrame:

    if data is None:
        return pd.DataFrame()

    if isinstance(
        data,
        pd.DataFrame,
    ):
        return data.copy()

    if isinstance(
        data,
        list,
    ):
        return pd.DataFrame(data)

    if isinstance(
        data,
        dict,
    ):
        return pd.DataFrame(data)

    return pd.DataFrame()


def normalise_symbol(
    value: Any,
) -> str:

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except (
        TypeError,
        ValueError,
    ):
        pass

    return (
        str(value)
        .strip()
        .upper()
        .replace(
            ".NS",
            "",
        )
    )


def find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    if dataframe is None or dataframe.empty:
        return None

    lookup = {
        str(column)
        .strip()
        .lower():
            column
        for column
        in dataframe.columns
    }

    for candidate in candidates:

        key = (
            str(candidate)
            .strip()
            .lower()
        )

        if key in lookup:
            return lookup[key]

    return None


def normalise_symbols(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = dataframe.copy()

    symbol_column = find_column(
        result,
        [
            "Symbol",
            "symbol",
            "SYMBOL",
            "Ticker",
        ],
    )

    if symbol_column is None:
        return result

    if symbol_column != "Symbol":

        result = result.rename(
            columns={
                symbol_column:
                    "Symbol"
            }
        )

    result["Symbol"] = (
        result["Symbol"]
        .apply(
            normalise_symbol
        )
    )

    result = result[
        result["Symbol"] != ""
    ]

    return result


# =========================================================
# FLEXIBLE ENGINE CALLER
# =========================================================

def call_engine(
    function: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:

    """
    Calls an engine defensively.

    Different versions of the engines may expose slightly
    different function signatures. This helper first tries
    the intended call and then adapts keyword arguments to
    the parameters actually accepted by the function.
    """

    try:

        return function(
            *args,
            **kwargs,
        )

    except TypeError as first_error:

        try:

            signature = inspect.signature(
                function
            )

            accepted = set(
                signature.parameters.keys()
            )

            filtered_kwargs = {
                key: value
                for key, value
                in kwargs.items()
                if key in accepted
            }

            return function(
                *args,
                **filtered_kwargs,
            )

        except Exception:

            raise first_error


# =========================================================
# NORMALISE ENGINE OUTPUT
# =========================================================

def normalise_engine_dataframe(
    data: Any,
    preferred_key: str | None = None,
) -> pd.DataFrame:

    if isinstance(
        data,
        pd.DataFrame,
    ):
        return data.copy()

    if isinstance(
        data,
        dict,
    ):

        if preferred_key:
            value = data.get(
                preferred_key
            )

            if isinstance(
                value,
                pd.DataFrame,
            ):
                return value.copy()

            if isinstance(
                value,
                list,
            ):
                return pd.DataFrame(value)

            if isinstance(
                value,
                dict,
            ):
                return pd.DataFrame(value)

        # Look for the first dataframe-like value.
        for value in data.values():

            if isinstance(
                value,
                pd.DataFrame,
            ):
                return value.copy()

            if isinstance(
                value,
                list,
            ) and value:

                if isinstance(
                    value[0],
                    dict,
                ):
                    return pd.DataFrame(
                        value
                    )

    if isinstance(
        data,
        list,
    ):

        if not data:
            return pd.DataFrame()

        if isinstance(
            data[0],
            dict,
        ):
            return pd.DataFrame(data)

    return pd.DataFrame()


# =========================================================
# NSE UNIVERSE
# =========================================================

def run_nse_universe() -> pd.DataFrame:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 1 — NSE UNIVERSE"
    )

    print(
        "=" * 60
    )

    universe = call_engine(
        get_nse_universe
    )

    universe = normalise_engine_dataframe(
        universe
    )

    universe = normalise_symbols(
        universe
    )

    if universe.empty:

        raise RuntimeError(
            "NSE universe returned no stocks."
        )

    universe_path = (
        DATA_DIR /
        "nse_universe.csv"
    )

    universe.to_csv(
        universe_path,
        index=False,
    )

    print(
        f"NSE universe: "
        f"{len(universe):,} stocks"
    )

    return universe


# =========================================================
# TECHNICAL ANALYSIS
# =========================================================

def run_technical_analysis(
    universe: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 2 — TECHNICAL ANALYSIS"
    )

    print(
        "=" * 60
    )

    try:

        technical = call_engine(
            calculate_technical_indicators,
            universe,
        )

    except TypeError:

        technical = call_engine(
            calculate_technical_indicators,
            universe[
                "Symbol"
            ].tolist()
        )

    technical = normalise_engine_dataframe(
        technical
    )

    technical = normalise_symbols(
        technical
    )

    if technical.empty:

        raise RuntimeError(
            "Technical engine returned no data."
        )

    technical_path = (
        OUTPUT_DIR /
        "technical_scan.csv"
    )

    technical.to_csv(
        technical_path,
        index=False,
    )

    print(
        f"Technical rows: "
        f"{len(technical):,}"
    )

    return technical


# =========================================================
# FUNDAMENTALS
# =========================================================

def run_fundamentals(
    universe: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 3 — FUNDAMENTAL ANALYSIS"
    )

    print(
        "=" * 60
    )

    # Import lazily so scanner remains compatible with
    # environments where the fundamental module is changed.
    from engines import fundamental_engine

    function = getattr(
        fundamental_engine,
        "get_fundamental_data",
        None,
    )

    if function is None:

        function = getattr(
            fundamental_engine,
            "calculate_fundamentals",
            None,
        )

    if function is None:

        function = getattr(
            fundamental_engine,
            "get_fundamentals",
            None,
        )

    if function is None:

        print(
            "Fundamental function not found. "
            "Using empty fundamentals."
        )

        return pd.DataFrame(
            columns=[
                "Symbol"
            ]
        )

    symbols = universe[
        "Symbol"
    ].tolist()

    try:

        fundamentals = call_engine(
            function,
            symbols,
        )

    except TypeError:

        fundamentals = call_engine(
            function,
            universe,
        )

    fundamentals = normalise_engine_dataframe(
        fundamentals
    )

    fundamentals = normalise_symbols(
        fundamentals
    )

    if fundamentals.empty:

        print(
            "Fundamental engine returned "
            "no rows."
        )

        fundamentals = pd.DataFrame(
            columns=[
                "Symbol"
            ]
        )

    fundamentals_path = (
        OUTPUT_DIR /
        "fundamentals.csv"
    )

    fundamentals.to_csv(
        fundamentals_path,
        index=False,
    )

    print(
        f"Fundamental rows: "
        f"{len(fundamentals):,}"
    )

    return fundamentals


# =========================================================
# MARKET BREADTH
# =========================================================

def run_market_breadth() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 4 — MARKET BREADTH"
    )

    print(
        "=" * 60
    )

    breadth_result = call_engine(
        get_market_breadth
    )

    breadth = pd.DataFrame()
    breadth_stocks = pd.DataFrame()

    if isinstance(
        breadth_result,
        tuple,
    ):

        if len(
            breadth_result
        ) >= 1:

            first = breadth_result[0]

            if isinstance(
                first,
                pd.DataFrame,
            ):
                breadth = first.copy()

            elif isinstance(
                first,
                dict,
            ):
                breadth = pd.DataFrame(
                    [first]
                )

        if len(
            breadth_result
        ) >= 2:

            second = breadth_result[1]

            if isinstance(
                second,
                pd.DataFrame,
            ):
                breadth_stocks = (
                    second.copy()
                )

    elif isinstance(
        breadth_result,
        dict,
    ):

        breadth = (
            normalise_engine_dataframe(
                breadth_result,
                "breadth",
            )
        )

        breadth_stocks = (
            normalise_engine_dataframe(
                breadth_result,
                "stocks",
            )
        )

    elif isinstance(
        breadth_result,
        pd.DataFrame,
    ):

        # A stock-level dataframe is more likely when it
        # contains Symbol.
        if find_column(
            breadth_result,
            [
                "Symbol",
                "symbol",
            ],
        ):

            breadth_stocks = (
                breadth_result.copy()
            )

        else:

            breadth = (
                breadth_result.copy()
            )

    breadth = ensure_dataframe(
        breadth
    )

    breadth_stocks = ensure_dataframe(
        breadth_stocks
    )

    breadth_path = (
        OUTPUT_DIR /
        "market_breadth.csv"
    )

    breadth_stocks_path = (
        OUTPUT_DIR /
        "market_breadth_stocks.csv"
    )

    breadth.to_csv(
        breadth_path,
        index=False,
    )

    breadth_stocks.to_csv(
        breadth_stocks_path,
        index=False,
    )

    print(
        f"Breadth summary rows: "
        f"{len(breadth):,}"
    )

    print(
        f"Breadth stock rows: "
        f"{len(breadth_stocks):,}"
    )

    return (
        breadth,
        breadth_stocks,
    )


# =========================================================
# MARKET REGIME
# =========================================================

def run_market_regime() -> Any:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 5 — MARKET REGIME"
    )

    print(
        "=" * 60
    )

    result = call_engine(
        get_market_regime
    )

    if isinstance(
        result,
        pd.DataFrame,
    ):

        market = result.copy()

    elif isinstance(
        result,
        dict,
    ):

        market = result.copy()

    else:

        market = {}

    market_path = (
        OUTPUT_DIR /
        "market_regime.csv"
    )

    if isinstance(
        market,
        pd.DataFrame,
    ):

        market.to_csv(
            market_path,
            index=False,
        )

    elif isinstance(
        market,
        dict,
    ):

        pd.DataFrame(
            [market]
        ).to_csv(
            market_path,
            index=False,
        )

    print(
        "Market regime generated."
    )

    return market


# =========================================================
# SECTOR ANALYSIS
# =========================================================

def run_sector_analysis() -> pd.DataFrame:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 6 — SECTOR ANALYSIS"
    )

    print(
        "=" * 60
    )

    result = call_engine(
        get_sector_analysis
    )

    sectors = normalise_engine_dataframe(
        result
    )

    if sectors.empty:

        print(
            "Sector engine returned no data."
        )

        sectors = pd.DataFrame()

    sector_path = (
        OUTPUT_DIR /
        "sector_analysis.csv"
    )

    sectors.to_csv(
        sector_path,
        index=False,
    )

    print(
        f"Sector rows: "
        f"{len(sectors):,}"
    )

    return sectors


# =========================================================
# SECTOR MAPPING
# =========================================================

def run_sector_mapping() -> pd.DataFrame:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 7 — SECTOR MAPPING"
    )

    print(
        "=" * 60
    )

    mapping = call_engine(
        load_sector_mapping
    )

    mapping = normalise_engine_dataframe(
        mapping
    )

    mapping = normalise_symbols(
        mapping
    )

    if mapping.empty:

        print(
            "Sector mapping unavailable."
        )

        return mapping

    mapping_path = (
        DATA_DIR /
        "sector_mapping.csv"
    )

    mapping.to_csv(
        mapping_path,
        index=False,
    )

    print(
        f"Sector mappings: "
        f"{len(mapping):,}"
    )

    return mapping


# =========================================================
# MERGE SECTOR MAPPING
# =========================================================

def merge_sector_mapping(
    technical: pd.DataFrame,
    mapping: pd.DataFrame,
) -> pd.DataFrame:

    result = technical.copy()

    if mapping is None or mapping.empty:
        return result

    result = normalise_symbols(
        result
    )

    mapping = normalise_symbols(
        mapping
    )

    if (
        "Symbol" not in result.columns
        or "Symbol" not in mapping.columns
    ):
        return result

    useful_columns = [
        column
        for column
        in [
            "Symbol",
            "primary_sector",
            "primary_sector_index",
            "primary_sector_type",
            "sector_indices",
        ]
        if column in mapping.columns
    ]

    if len(
        useful_columns
    ) <= 1:

        return result

    mapping_small = mapping[
        useful_columns
    ].copy()

    # Avoid duplicate columns.
    for column in useful_columns:

        if (
            column != "Symbol"
            and column in result.columns
        ):

            result = result.drop(
                columns=[
                    column
                ]
            )

    result = result.merge(
        mapping_small,
        on="Symbol",
        how="left",
    )

    if (
        "Primary_Sector"
        not in result.columns
    ):

        if (
            "primary_sector"
            in result.columns
        ):

            result[
                "Primary_Sector"
            ] = result[
                "primary_sector"
            ]

        else:

            result[
                "Primary_Sector"
            ] = "Unknown"

    return result


# =========================================================
# MERGE FUNDAMENTALS
# =========================================================

def merge_fundamentals(
    technical: pd.DataFrame,
    fundamentals: pd.DataFrame,
) -> pd.DataFrame:

    result = technical.copy()

    if fundamentals is None or fundamentals.empty:
        return result

    result = normalise_symbols(
        result
    )

    fundamentals = normalise_symbols(
        fundamentals
    )

    if (
        "Symbol" not in result.columns
        or "Symbol" not in fundamentals.columns
    ):
        return result

    duplicate_columns = [
        column
        for column
        in fundamentals.columns
        if (
            column in result.columns
            and column != "Symbol"
        )
    ]

    if duplicate_columns:

        fundamentals = (
            fundamentals.drop(
                columns=duplicate_columns
            )
        )

    result = result.merge(
        fundamentals,
        on="Symbol",
        how="left",
    )

    return result


# =========================================================
# RANKING
# =========================================================

def run_ranking(
    technical: pd.DataFrame,
    fundamentals: pd.DataFrame,
    sectors: pd.DataFrame,
    market: Any,
) -> pd.DataFrame:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 8 — STOCK RANKING"
    )

    print(
        "=" * 60
    )

    try:

        ranked = call_engine(
            rank_stocks,
            technical,
            fundamentals,
            sectors,
            market,
        )

    except TypeError:

        ranked = call_engine(
            rank_stocks,
            technical_data=technical,
            fundamental_data=fundamentals,
            sector_data=sectors,
            market_regime=market,
        )

    ranked = normalise_engine_dataframe(
        ranked
    )

    ranked = normalise_symbols(
        ranked
    )

    if ranked.empty:

        raise RuntimeError(
            "Ranking engine returned no stocks."
        )

    stocks_path = (
        OUTPUT_DIR /
        "stocks.csv"
    )

    ranked.to_csv(
        stocks_path,
        index=False,
    )

    print(
        f"Ranked stocks: "
        f"{len(ranked):,}"
    )

    return ranked


# =========================================================
# WATCHLISTS
# =========================================================

def run_watchlists(
    ranked: pd.DataFrame,
    market: Any,
) -> dict[str, pd.DataFrame]:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 9 — WATCHLISTS"
    )

    print(
        "=" * 60
    )

    try:

        watchlists = call_engine(
            create_watchlists,
            ranked,
            market,
        )

    except TypeError:

        watchlists = call_engine(
            create_watchlists,
            ranked_data=ranked,
            market_regime=market,
        )

    if not isinstance(
        watchlists,
        dict,
    ):

        watchlists = {}

    expected_lists = [
        "next_day",
        "intraday",
        "swing",
        "long_term",
        "52w_high",
        "dma_recovery",
        "momentum",
        "breakout",
        "options",
    ]

    normalised = {}

    for name in expected_lists:

        dataframe = (
            watchlists.get(
                name,
                pd.DataFrame(),
            )
        )

        dataframe = ensure_dataframe(
            dataframe
        )

        dataframe = normalise_symbols(
            dataframe
        )

        normalised[name] = dataframe

        output_path = (
            OUTPUT_DIR /
            f"watchlist_{name}.csv"
        )

        dataframe.to_csv(
            output_path,
            index=False,
        )

        print(
            f"{name:16s}: "
            f"{len(dataframe):,}"
        )

    return normalised


# =========================================================
# SETUP SUMMARY
# =========================================================

def run_setup_summary(
    ranked: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 10 — SETUP SUMMARY"
    )

    print(
        "=" * 60
    )

    try:

        summary = call_engine(
            create_setup_summary,
            ranked,
        )

    except TypeError:

        summary = call_engine(
            create_setup_summary,
            ranked_data=ranked,
        )

    summary = ensure_dataframe(
        summary
    )

    summary_path = (
        OUTPUT_DIR /
        "setup_summary.csv"
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    print(
        f"Setup summary rows: "
        f"{len(summary):,}"
    )

    return summary


# =========================================================
# EXPORT CSV FILES
# =========================================================

def write_export_csvs(
    ranked: pd.DataFrame,
    watchlists: dict[str, pd.DataFrame],
    setup_summary: pd.DataFrame,
) -> dict[str, str]:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 11 — EXPORT FILES"
    )

    print(
        "=" * 60
    )

    exports = {}

    # Main stocks.
    stocks_export = (
        EXPORT_DIR /
        "stocks.csv"
    )

    ranked.to_csv(
        stocks_export,
        index=False,
    )

    exports["stocks"] = str(
        stocks_export.relative_to(
            BASE_DIR
        )
    ).replace(
        os.sep,
        "/",
    )

    # Setup summary.
    summary_export = (
        EXPORT_DIR /
        "setup_summary.csv"
    )

    setup_summary.to_csv(
        summary_export,
        index=False,
    )

    exports[
        "setup_summary"
    ] = str(
        summary_export.relative_to(
            BASE_DIR
        )
    ).replace(
        os.sep,
        "/",
    )

    # Watchlists.
    for name, dataframe in (
        watchlists.items()
    ):

        path = (
            EXPORT_DIR /
            f"{name}.csv"
        )

        dataframe.to_csv(
            path,
            index=False,
        )

        exports[name] = str(
            path.relative_to(
                BASE_DIR
            )
        ).replace(
            os.sep,
            "/",
        )

    print(
        f"CSV exports: "
        f"{len(exports):,}"
    )

    return exports


# =========================================================
# EXCEL EXPORT
# =========================================================

def write_excel_export(
    ranked: pd.DataFrame,
    watchlists: dict[str, pd.DataFrame],
    setup_summary: pd.DataFrame,
) -> str | None:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STEP 12 — EXCEL EXPORT"
    )

    print(
        "=" * 60
    )

    path = (
        EXPORT_DIR /
        EXCEL_FILENAME
    )

    try:

        with pd.ExcelWriter(
            path,
            engine="openpyxl",
        ) as writer:

            ranked.to_excel(
                writer,
                sheet_name="Stocks",
                index=False,
            )

            setup_summary.to_excel(
                writer,
                sheet_name="Setup Summary",
                index=False,
            )

            for name, dataframe in (
                watchlists.items()
            ):

                if dataframe is None:
                    continue

                sheet_name = (
                    str(name)
                    .replace(
                        "_",
                        " ",
                    )
                    .title()
                )

                # Excel sheet names are limited to 31 chars.
                sheet_name = sheet_name[
                    :31
                ]

                dataframe.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                )

        print(
            f"Excel export created: "
            f"{path}"
        )

        return str(
            path.relative_to(
                BASE_DIR
            )
        ).replace(
            os.sep,
            "/",
        )

    except Exception as error:

        print(
            "Excel export failed: "
            f"{error}"
        )

        return None


# =========================================================
# MARKET DATA NORMALISATION
# =========================================================

def market_to_dict(
    market: Any,
) -> dict:

    if market is None:
        return {}

    if isinstance(
        market,
        pd.DataFrame,
    ):

        if market.empty:
            return {}

        return json_safe(
            market.iloc[-1].to_dict()
        )

    if isinstance(
        market,
        dict,
    ):

        return json_safe(
            market
        )

    return {}


def breadth_to_dict(
    breadth: pd.DataFrame,
) -> dict:

    if breadth is None or breadth.empty:
        return {}

    return json_safe(
        breadth.iloc[-1].to_dict()
    )


# =========================================================
# MARKET DISPLAY FIELDS
# =========================================================

def get_market_field(
    market: dict,
    *keys: str,
    default: Any = None,
) -> Any:

    for key in keys:

        value = market.get(
            key
        )

        if value is not None:

            try:

                if pd.isna(value):
                    continue

            except (
                TypeError,
                ValueError,
            ):
                pass

            return value

    return default


def build_market_payload(
    market: Any,
) -> dict:

    raw = market_to_dict(
        market
    )

    # Nested structures are retained.
    nifty = raw.get(
        "nifty",
        {},
    )

    bank_nifty = raw.get(
        "bank_nifty",
        {},
    )

    vix_data = raw.get(
        "vix_data",
        {},
    )

    if not isinstance(
        nifty,
        dict,
    ):
        nifty = {}

    if not isinstance(
        bank_nifty,
        dict,
    ):
        bank_nifty = {}

    if not isinstance(
        vix_data,
        dict,
    ):
        vix_data = {}

    market_regime = get_market_field(
        raw,
        "market_regime",
        "Regime",
        default="Unavailable",
    )

    market_score = safe_float(
        get_market_field(
            raw,
            "market_score",
            "Market_Score",
            "score",
        )
    )

    nifty_price = safe_float(
        get_market_field(
            raw,
            "nifty_price",
            "NIFTY_Price",
        )
    )

    if nifty_price is None:

        nifty_price = safe_float(
            get_market_field(
                nifty,
                "price",
                "Close",
                "close",
            )
        )

    bank_price = safe_float(
        get_market_field(
            raw,
            "bank_nifty_price",
            "BANK_NIFTY_Price",
        )
    )

    if bank_price is None:

        bank_price = safe_float(
            get_market_field(
                bank_nifty,
                "price",
                "Close",
                "close",
            )
        )

    vix = safe_float(
        get_market_field(
            raw,
            "vix",
            "VIX",
            "india_vix",
        )
    )

    if vix is None:

        vix = safe_float(
            get_market_field(
                vix_data,
                "price",
                "Close",
                "close",
                "vix",
            )
        )

    payload = {
        "market_regime":
            market_regime,

        "market_score":
            market_score,

        "nifty_price":
            nifty_price,

        "nifty_previous_close":
            safe_float(
                get_market_field(
                    raw,
                    "nifty_previous_close",
                    "NIFTY_Previous_Close",
                )
            ),

        "nifty_daily_return_pct":
            safe_float(
                get_market_field(
                    raw,
                    "nifty_daily_return_pct",
                    "NIFTY_Daily_Return_Pct",
                )
            ),

        "nifty_score":
            safe_float(
                get_market_field(
                    raw,
                    "nifty_score",
                )
            ),

        "nifty_trend":
            get_market_field(
                raw,
                "nifty_trend",
            ),

        "nifty_momentum":
            get_market_field(
                raw,
                "nifty_momentum",
            ),

        "nifty_rsi":
            safe_float(
                get_market_field(
                    raw,
                    "nifty_rsi",
                )
            ),

        "nifty_support":
            safe_float(
                get_market_field(
                    raw,
                    "nifty_support",
                    "market_support",
                    "support",
                )
            ),

        "nifty_resistance":
            safe_float(
                get_market_field(
                    raw,
                    "nifty_resistance",
                    "market_resistance",
                    "resistance",
                )
            ),

        "nifty_pivot":
            safe_float(
                get_market_field(
                    raw,
                    "nifty_pivot",
                    "market_pivot",
                    "pivot",
                )
            ),

        "bank_nifty_price":
            bank_price,

        "bank_nifty_previous_close":
            safe_float(
                get_market_field(
                    raw,
                    "bank_nifty_previous_close",
                    "BANK_NIFTY_Previous_Close",
                )
            ),

        "bank_nifty_daily_return_pct":
            safe_float(
                get_market_field(
                    raw,
                    "bank_nifty_daily_return_pct",
                    "BANK_NIFTY_Daily_Return_Pct",
                )
            ),

        "bank_nifty_score":
            safe_float(
                get_market_field(
                    raw,
                    "bank_nifty_score",
                )
            ),

        "bank_nifty_trend":
            get_market_field(
                raw,
                "bank_nifty_trend",
            ),

        "bank_nifty_momentum":
            get_market_field(
                raw,
                "bank_nifty_momentum",
            ),

        "bank_nifty_rsi":
            safe_float(
                get_market_field(
                    raw,
                    "bank_nifty_rsi",
                )
            ),

        "bank_nifty_support":
            safe_float(
                get_market_field(
                    raw,
                    "bank_nifty_support",
                )
            ),

        "bank_nifty_resistance":
            safe_float(
                get_market_field(
                    raw,
                    "bank_nifty_resistance",
                )
            ),

        "bank_nifty_pivot":
            safe_float(
                get_market_field(
                    raw,
                    "bank_nifty_pivot",
                )
            ),

        "vix":
            vix,

        "vix_interpretation":
            get_market_field(
                raw,
                "vix_interpretation",
                default="Unavailable",
            ),

        "equity_environment":
            get_market_field(
                raw,
                "equity_environment",
                default="Unavailable",
            ),

        "swing_environment":
            get_market_field(
                raw,
                "swing_environment",
                default="Unavailable",
            ),

        "breakout_environment":
            get_market_field(
                raw,
                "breakout_environment",
                default="Unavailable",
            ),

        "intraday_environment":
            get_market_field(
                raw,
                "intraday_environment",
                default="Unavailable",
            ),

        "options_environment":
            get_market_field(
                raw,
                "options_environment",
                default="Unavailable",
            ),

        "support":
            safe_float(
                get_market_field(
                    raw,
                    "support",
                    "market_support",
                    "nifty_support",
                )
            ),

        "resistance":
            safe_float(
                get_market_field(
                    raw,
                    "resistance",
                    "market_resistance",
                    "nifty_resistance",
                )
            ),

        "pivot":
            safe_float(
                get_market_field(
                    raw,
                    "pivot",
                    "market_pivot",
                    "nifty_pivot",
                )
            ),

        "market_support":
            safe_float(
                get_market_field(
                    raw,
                    "market_support",
                    "support",
                    "nifty_support",
                )
            ),

        "market_resistance":
            safe_float(
                get_market_field(
                    raw,
                    "market_resistance",
                    "resistance",
                    "nifty_resistance",
                )
            ),

        "market_pivot":
            safe_float(
                get_market_field(
                    raw,
                    "market_pivot",
                    "pivot",
                    "nifty_pivot",
                )
            ),

        "bullish_trigger":
            get_market_field(
                raw,
                "bullish_trigger",
            ),

        "bearish_trigger":
            get_market_field(
                raw,
                "bearish_trigger",
            ),

        "market_scenario":
            get_market_field(
                raw,
                "market_scenario",
                "scenario",
            ),

        "scenario":
            get_market_field(
                raw,
                "scenario",
                "market_scenario",
            ),

        "market_data_authority":
            get_market_field(
                raw,
                "market_data_authority",
                "data_authority",
                default="Historical market data",
            ),

        "data_authority":
            get_market_field(
                raw,
                "data_authority",
                "market_data_authority",
            ),

        "generated_at":
            get_market_field(
                raw,
                "generated_at",
            ),

        "nifty":
            nifty,

        "bank_nifty":
            bank_nifty,

        "vix_data":
            vix_data,

        "environments":
            raw.get(
                "environments",
                {},
            ),

        "market_analysis":
            raw.get(
                "market_analysis",
                {},
            ),
    }

    return json_safe(
        payload
    )


# =========================================================
# DASHBOARD STOCK FIELDS
# =========================================================

def add_dashboard_stock_fields(
    ranked: pd.DataFrame,
) -> pd.DataFrame:

    result = ranked.copy()

    # Price used by frontend.
    price_column = find_column(
        result,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    if (
        price_column is not None
        and "Price" not in result.columns
    ):

        result["Price"] = (
            pd.to_numeric(
                result[
                    price_column
                ],
                errors="coerce",
            )
        )

    # Display-friendly entry field.
    if (
        "Entry_Price"
        not in result.columns
        and "entry_price"
        in result.columns
    ):

        result["Entry_Price"] = (
            result[
                "entry_price"
            ]
        )

    if (
        "Stop_Loss"
        not in result.columns
        and "stop_loss"
        in result.columns
    ):

        result["Stop_Loss"] = (
            result[
                "stop_loss"
            ]
        )

    if (
        "Target_1"
        not in result.columns
        and "target_1"
        in result.columns
    ):

        result["Target_1"] = (
            result[
                "target_1"
            ]
        )

    if (
        "Target_2"
        not in result.columns
        and "target_2"
        in result.columns
    ):

        result["Target_2"] = (
            result[
                "target_2"
            ]
        )

    if (
        "Risk_Reward"
        not in result.columns
        and "risk_reward"
        in result.columns
    ):

        result["Risk_Reward"] = (
            result[
                "risk_reward"
            ]
        )

    if (
        "Primary_Sector"
        not in result.columns
    ):

        sector_column = find_column(
            result,
            [
                "primary_sector",
                "Sector",
                "sector",
            ],
        )

        if sector_column is not None:

            result[
                "Primary_Sector"
            ] = result[
                sector_column
            ]

        else:

            result[
                "Primary_Sector"
            ] = "Unknown"

    return result


# =========================================================
# DASHBOARD JSON
# =========================================================

def build_dashboard_json(
    ranked: pd.DataFrame,
    watchlists: dict[str, pd.DataFrame],
    setup_summary: pd.DataFrame,
    breadth: pd.DataFrame,
    breadth_stocks: pd.DataFrame,
    sectors: pd.DataFrame,
    market: Any,
    export_paths: dict[str, str],
    excel_path: str | None,
    runtime_seconds: float,
) -> dict:

    ranked = add_dashboard_stock_fields(
        ranked
    )

    market_payload = (
        build_market_payload(
            market
        )
    )

    breadth_payload = (
        breadth_to_dict(
            breadth
        )
    )

    setup_counts = (
        get_setup_counts(
            ranked
        )
    )

    watchlist_counts = (
        get_watchlist_counts(
            watchlists
        )
    )

    stock_records = dataframe_records(
        ranked
    )

    if (
        MAX_DASHBOARD_STOCKS
        is not None
    ):

        stock_records = (
            stock_records[
                :MAX_DASHBOARD_STOCKS
            ]
        )

    watchlist_records = (
        watchlists_to_records(
            watchlists
        )
    )

    setup_records = dataframe_records(
        setup_summary
    )

    sector_records = dataframe_records(
        sectors
    )

    breadth_stock_records = (
        dataframe_records(
            breadth_stocks
        )
    )

    generated_at = (
        datetime.now()
        .astimezone()
        .isoformat()
    )

    payload = {
        "dashboard": {
            "name":
                "NSE Smart Market Dashboard",

            "version":
                DASHBOARD_VERSION,

            "description":
                (
                    "Market intelligence dashboard "
                    "covering market regime, breadth, "
                    "technicals, fundamentals, sectors, "
                    "setups and trade plans."
                ),

            "created_by":
                "Rakesh Nagapuri",

            "generated_at":
                generated_at,
        },

        "version":
            DASHBOARD_VERSION,

        "generated_at":
            generated_at,

        "generated_at_display":
            datetime.now()
            .astimezone()
            .strftime(
                "%d %b %Y %H:%M:%S %Z"
            ),

        "market_data_authority":
            market_payload.get(
                "market_data_authority"
            ),

        "market_regime":
            market_payload,

        "market":
            market_payload,

        "market_breadth":
            breadth_payload,

        "breadth":
            breadth_payload,

        "market_breadth_stocks":
            breadth_stock_records,

        "sector_analysis":
            sector_records,

        "sectors":
            sector_records,

        "stocks":
            stock_records,

        "stock_count":
            int(len(ranked)),

        "watchlists":
            watchlist_records,

        "watchlist_counts":
            watchlist_counts,

        "setup_summary":
            setup_records,

        "setup_counts":
            setup_counts,

        "exports":
            {
                **export_paths,
                "excel":
                    excel_path,
            },

        "metadata":
            {
                "universe_count":
                    int(
                        len(ranked)
                    ),

                "stock_count":
                    int(
                        len(ranked)
                    ),

                "sector_count":
                    int(
                        len(sectors)
                    ),

                "watchlist_count":
                    int(
                        sum(
                            watchlist_counts.values()
                        )
                    ),

                "setup_count":
                    int(
                        len(setup_summary)
                    ),

                "runtime_seconds":
                    round(
                        runtime_seconds,
                        2,
                    ),
            },
    }

    return json_safe(
        payload
    )


# =========================================================
# WRITE DASHBOARD JSON
# =========================================================

def write_dashboard_json(
    payload: dict,
) -> str:

    path = (
        OUTPUT_DIR /
        "dashboard_data.json"
    )

    temporary_path = (
        OUTPUT_DIR /
        "dashboard_data.tmp.json"
    )

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            ensure_ascii=False,
            allow_nan=False,
            separators=(
                ",",
                ":",
            ),
        )

    os.replace(
        temporary_path,
        path,
    )

    print(
        f"Dashboard JSON created: "
        f"{path}"
    )

    return str(
        path
    )


# =========================================================
# VALIDATE DASHBOARD JSON
# =========================================================

def validate_dashboard_json(
    path: str | Path,
) -> dict:

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

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(
            file
        )

    missing = [
        key
        for key
        in required_keys
        if key not in data
    ]

    if missing:

        raise RuntimeError(
            "Dashboard JSON missing "
            f"keys: {missing}"
        )

    if not isinstance(
        data["stocks"],
        list,
    ):

        raise RuntimeError(
            "dashboard_data.json "
            "'stocks' must be a list."
        )

    if not isinstance(
        data["watchlists"],
        dict,
    ):

        raise RuntimeError(
            "dashboard_data.json "
            "'watchlists' must be a dict."
        )

    print(
        "Dashboard JSON validation: PASSED"
    )

    print(
        f"Dashboard stocks: "
        f"{len(data['stocks']):,}"
    )

    print(
        "Watchlists: "
        f"{len(data['watchlists']):,}"
    )

    return data


# =========================================================
# CLEAN OLD EXPORTS
# =========================================================

def clean_old_exports() -> None:

    """
    Removes only temporary export files created by
    this pipeline. Existing primary output files are
    intentionally preserved.
    """

    temporary_patterns = [
        "*.tmp",
        "*.tmp.json",
    ]

    for pattern in temporary_patterns:

        for path in OUTPUT_DIR.glob(
            pattern
        ):

            try:
                path.unlink()
            except OSError:
                pass


# =========================================================
# MAIN PIPELINE
# =========================================================

def main() -> None:

    start_time = time.time()

    print(
        "\n"
        + "#" * 70
    )

    print(
        "NSE SMART MARKET DASHBOARD"
    )

    print(
        f"Version {DASHBOARD_VERSION}"
    )

    print(
        "Full Market Intelligence Pipeline"
    )

    print(
        "#" * 70
    )

    print(
        f"Started: "
        f"{datetime.now().astimezone().isoformat()}"
    )

    clean_old_exports()

    # -----------------------------------------------------
    # 1. NSE Universe
    # -----------------------------------------------------

    universe = run_nse_universe()

    # -----------------------------------------------------
    # 2. Technicals
    # -----------------------------------------------------

    technical = run_technical_analysis(
        universe
    )

    # -----------------------------------------------------
    # 3. Fundamentals
    # -----------------------------------------------------

    fundamentals = run_fundamentals(
        universe
    )

    # -----------------------------------------------------
    # 4. Market Breadth
    # -----------------------------------------------------

    (
        breadth,
        breadth_stocks,
    ) = run_market_breadth()

    # -----------------------------------------------------
    # 5. Market Regime
    # -----------------------------------------------------

    market = run_market_regime()

    # -----------------------------------------------------
    # 6. Sector Analysis
    # -----------------------------------------------------

    sectors = run_sector_analysis()

    # -----------------------------------------------------
    # 7. Sector Mapping
    # -----------------------------------------------------

    sector_mapping = (
        run_sector_mapping()
    )

    technical = merge_sector_mapping(
        technical,
        sector_mapping,
    )

    # -----------------------------------------------------
    # 8. Ranking
    # -----------------------------------------------------

    ranked = run_ranking(
        technical,
        fundamentals,
        sectors,
        market,
    )

    # Ensure sector mapping survives into ranked data
    # even if the ranking engine did not merge it.
    if (
        "Primary_Sector"
        not in ranked.columns
    ):

        ranked = merge_sector_mapping(
            ranked,
            sector_mapping,
        )

    ranked = add_dashboard_stock_fields(
        ranked
    )

    ranked.to_csv(
        OUTPUT_DIR /
        "stocks.csv",
        index=False,
    )

    # -----------------------------------------------------
    # 9. Watchlists
    # -----------------------------------------------------

    watchlists = run_watchlists(
        ranked,
        market,
    )

    # -----------------------------------------------------
    # 10. Setup Summary
    # -----------------------------------------------------

    setup_summary = (
        run_setup_summary(
            ranked
        )
    )

    # -----------------------------------------------------
    # 11. CSV exports
    # -----------------------------------------------------

    export_paths = (
        write_export_csvs(
            ranked,
            watchlists,
            setup_summary,
        )
    )

    # -----------------------------------------------------
    # 12. Excel export
    # -----------------------------------------------------

    excel_path = (
        write_excel_export(
            ranked,
            watchlists,
            setup_summary,
        )
    )

    # -----------------------------------------------------
    # Dashboard JSON
    # -----------------------------------------------------

    runtime_seconds = (
        time.time()
        -
        start_time
    )

    dashboard_payload = (
        build_dashboard_json(
            ranked=ranked,
            watchlists=watchlists,
            setup_summary=setup_summary,
            breadth=breadth,
            breadth_stocks=breadth_stocks,
            sectors=sectors,
            market=market,
            export_paths=export_paths,
            excel_path=excel_path,
            runtime_seconds=runtime_seconds,
        )
    )

    dashboard_path = (
        write_dashboard_json(
            dashboard_payload
        )
    )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    validate_dashboard_json(
        dashboard_path
    )

    # -----------------------------------------------------
    # Final summary
    # -----------------------------------------------------

    runtime_seconds = (
        time.time()
        -
        start_time
    )

    print(
        "\n"
        + "#" * 70
    )

    print(
        "SCAN COMPLETED SUCCESSFULLY"
    )

    print(
        "#" * 70
    )

    print(
        f"Stocks analysed : "
        f"{len(ranked):,}"
    )

    print(
        f"Sectors         : "
        f"{len(sectors):,}"
    )

    print(
        f"Watchlists      : "
        f"{sum(get_watchlist_counts(watchlists).values()):,}"
    )

    print(
        f"Runtime         : "
        f"{runtime_seconds:.2f} seconds"
    )

    print(
        "\nOutput files:"
    )

    print(
        f"  {OUTPUT_DIR / 'stocks.csv'}"
    )

    print(
        f"  {OUTPUT_DIR / 'market_regime.csv'}"
    )

    print(
        f"  {OUTPUT_DIR / 'market_breadth.csv'}"
    )

    print(
        f"  {OUTPUT_DIR / 'sector_analysis.csv'}"
    )

    print(
        f"  {OUTPUT_DIR / 'setup_summary.csv'}"
    )

    print(
        f"  {OUTPUT_DIR / 'dashboard_data.json'}"
    )

    if excel_path:

        print(
            f"  {BASE_DIR / excel_path}"
        )

    print(
        "\n"
        "Dashboard pipeline finished."
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

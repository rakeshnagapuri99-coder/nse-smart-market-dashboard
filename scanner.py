"""
===========================================================
NSE SMART MARKET DASHBOARD
SCANNER V3
===========================================================

Master pipeline

1. NSE universe
2. Technical analysis
3. Fundamentals
4. Market breadth
5. Market regime
6. Sector analysis
7. Sector mapping
8. Ranking
9. Watchlists
10. Dashboard JSON
11. CSV exports
12. Excel exports

Run:
    python scanner.py
===========================================================
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from engines.nse_universe import get_nse_universe
from engines.technical_engine import (
    calculate_technical_indicators,
)
from engines.market_breadth import (
    get_market_breadth,
)
from engines.market_engine import (
    get_market_regime,
)
from engines.sector_engine import (
    get_sector_analysis,
)
from engines.sector_mapping import (
    load_sector_mapping,
)
from engines.ranking_engine import (
    rank_stocks,
    create_watchlists,
    create_setup_summary,
    prepare_export_data,
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
# CONFIGURATION
# =========================================================

TECHNICAL_FILE = (
    OUTPUT_DIR /
    "technical_scan.csv"
)

FUNDAMENTAL_FILE = (
    OUTPUT_DIR /
    "fundamentals.csv"
)

STOCKS_FILE = (
    OUTPUT_DIR /
    "stocks.csv"
)

MARKET_FILE = (
    OUTPUT_DIR /
    "market_regime.csv"
)

BREADTH_FILE = (
    OUTPUT_DIR /
    "market_breadth.csv"
)

BREADTH_STOCKS_FILE = (
    OUTPUT_DIR /
    "market_breadth_stocks.csv"
)

SECTOR_FILE = (
    OUTPUT_DIR /
    "sector_analysis.csv"
)

SECTOR_MAPPING_FILE = (
    DATA_DIR /
    "sector_mapping.csv"
)

SETUP_SUMMARY_FILE = (
    OUTPUT_DIR /
    "setup_summary.csv"
)

DASHBOARD_JSON_FILE = (
    OUTPUT_DIR /
    "dashboard_data.json"
)


# =========================================================
# HELPERS
# =========================================================

def clean_for_json(
    value: Any,
) -> Any:

    if value is None:
        return None


    if isinstance(
        value,
        dict,
    ):

        return {
            str(key):
                clean_for_json(val)
            for key, val
            in value.items()
        }


    if isinstance(
        value,
        list,
    ):

        return [
            clean_for_json(item)
            for item in value
        ]


    if isinstance(
        value,
        tuple,
    ):

        return [
            clean_for_json(item)
            for item in value
        ]


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
        np.integer,
    ):

        return int(value)


    if isinstance(
        value,
        np.floating,
    ):

        value = float(value)

        if not np.isfinite(value):
            return None

        return value


    if isinstance(
        value,
        float,
    ):

        if not np.isfinite(value):
            return None

        return value


    if isinstance(
        value,
        np.ndarray,
    ):

        return [
            clean_for_json(item)
            for item in value.tolist()
        ]


    if is_nan_like(value):

        return None


    return value


def is_nan_like(
    value: Any,
) -> bool:

    if value is None:
        return True

    try:

        result = pd.isna(
            value
        )

        if isinstance(
            result,
            (bool, np.bool_),
        ):

            return bool(result)

    except (
        TypeError,
        ValueError,
    ):

        pass

    return False


def dataframe_to_records(
    df: Any,
) -> list[dict]:

    if df is None:
        return []

    if not isinstance(
        df,
        pd.DataFrame,
    ):

        try:

            df = pd.DataFrame(df)

        except Exception:

            return []


    if df.empty:
        return []


    return clean_for_json(
        df.to_dict(
            orient="records"
        )
    )


def save_csv(
    df: pd.DataFrame,
    path: Path,
) -> None:

    if df is None:
        return

    df.to_csv(
        path,
        index=False,
    )

    print(
        f"Saved: {path}"
    )


def save_json(
    data: Any,
    path: Path,
) -> None:

    cleaned =
        clean_for_json(
            data
        )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            cleaned,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Saved: {path}"
    )


def normalise_symbol(
    value: Any,
) -> str:

    if value is None:
        return ""

    text =
        str(value).strip().upper()

    if text.endswith(
        ".NS"
    ):

        text =
            text[:-3]

    return text


def find_symbol_column(
    df: pd.DataFrame,
) -> str | None:

    candidates = [
        "Symbol",
        "symbol",
        "SYMBOL",
        "Ticker",
        "ticker",
    ]

    lookup = {
        str(column).lower():
            column
        for column in df.columns
    }

    for candidate in candidates:

        if (
            candidate.lower()
            in lookup
        ):

            return lookup[
                candidate.lower()
            ]

    return None


def normalise_symbol_column(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df is None or df.empty:
        return df


    result =
        df.copy()


    column =
        find_symbol_column(
            result
        )


    if column is None:
        return result


    if column != "Symbol":

        result =
            result.rename(
                columns={
                    column:
                        "Symbol"
                }
            )


    result["Symbol"] =
        result[
            "Symbol"
        ].apply(
            normalise_symbol
        )


    return result


# =========================================================
# TECHNICAL SCAN
# =========================================================

def run_technical_scan(
    universe: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 1 — TECHNICAL SCAN"
    )

    print(
        "===================================================="
    )


    if (
        universe is None
        or universe.empty
    ):

        raise RuntimeError(
            "NSE universe is empty."
        )


    result =
        calculate_technical_indicators(
            universe
        )


    result =
        normalise_symbol_column(
            result
        )


    if result.empty:

        raise RuntimeError(
            "Technical scan returned no stocks."
        )


    save_csv(
        result,
        TECHNICAL_FILE,
    )


    print(
        f"Technical stocks: "
        f"{len(result):,}"
    )


    return result


# =========================================================
# FUNDAMENTALS
# =========================================================

def load_existing_fundamentals() -> pd.DataFrame:

    if not FUNDAMENTAL_FILE.exists():

        return pd.DataFrame()


    try:

        df =
            pd.read_csv(
                FUNDAMENTAL_FILE
            )

        return normalise_symbol_column(
            df
        )

    except Exception as exc:

        print(
            "Unable to read existing "
            f"fundamentals: {exc}"
        )

        return pd.DataFrame()


def run_fundamentals(
    technical_data: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 2 — FUNDAMENTALS"
    )

    print(
        "===================================================="
    )


    /*
     Import lazily so a fundamental API problem does not
     prevent the rest of the scanner from loading.
     */

    try:

        from engines.fundamental_engine import (
            get_fundamentals,
        )

    except ImportError:

        print(
            "Fundamental engine import unavailable."
        )

        return load_existing_fundamentals()


    symbols =
        technical_data[
            "Symbol"
        ].dropna().astype(
            str
        ).tolist()


    fundamentals = None


    try:

        fundamentals =
            get_fundamentals(
                symbols
            )

    except TypeError:

        /*
         Compatibility with engines expecting a
         dataframe instead of symbol list.
         */

        try:

            fundamentals =
                get_fundamentals(
                    technical_data
                )

        except Exception as exc:

            print(
                "Fundamental engine failed: "
                f"{exc}"
            )

    except Exception as exc:

        print(
            "Fundamental engine failed: "
            f"{exc}"
        )


    if fundamentals is None:

        fundamentals =
            load_existing_fundamentals()


    if fundamentals is None:

        fundamentals =
            pd.DataFrame()


    fundamentals =
        normalise_symbol_column(
            fundamentals
        )


    if fundamentals.empty:

        print(
            "Fundamental data unavailable."
        )

        return fundamentals


    save_csv(
        fundamentals,
        FUNDAMENTAL_FILE,
    )


    print(
        f"Fundamental records: "
        f"{len(fundamentals):,}"
    )


    return fundamentals


# =========================================================
# MARKET BREADTH
# =========================================================

def run_market_breadth(
    universe: pd.DataFrame,
) -> tuple[dict, pd.DataFrame]:

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 3 — MARKET BREADTH"
    )

    print(
        "===================================================="
    )


    breadth_result =
        get_market_breadth(
            universe
        )


    /*
     The breadth engine can return either:

        dict

     or:

        (summary, stock_data)

     depending on version.
     */

    breadth_summary = {}
    breadth_stocks =
        pd.DataFrame()


    if isinstance(
        breadth_result,
        tuple,
    ):

        if len(
            breadth_result
        ) >= 1:

            breadth_summary =
                breadth_result[0]


        if len(
            breadth_result
        ) >= 2:

            breadth_stocks =
                breadth_result[1]


    elif isinstance(
        breadth_result,
        dict,
    ):

        breadth_summary =
            breadth_result


        candidate =
            breadth_result.get(
                "stocks"
            )


        if candidate is not None:

            breadth_stocks =
                pd.DataFrame(
                    candidate
                )


    elif isinstance(
        breadth_result,
        pd.DataFrame,
    ):

        breadth_stocks =
            breadth_result


        if not breadth_stocks.empty:

            breadth_summary = {}


    if breadth_summary is None:

        breadth_summary = {}


    if not isinstance(
        breadth_summary,
        dict,
    ):

        try:

            breadth_summary =
                dict(
                    breadth_summary
                )

        except Exception:

            breadth_summary = {}


    breadth_stocks =
        normalise_symbol_column(
            breadth_stocks
        )


    /*
     If engine already saved its own outputs, retain them.
     Otherwise create them here.
     */

    if (
        isinstance(
            breadth_stocks,
            pd.DataFrame,
        )
        and not breadth_stocks.empty
    ):

        save_csv(
            breadth_stocks,
            BREADTH_STOCKS_FILE,
        )


    if breadth_summary:

        save_csv(
            pd.DataFrame(
                [breadth_summary]
            ),
            BREADTH_FILE,
        )


    print(
        "Breadth summary:"
    )

    print(
        json.dumps(
            clean_for_json(
                breadth_summary
            ),
            indent=2,
        )
    )


    return (
        clean_for_json(
            breadth_summary
        ),
        breadth_stocks,
    )


# =========================================================
# MARKET REGIME
# =========================================================

def run_market_engine(
    breadth: dict,
) -> dict:

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 4 — MARKET REGIME"
    )

    print(
        "===================================================="
    )


    market =
        get_market_regime(
            breadth
        )


    if market is None:

        market = {}


    if isinstance(
        market,
        pd.DataFrame,
    ):

        if market.empty:

            market = {}

        else:

            market =
                market.iloc[
                    -1
                ].to_dict()


    if not isinstance(
        market,
        dict,
    ):

        market = {}


    market =
        clean_for_json(
            market
        )


    save_csv(
        pd.DataFrame(
            [market]
        ),
        MARKET_FILE,
    )


    print(
        f"Market Regime: "
        f"{market.get('market_regime', 'Unavailable')}"
    )

    print(
        f"Market Score: "
        f"{market.get('market_score', 'Unavailable')}"
    )


    return market


# =========================================================
# SECTOR ANALYSIS
# =========================================================

def run_sector_engine() -> pd.DataFrame:

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 5 — SECTOR ANALYSIS"
    )

    print(
        "===================================================="
    )


    try:

        result =
            get_sector_analysis()

    except TypeError:

        /*
         Compatibility with sector engines that expect
         no arguments or optional parameters.
         */

        result =
            get_sector_analysis(
                None
            )


    if result is None:

        return pd.DataFrame()


    if not isinstance(
        result,
        pd.DataFrame,
    ):

        result =
            pd.DataFrame(
                result
            )


    if result.empty:

        print(
            "Sector analysis unavailable."
        )

        return result


    save_csv(
        result,
        SECTOR_FILE,
    )


    print(
        f"Sector records: "
        f"{len(result):,}"
    )


    return result


# =========================================================
# SECTOR MAPPING
# =========================================================

def run_sector_mapping() -> pd.DataFrame:

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 6 — SECTOR MAPPING"
    )

    print(
        "===================================================="
    )


    try:

        mapping =
            load_sector_mapping()

    except Exception as exc:

        print(
            "Sector mapping failed: "
            f"{exc}"
        )

        if SECTOR_MAPPING_FILE.exists():

            try:

                mapping =
                    pd.read_csv(
                        SECTOR_MAPPING_FILE
                    )

            except Exception:

                mapping =
                    pd.DataFrame()

        else:

            mapping =
                pd.DataFrame()


    if mapping is None:

        mapping =
            pd.DataFrame()


    if not isinstance(
        mapping,
        pd.DataFrame,
    ):

        mapping =
            pd.DataFrame(
                mapping
            )


    mapping =
        normalise_symbol_column(
            mapping
        )


    if not mapping.empty:

        save_csv(
            mapping,
            SECTOR_MAPPING_FILE,
        )


    print(
        f"Sector mapping records: "
        f"{len(mapping):,}"
    )


    return mapping


# =========================================================
# MERGE SECTOR DATA
# =========================================================

def merge_sector_mapping(
    ranked_input: pd.DataFrame,
    mapping: pd.DataFrame,
) -> pd.DataFrame:

    if (
        ranked_input is None
        or ranked_input.empty
    ):

        return ranked_input


    result =
        ranked_input.copy()


    if (
        mapping is None
        or mapping.empty
    ):

        if (
            "Primary_Sector"
            not in result.columns
        ):

            result[
                "Primary_Sector"
            ] = "Unknown"

        return result


    mapping =
        normalise_symbol_column(
            mapping
        )


    if "Symbol" not in mapping.columns:

        return result


    mapping =
        mapping.drop_duplicates(
            subset=[
                "Symbol"
            ],
            keep="first",
        )


    /*
     Only add columns that don't already exist.
     */

    columns_to_add = [
        "Primary_Sector",
        "Primary_Sector_Index",
        "Primary_Sector_Type",
        "Sector_Indices",
        "sector_indices",
    ]


    available =
        [
            column
            for column
            in columns_to_add
            if column
            in mapping.columns
        ]


    if not available:

        return result


    mapping_subset =
        mapping[
            [
                "Symbol"
            ] + available
        ].copy()


    duplicate_columns = [
        column
        for column
        in available
        if column in result.columns
    ]


    if duplicate_columns:

        /*
         Prefer existing non-empty values.
         */

        for column
        in duplicate_columns:

            mapped_column =
                f"{column}_mapping"

            mapping_subset =
                mapping_subset.rename(
                    columns={
                        column:
                            mapped_column
                    }
                )


        result =
            result.merge(
                mapping_subset,
                on="Symbol",
                how="left",
            )


        for column
        in duplicate_columns:

            mapped_column =
                f"{column}_mapping"

            if (
                mapped_column
                in result.columns
            ):

                result[column] =
                    result[column].where(
                        result[column].notna()
                        &
                        (
                            result[column]
                            .astype(str)
                            .str.strip()
                            != ""
                        ),
                        result[
                            mapped_column
                        ],
                    )

                result =
                    result.drop(
                        columns=[
                            mapped_column
                        ]
                    )

    else:

        result =
            result.merge(
                mapping_subset,
                on="Symbol",
                how="left",
            )


    if (
        "Primary_Sector"
        not in result.columns
    ):

        result[
            "Primary_Sector"
        ] = "Unknown"


    result[
        "Primary_Sector"
    ] = (
        result[
            "Primary_Sector"
        ]
        .fillna("Unknown")
    )


    return result


# =========================================================
# MAIN PIPELINE
# =========================================================

def run_pipeline() -> dict:

    started =
        time.time()


    generated_at =
        datetime.now()
        .astimezone()
        .isoformat()


    print(
        "\n"
        "========================================================"
    )

    print(
        "       NSE SMART MARKET DASHBOARD — SCANNER V3"
    )

    print(
        "========================================================"
    )

    print(
        f"Started: {generated_at}"
    )


    # =====================================================
    # 1. NSE UNIVERSE
    # =====================================================

    print(
        "\n"
        "Loading NSE universe..."
    )


    universe =
        get_nse_universe()


    if universe is None:

        raise RuntimeError(
            "NSE universe returned None."
        )


    if not isinstance(
        universe,
        pd.DataFrame,
    ):

        universe =
            pd.DataFrame(
                universe
            )


    universe =
        normalise_symbol_column(
            universe
        )


    if universe.empty:

        raise RuntimeError(
            "NSE universe is empty."
        )


    print(
        f"NSE universe: "
        f"{len(universe):,}"
    )


    # =====================================================
    # 2. TECHNICAL
    # =====================================================

    technical =
        run_technical_scan(
            universe
        )


    # =====================================================
    # 3. FUNDAMENTALS
    # =====================================================

    fundamentals =
        run_fundamentals(
            technical
        )


    # =====================================================
    # 4. BREADTH
    # =====================================================

    breadth, breadth_stocks =
        run_market_breadth(
            universe
        )


    # =====================================================
    # 5. MARKET REGIME
    # =====================================================

    market =
        run_market_engine(
            breadth
        )


    # =====================================================
    # 6. SECTOR ANALYSIS
    # =====================================================

    sector_analysis =
        run_sector_engine()


    # =====================================================
    # 7. SECTOR MAPPING
    # =====================================================

    sector_mapping =
        run_sector_mapping()


    # =====================================================
    # 8. MERGE SECTOR MAPPING
    # =====================================================

    technical =
        merge_sector_mapping(
            technical,
            sector_mapping,
        )


    # =====================================================
    # 9. RANKING
    # =====================================================

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 7 — STOCK RANKING"
    )

    print(
        "===================================================="
    )


    ranked =
        rank_stocks(
            technical,
            fundamentals,
            sector_analysis,
            market,
        )


    if ranked is None:

        ranked =
            pd.DataFrame()


    if ranked.empty:

        raise RuntimeError(
            "Ranking engine returned no stocks."
        )


    ranked =
        normalise_symbol_column(
            ranked
        )


    save_csv(
        ranked,
        STOCKS_FILE,
    )


    print(
        f"Ranked stocks: "
        f"{len(ranked):,}"
    )


    # =====================================================
    # 10. WATCHLISTS
    # =====================================================

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 8 — WATCHLISTS"
    )

    print(
        "===================================================="
    )


    watchlists =
        create_watchlists(
            ranked,
            market,
        )


    if watchlists is None:

        watchlists = {}


    watchlist_counts = {

        name:
            len(
                values
                if values is not None
                else []
            )

        for name, values
        in watchlists.items()

    }


    for name, count
    in watchlist_counts.items():

        print(
            f"{name:15s}: "
            f"{count:,}"
        )


    # =====================================================
    # 11. SETUP SUMMARY
    # =====================================================

    setup_summary =
        create_setup_summary(
            ranked
        )


    if (
        setup_summary
        is not None
    ):

        save_csv(
            setup_summary,
            SETUP_SUMMARY_FILE,
        )


    # =====================================================
    # 12. EXPORT DATA
    # =====================================================

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 9 — EXPORTS"
    )

    print(
        "===================================================="
    )


    export_data =
        prepare_export_data(
            ranked,
            watchlists,
        )


    for name, dataframe
    in export_data.items():

        if dataframe is None:
            continue

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):

            try:

                dataframe =
                    pd.DataFrame(
                        dataframe
                    )

            except Exception:

                continue


        if dataframe.empty:
            continue


        export_path =
            EXPORT_DIR /
            f"{name}.csv"


        save_csv(
            dataframe,
            export_path,
        )


    # =====================================================
    # 13. EXCEL EXPORT
    # =====================================================

    excel_path =
        EXPORT_DIR /
        "nse_smart_market_dashboard.xlsx"


    try:

        with pd.ExcelWriter(
            excel_path,
            engine="openpyxl",
        ) as writer:

            /*
             Ranked stocks
             */

            ranked.to_excel(
                writer,
                sheet_name="All Stocks",
                index=False,
            )


            /*
             Watchlists
             */

            for name, values
            in watchlists.items():

                if not values:
                    continue


                sheet_name =
                    name[:31]


                pd.DataFrame(
                    values
                ).to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                )


            /*
             Setup summary
             */

            if (
                isinstance(
                    setup_summary,
                    pd.DataFrame,
                )
                and not setup_summary.empty
            ):

                setup_summary.to_excel(
                    writer,
                    sheet_name="Setup Summary",
                    index=False,
                )


            /*
             Breadth stocks
             */

            if (
                isinstance(
                    breadth_stocks,
                    pd.DataFrame,
                )
                and not breadth_stocks.empty
            ):

                breadth_stocks.to_excel(
                    writer,
                    sheet_name="Market Breadth",
                    index=False,
                )


            /*
             Sector analysis
             */

            if (
                isinstance(
                    sector_analysis,
                    pd.DataFrame,
                )
                and not sector_analysis.empty
            ):

                sector_analysis.to_excel(
                    writer,
                    sheet_name="Sectors",
                    index=False,
                )


            /*
             Market regime
             */

            pd.DataFrame(
                [market]
            ).to_excel(
                writer,
                sheet_name="Market Regime",
                index=False,
            )


        print(
            f"Saved Excel: {excel_path}"
        )


    except Exception as exc:

        print(
            "Excel export failed: "
            f"{exc}"
        )


    # =====================================================
    # 14. DASHBOARD DATA
    # =====================================================

    print(
        "\n"
        "===================================================="
    )

    print(
        "STEP 10 — DASHBOARD JSON"
    )

    print(
        "===================================================="
    )


    /*
     Keep ALL ranked stocks in JSON because the dashboard
     supports search/detail views and complete lists.

     The frontend controls visible row limits.
     */

    stocks_records =
        dataframe_to_records(
            ranked
        )


    watchlists_json = {

        name:
            clean_for_json(
                values
            )

        for name, values
        in watchlists.items()

    }


    setup_summary_records =
        dataframe_to_records(
            setup_summary
        )


    sector_records =
        dataframe_to_records(
            sector_analysis
        )


    breadth_stock_records =
        dataframe_to_records(
            breadth_stocks
        )


    /*
     Market object.
     */

    market_clean =
        clean_for_json(
            market
        )


    /*
     Breadth object.
     */

    breadth_clean =
        clean_for_json(
            breadth
        )


    dashboard_data = {

        "dashboard":
            "NSE Smart Market Dashboard",

        "version":
            "3.0",

        "generated_at":
            generated_at,

        "generated_at_display":
            datetime.now()
            .astimezone()
            .strftime(
                "%d %b %Y %I:%M:%S %p %Z"
            ),

        "market_data_authority":
            market_clean.get(
                "market_data_authority",
                "NSE Official + Yahoo Historical",
            ),

        # -----------------------------------------------
        # MARKET
        # -----------------------------------------------

        "market_regime":
            market_clean,

        "market":
            market_clean,

        # -----------------------------------------------
        # BREADTH
        # -----------------------------------------------

        "market_breadth":
            breadth_clean,

        "breadth":
            breadth_clean,

        "market_breadth_stocks":
            breadth_stock_records,

        # -----------------------------------------------
        # SECTORS
        # -----------------------------------------------

        "sector_analysis":
            sector_records,

        "sectors":
            sector_records,

        # -----------------------------------------------
        # STOCKS
        # -----------------------------------------------

        "stocks":
            stocks_records,

        "stock_count":
            len(stocks_records),

        # -----------------------------------------------
        # WATCHLISTS
        # -----------------------------------------------

        "watchlists":
            watchlists_json,

        "watchlist_counts":
            watchlist_counts,

        # -----------------------------------------------
        # SETUPS
        # -----------------------------------------------

        "setup_summary":
            setup_summary_records,

        "setup_counts": {

            str(
                record.get(
                    "Setup",
                    "Unknown",
                )
            ):
                int(
                    record.get(
                        "Count",
                        0,
                    )
                    or 0
                )

            for record
            in setup_summary_records

        },

        # -----------------------------------------------
        # EXPORTS
        # -----------------------------------------------

        "exports": {

            "excel":
                "exports/nse_smart_market_dashboard.xlsx",

            "all_stocks":
                "exports/all_stocks.csv",

        },

        # -----------------------------------------------
        # METADATA
        # -----------------------------------------------

        "universe_count":
            len(universe),

        "technical_count":
            len(technical),

        "fundamental_count":
            len(fundamentals)
            if isinstance(
                fundamentals,
                pd.DataFrame,
            )
            else 0,

        "sector_count":
            len(sector_analysis)
            if isinstance(
                sector_analysis,
                pd.DataFrame,
            )
            else 0,

        "runtime_seconds":
            round(
                time.time()
                - started,
                2,
            ),

    }


    save_json(
        dashboard_data,
        DASHBOARD_JSON_FILE,
    )


    # =====================================================
    # FINAL VALIDATION
    # =====================================================

    print(
        "\n"
        "===================================================="
    )

    print(
        "FINAL VALIDATION"
    )

    print(
        "===================================================="
    )


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


    missing_keys = [
        key
        for key
        in required_keys
        if key not in dashboard_data
    ]


    if missing_keys:

        raise RuntimeError(
            "Dashboard JSON missing keys: "
            +
            ", ".join(
                missing_keys
            )
        )


    if not stocks_records:

        raise RuntimeError(
            "Dashboard JSON contains no stocks."
        )


    if not watchlists_json:

        print(
            "WARNING: No watchlists generated."
        )


    runtime =
        time.time() -
        started


    print(
        "\n"
        "========================================================"
    )

    print(
        "SCANNER COMPLETED SUCCESSFULLY"
    )

    print(
        "========================================================"
    )

    print(
        f"Universe       : {len(universe):,}"
    )

    print(
        f"Technical      : {len(technical):,}"
    )

    print(
        f"Ranked Stocks  : {len(ranked):,}"
    )

    print(
        f"Fundamentals   : "
        f"{len(fundamentals):,}"
        if isinstance(
            fundamentals,
            pd.DataFrame,
        )
        else
        "Fundamentals   : 0"
    )

    print(
        f"Market Regime  : "
        f"{market_clean.get('market_regime')}"
    )

    print(
        f"Market Score   : "
        f"{market_clean.get('market_score')}"
    )

    print(
        f"NIFTY          : "
        f"{market_clean.get('nifty_price')}"
    )

    print(
        f"Bank NIFTY     : "
        f"{market_clean.get('bank_nifty_price')}"
    )

    print(
        f"India VIX      : "
        f"{market_clean.get('vix')}"
    )

    print(
        f"Watchlists     : "
        f"{sum(watchlist_counts.values()):,} "
        f"total selections"
    )

    print(
        f"Runtime        : "
        f"{runtime:.2f} seconds"
    )

    print(
        f"Dashboard JSON : "
        f"{DASHBOARD_JSON_FILE}"
    )

    print(
        "========================================================"
    )


    return dashboard_data


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:

        run_pipeline()

    except KeyboardInterrupt:

        print(
            "\nScanner interrupted by user."
        )

        raise SystemExit(130)

    except Exception as exc:

        print(
            "\n"
            "========================================================"
        )

        print(
            "SCANNER FAILED"
        )

        print(
            "========================================================"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        raise

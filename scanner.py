# ============================================================
# NSE SMART MARKET DASHBOARD V2
# PRODUCTION SCANNER
# Created by Rakesh Nagapuri
# ============================================================

import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from engines.nse_universe import get_nse_universe
from engines.technical_engine import calculate_technical_indicators
from engines.market_breadth import get_market_breadth
from engines.market_engine import get_market_regime
from engines.sector_engine import get_sector_analysis
from engines.ranking_engine import rank_stocks, create_watchlists

from engines.sector_mapping import (
    get_sector_mapping
    if hasattr(__import__("engines.sector_mapping", fromlist=["get_sector_mapping"]),
              "get_sector_mapping")
    else None
)

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = Path("output")
EXPORT_DIR = OUTPUT_DIR / "exports"

TECHNICAL_OUTPUT = OUTPUT_DIR / "technical_scan.csv"
FUNDAMENTAL_OUTPUT = OUTPUT_DIR / "fundamentals.csv"
STOCK_OUTPUT = OUTPUT_DIR / "stocks.csv"

MARKET_OUTPUT = OUTPUT_DIR / "market_regime.csv"
BREADTH_OUTPUT = OUTPUT_DIR / "market_breadth.csv"
BREADTH_STOCK_OUTPUT = OUTPUT_DIR / "market_breadth_stocks.csv"
SECTOR_OUTPUT = OUTPUT_DIR / "sector_analysis.csv"

SETUP_OUTPUT = OUTPUT_DIR / "setup_summary.csv"

DASHBOARD_OUTPUT = OUTPUT_DIR / "dashboard_data.json"

BATCH_SIZE = 100

YF_PERIOD = "2y"

MIN_ROWS = 200

FUNDAMENTAL_SHORTLIST = 500

REQUEST_DELAY = 0.5


# ============================================================
# OUTPUT DIRECTORIES
# ============================================================

def prepare_directories():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def safe_float(value):

    try:

        if value is None:
            return None

        value = float(value)

        if not np.isfinite(value):
            return None

        return value

    except Exception:

        return None


def clean_dataframe(df):

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame(df)

    return df.copy()


def normalize_symbol_column(df):

    df = clean_dataframe(df)

    if df.empty:
        return df

    possible_columns = [
        "symbol",
        "Symbol",
        "SYMBOL",
        "nse_symbol",
        "NSE_SYMBOL"
    ]

    symbol_column = None

    for column in possible_columns:

        if column in df.columns:

            symbol_column = column
            break

    if symbol_column is not None:

        if symbol_column != "symbol":

            df = df.rename(
                columns={
                    symbol_column: "symbol"
                }
            )

        df["symbol"] = (
            df["symbol"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    return df


# ============================================================
# YAHOO DATA EXTRACTION
# ============================================================

def extract_symbol_dataframe(
    downloaded,
    yahoo_symbol
):

    if downloaded is None:
        return pd.DataFrame()

    if downloaded.empty:
        return pd.DataFrame()

    try:

        # ----------------------------------------------------
        # MultiIndex structure
        # ----------------------------------------------------

        if isinstance(
            downloaded.columns,
            pd.MultiIndex
        ):

            level_0 = (
                downloaded.columns
                .get_level_values(0)
            )

            level_1 = (
                downloaded.columns
                .get_level_values(1)
            )

            # Format:
            # Price / Symbol

            if yahoo_symbol in level_1:

                data = downloaded.xs(
                    yahoo_symbol,
                    axis=1,
                    level=1,
                    drop_level=True
                )

                return data.copy()

            # Format:
            # Symbol / Price

            if yahoo_symbol in level_0:

                data = downloaded.xs(
                    yahoo_symbol,
                    axis=1,
                    level=0,
                    drop_level=True
                )

                return data.copy()

        # ----------------------------------------------------
        # Single-symbol download
        # ----------------------------------------------------

        data = downloaded.copy()

        return data

    except Exception:

        return pd.DataFrame()


# ============================================================
# DOWNLOAD TECHNICAL DATA
# ============================================================

def download_market_data(
    symbols
):

    results = []

    symbols = [
        str(symbol).strip()
        for symbol in symbols
        if str(symbol).strip()
    ]

    total = len(symbols)

    print()
    print("=" * 70)
    print("TECHNICAL DATA DOWNLOAD")
    print("=" * 70)
    print(
        f"Total symbols: {total}"
    )

    for start in range(
        0,
        total,
        BATCH_SIZE
    ):

        batch = symbols[
            start:start + BATCH_SIZE
        ]

        print()
        print(
            f"Downloading "
            f"{start + 1}-"
            f"{min(start + BATCH_SIZE, total)} "
            f"of {total}"
        )

        try:

            downloaded = yf.download(
                tickers=batch,
                period=YF_PERIOD,
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=True,
                group_by="column"
            )

        except Exception as error:

            print(
                f"Download failed: {error}"
            )

            continue

        for yahoo_symbol in batch:

            try:

                data = extract_symbol_dataframe(
                    downloaded,
                    yahoo_symbol
                )

                if data.empty:

                    continue

                # ------------------------------------------------
                # Normalize column names
                # ------------------------------------------------

                data.columns = [
                    str(column).strip()
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

                    continue

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

                if len(data) < MIN_ROWS:

                    continue

                symbol = (
                    yahoo_symbol
                    .replace(".NS", "")
                    .upper()
                )

                # ------------------------------------------------
                # Technical engine
                # ------------------------------------------------

                technical = (
                    calculate_technical_indicators(
                        data
                    )
                )

                if technical.empty:

                    continue

                technical[
                    "symbol"
                ] = symbol

                technical[
                    "yahoo_symbol"
                ] = yahoo_symbol

                results.append(
                    technical
                )

            except Exception as error:

                print(
                    f"  {yahoo_symbol}: "
                    f"{error}"
                )

        time.sleep(
            REQUEST_DELAY
        )

    if not results:

        return pd.DataFrame()

    combined = pd.concat(
        results,
        ignore_index=False
    )

    return combined


# ============================================================
# GET LATEST TECHNICAL SNAPSHOT
# ============================================================

def create_latest_snapshot(
    technical_history
):

    if (
        technical_history is None
        or technical_history.empty
    ):

        return pd.DataFrame()

    data = technical_history.copy()

    data = data.sort_index()

    latest_rows = []

    for symbol, group in data.groupby(
        "symbol"
    ):

        if group.empty:

            continue

        latest = group.iloc[-1].copy()

        latest_rows.append(
            latest
        )

    if not latest_rows:

        return pd.DataFrame()

    result = pd.DataFrame(
        latest_rows
    )

    result = (
        result
        .reset_index(drop=True)
    )

    return result


# ============================================================
# LOAD SECTOR MAPPING
# ============================================================

def load_mapping():

    try:

        if get_sector_mapping is not None:

            mapping = get_sector_mapping()

            if (
                mapping is not None
                and not mapping.empty
            ):

                return normalize_symbol_column(
                    mapping
                )

    except Exception as error:

        print(
            f"Sector mapping loader warning: "
            f"{error}"
        )

    # --------------------------------------------------------
    # Fallback to CSV
    # --------------------------------------------------------

    mapping_file = Path(
        "data/sector_mapping.csv"
    )

    if mapping_file.exists():

        try:

            mapping = pd.read_csv(
                mapping_file
            )

            return normalize_symbol_column(
                mapping
            )

        except Exception:

            pass

    return pd.DataFrame()


# ============================================================
# ENRICH WITH NSE MASTER
# ============================================================

def enrich_with_universe(
    snapshot,
    universe
):

    snapshot = normalize_symbol_column(
        snapshot
    )

    universe = normalize_symbol_column(
        universe
    )

    if (
        snapshot.empty
        or universe.empty
    ):

        return snapshot

    # --------------------------------------------------------
    # Keep only useful NSE master fields
    # --------------------------------------------------------

    master_columns = [
        "symbol",
        "company_name",
        "NAME OF COMPANY",
        "YAHOO_SYMBOL"
    ]

    available = [
        column
        for column in master_columns
        if column in universe.columns
    ]

    if "symbol" not in available:

        return snapshot

    master = universe[
        available
    ].copy()

    # --------------------------------------------------------
    # Company name normalization
    # --------------------------------------------------------

    if (
        "company_name"
        not in master.columns
        and
        "NAME OF COMPANY"
        in master.columns
    ):

        master = master.rename(
            columns={
                "NAME OF COMPANY":
                    "company_name"
            }
        )

    master = (
        master
        .drop_duplicates(
            "symbol"
        )
    )

    result = snapshot.merge(
        master,
        on="symbol",
        how="left",
        suffixes=(
            "",
            "_master"
        )
    )

    return result


# ============================================================
# ADD SECTOR INFORMATION
# ============================================================

def enrich_with_sector(
    data,
    sector_mapping
):

    data = normalize_symbol_column(
        data
    )

    sector_mapping = normalize_symbol_column(
        sector_mapping
    )

    if (
        data.empty
        or sector_mapping.empty
    ):

        return data

    # --------------------------------------------------------
    # Normalize sector column names
    # --------------------------------------------------------

    rename_map = {}

    if (
        "primary_sector"
        in sector_mapping.columns
    ):

        rename_map[
            "primary_sector"
        ] = "sector"

    elif (
        "sector"
        not in sector_mapping.columns
    ):

        if (
            "primary_sector_index"
            in sector_mapping.columns
        ):

            rename_map[
                "primary_sector_index"
            ] = "sector"

    if rename_map:

        sector_mapping = (
            sector_mapping.rename(
                columns=rename_map
            )
        )

    # --------------------------------------------------------
    # Keep useful fields
    # --------------------------------------------------------

    preferred = [
        "symbol",
        "sector",
        "primary_sector_index",
        "primary_sector_type",
        "sector_indices"
    ]

    available = [
        column
        for column in preferred
        if column in sector_mapping.columns
    ]

    sector_mapping = (
        sector_mapping[
            available
        ]
        .drop_duplicates(
            "symbol"
        )
    )

    # --------------------------------------------------------
    # Prevent duplicate sector columns
    # --------------------------------------------------------

    data = data.drop(
        columns=[
            column
            for column in [
                "sector",
                "primary_sector",
                "primary_sector_index"
            ]
            if column in data.columns
        ],
        errors="ignore"
    )

    result = data.merge(
        sector_mapping,
        on="symbol",
        how="left"
    )

    return result


# ============================================================
# FUNDAMENTAL ENGINE
# ============================================================

def get_fundamental_function():

    try:

        import engines.fundamental_engine as engine

        possible_functions = [
            "get_fundamentals",
            "get_fundamental_data",
            "fetch_fundamentals",
            "analyze_fundamentals",
            "calculate_fundamentals"
        ]

        for name in possible_functions:

            function = getattr(
                engine,
                name,
                None
            )

            if callable(function):

                return function

    except Exception as error:

        print(
            f"Fundamental engine import warning: "
            f"{error}"
        )

    return None


def run_fundamentals(
    symbols
):

    function = (
        get_fundamental_function()
    )

    if function is None:

        print(
            "Fundamental engine function "
            "not found."
        )

        return pd.DataFrame()

    symbols = list(
        dict.fromkeys(
            symbols
        )
    )

    if not symbols:

        return pd.DataFrame()

    print()
    print("=" * 70)
    print("FUNDAMENTAL ANALYSIS")
    print("=" * 70)
    print(
        f"Fundamental shortlist: "
        f"{len(symbols)}"
    )

    try:

        result = function(
            symbols
        )

        result = clean_dataframe(
            result
        )

        result = normalize_symbol_column(
            result
        )

        return result

    except TypeError:

        # ----------------------------------------------------
        # Some engines may expect yahoo symbols
        # ----------------------------------------------------

        yahoo_symbols = [
            f"{symbol}.NS"
            for symbol in symbols
        ]

        try:

            result = function(
                yahoo_symbols
            )

            result = clean_dataframe(
                result
            )

            result = normalize_symbol_column(
                result
            )

            if "symbol" in result.columns:

                result["symbol"] = (
                    result["symbol"]
                    .astype(str)
                    .str.replace(
                        ".NS",
                        "",
                        regex=False
                    )
                    .str.upper()
                )

            return result

        except Exception as error:

            print(
                f"Fundamental analysis failed: "
                f"{error}"
            )

    except Exception as error:

        print(
            f"Fundamental analysis failed: "
            f"{error}"
        )

    return pd.DataFrame()


# ============================================================
# FUNDAMENTAL SHORTLIST
# ============================================================

def select_fundamental_shortlist(
    technical
):

    if (
        technical is None
        or technical.empty
    ):

        return []

    data = technical.copy()

    candidates = set()

    # --------------------------------------------------------
    # 1. Top technical candidates
    # --------------------------------------------------------

    score_columns = [
        "Technical_Score",
        "technical_score",
        "Overall_Score",
        "overall_score"
    ]

    score_column = None

    for column in score_columns:

        if column in data.columns:

            score_column = column
            break

    if score_column:

        top = (
            data
            .sort_values(
                score_column,
                ascending=False
            )
            .head(300)
        )

        candidates.update(
            top["symbol"]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # 2. Stocks near 52-week high
    # --------------------------------------------------------

    if (
        "Distance_From_52W_High_Pct"
        in data.columns
    ):

        near_high = data[
            data[
                "Distance_From_52W_High_Pct"
            ] >= -15
        ]

        near_high = (
            near_high
            .sort_values(
                "Distance_From_52W_High_Pct",
                ascending=False
            )
            .head(150)
        )

        candidates.update(
            near_high[
                "symbol"
            ].dropna().tolist()
        )

    # --------------------------------------------------------
    # 3. Stocks near 200 DMA
    # --------------------------------------------------------

    if (
        "Distance_From_200DMA_Pct"
        in data.columns
    ):

        dma = data[
            data[
                "Distance_From_200DMA_Pct"
            ].abs() <= 7
        ]

        dma = (
            dma
            .sort_values(
                "Distance_From_200DMA_Pct"
            )
            .head(150)
        )

        candidates.update(
            dma[
                "symbol"
            ].dropna().tolist()
        )

    # --------------------------------------------------------
    # 4. Positive momentum
    # --------------------------------------------------------

    if "Momentum" in data.columns:

        momentum = data[
            data[
                "Momentum"
            ].isin([
                "Strong Positive",
                "Positive"
            ])
        ]

        momentum = (
            momentum
            .head(150)
        )

        candidates.update(
            momentum[
                "symbol"
            ].dropna().tolist()
        )

    # --------------------------------------------------------
    # Limit
    # --------------------------------------------------------

    candidates = list(
        dict.fromkeys(
            candidates
        )
    )

    return candidates[
        :FUNDAMENTAL_SHORTLIST
    ]


# ============================================================
# MERGE FUNDAMENTALS
# ============================================================

def merge_fundamentals(
    technical,
    fundamentals
):

    technical = normalize_symbol_column(
        technical
    )

    fundamentals = normalize_symbol_column(
        fundamentals
    )

    if technical.empty:

        return technical

    if fundamentals.empty:

        technical[
            "fundamental_status"
        ] = "Unavailable"

        return technical

    fundamentals = (
        fundamentals
        .drop_duplicates(
            "symbol"
        )
    )

    # --------------------------------------------------------
    # Avoid duplicate fields
    # --------------------------------------------------------

    overlapping = [
        column
        for column in fundamentals.columns
        if (
            column in technical.columns
            and column != "symbol"
        )
    ]

    if overlapping:

        fundamentals = fundamentals.drop(
            columns=overlapping
        )

    result = technical.merge(
        fundamentals,
        on="symbol",
        how="left"
    )

    if "fundamental_status" not in result.columns:

        important_fields = [
            "roe",
            "roce",
            "revenue_growth",
            "profit_margin",
            "debt_equity",
            "pe"
        ]

        available = [
            column
            for column in important_fields
            if column in result.columns
        ]

        if available:

            result[
                "fundamental_status"
            ] = np.where(
                result[
                    available
                ].notna().sum(axis=1) >= 2,
                "Available",
                "Unavailable"
            )

        else:

            result[
                "fundamental_status"
            ] = "Unavailable"

    return result


# ============================================================
# MARKET REGIME SAFE CALL
# ============================================================

def get_market_context(
    breadth
):

    try:

        market = get_market_regime(
            breadth
        )

        if isinstance(
            market,
            dict
        ):

            return market

        if isinstance(
            market,
            pd.DataFrame
        ):

            return market.to_dict(
                orient="records"
            )

        return market

    except TypeError:

        try:

            return get_market_regime()

        except Exception as error:

            print(
                f"Market regime failed: "
                f"{error}"
            )

    except Exception as error:

        print(
            f"Market regime failed: "
            f"{error}"
        )

    return {}


# ============================================================
# SECTOR ANALYSIS SAFE CALL
# ============================================================

def get_sector_context():

    try:

        result = get_sector_analysis()

        return clean_dataframe(
            result
        )

    except TypeError:

        try:

            result = get_sector_analysis(
                save_output=True
            )

            return clean_dataframe(
                result
            )

        except Exception as error:

            print(
                f"Sector analysis failed: "
                f"{error}"
            )

    except Exception as error:

        print(
            f"Sector analysis failed: "
            f"{error}"
        )

    return pd.DataFrame()


# ============================================================
# RANKING
# ============================================================

def run_ranking(
    technical,
    fundamentals,
    sector_data,
    market_regime
):

    try:

        ranked = rank_stocks(
            technical_data=technical,
            fundamental_data=fundamentals,
            sector_data=sector_data,
            market_regime=market_regime
        )

        return clean_dataframe(
            ranked
        )

    except TypeError:

        # ----------------------------------------------------
        # Fallback for positional signature
        # ----------------------------------------------------

        try:

            ranked = rank_stocks(
                technical,
                fundamentals,
                sector_data,
                market_regime
            )

            return clean_dataframe(
                ranked
            )

        except Exception as error:

            print(
                f"Ranking failed: "
                f"{error}"
            )

    except Exception as error:

        print(
            f"Ranking failed: "
            f"{error}"
        )

    return pd.DataFrame()


# ============================================================
# WATCHLIST CREATION
# ============================================================

def run_watchlists(
    ranked,
    market_regime
):

    try:

        result = create_watchlists(
            ranked,
            market_regime=market_regime
        )

        if isinstance(
            result,
            dict
        ):

            return result

    except TypeError:

        try:

            result = create_watchlists(
                ranked,
                market_regime
            )

            if isinstance(
                result,
                dict
            ):

                return result

        except Exception as error:

            print(
                f"Watchlist creation failed: "
                f"{error}"
            )

    except Exception as error:

        print(
            f"Watchlist creation failed: "
            f"{error}"
        )

    return {}


# ============================================================
# SAVE DATAFRAME
# ============================================================

def save_csv(
    df,
    path
):

    if (
        df is None
        or df.empty
    ):

        return

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        path,
        index=False
    )


# ============================================================
# EXCEL EXPORT
# ============================================================

def export_excel(
    df,
    filename
):

    if (
        df is None
        or df.empty
    ):

        return

    try:

        path = (
            EXPORT_DIR /
            filename
        )

        df.to_excel(
            path,
            index=False
        )

        print(
            f"Excel export: {path}"
        )

    except Exception as error:

        print(
            f"Excel export failed "
            f"for {filename}: "
            f"{error}"
        )


# ============================================================
# EXPORT WATCHLISTS
# ============================================================

def export_watchlists(
    watchlists
):

    if not watchlists:

        return

    for name, data in watchlists.items():

        if not isinstance(
            data,
            pd.DataFrame
        ):

            try:

                data = pd.DataFrame(
                    data
                )

            except Exception:

                continue

        if data.empty:

            continue

        csv_path = (
            OUTPUT_DIR /
            f"{name}.csv"
        )

        excel_path = (
            EXPORT_DIR /
            f"{name}.xlsx"
        )

        save_csv(
            data,
            csv_path
        )

        export_excel(
            data,
            f"{name}.xlsx"
        )


# ============================================================
# SETUP SUMMARY
# ============================================================

def create_setup_summary(
    watchlists
):

    rows = []

    for name, data in watchlists.items():

        if not isinstance(
            data,
            pd.DataFrame
        ):

            continue

        if data.empty:

            continue

        setup_name = (
            str(name)
            .replace("_", " ")
            .title()
        )

        rows.append({

            "watchlist":
                name,

            "setup":
                setup_name,

            "stocks":
                len(data)

        })

    if not rows:

        return pd.DataFrame()

    return pd.DataFrame(
        rows
    )


# ============================================================
# MARKET REGIME SERIALIZATION
# ============================================================

def make_json_safe(
    value
):

    if isinstance(
        value,
        dict
    ):

        return {
            str(key):
                make_json_safe(val)
            for key, val
            in value.items()
        }

    if isinstance(
        value,
        list
    ):

        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        tuple
    ):

        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        pd.Timestamp
    ):

        return value.isoformat()

    if isinstance(
        value,
        np.generic
    ):

        return make_json_safe(
            value.item()
        )

    if pd.isna(value):

        return None

    return value


# ============================================================
# DATAFRAME TO RECORDS
# ============================================================

def dataframe_records(
    df
):

    if (
        df is None
        or df.empty
    ):

        return []

    clean = df.copy()

    clean = clean.replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )

    clean = clean.where(
        pd.notna(clean),
        None
    )

    records = (
        clean
        .to_dict(
            orient="records"
        )
    )

    return make_json_safe(
        records
    )


# ============================================================
# DASHBOARD JSON
# ============================================================

def create_dashboard_json(
    market_regime,
    breadth,
    sector_data,
    ranked,
    watchlists
):

    dashboard = {

        "dashboard": {
            "name":
                "NSE Smart Market Dashboard",

            "version":
                "2.0",

            "created_by":
                "Rakesh Nagapuri",

            "data_type":
                "End of Day",

            "disclaimer":
                (
                    "This dashboard is for market "
                    "analysis and educational purposes. "
                    "It is not investment advice."
                )
        },

        "generated_at":
            pd.Timestamp.now(
                tz="Asia/Kolkata"
            ).isoformat(),

        "market_regime":
            make_json_safe(
                market_regime
            ),

        "market_breadth":
            make_json_safe(
                breadth
            ),

        "sector_analysis":
            dataframe_records(
                sector_data
            ),

        "stocks":
            dataframe_records(
                ranked
            ),

        "watchlists": {}
    }

    # --------------------------------------------------------
    # Watchlists
    # --------------------------------------------------------

    for name, data in watchlists.items():

        dashboard[
            "watchlists"
        ][name] = dataframe_records(
            data
        )

    # --------------------------------------------------------
    # Watchlist counts
    # --------------------------------------------------------

    dashboard[
        "watchlist_counts"
    ] = {

        name:
            len(data)
            if isinstance(
                data,
                pd.DataFrame
            )
            else 0

        for name, data
        in watchlists.items()
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        DASHBOARD_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dashboard,
            file,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    print()
    print(
        f"Dashboard JSON created: "
        f"{DASHBOARD_OUTPUT}"
    )


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_final_summary(
    universe,
    technical,
    ranked,
    market_regime,
    watchlists
):

    print()
    print()
    print("=" * 80)
    print("NSE SMART MARKET DASHBOARD")
    print("PRODUCTION SCAN COMPLETED")
    print("=" * 80)

    print()

    print(
        f"NSE Universe: "
        f"{len(universe):,}"
    )

    print(
        f"Stocks technically analyzed: "
        f"{ranked['symbol'].nunique():,}"
        if (
            not ranked.empty
            and "symbol" in ranked.columns
        )
        else
        f"Stocks technically analyzed: "
        f"{len(technical):,}"
    )

    print()

    # --------------------------------------------------------
    # Market regime
    # --------------------------------------------------------

    if isinstance(
        market_regime,
        dict
    ):

        print(
            "MARKET REGIME"
        )

        print(
            f"Regime: "
            f"{market_regime.get('regime', 'N/A')}"
        )

        print(
            f"Score: "
            f"{market_regime.get('market_score', 'N/A')}"
        )

        print()

    # --------------------------------------------------------
    # Watchlists
    # --------------------------------------------------------

    print(
        "WATCHLISTS"
    )

    for name, data in watchlists.items():

        count = (
            len(data)
            if isinstance(
                data,
                pd.DataFrame
            )
            else 0
        )

        print(
            f"{name:<20} "
            f"{count:>5}"
        )

    print()

    print(
        "OUTPUT FILES"
    )

    print(
        f"Dashboard JSON: "
        f"{DASHBOARD_OUTPUT}"
    )

    print(
        f"Exports folder: "
        f"{EXPORT_DIR}"
    )

    print()

    print("=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)


# ============================================================
# MAIN PRODUCTION PIPELINE
# ============================================================

def main():

    start_time = time.time()

    print()
    print("=" * 80)
    print("NSE SMART MARKET DASHBOARD V2")
    print("PRODUCTION MARKET SCANNER")
    print("Created by Rakesh Nagapuri")
    print("=" * 80)

    prepare_directories()

    # ========================================================
    # STEP 1 — NSE UNIVERSE
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 1 — NSE EQUITY UNIVERSE")
    print("=" * 70)

    universe = get_nse_universe()

    if (
        universe is None
        or universe.empty
    ):

        raise RuntimeError(
            "NSE equity universe could not be loaded."
        )

    universe = normalize_symbol_column(
        universe
    )

    if "YAHOO_SYMBOL" in universe.columns:

        yahoo_symbols = (
            universe[
                "YAHOO_SYMBOL"
            ]
            .dropna()
            .astype(str)
            .tolist()
        )

    else:

        yahoo_symbols = [
            f"{symbol}.NS"
            for symbol
            in universe[
                "symbol"
            ]
            .dropna()
            .tolist()
        ]

    print(
        f"Universe stocks: "
        f"{len(yahoo_symbols):,}"
    )

    # ========================================================
    # STEP 2 — MARKET BREADTH
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 2 — MARKET BREADTH")
    print("=" * 70)

    try:

        breadth_result = (
            get_market_breadth(
                universe
            )
        )

    except TypeError:

        breadth_result = (
            get_market_breadth()
        )

    except Exception as error:

        print(
            f"Market breadth failed: "
            f"{error}"
        )

        breadth_result = {}

    # --------------------------------------------------------
    # Save breadth
    # --------------------------------------------------------

    if isinstance(
        breadth_result,
        dict
    ):

        breadth_summary = (
            breadth_result.get(
                "summary",
                breadth_result
            )
        )

        breadth_stocks = (
            breadth_result.get(
                "stocks",
                pd.DataFrame()
            )
        )

    elif isinstance(
        breadth_result,
        pd.DataFrame
    ):

        breadth_summary = {}

        breadth_stocks = (
            breadth_result
        )

    else:

        breadth_summary = {}
        breadth_stocks = pd.DataFrame()

    if isinstance(
        breadth_summary,
        dict
    ):

        pd.DataFrame(
            [
                breadth_summary
            ]
        ).to_csv(
            BREADTH_OUTPUT,
            index=False
        )

    if isinstance(
        breadth_stocks,
        pd.DataFrame
    ):

        save_csv(
            breadth_stocks,
            BREADTH_STOCK_OUTPUT
        )

    # ========================================================
    # STEP 3 — MARKET REGIME
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 3 — MARKET REGIME")
    print("=" * 70)

    market_regime = (
        get_market_context(
            breadth_result
        )
    )

    if isinstance(
        market_regime,
        dict
    ):

        pd.DataFrame(
            [
                market_regime
            ]
        ).to_csv(
            MARKET_OUTPUT,
            index=False
        )

        print(
            f"Market regime: "
            f"{market_regime.get('regime', 'N/A')}"
        )

    # ========================================================
    # STEP 4 — SECTOR ANALYSIS
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 4 — SECTOR ANALYSIS")
    print("=" * 70)

    sector_data = (
        get_sector_context()
    )

    save_csv(
        sector_data,
        SECTOR_OUTPUT
    )

    print(
        f"Sectors analyzed: "
        f"{len(sector_data)}"
    )

    # ========================================================
    # STEP 5 — TECHNICAL DATA
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 5 — FULL NSE TECHNICAL SCAN")
    print("=" * 70)

    technical_history = (
        download_market_data(
            yahoo_symbols
        )
    )

    if (
        technical_history is None
        or technical_history.empty
    ):

        raise RuntimeError(
            "Technical scan returned no data."
        )

    # --------------------------------------------------------
    # Latest snapshot
    # --------------------------------------------------------

    technical = (
        create_latest_snapshot(
            technical_history
        )
    )

    technical = normalize_symbol_column(
        technical
    )

    print(
        f"Technical stocks: "
        f"{len(technical):,}"
    )

    save_csv(
        technical,
        TECHNICAL_OUTPUT
    )

    # ========================================================
    # STEP 6 — NSE MASTER ENRICHMENT
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 6 — NSE MASTER ENRICHMENT")
    print("=" * 70)

    technical = enrich_with_universe(
        technical,
        universe
    )

    # ========================================================
    # STEP 7 — SECTOR MAPPING
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 7 — STOCK SECTOR MAPPING")
    print("=" * 70)

    sector_mapping = (
        load_mapping()
    )

    print(
        f"Sector mapped stocks: "
        f"{len(sector_mapping):,}"
    )

    technical = enrich_with_sector(
        technical,
        sector_mapping
    )

    # ========================================================
    # STEP 8 — PRELIMINARY TECHNICAL RANKING
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 8 — PRELIMINARY TECHNICAL RANKING")
    print("=" * 70)

    preliminary = run_ranking(
        technical,
        pd.DataFrame(),
        sector_data,
        market_regime
    )

    if preliminary.empty:

        # ----------------------------------------------------
        # If ranking requires fundamentals, use technical
        # data directly for shortlist selection.
        # ----------------------------------------------------

        preliminary = technical.copy()

    # ========================================================
    # STEP 9 — FUNDAMENTAL SHORTLIST
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 9 — FUNDAMENTAL SHORTLIST")
    print("=" * 70)

    fundamental_symbols = (
        select_fundamental_shortlist(
            preliminary
        )
    )

    print(
        f"Fundamental candidates: "
        f"{len(fundamental_symbols):,}"
    )

    # ========================================================
    # STEP 10 — FUNDAMENTAL ANALYSIS
    # ========================================================

    fundamentals = run_fundamentals(
        fundamental_symbols
    )

    save_csv(
        fundamentals,
        FUNDAMENTAL_OUTPUT
    )

    print(
        f"Fundamental records: "
        f"{len(fundamentals):,}"
    )

    # ========================================================
    # STEP 11 — MERGE FUNDAMENTALS
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 11 — FINAL DATASET")
    print("=" * 70)

    final_data = merge_fundamentals(
        technical,
        fundamentals
    )

    # ========================================================
    # STEP 12 — FINAL RANKING
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 12 — FINAL TECHNICAL + FUNDAMENTAL RANKING")
    print("=" * 70)

    ranked = run_ranking(
        final_data,
        fundamentals,
        sector_data,
        market_regime
    )

    if ranked.empty:

        ranked = final_data.copy()

    ranked = normalize_symbol_column(
        ranked
    )

    print(
        f"Final ranked stocks: "
        f"{len(ranked):,}"
    )

    # ========================================================
    # STEP 13 — SAVE MASTER STOCK FILE
    # ========================================================

    save_csv(
        ranked,
        STOCK_OUTPUT
    )

    # ========================================================
    # STEP 14 — WATCHLISTS
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 14 — SMART WATCHLISTS")
    print("=" * 70)

    watchlists = run_watchlists(
        ranked,
        market_regime
    )

    # --------------------------------------------------------
    # Ensure expected watchlist names exist
    # --------------------------------------------------------

    expected_watchlists = [
        "next_day",
        "intraday",
        "swing",
        "long_term",
        "52w_high",
        "dma_recovery",
        "options",
        "momentum",
        "breakout"
    ]

    for name in expected_watchlists:

        if name not in watchlists:

            watchlists[
                name
            ] = pd.DataFrame()

    # ========================================================
    # STEP 15 — SAVE WATCHLISTS
    # ========================================================

    export_watchlists(
        watchlists
    )

    # ========================================================
    # STEP 16 — SETUP SUMMARY
    # ========================================================

    setup_summary = (
        create_setup_summary(
            watchlists
        )
    )

    save_csv(
        setup_summary,
        SETUP_OUTPUT
    )

    export_excel(
        setup_summary,
        "setup_summary.xlsx"
    )

    # ========================================================
    # STEP 17 — DASHBOARD JSON
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 17 — DASHBOARD DATA")
    print("=" * 70)

    create_dashboard_json(
        market_regime=market_regime,
        breadth=breadth_summary,
        sector_data=sector_data,
        ranked=ranked,
        watchlists=watchlists
    )

    # ========================================================
    # STEP 18 — FINAL SUMMARY
    # ========================================================

    elapsed = (
        time.time()
        - start_time
    )

    print_final_summary(
        universe=universe,
        technical=technical,
        ranked=ranked,
        market_regime=market_regime,
        watchlists=watchlists
    )

    print()
    print(
        f"Total execution time: "
        f"{elapsed / 60:.2f} minutes"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()
        print(
            "Scanner stopped by user."
        )

        raise SystemExit(1)

    except Exception as error:

        print()
        print("=" * 80)
        print("SCANNER FAILED")
        print("=" * 80)

        print(
            f"Error: {error}"
        )

        raise

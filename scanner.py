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
import yfinance as yf

from engines.nse_universe import get_nse_universe
from engines.technical_engine import calculate_technical_indicators
from engines.market_breadth import get_market_breadth
from engines.market_engine import get_market_regime
from engines.sector_engine import get_sector_analysis
from engines.sector_mapping import load_sector_mapping
from engines.ranking_engine import rank_stocks, create_watchlists

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
# DIRECTORY SETUP
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
# GENERAL HELPERS
# ============================================================

def clean_dataframe(df):

    if df is None:
        return pd.DataFrame()

    if isinstance(df, pd.DataFrame):
        return df.copy()

    try:
        return pd.DataFrame(df)

    except Exception:
        return pd.DataFrame()


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

    if symbol_column is None:
        return df

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
        .str.replace(
            ".NS",
            "",
            regex=False
        )
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
        # MultiIndex result
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

            # ------------------------------------------------
            # Structure:
            # Price / Symbol
            # ------------------------------------------------

            if yahoo_symbol in level_1:

                return downloaded.xs(
                    yahoo_symbol,
                    axis=1,
                    level=1,
                    drop_level=True
                ).copy()

            # ------------------------------------------------
            # Structure:
            # Symbol / Price
            # ------------------------------------------------

            if yahoo_symbol in level_0:

                return downloaded.xs(
                    yahoo_symbol,
                    axis=1,
                    level=0,
                    drop_level=True
                ).copy()

            return pd.DataFrame()

        # ----------------------------------------------------
        # Single-symbol result
        # ----------------------------------------------------

        return downloaded.copy()

    except Exception:

        return pd.DataFrame()


# ============================================================
# DOWNLOAD FULL NSE TECHNICAL DATA
# ============================================================

def download_market_data(symbols):

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
    print(f"Total symbols: {total:,}")

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
            f"{start + 1:,}-"
            f"{min(start + BATCH_SIZE, total):,} "
            f"of {total:,}"
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
                f"Batch download failed: {error}"
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

                # --------------------------------------------
                # Normalize columns
                # --------------------------------------------

                data.columns = [
                    str(column).strip()
                    for column in data.columns
                ]

                required_columns = [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"
                ]

                if not all(
                    column in data.columns
                    for column in required_columns
                ):
                    continue

                data = data[
                    required_columns
                ].copy()

                for column in required_columns:

                    data[column] = pd.to_numeric(
                        data[column],
                        errors="coerce"
                    )

                data = data.dropna(
                    subset=["Close"]
                )

                if len(data) < MIN_ROWS:
                    continue

                symbol = (
                    yahoo_symbol
                    .replace(".NS", "")
                    .upper()
                )

                # --------------------------------------------
                # Technical engine
                # --------------------------------------------

                technical = (
                    calculate_technical_indicators(
                        data
                    )
                )

                if technical is None:
                    continue

                if technical.empty:
                    continue

                technical = technical.copy()

                technical["symbol"] = symbol
                technical["yahoo_symbol"] = yahoo_symbol

                results.append(
                    technical
                )

            except Exception as error:

                print(
                    f"{yahoo_symbol}: {error}"
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
# CREATE LATEST TECHNICAL SNAPSHOT
# ============================================================

def create_latest_snapshot(
    technical_history
):

    if technical_history is None:
        return pd.DataFrame()

    if technical_history.empty:
        return pd.DataFrame()

    latest_rows = []

    for symbol, group in technical_history.groupby(
        "symbol"
    ):

        if group.empty:
            continue

        group = group.sort_index()

        latest = (
            group
            .iloc[-1]
            .copy()
        )

        latest_rows.append(
            latest
        )

    if not latest_rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(
            latest_rows
        )
        .reset_index(drop=True)
    )


# ============================================================
# LOAD SECTOR MAPPING
# ============================================================

def load_mapping():

    try:

        mapping = load_sector_mapping()

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
    # Direct CSV fallback
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

        except Exception as error:

            print(
                f"Unable to load sector mapping CSV: "
                f"{error}"
            )

    return pd.DataFrame()


# ============================================================
# NSE MASTER ENRICHMENT
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

    if snapshot.empty:
        return snapshot

    if universe.empty:
        return snapshot

    master = universe.copy()

    # --------------------------------------------------------
    # Company name
    # --------------------------------------------------------

    company_name_candidates = [
        "company_name",
        "NAME OF COMPANY",
        "NAME_OF_COMPANY",
        "NAME"
    ]

    company_column = None

    for column in company_name_candidates:

        if column in master.columns:

            company_column = column
            break

    columns = ["symbol"]

    if company_column is not None:

        if company_column != "company_name":

            master = master.rename(
                columns={
                    company_column:
                        "company_name"
                }
            )

        columns.append(
            "company_name"
        )

    master = (
        master[
            list(
                dict.fromkeys(
                    columns
                )
            )
        ]
        .drop_duplicates(
            subset=["symbol"]
        )
    )

    return snapshot.merge(
        master,
        on="symbol",
        how="left"
    )


# ============================================================
# SECTOR ENRICHMENT
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

    if data.empty:
        return data

    if sector_mapping.empty:

        print(
            "Sector mapping unavailable."
        )

        return data

    mapping = sector_mapping.copy()

    # --------------------------------------------------------
    # Normalize sector field
    # --------------------------------------------------------

    if "primary_sector" in mapping.columns:

        mapping = mapping.rename(
            columns={
                "primary_sector":
                    "sector"
            }
        )

    elif (
        "sector" not in mapping.columns
        and
        "primary_sector_index"
        in mapping.columns
    ):

        mapping["sector"] = (
            mapping[
                "primary_sector_index"
            ]
        )

    preferred_columns = [
        "symbol",
        "sector",
        "primary_sector_index",
        "primary_sector_type",
        "sector_indices"
    ]

    available_columns = [
        column
        for column in preferred_columns
        if column in mapping.columns
    ]

    if "symbol" not in available_columns:
        return data

    mapping = (
        mapping[
            available_columns
        ]
        .drop_duplicates(
            subset=["symbol"]
        )
    )

    # --------------------------------------------------------
    # Remove existing mapping fields
    # --------------------------------------------------------

    fields_to_remove = [
        "sector",
        "primary_sector",
        "primary_sector_index",
        "primary_sector_type",
        "sector_indices"
    ]

    data = data.drop(
        columns=[
            column
            for column in fields_to_remove
            if column in data.columns
        ],
        errors="ignore"
    )

    return data.merge(
        mapping,
        on="symbol",
        how="left"
    )


# ============================================================
# FUNDAMENTAL ENGINE DISCOVERY
# ============================================================

def get_fundamental_function():

    try:

        import engines.fundamental_engine as engine

    except Exception as error:

        print(
            f"Unable to import fundamental engine: "
            f"{error}"
        )

        return None

    possible_functions = [
        "get_fundamentals",
        "get_fundamental_data",
        "fetch_fundamentals",
        "analyze_fundamentals",
        "calculate_fundamentals"
    ]

    for function_name in possible_functions:

        function = getattr(
            engine,
            function_name,
            None
        )

        if callable(function):
            return function

    return None


# ============================================================
# RUN FUNDAMENTALS
# ============================================================

def run_fundamentals(symbols):

    function = get_fundamental_function()

    if function is None:

        print(
            "No compatible fundamental "
            "engine function found."
        )

        return pd.DataFrame()

    symbols = [
        str(symbol)
        .replace(".NS", "")
        .strip()
        .upper()
        for symbol in symbols
        if str(symbol).strip()
    ]

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
        f"{len(symbols):,}"
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

    except Exception as first_error:

        print(
            "Direct NSE symbol call failed. "
            "Trying Yahoo symbols..."
        )

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

            return result

        except Exception as second_error:

            print(
                f"Fundamental analysis failed: "
                f"{second_error}"
            )

            print(
                f"Initial error: "
                f"{first_error}"
            )

            return pd.DataFrame()


# ============================================================
# FUNDAMENTAL SHORTLIST
# ============================================================

def select_fundamental_shortlist(
    technical
):

    if technical is None:
        return []

    if technical.empty:
        return []

    data = technical.copy()

    candidates = set()

    # --------------------------------------------------------
    # Technical ranking
    # --------------------------------------------------------

    score_column = None

    for column in [
        "Overall_Score",
        "overall_score",
        "Technical_Score",
        "technical_score"
    ]:

        if column in data.columns:

            score_column = column
            break

    if score_column is not None:

        scores = pd.to_numeric(
            data[score_column],
            errors="coerce"
        )

        temp = data.copy()
        temp["_shortlist_score"] = scores

        top = (
            temp
            .sort_values(
                "_shortlist_score",
                ascending=False
            )
            .head(300)
        )

        candidates.update(
            top[
                "symbol"
            ]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # Near rolling 52-week high
    # --------------------------------------------------------

    if (
        "Distance_From_52W_High_Pct"
        in data.columns
    ):

        distance = pd.to_numeric(
            data[
                "Distance_From_52W_High_Pct"
            ],
            errors="coerce"
        )

        near_high = data[
            (distance >= -15)
            &
            (distance <= 5)
        ].copy()

        near_high[
            "_distance"
        ] = distance.loc[
            near_high.index
        ]

        near_high = (
            near_high
            .sort_values(
                "_distance",
                ascending=False
            )
            .head(150)
        )

        candidates.update(
            near_high[
                "symbol"
            ]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # Near 200 DMA
    # --------------------------------------------------------

    if (
        "Distance_From_200DMA_Pct"
        in data.columns
    ):

        dma_distance = pd.to_numeric(
            data[
                "Distance_From_200DMA_Pct"
            ],
            errors="coerce"
        )

        dma = data[
            dma_distance.abs() <= 7
        ].copy()

        dma[
            "_dma_abs"
        ] = dma_distance.loc[
            dma.index
        ].abs()

        dma = (
            dma
            .sort_values(
                "_dma_abs",
                ascending=True
            )
            .head(150)
        )

        candidates.update(
            dma[
                "symbol"
            ]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # Positive momentum
    # --------------------------------------------------------

    if "Momentum" in data.columns:

        momentum = data[
            data[
                "Momentum"
            ].isin([
                "Strong Positive",
                "Positive"
            ])
        ].copy()

        if score_column is not None:

            momentum[
                "_score"
            ] = pd.to_numeric(
                momentum[
                    score_column
                ],
                errors="coerce"
            )

            momentum = (
                momentum
                .sort_values(
                    "_score",
                    ascending=False
                )
            )

        momentum = momentum.head(
            150
        )

        candidates.update(
            momentum[
                "symbol"
            ]
            .dropna()
            .tolist()
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if not candidates:

        candidates.update(
            data[
                "symbol"
            ]
            .dropna()
            .head(
                FUNDAMENTAL_SHORTLIST
            )
            .tolist()
        )

    candidates = list(
        dict.fromkeys(
            candidates
        )
    )

    return candidates[
        :FUNDAMENTAL_SHORTLIST
    ]


# ============================================================
# MARKET REGIME
# ============================================================

def get_market_context(
    breadth
):

    try:

        return get_market_regime(
            breadth
        )

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
# SECTOR ANALYSIS
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
# WATCHLISTS
# ============================================================

def run_watchlists(
    ranked,
    market_regime
):

    try:

        watchlists = create_watchlists(
            ranked,
            market_regime=market_regime
        )

        if isinstance(
            watchlists,
            dict
        ):

            return watchlists

    except TypeError:

        try:

            watchlists = create_watchlists(
                ranked,
                market_regime
            )

            if isinstance(
                watchlists,
                dict
            ):

                return watchlists

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
# SAVE CSV
# ============================================================

def save_csv(
    df,
    path
):

    if df is None:
        return

    if not isinstance(
        df,
        pd.DataFrame
    ):
        return

    if df.empty:
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
# SAVE DICTIONARY AS CSV
# ============================================================

def save_dict_csv(
    data,
    path
):

    if not isinstance(
        data,
        dict
    ):
        return

    try:

        flat = {}

        for key, value in data.items():

            if isinstance(
                value,
                (
                    dict,
                    list,
                    tuple,
                    pd.DataFrame
                )
            ):

                flat[key] = json.dumps(
                    make_json_safe(
                        value
                    ),
                    default=str
                )

            else:

                flat[key] = value

        pd.DataFrame(
            [flat]
        ).to_csv(
            path,
            index=False
        )

    except Exception as error:

        print(
            f"Unable to save {path}: "
            f"{error}"
        )


# ============================================================
# EXCEL EXPORT
# ============================================================

def export_excel(
    df,
    filename
):

    if df is None:
        return

    if not isinstance(
        df,
        pd.DataFrame
    ):
        return

    if df.empty:
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
            f"Excel export failed for "
            f"{filename}: {error}"
        )


# ============================================================
# EXPORT WATCHLISTS
# ============================================================

def export_watchlists(
    watchlists
):

    for name, data in watchlists.items():

        data = clean_dataframe(
            data
        )

        if data.empty:
            continue

        save_csv(
            data,
            OUTPUT_DIR /
            f"{name}.csv"
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

        data = clean_dataframe(
            data
        )

        rows.append({

            "watchlist":
                name,

            "setup":
                str(name)
                .replace(
                    "_",
                    " "
                )
                .title(),

            "stocks":
                len(data)

        })

    return pd.DataFrame(
        rows
    )


# ============================================================
# JSON HELPERS
# ============================================================

def make_json_safe(value):

    if isinstance(
        value,
        pd.DataFrame
    ):

        return dataframe_records(
            value
        )

    if isinstance(
        value,
        pd.Series
    ):

        return make_json_safe(
            value.to_dict()
        )

    if isinstance(
        value,
        dict
    ):

        return {

            str(key):
                make_json_safe(item)

            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple
        )
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

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    if isinstance(
        value,
        float
    ):

        if not np.isfinite(
            value
        ):
            return None

    return value


def dataframe_records(df):

    if df is None:
        return []

    if not isinstance(
        df,
        pd.DataFrame
    ):
        return []

    if df.empty:
        return []

    clean = df.copy()

    clean = clean.replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )

    records = clean.to_dict(
        orient="records"
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
                    "Market analysis and educational "
                    "dashboard. Not investment advice."
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

        "watchlists": {},

        "watchlist_counts": {}
    }

    for name, data in watchlists.items():

        data = clean_dataframe(
            data
        )

        dashboard[
            "watchlists"
        ][name] = dataframe_records(
            data
        )

        dashboard[
            "watchlist_counts"
        ][name] = len(
            data
        )

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
        f"Technical stocks: "
        f"{len(technical):,}"
    )

    print(
        f"Final ranked stocks: "
        f"{len(ranked):,}"
    )

    print()

    if isinstance(
        market_regime,
        dict
    ):

        print(
            "MARKET REGIME"
        )

        print(
            "Regime:",
            market_regime.get(
                "regime",
                "N/A"
            )
        )

        print(
            "Score:",
            market_regime.get(
                "market_score",
                "N/A"
            )
        )

        print()

    print(
        "WATCHLISTS"
    )

    for name, data in watchlists.items():

        data = clean_dataframe(
            data
        )

        print(
            f"{name:<20}"
            f"{len(data):>6}"
        )

    print()
    print(
        f"Dashboard JSON: "
        f"{DASHBOARD_OUTPUT}"
    )

    print(
        f"Excel exports: "
        f"{EXPORT_DIR}"
    )

    print()
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
    # STEP 1
    # NSE EQUITY UNIVERSE
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 1 — NSE EQUITY UNIVERSE")
    print("=" * 70)

    universe = get_nse_universe()

    universe = normalize_symbol_column(
        universe
    )

    if universe.empty:

        raise RuntimeError(
            "NSE equity universe "
            "could not be loaded."
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

    elif "yahoo_symbol" in universe.columns:

        yahoo_symbols = (
            universe[
                "yahoo_symbol"
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

    yahoo_symbols = list(
        dict.fromkeys(
            yahoo_symbols
        )
    )

    print(
        f"NSE universe: "
        f"{len(yahoo_symbols):,}"
    )

    # ========================================================
    # STEP 2
    # MARKET BREADTH
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 2 — MARKET BREADTH")
    print("=" * 70)

    breadth_result = {}

    try:

        breadth_result = (
            get_market_breadth(
                universe
            )
        )

    except TypeError:

        try:

            breadth_result = (
                get_market_breadth()
            )

        except Exception as error:

            print(
                f"Market breadth failed: "
                f"{error}"
            )

    except Exception as error:

        print(
            f"Market breadth failed: "
            f"{error}"
        )

    breadth_summary = {}
    breadth_stocks = pd.DataFrame()

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

        breadth_stocks = clean_dataframe(
            breadth_result.get(
                "stocks"
            )
        )

    elif isinstance(
        breadth_result,
        pd.DataFrame
    ):

        breadth_stocks = (
            breadth_result.copy()
        )

    if isinstance(
        breadth_summary,
        dict
    ):

        save_dict_csv(
            breadth_summary,
            BREADTH_OUTPUT
        )

    save_csv(
        breadth_stocks,
        BREADTH_STOCK_OUTPUT
    )

    # ========================================================
    # STEP 3
    # MARKET REGIME
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

        save_dict_csv(
            market_regime,
            MARKET_OUTPUT
        )

        print(
            "Market regime:",
            market_regime.get(
                "regime",
                "N/A"
            )
        )

    # ========================================================
    # STEP 4
    # SECTOR STRENGTH
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
        f"{len(sector_data):,}"
    )

    # ========================================================
    # STEP 5
    # FULL TECHNICAL SCAN
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

    if technical_history.empty:

        raise RuntimeError(
            "Technical scan returned no data."
        )

    technical = (
        create_latest_snapshot(
            technical_history
        )
    )

    technical = normalize_symbol_column(
        technical
    )

    if technical.empty:

        raise RuntimeError(
            "Technical snapshot "
            "returned no stocks."
        )

    print(
        f"Technical stocks analyzed: "
        f"{len(technical):,}"
    )

    save_csv(
        technical,
        TECHNICAL_OUTPUT
    )

    # ========================================================
    # STEP 6
    # NSE MASTER DATA
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
    # STEP 7
    # SECTOR MAPPING
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 7 — STOCK SECTOR MAPPING")
    print("=" * 70)

    sector_mapping = load_mapping()

    print(
        f"Sector mapping rows: "
        f"{len(sector_mapping):,}"
    )

    technical = enrich_with_sector(
        technical,
        sector_mapping
    )

    if "sector" in technical.columns:

        mapped_count = (
            technical[
                "sector"
            ]
            .notna()
            .sum()
        )

        print(
            f"Technical stocks with "
            f"sector mapping: "
            f"{mapped_count:,}"
        )

    # ========================================================
    # STEP 8
    # PRELIMINARY RANKING
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 8 — PRELIMINARY RANKING")
    print("=" * 70)

    preliminary = run_ranking(
        technical=technical,
        fundamentals=pd.DataFrame(),
        sector_data=sector_data,
        market_regime=market_regime
    )

    if preliminary.empty:

        print(
            "Preliminary ranking unavailable. "
            "Using technical dataset."
        )

        preliminary = (
            technical.copy()
        )

    # ========================================================
    # STEP 9
    # FUNDAMENTAL SHORTLIST
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
        f"Stocks selected for fundamentals: "
        f"{len(fundamental_symbols):,}"
    )

    # ========================================================
    # STEP 10
    # FUNDAMENTAL ANALYSIS
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 10 — FUNDAMENTAL ANALYSIS")
    print("=" * 70)

    fundamentals = (
        run_fundamentals(
            fundamental_symbols
        )
    )

    save_csv(
        fundamentals,
        FUNDAMENTAL_OUTPUT
    )

    # --------------------------------------------------------
    # Workflow requires fundamentals.csv.
    # Create empty CSV when fundamentals are unavailable.
    # --------------------------------------------------------

    if not FUNDAMENTAL_OUTPUT.exists():

        pd.DataFrame(
            columns=[
                "symbol",
                "fundamental_status"
            ]
        ).to_csv(
            FUNDAMENTAL_OUTPUT,
            index=False
        )

    print(
        f"Fundamental records: "
        f"{len(fundamentals):,}"
    )

    # ========================================================
    # STEP 11
    # FINAL RANKING
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 11 — FINAL STOCK RANKING")
    print("=" * 70)

    ranked = run_ranking(
        technical=technical,
        fundamentals=fundamentals,
        sector_data=sector_data,
        market_regime=market_regime
    )

    if ranked.empty:

        print(
            "Final ranking unavailable. "
            "Using preliminary ranking."
        )

        ranked = (
            preliminary.copy()
        )

    ranked = normalize_symbol_column(
        ranked
    )

    if ranked.empty:

        raise RuntimeError(
            "Final stock ranking "
            "returned no stocks."
        )

    print(
        f"Final ranked stocks: "
        f"{len(ranked):,}"
    )

    save_csv(
        ranked,
        STOCK_OUTPUT
    )

    # ========================================================
    # STEP 12
    # SMART WATCHLISTS
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 12 — SMART WATCHLISTS")
    print("=" * 70)

    watchlists = run_watchlists(
        ranked,
        market_regime
    )

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

        else:

            watchlists[
                name
            ] = clean_dataframe(
                watchlists[
                    name
                ]
            )

    # ========================================================
    # STEP 13
    # WATCHLIST EXPORTS
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 13 — CSV AND EXCEL EXPORTS")
    print("=" * 70)

    export_watchlists(
        watchlists
    )

    # ========================================================
    # STEP 14
    # SETUP SUMMARY
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
    # STEP 15
    # DASHBOARD JSON
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 15 — DASHBOARD JSON")
    print("=" * 70)

    create_dashboard_json(
        market_regime=market_regime,
        breadth=breadth_summary,
        sector_data=sector_data,
        ranked=ranked,
        watchlists=watchlists
    )

    # ========================================================
    # STEP 16
    # FINAL VALIDATION
    # ========================================================

    print()
    print("=" * 70)
    print("STEP 16 — FINAL VALIDATION")
    print("=" * 70)

    required_outputs = [
        DASHBOARD_OUTPUT,
        STOCK_OUTPUT,
        MARKET_OUTPUT,
        BREADTH_OUTPUT,
        SECTOR_OUTPUT,
        TECHNICAL_OUTPUT,
        FUNDAMENTAL_OUTPUT,
        SETUP_OUTPUT
    ]

    missing = [
        str(path)
        for path in required_outputs
        if not path.exists()
    ]

    if missing:

        raise RuntimeError(
            "Missing required output files: "
            + ", ".join(
                missing
            )
        )

    # ========================================================
    # FINISH
    # ========================================================

    elapsed = (
        time.time()
        -
        start_time
    )

    print_final_summary(
        universe=universe,
        technical=technical,
        ranked=ranked,
        market_regime=market_regime,
        watchlists=watchlists
    )

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
        print("=" * 80)

        raise

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

from engines.nse_universe import (
    get_nse_universe,
    save_universe
)

from engines.technical_engine import (
    calculate_technical_indicators
)

from engines.market_breadth import (
    get_market_breadth
)

from engines.market_engine import (
    get_market_regime
)

from engines.sector_engine import (
    get_sector_analysis
)

from engines.ranking_engine import (
    rank_stocks,
    create_watchlists,
    create_setup_summary
)

from engines.fundamental_engine import (
    get_fundamentals
)


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
# GENERIC HELPERS
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

    if isinstance(value, bool):
        return value

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):

        if not np.isfinite(value):
            return None

        return float(value)

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return value

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    if isinstance(
        value,
        pd.Timestamp
    ):

        return value.isoformat()

    return value


def clean_dataframe_for_json(df):

    if (
        df is None or
        df.empty
    ):
        return []

    records = []

    for record in df.to_dict(
        orient="records"
    ):

        cleaned = {
            str(key):
            clean_value(value)
            for key, value
            in record.items()
        }

        records.append(
            cleaned
        )

    return records


def save_csv(
    df,
    filename
):

    if df is None:
        return

    if df.empty:

        print(
            f"Skipping empty output: "
            f"{filename}"
        )

        return

    path = (
        OUTPUT_DIR /
        filename
    )

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

    if (
        raw_data is None or
        raw_data.empty
    ):
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

            level0 = (
                data.columns
                .get_level_values(0)
            )

            level1 = (
                data.columns
                .get_level_values(1)
            )

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

            elif len(
                set(level0)
            ) == 1:

                data.columns = level1

            elif len(
                set(level1)
            ) == 1:

                data.columns = level0

            else:

                return None

        data.columns = [
            str(column).strip()
            for column
            in data.columns
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
# TECHNICAL SCANNER
# ============================================================

def scan_technical_data(
    universe
):

    if (
        universe is None or
        universe.empty
    ):
        return pd.DataFrame()

    universe = universe.copy()

    if "YAHOO_SYMBOL" not in universe.columns:

        if "SYMBOL" not in universe.columns:

            raise RuntimeError(
                "NSE universe does not contain SYMBOL."
            )

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
        "FULL NSE TECHNICAL SCAN"
    )

    print(
        f"Yahoo symbols: "
        f"{len(yahoo_symbols)}"
    )

    print(
        "=" * 70
    )

    results = []

    total_batches = math.ceil(
        len(yahoo_symbols) /
        BATCH_SIZE
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
            f"{batch_number}/"
            f"{total_batches}"
        )

        try:

            raw_data = yf.download(
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
                f"Batch download failed: "
                f"{error}"
            )

            continue

        for yahoo_symbol in batch:

            data = extract_symbol_data(
                raw_data,
                yahoo_symbol
            )

            if (
                data is None or
                len(data) < 200
            ):
                continue

            try:

                technical = (
                    calculate_technical_indicators(
                        data
                    )
                )

                if (
                    technical is None or
                    technical.empty
                ):
                    continue

                latest = (
                    technical.iloc[-1]
                )

                if pd.isna(
                    latest.get(
                        "SMA200"
                    )
                ):
                    continue

                symbol = (
                    yahoo_symbol
                    .replace(
                        ".NS",
                        ""
                    )
                    .upper()
                )

                record = {
                    "symbol":
                        symbol,

                    "yahoo_symbol":
                        yahoo_symbol,

                    "date":
                        technical.index[-1]
                }

                for column in (
                    technical.columns
                ):

                    record[column] = (
                        latest[column]
                    )

                results.append(
                    record
                )

            except Exception as error:

                print(
                    f"Technical calculation failed "
                    f"for {yahoo_symbol}: "
                    f"{error}"
                )

        print(
            f"Stocks successfully analysed so far: "
            f"{len(results)}"
        )

    if not results:

        return pd.DataFrame()

    result = pd.DataFrame(
        results
    )

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
    # Add NSE master fields
    # --------------------------------------------------------

    if "SYMBOL" in universe.columns:

        master = universe.copy()

        master["SYMBOL"] = (
            master["SYMBOL"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        master = master.rename(
            columns={
                "SYMBOL":
                    "nse_symbol"
            }
        )

        preferred = [
            "nse_symbol",
            "COMPANY_NAME",
            "NAME OF COMPANY",
            "ISIN NUMBER",
            "SERIES",
            " SERIES"
        ]

        available = [
            column
            for column in preferred
            if column in master.columns
        ]

        master = (
            master[
                available
            ]
            .drop_duplicates(
                subset=[
                    "nse_symbol"
                ]
            )
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

    selected = []

    def add_symbols(frame):

        if (
            frame is None or
            frame.empty or
            "symbol" not in frame.columns
        ):
            return

        selected.extend(
            frame[
                "symbol"
            ]
            .dropna()
            .astype(str)
            .str.upper()
            .str.replace(
                ".NS",
                "",
                regex=False
            )
            .tolist()
        )

    # --------------------------------------------------------
    # 1. Top technical stocks
    # --------------------------------------------------------

    if "technical_score" in data.columns:

        top_technical = (
            data
            .sort_values(
                "technical_score",
                ascending=False
            )
            .head(300)
        )

        add_symbols(
            top_technical
        )

    # --------------------------------------------------------
    # 2. Near 52W high
    # --------------------------------------------------------

    if (
        "Distance_From_52W_High_Pct"
        in data.columns
    ):

        near_high = (
            data[
                data[
                    "Distance_From_52W_High_Pct"
                ] >= -10
            ]
            .sort_values(
                "Distance_From_52W_High_Pct",
                ascending=False
            )
            .head(150)
        )

        add_symbols(
            near_high
        )

    # --------------------------------------------------------
    # 3. Around 200 DMA
    # --------------------------------------------------------

    if (
        "Distance_From_200DMA_Pct"
        in data.columns
    ):

        near_dma = (
            data[
                data[
                    "Distance_From_200DMA_Pct"
                ].between(
                    -7,
                    7
                )
            ]
            .sort_values(
                "Distance_From_200DMA_Pct"
            )
            .head(150)
        )

        add_symbols(
            near_dma
        )

    # --------------------------------------------------------
    # 4. Positive momentum
    # --------------------------------------------------------

    if "Momentum" in data.columns:

        positive_momentum = (
            data[
                data[
                    "Momentum"
                ]
                .astype(str)
                .str.lower()
                .isin(
                    [
                        "positive",
                        "strong positive"
                    ]
                )
            ]
            .sort_values(
                "technical_score",
                ascending=False
            )
            .head(150)
        )

        add_symbols(
            positive_momentum
        )

    # --------------------------------------------------------
    # Unique symbols
    # --------------------------------------------------------

    selected = list(
        dict.fromkeys(
            selected
        )
    )

    # Limit first-pass Yahoo fundamentals
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
# SECTOR MAPPING
# ============================================================

def load_sector_mapping():

    mapping_file = Path(
        "data/sector_mapping.csv"
    )

    if not mapping_file.exists():

        print(
            "Sector mapping file not found."
        )

        return pd.DataFrame()

    try:

        mapping = pd.read_csv(
            mapping_file
        )

        if mapping.empty:
            return mapping

        mapping.columns = [
            str(column).strip()
            for column
            in mapping.columns
        ]

        if "symbol" not in mapping.columns:
            return pd.DataFrame()

        mapping["symbol"] = (
            mapping["symbol"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        return mapping

    except Exception as error:

        print(
            f"Unable to load sector mapping: "
            f"{error}"
        )

        return pd.DataFrame()


# ============================================================
# ENRICH STOCKS WITH PRIMARY SECTOR
# ============================================================

def apply_sector_mapping(
    stock_data,
    sector_mapping
):

    if (
        stock_data is None or
        stock_data.empty
    ):
        return stock_data

    if (
        sector_mapping is None or
        sector_mapping.empty
    ):
        return stock_data

    if "symbol" not in sector_mapping.columns:
        return stock_data

    data = stock_data.copy()
    mapping = sector_mapping.copy()

    # --------------------------------------------------------
    # Prefer primary sector
    # --------------------------------------------------------

    if "primary_sector" in mapping.columns:

        primary = (
            mapping[
                [
                    "symbol",
                    "primary_sector"
                ]
            ]
            .drop_duplicates(
                subset=[
                    "symbol"
                ]
            )
        )

        data = data.merge(
            primary,
            on="symbol",
            how="left"
        )

    # --------------------------------------------------------
    # Fallback to sector
    # --------------------------------------------------------

    elif "sector" in mapping.columns:

        primary = (
            mapping[
                [
                    "symbol",
                    "sector"
                ]
            ]
            .drop_duplicates(
                subset=[
                    "symbol"
                ]
            )
            .rename(
                columns={
                    "sector":
                        "primary_sector"
                }
            )
        )

        data = data.merge(
            primary,
            on="symbol",
            how="left"
        )

    return data


# ============================================================
# MARKET REGIME NORMALIZATION
# ============================================================

def normalize_market_regime(
    market
):

    if market is None:
        return "Unknown"

    if isinstance(
        market,
        dict
    ):

        return (
            market.get(
                "regime"
            )
            or
            market.get(
                "market_regime"
            )
            or
            "Unknown"
        )

    return str(
        market
    )


# ============================================================
# FINAL DATA PREPARATION
# ============================================================

def prepare_final_data(
    technical_data,
    fundamentals,
    sector_data,
    sector_mapping,
    market
):

    data = technical_data.copy()

    # --------------------------------------------------------
    # Add sector mapping BEFORE ranking
    # --------------------------------------------------------

    data = apply_sector_mapping(
        data,
        sector_mapping
    )

    # --------------------------------------------------------
    # Yahoo sector can still be used if fundamental
    # information is available.
    # --------------------------------------------------------

    if (
        fundamentals is not None and
        not fundamentals.empty and
        "symbol" in fundamentals.columns
    ):

        fund = fundamentals.copy()

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

        # Only bring company/fundamental fields
        # not already present.
        additional_columns = [
            column
            for column in fund.columns
            if (
                column != "symbol" and
                column not in data.columns
            )
        ]

        if additional_columns:

            data = data.merge(
                fund[
                    [
                        "symbol"
                    ] +
                    additional_columns
                ],
                on="symbol",
                how="left"
            )

    # --------------------------------------------------------
    # Ranking
    # --------------------------------------------------------

    ranked = rank_stocks(
        data,
        fundamental_data=None,
        sector_data=sector_data,
        market_regime=market
    )

    return ranked


# ============================================================
# EXCEL EXPORT
# ============================================================

def export_excel_files(
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
                f"All-stocks Excel export failed: "
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

        try:

            path = (
                EXPORT_DIR /
                f"{name}.xlsx"
            )

            data.to_excel(
                path,
                index=False
            )

            print(
                f"Saved: {path}"
            )

        except Exception as error:

            print(
                f"{name} Excel export failed: "
                f"{error}"
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
        f"Saved: {path}"
    )


# ============================================================
# CLEAN OLD GENERATED OUTPUTS
# ============================================================

def clean_old_exports():

    # We intentionally do not delete the fundamental cache.
    # It is valuable for reducing repeated Yahoo requests.

    for file in EXPORT_DIR.glob(
        "*.xlsx"
    ):

        try:

            file.unlink()

        except Exception:
            pass


# ============================================================
# MAIN PRODUCTION PIPELINE
# ============================================================

def main():

    print()
    print(
        "=" * 80
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
        "=" * 80
    )

    # ========================================================
    # STEP 1 — NSE UNIVERSE
    # ========================================================

    print()
    print(
        "STEP 1/10 — NSE EQUITY UNIVERSE"
    )

    universe = get_nse_universe()

    if (
        universe is None or
        universe.empty
    ):

        raise RuntimeError(
            "NSE equity universe could not be loaded."
        )

    save_universe(
        universe
    )

    # ========================================================
    # STEP 2 — MARKET BREADTH
    # ========================================================

    print()
    print(
        "STEP 2/10 — MARKET BREADTH"
    )

    breadth = get_market_breadth(
        universe
    )

    if breadth is None:
        breadth = {}

    # ========================================================
    # STEP 3 — MARKET REGIME
    # ========================================================

    print()
    print(
        "STEP 3/10 — MARKET REGIME"
    )

    market = get_market_regime(
        breadth=breadth
    )

    if market is None:
        market = {}

    market_regime = (
        normalize_market_regime(
            market
        )
    )

    print(
        f"Market regime: "
        f"{market_regime}"
    )

    # ========================================================
    # STEP 4 — SECTOR ANALYSIS
    # ========================================================

    print()
    print(
        "STEP 4/10 — SECTOR ANALYSIS"
    )

    sector_data = (
        get_sector_analysis()
    )

    if sector_data is None:
        sector_data = pd.DataFrame()

    # ========================================================
    # STEP 5 — SECTOR MAPPING
    # ========================================================

    print()
    print(
        "STEP 5/10 — STOCK SECTOR MAPPING"
    )

    sector_mapping = (
        load_sector_mapping()
    )

    if not sector_mapping.empty:

        print(
            f"Sector mapping records: "
            f"{len(sector_mapping)}"
        )

        print(
            f"Mapped stocks: "
            f"{sector_mapping['symbol'].nunique()}"
        )

    else:

        print(
            "Sector mapping unavailable; "
            "ranking will continue without it."
        )

    # ========================================================
    # STEP 6 — TECHNICAL SCAN
    # ========================================================

    print()
    print(
        "STEP 6/10 — FULL TECHNICAL SCAN"
    )

    technical_data = (
        scan_technical_data(
            universe
        )
    )

    if technical_data.empty:

        raise RuntimeError(
            "Technical scan returned no stocks."
        )

    # Save complete technical scan
    save_csv(
        technical_data,
        "technical_scan.csv"
    )

    # ========================================================
    # STEP 7 — FUNDAMENTAL SHORTLIST
    # ========================================================

    print()
    print(
        "STEP 7/10 — FUNDAMENTAL ANALYSIS"
    )

    # Initial technical ranking is used only
    # to create an efficient fundamental shortlist.
    preliminary = rank_stocks(
        technical_data,
        fundamental_data=None,
        sector_data=sector_data,
        market_regime=market
    )

    fundamental_symbols = (
        create_fundamental_shortlist(
            preliminary
        )
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
    # STEP 8 — FINAL RANKING
    # ========================================================

    print()
    print(
        "STEP 8/10 — FINAL STOCK RANKING"
    )

    ranked = prepare_final_data(
        technical_data,
        fundamentals,
        sector_data,
        sector_mapping,
        market
    )

    if ranked.empty:

        raise RuntimeError(
            "Final stock ranking returned no data."
        )

    save_csv(
        ranked,
        "stocks.csv"
    )

    # ========================================================
    # STEP 9 — WATCHLISTS
    # ========================================================

    print()
    print(
        "STEP 9/10 — SMART WATCHLISTS"
    )

    watchlists = create_watchlists(
        ranked,
        market_regime=market
    )

    for name, data in (
        watchlists.items()
    ):

        save_csv(
            data,
            f"{name}.csv"
        )

    # --------------------------------------------------------
    # Setup summary
    # --------------------------------------------------------

    setup_summary = (
        create_setup_summary(
            ranked
        )
    )

    save_csv(
        setup_summary,
        "setup_summary.csv"
    )

    # --------------------------------------------------------
    # Market regime
    # --------------------------------------------------------

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
    # STEP 10 — DASHBOARD + EXCEL
    # ========================================================

    print()
    print(
        "STEP 10/10 — DASHBOARD OUTPUT"
    )

    clean_old_exports()

    export_excel_files(
        ranked,
        watchlists
    )

    create_dashboard_json(
        market,
        breadth,
        sector_data,
        ranked,
        watchlists
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print(
        "=" * 80
    )

    print(
        "PRODUCTION SCAN COMPLETED"
    )

    print(
        "=" * 80
    )

    print()

    print(
        f"NSE universe: "
        f"{len(universe)}"
    )

    print(
        f"Technical stocks: "
        f"{len(technical_data)}"
    )

    print(
        f"Fundamental stocks: "
        f"{len(fundamentals) if fundamentals is not None else 0}"
    )

    print(
        f"Final ranked stocks: "
        f"{len(ranked)}"
    )

    print(
        f"Market regime: "
        f"{market_regime}"
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
        f"Excel directory: "
        f"{EXPORT_DIR}"
    )

    print()
    print(
        "=" * 80
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()

# ============================================================
# NSE SMART MARKET DASHBOARD V2
# SECTOR MAPPING ENGINE
# Created by Rakesh Nagapuri
# ============================================================

import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

NSE_HOME_URL = "https://www.nseindia.com/"

NSE_INDEX_URL = (
    "https://www.nseindia.com/api/equity-stockIndices"
)

OUTPUT_FILE = Path(
    "data/sector_mapping.csv"
)

REQUEST_TIMEOUT = 30


# ============================================================
# SECTOR / INDEX DEFINITIONS
# ============================================================

SECTOR_INDICES = {

    "NIFTY AUTO":
        "NIFTY AUTO",

    "NIFTY BANK":
        "NIFTY BANK",

    "NIFTY FINANCIAL SERVICES":
        "NIFTY FINANCIAL SERVICES",

    "NIFTY FMCG":
        "NIFTY FMCG",

    "NIFTY IT":
        "NIFTY IT",

    "NIFTY MEDIA":
        "NIFTY MEDIA",

    "NIFTY METAL":
        "NIFTY METAL",

    "NIFTY PHARMA":
        "NIFTY PHARMA",

    "NIFTY PSU BANK":
        "NIFTY PSU BANK",

    "NIFTY REALTY":
        "NIFTY REALTY",

    "NIFTY INFRASTRUCTURE":
        "NIFTY INFRASTRUCTURE",

    "NIFTY PSE":
        "NIFTY PSE",

    "NIFTY CONSUMPTION":
        "NIFTY CONSUMPTION",

    "NIFTY MNC":
        "NIFTY MNC",

    "NIFTY SERVICES SECTOR":
        "NIFTY SERVICES SECTOR",

    "NIFTY ENERGY":
        "NIFTY ENERGY"
}


# ============================================================
# HTTP SESSION
# ============================================================

def get_nse_headers():

    return {

        "User-Agent":
            (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            ),

        "Accept":
            "application/json,text/plain,*/*",

        "Accept-Language":
            "en-US,en;q=0.9",

        "Referer":
            NSE_HOME_URL,

        "Connection":
            "keep-alive"
    }


def create_nse_session():

    session = requests.Session()

    session.headers.update(
        get_nse_headers()
    )

    try:

        session.get(
            NSE_HOME_URL,
            timeout=REQUEST_TIMEOUT
        )

    except Exception as error:

        print(
            f"NSE homepage request warning: {error}"
        )

    return session


# ============================================================
# NSE INDEX REQUEST
# ============================================================

def download_sector_index(
    session,
    index_name
):

    try:

        response = session.get(
            NSE_INDEX_URL,
            params={
                "index": index_name
            },
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        payload = response.json()

        if not isinstance(
            payload,
            dict
        ):
            return pd.DataFrame()

        records = payload.get(
            "data",
            []
        )

        if not records:
            return pd.DataFrame()

        return pd.DataFrame(
            records
        )

    except Exception as error:

        print(
            f"Unable to download "
            f"{index_name}: {error}"
        )

        return pd.DataFrame()


# ============================================================
# CLEAN INDEX DATA
# ============================================================

def clean_sector_data(
    data,
    sector_name
):

    if data is None or data.empty:
        return pd.DataFrame()

    df = data.copy()

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # --------------------------------------------------------
    # Find symbol field
    # --------------------------------------------------------

    symbol_column = None

    for column in [
        "symbol",
        "Symbol",
        "SYMBOL"
    ]:

        if column in df.columns:

            symbol_column = column
            break

    if symbol_column is None:

        return pd.DataFrame()

    df["symbol"] = (
        df[symbol_column]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Remove index itself
    # --------------------------------------------------------

    index_mask = (
        df["symbol"]
        .str.contains(
            "NIFTY",
            case=False,
            na=False
        )
    )

    df = df[
        ~index_mask
    ].copy()

    # --------------------------------------------------------
    # Remove invalid symbols
    # --------------------------------------------------------

    invalid_symbols = [
        "",
        "NAN",
        "NONE",
        "NULL"
    ]

    df = df[
        ~df["symbol"].isin(
            invalid_symbols
        )
    ].copy()

    # --------------------------------------------------------
    # Add Yahoo symbol
    # --------------------------------------------------------

    df["yahoo_symbol"] = (
        df["symbol"] +
        ".NS"
    )

    # --------------------------------------------------------
    # Sector metadata
    # --------------------------------------------------------

    df["sector"] = sector_name

    df["sector_type"] = "NSE Sector / Theme"

    # --------------------------------------------------------
    # Keep useful NSE fields where available
    # --------------------------------------------------------

    preferred_columns = [
        "symbol",
        "yahoo_symbol",
        "sector",
        "sector_type",
        "identifier",
        "series",
        "lastPrice",
        "pChange",
        "totalTradedVolume",
        "totalTradedValue"
    ]

    available_columns = [
        column
        for column in preferred_columns
        if column in df.columns
    ]

    return df[
        available_columns
    ].copy()


# ============================================================
# BUILD COMPLETE SECTOR MAPPING
# ============================================================

def build_sector_mapping():

    print()
    print(
        "=" * 70
    )

    print(
        "NSE SECTOR MAPPING"
    )

    print(
        "=" * 70
    )

    session = create_nse_session()

    all_data = []

    for sector_name, index_name in (
        SECTOR_INDICES.items()
    ):

        print(
            f"Downloading: {sector_name}"
        )

        data = download_sector_index(
            session,
            index_name
        )

        cleaned = clean_sector_data(
            data,
            sector_name
        )

        if not cleaned.empty:

            print(
                f"  Stocks found: "
                f"{len(cleaned)}"
            )

            all_data.append(
                cleaned
            )

        else:

            print(
                "  No constituents returned."
            )

        # Be polite to NSE API
        time.sleep(0.5)

    if not all_data:

        print()
        print(
            "No sector mappings were retrieved."
        )

        return pd.DataFrame()

    mapping = pd.concat(
        all_data,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Remove duplicates within same sector
    # --------------------------------------------------------

    mapping = mapping.drop_duplicates(
        subset=[
            "symbol",
            "sector"
        ]
    )

    # --------------------------------------------------------
    # Primary sector assignment
    #
    # A stock can belong to multiple NSE indices.
    # Keep all memberships above, then create a
    # primary sector using a deterministic priority.
    # --------------------------------------------------------

    sector_priority = [

        "NIFTY BANK",

        "NIFTY FINANCIAL SERVICES",

        "NIFTY AUTO",

        "NIFTY IT",

        "NIFTY PHARMA",

        "NIFTY METAL",

        "NIFTY ENERGY",

        "NIFTY FMCG",

        "NIFTY REALTY",

        "NIFTY MEDIA",

        "NIFTY PSU BANK",

        "NIFTY PSE",

        "NIFTY INFRASTRUCTURE",

        "NIFTY CONSUMPTION",

        "NIFTY SERVICES SECTOR",

        "NIFTY MNC"
    ]

    priority_map = {
        sector: index
        for index, sector
        in enumerate(
            sector_priority
        )
    }

    mapping["_priority"] = (
        mapping["sector"]
        .map(
            lambda value:
                priority_map.get(
                    value,
                    999
                )
        )
    )

    mapping = mapping.sort_values(
        by=[
            "symbol",
            "_priority",
            "sector"
        ],
        ascending=[
            True,
            True,
            True
        ]
    )

    # --------------------------------------------------------
    # Primary sector table
    # --------------------------------------------------------

    primary = (
        mapping
        .drop_duplicates(
            subset=[
                "symbol"
            ],
            keep="first"
        )
        [
            [
                "symbol",
                "sector"
            ]
        ]
        .rename(
            columns={
                "sector":
                    "primary_sector"
            }
        )
    )

    # --------------------------------------------------------
    # Merge primary sector back
    # --------------------------------------------------------

    mapping = mapping.merge(
        primary,
        on="symbol",
        how="left"
    )

    mapping = mapping.drop(
        columns=[
            "_priority"
        ],
        errors="ignore"
    )

    # --------------------------------------------------------
    # Final ordering
    # --------------------------------------------------------

    mapping = mapping.sort_values(
        by=[
            "primary_sector",
            "symbol"
        ]
    ).reset_index(
        drop=True
    )

    return mapping


# ============================================================
# SAVE
# ============================================================

def save_sector_mapping(
    mapping
):

    if (
        mapping is None or
        mapping.empty
    ):

        print(
            "No sector mapping available to save."
        )

        return

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    mapping.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Saved sector mapping: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Mapping records: "
        f"{len(mapping)}"
    )

    print(
        f"Unique stocks: "
        f"{mapping['symbol'].nunique()}"
    )


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def get_sector_mapping():

    mapping = build_sector_mapping()

    if mapping.empty:

        return mapping

    save_sector_mapping(
        mapping
    )

    return mapping


# ============================================================
# COMMAND LINE
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
        "SECTOR MAPPING ENGINE"
    )

    print(
        "Created by Rakesh Nagapuri"
    )

    print(
        "=" * 70
    )

    mapping = get_sector_mapping()

    if mapping.empty:

        print()
        print(
            "Sector mapping failed."
        )

        return

    print()
    print(
        "Sector mapping completed."
    )

    print()
    print(
        "Sector membership summary:"
    )

    summary = (
        mapping[
            [
                "sector"
            ]
        ]
        .value_counts()
        .rename_axis(
            "sector"
        )
        .reset_index(
            name="stocks"
        )
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()

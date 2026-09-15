# ============================================================
# NSE SMART MARKET DASHBOARD V2
# NSE STOCK SECTOR MAPPING ENGINE
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

NSE_INDEX_API = (
    "https://www.nseindia.com/api/equity-stockIndices"
)

OUTPUT_FILE = Path(
    "data/sector_mapping.csv"
)

REQUEST_TIMEOUT = 30

MAX_RETRIES = 3

RETRY_DELAY = 2


# ============================================================
# SECTOR / THEME INDEX DEFINITIONS
# ============================================================
#
# "type" indicates whether the index is a practical sector
# index or a broader/theme index.
#
# Primary sector selection prefers actual sector indices.
#
# ============================================================

SECTOR_INDICES = {

    "NIFTY AUTO": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY BANK": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY FINANCIAL SERVICES": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY FMCG": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY IT": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY MEDIA": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY METAL": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY PHARMA": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY PSU BANK": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY PRIVATE BANK": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY REALTY": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY ENERGY": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY OIL & GAS": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY HEALTHCARE INDEX": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY CONSUMER DURABLES": {
        "type": "sector",
        "priority": 10
    },

    "NIFTY INFRASTRUCTURE": {
        "type": "theme",
        "priority": 20
    },

    "NIFTY PSE": {
        "type": "theme",
        "priority": 20
    },

    "NIFTY CONSUMPTION": {
        "type": "theme",
        "priority": 20
    },

    "NIFTY MNC": {
        "type": "theme",
        "priority": 20
    },

    "NIFTY SERVICES SECTOR": {
        "type": "theme",
        "priority": 20
    }
}


# ============================================================
# NSE SESSION
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
            (
                "application/json,"
                "text/plain,*/*"
            ),

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

    return session


# ============================================================
# FETCH ONE INDEX
# ============================================================

def fetch_sector_index(
    session,
    index_name
):

    params = {
        "index": index_name
    }

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = session.get(
                NSE_INDEX_API,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            # ------------------------------------------------
            # Authentication / rate-limit response
            # ------------------------------------------------

            if response.status_code in [
                401,
                403,
                429
            ]:

                print(
                    f"  NSE returned HTTP "
                    f"{response.status_code} "
                    f"for {index_name}"
                )

                if attempt < MAX_RETRIES:

                    time.sleep(
                        RETRY_DELAY * attempt
                    )

                    continue

                return pd.DataFrame()

            response.raise_for_status()

            payload = response.json()

            records = payload.get(
                "data",
                []
            )

            if not records:

                print(
                    f"  No constituents returned "
                    f"for {index_name}"
                )

                return pd.DataFrame()

            rows = []

            for item in records:

                symbol = item.get(
                    "symbol"
                )

                if not symbol:

                    continue

                symbol = (
                    str(symbol)
                    .strip()
                    .upper()
                )

                # --------------------------------------------
                # Ignore index summary row
                # --------------------------------------------

                if symbol == index_name.upper():
                    continue

                if symbol.startswith(
                    "NIFTY"
                ):
                    continue

                rows.append({

                    "symbol":
                        symbol,

                    "yahoo_symbol":
                        f"{symbol}.NS",

                    "sector_index":
                        index_name,

                    "mapping_type":
                        SECTOR_INDICES[
                            index_name
                        ]["type"],

                    "priority":
                        SECTOR_INDICES[
                            index_name
                        ]["priority"],

                    "source":
                        "NSE"
                })

            if not rows:

                return pd.DataFrame()

            return pd.DataFrame(
                rows
            )

        except requests.RequestException as error:

            print(
                f"  Request failed for "
                f"{index_name}: "
                f"{error}"
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY * attempt
                )

        except ValueError as error:

            print(
                f"  Invalid NSE response for "
                f"{index_name}: "
                f"{error}"
            )

            return pd.DataFrame()

        except Exception as error:

            print(
                f"  Unexpected error for "
                f"{index_name}: "
                f"{error}"
            )

            return pd.DataFrame()

    return pd.DataFrame()


# ============================================================
# FETCH ALL SECTORS
# ============================================================

def download_sector_membership():

    session = create_nse_session()

    # --------------------------------------------------------
    # Warm up NSE session
    # --------------------------------------------------------

    try:

        print(
            "Connecting to NSE..."
        )

        response = session.get(
            NSE_HOME_URL,
            timeout=REQUEST_TIMEOUT
        )

        print(
            f"NSE home response: "
            f"HTTP {response.status_code}"
        )

    except Exception as error:

        print(
            f"NSE home connection failed: "
            f"{error}"
        )

    all_frames = []

    print()
    print(
        "=" * 70
    )

    print(
        "DOWNLOADING NSE SECTOR CONSTITUENTS"
    )

    print(
        "=" * 70
    )

    for index_number, index_name in enumerate(
        SECTOR_INDICES,
        start=1
    ):

        print()
        print(
            f"{index_number}/"
            f"{len(SECTOR_INDICES)} "
            f"{index_name}"
        )

        frame = fetch_sector_index(
            session,
            index_name
        )

        if (
            frame is not None
            and
            not frame.empty
        ):

            print(
                f"  Constituents: "
                f"{len(frame)}"
            )

            all_frames.append(
                frame
            )

        else:

            print(
                "  Constituents unavailable"
            )

        # ----------------------------------------------------
        # Avoid hammering NSE
        # ----------------------------------------------------

        time.sleep(
            0.5
        )

    if not all_frames:

        return pd.DataFrame()

    mapping = pd.concat(
        all_frames,
        ignore_index=True
    )

    return mapping


# ============================================================
# NORMALIZE INDEX NAME
# ============================================================

def normalize_sector_name(
    value
):

    if value is None:
        return ""

    value = (
        str(value)
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # Make sector labels easier to use in ranking/dashboard
    # --------------------------------------------------------

    replacements = {

        "NIFTY FINANCIAL SERVICES":
            "Financial Services",

        "NIFTY BANK":
            "Banking",

        "NIFTY PRIVATE BANK":
            "Private Banking",

        "NIFTY PSU BANK":
            "PSU Banking",

        "NIFTY IT":
            "Information Technology",

        "NIFTY AUTO":
            "Automobile",

        "NIFTY FMCG":
            "FMCG",

        "NIFTY PHARMA":
            "Pharmaceuticals",

        "NIFTY METAL":
            "Metals",

        "NIFTY REALTY":
            "Real Estate",

        "NIFTY MEDIA":
            "Media",

        "NIFTY ENERGY":
            "Energy",

        "NIFTY OIL & GAS":
            "Oil & Gas",

        "NIFTY HEALTHCARE INDEX":
            "Healthcare",

        "NIFTY CONSUMER DURABLES":
            "Consumer Durables",

        "NIFTY INFRASTRUCTURE":
            "Infrastructure",

        "NIFTY PSE":
            "Public Sector Enterprises",

        "NIFTY CONSUMPTION":
            "Consumption",

        "NIFTY MNC":
            "MNC",

        "NIFTY SERVICES SECTOR":
            "Services"
    }

    return replacements.get(
        value,
        value.replace(
            "NIFTY ",
            ""
        ).title()
    )


# ============================================================
# CREATE PRIMARY SECTOR
# ============================================================

def create_primary_sector(
    mapping
):

    if (
        mapping is None
        or
        mapping.empty
    ):

        return mapping

    mapping = mapping.copy()

    # --------------------------------------------------------
    # Primary sector selection:
    #
    # Actual sector indexes have priority over themes.
    # Within the same type, lower priority number wins.
    # --------------------------------------------------------

    mapping = mapping.sort_values(
        by=[
            "symbol",
            "mapping_type",
            "priority",
            "sector_index"
        ],
        ascending=[
            True,
            True,
            True,
            True
        ]
    )

    # Explicitly prioritize actual sectors
    mapping["_type_rank"] = (
        mapping[
            "mapping_type"
        ]
        .map({
            "sector": 1,
            "theme": 2
        })
        .fillna(9)
    )

    mapping = mapping.sort_values(
        by=[
            "symbol",
            "_type_rank",
            "priority"
        ],
        ascending=[
            True,
            True,
            True
        ]
    )

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
                "sector_index",
                "mapping_type"
            ]
        ]
        .rename(
            columns={
                "sector_index":
                    "primary_sector_index",
                "mapping_type":
                    "primary_sector_type"
            }
        )
    )

    # --------------------------------------------------------
    # All sector/theme memberships
    # --------------------------------------------------------

    memberships = (
        mapping
        .sort_values(
            [
                "symbol",
                "_type_rank",
                "priority"
            ]
        )
        .groupby(
            "symbol"
        )[
            "sector_index"
        ]
        .apply(
            lambda values:
                " | ".join(
                    dict.fromkeys(
                        values.tolist()
                    )
                )
        )
        .reset_index(
            name="sector_indices"
        )
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    result = primary.merge(
        memberships,
        on="symbol",
        how="left"
    )

    result["primary_sector"] = (
        result[
            "primary_sector_index"
        ]
        .apply(
            normalize_sector_name
        )
    )

    result = result[
        [
            "symbol",
            "primary_sector",
            "primary_sector_index",
            "primary_sector_type",
            "sector_indices"
        ]
    ]

    return result


# ============================================================
# BUILD FINAL MAPPING
# ============================================================

def build_sector_mapping():

    raw_mapping = (
        download_sector_membership()
    )

    if (
        raw_mapping is None
        or
        raw_mapping.empty
    ):

        print()
        print(
            "No fresh NSE sector mapping available."
        )

        return pd.DataFrame()

    # --------------------------------------------------------
    # Clean symbols
    # --------------------------------------------------------

    raw_mapping["symbol"] = (
        raw_mapping[
            "symbol"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    raw_mapping = raw_mapping[
        raw_mapping[
            "symbol"
        ].notna()
    ]

    raw_mapping = raw_mapping[
        raw_mapping[
            "symbol"
        ] != ""
    ]

    # --------------------------------------------------------
    # Remove duplicate memberships
    # --------------------------------------------------------

    raw_mapping = (
        raw_mapping
        .drop_duplicates(
            subset=[
                "symbol",
                "sector_index"
            ]
        )
    )

    # --------------------------------------------------------
    # Primary mapping
    # --------------------------------------------------------

    final_mapping = (
        create_primary_sector(
            raw_mapping
        )
    )

    if final_mapping.empty:

        return final_mapping

    # --------------------------------------------------------
    # Yahoo symbol
    # --------------------------------------------------------

    final_mapping.insert(
        1,
        "yahoo_symbol",
        final_mapping[
            "symbol"
        ].apply(
            lambda symbol:
                f"{symbol}.NS"
        )
    )

    # --------------------------------------------------------
    # Source
    # --------------------------------------------------------

    final_mapping["source"] = (
        "NSE"
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    final_mapping = (
        final_mapping
        .sort_values(
            "symbol"
        )
        .reset_index(
            drop=True
        )
    )

    return final_mapping


# ============================================================
# SAVE
# ============================================================

def save_sector_mapping(
    mapping
):

    if (
        mapping is None
        or
        mapping.empty
    ):

        print(
            "No sector mapping to save."
        )

        return False

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
        "=" * 70
    )

    print(
        "SECTOR MAPPING SAVED"
    )

    print(
        "=" * 70
    )

    print(
        f"File: {OUTPUT_FILE}"
    )

    print(
        f"Stocks mapped: "
        f"{mapping['symbol'].nunique()}"
    )

    print(
        f"Rows: "
        f"{len(mapping)}"
    )

    print()

    return True


# ============================================================
# LOAD EXISTING MAPPING
# ============================================================

def load_sector_mapping():

    if not OUTPUT_FILE.exists():

        return pd.DataFrame()

    try:

        mapping = pd.read_csv(
            OUTPUT_FILE
        )

        if mapping.empty:

            return mapping

        mapping.columns = [
            str(column).strip()
            for column
            in mapping.columns
        ]

        if "symbol" in mapping.columns:

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
# MAIN
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
        "NSE STOCK SECTOR MAPPING"
    )

    print(
        "Created by Rakesh Nagapuri"
    )

    print(
        "=" * 80
    )

    mapping = (
        build_sector_mapping()
    )

    # --------------------------------------------------------
    # Important production behaviour:
    #
    # If NSE fails temporarily, keep the existing mapping
    # instead of destroying a previously working file.
    # --------------------------------------------------------

    if mapping.empty:

        existing = (
            load_sector_mapping()
        )

        if not existing.empty:

            print()
            print(
                "Fresh NSE mapping unavailable."
            )

            print(
                "Keeping existing sector mapping."
            )

            print(
                f"Existing stocks mapped: "
                f"{existing['symbol'].nunique()}"
            )

            return

        print()
        print(
            "No sector mapping available."
        )

        return

    save_sector_mapping(
        mapping
    )

    # --------------------------------------------------------
    # Sample
    # --------------------------------------------------------

    print()
    print(
        "Sample:"
    )

    print(
        mapping.head(
            15
        ).to_string(
            index=False
        )
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

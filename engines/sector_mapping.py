import pandas as pd
import requests
from io import StringIO
from pathlib import Path


# ============================================================
# NSE SMART MARKET DASHBOARD
# SECTOR MAPPING ENGINE — V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

OUTPUT_FILE = DATA_DIR / "sector_mapping.csv"


# ============================================================
# NSE INDEX CONSTITUENT URLS
# ============================================================

NSE_INDEX_URL = (
    "https://www.nseindia.com/api/equity-stockIndices"
)


# ============================================================
# NSE HEADERS
# ============================================================

def get_nse_headers():

    return {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }


# ============================================================
# DOWNLOAD NSE INDEX CONSTITUENTS
# ============================================================

def download_index_constituents(index_name):

    headers = get_nse_headers()

    session = requests.Session()

    try:

        # Establish NSE session
        session.get(
            "https://www.nseindia.com/",
            headers=headers,
            timeout=20
        )

        response = session.get(
            NSE_INDEX_URL,
            params={
                "index": index_name
            },
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        records = data.get(
            "data",
            []
        )

        if not records:

            return pd.DataFrame()

        return pd.DataFrame(records)

    except Exception as e:

        print(
            f"Unable to download "
            f"{index_name}: {e}"
        )

        return pd.DataFrame()


# ============================================================
# CLEAN CONSTITUENTS
# ============================================================

def clean_constituents(
    df,
    sector_name,
    sector_type
):

    if df.empty:

        return pd.DataFrame()

    df = df.copy()

    # --------------------------------------------------------
    # Identify symbol column
    # --------------------------------------------------------

    if "symbol" not in df.columns:

        return pd.DataFrame()

    df["symbol"] = (
        df["symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df = df[
        df["symbol"].notna()
        & (df["symbol"] != "")
        & (df["symbol"] != "NAN")
    ]

    # --------------------------------------------------------
    # Remove index summary rows
    # --------------------------------------------------------

    if "identifier" in df.columns:

        df["identifier"] = (
            df["identifier"]
            .astype(str)
            .str.strip()
        )

        df = df[
            ~df["identifier"]
            .str.contains(
                "index",
                case=False,
                na=False
            )
        ]

    # --------------------------------------------------------
    # Build mapping
    # --------------------------------------------------------

    result = pd.DataFrame({

        "symbol": df["symbol"],

        "yahoo_symbol":
            df["symbol"].apply(
                lambda x: f"{x}.NS"
            ),

        "sector": sector_name,

        "type": sector_type
    })

    return result


# ============================================================
# SECTOR INDEX LIST
# ============================================================

SECTOR_INDEXES = {

    # --------------------------------------------------------
    # Sectoral
    # --------------------------------------------------------

    "NIFTY AUTO": "Sector",

    "NIFTY BANK": "Sector",

    "NIFTY FINANCIAL SERVICES": "Sector",

    "NIFTY FMCG": "Sector",

    "NIFTY IT": "Sector",

    "NIFTY MEDIA": "Sector",

    "NIFTY METAL": "Sector",

    "NIFTY PHARMA": "Sector",

    "NIFTY PSU BANK": "Sector",

    "NIFTY REALTY": "Sector",

    # --------------------------------------------------------
    # Thematic
    # --------------------------------------------------------

    "NIFTY INFRASTRUCTURE": "Theme",

    "NIFTY PSE": "Theme",

    "NIFTY CONSUMPTION": "Theme",

    "NIFTY MNC": "Theme",

    "NIFTY SERVICES SECTOR": "Theme"
}


# ============================================================
# BUILD MAPPING
# ============================================================

def build_sector_mapping():

    all_mappings = []

    print()

    print("=" * 60)

    print("NSE SECTOR MAPPING")

    print("=" * 60)

    total = len(
        SECTOR_INDEXES
    )

    for number, (
        sector,
        sector_type
    ) in enumerate(
        SECTOR_INDEXES.items(),
        start=1
    ):

        print()

        print(
            f"[{number}/{total}] "
            f"Downloading {sector}..."
        )

        constituents = (
            download_index_constituents(
                sector
            )
        )

        if constituents.empty:

            print(
                f"No constituents found "
                f"for {sector}"
            )

            continue

        cleaned = clean_constituents(
            constituents,
            sector,
            sector_type
        )

        if cleaned.empty:

            print(
                f"No valid stocks found "
                f"for {sector}"
            )

            continue

        all_mappings.append(
            cleaned
        )

        print(
            f"Stocks found: "
            f"{len(cleaned)}"
        )

    if not all_mappings:

        return pd.DataFrame()

    mapping = pd.concat(
        all_mappings,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Remove duplicate sector memberships
    # --------------------------------------------------------

    mapping = mapping.drop_duplicates(
        subset=[
            "symbol",
            "sector"
        ]
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    mapping = mapping.sort_values(
        [
            "sector",
            "symbol"
        ]
    ).reset_index(
        drop=True
    )

    return mapping


# ============================================================
# SAVE
# ============================================================

def save_sector_mapping(mapping):

    if (
        mapping is None
        or mapping.empty
    ):

        print(
            "No sector mapping "
            "available to save."
        )

        return

    DATA_DIR.mkdir(
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
        f"Total mappings: "
        f"{len(mapping)}"
    )

    print(
        f"Unique stocks: "
        f"{mapping['symbol'].nunique()}"
    )


# ============================================================
# DISPLAY SUMMARY
# ============================================================

def display_mapping_summary(
    mapping
):

    if (
        mapping is None
        or mapping.empty
    ):

        return

    print()

    print("=" * 60)

    print("SECTOR MAPPING SUMMARY")

    print("=" * 60)

    print()

    summary = (
        mapping
        .groupby(
            ["type", "sector"]
        )
        .agg(
            stocks=(
                "symbol",
                "nunique"
            )
        )
        .reset_index()
        .sort_values(
            "stocks",
            ascending=False
        )
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print()

    print(
        f"Unique NSE stocks mapped: "
        f"{mapping['symbol'].nunique()}"
    )

    print()

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def get_sector_mapping():

    mapping = build_sector_mapping()

    if mapping.empty:

        print(
            "Sector mapping could "
            "not be created."
        )

        return mapping

    save_sector_mapping(
        mapping
    )

    display_mapping_summary(
        mapping
    )

    return mapping


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    mapping = get_sector_mapping()

    if not mapping.empty:

        print()

        print(
            "Sector mapping test "
            "completed successfully."
        )

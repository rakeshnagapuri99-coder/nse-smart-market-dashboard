import pandas as pd
import requests
from io import StringIO
from pathlib import Path


# ============================================================
# NSE SMART MARKET DASHBOARD
# NSE STOCK UNIVERSE
# ============================================================

NSE_EQUITY_URL = (
    "https://archives.nseindia.com/content/equities/"
    "EQUITY_L.csv"
)

OUTPUT_FILE = Path("data/nse_universe.csv")


def get_nse_headers():
    """
    Headers required to access NSE data.
    """

    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
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


def download_nse_equity_list():
    """
    Download the latest NSE equity security list.
    """

    headers = get_nse_headers()

    session = requests.Session()

    try:

        # Establish NSE session first
        session.get(
            "https://www.nseindia.com/",
            headers=headers,
            timeout=20
        )

        response = session.get(
            NSE_EQUITY_URL,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        df = pd.read_csv(
            StringIO(response.text)
        )

        return df

    except Exception as e:

        print(
            f"Unable to download NSE equity list: {e}"
        )

        return pd.DataFrame()


def clean_nse_universe(df):
    """
    Clean and standardize NSE security list.
    """

    if df.empty:
        return df

    df = df.copy()

    # Remove spaces from column names
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # Standard NSE columns expected:
    # SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING,
    # PAID UP VALUE, MARKET LOT, ISIN NUMBER,
    # FACE VALUE

    if "SYMBOL" not in df.columns:
        raise ValueError(
            "NSE file does not contain SYMBOL column."
        )

    # Keep only equity series
    if " SERIES" in df.columns:

        df[" SERIES"] = (
            df[" SERIES"]
            .astype(str)
            .str.strip()
        )

        df = df[
            df[" SERIES"].isin(
                ["EQ", "BE", "BZ"]
            )
        ]

    elif "SERIES" in df.columns:

        df["SERIES"] = (
            df["SERIES"]
            .astype(str)
            .str.strip()
        )

        df = df[
            df["SERIES"].isin(
                ["EQ", "BE", "BZ"]
            )
        ]

    # Clean symbol
    df["SYMBOL"] = (
        df["SYMBOL"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Remove invalid symbols
    df = df[
        df["SYMBOL"].notna()
        & (df["SYMBOL"] != "")
        & (df["SYMBOL"] != "NAN")
    ]

    # Remove duplicate symbols
    df = df.drop_duplicates(
        subset=["SYMBOL"]
    )

    # Sort alphabetically
    df = df.sort_values(
        "SYMBOL"
    ).reset_index(drop=True)

    return df


def create_yahoo_symbol(symbol):
    """
    Convert NSE symbol to Yahoo Finance symbol.

    Example:
        RELIANCE -> RELIANCE.NS
    """

    return f"{symbol}.NS"


def add_yahoo_symbols(df):
    """
    Add Yahoo Finance ticker symbol.
    """

    if df.empty:
        return df

    df = df.copy()

    df["YAHOO_SYMBOL"] = (
        df["SYMBOL"]
        .apply(create_yahoo_symbol)
    )

    return df


def save_universe(df):
    """
    Save cleaned NSE universe to CSV.
    """

    if df.empty:
        print(
            "No NSE securities available to save."
        )
        return

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved NSE universe: {OUTPUT_FILE}"
    )

    print(
        f"Total securities: {len(df)}"
    )


def get_nse_universe():
    """
    Main function.

    Downloads, cleans and prepares
    the NSE equity universe.
    """

    print(
        "Downloading latest NSE equity universe..."
    )

    df = download_nse_equity_list()

    if df.empty:

        print(
            "NSE universe download failed."
        )

        return pd.DataFrame()

    print(
        f"Downloaded {len(df)} records."
    )

    df = clean_nse_universe(df)

    df = add_yahoo_symbols(df)

    print(
        f"Valid NSE equity securities: {len(df)}"
    )

    return df


def main():

    print("=" * 60)

    print(
        "NSE SMART MARKET DASHBOARD"
    )

    print(
        "NSE STOCK UNIVERSE"
    )

    print("=" * 60)

    print()

    df = get_nse_universe()

    if df.empty:

        print(
            "No data available."
        )

        return

    save_universe(df)

    print()

    print(
        "NSE universe created successfully."
    )

    print()

    print(
        f"Total stocks: {len(df)}"
    )

    print()

    print(
        "Sample:"
    )

    print(
        df[
            [
                "SYMBOL",
                "YAHOO_SYMBOL"
            ]
        ].head(10).to_string(
            index=False
        )
    )

    print()

    print("=" * 60)


if __name__ == "__main__":
    main()

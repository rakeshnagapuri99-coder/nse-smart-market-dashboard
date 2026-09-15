import pandas as pd
import yfinance as yf
from pathlib import Path

from engines.technical_engine import (
    calculate_technical_indicators,
    get_latest_analysis
)


# ============================================================
# NSE SMART MARKET DASHBOARD
# BATCH STOCK SCANNER
# ============================================================


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_FILE = (
    OUTPUT_DIR / "technical_scan_test.csv"
)


# ------------------------------------------------------------
# TEST STOCKS
# ------------------------------------------------------------

TEST_STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]


def download_stock_data(
    symbol,
    period="2y"
):
    """
    Download historical OHLCV data.
    """

    print(
        f"Downloading: {symbol}"
    )

    try:

        data = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if data is None or data.empty:

            print(
                f"No data: {symbol}"
            )

            return pd.DataFrame()

        # ----------------------------------------------------
        # Handle MultiIndex returned by yfinance
        # ----------------------------------------------------

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            data.columns = (
                data.columns
                .get_level_values(0)
            )

        required_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in data.columns
        ]

        if missing_columns:

            print(
                f"Missing columns for "
                f"{symbol}: {missing_columns}"
            )

            return pd.DataFrame()

        data = data[
            required_columns
        ].copy()

        data = data.dropna()

        return data

    except Exception as e:

        print(
            f"Error downloading "
            f"{symbol}: {e}"
        )

        return pd.DataFrame()


def analyze_stock(symbol):
    """
    Download and technically analyze
    one stock.
    """

    data = download_stock_data(
        symbol
    )

    if data.empty:

        return None

    technical_data = (
        calculate_technical_indicators(
            data
        )
    )

    if technical_data.empty:

        return None

    analysis = get_latest_analysis(
        technical_data
    )

    if not analysis:

        return None

    analysis["symbol"] = symbol

    return analysis


def scan_stocks(symbols):
    """
    Scan multiple stocks.
    """

    results = []

    total = len(symbols)

    print()
    print("=" * 60)

    print(
        f"Starting batch scan: "
        f"{total} stocks"
    )

    print("=" * 60)

    for number, symbol in enumerate(
        symbols,
        start=1
    ):

        print()
        print(
            f"[{number}/{total}] "
            f"{symbol}"
        )

        result = analyze_stock(
            symbol
        )

        if result is not None:

            results.append(
                result
            )

            print(
                f"✓ Analysis completed: "
                f"{symbol}"
            )

        else:

            print(
                f"✗ Analysis failed: "
                f"{symbol}"
            )

    return results


def create_dataframe(results):
    """
    Convert analysis results
    into a dataframe.
    """

    if not results:

        return pd.DataFrame()

    df = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Put symbol first
    # --------------------------------------------------------

    if "symbol" in df.columns:

        columns = [
            "symbol"
        ] + [
            column
            for column in df.columns
            if column != "symbol"
        ]

        df = df[
            columns
        ]

    # --------------------------------------------------------
    # Sort by technical strength
    # --------------------------------------------------------

    if "rsi14" in df.columns:

        df = df.sort_values(
            by="rsi14",
            ascending=False
        )

    return df.reset_index(
        drop=True
    )


def save_results(df):
    """
    Save scanner results.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Saved results to:"
    )

    print(
        OUTPUT_FILE
    )


def display_results(df):
    """
    Display important fields
    in GitHub Actions log.
    """

    if df.empty:

        print(
            "No results available."
        )

        return

    display_columns = [
        "symbol",
        "price",
        "daily_return_pct",
        "sma20",
        "sma50",
        "sma200",
        "rsi14",
        "atr_percent",
        "volume_ratio",
        "52w_high",
        "52w_low",
        "distance_from_52w_high_pct",
        "distance_from_200dma_pct",
        "above_200dma",
        "support",
        "resistance",
        "trend",
        "momentum",
        "breakout_status"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in df.columns
    ]

    print()
    print("=" * 60)
    print("BATCH SCAN RESULTS")
    print("=" * 60)

    print()

    print(
        df[
            available_columns
        ].to_string(
            index=False
        )
    )

    print()
    print("=" * 60)


def main():

    print()
    print("=" * 60)

    print(
        "NSE SMART MARKET DASHBOARD"
    )

    print(
        "BATCH STOCK SCANNER"
    )

    print("=" * 60)

    print()

    # --------------------------------------------------------
    # Scan test stocks
    # --------------------------------------------------------

    results = scan_stocks(
        TEST_STOCKS
    )

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = create_dataframe(
        results
    )

    if df.empty:

        print()
        print(
            "No stocks were successfully analyzed."
        )

        return

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    save_results(
        df
    )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    display_results(
        df
    )

    print()
    print("=" * 60)

    print(
        "BATCH SCANNER TEST COMPLETE"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()

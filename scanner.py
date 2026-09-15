import pandas as pd
import yfinance as yf
from pathlib import Path

from engines.technical_engine import (
    calculate_technical_indicators,
    get_latest_analysis
)

from engines.ranking_engine import (
    rank_stocks,
    create_setup_summary
)


# ============================================================
# NSE SMART MARKET DASHBOARD
# BATCH STOCK SCANNER + RANKING
# ============================================================


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_FILE = (
    OUTPUT_DIR / "technical_ranked_test.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR / "setup_summary_test.csv"
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
                f"{symbol}: "
                f"{missing_columns}"
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
    into dataframe.
    """

    if not results:

        return pd.DataFrame()

    df = pd.DataFrame(
        results
    )

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

    return df


def save_results(df):
    """
    Save ranked technical results.
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
        f"Saved ranked results:"
    )

    print(
        OUTPUT_FILE
    )


def save_summary(summary):
    """
    Save setup summary.
    """

    if summary.empty:

        return

    summary.to_csv(
        SUMMARY_FILE,
        index=False
    )

    print()

    print(
        "Saved setup summary:"
    )

    print(
        SUMMARY_FILE
    )


def display_rankings(df):
    """
    Display ranked stocks.
    """

    if df.empty:

        print(
            "No ranking results."
        )

        return

    display_columns = [
        "technical_rank",
        "symbol",
        "technical_score",
        "setup",
        "trend",
        "momentum",
        "rsi14",
        "volume_ratio",
        "distance_from_52w_high_pct",
        "distance_from_200dma_pct",
        "risk_reward",
        "setup_reasons"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in df.columns
    ]

    print()
    print("=" * 60)
    print("STOCK RANKINGS")
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


def display_setup_summary(summary):
    """
    Display setup counts.
    """

    if summary.empty:

        print(
            "No setup summary available."
        )

        return

    print()
    print("=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)

    print()

    print(
        summary.to_string(
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
        "RANKED STOCK SCANNER"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Scan stocks
    # --------------------------------------------------------

    results = scan_stocks(
        TEST_STOCKS
    )

    if not results:

        print()
        print(
            "No stocks were successfully analyzed."
        )

        return

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = create_dataframe(
        results
    )

    # --------------------------------------------------------
    # Apply ranking engine
    # --------------------------------------------------------

    print()
    print("=" * 60)

    print(
        "RUNNING RANKING ENGINE"
    )

    print("=" * 60)

    ranked_df = rank_stocks(
        df
    )

    # --------------------------------------------------------
    # Setup summary
    # --------------------------------------------------------

    summary = create_setup_summary(
        ranked_df
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    save_results(
        ranked_df
    )

    save_summary(
        summary
    )

    # --------------------------------------------------------
    # Display rankings
    # --------------------------------------------------------

    display_rankings(
        ranked_df
    )

    # --------------------------------------------------------
    # Display setup summary
    # --------------------------------------------------------

    display_setup_summary(
        summary
    )

    # --------------------------------------------------------
    # Complete
    # --------------------------------------------------------

    print()
    print("=" * 60)

    print(
        "RANKED SCANNER TEST COMPLETE"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()

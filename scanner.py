import pandas as pd
import yfinance as yf

from engines.technical_engine import (
    calculate_technical_indicators,
    get_latest_analysis
)


# ============================================================
# NSE SMART MARKET DASHBOARD
# STEP 6.3
# SINGLE STOCK TECHNICAL TEST
# ============================================================


TEST_SYMBOL = "RELIANCE.NS"


def download_stock_data(symbol, period="2y"):
    """
    Download historical OHLCV data for one stock.
    """

    print()
    print("=" * 60)
    print(f"Downloading data: {symbol}")
    print("=" * 60)

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
                f"No data received for {symbol}"
            )

            return pd.DataFrame()

        # ----------------------------------------------------
        # Handle yfinance MultiIndex columns
        # ----------------------------------------------------

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            data.columns = (
                data.columns
                .get_level_values(0)
            )

        # ----------------------------------------------------
        # Clean data
        # ----------------------------------------------------

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
                "Missing columns:"
            )

            print(
                missing_columns
            )

            return pd.DataFrame()

        data = data[
            required_columns
        ].copy()

        data = data.dropna()

        return data

    except Exception as e:

        print(
            f"Error downloading {symbol}: {e}"
        )

        return pd.DataFrame()


def test_single_stock(symbol):
    """
    Test complete technical analysis
    for a single stock.
    """

    data = download_stock_data(
        symbol
    )

    if data.empty:

        print(
            "Stock data unavailable."
        )

        return

    print()
    print(
        f"Historical records: {len(data)}"
    )

    # --------------------------------------------------------
    # Run Technical Engine
    # --------------------------------------------------------

    print()
    print(
        "Running Technical Engine..."
    )

    technical_data = (
        calculate_technical_indicators(
            data
        )
    )

    if technical_data.empty:

        print(
            "Technical analysis failed."
        )

        return

    # --------------------------------------------------------
    # Get Latest Analysis
    # --------------------------------------------------------

    analysis = get_latest_analysis(
        technical_data
    )

    if not analysis:

        print(
            "Unable to generate analysis."
        )

        return

    # --------------------------------------------------------
    # Display Results
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("TECHNICAL ANALYSIS")
    print("=" * 60)

    print()

    print(
        f"Stock              : {symbol}"
    )

    print(
        f"Price              : "
        f"{analysis['price']:.2f}"
    )

    print(
        f"Previous Close     : "
        f"{analysis['previous_close']:.2f}"
    )

    print(
        f"Daily Return       : "
        f"{analysis['daily_return_pct']:.2f}%"
    )

    print()

    print("MOVING AVERAGES")

    print(
        f"SMA 20             : "
        f"{analysis['sma20']:.2f}"
    )

    print(
        f"SMA 50             : "
        f"{analysis['sma50']:.2f}"
    )

    print(
        f"SMA 100            : "
        f"{analysis['sma100']:.2f}"
    )

    print(
        f"SMA 200            : "
        f"{analysis['sma200']:.2f}"
    )

    print()

    print("EXPONENTIAL MOVING AVERAGES")

    print(
        f"EMA 9              : "
        f"{analysis['ema9']:.2f}"
    )

    print(
        f"EMA 20             : "
        f"{analysis['ema20']:.2f}"
    )

    print(
        f"EMA 50             : "
        f"{analysis['ema50']:.2f}"
    )

    print()

    print("MOMENTUM")

    print(
        f"RSI 14             : "
        f"{analysis['rsi14']:.2f}"
    )

    print(
        f"Trend              : "
        f"{analysis['trend']}"
    )

    print(
        f"Momentum           : "
        f"{analysis['momentum']}"
    )

    print()

    print("VOLATILITY")

    print(
        f"ATR 14             : "
        f"{analysis['atr14']:.2f}"
    )

    print(
        f"ATR %              : "
        f"{analysis['atr_percent']:.2f}%"
    )

    print()

    print("VOLUME")

    print(
        f"Volume             : "
        f"{analysis['volume']:.0f}"
    )

    print(
        f"Average Volume     : "
        f"{analysis['average_volume_20']:.0f}"
    )

    print(
        f"Volume Ratio       : "
        f"{analysis['volume_ratio']:.2f}x"
    )

    print()

    print("52-WEEK RANGE")

    print(
        f"52W High           : "
        f"{analysis['52w_high']:.2f}"
    )

    print(
        f"52W Low            : "
        f"{analysis['52w_low']:.2f}"
    )

    print(
        f"Distance from High : "
        f"{analysis['distance_from_52w_high_pct']:.2f}%"
    )

    print(
        f"Distance from Low  : "
        f"{analysis['distance_from_52w_low_pct']:.2f}%"
    )

    print()

    print("200 DMA")

    print(
        f"Distance from 200DMA : "
        f"{analysis['distance_from_200dma_pct']:.2f}%"
    )

    print(
        f"Above 200 DMA        : "
        f"{analysis['above_200dma']}"
    )

    print()

    print("PRICE ACTION")

    print(
        f"Support            : "
        f"{analysis['support']:.2f}"
    )

    print(
        f"Resistance         : "
        f"{analysis['resistance']:.2f}"
    )

    print(
        f"Breakout Status    : "
        f"{analysis['breakout_status']}"
    )

    print()

    print("=" * 60)
    print("SINGLE STOCK TEST COMPLETE")
    print("=" * 60)


def main():

    print()
    print("=" * 60)
    print("NSE SMART MARKET DASHBOARD")
    print("TECHNICAL ENGINE TEST")
    print("=" * 60)

    test_single_stock(
        TEST_SYMBOL
    )


if __name__ == "__main__":

    main()

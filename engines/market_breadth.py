import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path


# ============================================================
# NSE SMART MARKET DASHBOARD
# MARKET BREADTH ENGINE
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"

BREADTH_FILE = (
    OUTPUT_DIR / "market_breadth.csv"
)


# ============================================================
# SETTINGS
# ============================================================

DOWNLOAD_PERIOD = "2y"

BATCH_SIZE = 100

# A stock within 1% of its 52-week high/low
# is considered to be at the extreme.
EXTREME_THRESHOLD = 1.0


# ============================================================
# DOWNLOAD DATA IN BATCHES
# ============================================================

def download_batch(symbols):

    try:

        data = yf.download(
            symbols,
            period=DOWNLOAD_PERIOD,
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True
        )

        return data

    except Exception as e:

        print(
            f"Batch download error: {e}"
        )

        return pd.DataFrame()


# ============================================================
# ANALYZE ONE STOCK
# ============================================================

def analyze_stock_data(
    stock_data,
    symbol
):

    try:

        if stock_data is None:
            return None

        if stock_data.empty:
            return None

        stock_data = stock_data.dropna(
            subset=["Close"]
        )

        # Need enough history for 200 DMA
        if len(stock_data) < 200:
            return None

        close = stock_data["Close"]

        high = stock_data["High"]

        low = stock_data["Low"]

        # ----------------------------------------------------
        # Moving averages
        # ----------------------------------------------------

        sma20 = (
            close
            .rolling(20)
            .mean()
            .iloc[-1]
        )

        sma50 = (
            close
            .rolling(50)
            .mean()
            .iloc[-1]
        )

        sma200 = (
            close
            .rolling(200)
            .mean()
            .iloc[-1]
        )

        latest_close = float(
            close.iloc[-1]
        )

        # ----------------------------------------------------
        # 52 Week High / Low
        #
        # Use previous 252 sessions.
        # Current day is excluded so that a genuine breakout
        # can be detected later.
        # ----------------------------------------------------

        previous_52w_high = (
            high
            .rolling(252)
            .max()
            .shift(1)
            .iloc[-1]
        )

        previous_52w_low = (
            low
            .rolling(252)
            .min()
            .shift(1)
            .iloc[-1]
        )

        if (
            pd.isna(previous_52w_high)
            or pd.isna(previous_52w_low)
        ):
            return None

        # ----------------------------------------------------
        # Distance from 52W High / Low
        # ----------------------------------------------------

        distance_from_high = (
            (
                latest_close
                - previous_52w_high
            )
            / previous_52w_high
        ) * 100

        distance_from_low = (
            (
                latest_close
                - previous_52w_low
            )
            / previous_52w_low
        ) * 100

        # ----------------------------------------------------
        # Moving average position
        # ----------------------------------------------------

        above_20 = (
            latest_close > sma20
        )

        above_50 = (
            latest_close > sma50
        )

        above_200 = (
            latest_close > sma200
        )

        # ----------------------------------------------------
        # 52W extremes
        #
        # High:
        # Close is at/above previous 52W high
        #
        # Low:
        # Close is within 1% of previous 52W low
        # ----------------------------------------------------

        at_52w_high = (
            latest_close
            >= previous_52w_high
        )

        at_52w_low = (
            latest_close
            <= (
                previous_52w_low
                * (
                    1
                    + EXTREME_THRESHOLD
                    / 100
                )
            )
        )

        return {

            "symbol": symbol,

            "price": latest_close,

            "sma20": sma20,

            "sma50": sma50,

            "sma200": sma200,

            "above_20dma": above_20,

            "above_50dma": above_50,

            "above_200dma": above_200,

            "52w_high": previous_52w_high,

            "52w_low": previous_52w_low,

            "distance_from_52w_high_pct": (
                round(
                    distance_from_high,
                    2
                )
            ),

            "distance_from_52w_low_pct": (
                round(
                    distance_from_low,
                    2
                )
            ),

            "at_52w_high": at_52w_high,

            "at_52w_low": at_52w_low
        }

    except Exception as e:

        print(
            f"Stock analysis error "
            f"{symbol}: {e}"
        )

        return None


# ============================================================
# ANALYZE COMPLETE UNIVERSE
# ============================================================

def analyze_universe(universe):

    if universe is None or universe.empty:

        return pd.DataFrame()

    symbols = (
        universe["YAHOO_SYMBOL"]
        .dropna()
        .astype(str)
        .tolist()
    )

    results = []

    total = len(symbols)

    print()
    print("=" * 60)

    print(
        "MARKET BREADTH SCAN"
    )

    print(
        f"Total stocks: {total}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Batch processing
    # --------------------------------------------------------

    for start in range(
        0,
        total,
        BATCH_SIZE
    ):

        batch = symbols[
            start:
            start + BATCH_SIZE
        ]

        batch_number = (
            start // BATCH_SIZE
        ) + 1

        total_batches = (
            int(
                np.ceil(
                    total
                    / BATCH_SIZE
                )
            )
        )

        print()
        print(
            f"Batch "
            f"{batch_number}/"
            f"{total_batches}"
        )

        print(
            f"Stocks: "
            f"{start + 1}-"
            f"{min(start + BATCH_SIZE, total)}"
        )

        data = download_batch(
            batch
        )

        if data is None or data.empty:

            print(
                "Batch returned no data."
            )

            continue

        # ----------------------------------------------------
        # Process batch
        # ----------------------------------------------------

        for symbol in batch:

            try:

                if (
                    isinstance(
                        data.columns,
                        pd.MultiIndex
                    )
                ):

                    if (
                        symbol
                        not in
                        data.columns.get_level_values(0)
                    ):
                        continue

                    stock_data = (
                        data[symbol]
                    )

                else:

                    stock_data = data

                result = analyze_stock_data(
                    stock_data,
                    symbol
                )

                if result is not None:

                    results.append(
                        result
                    )

            except Exception as e:

                print(
                    f"Error processing "
                    f"{symbol}: {e}"
                )

    if not results:

        return pd.DataFrame()

    return pd.DataFrame(
        results
    )


# ============================================================
# CALCULATE MARKET BREADTH
# ============================================================

def calculate_market_breadth(
    stock_analysis
):

    if (
        stock_analysis is None
        or stock_analysis.empty
    ):

        return {}

    total = len(
        stock_analysis
    )

    above_20 = int(
        stock_analysis[
            "above_20dma"
        ].sum()
    )

    above_50 = int(
        stock_analysis[
            "above_50dma"
        ].sum()
    )

    above_200 = int(
        stock_analysis[
            "above_200dma"
        ].sum()
    )

    highs = int(
        stock_analysis[
            "at_52w_high"
        ].sum()
    )

    lows = int(
        stock_analysis[
            "at_52w_low"
        ].sum()
    )

    # --------------------------------------------------------
    # Percentages
    # --------------------------------------------------------

    pct_above_20 = (
        above_20
        / total
        * 100
    )

    pct_above_50 = (
        above_50
        / total
        * 100
    )

    pct_above_200 = (
        above_200
        / total
        * 100
    )

    pct_highs = (
        highs
        / total
        * 100
    )

    pct_lows = (
        lows
        / total
        * 100
    )

    # --------------------------------------------------------
    # High / Low Ratio
    # --------------------------------------------------------

    high_low_ratio = (
        highs / lows
        if lows > 0
        else np.inf
    )

    # --------------------------------------------------------
    # Breadth Score
    #
    # Components:
    #
    # 20 DMA     = 20%
    # 50 DMA     = 30%
    # 200 DMA    = 30%
    # 52W Highs  = 10%
    # 52W Lows   = -10%
    #
    # Score remains 0-100.
    # --------------------------------------------------------

    breadth_score = (
        (
            pct_above_20
            / 100
        ) * 20

        +

        (
            pct_above_50
            / 100
        ) * 30

        +

        (
            pct_above_200
            / 100
        ) * 30

        +

        (
            pct_highs
            / 100
        ) * 10

        -

        (
            pct_lows
            / 100
        ) * 10
    )

    breadth_score = round(
        max(
            0,
            min(
                100,
                breadth_score
            )
        ),
        2
    )

    # --------------------------------------------------------
    # Breadth interpretation
    # --------------------------------------------------------

    if breadth_score >= 65:

        breadth_regime = "Strong"

    elif breadth_score >= 52:

        breadth_regime = "Positive"

    elif breadth_score >= 42:

        breadth_regime = "Neutral"

    elif breadth_score >= 30:

        breadth_regime = "Weak"

    else:

        breadth_regime = "Very Weak"

    return {

        "stocks_analyzed": total,

        "above_20dma": above_20,

        "above_50dma": above_50,

        "above_200dma": above_200,

        "pct_above_20dma": round(
            pct_above_20,
            2
        ),

        "pct_above_50dma": round(
            pct_above_50,
            2
        ),

        "pct_above_200dma": round(
            pct_above_200,
            2
        ),

        "52w_highs": highs,

        "52w_lows": lows,

        "high_low_ratio": (
            round(
                high_low_ratio,
                2
            )
            if np.isfinite(
                high_low_ratio
            )
            else 999
        ),

        "breadth_score": breadth_score,

        "breadth_regime": breadth_regime
    }


# ============================================================
# SAVE STOCK BREADTH DATA
# ============================================================

def save_stock_analysis(
    stock_analysis
):

    if (
        stock_analysis is None
        or stock_analysis.empty
    ):

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = (
        OUTPUT_DIR
        / "market_breadth_stocks.csv"
    )

    stock_analysis.to_csv(
        file_path,
        index=False
    )

    print()

    print(
        "Saved stock breadth data:"
    )

    print(
        file_path
    )


# ============================================================
# SAVE MARKET BREADTH SUMMARY
# ============================================================

def save_breadth_summary(
    breadth
):

    if not breadth:

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = pd.DataFrame(
        [breadth]
    )

    df.to_csv(
        BREADTH_FILE,
        index=False
    )

    print()

    print(
        "Saved market breadth:"
    )

    print(
        BREADTH_FILE
    )


# ============================================================
# MAIN FUNCTION
# ============================================================

def get_market_breadth(
    universe
):

    stock_analysis = (
        analyze_universe(
            universe
        )
    )

    if stock_analysis.empty:

        print(
            "No stock breadth data available."
        )

        return {}

    breadth = (
        calculate_market_breadth(
            stock_analysis
        )
    )

    save_stock_analysis(
        stock_analysis
    )

    save_breadth_summary(
        breadth
    )

    return breadth


# ============================================================
# DISPLAY
# ============================================================

def display_breadth(
    breadth
):

    if not breadth:

        return

    print()
    print("=" * 60)

    print(
        "MARKET BREADTH SUMMARY"
    )

    print("=" * 60)

    print()

    print(
        f"Stocks analyzed       : "
        f"{breadth['stocks_analyzed']}"
    )

    print(
        f"Above 20 DMA          : "
        f"{breadth['above_20dma']} "
        f"({breadth['pct_above_20dma']}%)"
    )

    print(
        f"Above 50 DMA          : "
        f"{breadth['above_50dma']} "
        f"({breadth['pct_above_50dma']}%)"
    )

    print(
        f"Above 200 DMA         : "
        f"{breadth['above_200dma']} "
        f"({breadth['pct_above_200dma']}%)"
    )

    print(
        f"52W Highs             : "
        f"{breadth['52w_highs']}"
    )

    print(
        f"52W Lows              : "
        f"{breadth['52w_lows']}"
    )

    print(
        f"High / Low Ratio      : "
        f"{breadth['high_low_ratio']}"
    )

    print(
        f"Breadth Score         : "
        f"{breadth['breadth_score']}"
    )

    print(
        f"Breadth Regime        : "
        f"{breadth['breadth_regime']}"
    )

    print()

    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from engines.nse_universe import (
        get_nse_universe
    )

    print()

    print(
        "Loading NSE universe..."
    )

    universe = (
        get_nse_universe()
    )

    if universe.empty:

        print(
            "NSE universe unavailable."
        )

    else:

        breadth = (
            get_market_breadth(
                universe
            )
        )

        display_breadth(
            breadth
        )

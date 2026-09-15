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

from engines.market_engine import (
    get_market_regime
)


# ============================================================
# NSE SMART MARKET DASHBOARD
# MARKET + STOCK RANKING ENGINE
# ============================================================


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"

RANKED_FILE = (
    OUTPUT_DIR / "technical_ranked_test.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR / "setup_summary_test.csv"
)

MARKET_FILE = (
    OUTPUT_DIR / "market_regime_test.csv"
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


# ============================================================
# MARKET ANALYSIS
# ============================================================

def analyze_market():

    print()
    print("=" * 60)
    print("RUNNING MARKET ENGINE")
    print("=" * 60)

    market = get_market_regime()

    if not market:

        print(
            "Market Engine returned no data."
        )

        return {}

    overall = market.get(
        "MARKET",
        {}
    )

    print()
    print(
        f"Overall Market Regime : "
        f"{overall.get('regime', 'Unknown')}"
    )

    print(
        f"Overall Market Score   : "
        f"{overall.get('market_score', 0):.2f}"
    )

    # --------------------------------------------------------
    # NIFTY
    # --------------------------------------------------------

    nifty = market.get(
        "NIFTY 50",
        {}
    )

    if nifty:

        print()
        print("NIFTY 50")

        print(
            f"Price       : "
            f"{nifty.get('price', 0):.2f}"
        )

        print(
            f"Trend       : "
            f"{nifty.get('trend', 'Unknown')}"
        )

        print(
            f"Momentum    : "
            f"{nifty.get('momentum', 'Unknown')}"
        )

        print(
            f"RSI         : "
            f"{nifty.get('rsi14', 0):.2f}"
        )

        print(
            f"Score       : "
            f"{nifty.get('market_score', 0):.2f}"
        )

    # --------------------------------------------------------
    # BANK NIFTY
    # --------------------------------------------------------

    banknifty = market.get(
        "BANK NIFTY",
        {}
    )

    if banknifty:

        print()
        print("BANK NIFTY")

        print(
            f"Price       : "
            f"{banknifty.get('price', 0):.2f}"
        )

        print(
            f"Trend       : "
            f"{banknifty.get('trend', 'Unknown')}"
        )

        print(
            f"Momentum    : "
            f"{banknifty.get('momentum', 'Unknown')}"
        )

        print(
            f"RSI         : "
            f"{banknifty.get('rsi14', 0):.2f}"
        )

        print(
            f"Score       : "
            f"{banknifty.get('market_score', 0):.2f}"
        )

    # --------------------------------------------------------
    # INDIA VIX
    # --------------------------------------------------------

    vix = market.get(
        "INDIA VIX",
        {}
    )

    if vix:

        print()
        print(
            f"INDIA VIX   : "
            f"{vix.get('value', 0):.2f}"
        )

    return market


# ============================================================
# SAVE MARKET DATA
# ============================================================

def save_market_data(market):

    if not market:

        return

    rows = []

    for name, values in market.items():

        row = {
            "market_component": name
        }

        row.update(values)

        rows.append(row)

    if not rows:

        return

    df = pd.DataFrame(
        rows
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        MARKET_FILE,
        index=False
    )

    print()
    print(
        f"Saved market data:"
    )

    print(
        MARKET_FILE
    )


# ============================================================
# DOWNLOAD STOCK DATA
# ============================================================

def download_stock_data(
    symbol,
    period="2y"
):

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


# ============================================================
# ANALYZE ONE STOCK
# ============================================================

def analyze_stock(symbol):

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


# ============================================================
# SCAN STOCKS
# ============================================================

def scan_stocks(symbols):

    results = []

    total = len(symbols)

    print()
    print("=" * 60)

    print(
        f"Starting stock scan: "
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


# ============================================================
# CREATE DATAFRAME
# ============================================================

def create_dataframe(results):

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


# ============================================================
# SAVE RANKED RESULTS
# ============================================================

def save_ranked_results(df):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        RANKED_FILE,
        index=False
    )

    print()
    print(
        "Saved ranked results:"
    )

    print(
        RANKED_FILE
    )


# ============================================================
# SAVE SETUP SUMMARY
# ============================================================

def save_setup_summary(summary):

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


# ============================================================
# DISPLAY MARKET
# ============================================================

def display_market(market):

    if not market:

        return

    overall = market.get(
        "MARKET",
        {}
    )

    print()
    print("=" * 60)
    print("MARKET REGIME")
    print("=" * 60)

    print()

    print(
        f"Regime : "
        f"{overall.get('regime', 'Unknown')}"
    )

    print(
        f"Score  : "
        f"{overall.get('market_score', 0):.2f}"
    )


# ============================================================
# DISPLAY RANKINGS
# ============================================================

def display_rankings(df):

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


# ============================================================
# DISPLAY SETUP SUMMARY
# ============================================================

def display_setup_summary(summary):

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


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)

    print(
        "NSE SMART MARKET DASHBOARD"
    )

    print(
        "MARKET + STOCK RANKING TEST"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1 — MARKET
    # --------------------------------------------------------

    market = analyze_market()

    save_market_data(
        market
    )

    display_market(
        market
    )

    # --------------------------------------------------------
    # STEP 2 — STOCKS
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
    # STEP 3 — DATAFRAME
    # --------------------------------------------------------

    df = create_dataframe(
        results
    )

    # --------------------------------------------------------
    # STEP 4 — RANKING
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
    # STEP 5 — SETUP SUMMARY
    # --------------------------------------------------------

    summary = create_setup_summary(
        ranked_df
    )

    # --------------------------------------------------------
    # STEP 6 — SAVE
    # --------------------------------------------------------

    save_ranked_results(
        ranked_df
    )

    save_setup_summary(
        summary
    )

    # --------------------------------------------------------
    # STEP 7 — DISPLAY
    # --------------------------------------------------------

    display_rankings(
        ranked_df
    )

    display_setup_summary(
        summary
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print("=" * 60)

    print(
        "MARKET + STOCK RANKING TEST COMPLETE"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()

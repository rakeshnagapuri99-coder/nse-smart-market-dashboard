import pandas as pd
from pathlib import Path

from engines.nse_universe import get_nse_universe
from engines.market_engine import get_market_regime


# ============================================================
# NSE SMART MARKET DASHBOARD
# MAIN SCANNER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

UNIVERSE_FILE = DATA_DIR / "nse_universe.csv"


def create_directories():
    """
    Create required project directories.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def load_nse_universe():
    """
    Load the NSE stock universe.

    If the universe file does not exist,
    download the latest NSE universe.
    """

    if UNIVERSE_FILE.exists():

        print(
            "Loading existing NSE universe..."
        )

        df = pd.read_csv(
            UNIVERSE_FILE
        )

        return df

    print(
        "NSE universe file not found."
    )

    print(
        "Downloading latest NSE universe..."
    )

    df = get_nse_universe()

    if df.empty:

        print(
            "Unable to create NSE universe."
        )

        return pd.DataFrame()

    df.to_csv(
        UNIVERSE_FILE,
        index=False
    )

    return df


def analyze_market():
    """
    Run the market engine.
    """

    print()
    print("=" * 60)
    print("MARKET ANALYSIS")
    print("=" * 60)

    market = get_market_regime()

    if not market:

        print(
            "Market analysis unavailable."
        )

        return {}

    overall = market.get(
        "MARKET",
        {}
    )

    print()

    print(
        f"Market Regime: "
        f"{overall.get('regime', 'Unknown')}"
    )

    print(
        f"Market Score: "
        f"{overall.get('market_score', 0)}"
    )

    print()

    # NIFTY
    nifty = market.get(
        "NIFTY 50",
        {}
    )

    if nifty:

        print("NIFTY 50")

        print(
            f"Price: {nifty.get('price', 0):.2f}"
        )

        print(
            f"Trend: {nifty.get('trend', 'Unknown')}"
        )

        print(
            f"Momentum: "
            f"{nifty.get('momentum', 'Unknown')}"
        )

        print(
            f"RSI: "
            f"{nifty.get('rsi14', 0):.2f}"
        )

        print(
            f"Score: "
            f"{nifty.get('market_score', 0):.2f}"
        )

        print()

    # BANK NIFTY
    banknifty = market.get(
        "BANK NIFTY",
        {}
    )

    if banknifty:

        print("BANK NIFTY")

        print(
            f"Price: "
            f"{banknifty.get('price', 0):.2f}"
        )

        print(
            f"Trend: "
            f"{banknifty.get('trend', 'Unknown')}"
        )

        print(
            f"Momentum: "
            f"{banknifty.get('momentum', 'Unknown')}"
        )

        print(
            f"RSI: "
            f"{banknifty.get('rsi14', 0):.2f}"
        )

        print(
            f"Score: "
            f"{banknifty.get('market_score', 0):.2f}"
        )

        print()

    # INDIA VIX
    vix = market.get(
        "INDIA VIX",
        {}
    )

    if vix:

        print(
            f"India VIX: "
            f"{vix.get('value', 0):.2f}"
        )

    print(
        "=" * 60
    )

    return market


def show_universe_summary(universe):
    """
    Display stock universe summary.
    """

    print()
    print("=" * 60)
    print("NSE STOCK UNIVERSE")
    print("=" * 60)

    if universe.empty:

        print(
            "No stocks available."
        )

        return

    print(
        f"Total securities: "
        f"{len(universe)}"
    )

    print()

    required_columns = [
        "SYMBOL",
        "YAHOO_SYMBOL"
    ]

    available_columns = [
        column
        for column in required_columns
        if column in universe.columns
    ]

    if available_columns:

        print(
            universe[
                available_columns
            ].head(10).to_string(
                index=False
            )
        )

    print(
        "=" * 60
    )


def main():

    print()
    print("=" * 60)
    print("NSE SMART MARKET DASHBOARD")
    print("MAIN SCANNER")
    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    create_directories()

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    universe = load_nse_universe()

    if universe.empty:

        print()
        print(
            "Scanner stopped because "
            "NSE universe is unavailable."
        )

        return

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    show_universe_summary(
        universe
    )

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    market = analyze_market()

    # --------------------------------------------------------
    # CURRENT STATUS
    # --------------------------------------------------------

    print()

    print("=" * 60)

    print(
        "SCANNER FOUNDATION COMPLETE"
    )

    print("=" * 60)

    print()

    print(
        "NSE Universe: READY"
    )

    print(
        "Market Engine: READY"
    )

    print(
        "Technical Engine: READY"
    )

    print()

    print(
        "Next stage:"
    )

    print(
        "Download historical stock data "
        "and run technical analysis."
    )

    print()

    print("=" * 60)


if __name__ == "__main__":
    main()

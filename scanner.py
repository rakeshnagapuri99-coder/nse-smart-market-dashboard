import pandas as pd

from engines.nse_universe import get_nse_universe
from engines.market_breadth import get_market_breadth, display_breadth
from engines.market_engine import get_market_regime
from engines.technical_engine import calculate_technical_indicators
from engines.ranking_engine import rank_stocks, create_setup_summary


# ============================================================
# NSE SMART MARKET DASHBOARD
# MAIN SCANNER
# ============================================================

OUTPUT_DIR = "output"


# ============================================================
# MARKET BREADTH
# ============================================================

def analyze_breadth():
    print()
    print("=" * 60)
    print("STEP 1 — MARKET BREADTH")
    print("=" * 60)

    universe = get_nse_universe()

    if universe.empty:
        print("NSE universe unavailable.")
        return {}

    breadth = get_market_breadth(universe)

    display_breadth(breadth)

    return breadth


# ============================================================
# MARKET REGIME
# ============================================================

def analyze_market(breadth=None):
    print()
    print("=" * 60)
    print("STEP 2 — MARKET REGIME")
    print("=" * 60)

    market = get_market_regime(breadth)

    return market


def save_market_data(market):
    if not market:
        print("No market data available.")
        return

    output_file = f"{OUTPUT_DIR}/market_regime_test.csv"

    df = pd.DataFrame([market])
    df.to_csv(output_file, index=False)

    print()
    print(f"Saved market regime: {output_file}")


def display_market(market):
    if not market:
        return

    print()
    print("=" * 60)
    print("MARKET REGIME SUMMARY")
    print("=" * 60)
    print()

    print(f"Market Regime        : {market.get('market_regime')}")
    print(f"Market Score         : {market.get('market_score')}")
    print(f"Nifty Score          : {market.get('nifty_score')}")
    print(f"Bank Nifty Score     : {market.get('bank_nifty_score')}")
    print(f"Breadth Score        : {market.get('breadth_score')}")
    print(f"India VIX            : {market.get('vix')}")
    print(f"VIX Interpretation   : {market.get('vix_interpretation')}")

    print()
    print("=" * 60)


# ============================================================
# TEST STOCK DATA
# ============================================================

def get_test_stocks():
    return [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS"
    ]


def analyze_test_stocks():
    print()
    print("=" * 60)
    print("STEP 3 — TEST STOCK ANALYSIS")
    print("=" * 60)

    import yfinance as yf

    stocks = get_test_stocks()

    results = []

    for symbol in stocks:

        print()
        print(f"Analyzing {symbol}...")

        try:
            data = yf.download(
                symbol,
                period="2y",
                interval="1d",
                auto_adjust=False,
                progress=False
            )

            if data.empty:
                print(f"No data for {symbol}")
                continue

            # Handle yfinance MultiIndex columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data = calculate_technical_indicators(data)

            if data.empty:
                continue

            latest = data.iloc[-1]

            result = {
                "symbol": symbol,
                "price": latest["Close"],
                "trend": latest["Trend"],
                "momentum": latest["Momentum"],
                "rsi14": latest["RSI14"],
                "volume_ratio": latest["Volume_Ratio"],
                "distance_from_52w_high_pct":
                    latest["Distance_From_52W_High_Pct"],
                "distance_from_200dma_pct":
                    latest["Distance_From_200DMA_Pct"],
                "breakout_status":
                    latest["Breakout_Status"],
                "support": latest["Support"],
                "resistance": latest["Resistance"]
            }

            results.append(result)

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


# ============================================================
# RANK STOCKS
# ============================================================

def analyze_rankings(stock_data):

    if stock_data.empty:
        print("No stock data available for ranking.")
        return pd.DataFrame()

    print()
    print("=" * 60)
    print("STEP 4 — STOCK RANKING")
    print("=" * 60)

    ranked = rank_stocks(stock_data)

    output_file = f"{OUTPUT_DIR}/technical_ranked_test.csv"

    ranked.to_csv(output_file, index=False)

    print()
    print(f"Saved ranked stocks: {output_file}")

    print()
    print(ranked.to_string(index=False))

    return ranked


# ============================================================
# SETUP SUMMARY
# ============================================================

def save_setup_summary(ranked):

    if ranked.empty:
        return

    summary = create_setup_summary(ranked)

    output_file = f"{OUTPUT_DIR}/setup_summary_test.csv"

    summary.to_csv(output_file, index=False)

    print()
    print(f"Saved setup summary: {output_file}")

    print()
    print(summary.to_string(index=False))


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("NSE SMART MARKET DASHBOARD")
    print("SCANNER TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1 — MARKET BREADTH
    # --------------------------------------------------------

    breadth = analyze_breadth()

    # --------------------------------------------------------
    # STEP 2 — MARKET REGIME
    # --------------------------------------------------------

    market = analyze_market(breadth)

    save_market_data(market)

    display_market(market)

    # --------------------------------------------------------
    # STEP 3 — TEST STOCK ANALYSIS
    # --------------------------------------------------------

    stock_data = analyze_test_stocks()

    # --------------------------------------------------------
    # STEP 4 — RANK STOCKS
    # --------------------------------------------------------

    ranked = analyze_rankings(stock_data)

    # --------------------------------------------------------
    # STEP 5 — SETUP SUMMARY
    # --------------------------------------------------------

    save_setup_summary(ranked)

    print()
    print("=" * 60)
    print("SCANNER TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

import pandas as pd

from engines.nse_universe import (
    get_nse_universe,
    save_universe
)


# ============================================================
# NSE SMART MARKET DASHBOARD
# NSE UNIVERSE TEST
# ============================================================


def main():

    print()
    print("=" * 60)

    print(
        "NSE SMART MARKET DASHBOARD"
    )

    print(
        "NSE UNIVERSE TEST"
    )

    print("=" * 60)

    print()

    # --------------------------------------------------------
    # Download NSE Universe
    # --------------------------------------------------------

    universe = get_nse_universe()

    # --------------------------------------------------------
    # Check result
    # --------------------------------------------------------

    if universe.empty:

        print()
        print(
            "ERROR: NSE universe is empty."
        )

        return

    # --------------------------------------------------------
    # Save NSE Universe
    # --------------------------------------------------------

    save_universe(
        universe
    )

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    print()

    print(
        "NSE UNIVERSE SUCCESSFULLY LOADED"
    )

    print()

    print(
        f"Total securities: "
        f"{len(universe)}"
    )

    print()

    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    print(
        "Available columns:"
    )

    print(
        list(universe.columns)
    )

    print()

    # --------------------------------------------------------
    # Sample stocks
    # --------------------------------------------------------

    print("=" * 60)

    print(
        "SAMPLE STOCKS"
    )

    print("=" * 60)

    print()

    columns = [
        "SYMBOL",
        "YAHOO_SYMBOL"
    ]

    available_columns = [
        column
        for column in columns
        if column in universe.columns
    ]

    print(
        universe[
            available_columns
        ].head(20).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    print()

    print("=" * 60)

    print(
        "DATA QUALITY CHECK"
    )

    print("=" * 60)

    print()

    duplicate_count = (
        universe["SYMBOL"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate symbols: "
        f"{duplicate_count}"
    )

    # --------------------------------------------------------
    # Missing Yahoo symbols
    # --------------------------------------------------------

    missing_yahoo = (
        universe["YAHOO_SYMBOL"]
        .isna()
        .sum()
    )

    print(
        f"Missing Yahoo symbols: "
        f"{missing_yahoo}"
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print()

    if (
        duplicate_count == 0
        and missing_yahoo == 0
    ):

        print(
            "✓ NSE UNIVERSE TEST PASSED"
        )

    else:

        print(
            "⚠ NSE UNIVERSE HAS DATA QUALITY ISSUES"
        )

    print()

    print("=" * 60)


if __name__ == "__main__":

    main()

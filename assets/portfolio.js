// ============================================================
// NSE SMART MARKET DASHBOARD
// PORTFOLIO BUILDER
// ============================================================

let portfolioData = null;


// ============================================================
// INITIALIZE
// ============================================================

function initializePortfolioBuilder() {

    if (
        typeof dashboardData === "undefined" ||
        !dashboardData
    ) {
        return;
    }

    portfolioData =
        dashboardData.stocks || [];

    renderPortfolioBuilder();
}


// ============================================================
// BUILD CANDIDATES
// ============================================================

function getPortfolioCandidates() {

    if (!portfolioData) {
        return [];
    }

    return portfolioData
        .filter(stock => {

            const price =
                Number(stock.price);

            const sma200 =
                Number(stock.sma200);

            const highDistance =
                Number(
                    stock.distance_from_52w_high_pct
                );

            const rating =
                Number(
                    stock.overall_rating ??
                    stock.rating ??
                    0
                );

            if (
                !Number.isFinite(price) ||
                !Number.isFinite(sma200) ||
                !Number.isFinite(highDistance)
            ) {
                return false;
            }

            return (
                price > sma200 &&
                highDistance >= -15 &&
                rating >= 45
            );

        })
        .sort(
            (a, b) =>
                Number(
                    b.overall_rating ??
                    b.rating ??
                    0
                )
                -
                Number(
                    a.overall_rating ??
                    a.rating ??
                    0
                )
        );

}


// ============================================================
// RENDER
// ============================================================

function renderPortfolioBuilder() {

    const container =
        document.getElementById(
            "portfolioBuilder"
        );

    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="portfolio-controls">

            <div class="portfolio-input">

                <label>
                    Portfolio Amount
                </label>

                <input
                    id="portfolioAmount"
                    type="number"
                    min="10000"
                    value="100000"
                    step="10000"
                >

            </div>


            <div class="portfolio-input">

                <label>
                    Number of Stocks
                </label>

                <input
                    id="portfolioStockCount"
                    type="number"
                    min="3"
                    max="25"
                    value="10"
                >

            </div>


            <div class="portfolio-input">

                <label>
                    Stop Loss
                </label>

                <input
                    id="portfolioStopLoss"
                    type="number"
                    min="1"
                    max="30"
                    value="10"
                    step="1"
                >

            </div>


            <button
                class="portfolio-button"
                id="buildPortfolioButton"
            >
                Build Portfolio
            </button>

        </div>


        <div
            id="portfolioSummary"
            class="portfolio-summary"
        ></div>


        <div
            id="portfolioResults"
            class="portfolio-results"
        ></div>

    `;


    document
        .getElementById(
            "buildPortfolioButton"
        )
        .addEventListener(
            "click",
            buildPortfolio
        );


    buildPortfolio();

}


// ============================================================
// BUILD PORTFOLIO
// ============================================================

function buildPortfolio() {

    const amount =
        Number(
            document.getElementById(
                "portfolioAmount"
            ).value
        );

    const stockCount =
        Number(
            document.getElementById(
                "portfolioStockCount"
            ).value
        );

    const stopLossPercent =
        Number(
            document.getElementById(
                "portfolioStopLoss"
            ).value
        );


    if (
        !Number.isFinite(amount) ||
        amount <= 0
    ) {
        return;
    }


    const candidates =
        getPortfolioCandidates();


    if (!candidates.length) {

        document.getElementById(
            "portfolioResults"
        ).innerHTML = `

            <div class="empty-state">

                No stocks currently satisfy
                the portfolio filters.

            </div>

        `;

        return;

    }


    const selected =
        candidates.slice(
            0,
            Math.max(
                1,
                Math.min(
                    stockCount,
                    candidates.length
                )
            )
        );


    // Equal allocation by default.
    const allocation =
        amount / selected.length;


    let expectedProfit = 0;
    let maximumLoss = 0;


    const portfolio = selected.map(
        (stock, index) => {

            const price =
                Number(stock.price);


            const shares =
                Math.floor(
                    allocation / price
                );


            const invested =
                shares * price;


            const stopLoss =
                price *
                (
                    1 -
                    stopLossPercent / 100
                );


            const expectedGain =
                calculateExpectedGain(
                    stock
                );


            const expectedValue =
                invested *
                (
                    expectedGain / 100
                );


            const loss =
                invested *
                (
                    stopLossPercent / 100
                );


            expectedProfit +=
                expectedValue;

            maximumLoss +=
                loss;


            return {

                rank:
                    index + 1,

                symbol:
                    stock.nse_symbol ||
                    stock.symbol
                        .replace(
                            ".NS",
                            ""
                        ),

                company:
                    stock.company_name ||
                    "",

                price,

                shares,

                invested,

                allocation:
                    invested /
                    amount *
                    100,

                stopLoss,

                expectedGain,

                expectedProfit:
                    expectedValue,

                maximumLoss:
                    loss,

                rating:
                    Number(
                        stock.overall_rating ??
                        stock.rating ??
                        0
                    ),

                setup:
                    stock.setup ||
                    "—",

                trend:
                    stock.trend ||
                    "—"

            };

        }
    );


    renderPortfolioSummary(
        amount,
        portfolio,
        expectedProfit,
        maximumLoss
    );


    renderPortfolioResults(
        portfolio
    );

}


// ============================================================
// EXPECTED GAIN
// ============================================================

function calculateExpectedGain(
    stock
) {

    const trend =
        String(
            stock.trend ||
            ""
        );


    const setup =
        String(
            stock.setup ||
            ""
        );


    const rating =
        Number(
            stock.overall_rating ??
            stock.rating ??
            50
        );


    let gain = 8;


    if (
        trend.includes(
            "Strong Uptrend"
        ) ||
        trend.includes(
            "Strong Bullish"
        )
    ) {

        gain += 6;

    } else if (
        trend.includes(
            "Uptrend"
        ) ||
        trend.includes(
            "Bullish"
        )
    ) {

        gain += 4;

    }


    if (
        setup.includes(
            "Breakout"
        )
    ) {

        gain += 4;

    }


    if (
        setup.includes(
            "52W High"
        )
    ) {

        gain += 3;

    }


    if (
        setup.includes(
            "Momentum"
        )
    ) {

        gain += 3;

    }


    if (rating >= 75) {

        gain += 4;

    } else if (
        rating >= 60
    ) {

        gain += 2;

    }


    return Math.min(
        30,
        Math.max(
            5,
            gain
        )
    );

}


// ============================================================
// SUMMARY
// ============================================================

function renderPortfolioSummary(
    amount,
    portfolio,
    expectedProfit,
    maximumLoss
) {

    const invested =
        portfolio.reduce(
            (sum, item) =>
                sum + item.invested,
            0
        );


    const expectedReturn =
        invested > 0
            ? expectedProfit /
              invested *
              100
            : 0;


    const lossPercent =
        invested > 0
            ? maximumLoss /
              invested *
              100
            : 0;


    const container =
        document.getElementById(
            "portfolioSummary"
        );


    container.innerHTML = `

        <div class="portfolio-stat">

            <span>
                Portfolio
            </span>

            <strong>
                ₹${formatPortfolioNumber(
                    amount
                )}
            </strong>

        </div>


        <div class="portfolio-stat">

            <span>
                Invested
            </span>

            <strong>
                ₹${formatPortfolioNumber(
                    invested
                )}
            </strong>

        </div>


        <div class="portfolio-stat">

            <span>
                Expected Gain
            </span>

            <strong>
                ₹${formatPortfolioNumber(
                    expectedProfit
                )}
            </strong>

            <small>
                ${expectedReturn.toFixed(2)}%
            </small>

        </div>


        <div class="portfolio-stat">

            <span>
                Maximum Loss
            </span>

            <strong>
                ₹${formatPortfolioNumber(
                    maximumLoss
                )}
            </strong>

            <small>
                ${lossPercent.toFixed(2)}%
            </small>

        </div>


        <div class="portfolio-stat">

            <span>
                Stocks
            </span>

            <strong>
                ${portfolio.length}
            </strong>

        </div>

    `;

}


// ============================================================
// RESULTS
// ============================================================

function renderPortfolioResults(
    portfolio
) {

    const container =
        document.getElementById(
            "portfolioResults"
        );


    const rows =
        portfolio.map(
            item => `

                <tr>

                    <td>
                        ${item.rank}
                    </td>

                    <td>

                        <strong>
                            ${escapeHtml(
                                item.symbol
                            )}
                        </strong>

                        <small>
                            ${escapeHtml(
                                item.company
                            )}
                        </small>

                    </td>

                    <td>
                        ₹${formatPortfolioNumber(
                            item.price
                        )}
                    </td>

                    <td>
                        ${item.shares}
                    </td>

                    <td>
                        ₹${formatPortfolioNumber(
                            item.invested
                        )}
                    </td>

                    <td>
                        ${item.allocation.toFixed(2)}%
                    </td>

                    <td>
                        ₹${formatPortfolioNumber(
                            item.stopLoss
                        )}
                    </td>

                    <td>
                        ${item.expectedGain.toFixed(2)}%
                    </td>

                    <td>
                        ₹${formatPortfolioNumber(
                            item.expectedProfit
                        )}
                    </td>

                    <td>
                        ${item.rating.toFixed(2)}
                    </td>

                    <td>
                        ${escapeHtml(
                            item.setup
                        )}
                    </td>

                </tr>

            `
        ).join("");


    container.innerHTML = `

        <div class="table-scroll">

            <table>

                <thead>

                    <tr>

                        <th>#</th>
                        <th>Stock</th>
                        <th>Entry</th>
                        <th>Qty</th>
                        <th>Investment</th>
                        <th>Allocation</th>
                        <th>Stop Loss</th>
                        <th>Expected Gain</th>
                        <th>Expected Profit</th>
                        <th>Rating</th>
                        <th>Setup</th>

                    </tr>

                </thead>

                <tbody>
                    ${rows}
                </tbody>

            </table>

        </div>

    `;

}


// ============================================================
// NUMBER FORMAT
// ============================================================

function formatPortfolioNumber(
    value
) {

    return Number(
        value || 0
    ).toLocaleString(
        "en-IN",
        {
            maximumFractionDigits: 0
        }
    );

}


// ============================================================
// START
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setTimeout(
            initializePortfolioBuilder,
            500
        );

    }
);

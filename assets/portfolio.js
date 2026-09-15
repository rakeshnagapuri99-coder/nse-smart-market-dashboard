// ============================================================
// NSE SMART MARKET DASHBOARD V2
// PORTFOLIO BUILDER
// Created by Rakesh Nagapuri
// ============================================================

let portfolioInitialized = false;


// ============================================================
// INITIALIZATION
// ============================================================

function initializePortfolioBuilder() {

    if (portfolioInitialized) {
        return;
    }

    if (
        typeof dashboardData === "undefined" ||
        !dashboardData ||
        !Array.isArray(dashboardData.stocks)
    ) {
        return;
    }

    portfolioInitialized = true;

    setupPortfolioControls();
    calculatePortfolio();
}


// ============================================================
// CONTROLS
// ============================================================

function setupPortfolioControls() {

    const amountInput =
        document.getElementById("portfolioAmount");

    const stockCountInput =
        document.getElementById("portfolioStockCount");

    const stopLossInput =
        document.getElementById("portfolioStopLoss");

    const inputs = [
        amountInput,
        stockCountInput,
        stopLossInput
    ];

    inputs.forEach(input => {

        if (!input) {
            return;
        }

        input.addEventListener(
            "input",
            calculatePortfolio
        );

        input.addEventListener(
            "change",
            calculatePortfolio
        );
    });

    const calculateButton =
        document.getElementById("calculatePortfolio");

    if (calculateButton) {

        calculateButton.addEventListener(
            "click",
            calculatePortfolio
        );
    }
}


// ============================================================
// MAIN CALCULATION
// ============================================================

function calculatePortfolio() {

    if (
        typeof dashboardData === "undefined" ||
        !dashboardData ||
        !Array.isArray(dashboardData.stocks)
    ) {
        renderPortfolioMessage(
            "Portfolio data is not available yet."
        );

        return;
    }

    const amount =
        getInputNumber(
            "portfolioAmount",
            100000
        );

    const requestedStocks =
        Math.max(
            1,
            Math.round(
                getInputNumber(
                    "portfolioStockCount",
                    10
                )
            )
        );

    const stopLossPct =
        Math.max(
            0,
            getInputNumber(
                "portfolioStopLoss",
                10
            )
        );

    if (amount <= 0) {

        renderPortfolioMessage(
            "Enter a portfolio amount greater than ₹0."
        );

        return;
    }

    const candidates =
        getPortfolioCandidates();

    if (candidates.length === 0) {

        renderPortfolioMessage(
            "No stocks currently satisfy the portfolio criteria."
        );

        return;
    }

    const selected =
        selectPortfolioStocks(
            candidates,
            requestedStocks
        );

    const portfolio =
        buildPortfolio(
            selected,
            amount,
            stopLossPct
        );

    renderPortfolio(
        portfolio,
        amount,
        requestedStocks,
        stopLossPct
    );
}


// ============================================================
// INPUT HELPERS
// ============================================================

function getInputNumber(id, fallback) {

    const element =
        document.getElementById(id);

    if (!element) {
        return fallback;
    }

    const value =
        Number(element.value);

    if (!Number.isFinite(value)) {
        return fallback;
    }

    return value;
}


// ============================================================
// CANDIDATE SELECTION
// ============================================================

function getPortfolioCandidates() {

    const stocks =
        dashboardData.stocks || [];

    return stocks
        .filter(stock => {

            const price =
                Number(stock.price);

            const sma200 =
                Number(stock.sma200);

            const distanceHigh =
                Number(
                    stock.distance_from_52w_high_pct
                );

            const overallScore =
                Number(
                    stock.overall_score ??
                    stock.rating ??
                    0
                );

            if (
                !Number.isFinite(price) ||
                !Number.isFinite(sma200)
            ) {
                return false;
            }

            if (price <= sma200) {
                return false;
            }

            // Within 15% of rolling 52-week high
            if (
                !Number.isFinite(distanceHigh) ||
                distanceHigh < -15
            ) {
                return false;
            }

            // Minimum quality/rating threshold
            if (overallScore < 45) {
                return false;
            }

            return true;
        })
        .map(stock => {

            const score =
                Number(
                    stock.overall_score ??
                    stock.rating ??
                    0
                );

            const technical =
                Number(
                    stock.technical_score ?? 0
                );

            const fundamental =
                Number(
                    stock.fundamental_score ?? 0
                );

            const sector =
                Number(
                    stock.sector_score ?? 0
                );

            const distanceHigh =
                Number(
                    stock.distance_from_52w_high_pct
                );

            return {
                ...stock,

                portfolio_rank_score:
                    calculatePortfolioRankScore(
                        score,
                        technical,
                        fundamental,
                        sector,
                        distanceHigh
                    )
            };
        })
        .sort(
            (a, b) =>
                b.portfolio_rank_score -
                a.portfolio_rank_score
        );
}


function calculatePortfolioRankScore(
    overall,
    technical,
    fundamental,
    sector,
    distanceHigh
) {

    let score = 0;

    // Overall quality
    score += overall * 0.50;

    // Technical strength
    score += technical * 0.25;

    // Fundamental quality
    score += fundamental * 0.15;

    // Sector context
    score += sector * 0.10;

    // Preference for stocks closer to 52W high
    if (Number.isFinite(distanceHigh)) {

        const proximity =
            Math.max(
                0,
                Math.min(
                    100,
                    100 + distanceHigh * 4
                )
            );

        score += proximity * 0.05;
    }

    return score;
}


// ============================================================
// SELECT STOCKS
// ============================================================

function selectPortfolioStocks(
    candidates,
    requestedStocks
) {

    return candidates.slice(
        0,
        requestedStocks
    );
}


// ============================================================
// BUILD PORTFOLIO
// ============================================================

function buildPortfolio(
    stocks,
    totalAmount,
    stopLossPct
) {

    if (!stocks.length) {
        return [];
    }

    const allocationPerStock =
        totalAmount / stocks.length;

    let remainingCash =
        totalAmount;

    const portfolio = [];

    stocks.forEach(stock => {

        const price =
            Number(stock.price);

        if (
            !Number.isFinite(price) ||
            price <= 0
        ) {
            return;
        }

        const quantity =
            Math.floor(
                allocationPerStock / price
            );

        if (quantity <= 0) {
            return;
        }

        const invested =
            quantity * price;

        const stopLoss =
            price *
            (1 - stopLossPct / 100);

        const expectedGainPct =
            calculateExpectedGain(stock);

        const expectedTarget =
            price *
            (1 + expectedGainPct / 100);

        const expectedProfit =
            (expectedTarget - price) *
            quantity;

        const maximumLoss =
            (price - stopLoss) *
            quantity;

        remainingCash -= invested;

        portfolio.push({

            stock,

            symbol:
                stock.symbol ||
                stock.nse_symbol ||
                "-",

            price,

            quantity,

            invested,

            allocationPct:
                (invested / totalAmount) * 100,

            stopLoss,

            expectedGainPct,

            expectedTarget,

            expectedProfit,

            maximumLoss
        });
    });

    return portfolio;
}


// ============================================================
// EXPECTED GAIN MODEL
// ============================================================

function calculateExpectedGain(stock) {

    const trend =
        String(
            stock.trend || ""
        ).toLowerCase();

    const momentum =
        String(
            stock.momentum || ""
        ).toLowerCase();

    const setup =
        String(
            stock.setup || ""
        ).toLowerCase();

    const rating =
        Number(
            stock.overall_score ??
            stock.rating ??
            0
        );

    let expected = 8;

    // Trend
    if (trend.includes("strong uptrend")) {
        expected += 7;
    } else if (trend.includes("uptrend")) {
        expected += 4;
    }

    // Momentum
    if (momentum.includes("strong positive")) {
        expected += 5;
    } else if (momentum.includes("positive")) {
        expected += 3;
    }

    // Setup
    if (setup.includes("strong breakout")) {
        expected += 5;
    } else if (
        setup.includes("breakout") ||
        setup.includes("52w")
    ) {
        expected += 3;
    } else if (
        setup.includes("dma")
    ) {
        expected += 2;
    }

    // Rating
    if (rating >= 75) {
        expected += 5;
    } else if (rating >= 65) {
        expected += 3;
    } else if (rating >= 55) {
        expected += 1;
    }

    // Keep the scenario within a reasonable model range
    expected =
        Math.max(
            5,
            Math.min(
                30,
                expected
            )
        );

    return expected;
}


// ============================================================
// RENDER PORTFOLIO
// ============================================================

function renderPortfolio(
    portfolio,
    totalAmount,
    requestedStocks,
    stopLossPct
) {

    const summary =
        document.getElementById(
            "portfolioSummary"
        );

    const table =
        document.getElementById(
            "portfolioTable"
        );

    if (!summary || !table) {
        return;
    }

    if (!portfolio.length) {

        renderPortfolioMessage(
            "The selected portfolio amount is too small to purchase whole shares of the current candidates."
        );

        return;
    }

    const invested =
        portfolio.reduce(
            (sum, item) =>
                sum + item.invested,
            0
        );

    const cashRemaining =
        Math.max(
            0,
            totalAmount - invested
        );

    const expectedProfit =
        portfolio.reduce(
            (sum, item) =>
                sum + item.expectedProfit,
            0
        );

    const maximumLoss =
        portfolio.reduce(
            (sum, item) =>
                sum + item.maximumLoss,
            0
        );

    const expectedReturnPct =
        invested > 0
            ? (
                expectedProfit /
                invested
            ) * 100
            : 0;

    const investedPct =
        totalAmount > 0
            ? (
                invested /
                totalAmount
            ) * 100
            : 0;

    summary.innerHTML = `

        <div class="portfolio-summary-card">

            <span>Stocks Selected</span>

            <strong>
                ${portfolio.length}
            </strong>

            <small>
                Requested: ${requestedStocks}
            </small>

        </div>


        <div class="portfolio-summary-card">

            <span>Portfolio Amount</span>

            <strong>
                ${formatPortfolioCurrency(
                    totalAmount
                )}
            </strong>

            <small>
                Model capital
            </small>

        </div>


        <div class="portfolio-summary-card">

            <span>Amount Invested</span>

            <strong>
                ${formatPortfolioCurrency(
                    invested
                )}
            </strong>

            <small>
                ${formatPortfolioPercent(
                    investedPct
                )} deployed
            </small>

        </div>


        <div class="portfolio-summary-card">

            <span>Cash Remaining</span>

            <strong>
                ${formatPortfolioCurrency(
                    cashRemaining
                )}
            </strong>

            <small>
                Whole-share allocation
            </small>

        </div>


        <div class="portfolio-summary-card">

            <span>Expected Profit</span>

            <strong class="positive">
                ${formatPortfolioCurrency(
                    expectedProfit
                )}
            </strong>

            <small>
                Scenario: ${formatPortfolioPercent(
                    expectedReturnPct
                )}
            </small>

        </div>


        <div class="portfolio-summary-card">

            <span>Maximum Loss</span>

            <strong class="negative">
                ${formatPortfolioCurrency(
                    maximumLoss
                )}
            </strong>

            <small>
                Stop loss: ${formatPortfolioPercent(
                    stopLossPct
                )}
            </small>

        </div>

    `;


    table.innerHTML = `

        <div class="table-wrapper">

            <table class="dashboard-table portfolio-table">

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
                        <th>Expected Target</th>
                        <th>Expected Profit</th>
                        <th>Max Loss</th>
                        <th>Rating</th>

                    </tr>

                </thead>

                <tbody>

                    ${
                        portfolio
                            .map(
                                (item, index) =>
                                    renderPortfolioRow(
                                        item,
                                        index + 1
                                    )
                            )
                            .join("")
                    }

                </tbody>

            </table>

        </div>


        <div class="portfolio-note">

            <strong>How this portfolio is built:</strong>

            Stocks must be above the 200 DMA,
            within 15% of their rolling 52-week high,
            and have an overall model score of at least 45.

            Selection is then ranked using technical,
            fundamental, sector and 52-week-high proximity factors.

        </div>


        <div class="portfolio-disclaimer">

            <strong>Important:</strong>
            This is a quantitative portfolio-building tool,
            not personalised investment advice.

            Expected gain is a model scenario, not a forecast
            or guaranteed return. Actual prices, liquidity,
            execution and market conditions may differ.

        </div>

    `;
}


function renderPortfolioRow(
    item,
    rank
) {

    const stock =
        item.stock;

    const symbol =
        item.symbol;

    const rating =
        Number(
            stock.overall_score ??
            stock.rating ??
            0
        );

    return `

        <tr
            onclick="openStockDetail('${escapePortfolioJs(symbol)}')"
            class="stock-row"
        >

            <td>
                ${rank}
            </td>

            <td>
                <strong>
                    ${escapePortfolioHtml(symbol)}
                </strong>
            </td>

            <td>
                ${formatPortfolioCurrency(
                    item.price
                )}
            </td>

            <td>
                ${formatPortfolioInteger(
                    item.quantity
                )}
            </td>

            <td>
                ${formatPortfolioCurrency(
                    item.invested
                )}
            </td>

            <td>
                ${formatPortfolioPercent(
                    item.allocationPct
                )}
            </td>

            <td class="negative">
                ${formatPortfolioCurrency(
                    item.stopLoss
                )}
            </td>

            <td class="positive">
                +${formatPortfolioPercent(
                    item.expectedGainPct
                )}
            </td>

            <td>
                ${formatPortfolioCurrency(
                    item.expectedTarget
                )}
            </td>

            <td class="positive">
                ${formatPortfolioCurrency(
                    item.expectedProfit
                )}
            </td>

            <td class="negative">
                ${formatPortfolioCurrency(
                    item.maximumLoss
                )}
            </td>

            <td>
                <strong>
                    ${formatPortfolioNumber(
                        rating
                    )}
                </strong>
            </td>

        </tr>
    `;
}


// ============================================================
// EMPTY / ERROR STATE
// ============================================================

function renderPortfolioMessage(message) {

    const summary =
        document.getElementById(
            "portfolioSummary"
        );

    const table =
        document.getElementById(
            "portfolioTable"
        );

    if (summary) {

        summary.innerHTML = `
            <div class="empty-state">
                ${escapePortfolioHtml(message)}
            </div>
        `;
    }

    if (table) {
        table.innerHTML = "";
    }
}


// ============================================================
// FORMATTING
// ============================================================

function formatPortfolioCurrency(value) {

    if (!Number.isFinite(Number(value))) {
        return "—";
    }

    return "₹" +
        Number(value).toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );
}


function formatPortfolioNumber(value) {

    if (!Number.isFinite(Number(value))) {
        return "—";
    }

    return Number(value).toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }
    );
}


function formatPortfolioInteger(value) {

    if (!Number.isFinite(Number(value))) {
        return "—";
    }

    return Math.floor(Number(value))
        .toLocaleString("en-IN");
}


function formatPortfolioPercent(value) {

    if (!Number.isFinite(Number(value))) {
        return "—";
    }

    return Number(value).toFixed(2) + "%";
}


// ============================================================
// SECURITY HELPERS
// ============================================================

function escapePortfolioHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function escapePortfolioJs(value) {

    return String(value ?? "")
        .replace(/\\/g, "\\\\")
        .replace(/'/g, "\\'");
}


// ============================================================
// GLOBAL
// ============================================================

window.initializePortfolioBuilder =
    initializePortfolioBuilder;

window.calculatePortfolio =
    calculatePortfolio;


// ============================================================
// END
// ============================================================

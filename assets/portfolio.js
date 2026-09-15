// ============================================================
// NSE SMART MARKET DASHBOARD V2.1
// PORTFOLIO BUILDER
// Created by Rakesh Nagapuri
//
// STEP 3
// - Working Portfolio Builder
// - Uses dashboardData from dashboard.js
// - Uses ranking-engine trade plans
// - No arbitrary 10% stop loss
// - No invented targets
// - Diversification control
// - Risk and reward calculations
// - Stock detail integration
// - Excel/CSV export
// ============================================================


let portfolioResult = null;


// ============================================================
// INITIALIZE
// ============================================================

function initializePortfolioBuilder() {

    const container =
        document.getElementById(
            "portfolioBuilder"
        );


    if (!container) {

        console.warn(
            "Portfolio Builder container not found."
        );

        return;

    }


    renderPortfolioBuilder();

}


window.initializePortfolioBuilder =
    initializePortfolioBuilder;


// ============================================================
// RENDER BUILDER
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

        <div class="portfolio-header">

            <div>

                <h2>
                    Portfolio Builder
                </h2>

                <p>
                    Build a diversified portfolio using
                    the dashboard's ranked trade plans.
                </p>

            </div>

            <div class="portfolio-engine-badge">
                ENGINE TRADE PLANS
            </div>

        </div>


        <div class="portfolio-controls">


            <div class="portfolio-control">

                <label for="portfolioAmount">
                    Portfolio Amount
                </label>

                <input
                    id="portfolioAmount"
                    type="number"
                    min="10000"
                    step="1000"
                    value="100000"
                >

            </div>


            <div class="portfolio-control">

                <label for="portfolioStockCount">
                    Number of Stocks
                </label>

                <input
                    id="portfolioStockCount"
                    type="number"
                    min="1"
                    max="25"
                    step="1"
                    value="10"
                >

            </div>


            <div class="portfolio-control">

                <label for="portfolioMinScore">
                    Minimum Score
                </label>

                <input
                    id="portfolioMinScore"
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value="50"
                >

            </div>


            <div class="portfolio-control">

                <label for="portfolioMaxRisk">
                    Max Risk / Stock %
                </label>

                <input
                    id="portfolioMaxRisk"
                    type="number"
                    min="0.25"
                    max="10"
                    step="0.25"
                    value="2"
                >

            </div>


            <div class="portfolio-actions">

                <button
                    id="calculatePortfolio"
                    class="portfolio-build-button"
                    type="button"
                >
                    Build Portfolio
                </button>

                <button
                    id="exportPortfolioButton"
                    class="portfolio-export-button"
                    type="button"
                    disabled
                >
                    Export Excel
                </button>

            </div>

        </div>


        <div
            id="portfolioOutput"
        >

            <div class="empty-state">

                Set your portfolio parameters and click
                <strong>Build Portfolio</strong>.

            </div>

        </div>

    `;


    bindPortfolioEvents();

}


// ============================================================
// EVENTS
// ============================================================

function bindPortfolioEvents() {

    const buildButton =
        document.getElementById(
            "calculatePortfolio"
        );


    const exportButton =
        document.getElementById(
            "exportPortfolioButton"
        );


    if (buildButton) {

        buildButton.addEventListener(
            "click",
            buildPortfolio
        );

    }


    if (exportButton) {

        exportButton.addEventListener(
            "click",
            exportPortfolio
        );

    }

}


// ============================================================
// BUILD PORTFOLIO
// ============================================================

function buildPortfolio() {

    const amountInput =
        document.getElementById(
            "portfolioAmount"
        );


    const countInput =
        document.getElementById(
            "portfolioStockCount"
        );


    const scoreInput =
        document.getElementById(
            "portfolioMinScore"
        );


    const riskInput =
        document.getElementById(
            "portfolioMaxRisk"
        );


    const output =
        document.getElementById(
            "portfolioOutput"
        );


    if (!output) {
        return;
    }


    const amount =
        Number(
            amountInput?.value
        );


    const count =
        Number(
            countInput?.value
        );


    const minimumScore =
        Number(
            scoreInput?.value
        );


    const maxRiskPercent =
        Number(
            riskInput?.value
        );


    // --------------------------------------------------------
    // VALIDATION
    // --------------------------------------------------------

    if (
        !Number.isFinite(amount)
        ||
        amount <= 0
    ) {

        output.innerHTML = `

            <div class="error-state">
                Please enter a valid portfolio amount.
            </div>

        `;

        return;

    }


    if (
        !Number.isFinite(count)
        ||
        count < 1
    ) {

        output.innerHTML = `

            <div class="error-state">
                Number of stocks must be at least 1.
            </div>

        `;

        return;

    }


    if (
        !Number.isFinite(minimumScore)
        ||
        minimumScore < 0
        ||
        minimumScore > 100
    ) {

        output.innerHTML = `

            <div class="error-state">
                Minimum score must be between 0 and 100.
            </div>

        `;

        return;

    }


    if (
        !Number.isFinite(maxRiskPercent)
        ||
        maxRiskPercent <= 0
    ) {

        output.innerHTML = `

            <div class="error-state">
                Maximum risk per stock must be greater than zero.
            </div>

        `;

        return;

    }


    // --------------------------------------------------------
    // SHOW PROCESSING
    // --------------------------------------------------------

    output.innerHTML = `

        <div class="loading-state">

            Analysing ranked stocks and trade plans...

        </div>

    `;


    // --------------------------------------------------------
    // GET CANDIDATES
    // --------------------------------------------------------

    const candidates =
        getPortfolioCandidates(
            minimumScore
        );


    if (
        candidates.length === 0
    ) {

        portfolioResult =
            null;


        output.innerHTML = `

            <div class="error-state">

                No suitable stocks were found with
                the current score and trade-plan filters.

                <br><br>

                Try reducing the minimum score or
                selecting fewer stocks.

            </div>

        `;


        disableExport();

        return;

    }


    // --------------------------------------------------------
    // SELECT DIVERSIFIED STOCKS
    // --------------------------------------------------------

    const selected =
        selectPortfolioStocks(
            candidates,
            count
        );


    if (
        selected.length === 0
    ) {

        output.innerHTML = `

            <div class="error-state">

                Portfolio could not be constructed
                from the available qualified setups.

            </div>

        `;


        disableExport();

        return;

    }


    // --------------------------------------------------------
    // ALLOCATE
    // --------------------------------------------------------

    const portfolio =
        calculatePortfolioAllocation(
            selected,
            amount,
            maxRiskPercent
        );


    portfolioResult =
        portfolio;


    // --------------------------------------------------------
    // RENDER
    // --------------------------------------------------------

    renderPortfolioResult(
        portfolio
    );


    enableExport();

}


// ============================================================
// CANDIDATES
// ============================================================

function getPortfolioCandidates(
    minimumScore
) {

    if (
        typeof dashboardData ===
        "undefined"
        ||
        !dashboardData
    ) {

        console.error(
            "dashboardData unavailable."
        );

        return [];

    }


    const stocks =
        Array.isArray(
            dashboardData.stocks
        )
            ?
            dashboardData.stocks
            :
            [];


    const candidates = [];


    stocks.forEach(
        stock => {

            if (!stock) {
                return;
            }


            const score =
                Number(
                    firstValue(
                        stock.overall_score,
                        stock.score
                    )
                );


            const price =
                Number(
                    firstValue(
                        stock.price,
                        stock.close
                    )
                );


            const entry =
                getTradeValue(
                    stock,
                    [
                        "entry_price",
                        "entry",
                        "Entry_Price"
                    ]
                );


            const stop =
                getTradeValue(
                    stock,
                    [
                        "stop_loss",
                        "stop",
                        "Stop_Loss"
                    ]
                );


            const target1 =
                getTradeValue(
                    stock,
                    [
                        "target_1",
                        "target1",
                        "Target_1"
                    ]
                );


            const target2 =
                getTradeValue(
                    stock,
                    [
                        "target_2",
                        "target2",
                        "Target_2"
                    ]
                );


            const rr =
                Number(
                    firstValue(
                        stock.risk_reward_1,
                        stock.risk_reward
                    )
                );


            // ------------------------------------------------
            // Basic validity
            // ------------------------------------------------

            if (
                !Number.isFinite(
                    score
                )
            ) {
                return;
            }


            if (
                score < minimumScore
            ) {
                return;
            }


            if (
                !Number.isFinite(
                    price
                )
                ||
                price <= 0
            ) {
                return;
            }


            // ------------------------------------------------
            // Must have engine trade plan
            // ------------------------------------------------

            if (
                !Number.isFinite(
                    entry
                )
                ||
                !Number.isFinite(
                    stop
                )
                ||
                !Number.isFinite(
                    target1
                )
            ) {

                return;

            }


            // ------------------------------------------------
            // Never accept invalid plan geometry
            // ------------------------------------------------

            if (
                stop >= entry
            ) {
                return;
            }


            if (
                target1 <= entry
            ) {
                return;
            }


            // ------------------------------------------------
            // R:R filter
            // ------------------------------------------------

            if (
                Number.isFinite(
                    rr
                )
                &&
                rr < 1.5
            ) {

                return;

            }


            // ------------------------------------------------
            // Reject weak / avoid
            // ------------------------------------------------

            const setup =
                String(
                    firstValue(
                        stock.setup,
                        stock.trade_plan_type,
                        ""
                    )
                ).toLowerCase();


            const status =
                String(
                    firstValue(
                        stock.trade_plan_status,
                        ""
                    )
                ).toLowerCase();


            if (
                setup.includes(
                    "weak"
                )
                ||
                setup.includes(
                    "avoid"
                )
                ||
                status.includes(
                    "avoid"
                )
            ) {

                return;

            }


            // ------------------------------------------------
            // Prefer stocks above 200 DMA when available
            // ------------------------------------------------

            const above200 =
                stock.above_200dma;


            const sma200 =
                Number(
                    stock.sma200
                );


            const above200Score =
                above200 === true
                ||
                (
                    Number.isFinite(
                        sma200
                    )
                    &&
                    price > sma200
                )
                    ? 1
                    : 0;


            // ------------------------------------------------
            // Trade quality
            // ------------------------------------------------

            const tradeQuality =
                String(
                    stock.trade_plan_quality ||
                    ""
                ).toLowerCase();


            let qualityScore = 0;


            if (
                tradeQuality.includes(
                    "strong"
                )
            ) {

                qualityScore = 3;

            }
            else if (
                tradeQuality.includes(
                    "acceptable"
                )
            ) {

                qualityScore = 2;

            }
            else if (
                tradeQuality.includes(
                    "poor"
                )
            ) {

                qualityScore = 0;

            }
            else {

                qualityScore = 1;

            }


            // ------------------------------------------------
            // Composite portfolio ranking
            // ------------------------------------------------

            const technical =
                Number(
                    stock.technical_score
                ) || 0;


            const fundamental =
                Number(
                    stock.fundamental_score
                ) || 0;


            const sector =
                Number(
                    stock.sector_score
                ) || 0;


            const rankingScore =

                score * 0.50

                +

                technical * 0.15

                +

                fundamental * 0.15

                +

                sector * 0.05

                +

                qualityScore * 5

                +

                above200Score * 5;


            candidates.push({

                ...stock,

                _price:
                    price,

                _entry:
                    entry,

                _stop:
                    stop,

                _target1:
                    target1,

                _target2:
                    Number.isFinite(
                        target2
                    )
                        ? target2
                        : null,

                _rr:
                    Number.isFinite(
                        rr
                    )
                        ? rr
                        : calculateRiskReward(
                            entry,
                            stop,
                            target1
                        ),

                _rankingScore:
                    rankingScore

            });

        }
    );


    candidates.sort(
        (
            a,
            b
        ) =>
            b._rankingScore
            -
            a._rankingScore
    );


    return candidates;

}


// ============================================================
// DIVERSIFICATION
// ============================================================

function selectPortfolioStocks(
    candidates,
    desiredCount
) {

    const selected = [];

    const sectorCounts = {};


    // --------------------------------------------------------
    // First pass:
    // maximum 2 stocks per sector
    // --------------------------------------------------------

    for (
        const stock of candidates
    ) {

        if (
            selected.length >=
            desiredCount
        ) {

            break;

        }


        const sector =
            normalizeSector(
                stock
            );


        const count =
            sectorCounts[
                sector
            ] || 0;


        if (
            count >= 2
        ) {

            continue;

        }


        selected.push(
            stock
        );


        sectorCounts[
            sector
        ] =
            count + 1;

    }


    // --------------------------------------------------------
    // Second pass:
    // fill remaining slots if needed
    // --------------------------------------------------------

    if (
        selected.length <
        desiredCount
    ) {

        for (
            const stock of candidates
        ) {

            if (
                selected.length >=
                desiredCount
            ) {

                break;

            }


            const symbol =
                getSymbol(
                    stock
                );


            const exists =
                selected.some(
                    item =>
                        getSymbol(
                            item
                        ) ===
                        symbol
                );


            if (
                exists
            ) {

                continue;

            }


            selected.push(
                stock
            );

        }

    }


    return selected;

}


// ============================================================
// PORTFOLIO ALLOCATION
// ============================================================

function calculatePortfolioAllocation(
    stocks,
    amount,
    maxRiskPercent
) {

    const count =
        stocks.length;


    const equalCapital =
        amount /
        count;


    const rows =
        stocks.map(
            stock => {

                const entry =
                    stock._entry;


                const stop =
                    stock._stop;


                const target1 =
                    stock._target1;


                const target2 =
                    stock._target2;


                const riskPerShare =
                    Math.max(
                        0,
                        entry -
                        stop
                    );


                let quantity =
                    Math.floor(
                        equalCapital /
                        entry
                    );


                /*
                 * Risk cap:
                 *
                 * Maximum permitted rupee risk
                 * for this stock.
                 */

                const maximumRisk =
                    amount *
                    (
                        maxRiskPercent /
                        100
                    );


                if (
                    riskPerShare > 0
                ) {

                    const riskBasedQuantity =
                        Math.floor(
                            maximumRisk /
                            riskPerShare
                        );


                    if (
                        riskBasedQuantity >
                        0
                    ) {

                        quantity =
                            Math.min(
                                quantity,
                                riskBasedQuantity
                            );

                    }

                }


                /*
                 * Make sure we never
                 * allocate more than the
                 * available capital.
                 */

                const investment =
                    quantity *
                    entry;


                const risk =
                    quantity *
                    riskPerShare;


                const reward1 =
                    quantity *
                    Math.max(
                        0,
                        target1 -
                        entry
                    );


                const reward2 =
                    quantity *
                    Math.max(
                        0,
                        (
                            Number.isFinite(
                                target2
                            )
                                ? target2
                                : target1
                        )
                        -
                        entry
                    );


                return {

                    ...stock,

                    quantity:
                        quantity,

                    investment:
                        investment,

                    allocation_pct:
                        (
                            investment /
                            amount *
                            100
                        ),

                    risk_amount:
                        risk,

                    reward1_amount:
                        reward1,

                    reward2_amount:
                        reward2,

                    risk_reward_1:
                        calculateRiskReward(
                            entry,
                            stop,
                            target1
                        ),

                    risk_reward_2:
                        Number.isFinite(
                            target2
                        )
                            ?
                            calculateRiskReward(
                                entry,
                                stop,
                                target2
                            )
                            :
                            null

                };

            }
        );


    const totalInvestment =
        rows.reduce(
            (
                total,
                row
            ) =>
                total +
                row.investment,
            0
        );


    const totalRisk =
        rows.reduce(
            (
                total,
                row
            ) =>
                total +
                row.risk_amount,
            0
        );


    const totalReward1 =
        rows.reduce(
            (
                total,
                row
            ) =>
                total +
                row.reward1_amount,
            0
        );


    const totalReward2 =
        rows.reduce(
            (
                total,
                row
            ) =>
                total +
                row.reward2_amount,
            0
        );


    const unusedCapital =
        Math.max(
            0,
            amount -
            totalInvestment
        );


    const portfolioRiskPct =
        amount > 0
            ?
            (
                totalRisk /
                amount *
                100
            )
            :
            0;


    const portfolioReward1Pct =
        amount > 0
            ?
            (
                totalReward1 /
                amount *
                100
            )
            :
            0;


    const portfolioReward2Pct =
        amount > 0
            ?
            (
                totalReward2 /
                amount *
                100
            )
            :
            0;


    return {

        amount:
            amount,

        requested_count:
            count,

        stocks:
            rows,

        total_investment:
            totalInvestment,

        unused_capital:
            unusedCapital,

        total_risk:
            totalRisk,

        total_reward1:
            totalReward1,

        total_reward2:
            totalReward2,

        portfolio_risk_pct:
            portfolioRiskPct,

        portfolio_reward1_pct:
            portfolioReward1Pct,

        portfolio_reward2_pct:
            portfolioReward2Pct

    };

}


// ============================================================
// RENDER RESULT
// ============================================================

function renderPortfolioResult(
    portfolio
) {

    const output =
        document.getElementById(
            "portfolioOutput"
        );


    if (!output) {
        return;
    }


    output.innerHTML = `

        <div class="portfolio-summary">

            <div class="portfolio-summary-grid">

                ${portfolioMetric(
                    "Stocks",
                    portfolio.stocks.length
                )}

                ${portfolioMetric(
                    "Capital",
                    formatMoney(
                        portfolio.amount
                    )
                )}

                ${portfolioMetric(
                    "Invested",
                    formatMoney(
                        portfolio.total_investment
                    )
                )}

                ${portfolioMetric(
                    "Unused",
                    formatMoney(
                        portfolio.unused_capital
                    )
                )}

                ${portfolioMetric(
                    "Max Portfolio Risk",
                    formatMoney(
                        portfolio.total_risk
                    ),
                    formatPercent(
                        portfolio.portfolio_risk_pct
                    )
                )}

                ${portfolioMetric(
                    "Reward @ T1",
                    formatMoney(
                        portfolio.total_reward1
                    ),
                    formatPercent(
                        portfolio.portfolio_reward1_pct
                    )
                )}

                ${portfolioMetric(
                    "Reward @ T2",
                    formatMoney(
                        portfolio.total_reward2
                    ),
                    formatPercent(
                        portfolio.portfolio_reward2_pct
                    )
                )}

                ${portfolioMetric(
                    "Avg Score",
                    formatNumber(
                        averageScore(
                            portfolio.stocks
                        )
                    )
                )}

            </div>

        </div>


        <div class="portfolio-table-container">

            <div class="portfolio-table-wrapper">

                <table class="dashboard-table portfolio-table">

                    <thead>

                        <tr>

                            <th>
                                #
                            </th>

                            <th>
                                Stock
                            </th>

                            <th>
                                Score
                            </th>

                            <th>
                                Setup
                            </th>

                            <th>
                                Entry
                            </th>

                            <th>
                                Stop Loss
                            </th>

                            <th>
                                Target 1
                            </th>

                            <th>
                                Target 2
                            </th>

                            <th>
                                R:R
                            </th>

                            <th>
                                Qty
                            </th>

                            <th>
                                Investment
                            </th>

                            <th>
                                Allocation
                            </th>

                            <th>
                                Risk
                            </th>

                            <th>
                                Sector
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        ${
                            portfolio.stocks
                                .map(
                                    (
                                        stock,
                                        index
                                    ) =>
                                        renderPortfolioRow(
                                            stock,
                                            index + 1
                                        )
                                )
                                .join("")
                        }

                    </tbody>

                </table>

            </div>

        </div>


        <div class="portfolio-notes">

            <div class="portfolio-disclaimer">

                <strong>
                    Portfolio construction logic
                </strong>

                <ul>

                    <li>
                        Entry, Stop Loss and Targets are taken
                        from the ranking engine's setup-specific
                        trade plan.
                    </li>

                    <li>
                        No blanket 10% stop-loss is used.
                    </li>

                    <li>
                        Stocks with unavailable or invalid
                        trade plans are excluded.
                    </li>

                    <li>
                        Portfolio selection initially limits
                        exposure to a maximum of two stocks
                        from the same sector.
                    </li>

                    <li>
                        Actual execution should consider
                        liquidity, slippage and current market
                        conditions.
                    </li>

                </ul>

                <p class="risk-warning">

                    This portfolio is a model allocation for
                    research and educational purposes only.
                    It is not investment advice.

                </p>

            </div>

        </div>

    `;


    bindPortfolioStockRows();

}


// ============================================================
// PORTFOLIO METRIC
// ============================================================

function portfolioMetric(
    label,
    value,
    small = ""
) {

    return `

        <div class="portfolio-metric">

            <span>
                ${escapeHtml(
                    label
                )}
            </span>

            <strong>
                ${escapeHtml(
                    String(value)
                )}
            </strong>

            ${
                small

                    ?

                    `
                        <small>
                            ${escapeHtml(
                                String(
                                    small
                                )
                            )}
                        </small>
                    `

                    :

                    ""
            }

        </div>

    `;

}


// ============================================================
// PORTFOLIO ROW
// ============================================================

function renderPortfolioRow(
    stock,
    rank
) {

    const symbol =
        getSymbol(
            stock
        );


    return `

        <tr
            class="portfolio-stock-row"
            data-symbol="${escapeHtml(
                symbol
            )}"
        >

            <td>
                ${rank}
            </td>


            <td>

                <div class="stock-symbol">
                    ${escapeHtml(
                        symbol
                    )}
                </div>

                <small>
                    ${escapeHtml(
                        stock.company_name ||
                        ""
                    )}
                </small>

            </td>


            <td>
                <strong>
                    ${formatNumber(
                        stock.overall_score
                    )}
                </strong>
            </td>


            <td>
                ${statusBadge(
                    stock.setup ||
                    stock.trade_plan_type
                )}
            </td>


            <td class="trade-entry">
                ${formatMoney(
                    stock._entry
                )}
            </td>


            <td class="trade-stop">
                ${formatMoney(
                    stock._stop
                )}
            </td>


            <td class="trade-target">
                ${formatMoney(
                    stock._target1
                )}
            </td>


            <td class="trade-target">
                ${
                    Number.isFinite(
                        stock._target2
                    )
                        ?
                        formatMoney(
                            stock._target2
                        )
                        :
                        "—"
                }
            </td>


            <td class="${riskRewardClass(
                stock._rr
            )}">
                ${formatRiskReward(
                    stock._rr
                )}
            </td>


            <td>
                ${formatInteger(
                    stock.quantity
                )}
            </td>


            <td>
                ${formatMoney(
                    stock.investment
                )}
            </td>


            <td>
                ${formatPercent(
                    stock.allocation_pct
                )}
            </td>


            <td class="negative">
                ${formatMoney(
                    stock.risk_amount
                )}
            </td>


            <td>
                ${escapeHtml(
                    normalizeSector(
                        stock
                    )
                )}
            </td>

        </tr>

    `;

}


// ============================================================
// STOCK ROW EVENTS
// ============================================================

function bindPortfolioStockRows() {

    const rows =
        document.querySelectorAll(
            ".portfolio-stock-row"
        );


    rows.forEach(
        row => {

            row.addEventListener(
                "click",
                () => {

                    const symbol =
                        row.dataset.symbol;


                    if (
                        typeof openStockDetail ===
                        "function"
                    ) {

                        openStockDetail(
                            symbol
                        );

                    }
                    else if (
                        typeof openPortfolioStock ===
                        "function"
                    ) {

                        openPortfolioStock(
                            symbol
                        );

                    }

                }
            );

        }
    );

}


function openPortfolioStock(
    symbol
) {

    if (
        typeof openStockDetail ===
        "function"
    ) {

        openStockDetail(
            symbol
        );

    }

}


window.openPortfolioStock =
    openPortfolioStock;


// ============================================================
// EXPORT
// ============================================================

function exportPortfolio() {

    if (
        !portfolioResult
        ||
        !Array.isArray(
            portfolioResult.stocks
        )
        ||
        portfolioResult.stocks.length === 0
    ) {

        return;

    }


    const rows =
        portfolioResult.stocks.map(
            (
                stock,
                index
            ) => ({

                Rank:
                    index + 1,

                Symbol:
                    getSymbol(
                        stock
                    ),

                Company:
                    stock.company_name ||
                    "",

                Sector:
                    normalizeSector(
                        stock
                    ),

                Score:
                    stock.overall_score,

                Setup:
                    stock.setup ||
                    stock.trade_plan_type ||
                    "",

                Entry:
                    stock._entry,

                Stop_Loss:
                    stock._stop,

                Target_1:
                    stock._target1,

                Target_2:
                    stock._target2,

                Risk_Reward:
                    stock._rr,

                Quantity:
                    stock.quantity,

                Investment:
                    stock.investment,

                Allocation_Percent:
                    stock.allocation_pct,

                Risk:
                    stock.risk_amount,

                Reward_Target_1:
                    stock.reward1_amount,

                Reward_Target_2:
                    stock.reward2_amount

            })
        );


    // --------------------------------------------------------
    // SheetJS if available
    // --------------------------------------------------------

    if (
        typeof XLSX !==
        "undefined"
    ) {

        const worksheet =
            XLSX.utils.json_to_sheet(
                rows
            );


        const workbook =
            XLSX.utils.book_new();


        XLSX.utils.book_append_sheet(
            workbook,
            worksheet,
            "Portfolio"
        );


        XLSX.writeFile(
            workbook,
            "NSE_Smart_Portfolio.xlsx"
        );


        return;

    }


    // --------------------------------------------------------
    // CSV fallback
    // --------------------------------------------------------

    const csv =
        convertToCSV(
            rows
        );


    const blob =
        new Blob(
            [
                csv
            ],
            {
                type:
                    "text/csv;charset=utf-8;"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement(
            "a"
        );


    link.href =
        url;


    link.download =
        "NSE_Smart_Portfolio.csv";


    document.body.appendChild(
        link
    );


    link.click();


    link.remove();


    URL.revokeObjectURL(
        url
    );

}


window.exportPortfolio =
    exportPortfolio;


// ============================================================
// ENABLE / DISABLE EXPORT
// ============================================================

function enableExport() {

    const button =
        document.getElementById(
            "exportPortfolioButton"
        );


    if (button) {

        button.disabled =
            false;

    }

}


function disableExport() {

    const button =
        document.getElementById(
            "exportPortfolioButton"
        );


    if (button) {

        button.disabled =
            true;

    }

}


// ============================================================
// CSV
// ============================================================

function convertToCSV(
    rows
) {

    if (
        !rows.length
    ) {

        return "";

    }


    const headers =
        Object.keys(
            rows[0]
        );


    const lines = [

        headers.join(",")

    ];


    rows.forEach(
        row => {

            const values =
                headers.map(
                    header =>
                        csvEscape(
                            row[
                                header
                            ]
                        )
                );


            lines.push(
                values.join(",")
            );

        }
    );


    return lines.join(
        "\n"
    );

}


function csvEscape(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    const text =
        String(
            value
        );


    if (
        text.includes(",")
        ||
        text.includes('"')
        ||
        text.includes("\n")
    ) {

        return (

            '"' +

            text.replace(
                /"/g,
                '""'
            )

            +

            '"'

        );

    }


    return text;

}


// ============================================================
// HELPERS
// ============================================================

function getSymbol(
    stock
) {

    return String(
        firstValue(
            stock.symbol,
            stock.nse_symbol,
            stock.Symbol,
            ""
        )
    );

}


function normalizeSector(
    stock
) {

    return String(
        firstValue(
            stock.primary_sector,
            stock.sector,
            stock.Sector,
            "Unknown"
        )
    );

}


function getTradeValue(
    stock,
    fields
) {

    for (
        const field of fields
    ) {

        const value =
            Number(
                stock[
                    field
                ]
            );


        if (
            Number.isFinite(
                value
            )
        ) {

            return value;

        }

    }


    return null;

}


function calculateRiskReward(
    entry,
    stop,
    target
) {

    if (
        !Number.isFinite(
            entry
        )
        ||
        !Number.isFinite(
            stop
        )
        ||
        !Number.isFinite(
            target
        )
    ) {

        return null;

    }


    const risk =
        entry -
        stop;


    const reward =
        target -
        entry;


    if (
        risk <= 0
        ||
        reward <= 0
    ) {

        return null;

    }


    return (
        reward /
        risk
    );

}


function averageScore(
    stocks
) {

    if (
        !stocks.length
    ) {

        return null;

    }


    const scores =
        stocks
            .map(
                stock =>
                    Number(
                        stock.overall_score
                    )
            )
            .filter(
                Number.isFinite
            );


    if (
        !scores.length
    ) {

        return null;

    }


    return (
        scores.reduce(
            (
                sum,
                value
            ) =>
                sum +
                value,
            0
        )
        /
        scores.length
    );

}


function firstValue(
    ...values
) {

    for (
        const value of values
    ) {

        if (
            value !== undefined
            &&
            value !== null
            &&
            value !== ""
        ) {

            return value;

        }

    }


    return null;

}


// ============================================================
// FORMATTING
// ============================================================

function formatMoney(
    value
) {

    if (
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    return (

        "₹" +

        Number(
            value
        ).toLocaleString(
            "en-IN",
            {
                minimumFractionDigits:
                    2,

                maximumFractionDigits:
                    2
            }
        )

    );

}


function formatNumber(
    value
) {

    if (
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    return Number(
        value
    ).toLocaleString(
        "en-IN",
        {
            minimumFractionDigits:
                2,

            maximumFractionDigits:
                2
        }
    );

}


function formatInteger(
    value
) {

    if (
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    return Number(
        value
    ).toLocaleString(
        "en-IN",
        {
            maximumFractionDigits:
                0
        }
    );

}


function formatPercent(
    value
) {

    if (
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    return (

        Number(
            value
        ).toFixed(2)

        +

        "%"

    );

}


function formatRiskReward(
    value
) {

    if (
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    return (

        "1:" +

        Number(
            value
        ).toFixed(2)

    );

}


function riskRewardClass(
    value
) {

    if (
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "neutral";

    }


    const rr =
        Number(value);


    if (
        rr >= 2
    ) {

        return "positive";

    }


    if (
        rr >= 1.5
    ) {

        return "neutral";

    }


    return "negative";

}


function statusBadge(
    value
) {

    if (
        value === undefined
        ||
        value === null
        ||
        value === ""
    ) {

        return "—";

    }


    const text =
        String(
            value
        );


    const lower =
        text.toLowerCase();


    let className =
        "badge-neutral";


    if (
        lower.includes(
            "strong"
        )
        ||
        lower.includes(
            "confirmed"
        )
        ||
        lower.includes(
            "bullish"
        )
        ||
        lower.includes(
            "positive"
        )
        ||
        lower.includes(
            "breakout"
        )
    ) {

        className =
            "badge-positive";

    }
    else if (
        lower.includes(
            "avoid"
        )
        ||
        lower.includes(
            "weak"
        )
        ||
        lower.includes(
            "bearish"
        )
    ) {

        className =
            "badge-negative";

    }


    return `

        <span
            class="status-badge ${className}"
        >
            ${escapeHtml(
                text
            )}
        </span>

    `;

}


function escapeHtml(
    value
) {

    if (
        value === undefined
        ||
        value === null
    ) {

        return "";

    }


    return String(
        value
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}

// ============================================================
// NSE SMART MARKET DASHBOARD V2.1
// PORTFOLIO BUILDER
// Created by Rakesh Nagapuri
// ============================================================

let portfolioInitialized = false;

// ============================================================
// INITIALIZE
// ============================================================

function initializePortfolioBuilder() {
    if (portfolioInitialized) return;

    const container =
        document.getElementById("portfolioBuilder");

    if (!container) {
        console.warn(
            "Portfolio Builder container not found."
        );
        return;
    }

    portfolioInitialized = true;

    renderPortfolioBuilder();
}

// ============================================================
// MAIN UI
// ============================================================

function renderPortfolioBuilder() {
    const container =
        document.getElementById(
            "portfolioBuilder"
        );

    if (!container) return;

    container.innerHTML = `

        <div class="portfolio-builder">

            <div class="portfolio-header">

                <div>
                    <h2>
                        Portfolio Builder
                    </h2>

                    <p>
                        Build a diversified portfolio
                        using the dashboard's ranked
                        stocks and engine-generated
                        trade plans.
                    </p>
                </div>

                <div class="portfolio-engine-badge">
                    V2.1 ENGINE
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
                        min="1000"
                        step="1000"
                        value="100000"
                    >

                </div>

                <div class="portfolio-control">

                    <label for="portfolioStockCount">
                        Number of Stocks
                    </label>

                    <select id="portfolioStockCount">

                        <option value="5">
                            5
                        </option>

                        <option value="10" selected>
                            10
                        </option>

                        <option value="15">
                            15
                        </option>

                        <option value="20">
                            20
                        </option>

                    </select>

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
                        min="0.1"
                        max="20"
                        step="0.1"
                        value="2"
                    >

                </div>

                <div class="portfolio-actions">

                    <button
                        id="buildPortfolioBtn"
                        class="portfolio-build-button"
                        type="button"
                    >
                        Build Portfolio
                    </button>

                    <button
                        id="exportPortfolioBtn"
                        class="portfolio-export-button"
                        type="button"
                    >
                        Export Excel
                    </button>

                </div>

            </div>

            <div
                id="portfolioSummary"
                class="portfolio-summary"
            ></div>

            <div
                id="portfolioTable"
                class="portfolio-table-container"
            ></div>

            <div
                id="portfolioNotes"
                class="portfolio-notes"
            ></div>

        </div>
    `;

    bindPortfolioEvents();

    buildPortfolio();
}

// ============================================================
// EVENTS
// ============================================================

function bindPortfolioEvents() {
    const buildButton =
        document.getElementById(
            "buildPortfolioBtn"
        );

    const exportButton =
        document.getElementById(
            "exportPortfolioBtn"
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
    if (
        typeof dashboardData ===
        "undefined" ||
        !dashboardData
    ) {
        showPortfolioMessage(
            "Dashboard data is still loading."
        );

        return;
    }

    const amount =
        getInputNumber(
            "portfolioAmount",
            100000
        );

    const stockCount =
        getInputNumber(
            "portfolioStockCount",
            10
        );

    const minimumScore =
        getInputNumber(
            "portfolioMinScore",
            50
        );

    const maxRiskPct =
        getInputNumber(
            "portfolioMaxRisk",
            2
        );

    if (amount <= 0) {
        showPortfolioMessage(
            "Please enter a valid portfolio amount."
        );

        return;
    }

    const candidates =
        getPortfolioCandidates(
            minimumScore
        );

    if (candidates.length === 0) {
        renderPortfolioEmptyState();
        return;
    }

    const selected =
        selectPortfolioStocks(
            candidates,
            stockCount
        );

    const portfolio =
        calculatePortfolio(
            selected,
            amount,
            maxRiskPct
        );

    renderPortfolioSummary(
        portfolio
    );

    renderPortfolioTable(
        portfolio
    );

    renderPortfolioNotes(
        portfolio
    );
}

// ============================================================
// CANDIDATES
// ============================================================

function getPortfolioCandidates(
    minimumScore
) {
    const stocks =
        Array.isArray(
            dashboardData.stocks
        )
            ? dashboardData.stocks
            : [];

    return stocks
        .map(normalizePortfolioStock)
        .filter(stock => {

            if (
                !stock.symbol
            ) {
                return false;
            }

            if (
                !isFiniteNumber(
                    stock.price
                ) ||
                stock.price <= 0
            ) {
                return false;
            }

            if (
                !isFiniteNumber(
                    stock.overall_score
                )
            ) {
                return false;
            }

            if (
                stock.overall_score <
                minimumScore
            ) {
                return false;
            }

            /*
             * Portfolio Builder should prefer
             * stocks that are technically healthy.
             */
            if (
                stock.sma200 &&
                stock.price <
                stock.sma200
            ) {
                return false;
            }

            /*
             * Avoid Weak / Avoid setups.
             */
            const setup =
                String(
                    stock.setup || ""
                ).toLowerCase();

            if (
                setup.includes("weak") ||
                setup.includes("avoid")
            ) {
                return false;
            }

            /*
             * Portfolio Builder should use
             * engine-generated trade plans.
             *
             * We do NOT create our own
             * 10% stop-loss here.
             */
            if (
                !isFiniteNumber(
                    stock.stop_loss
                )
            ) {
                return false;
            }

            if (
                !isFiniteNumber(
                    stock.entry_price
                )
            ) {
                return false;
            }

            if (
                !isFiniteNumber(
                    stock.target_1
                )
            ) {
                return false;
            }

            /*
             * Require a usable risk/reward
             * where available.
             */
            if (
                isFiniteNumber(
                    stock.risk_reward_1
                ) &&
                stock.risk_reward_1 < 1.5
            ) {
                return false;
            }

            return true;
        })
        .sort(
            portfolioRankingComparator
        );
}

function normalizePortfolioStock(
    stock
) {
    const entryPrice =
        firstNumber(
            stock.entry_price,
            stock.entry,
            stock.Entry_Price
        );

    const entryLow =
        firstNumber(
            stock.entry_low,
            stock.Entry_Low
        );

    const entryHigh =
        firstNumber(
            stock.entry_high,
            stock.Entry_High
        );

    const stopLoss =
        firstNumber(
            stock.stop_loss,
            stock.stop,
            stock.Stop_Loss
        );

    const target1 =
        firstNumber(
            stock.target_1,
            stock.target1,
            stock.Target_1
        );

    const target2 =
        firstNumber(
            stock.target_2,
            stock.target2,
            stock.Target_2
        );

    const rr1 =
        firstNumber(
            stock.risk_reward_1,
            stock.risk_reward
        );

    const rr2 =
        firstNumber(
            stock.risk_reward_2
        );

    return {
        ...stock,

        symbol:
            stock.symbol ||
            stock.nse_symbol ||
            "",

        company_name:
            stock.company_name ||
            "",

        price:
            firstNumber(
                stock.price,
                stock.close
            ),

        overall_score:
            firstNumber(
                stock.overall_score,
                stock.rating
            ) || 0,

        technical_score:
            firstNumber(
                stock.technical_score
            ) || 0,

        fundamental_score:
            firstNumber(
                stock.fundamental_score
            ) || 0,

        sector_score:
            firstNumber(
                stock.sector_score
            ) || 0,

        entry_price:
            entryPrice,

        entry_low:
            entryLow,

        entry_high:
            entryHigh,

        stop_loss:
            stopLoss,

        target_1:
            target1,

        target_2:
            target2,

        risk_reward_1:
            rr1,

        risk_reward_2:
            rr2,

        trade_plan_type:
            stock.trade_plan_type ||
            "",

        trade_plan_status:
            stock.trade_plan_status ||
            "",

        trade_plan_quality:
            stock.trade_plan_quality ||
            "",

        trade_plan_reason:
            stock.trade_plan_reason ||
            "",

        invalidation:
            stock.invalidation ||
            "",

        setup:
            stock.setup ||
            "Neutral Watch",

        trend:
            stock.trend ||
            "",

        momentum:
            stock.momentum ||
            "",

        sector:
            stock.sector ||
            stock.primary_sector ||
            ""
    };
}

// ============================================================
// RANKING
// ============================================================

function portfolioRankingComparator(
    a,
    b
) {
    /*
     * Ranking priority:
     *
     * 1. Overall score
     * 2. Trade-plan quality
     * 3. R:R
     * 4. Technical score
     * 5. Fundamental score
     * 6. Sector score
     */

    const scoreDiff =
        Number(
            b.overall_score || 0
        ) -
        Number(
            a.overall_score || 0
        );

    if (
        Math.abs(scoreDiff) > 0.001
    ) {
        return scoreDiff;
    }

    const qualityDiff =
        tradeQualityRank(
            b.trade_plan_quality
        ) -
        tradeQualityRank(
            a.trade_plan_quality
        );

    if (
        qualityDiff !== 0
    ) {
        return qualityDiff;
    }

    const rrDiff =
        Number(
            b.risk_reward_1 || 0
        ) -
        Number(
            a.risk_reward_1 || 0
        );

    if (
        Math.abs(rrDiff) > 0.001
    ) {
        return rrDiff;
    }

    const technicalDiff =
        Number(
            b.technical_score || 0
        ) -
        Number(
            a.technical_score || 0
        );

    if (
        Math.abs(technicalDiff) > 0.001
    ) {
        return technicalDiff;
    }

    const fundamentalDiff =
        Number(
            b.fundamental_score || 0
        ) -
        Number(
            a.fundamental_score || 0
        );

    if (
        Math.abs(fundamentalDiff) > 0.001
    ) {
        return fundamentalDiff;
    }

    return (
        Number(
            b.sector_score || 0
        ) -
        Number(
            a.sector_score || 0
        )
    );
}

function tradeQualityRank(
    quality
) {
    const text =
        String(
            quality || ""
        ).toLowerCase();

    if (
        text.includes("strong")
    ) {
        return 3;
    }

    if (
        text.includes("acceptable")
    ) {
        return 2;
    }

    if (
        text.includes("poor")
    ) {
        return 1;
    }

    return 0;
}

// ============================================================
// STOCK SELECTION
// ============================================================

function selectPortfolioStocks(
    candidates,
    count
) {
    const selected = [];

    const sectorCount = {};

    for (
        const stock of candidates
    ) {
        if (
            selected.length >= count
        ) {
            break;
        }

        const sector =
            stock.sector ||
            "Unknown";

        /*
         * Basic diversification:
         * do not initially take more than
         * 2 stocks from one sector.
         */
        const existing =
            sectorCount[sector] || 0;

        if (
            existing >= 2 &&
            candidates.length >= count * 2
        ) {
            continue;
        }

        selected.push(stock);

        sectorCount[sector] =
            existing + 1;
    }

    /*
     * If diversification prevented
     * reaching the requested count,
     * fill remaining slots by ranking.
     */
    if (
        selected.length < count
    ) {
        for (
            const stock of candidates
        ) {
            if (
                selected.length >= count
            ) {
                break;
            }

            const exists =
                selected.some(
                    item =>
                        item.symbol ===
                        stock.symbol
                );

            if (!exists) {
                selected.push(stock);
            }
        }
    }

    return selected;
}

// ============================================================
// PORTFOLIO CALCULATION
// ============================================================

function calculatePortfolio(
    stocks,
    amount,
    maxRiskPct
) {
    if (
        !stocks ||
        stocks.length === 0
    ) {
        return {
            stocks: [],
            amount,
            invested: 0,
            cash: amount,
            expectedProfitT1: 0,
            expectedProfitT2: 0,
            maximumLoss: 0,
            riskPercent: 0
        };
    }

    /*
     * Equal capital allocation.
     *
     * Trade plan itself determines:
     * Entry / SL / T1 / T2.
     *
     * The portfolio builder does NOT
     * overwrite those values.
     */
    const allocation =
        amount / stocks.length;

    const rows = [];

    let invested = 0;
    let expectedProfitT1 = 0;
    let expectedProfitT2 = 0;
    let maximumLoss = 0;

    for (
        const stock of stocks
    ) {
        const entry =
            stock.entry_price;

        const stop =
            stock.stop_loss;

        const target1 =
            stock.target_1;

        const target2 =
            stock.target_2;

        if (
            !isFiniteNumber(entry) ||
            !isFiniteNumber(stop) ||
            !isFiniteNumber(target1)
        ) {
            continue;
        }

        let quantity =
            Math.floor(
                allocation / entry
            );

        if (
            quantity < 1
        ) {
            quantity = 0;
        }

        const investment =
            quantity * entry;

        const riskPerShare =
            Math.max(
                0,
                entry - stop
            );

        const rewardT1PerShare =
            Math.max(
                0,
                target1 - entry
            );

        const rewardT2PerShare =
            isFiniteNumber(target2)
                ? Math.max(
                    0,
                    target2 - entry
                )
                : 0;

        const stockRisk =
            riskPerShare *
            quantity;

        const profitT1 =
            rewardT1PerShare *
            quantity;

        const profitT2 =
            rewardT2PerShare *
            quantity;

        const portfolioWeight =
            amount > 0
                ? investment /
                  amount *
                  100
                : 0;

        const riskPercent =
            amount > 0
                ? stockRisk /
                  amount *
                  100
                : 0;

        rows.push({
            ...stock,

            allocation:
                allocation,

            quantity:
                quantity,

            investment:
                investment,

            portfolio_weight:
                portfolioWeight,

            risk_per_share:
                riskPerShare,

            reward_t1_per_share:
                rewardT1PerShare,

            reward_t2_per_share:
                rewardT2PerShare,

            stock_risk:
                stockRisk,

            risk_percent:
                riskPercent,

            expected_profit_t1:
                profitT1,

            expected_profit_t2:
                profitT2
        });

        invested += investment;
        expectedProfitT1 +=
            profitT1;

        expectedProfitT2 +=
            profitT2;

        maximumLoss +=
            stockRisk;
    }

    const cash =
        Math.max(
            0,
            amount - invested
        );

    const riskPercent =
        amount > 0
            ? maximumLoss /
              amount *
              100
            : 0;

    /*
     * maxRiskPct is a portfolio-awareness
     * indicator, not a reason to distort
     * the engine's stop-loss.
     */
    return {
        stocks: rows,

        amount,

        allocation,

        invested,

        cash,

        expectedProfitT1,

        expectedProfitT2,

        maximumLoss,

        riskPercent,

        maxRiskPct,

        expectedReturnT1:
            invested > 0
                ? expectedProfitT1 /
                  invested *
                  100
                : 0,

        expectedReturnT2:
            invested > 0
                ? expectedProfitT2 /
                  invested *
                  100
                : 0,

        investmentUtilization:
            amount > 0
                ? invested /
                  amount *
                  100
                : 0
    };
}

// ============================================================
// SUMMARY
// ============================================================

function renderPortfolioSummary(
    portfolio
) {
    const container =
        document.getElementById(
            "portfolioSummary"
        );

    if (!container) return;

    const riskStatus =
        getRiskStatus(
            portfolio.riskPercent,
            portfolio.maxRiskPct
        );

    container.innerHTML = `

        <div class="portfolio-summary-grid">

            ${portfolioMetric(
                "Portfolio Value",
                formatMoney(
                    portfolio.amount
                ),
                "Capital"
            )}

            ${portfolioMetric(
                "Invested",
                formatMoney(
                    portfolio.invested
                ),
                formatPercent(
                    portfolio.investmentUtilization
                ) + " deployed"
            )}

            ${portfolioMetric(
                "Cash",
                formatMoney(
                    portfolio.cash
                ),
                "Unallocated"
            )}

            ${portfolioMetric(
                "Expected Profit T1",
                formatMoney(
                    portfolio.expectedProfitT1
                ),
                formatPercent(
                    portfolio.expectedReturnT1
                )
            )}

            ${portfolioMetric(
                "Expected Profit T2",
                formatMoney(
                    portfolio.expectedProfitT2
                ),
                formatPercent(
                    portfolio.expectedReturnT2
                )
            )}

            ${portfolioMetric(
                "Maximum Planned Loss",
                formatMoney(
                    portfolio.maximumLoss
                ),
                formatPercent(
                    portfolio.riskPercent
                )
            )}

            ${portfolioMetric(
                "Stocks",
                String(
                    portfolio.stocks.length
                ),
                "Selected"
            )}

            ${portfolioMetric(
                "Risk Status",
                riskStatus.label,
                riskStatus.description
            )}

        </div>
    `;
}

function portfolioMetric(
    title,
    value,
    subtitle
) {
    return `
        <div class="portfolio-metric">

            <span>
                ${escapeHtml(title)}
            </span>

            <strong>
                ${escapeHtml(value)}
            </strong>

            <small>
                ${escapeHtml(
                    subtitle || ""
                )}
            </small>

        </div>
    `;
}

// ============================================================
// PORTFOLIO TABLE
// ============================================================

function renderPortfolioTable(
    portfolio
) {
    const container =
        document.getElementById(
            "portfolioTable"
        );

    if (!container) return;

    if (
        portfolio.stocks.length === 0
    ) {
        renderPortfolioEmptyState();
        return;
    }

    const rows =
        portfolio.stocks
            .map(
                (stock, index) =>
                    renderPortfolioRow(
                        stock,
                        index + 1
                    )
            )
            .join("");

    container.innerHTML = `

        <div class="portfolio-table-wrapper">

            <table class="dashboard-table portfolio-table">

                <thead>

                    <tr>

                        <th>#</th>
                        <th>Stock</th>
                        <th>Setup</th>
                        <th>Entry</th>
                        <th>Stop Loss</th>
                        <th>Target 1</th>
                        <th>Target 2</th>
                        <th>R:R</th>
                        <th>Qty</th>
                        <th>Investment</th>
                        <th>Risk</th>
                        <th>T1 Profit</th>
                        <th>T2 Profit</th>
                        <th>Score</th>

                    </tr>

                </thead>

                <tbody>
                    ${rows}
                </tbody>

            </table>

        </div>

    `;
}

function renderPortfolioRow(
    stock,
    rank
) {
    const rr =
        stock.risk_reward_1;

    return `
        <tr
            class="portfolio-stock-row"
            onclick="openPortfolioStock(
                '${escapePortfolioJs(
                    stock.symbol
                )}'
            )"
        >

            <td>
                ${rank}
            </td>

            <td>

                <strong>
                    ${escapeHtml(
                        stock.symbol
                    )}
                </strong>

                ${
                    stock.company_name
                        ? `
                            <div class="stock-company">
                                ${escapeHtml(
                                    stock.company_name
                                )}
                            </div>
                        `
                        : ""
                }

            </td>

            <td>
                ${portfolioSetupBadge(
                    stock.setup
                )}
            </td>

            <td class="trade-entry">
                ${formatMoney(
                    stock.entry_price
                )}
            </td>

            <td class="trade-stop">
                ${formatMoney(
                    stock.stop_loss
                )}
            </td>

            <td class="trade-target">
                ${formatMoney(
                    stock.target_1
                )}
            </td>

            <td class="trade-target">
                ${formatMoney(
                    stock.target_2
                )}
            </td>

            <td class="${portfolioRRClass(
                rr
            )}">
                ${formatRR(rr)}
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

            <td class="negative">
                ${formatMoney(
                    stock.stock_risk
                )}
                <small>
                    ${formatPercent(
                        stock.risk_percent
                    )}
                </small>
            </td>

            <td class="positive">
                ${formatMoney(
                    stock.expected_profit_t1
                )}
            </td>

            <td class="positive">
                ${formatMoney(
                    stock.expected_profit_t2
                )}
            </td>

            <td>
                <strong>
                    ${formatNumber(
                        stock.overall_score
                    )}
                </strong>
            </td>

        </tr>
    `;
}

// ============================================================
// NOTES
// ============================================================

function renderPortfolioNotes(
    portfolio
) {
    const container =
        document.getElementById(
            "portfolioNotes"
        );

    if (!container) return;

    const riskExceeded =
        isFiniteNumber(
            portfolio.maxRiskPct
        ) &&
        portfolio.riskPercent >
        portfolio.maxRiskPct;

    container.innerHTML = `

        <div class="portfolio-disclaimer">

            <strong>
                Portfolio methodology
            </strong>

            <ul>

                <li>
                    Stock selection uses the
                    dashboard's ranking engine.
                </li>

                <li>
                    Entry, Stop Loss, Target 1,
                    Target 2 and Risk/Reward are
                    taken directly from the
                    engine-generated trade plan.
                </li>

                <li>
                    The Portfolio Builder does
                    not apply a blanket 10% stop
                    loss.
                </li>

                <li>
                    Quantity is calculated using
                    equal capital allocation.
                </li>

                <li>
                    Maximum planned loss assumes
                    every selected position reaches
                    its engine-defined stop loss.
                </li>

                <li>
                    Target profits are scenario
                    calculations, not guaranteed
                    returns.
                </li>

                ${
                    riskExceeded
                        ? `
                            <li class="risk-warning">
                                Planned portfolio risk
                                is above the selected
                                ${formatPercent(
                                    portfolio.maxRiskPct
                                )}
                                risk threshold.
                            </li>
                        `
                        : ""
                }

            </ul>

            <p>
                This dashboard is an analytical
                decision-support tool and not
                investment advice.
            </p>

        </div>
    `;
}

// ============================================================
// EMPTY STATE
// ============================================================

function renderPortfolioEmptyState() {
    const summary =
        document.getElementById(
            "portfolioSummary"
        );

    const table =
        document.getElementById(
            "portfolioTable"
        );

    const notes =
        document.getElementById(
            "portfolioNotes"
        );

    if (summary) {
        summary.innerHTML = "";
    }

    if (table) {
        table.innerHTML = `

            <div class="empty-state">

                <h3>
                    No suitable portfolio
                    candidates
                </h3>

                <p>
                    No stocks currently meet
                    the selected score,
                    technical and trade-plan
                    requirements.
                </p>

                <p>
                    Try lowering the minimum
                    score or increasing the
                    number of stocks.
                </p>

            </div>
        `;
    }

    if (notes) {
        notes.innerHTML = `
            <div class="portfolio-disclaimer">
                Portfolio Builder only selects
                stocks with a valid engine-generated
                trade plan.
            </div>
        `;
    }
}

function showPortfolioMessage(
    message
) {
    const container =
        document.getElementById(
            "portfolioBuilder"
        );

    if (!container) return;

    container.innerHTML = `
        <div class="empty-state">
            ${escapeHtml(message)}
        </div>
    `;
}

// ============================================================
// OPEN STOCK
// ============================================================

function openPortfolioStock(
    symbol
) {
    if (
        typeof openStockDetail ===
        "function"
    ) {
        openStockDetail(symbol);
    }
}

// ============================================================
// EXCEL EXPORT
// ============================================================

function exportPortfolio() {
    if (
        typeof dashboardData ===
        "undefined" ||
        !dashboardData
    ) {
        return;
    }

    const amount =
        getInputNumber(
            "portfolioAmount",
            100000
        );

    const stockCount =
        getInputNumber(
            "portfolioStockCount",
            10
        );

    const minimumScore =
        getInputNumber(
            "portfolioMinScore",
            50
        );

    const maxRiskPct =
        getInputNumber(
            "portfolioMaxRisk",
            2
        );

    const candidates =
        getPortfolioCandidates(
            minimumScore
        );

    const selected =
        selectPortfolioStocks(
            candidates,
            stockCount
        );

    const portfolio =
        calculatePortfolio(
            selected,
            amount,
            maxRiskPct
        );

    if (
        portfolio.stocks.length === 0
    ) {
        alert(
            "No portfolio positions available for export."
        );

        return;
    }

    /*
     * If SheetJS is available,
     * generate a real XLSX file.
     */
    if (
        typeof XLSX !==
        "undefined"
    ) {
        exportWithSheetJS(
            portfolio
        );

        return;
    }

    /*
     * Fallback:
     * create a CSV that Excel can open.
     */
    exportPortfolioCSV(
        portfolio
    );
}

function exportWithSheetJS(
    portfolio
) {
    const rows =
        portfolio.stocks.map(
            (stock, index) => ({
                Rank:
                    index + 1,

                Symbol:
                    stock.symbol,

                Company:
                    stock.company_name,

                Sector:
                    stock.sector,

                Setup:
                    stock.setup,

                Trade_Plan:
                    stock.trade_plan_type,

                Status:
                    stock.trade_plan_status,

                Entry:
                    stock.entry_price,

                Entry_Low:
                    stock.entry_low,

                Entry_High:
                    stock.entry_high,

                Stop_Loss:
                    stock.stop_loss,

                Target_1:
                    stock.target_1,

                Target_2:
                    stock.target_2,

                Risk_Reward_T1:
                    stock.risk_reward_1,

                Risk_Reward_T2:
                    stock.risk_reward_2,

                Quantity:
                    stock.quantity,

                Investment:
                    stock.investment,

                Portfolio_Weight:
                    stock.portfolio_weight,

                Risk:
                    stock.stock_risk,

                Risk_Percent:
                    stock.risk_percent,

                Expected_Profit_T1:
                    stock.expected_profit_t1,

                Expected_Profit_T2:
                    stock.expected_profit_t2,

                Overall_Score:
                    stock.overall_score,

                Technical_Score:
                    stock.technical_score,

                Fundamental_Score:
                    stock.fundamental_score,

                Sector_Score:
                    stock.sector_score,

                Trade_Quality:
                    stock.trade_plan_quality,

                Invalidation:
                    stock.invalidation
            })
        );

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
}

function exportPortfolioCSV(
    portfolio
) {
    const headers = [
        "Rank",
        "Symbol",
        "Company",
        "Sector",
        "Setup",
        "Trade Plan",
        "Status",
        "Entry",
        "Entry Low",
        "Entry High",
        "Stop Loss",
        "Target 1",
        "Target 2",
        "Risk Reward T1",
        "Risk Reward T2",
        "Quantity",
        "Investment",
        "Portfolio Weight %",
        "Risk",
        "Risk %",
        "Expected Profit T1",
        "Expected Profit T2",
        "Overall Score",
        "Technical Score",
        "Fundamental Score",
        "Sector Score",
        "Trade Quality",
        "Invalidation"
    ];

    const rows =
        portfolio.stocks.map(
            (stock, index) => [

                index + 1,

                stock.symbol,

                stock.company_name,

                stock.sector,

                stock.setup,

                stock.trade_plan_type,

                stock.trade_plan_status,

                stock.entry_price,

                stock.entry_low,

                stock.entry_high,

                stock.stop_loss,

                stock.target_1,

                stock.target_2,

                stock.risk_reward_1,

                stock.risk_reward_2,

                stock.quantity,

                stock.investment,

                stock.portfolio_weight,

                stock.stock_risk,

                stock.risk_percent,

                stock.expected_profit_t1,

                stock.expected_profit_t2,

                stock.overall_score,

                stock.technical_score,

                stock.fundamental_score,

                stock.sector_score,

                stock.trade_plan_quality,

                stock.invalidation

            ]
        );

    const csv =
        [
            headers,
            ...rows
        ]
            .map(row =>
                row
                    .map(csvEscape)
                    .join(",")
            )
            .join("\n");

    const blob =
        new Blob(
            [csv],
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

    link.href = url;

    link.download =
        "NSE_Smart_Portfolio.csv";

    document.body.appendChild(
        link
    );

    link.click();

    document.body.removeChild(
        link
    );

    URL.revokeObjectURL(url);
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
        String(value);

    if (
        text.includes(",") ||
        text.includes('"') ||
        text.includes("\n")
    ) {
        return (
            '"' +
            text.replace(
                /"/g,
                '""'
            ) +
            '"'
        );
    }

    return text;
}

// ============================================================
// UI HELPERS
// ============================================================

function portfolioSetupBadge(
    value
) {
    if (!value) {
        return "—";
    }

    const text =
        String(value)
            .toLowerCase();

    let cls =
        "setup-neutral";

    if (
        text.includes("strong") ||
        text.includes("confirmed")
    ) {
        cls =
            "setup-positive";
    } else if (
        text.includes(
            "confirmation"
        ) ||
        text.includes(
            "pre-breakout"
        ) ||
        text.includes("momentum") ||
        text.includes("52w") ||
        text.includes("dma")
    ) {
        cls =
            "setup-watch";
    } else if (
        text.includes("weak") ||
        text.includes("avoid")
    ) {
        cls =
            "setup-negative";
    }

    return `
        <span class="setup-badge ${cls}">
            ${escapeHtml(value)}
        </span>
    `;
}

function portfolioRRClass(
    value
) {
    if (
        !isFiniteNumber(value)
    ) {
        return "";
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

function getRiskStatus(
    risk,
    maximum
) {
    if (
        !isFiniteNumber(risk)
    ) {
        return {
            label: "Unavailable",
            description:
                "Risk could not be calculated."
        };
    }

    if (
        !isFiniteNumber(maximum)
    ) {
        return {
            label: "Calculated",
            description:
                "Based on engine-defined stops."
        };
    }

    if (
        risk <= maximum
    ) {
        return {
            label: "Within Limit",
            description:
                `≤ ${formatPercent(
                    maximum
                )}`
        };
    }

    return {
        label: "Above Limit",
        description:
            `> ${formatPercent(
                maximum
            )}`
    };
}

// ============================================================
// INPUT HELPERS
// ============================================================

function getInputNumber(
    id,
    fallback
) {
    const element =
        document.getElementById(id);

    if (!element) {
        return fallback;
    }

    const value =
        Number(
            element.value
        );

    if (
        !Number.isFinite(value)
    ) {
        return fallback;
    }

    return value;
}

function firstNumber(
    ...values
) {
    for (
        const value of values
    ) {
        if (
            isFiniteNumber(value)
        ) {
            return Number(value);
        }
    }

    return null;
}

function isFiniteNumber(
    value
) {
    if (
        value === null ||
        value === undefined ||
        value === "" ||
        typeof value === "boolean"
    ) {
        return false;
    }

    return Number.isFinite(
        Number(value)
    );
}

// ============================================================
// FORMATTING
// ============================================================

function formatMoney(
    value
) {
    if (
        !isFiniteNumber(value)
    ) {
        return "—";
    }

    return (
        "₹" +
        Number(value)
            .toLocaleString(
                "en-IN",
                {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            )
    );
}

function formatNumber(
    value,
    decimals = 2
) {
    if (
        !isFiniteNumber(value)
    ) {
        return "—";
    }

    return Number(value)
        .toLocaleString(
            "en-IN",
            {
                minimumFractionDigits:
                    decimals,

                maximumFractionDigits:
                    decimals
            }
        );
}

function formatInteger(
    value
) {
    if (
        !isFiniteNumber(value)
    ) {
        return "—";
    }

    return Math.floor(
        Number(value)
    ).toLocaleString(
        "en-IN"
    );
}

function formatPercent(
    value
) {
    if (
        !isFiniteNumber(value)
    ) {
        return "—";
    }

    return (
        Number(value).toFixed(2) +
        "%"
    );
}

function formatRR(
    value
) {
    if (
        !isFiniteNumber(value)
    ) {
        return "—";
    }

    return (
        Number(value).toFixed(2) +
        "x"
    );
}

// ============================================================
// SECURITY
// ============================================================

function escapeHtml(
    value
) {
    return String(
        value ?? ""
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

function escapePortfolioJs(
    value
) {
    return String(
        value ?? ""
    )
        .replace(
            /\\/g,
            "\\\\"
        )
        .replace(
            /'/g,
            "\\'"
        );
}

// ============================================================
// GLOBAL EXPORTS
// ============================================================

window.initializePortfolioBuilder =
    initializePortfolioBuilder;

window.buildPortfolio =
    buildPortfolio;

window.exportPortfolio =
    exportPortfolio;

window.openPortfolioStock =
    openPortfolioStock;

// ============================================================
// END
// ============================================================

/* =========================================================
   NSE SMART MARKET DASHBOARD
   PORTFOLIO BUILDER V3
========================================================= */

(() => {

    "use strict";

    let portfolioData = {};

    let portfolioRows = [];

    let selectedPortfolio = [];


    /* =====================================================
       HELPERS
    ===================================================== */

    function el(id) {
        return document.getElementById(id);
    }


    function num(value) {

        if (
            value === null ||
            value === undefined ||
            value === "" ||
            String(value).toLowerCase() === "nan"
        ) {
            return null;
        }

        const n = Number(value);

        return Number.isFinite(n) ? n : null;
    }


    function first(obj, keys) {

        if (!obj) return null;

        for (const key of keys) {

            if (
                obj[key] !== undefined &&
                obj[key] !== null &&
                obj[key] !== ""
            ) {
                return obj[key];
            }

        }

        return null;
    }


    function money(value) {

        const n = num(value);

        if (n === null) return "—";

        return "₹" + n.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );

    }


    function integer(value) {

        const n = num(value);

        if (n === null) return "—";

        return Math.round(n).toLocaleString("en-IN");

    }


    function pct(value) {

        const n = num(value);

        if (n === null) return "—";

        return (
            n > 0 ? "+" : ""
        ) + n.toFixed(2) + "%";

    }


    function escapeHTML(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    function stocksFromData(data) {

        if (!data) return [];

        const sources = [

            data.stocks,

            data.stock_data,

            data.ranked_stocks,

            data.data?.stocks,

            data.dashboard?.stocks

        ];


        for (const source of sources) {

            if (Array.isArray(source)) {

                return source;

            }

        }


        return [];

    }


    /* =====================================================
       NORMALIZE STOCK
    ===================================================== */

    function normalizeStock(raw) {

        const s = {
            ...raw
        };


        s.symbol =
            String(
                first(
                    s,
                    [
                        "symbol",
                        "Symbol",
                        "ticker",
                        "Ticker",
                        "NSE_Symbol"
                    ]
                ) || ""
            )
            .replace(".NS", "")
            .trim();


        s.company =
            String(
                first(
                    s,
                    [
                        "company_name",
                        "Company_Name",
                        "Company",
                        "company",
                        "longName",
                        "name"
                    ]
                ) || s.symbol
            );


        s.price =
            num(
                first(
                    s,
                    [
                        "Close",
                        "close",
                        "Price",
                        "price",
                        "LTP",
                        "ltp",
                        "CMP",
                        "Current_Price"
                    ]
                )
            );


        s.sma200 =
            num(
                first(
                    s,
                    [
                        "SMA_200",
                        "SMA200",
                        "sma200",
                        "200_DMA",
                        "DMA_200"
                    ]
                )
            );


        s.score =
            num(
                first(
                    s,
                    [
                        "Overall_Score",
                        "overall_score",
                        "Score",
                        "score"
                    ]
                )
            );


        s.technical =
            num(
                first(
                    s,
                    [
                        "Technical_Score",
                        "technical_score"
                    ]
                )
            );


        s.fundamental =
            num(
                first(
                    s,
                    [
                        "Fundamental_Score",
                        "fundamental_score"
                    ]
                )
            );


        s.sector =
            String(
                first(
                    s,
                    [
                        "Primary_Sector",
                        "primary_sector",
                        "Sector",
                        "sector"
                    ]
                ) || "Unknown"
            );


        s.setup =
            String(
                first(
                    s,
                    [
                        "Setup",
                        "setup",
                        "Setup_Type",
                        "setup_type"
                    ]
                ) || "Neutral Watch"
            );


        s.trend =
            String(
                first(
                    s,
                    [
                        "Trend",
                        "trend"
                    ]
                ) || ""
            );


        s.momentum =
            String(
                first(
                    s,
                    [
                        "Momentum",
                        "momentum"
                    ]
                ) || ""
            );


        /*
         ENGINE-GENERATED TRADE PLAN
        */

        s.entry =
            num(
                first(
                    s,
                    [
                        "entry_price",
                        "Entry_Price",
                        "Entry"
                    ]
                )
            );


        s.entryLow =
            num(
                first(
                    s,
                    [
                        "entry_low",
                        "Entry_Low",
                        "Entry_Zone_Low"
                    ]
                )
            );


        s.entryHigh =
            num(
                first(
                    s,
                    [
                        "entry_high",
                        "Entry_High",
                        "Entry_Zone_High"
                    ]
                )
            );


        s.stop =
            num(
                first(
                    s,
                    [
                        "stop_loss",
                        "Stop_Loss",
                        "Stop",
                        "SL"
                    ]
                )
            );


        s.target1 =
            num(
                first(
                    s,
                    [
                        "target_1",
                        "Target_1",
                        "T1"
                    ]
                )
            );


        s.target2 =
            num(
                first(
                    s,
                    [
                        "target_2",
                        "Target_2",
                        "T2"
                    ]
                )
            );


        s.rr =
            num(
                first(
                    s,
                    [
                        "risk_reward_1",
                        "Risk_Reward_1",
                        "risk_reward",
                        "Risk_Reward",
                        "RR"
                    ]
                )
            );


        s.planStatus =
            String(
                first(
                    s,
                    [
                        "trade_plan_status",
                        "Trade_Plan_Status"
                    ]
                ) || ""
            );


        s.planReason =
            String(
                first(
                    s,
                    [
                        "trade_plan_reason",
                        "Trade_Plan_Reason"
                    ]
                ) || ""
            );


        s.invalidation =
            String(
                first(
                    s,
                    [
                        "trade_plan_invalidation",
                        "Trade_Plan_Invalidation",
                        "Invalidation"
                    ]
                ) || ""
            );


        return s;

    }


    /* =====================================================
       PORTFOLIO UI
    ===================================================== */

    function renderBuilder() {

        const container =
            el("portfolioBuilder");

        if (!container) return;


        container.innerHTML = `

            <div class="portfolio-header">

                <div>

                    <div class="section-kicker">
                        DECISION ENGINE
                    </div>

                    <h3 class="section-heading">
                        Smart Portfolio Builder
                    </h3>

                    <div class="section-description">
                        Builds a diversified portfolio from
                        engine-generated actionable setups.
                    </div>

                </div>

                <div class="portfolio-engine-badge">
                    V3 ENGINE
                </div>

            </div>


            <div class="portfolio-controls">

                <div class="portfolio-control">

                    <label>
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

                    <label>
                        Number of Stocks
                    </label>

                    <input
                        id="portfolioStockCount"
                        type="number"
                        min="1"
                        max="30"
                        value="10"
                    >

                </div>


                <div class="portfolio-control">

                    <label>
                        Minimum Score
                    </label>

                    <input
                        id="portfolioMinScore"
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value="55"
                    >

                </div>


                <div class="portfolio-control">

                    <label>
                        Max Risk / Stock %
                    </label>

                    <input
                        id="portfolioRiskPct"
                        type="number"
                        min="0.25"
                        max="10"
                        step="0.25"
                        value="2"
                    >

                </div>

            </div>


            <div class="portfolio-actions">

                <button
                    class="portfolio-build-button"
                    id="buildPortfolioButton"
                    type="button"
                >
                    Build Portfolio
                </button>


                <button
                    class="portfolio-export-button"
                    id="exportPortfolioButton"
                    type="button"
                    disabled
                >
                    Export Portfolio
                </button>

            </div>


            <div
                id="portfolioOutput"
                class="portfolio-output"
            >

                <div class="loading-state">
                    Set your parameters and build the portfolio.
                </div>

            </div>

        `;


        el("buildPortfolioButton")
            ?.addEventListener(
                "click",
                buildPortfolio
            );


        el("exportPortfolioButton")
            ?.addEventListener(
                "click",
                exportPortfolio
            );

    }


    /* =====================================================
       BUILD PORTFOLIO
    ===================================================== */

    function buildPortfolio() {

        const amount =
            num(
                el("portfolioAmount")?.value
            );


        const requestedCount =
            num(
                el("portfolioStockCount")?.value
            );


        const minScore =
            num(
                el("portfolioMinScore")?.value
            );


        const maxRiskPct =
            num(
                el("portfolioRiskPct")?.value
            );


        const output =
            el("portfolioOutput");


        if (!output) return;


        if (
            amount === null ||
            amount <= 0
        ) {

            output.innerHTML = `
                <div class="error-state">
                    Enter a valid portfolio amount.
                </div>
            `;

            return;

        }


        const count =
            Math.max(
                1,
                Math.min(
                    30,
                    Math.round(
                        requestedCount || 10
                    )
                )
            );


        const minimumScore =
            minScore === null
                ? 55
                : minScore;


        const riskLimit =
            maxRiskPct === null
                ? 2
                : maxRiskPct;


        /*
         Candidate selection
        */

        let candidates =
            portfolioData._stocks || [];


        candidates =
            candidates
                .filter(
                    isValidCandidate
                )
                .filter(
                    stock =>
                        stock.score !== null &&
                        stock.score >=
                        minimumScore
                )
                .filter(
                    stock =>
                        stock.setup &&
                        !/weak|avoid/i.test(
                            stock.setup
                        )
                )
                .filter(
                    stock =>
                        stock.entry !== null ||
                        (
                            stock.entryLow !== null &&
                            stock.entryHigh !== null
                        )
                )
                .filter(
                    stock =>
                        stock.stop !== null &&
                        stock.target1 !== null
                )
                .filter(
                    stock =>
                        stock.rr === null ||
                        stock.rr >= 1.5
                );


        /*
         Ranking
        */

        candidates.sort(
            (a,b) => {

                const aScore =
                    candidateScore(a);

                const bScore =
                    candidateScore(b);

                return bScore - aScore;

            }
        );


        /*
         Diversification:
         Maximum 2 stocks per primary sector
        */

        selectedPortfolio = [];

        const sectorCounts = {};


        for (
            const stock of candidates
        ) {

            if (
                selectedPortfolio.length >=
                count
            ) {
                break;
            }


            const sector =
                stock.sector ||
                "Unknown";


            const existing =
                sectorCounts[sector] || 0;


            if (existing >= 2) {

                continue;

            }


            selectedPortfolio.push(
                stock
            );


            sectorCounts[sector] =
                existing + 1;

        }


        /*
         If diversification prevented target count,
         fill remaining positions without sector limit.
        */

        if (
            selectedPortfolio.length < count
        ) {

            for (
                const stock of candidates
            ) {

                if (
                    selectedPortfolio.length >=
                    count
                ) {
                    break;
                }


                if (
                    selectedPortfolio.some(
                        item =>
                            item.symbol ===
                            stock.symbol
                    )
                ) {
                    continue;
                }


                selectedPortfolio.push(
                    stock
                );

            }

        }


        if (!selectedPortfolio.length) {

            output.innerHTML = `

                <div class="error-state">

                    <strong>
                        No actionable stocks found.
                    </strong>

                    Try lowering the minimum score
                    or check the latest dashboard data.

                </div>

            `;

            el(
                "exportPortfolioButton"
            ).disabled = true;

            return;

        }


        /*
         Allocation
        */

        portfolioRows =
            calculateAllocation(
                selectedPortfolio,
                amount,
                riskLimit
            );


        renderPortfolioOutput(
            portfolioRows,
            amount,
            riskLimit,
            candidates.length
        );


        el(
            "exportPortfolioButton"
        ).disabled = false;

    }


    /* =====================================================
       VALID CANDIDATE
    ===================================================== */

    function isValidCandidate(stock) {

        if (!stock) return false;

        if (!stock.symbol) return false;

        if (
            stock.price === null ||
            stock.price <= 0
        ) {
            return false;
        }


        /*
         Don't use a fabricated stop.
        */

        if (
            stock.stop === null ||
            stock.stop <= 0
        ) {
            return false;
        }


        /*
         Stop must be below entry/price for long portfolio.
        */

        const entry =
            stock.entry !== null
                ? stock.entry
                : (
                    stock.entryLow !== null
                        ? stock.entryLow
                        : stock.price
                );


        if (
            entry === null ||
            entry <= 0
        ) {
            return false;
        }


        if (
            stock.stop >= entry
        ) {
            return false;
        }


        if (
            stock.target1 !== null &&
            stock.target1 <= entry
        ) {
            return false;
        }


        return true;

    }


    /* =====================================================
       CANDIDATE SCORE
    ===================================================== */

    function candidateScore(stock) {

        let score =
            stock.score || 0;


        /*
         Reward quality of trade plan.
        */

        if (
            stock.rr !== null
        ) {

            if (
                stock.rr >= 2
            ) {

                score += 8;

            } else if (
                stock.rr >= 1.5
            ) {

                score += 3;

            }

        }


        /*
         Strong setup preference.
        */

        if (
            /strong breakout/i.test(
                stock.setup
            )
        ) {

            score += 8;

        } else if (
            /breakout confirmation/i.test(
                stock.setup
            )
        ) {

            score += 5;

        } else if (
            /momentum|52w high/i.test(
                stock.setup
            )
        ) {

            score += 3;

        }


        /*
         Trend.
        */

        if (
            /positive|strong|bull/i.test(
                stock.trend
            )
        ) {

            score += 3;

        }


        /*
         Momentum.
        */

        if (
            /positive|strong/i.test(
                stock.momentum
            )
        ) {

            score += 3;

        }


        return score;

    }


    /* =====================================================
       ALLOCATION
    ===================================================== */

    function calculateAllocation(
        stocks,
        amount,
        maxRiskPct
    ) {

        const equalCapital =
            amount /
            stocks.length;


        const maxRiskAmount =
            amount *
            (
                maxRiskPct /
                100
            );


        return stocks.map(
            (stock,index) => {

                const entry =
                    stock.entry !== null
                        ? stock.entry
                        : (
                            stock.entryLow !== null
                                ? (
                                    stock.entryLow +
                                    (
                                        (
                                            stock.entryHigh -
                                            stock.entryLow
                                        ) / 2
                                    )
                                )
                                : stock.price
                        );


                const stop =
                    stock.stop;


                const target1 =
                    stock.target1;


                const target2 =
                    stock.target2;


                const riskPerShare =
                    Math.max(
                        0,
                        entry - stop
                    );


                /*
                 Initial equal allocation.
                */

                let quantity =
                    Math.floor(
                        equalCapital /
                        entry
                    );


                /*
                 Respect max portfolio risk.
                */

                if (
                    riskPerShare > 0
                ) {

                    const riskBasedQty =
                        Math.floor(
                            maxRiskAmount /
                            riskPerShare
                        );


                    quantity =
                        Math.min(
                            quantity,
                            riskBasedQty
                        );

                }


                /*
                 At least one share if
                 capital allows it.
                */

                if (
                    quantity < 1 &&
                    entry <= amount
                ) {

                    quantity = 1;

                }


                const invested =
                    quantity *
                    entry;


                const risk =
                    quantity *
                    riskPerShare;


                const profit1 =
                    target1 !== null
                        ?
                            quantity *
                            Math.max(
                                0,
                                target1 -
                                entry
                            )
                        :
                            0;


                const profit2 =
                    target2 !== null
                        ?
                            quantity *
                            Math.max(
                                0,
                                target2 -
                                entry
                            )
                        :
                            profit1;


                const rrActual =
                    risk > 0
                        ?
                            profit1 /
                            risk
                        :
                            null;


                return {

                    rank:
                        index + 1,

                    ...stock,

                    portfolioEntry:
                        entry,

                    portfolioStop:
                        stop,

                    portfolioTarget1:
                        target1,

                    portfolioTarget2:
                        target2,

                    riskPerShare,

                    quantity,

                    invested,

                    risk,

                    profit1,

                    profit2,

                    rrActual

                };

            }
        );

    }


    /* =====================================================
       OUTPUT
    ===================================================== */

    function renderPortfolioOutput(
        rows,
        amount,
        maxRiskPct,
        candidateCount
    ) {

        const output =
            el("portfolioOutput");


        if (!output) return;


        const invested =
            rows.reduce(
                (
                    total,
                    row
                ) =>
                    total +
                    row.invested,
                0
            );


        const totalRisk =
            rows.reduce(
                (
                    total,
                    row
                ) =>
                    total +
                    row.risk,
                0
            );


        const target1Profit =
            rows.reduce(
                (
                    total,
                    row
                ) =>
                    total +
                    row.profit1,
                0
            );


        const target2Profit =
            rows.reduce(
                (
                    total,
                    row
                ) =>
                    total +
                    row.profit2,
                0
            );


        const cash =
            Math.max(
                0,
                amount -
                invested
            );


        const portfolioRiskPct =
            amount > 0
                ?
                    (
                        totalRisk /
                        amount
                    ) *
                    100
                :
                    0;


        const target1Pct =
            invested > 0
                ?
                    (
                        target1Profit /
                        invested
                    ) *
                    100
                :
                    0;


        const target2Pct =
            invested > 0
                ?
                    (
                        target2Profit /
                        invested
                    ) *
                    100
                :
                    0;


        output.innerHTML = `

            <div class="portfolio-summary-grid">

                ${metric(
                    "Stocks Selected",
                    rows.length
                )}

                ${metric(
                    "Capital Invested",
                    money(invested)
                )}

                ${metric(
                    "Cash Remaining",
                    money(cash)
                )}

                ${metric(
                    "Maximum Risk",
                    money(totalRisk),
                    portfolioRiskPct <= maxRiskPct
                        ? "positive"
                        : "negative"
                )}

                ${metric(
                    "T1 Potential",
                    money(target1Profit),
                    "positive"
                )}

                ${metric(
                    "T2 Potential",
                    money(target2Profit),
                    "positive"
                )}

            </div>


            <div class="portfolio-table-wrapper">

                <table class="portfolio-table">

                    <thead>

                        <tr>

                            <th>
                                #
                            </th>

                            <th>
                                Stock
                            </th>

                            <th>
                                Sector
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
                                Risk
                            </th>

                            <th>
                                T1 Profit
                            </th>

                            <th>
                                T2 Profit
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        ${
                            rows
                                .map(
                                    portfolioRowHTML
                                )
                                .join("")
                        }

                    </tbody>

                </table>

            </div>


            <div class="portfolio-notes">

                <strong>
                    Portfolio logic:
                </strong>

                ${
                    candidateCount
                }
                actionable candidates were available.
                Selection prioritises score, setup quality,
                trend, momentum and risk/reward while limiting
                sector concentration.

                <br>

                <strong>
                    Risk control:
                </strong>

                Maximum risk per position is capped at
                ${
                    maxRiskPct
                }%
                of portfolio capital where the calculated
                engine stop permits.

                <br>

                <span class="portfolio-disclaimer">
                    This is a decision-support model, not a
                    guaranteed-return portfolio. Trade plans
                    are based on the dashboard's latest data
                    and should be independently verified before
                    execution.
                </span>

            </div>

        `;


        output
            .querySelectorAll(
                ".portfolio-stock-row"
            )
            .forEach(
                row => {

                    row.addEventListener(
                        "click",
                        () => {

                            const symbol =
                                row.dataset.symbol;


                            if (
                                typeof window.openStockDetail ===
                                "function"
                            ) {

                                window.openStockDetail(
                                    symbol
                                );

                            }

                        }
                    );

                }
            );

    }


    function metric(
        label,
        value,
        className = ""
    ) {

        return `

            <div class="portfolio-metric">

                <span>
                    ${escapeHTML(label)}
                </span>

                <b class="${className}">
                    ${escapeHTML(
                        String(value)
                    )}
                </b>

            </div>

        `;

    }


    function portfolioRowHTML(row) {

        return `

            <tr
                class="portfolio-stock-row"
                data-symbol="${escapeHTML(
                    row.symbol
                )}"
            >

                <td>
                    ${row.rank}
                </td>

                <td>

                    <strong class="stock-symbol">
                        ${escapeHTML(
                            row.symbol
                        )}
                    </strong>

                    <div class="stock-company">
                        ${escapeHTML(
                            row.company
                        )}
                    </div>

                </td>

                <td>
                    ${escapeHTML(
                        row.sector
                    )}
                </td>

                <td>
                    <strong>
                        ${
                            row.score === null
                                ? "—"
                                : row.score.toFixed(1)
                        }
                    </strong>
                </td>

                <td>

                    <span class="setup-badge">
                        ${escapeHTML(
                            row.setup
                        )}
                    </span>

                </td>

                <td class="trade-entry">
                    ${money(
                        row.portfolioEntry
                    )}
                </td>

                <td class="trade-stop">
                    ${money(
                        row.portfolioStop
                    )}
                </td>

                <td class="trade-target">
                    ${money(
                        row.portfolioTarget1
                    )}
                </td>

                <td class="trade-target">
                    ${money(
                        row.portfolioTarget2
                    )}
                </td>

                <td>
                    ${
                        row.rrActual === null
                            ? (
                                row.rr === null
                                    ? "—"
                                    : row.rr.toFixed(2) + "x"
                            )
                            :
                            row.rrActual.toFixed(2) + "x"
                    }
                </td>

                <td>
                    <strong>
                        ${integer(
                            row.quantity
                        )}
                    </strong>
                </td>

                <td>
                    ${money(
                        row.invested
                    )}
                </td>

                <td class="${
                    row.risk > 0
                        ? "negative"
                        : "neutral"
                }">
                    ${money(
                        row.risk
                    )}
                </td>

                <td class="positive">
                    ${money(
                        row.profit1
                    )}
                </td>

                <td class="positive">
                    ${money(
                        row.profit2
                    )}
                </td>

            </tr>

        `;

    }


    /* =====================================================
       EXPORT
    ===================================================== */

    function exportPortfolio() {

        if (
            !portfolioRows.length
        ) {

            alert(
                "Build the portfolio first."
            );

            return;

        }


        const rows =
            portfolioRows.map(
                row => ({

                    Rank:
                        row.rank,

                    Symbol:
                        row.symbol,

                    Company:
                        row.company,

                    Sector:
                        row.sector,

                    Score:
                        row.score,

                    Setup:
                        row.setup,

                    Entry:
                        row.portfolioEntry,

                    Stop_Loss:
                        row.portfolioStop,

                    Target_1:
                        row.portfolioTarget1,

                    Target_2:
                        row.portfolioTarget2,

                    Risk_Reward:
                        row.rrActual ??
                        row.rr,

                    Quantity:
                        row.quantity,

                    Investment:
                        row.invested,

                    Risk:
                        row.risk,

                    Target_1_Profit:
                        row.profit1,

                    Target_2_Profit:
                        row.profit2

                })
            );


        /*
         Prefer SheetJS if already available.
        */

        if (
            typeof XLSX !== "undefined"
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


        /*
         CSV fallback.
        */

        const headers =
            Object.keys(
                rows[0]
            );


        const csv =
            [

                headers.join(","),

                ...rows.map(
                    row =>
                        headers
                            .map(
                                key =>
                                    csvValue(
                                        row[key]
                                    )
                            )
                            .join(",")
                )

            ].join("\n");


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


    function csvValue(value) {

        if (
            value === null ||
            value === undefined
        ) {

            return "";

        }


        return (
            '"' +
            String(value)
                .replace(
                    /"/g,
                    '""'
                ) +
            '"'
        );

    }


    /* =====================================================
       INITIALIZE
    ===================================================== */

    function initializePortfolioBuilder(
        data
    ) {

        portfolioData =
            data || {};


        portfolioData._stocks =
            stocksFromData(
                portfolioData
            )
            .map(
                normalizeStock
            )
            .filter(
                stock =>
                    stock.symbol
            );


        renderBuilder();

    }


    /* =====================================================
       GLOBAL API
    ===================================================== */

    window.initializePortfolioBuilder =
        initializePortfolioBuilder;

    window.buildPortfolio =
        buildPortfolio;

    window.exportPortfolio =
        exportPortfolio;


    /*
     If dashboard.js has not initialized it yet,
     wait for DOM.
    */

    document.addEventListener(
        "DOMContentLoaded",
        () => {

            /*
             dashboard.js normally calls
             initializePortfolioBuilder(data).

             This fallback prevents the builder
             from remaining blank if dashboard.js
             does not call it.
            */

            if (
                !el("portfolioBuilder")
            ) {

                return;

            }


            if (
                !el("buildPortfolioButton")
            ) {

                renderBuilder();

            }

        }
    );

})();

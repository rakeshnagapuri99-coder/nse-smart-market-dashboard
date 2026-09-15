// ============================================================
// NSE SMART MARKET DASHBOARD
// DASHBOARD ENGINE — PRODUCTION V2
// ============================================================

const DATA_FILE = "output/dashboard_data.json";

let dashboardData = null;
let currentWatchlist = "next_day";


// ============================================================
// HELPERS
// ============================================================

function byId(id) {
    return document.getElementById(id);
}


function formatNumber(value, decimals = 2) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        Number.isNaN(Number(value))
    ) {
        return "—";
    }

    return Number(value).toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }
    );
}


function formatPrice(value) {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {
        return "—";
    }

    return "₹" + formatNumber(value, 2);
}


function formatPercent(value) {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {
        return "—";
    }

    const number = Number(value);

    return (
        number >= 0 ? "+" : ""
    )
    + formatNumber(number, 2)
    + "%";
}


function formatRatio(value) {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {
        return "—";
    }

    return formatNumber(value, 2);
}


function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function ratingClass(score) {

    if (
        score === null ||
        score === undefined ||
        Number.isNaN(Number(score))
    ) {
        return "";
    }

    const value = Number(score);

    if (value >= 75) {
        return "rating-excellent";
    }

    if (value >= 60) {
        return "rating-good";
    }

    if (value >= 45) {
        return "rating-neutral";
    }

    if (value >= 30) {
        return "rating-weak";
    }

    return "rating-poor";
}


function statusClass(value) {

    if (!value) {
        return "";
    }

    const text = String(value).toLowerCase();

    if (
        text.includes("strong") ||
        text.includes("bullish") ||
        text.includes("positive") ||
        text.includes("leading") ||
        text.includes("confirmed")
    ) {
        return "status-positive";
    }

    if (
        text.includes("weak") ||
        text.includes("bearish") ||
        text.includes("negative") ||
        text.includes("lagging") ||
        text.includes("avoid")
    ) {
        return "status-negative";
    }

    if (
        text.includes("required") ||
        text.includes("caution") ||
        text.includes("selective") ||
        text.includes("neutral")
    ) {
        return "status-warning";
    }

    return "status-neutral";
}


function safeText(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    return escapeHtml(value);
}


// ============================================================
// LOAD DASHBOARD DATA
// ============================================================

async function loadDashboard() {

    try {

        const response = await fetch(
            DATA_FILE + "?v=" + Date.now()
        );

        if (!response.ok) {
            throw new Error(
                "Unable to load dashboard data."
            );
        }

        dashboardData =
            await response.json();

        renderDashboard();

    } catch (error) {

        console.error(error);

        showDashboardError(
            "Dashboard data is currently unavailable. " +
            "Please try again after the daily market update."
        );
    }
}


// ============================================================
// ERROR
// ============================================================

function showDashboardError(message) {

    const containers = [
        "marketRegime",
        "breadthCards",
        "sectorTable",
        "stockTable"
    ];

    containers.forEach(id => {

        const element = byId(id);

        if (element) {

            element.innerHTML =
                `<div class="dashboard-error">
                    ${escapeHtml(message)}
                </div>`;
        }
    });
}


// ============================================================
// MAIN RENDER
// ============================================================

function renderDashboard() {

    if (!dashboardData) {
        return;
    }

    renderMarket();
    renderBreadth();
    renderSectors();

    renderWatchlist(
        currentWatchlist
    );

    setupTabs();

    updateGeneratedTime();
}


// ============================================================
// MARKET
// ============================================================

function renderMarket() {

    const market =
        dashboardData.market || {};

    const regime =
        market.market_regime || "Unavailable";

    const score =
        market.market_score;

    const html = `

        <div class="market-card regime-card">

            <div class="card-label">
                MARKET REGIME
            </div>

            <div class="market-main-value">
                ${safeText(regime)}
            </div>

            <div class="score-line">
                Market Score:
                <strong>
                    ${formatNumber(score)}
                </strong>
            </div>

        </div>


        <div class="market-card">

            <div class="card-label">
                NIFTY 50
            </div>

            <div class="market-main-value">
                ${formatPrice(
                    market.nifty_price
                )}
            </div>

            <div class="status-badge
                ${statusClass(
                    market.nifty_trend
                )}">
                ${safeText(
                    market.nifty_trend
                )}
            </div>

        </div>


        <div class="market-card">

            <div class="card-label">
                BANK NIFTY
            </div>

            <div class="market-main-value">
                ${formatPrice(
                    market.bank_nifty_price
                )}
            </div>

            <div class="status-badge
                ${statusClass(
                    market.bank_nifty_trend
                )}">
                ${safeText(
                    market.bank_nifty_trend
                )}
            </div>

        </div>


        <div class="market-card">

            <div class="card-label">
                INDIA VIX
            </div>

            <div class="market-main-value">
                ${formatNumber(
                    market.vix
                )}
            </div>

            <div class="status-badge
                ${statusClass(
                    market.vix_interpretation
                )}">
                ${safeText(
                    market.vix_interpretation
                )}
            </div>

        </div>


        <div class="market-card">

            <div class="card-label">
                BREADTH
            </div>

            <div class="market-main-value">
                ${formatNumber(
                    market.breadth_score
                )}
            </div>

            <div class="status-badge
                ${statusClass(
                    market.breadth_score >= 50
                        ? "Positive"
                        : "Weak"
                )}">
                ${safeText(
                    market.breadth_score >= 50
                        ? "Positive"
                        : "Weak"
                )}
            </div>

        </div>

    `;

    const container =
        byId("marketRegime");

    if (container) {
        container.innerHTML = html;
    }
}


// ============================================================
// BREADTH
// ============================================================

function renderBreadth() {

    const breadth =
        dashboardData.breadth || {};

    const cards = [

        {
            label: "Above 20 DMA",
            value:
                breadth.pct_above_20dma,
            suffix: "%",
            count:
                breadth.above_20dma
        },

        {
            label: "Above 50 DMA",
            value:
                breadth.pct_above_50dma,
            suffix: "%",
            count:
                breadth.above_50dma
        },

        {
            label: "Above 200 DMA",
            value:
                breadth.pct_above_200dma,
            suffix: "%",
            count:
                breadth.above_200dma
        },

        {
            label: "52W Highs",
            value:
                breadth["52w_highs"],
            suffix: "",
            count: null
        },

        {
            label: "52W Lows",
            value:
                breadth["52w_lows"],
            suffix: "",
            count: null
        },

        {
            label: "High / Low",
            value:
                breadth.high_low_ratio,
            suffix: "x",
            count: null
        }

    ];


    const html =
        cards.map(card => `

            <div class="breadth-card">

                <div class="card-label">
                    ${escapeHtml(
                        card.label
                    )}
                </div>

                <div class="breadth-value">

                    ${formatNumber(
                        card.value
                    )}${card.suffix}

                </div>

                ${
                    card.count !== null
                        ? `
                            <div class="breadth-count">
                                ${formatNumber(
                                    card.count,
                                    0
                                )} stocks
                            </div>
                          `
                        : ""
                }

            </div>

        `).join("");


    const container =
        byId("breadthCards");

    if (container) {
        container.innerHTML = html;
    }
}


// ============================================================
// SECTORS
// ============================================================

function renderSectors() {

    const sectors =
        dashboardData.sectors || [];

    const container =
        byId("sectorTable");

    if (!container) {
        return;
    }

    if (!sectors.length) {

        container.innerHTML =
            "<p>No sector data available.</p>";

        return;
    }


    const rows =
        sectors.map(sector => `

            <tr>

                <td>
                    <strong>
                        ${safeText(
                            sector.sector
                        )}
                    </strong>
                </td>

                <td>
                    ${safeText(
                        sector.type
                    )}
                </td>

                <td>
                    ${formatNumber(
                        sector.sector_score
                    )}
                </td>

                <td>
                    <span class="status-badge
                        ${statusClass(
                            sector.classification
                        )}">
                        ${safeText(
                            sector.classification
                        )}
                    </span>
                </td>

                <td>
                    ${safeText(
                        sector.trend
                    )}
                </td>

                <td>
                    ${formatPercent(
                        sector.return_20d_pct
                    )}
                </td>

                <td>
                    ${formatPercent(
                        sector.return_60d_pct
                    )}
                </td>

                <td>
                    ${formatNumber(
                        sector.rsi14
                    )}
                </td>

            </tr>

        `).join("");


    container.innerHTML = `

        <table>

            <thead>

                <tr>

                    <th>Sector</th>
                    <th>Type</th>
                    <th>Score</th>
                    <th>Classification</th>
                    <th>Trend</th>
                    <th>20D</th>
                    <th>60D</th>
                    <th>RSI</th>

                </tr>

            </thead>

            <tbody>
                ${rows}
            </tbody>

        </table>

    `;
}


// ============================================================
// WATCHLIST
// ============================================================

function renderWatchlist(
    watchlistName
) {

    currentWatchlist =
        watchlistName;

    const watchlists =
        dashboardData.watchlists || {};

    const stocks =
        watchlists[
            watchlistName
        ] || [];


    const container =
        byId("stockTable");

    if (!container) {
        return;
    }


    if (!stocks.length) {

        container.innerHTML = `

            <div class="empty-state">

                <strong>
                    No stocks currently qualify.
                </strong>

                <p>
                    The list will update with the
                    next market scan.
                </p>

            </div>

        `;

        updateWatchlistCount(
            0
        );

        return;
    }


    const topStocks =
        stocks.slice(
            0,
            15
        );


    const rows =
        topStocks.map(
            (stock, index) =>
                createStockRow(
                    stock,
                    index
                )
        ).join("");


    container.innerHTML = `

        <div class="table-toolbar">

            <div>
                Showing
                <strong>
                    ${topStocks.length}
                </strong>
                of
                <strong>
                    ${stocks.length}
                </strong>
                qualifying stocks
            </div>

            <div class="table-note">
                Click a stock for full analysis
            </div>

        </div>


        <div class="table-scroll">

            <table>

                <thead>

                    <tr>

                        <th>Rank</th>
                        <th>Stock</th>
                        <th>Price</th>
                        <th>Rating</th>
                        <th>Setup</th>
                        <th>Trend</th>
                        <th>RSI</th>
                        <th>Vol.</th>
                        <th>52W High</th>
                        <th>200 DMA</th>
                        <th>R:R</th>

                    </tr>

                </thead>

                <tbody>
                    ${rows}
                </tbody>

            </table>

        </div>

    `;


    updateWatchlistCount(
        stocks.length
    );


    // Make rows clickable
    document
        .querySelectorAll(
            ".stock-row"
        )
        .forEach(row => {

            row.addEventListener(
                "click",
                () => {

                    const symbol =
                        row.dataset.symbol;

                    openStockDetail(
                        symbol
                    );

                }
            );

        });
}


// ============================================================
// STOCK ROW
// ============================================================

function createStockRow(
    stock,
    index
) {

    const symbol =
        stock.symbol ||
        stock.nse_symbol ||
        "—";

    const company =
        stock.company_name ||
        symbol;


    const rating =
        stock.overall_rating ??
        stock.rating ??
        stock.total_score;


    return `

        <tr
            class="stock-row"
            data-symbol="${escapeHtml(
                symbol
            )}"
        >

            <td>
                ${formatNumber(
                    index + 1,
                    0
                )}
            </td>

            <td>

                <div class="stock-name">

                    <strong>
                        ${safeText(
                            stock.nse_symbol ||
                            symbol.replace(
                                ".NS",
                                ""
                            )
                        )}
                    </strong>

                    <small>
                        ${safeText(
                            company
                        )}
                    </small>

                </div>

            </td>

            <td>
                ${formatPrice(
                    stock.price
                )}
            </td>

            <td>

                <span class="
                    rating-badge
                    ${ratingClass(
                        rating
                    )}
                ">

                    ${formatNumber(
                        rating
                    )}

                </span>

            </td>

            <td>

                <span class="
                    status-badge
                    ${statusClass(
                        stock.setup
                    )}
                ">

                    ${safeText(
                        stock.setup
                    )}

                </span>

            </td>

            <td>
                ${safeText(
                    stock.trend
                )}
            </td>

            <td>
                ${formatNumber(
                    stock.rsi14
                )}
            </td>

            <td>
                ${formatRatio(
                    stock.volume_ratio
                )}x
            </td>

            <td>
                ${formatPercent(
                    stock.distance_from_52w_high_pct
                )}
            </td>

            <td>
                ${formatPercent(
                    stock.distance_from_200dma_pct
                )}
            </td>

            <td>
                ${formatRatio(
                    stock.risk_reward
                )}
            </td>

        </tr>

    `;
}


// ============================================================
// WATCHLIST TABS
// ============================================================

function setupTabs() {

    const tabs =
        document.querySelectorAll(
            ".watchlist-tab"
        );

    tabs.forEach(tab => {

        tab.addEventListener(
            "click",
            () => {

                tabs.forEach(
                    item =>
                        item.classList.remove(
                            "active"
                        )
                );

                tab.classList.add(
                    "active"
                );

                const watchlist =
                    tab.dataset.watchlist;

                renderWatchlist(
                    watchlist
                );

            }
        );

    });
}


// ============================================================
// WATCHLIST COUNT
// ============================================================

function updateWatchlistCount(
    count
) {

    const element =
        byId("watchlistCount");

    if (element) {

        element.textContent =
            count.toLocaleString(
                "en-IN"
            );
    }
}


// ============================================================
// STOCK DETAIL
// ============================================================

function openStockDetail(
    symbol
) {

    const stocks =
        dashboardData.stocks || [];

    const stock =
        stocks.find(
            item =>
                item.symbol === symbol
                ||
                item.nse_symbol === symbol
        );


    if (!stock) {
        return;
    }


    const modal =
        byId("stockModal");

    const detail =
        byId("stockDetail");


    if (!modal || !detail) {
        return;
    }


    const rating =
        stock.overall_rating ??
        stock.rating ??
        stock.total_score;


    detail.innerHTML = `

        <div class="detail-header">

            <div>

                <div class="detail-symbol">

                    ${safeText(
                        stock.nse_symbol ||
                        symbol.replace(
                            ".NS",
                            ""
                        )
                    )}

                </div>

                <div class="detail-company">

                    ${safeText(
                        stock.company_name ||
                        "NSE Equity"
                    )}

                </div>

            </div>


            <div class="
                rating-badge
                large
                ${ratingClass(
                    rating
                )}
            ">

                ${formatNumber(
                    rating
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Overall View
            </h3>

            <div class="detail-grid">

                ${detailItem(
                    "Setup",
                    stock.setup
                )}

                ${detailItem(
                    "Trend",
                    stock.trend
                )}

                ${detailItem(
                    "Momentum",
                    stock.momentum
                )}

                ${detailItem(
                    "Breakout",
                    stock.breakout_status
                )}

                ${detailItem(
                    "Technical Score",
                    formatNumber(
                        stock.technical_score
                    )
                )}

                ${detailItem(
                    "Fundamental Score",
                    formatNumber(
                        stock.fundamental_score
                    )
                )}

                ${detailItem(
                    "Sector Score",
                    formatNumber(
                        stock.sector_score
                    )
                )}

                ${detailItem(
                    "Fundamental Quality",
                    stock.fundamental_quality
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Price & Trend
            </h3>

            <div class="detail-grid">

                ${detailItem(
                    "Current Price",
                    formatPrice(
                        stock.price
                    )
                )}

                ${detailItem(
                    "Previous Close",
                    formatPrice(
                        stock.previous_close
                    )
                )}

                ${detailItem(
                    "Daily Return",
                    formatPercent(
                        stock.daily_return_pct
                    )
                )}

                ${detailItem(
                    "SMA 20",
                    formatPrice(
                        stock.sma20
                    )
                )}

                ${detailItem(
                    "SMA 50",
                    formatPrice(
                        stock.sma50
                    )
                )}

                ${detailItem(
                    "SMA 100",
                    formatPrice(
                        stock.sma100
                    )
                )}

                ${detailItem(
                    "SMA 200",
                    formatPrice(
                        stock.sma200
                    )
                )}

                ${detailItem(
                    "EMA 9",
                    formatPrice(
                        stock.ema9
                    )
                )}

                ${detailItem(
                    "EMA 20",
                    formatPrice(
                        stock.ema20
                    )
                )}

                ${detailItem(
                    "EMA 50",
                    formatPrice(
                        stock.ema50
                    )
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Momentum & Volatility
            </h3>

            <div class="detail-grid">

                ${detailItem(
                    "RSI 14",
                    formatNumber(
                        stock.rsi14
                    )
                )}

                ${detailItem(
                    "ATR 14",
                    formatPrice(
                        stock.atr14
                    )
                )}

                ${detailItem(
                    "ATR %",
                    formatPercent(
                        stock.atr_percent
                    )
                )}

                ${detailItem(
                    "Volume Ratio",
                    formatRatio(
                        stock.volume_ratio
                    ) + "x"
                )}

                ${detailItem(
                    "Volume",
                    formatNumber(
                        stock.volume,
                        0
                    )
                )}

                ${detailItem(
                    "Avg Volume 20D",
                    formatNumber(
                        stock.average_volume_20,
                        0
                    )
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                52-Week Position
            </h3>

            <div class="detail-grid">

                ${detailItem(
                    "52W High",
                    formatPrice(
                        stock["52w_high"]
                    )
                )}

                ${detailItem(
                    "52W Low",
                    formatPrice(
                        stock["52w_low"]
                    )
                )}

                ${detailItem(
                    "Distance from 52W High",
                    formatPercent(
                        stock.distance_from_52w_high_pct
                    )
                )}

                ${detailItem(
                    "Distance from 52W Low",
                    formatPercent(
                        stock.distance_from_52w_low_pct
                    )
                )}

                ${detailItem(
                    "Distance from 200 DMA",
                    formatPercent(
                        stock.distance_from_200dma_pct
                    )
                )}

                ${detailItem(
                    "Above 200 DMA",
                    stock.above_200dma
                        ? "Yes"
                        : "No"
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Support & Resistance
            </h3>

            <div class="detail-grid">

                ${detailItem(
                    "Support",
                    formatPrice(
                        stock.support
                    )
                )}

                ${detailItem(
                    "Resistance",
                    formatPrice(
                        stock.resistance
                    )
                )}

                ${detailItem(
                    "Risk / Reward",
                    formatRatio(
                        stock.risk_reward
                    )
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Fundamentals
            </h3>

            <div class="detail-grid">

                ${detailItem(
                    "Market Cap",
                    formatLargeNumber(
                        stock.market_cap
                    )
                )}

                ${detailItem(
                    "Revenue",
                    formatLargeNumber(
                        stock.revenue
                    )
                )}

                ${detailItem(
                    "Net Income",
                    formatLargeNumber(
                        stock.net_income
                    )
                )}

                ${detailItem(
                    "EPS",
                    formatNumber(
                        stock.eps
                    )
                )}

                ${detailItem(
                    "Forward EPS",
                    formatNumber(
                        stock.forward_eps
                    )
                )}

                ${detailItem(
                    "ROE",
                    formatPercent(
                        stock.roe
                    )
                )}

                ${detailItem(
                    "ROA",
                    formatPercent(
                        stock.roa
                    )
                )}

                ${detailItem(
                    "Operating Margin",
                    formatPercent(
                        stock.operating_margin
                    )
                )}

                ${detailItem(
                    "Profit Margin",
                    formatPercent(
                        stock.profit_margin
                    )
                )}

                ${detailItem(
                    "EBITDA Margin",
                    formatPercent(
                        stock.ebitda_margin
                    )
                )}

                ${detailItem(
                    "Debt / Equity",
                    formatRatio(
                        stock.debt_equity
                    )
                )}

                ${detailItem(
                    "Current Ratio",
                    formatRatio(
                        stock.current_ratio
                    )
                )}

                ${detailItem(
                    "Quick Ratio",
                    formatRatio(
                        stock.quick_ratio
                    )
                )}

                ${detailItem(
                    "P/E",
                    formatRatio(
                        stock.pe
                    )
                )}

                ${detailItem(
                    "Forward P/E",
                    formatRatio(
                        stock.forward_pe
                    )
                )}

                ${detailItem(
                    "PEG",
                    formatRatio(
                        stock.peg
                    )
                )}

                ${detailItem(
                    "Price / Book",
                    formatRatio(
                        stock.price_to_book
                    )
                )}

                ${detailItem(
                    "Dividend Yield",
                    formatPercent(
                        stock.dividend_yield
                    )
                )}

                ${detailItem(
                    "Revenue Growth",
                    formatPercent(
                        stock.revenue_growth
                    )
                )}

                ${detailItem(
                    "Earnings Growth",
                    formatPercent(
                        stock.earnings_growth
                    )
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Analysis
            </h3>

            <div class="analysis-box">

                ${
                    stock.reasons
                        ? escapeHtml(
                            stock.reasons
                        )
                        : "No additional analysis available."
                }

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Data Status
            </h3>

            <p class="data-status">

                Fundamentals:
                <strong>
                    ${safeText(
                        stock.fundamental_status ||
                        (
                            stock.fundamental_data_available
                                ? "Available"
                                : "Data unavailable"
                        )
                    )}
                </strong>

                ${
                    stock.data_source
                        ? `
                            · Source:
                            ${safeText(
                                stock.data_source
                            )}
                          `
                        : ""
                }

            </p>

        </div>

    `;


    modal.classList.add(
        "open"
    );


    document.body.classList.add(
        "modal-open"
    );
}


// ============================================================
// DETAIL ITEM
// ============================================================

function detailItem(
    label,
    value
) {

    return `

        <div class="detail-item">

            <span class="detail-label">
                ${escapeHtml(
                    label
                )}
            </span>

            <strong class="detail-value">
                ${
                    value === null ||
                    value === undefined ||
                    value === ""
                        ? "—"
                        : escapeHtml(
                            String(value)
                        )
                }
            </strong>

        </div>

    `;
}


// ============================================================
// LARGE NUMBER
// ============================================================

function formatLargeNumber(
    value
) {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {
        return "—";
    }


    const number =
        Number(value);


    if (
        Math.abs(number)
        >= 1000000000000
    ) {

        return (
            "₹"
            + formatNumber(
                number / 1000000000000
            )
            + " T"
        );
    }


    if (
        Math.abs(number)
        >= 1000000000
    ) {

        return (
            "₹"
            + formatNumber(
                number / 1000000000
            )
            + " B"
        );
    }


    if (
        Math.abs(number)
        >= 10000000
    ) {

        return (
            "₹"
            + formatNumber(
                number / 10000000
            )
            + " Cr"
        );
    }


    return (
        "₹"
        + formatNumber(
            number
        )
    );
}


// ============================================================
// CLOSE MODAL
// ============================================================

function closeStockModal() {

    const modal =
        byId("stockModal");

    if (modal) {

        modal.classList.remove(
            "open"
        );
    }

    document.body.classList.remove(
        "modal-open"
    );
}


// ============================================================
// MODAL EVENTS
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadDashboard();


        const closeButton =
            document.querySelector(
                ".modal-close"
            );

        if (closeButton) {

            closeButton.addEventListener(
                "click",
                closeStockModal
            );

        }


        const modal =
            byId("stockModal");

        if (modal) {

            modal.addEventListener(
                "click",
                event => {

                    if (
                        event.target === modal
                    ) {

                        closeStockModal();

                    }

                }
            );

        }


        document.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Escape"
                ) {

                    closeStockModal();

                }

            }
        );

    }
);


// ============================================================
// GENERATED TIME
// ============================================================

function updateGeneratedTime() {

    const element =
        byId("lastUpdated");

    if (
        !element ||
        !dashboardData.generated_at
    ) {
        return;
    }

    try {

        const date =
            new Date(
                dashboardData.generated_at
            );

        element.textContent =
            date.toLocaleString(
                "en-IN",
                {
                    dateStyle: "medium",
                    timeStyle: "short"
                }
            );

    } catch (error) {

        element.textContent =
            "Latest market scan";

    }
}

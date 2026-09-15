// ============================================================
// NSE SMART MARKET DASHBOARD V2
// DASHBOARD ENGINE
// Created by Rakesh Nagapuri
// ============================================================

let dashboardData = null;


// ============================================================
// WATCHLIST CONFIGURATION
// ============================================================

const WATCHLIST_NAMES = {

    next_day:
        "Next Day Watchlist",

    intraday:
        "Intraday Watchlist",

    swing:
        "Equity Swing",

    long_term:
        "Long-Term Investment",

    "52w_high":
        "52W High",

    dma_recovery:
        "200 DMA Recovery",

    options:
        "Options Watch",

    momentum:
        "Momentum Watch",

    breakout:
        "Breakout Watch"
};


const WATCHLIST_FILES = {

    next_day:
        "next_day.xlsx",

    intraday:
        "intraday.xlsx",

    swing:
        "swing.xlsx",

    long_term:
        "long_term.xlsx",

    "52w_high":
        "52w_high.xlsx",

    dma_recovery:
        "dma_recovery.xlsx",

    options:
        "options.xlsx",

    momentum:
        "momentum.xlsx",

    breakout:
        "breakout.xlsx"
};


// ============================================================
// INITIAL LOAD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {
        loadDashboard();
    }
);


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const response = await fetch(
            "output/dashboard_data.json?v=" +
            Date.now()
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load dashboard data."
            );
        }

        dashboardData =
            await response.json();


        // ----------------------------------------------------
        // IMPORTANT:
        // Convert backend JSON structure into the structure
        // expected by the frontend.
        // ----------------------------------------------------

        normalizeDashboardData();


        renderDashboard();


        // ----------------------------------------------------
        // Portfolio Builder
        // ----------------------------------------------------

        if (
            typeof initializePortfolioBuilder ===
            "function"
        ) {

            initializePortfolioBuilder();
        }

    }

    catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

        showDashboardError(
            "Dashboard data could not be loaded. Please run the market scanner first."
        );
    }
}


// ============================================================
// BACKEND → FRONTEND NORMALIZATION
// ============================================================

function normalizeDashboardData() {

    if (!dashboardData) {
        return;
    }


    // ========================================================
    // MARKET REGIME
    // ========================================================

    const sourceMarket =
        dashboardData.market_regime ||
        dashboardData.market ||
        {};


    if (
        !dashboardData.market ||
        Object.keys(
            dashboardData.market
        ).length === 0
    ) {

        dashboardData.market = {

            regime:
                sourceMarket.market_regime ??
                sourceMarket.regime ??
                "Unavailable",

            market_score:
                sourceMarket.market_score,

            nifty: {

                price:
                    sourceMarket.nifty_price ??
                    sourceMarket.nifty?.price,

                daily_return_pct:
                    sourceMarket.nifty_daily_return_pct ??
                    sourceMarket.nifty_change_pct ??
                    sourceMarket.nifty?.daily_return_pct,

                trend:
                    sourceMarket.nifty_trend ??
                    sourceMarket.nifty?.trend,

                momentum:
                    sourceMarket.nifty_momentum ??
                    sourceMarket.nifty?.momentum,

                rsi14:
                    sourceMarket.nifty_rsi ??
                    sourceMarket.nifty_rsi14 ??
                    sourceMarket.nifty?.rsi14
            },


            bank_nifty: {

                price:
                    sourceMarket.bank_nifty_price ??
                    sourceMarket.bank_nifty?.price,

                daily_return_pct:
                    sourceMarket.bank_nifty_daily_return_pct ??
                    sourceMarket.bank_nifty_change_pct ??
                    sourceMarket.bank_nifty?.daily_return_pct,

                trend:
                    sourceMarket.bank_nifty_trend ??
                    sourceMarket.bank_nifty?.trend,

                momentum:
                    sourceMarket.bank_nifty_momentum ??
                    sourceMarket.bank_nifty?.momentum,

                rsi14:
                    sourceMarket.bank_nifty_rsi ??
                    sourceMarket.bank_nifty_rsi14 ??
                    sourceMarket.bank_nifty?.rsi14
            },


            vix: {

                price:
                    sourceMarket.vix ??
                    sourceMarket.vix_price ??
                    sourceMarket.vix?.price,

                daily_return_pct:
                    sourceMarket.vix_daily_return_pct ??
                    sourceMarket.vix_change_pct ??
                    sourceMarket.vix?.daily_return_pct,

                environment:
                    sourceMarket.vix_interpretation ??
                    sourceMarket.vix?.environment
            },


            equity_environment:
                sourceMarket.equity_environment,

            swing_environment:
                sourceMarket.swing_environment,

            breakout_environment:
                sourceMarket.breakout_environment,

            intraday_environment:
                sourceMarket.intraday_environment,

            options_environment:
                sourceMarket.options_environment
        };
    }


    // ========================================================
    // MARKET BREADTH
    // ========================================================

    const sourceBreadth =
        dashboardData.market_breadth ||
        dashboardData.breadth ||
        {};


    if (
        !dashboardData.breadth ||
        Object.keys(
            dashboardData.breadth
        ).length === 0
    ) {

        dashboardData.breadth = {

            stocks_analyzed:
                sourceBreadth.stocks_analyzed,

            above_20_dma:
                sourceBreadth.above_20dma ??
                sourceBreadth.above_20_dma,

            above_50_dma:
                sourceBreadth.above_50dma ??
                sourceBreadth.above_50_dma,

            above_200_dma:
                sourceBreadth.above_200dma ??
                sourceBreadth.above_200_dma,

            high_52w_count:
                sourceBreadth["52w_highs"] ??
                sourceBreadth.high_52w_count,

            low_52w_count:
                sourceBreadth["52w_lows"] ??
                sourceBreadth.low_52w_count,

            high_low_ratio:
                sourceBreadth.high_low_ratio,

            breadth_score:
                sourceBreadth.breadth_score,

            breadth_regime:
                sourceBreadth.breadth_regime
        };
    }


    // ========================================================
    // SECTOR DATA
    // ========================================================

    if (
        !dashboardData.sectors ||
        !Array.isArray(
            dashboardData.sectors
        )
    ) {

        dashboardData.sectors =
            dashboardData.sector_analysis ||
            [];
    }


    // ========================================================
    // STOCK DATA
    // ========================================================

    if (
        !dashboardData.stocks ||
        !Array.isArray(
            dashboardData.stocks
        )
    ) {

        dashboardData.stocks = [];
    }


    // ========================================================
    // WATCHLIST DATA
    // ========================================================

    if (
        !dashboardData.watchlists ||
        typeof dashboardData.watchlists !==
        "object"
    ) {

        dashboardData.watchlists = {};
    }


    // ========================================================
    // NORMALIZE WATCHLIST STOCK FIELDS
    // ========================================================

    Object.keys(
        dashboardData.watchlists
    ).forEach(
        name => {

            if (
                !Array.isArray(
                    dashboardData.watchlists[name]
                )
            ) {
                dashboardData.watchlists[name] = [];
            }

            dashboardData.watchlists[name] =
                dashboardData.watchlists[name].map(
                    normalizeStock
                );
        }
    );


    // ========================================================
    // NORMALIZE MASTER STOCK DATA
    // ========================================================

    dashboardData.stocks =
        dashboardData.stocks.map(
            normalizeStock
        );
}


// ============================================================
// STOCK FIELD NORMALIZATION
// ============================================================

function normalizeStock(stock) {

    if (!stock || typeof stock !== "object") {
        return {};
    }

    return {

        ...stock,

        symbol:
            stock.symbol ??
            stock.nse_symbol ??
            stock.SYMBOL,

        company_name:
            stock.company_name ??
            stock.company ??
            stock["NAME OF COMPANY"],

        price:
            stock.price ??
            stock.close ??
            stock.Close,

        previous_close:
            stock.previous_close ??
            stock.Previous_Close,

        daily_return_pct:
            stock.daily_return_pct ??
            stock.change_pct ??
            stock.Daily_Return_Pct,

        sma20:
            stock.sma20 ??
            stock.SMA20,

        sma50:
            stock.sma50 ??
            stock.SMA50,

        sma100:
            stock.sma100 ??
            stock.SMA100,

        sma200:
            stock.sma200 ??
            stock.SMA200,

        ema9:
            stock.ema9 ??
            stock.EMA9,

        ema20:
            stock.ema20 ??
            stock.EMA20,

        ema50:
            stock.ema50 ??
            stock.EMA50,

        rsi14:
            stock.rsi14 ??
            stock.RSI14,

        atr14:
            stock.atr14 ??
            stock.ATR14,

        atr_percent:
            stock.atr_percent ??
            stock.ATR_Percent,

        volume:
            stock.volume ??
            stock.Volume,

        average_volume_20:
            stock.average_volume_20 ??
            stock.Average_Volume_20,

        volume_ratio:
            stock.volume_ratio ??
            stock.Volume_Ratio,

        "52w_high":
            stock["52w_high"] ??
            stock["52W_High"],

        "52w_low":
            stock["52w_low"] ??
            stock["52W_Low"],

        distance_from_52w_high_pct:
            stock.distance_from_52w_high_pct ??
            stock.Distance_From_52W_High_Pct,

        distance_from_52w_low_pct:
            stock.distance_from_52w_low_pct ??
            stock.Distance_From_52W_Low_Pct,

        distance_from_200dma_pct:
            stock.distance_from_200dma_pct ??
            stock.Distance_From_200DMA_Pct,

        above_200dma:
            stock.above_200dma ??
            stock.Above_200DMA,

        support:
            stock.support ??
            stock.Support,

        resistance:
            stock.resistance ??
            stock.Resistance,

        trend:
            stock.trend ??
            stock.Trend,

        momentum:
            stock.momentum ??
            stock.Momentum,

        breakout_status:
            stock.breakout_status ??
            stock.Breakout_Status,

        setup:
            stock.setup ??
            stock.Setup,

        overall_score:
            stock.overall_score ??
            stock.Overall_Score,

        technical_score:
            stock.technical_score ??
            stock.Technical_Score,

        fundamental_score:
            stock.fundamental_score ??
            stock.Fundamental_Score,

        sector_score:
            stock.sector_score ??
            stock.Sector_Score,

        rating:
            stock.rating ??
            stock.Rating,

        risk_reward:
            stock.risk_reward ??
            stock.Risk_Reward
    };
}


// ============================================================
// MAIN RENDER
// ============================================================

function renderDashboard() {

    if (!dashboardData) {
        return;
    }

    renderMarketRegime();

    renderBreadth();

    renderSectors();

    renderWatchlists();

    updateLastUpdated();

    document.body.classList.add(
        "dashboard-loaded"
    );
}


// ============================================================
// MARKET REGIME
// ============================================================

function renderMarketRegime() {

    const container =
        document.getElementById(
            "marketRegime"
        );

    if (!container) {
        return;
    }

    const market =
        dashboardData.market || {};

    const regime =
        market.regime ||
        "Unavailable";

    const score =
        market.market_score;

    const nifty =
        market.nifty || {};

    const bank =
        market.bank_nifty || {};

    const vix =
        market.vix || {};


    container.innerHTML = `

        <div class="market-regime-main">

            <div class="regime-badge ${getRegimeClass(regime)}">
                ${escapeHtml(regime)}
            </div>

            <div class="regime-score">
                Market Score:
                <strong>
                    ${formatNumber(score)}
                </strong>
            </div>

        </div>


        <div class="market-index-grid">

            ${renderMarketIndexCard(
                "NIFTY 50",
                nifty
            )}

            ${renderMarketIndexCard(
                "BANK NIFTY",
                bank
            )}

            ${renderVixCard(vix)}

        </div>


        <div class="market-environment-grid">

            ${renderEnvironment(
                "Equity / Swing",
                market.equity_environment ||
                market.swing_environment
            )}

            ${renderEnvironment(
                "Breakout",
                market.breakout_environment
            )}

            ${renderEnvironment(
                "Intraday",
                market.intraday_environment
            )}

            ${renderEnvironment(
                "Options",
                market.options_environment
            )}

        </div>

    `;
}


// ============================================================
// MARKET INDEX CARD
// ============================================================

function renderMarketIndexCard(
    title,
    indexData
) {

    if (
        !indexData ||
        Object.keys(indexData).length === 0
    ) {

        return `
            <div class="market-index-card">

                <h4>
                    ${escapeHtml(title)}
                </h4>

                <div class="muted">
                    Data unavailable
                </div>

            </div>
        `;
    }


    return `

        <div class="market-index-card">

            <h4>
                ${escapeHtml(title)}
            </h4>

            <div class="index-price">
                ${formatPrice(indexData.price)}
            </div>

            <div class="${getChangeClass(
                indexData.daily_return_pct
            )}">
                ${formatSignedPercent(
                    indexData.daily_return_pct
                )}
            </div>


            <div class="index-meta">

                <span>
                    Trend:
                    <strong>
                        ${escapeHtml(
                            indexData.trend || "-"
                        )}
                    </strong>
                </span>


                <span>
                    Momentum:
                    <strong>
                        ${escapeHtml(
                            indexData.momentum || "-"
                        )}
                    </strong>
                </span>


                <span>
                    RSI:
                    <strong>
                        ${formatNumber(
                            indexData.rsi14
                        )}
                    </strong>
                </span>

            </div>

        </div>

    `;
}


// ============================================================
// INDIA VIX
// ============================================================

function renderVixCard(vix) {

    if (
        !vix ||
        Object.keys(vix).length === 0
    ) {

        return `
            <div class="market-index-card">

                <h4>
                    INDIA VIX
                </h4>

                <div class="muted">
                    Data unavailable
                </div>

            </div>
        `;
    }


    return `

        <div class="market-index-card">

            <h4>
                INDIA VIX
            </h4>

            <div class="index-price">
                ${formatNumber(vix.price)}
            </div>

            <div class="${getChangeClass(
                vix.daily_return_pct
            )}">
                ${formatSignedPercent(
                    vix.daily_return_pct
                )}
            </div>

            <div class="index-meta">

                <span>
                    Environment:
                    <strong>
                        ${escapeHtml(
                            vix.environment || "-"
                        )}
                    </strong>
                </span>

            </div>

        </div>

    `;
}


// ============================================================
// MARKET ENVIRONMENT
// ============================================================

function renderEnvironment(
    title,
    value
) {

    return `

        <div class="environment-card">

            <span class="environment-title">
                ${escapeHtml(title)}
            </span>

            <strong class="${getEnvironmentClass(value)}">
                ${escapeHtml(
                    value ||
                    "Unavailable"
                )}
            </strong>

        </div>

    `;
}


// ============================================================
// MARKET BREADTH
// ============================================================

function renderBreadth() {

    const container =
        document.getElementById(
            "breadthCards"
        );

    if (!container) {
        return;
    }

    const breadth =
        dashboardData.breadth || {};


    if (
        !breadth ||
        Object.keys(breadth).length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                Market breadth data unavailable.
            </div>
        `;

        return;
    }


    const stocksAnalyzed =
        breadth.stocks_analyzed;

    const above20 =
        breadth.above_20_dma;

    const above50 =
        breadth.above_50_dma;

    const above200 =
        breadth.above_200_dma;

    const highCount =
        breadth.high_52w_count;

    const lowCount =
        breadth.low_52w_count;

    const highLowRatio =
        breadth.high_low_ratio;

    const breadthScore =
        breadth.breadth_score;

    const regime =
        breadth.breadth_regime;


    container.innerHTML = `

        ${breadthCard(
            "Stocks Analysed",
            formatInteger(
                stocksAnalyzed
            ),
            ""
        )}


        ${breadthCard(
            "Above 20 DMA",
            formatInteger(
                above20
            ),
            percentageOf(
                above20,
                stocksAnalyzed
            )
        )}


        ${breadthCard(
            "Above 50 DMA",
            formatInteger(
                above50
            ),
            percentageOf(
                above50,
                stocksAnalyzed
            )
        )}


        ${breadthCard(
            "Above 200 DMA",
            formatInteger(
                above200
            ),
            percentageOf(
                above200,
                stocksAnalyzed
            )
        )}


        ${breadthCard(
            "52W Highs",
            formatInteger(
                highCount
            ),
            ""
        )}


        ${breadthCard(
            "52W Lows",
            formatInteger(
                lowCount
            ),
            ""
        )}


        ${breadthCard(
            "High / Low",
            formatNumber(
                highLowRatio
            ),
            ""
        )}


        ${breadthCard(
            "Breadth Score",
            formatNumber(
                breadthScore
            ),
            escapeHtml(
                regime || ""
            )
        )}

    `;
}


// ============================================================
// BREADTH CARD
// ============================================================

function breadthCard(
    title,
    value,
    subtitle
) {

    return `

        <div class="breadth-card">

            <div class="breadth-title">
                ${escapeHtml(title)}
            </div>

            <div class="breadth-value">
                ${value}
            </div>

            ${
                subtitle
                    ? `
                        <div class="breadth-subtitle">
                            ${subtitle}
                        </div>
                      `
                    : ""
            }

        </div>

    `;
}


// ============================================================
// SECTORS
// ============================================================

function renderSectors() {

    const container =
        document.getElementById(
            "sectorTable"
        );

    if (!container) {
        return;
    }

    const sectors =
        dashboardData.sectors || [];


    if (
        !Array.isArray(sectors) ||
        sectors.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                Sector data unavailable.
            </div>
        `;

        return;
    }


    const rows =
        sectors
            .map(
                (sector, index) => {

                    return `

                        <tr>

                            <td>
                                ${index + 1}
                            </td>


                            <td>
                                <strong>
                                    ${escapeHtml(
                                        sector.sector ||
                                        sector.name ||
                                        "-"
                                    )}
                                </strong>
                            </td>


                            <td>

                                <span class="status-badge ${
                                    getSectorClass(
                                        sector.strength
                                    )
                                }">

                                    ${escapeHtml(
                                        sector.strength ||
                                        sector.sector_strength ||
                                        "-"
                                    )}

                                </span>

                            </td>


                            <td>
                                ${escapeHtml(
                                    sector.trend ||
                                    "-"
                                )}
                            </td>


                            <td>
                                ${escapeHtml(
                                    sector.momentum ||
                                    "-"
                                )}
                            </td>


                            <td class="${getChangeClass(
                                sector.performance_20d_pct
                            )}">

                                ${formatSignedPercent(
                                    sector.performance_20d_pct
                                )}

                            </td>


                            <td>
                                ${formatNumber(
                                    sector.score
                                )}
                            </td>

                        </tr>

                    `;
                }
            )
            .join("");


    container.innerHTML = `

        <div class="table-wrapper">

            <table class="dashboard-table">

                <thead>

                    <tr>

                        <th>#</th>
                        <th>Sector</th>
                        <th>Strength</th>
                        <th>Trend</th>
                        <th>Momentum</th>
                        <th>20D Performance</th>
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


// ============================================================
// WATCHLISTS
// ============================================================

function renderWatchlists() {

    setupWatchlistTabs();


    const activeTab =
        document.querySelector(
            ".watchlist-tab.active"
        );


    let watchlist =
        "next_day";


    if (activeTab) {

        watchlist =
            activeTab.dataset.watchlist;
    }


    renderWatchlist(
        watchlist
    );
}


// ============================================================
// WATCHLIST TABS
// ============================================================

function setupWatchlistTabs() {

    const tabs =
        document.querySelectorAll(
            ".watchlist-tab"
        );


    tabs.forEach(
        tab => {

            // Prevent duplicate listeners
            if (
                tab.dataset.listenerAttached ===
                "true"
            ) {
                return;
            }


            tab.dataset.listenerAttached =
                "true";


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

        }
    );
}


// ============================================================
// RENDER WATCHLIST
// ============================================================

function renderWatchlist(
    name
) {

    const container =
        document.getElementById(
            "stockTable"
        );

    const countContainer =
        document.getElementById(
            "watchlistCount"
        );


    if (!container) {
        return;
    }


    const watchlists =
        dashboardData.watchlists ||
        {};


    let stocks =
        watchlists[name] ||
        [];


    if (!Array.isArray(stocks)) {
        stocks = [];
    }


    stocks =
        stocks.map(
            normalizeStock
        );


    if (countContainer) {

        countContainer.innerHTML = `

            ${formatInteger(
                stocks.length
            )}

            stocks in

            <strong>
                ${escapeHtml(
                    WATCHLIST_NAMES[name] ||
                    name
                )}
            </strong>

        `;
    }


    renderDownloadButton(
        name,
        stocks.length
    );


    if (stocks.length === 0) {

        container.innerHTML = `

            <div class="empty-state">

                No stocks currently match
                this watchlist.

            </div>

        `;

        return;
    }


    // --------------------------------------------------------
    // Dashboard displays top 15.
    // Excel contains the complete list.
    // --------------------------------------------------------

    const visibleStocks =
        stocks.slice(
            0,
            15
        );


    const rows =
        visibleStocks
            .map(
                (stock, index) =>
                    renderStockRow(
                        stock,
                        index + 1
                    )
            )
            .join("");


    container.innerHTML = `

        <div class="table-wrapper">

            <table class="dashboard-table stock-table">

                <thead>

                    <tr>

                        <th>#</th>
                        <th>Stock</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>Trend</th>
                        <th>Momentum</th>
                        <th>RSI</th>
                        <th>Vol Ratio</th>
                        <th>52W High</th>
                        <th>200 DMA</th>
                        <th>Setup</th>
                        <th>Rating</th>

                    </tr>

                </thead>


                <tbody>
                    ${rows}
                </tbody>

            </table>

        </div>


        ${
            stocks.length > 15

                ? `

                    <div class="table-note">

                        Showing top 15 of
                        ${formatInteger(
                            stocks.length
                        )}.

                        Download Excel for
                        the complete list.

                    </div>

                  `

                : ""
        }

    `;
}


// ============================================================
// STOCK ROW
// ============================================================

function renderStockRow(
    stock,
    rank
) {

    const symbol =
        stock.symbol ||
        stock.nse_symbol ||
        "-";


    const price =
        stock.price ??
        stock.close;


    const change =
        stock.daily_return_pct ??
        stock.change_pct;


    const rating =
        stock.overall_score ??
        stock.rating;


    return `

        <tr
            class="stock-row"
            onclick="openStockDetail('${escapeJs(symbol)}')"
        >

            <td>
                ${rank}
            </td>


            <td>

                <div class="stock-symbol">
                    ${escapeHtml(symbol)}
                </div>


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
                ${formatPrice(price)}
            </td>


            <td class="${getChangeClass(change)}">
                ${formatSignedPercent(change)}
            </td>


            <td>
                ${statusBadge(
                    stock.trend
                )}
            </td>


            <td>
                ${statusBadge(
                    stock.momentum
                )}
            </td>


            <td>
                ${formatNumber(
                    stock.rsi14
                )}
            </td>


            <td>
                ${formatNumber(
                    stock.volume_ratio,
                    2
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
                ${setupBadge(
                    stock.setup
                )}
            </td>


            <td>
                <strong>
                    ${formatNumber(
                        rating
                    )}
                </strong>
            </td>

        </tr>

    `;
}


// ============================================================
// DOWNLOAD EXCEL
// ============================================================

function renderDownloadButton(
    name,
    count
) {

    const countContainer =
        document.getElementById(
            "watchlistCount"
        );


    if (!countContainer) {
        return;
    }


    const file =
        WATCHLIST_FILES[name];


    if (!file) {
        return;
    }


    const existing =
        document.getElementById(
            "watchlistDownload"
        );


    if (existing) {
        existing.remove();
    }


    const button =
        document.createElement(
            "a"
        );


    button.id =
        "watchlistDownload";


    button.className =
        "download-button";


    button.href =
        "output/exports/" +
        file;


    button.download =
        file;


    button.target =
        "_blank";


    button.rel =
        "noopener";


    button.textContent =
        "Download Excel";


    countContainer.appendChild(
        button
    );
}


// ============================================================
// STOCK DETAIL MODAL
// ============================================================

function openStockDetail(
    symbol
) {

    if (!dashboardData) {
        return;
    }


    const stocks =
        dashboardData.stocks ||
        [];


    const stock =
        stocks.find(
            item => {

                const itemSymbol =
                    item.symbol ||
                    item.nse_symbol ||
                    "";


                return String(
                    itemSymbol
                ).toUpperCase() ===
                String(
                    symbol
                ).toUpperCase();

            }
        );


    if (!stock) {

        console.warn(
            "Stock not found:",
            symbol
        );

        return;
    }


    const modal =
        document.getElementById(
            "stockModal"
        );


    const detail =
        document.getElementById(
            "stockDetail"
        );


    if (!modal || !detail) {
        return;
    }


    detail.innerHTML =
        buildStockDetail(
            normalizeStock(stock)
        );


    modal.classList.add(
        "active"
    );


    document.body.classList.add(
        "modal-open"
    );
}


// ============================================================
// CLOSE MODAL
// ============================================================

function closeStockModal() {

    const modal =
        document.getElementById(
            "stockModal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove(
        "active"
    );


    document.body.classList.remove(
        "modal-open"
    );
}


// ============================================================
// STOCK DETAIL
// ============================================================

function buildStockDetail(
    stock
) {

    const symbol =
        stock.symbol ||
        stock.nse_symbol ||
        "-";


    return `

        <div class="stock-detail-header">

            <div>

                <h2>
                    ${escapeHtml(symbol)}
                </h2>


                ${
                    stock.company_name

                        ? `

                            <p>
                                ${escapeHtml(
                                    stock.company_name
                                )}
                            </p>

                          `

                        : ""
                }

            </div>


            <div class="detail-rating">

                <span>
                    Overall Score
                </span>

                <strong>
                    ${formatNumber(
                        stock.overall_score ??
                        stock.rating
                    )}
                </strong>

            </div>

        </div>


        ${detailSection(
            "Trading Setup",
            [

                detailItem(
                    "Setup",
                    stock.setup
                ),

                detailItem(
                    "Technical Score",
                    stock.technical_score
                ),

                detailItem(
                    "Fundamental Score",
                    stock.fundamental_score
                ),

                detailItem(
                    "Sector Score",
                    stock.sector_score
                ),

                detailItem(
                    "Rating",
                    stock.rating
                ),

                detailItem(
                    "Risk / Reward",
                    stock.risk_reward
                )

            ]
        )}


        ${detailSection(
            "Price & Trend",
            [

                detailItem(
                    "Price",
                    formatPrice(
                        stock.price
                    )
                ),

                detailItem(
                    "Previous Close",
                    formatPrice(
                        stock.previous_close
                    )
                ),

                detailItem(
                    "Daily Change",
                    formatSignedPercent(
                        stock.daily_return_pct
                    )
                ),

                detailItem(
                    "Trend",
                    stock.trend
                ),

                detailItem(
                    "Momentum",
                    stock.momentum
                ),

                detailItem(
                    "Breakout",
                    stock.breakout_status
                )

            ]
        )}


        ${detailSection(
            "Moving Averages",
            [

                detailItem(
                    "SMA 20",
                    formatPrice(
                        stock.sma20
                    )
                ),

                detailItem(
                    "SMA 50",
                    formatPrice(
                        stock.sma50
                    )
                ),

                detailItem(
                    "SMA 100",
                    formatPrice(
                        stock.sma100
                    )
                ),

                detailItem(
                    "SMA 200",
                    formatPrice(
                        stock.sma200
                    )
                ),

                detailItem(
                    "EMA 9",
                    formatPrice(
                        stock.ema9
                    )
                ),

                detailItem(
                    "EMA 20",
                    formatPrice(
                        stock.ema20
                    )
                ),

                detailItem(
                    "EMA 50",
                    formatPrice(
                        stock.ema50
                    )
                )

            ]
        )}


        ${detailSection(
            "Momentum & Volatility",
            [

                detailItem(
                    "RSI 14",
                    formatNumber(
                        stock.rsi14
                    )
                ),

                detailItem(
                    "ATR 14",
                    formatPrice(
                        stock.atr14
                    )
                ),

                detailItem(
                    "ATR %",
                    formatPercent(
                        stock.atr_percent
                    )
                ),

                detailItem(
                    "Volume",
                    formatLargeNumber(
                        stock.volume
                    )
                ),

                detailItem(
                    "Average Volume 20",
                    formatLargeNumber(
                        stock.average_volume_20
                    )
                ),

                detailItem(
                    "Volume Ratio",
                    formatNumber(
                        stock.volume_ratio,
                        2
                    ) + "x"
                )

            ]
        )}


        ${detailSection(
            "52 Week & 200 DMA",
            [

                detailItem(
                    "52W High",
                    formatPrice(
                        stock["52w_high"]
                    )
                ),

                detailItem(
                    "52W Low",
                    formatPrice(
                        stock["52w_low"]
                    )
                ),

                detailItem(
                    "Distance from 52W High",
                    formatPercent(
                        stock.distance_from_52w_high_pct
                    )
                ),

                detailItem(
                    "Distance from 52W Low",
                    formatPercent(
                        stock.distance_from_52w_low_pct
                    )
                ),

                detailItem(
                    "Distance from 200 DMA",
                    formatPercent(
                        stock.distance_from_200dma_pct
                    )
                ),

                detailItem(
                    "Above 200 DMA",
                    formatBoolean(
                        stock.above_200dma
                    )
                )

            ]
        )}


        ${detailSection(
            "Support & Resistance",
            [

                detailItem(
                    "Support",
                    formatPrice(
                        stock.support
                    )
                ),

                detailItem(
                    "Resistance",
                    formatPrice(
                        stock.resistance
                    )
                )

            ]
        )}


        ${detailSection(
            "Fundamental Quality",
            [

                detailItem(
                    "Fundamental Status",
                    stock.fundamental_status
                ),

                detailItem(
                    "Fundamental Quality",
                    stock.fundamental_quality
                ),

                detailItem(
                    "Market Cap",
                    formatLargeNumber(
                        stock.market_cap
                    )
                ),

                detailItem(
                    "Enterprise Value",
                    formatLargeNumber(
                        stock.enterprise_value
                    )
                ),

                detailItem(
                    "Sector",
                    stock.sector
                ),

                detailItem(
                    "Industry",
                    stock.industry
                )

            ]
        )}


        ${detailSection(
            "Growth & Profitability",
            [

                detailItem(
                    "Revenue",
                    formatLargeNumber(
                        stock.revenue
                    )
                ),

                detailItem(
                    "Revenue Growth",
                    formatPercent(
                        stock.revenue_growth
                    )
                ),

                detailItem(
                    "Revenue CAGR",
                    formatPercent(
                        stock.revenue_cagr ??
                        stock.revenue_cagr_3y ??
                        stock.revenue_cagr_5y
                    )
                ),

                detailItem(
                    "Net Income",
                    formatLargeNumber(
                        stock.net_income
                    )
                ),

                detailItem(
                    "Earnings Growth",
                    formatPercent(
                        stock.earnings_growth
                    )
                ),

                detailItem(
                    "Profit CAGR",
                    formatPercent(
                        stock.profit_cagr ??
                        stock.profit_cagr_3y ??
                        stock.profit_cagr_5y
                    )
                ),

                detailItem(
                    "EPS",
                    formatNumber(
                        stock.eps
                    )
                ),

                detailItem(
                    "EPS Growth",
                    formatPercent(
                        stock.eps_growth
                    )
                ),

                detailItem(
                    "EPS CAGR",
                    formatPercent(
                        stock.eps_cagr ??
                        stock.eps_cagr_3y ??
                        stock.eps_cagr_5y
                    )
                ),

                detailItem(
                    "Gross Margin",
                    formatPercent(
                        stock.gross_margin
                    )
                ),

                detailItem(
                    "Operating Margin",
                    formatPercent(
                        stock.operating_margin
                    )
                ),

                detailItem(
                    "Profit Margin",
                    formatPercent(
                        stock.profit_margin
                    )
                ),

                detailItem(
                    "EBITDA Margin",
                    formatPercent(
                        stock.ebitda_margin
                    )
                )

            ]
        )}


        ${detailSection(
            "Returns & Balance Sheet",
            [

                detailItem(
                    "ROE",
                    formatPercent(
                        stock.roe
                    )
                ),

                detailItem(
                    "ROCE",
                    formatPercent(
                        stock.roce
                    )
                ),

                detailItem(
                    "ROA",
                    formatPercent(
                        stock.roa
                    )
                ),

                detailItem(
                    "Debt / Equity",
                    formatNumber(
                        stock.debt_equity,
                        2
                    )
                ),

                detailItem(
                    "Current Ratio",
                    formatNumber(
                        stock.current_ratio,
                        2
                    )
                ),

                detailItem(
                    "Quick Ratio",
                    formatNumber(
                        stock.quick_ratio,
                        2
                    )
                ),

                detailItem(
                    "Total Debt",
                    formatLargeNumber(
                        stock.total_debt
                    )
                ),

                detailItem(
                    "Cash",
                    formatLargeNumber(
                        stock.total_cash
                    )
                )

            ]
        )}


        ${detailSection(
            "Valuation",
            [

                detailItem(
                    "PE",
                    formatNumber(
                        stock.pe,
                        2
                    )
                ),

                detailItem(
                    "Forward PE",
                    formatNumber(
                        stock.forward_pe,
                        2
                    )
                ),

                detailItem(
                    "PEG",
                    formatNumber(
                        stock.peg,
                        2
                    )
                ),

                detailItem(
                    "Price / Book",
                    formatNumber(
                        stock.price_to_book,
                        2
                    )
                ),

                detailItem(
                    "Dividend Yield",
                    formatPercent(
                        stock.dividend_yield
                    )
                )

            ]
        )}


        ${detailSection(
            "Why This Stock Appears",
            [

                detailItem(
                    "Analysis",
                    stock.reasons ||
                    stock.reason ||
                    "See technical and fundamental metrics above."
                )

            ]
        )}

    `;
}


// ============================================================
// DETAIL SECTION
// ============================================================

function detailSection(
    title,
    items
) {

    const validItems =
        items.filter(
            item =>
                item !== ""
        );


    return `

        <div class="detail-section">

            <h3>
                ${escapeHtml(title)}
            </h3>


            <div class="detail-grid">

                ${validItems.join("")}

            </div>

        </div>

    `;
}


// ============================================================
// DETAIL ITEM
// ============================================================

function detailItem(
    label,
    value
) {

    if (
        value === undefined ||
        value === null ||
        value === "" ||
        value === "nan" ||
        value === "NaN"
    ) {

        value =
            "Unavailable";
    }


    return `

        <div class="detail-item">

            <span>
                ${escapeHtml(label)}
            </span>

            <strong>
                ${escapeHtml(
                    String(value)
                )}
            </strong>

        </div>

    `;
}


// ============================================================
// MODAL EVENTS
// ============================================================

document.addEventListener(
    "click",
    event => {

        const modal =
            document.getElementById(
                "stockModal"
            );


        if (!modal) {
            return;
        }


        if (
            event.target ===
            modal
        ) {

            closeStockModal();
        }

    }
);


document.addEventListener(
    "keydown",
    event => {

        if (
            event.key ===
            "Escape"
        ) {

            closeStockModal();
        }

    }
);


// ============================================================
// LAST UPDATED
// ============================================================

function updateLastUpdated() {

    const element =
        document.getElementById(
            "lastUpdated"
        );


    if (!element) {
        return;
    }


    const generated =
        dashboardData.generated_at;


    if (!generated) {

        element.textContent =
            "Data timestamp unavailable.";

        return;
    }


    const date =
        new Date(
            generated
        );


    if (
        isNaN(
            date.getTime()
        )
    ) {

        element.textContent =
            "Generated: " +
            generated;

        return;
    }


    element.textContent =
        "Last updated: " +
        date.toLocaleString(
            "en-IN",
            {
                dateStyle:
                    "medium",

                timeStyle:
                    "short"
            }
        );
}


// ============================================================
// ERROR
// ============================================================

function showDashboardError(
    message
) {

    const containers = [

        "marketRegime",
        "breadthCards",
        "sectorTable",
        "stockTable"

    ];


    containers.forEach(
        id => {

            const element =
                document.getElementById(
                    id
                );


            if (element) {

                element.innerHTML = `

                    <div class="error-state">

                        ${escapeHtml(
                            message
                        )}

                    </div>

                `;
            }

        }
    );
}


// ============================================================
// FORMATTING
// ============================================================

function formatNumber(
    value,
    decimals = 2
) {

    if (
        !isValidNumber(value)
    ) {

        return "—";
    }


    return Number(
        value
    ).toLocaleString(
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
        !isValidNumber(value)
    ) {

        return "—";
    }


    return Math.round(
        Number(value)
    ).toLocaleString(
        "en-IN"
    );
}


function formatPrice(
    value
) {

    if (
        !isValidNumber(value)
    ) {

        return "—";
    }


    return "₹" +
        Number(value).toLocaleString(
            "en-IN",
            {
                minimumFractionDigits:
                    2,

                maximumFractionDigits:
                    2
            }
        );
}


function formatLargeNumber(
    value
) {

    if (
        !isValidNumber(value)
    ) {

        return "—";
    }


    const number =
        Number(value);


    if (
        Math.abs(number) >=
        1e12
    ) {

        return "₹" +
            (
                number / 1e12
            ).toFixed(2) +
            " T";
    }


    if (
        Math.abs(number) >=
        1e9
    ) {

        return "₹" +
            (
                number / 1e9
            ).toFixed(2) +
            " B";
    }


    if (
        Math.abs(number) >=
        1e7
    ) {

        return "₹" +
            (
                number / 1e7
            ).toFixed(2) +
            " Cr";
    }


    if (
        Math.abs(number) >=
        1e5
    ) {

        return "₹" +
            (
                number / 1e5
            ).toFixed(2) +
            " L";
    }


    return "₹" +
        number.toLocaleString(
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
        !isValidNumber(value)
    ) {

        return "—";
    }


    return Number(value)
        .toFixed(2) +
        "%";
}


function formatSignedPercent(
    value
) {

    if (
        !isValidNumber(value)
    ) {

        return "—";
    }


    const number =
        Number(value);


    const sign =
        number > 0
            ? "+"
            : "";


    return sign +
        number.toFixed(2) +
        "%";
}


function formatBoolean(
    value
) {

    if (
        value === true ||
        value === "true" ||
        value === 1
    ) {

        return "Yes";
    }


    if (
        value === false ||
        value === "false" ||
        value === 0
    ) {

        return "No";
    }


    return "—";
}


function percentageOf(
    value,
    total
) {

    if (
        !isValidNumber(value) ||
        !isValidNumber(total) ||
        Number(total) === 0
    ) {

        return "";
    }


    return (
        Number(value) /
        Number(total) *
        100
    ).toFixed(2) +
    "%";
}


function isValidNumber(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return false;
    }


    const number =
        Number(value);


    return Number.isFinite(
        number
    );
}


// ============================================================
// CHANGE CLASS
// ============================================================

function getChangeClass(
    value
) {

    if (
        !isValidNumber(value)
    ) {

        return "";
    }


    const number =
        Number(value);


    if (number > 0) {
        return "positive";
    }


    if (number < 0) {
        return "negative";
    }


    return "neutral";
}


// ============================================================
// REGIME CLASS
// ============================================================

function getRegimeClass(
    value
) {

    const text =
        String(
            value || ""
        ).toLowerCase();


    if (
        text.includes(
            "bullish"
        )
    ) {

        return "regime-bullish";
    }


    if (
        text.includes(
            "bearish"
        )
    ) {

        return "regime-bearish";
    }


    if (
        text.includes("weak") ||
        text.includes("cautious")
    ) {

        return "regime-caution";
    }


    return "regime-neutral";
}


// ============================================================
// ENVIRONMENT CLASS
// ============================================================

function getEnvironmentClass(
    value
) {

    const text =
        String(
            value || ""
        ).toLowerCase();


    if (
        text.includes(
            "favorable"
        ) ||
        text.includes(
            "positive"
        ) ||
        text.includes(
            "bullish"
        )
    ) {

        return "positive";
    }


    if (
        text.includes("avoid") ||
        text.includes("weak") ||
        text.includes("bearish")
    ) {

        return "negative";
    }


    return "neutral";
}


// ============================================================
// SECTOR CLASS
// ============================================================

function getSectorClass(
    value
) {

    const text =
        String(
            value || ""
        ).toLowerCase();


    if (
        text.includes(
            "leading"
        ) ||
        text.includes(
            "strong"
        )
    ) {

        return "badge-positive";
    }


    if (
        text.includes(
            "lagging"
        ) ||
        text.includes(
            "weak"
        )
    ) {

        return "badge-negative";
    }


    return "badge-neutral";
}


// ============================================================
// STATUS BADGE
// ============================================================

function statusBadge(
    value
) {

    if (!value) {
        return "—";
    }


    return `

        <span class="status-badge ${getStatusClass(value)}">

            ${escapeHtml(value)}

        </span>

    `;
}


// ============================================================
// SETUP BADGE
// ============================================================

function setupBadge(
    value
) {

    if (!value) {
        return "—";
    }


    return `

        <span class="setup-badge ${getSetupClass(value)}">

            ${escapeHtml(value)}

        </span>

    `;
}


// ============================================================
// STATUS CLASS
// ============================================================

function getStatusClass(
    value
) {

    const text =
        String(value)
            .toLowerCase();


    if (
        text.includes(
            "strong positive"
        ) ||
        text.includes(
            "strong uptrend"
        ) ||
        text.includes(
            "positive"
        ) ||
        text.includes(
            "uptrend"
        )
    ) {

        return "badge-positive";
    }


    if (
        text.includes(
            "strong negative"
        ) ||
        text.includes(
            "strong downtrend"
        ) ||
        text.includes(
            "negative"
        ) ||
        text.includes(
            "downtrend"
        )
    ) {

        return "badge-negative";
    }


    return "badge-neutral";
}


// ============================================================
// SETUP CLASS
// ============================================================

function getSetupClass(
    value
) {

    const text =
        String(
            value || ""
        ).toLowerCase();


    if (
        text.includes(
            "strong"
        ) ||
        text.includes(
            "confirmed"
        )
    ) {

        return "setup-positive";
    }


    if (
        text.includes(
            "confirmation"
        ) ||
        text.includes(
            "pre-breakout"
        ) ||
        text.includes(
            "52w"
        ) ||
        text.includes(
            "dma"
        )
    ) {

        return "setup-watch";
    }


    if (
        text.includes(
            "weak"
        ) ||
        text.includes(
            "avoid"
        )
    ) {

        return "setup-negative";
    }


    return "setup-neutral";
}


// ============================================================
// SECURITY / HTML HELPERS
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


function escapeJs(
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
// GLOBAL MODAL FUNCTIONS
// ============================================================

window.openStockDetail =
    openStockDetail;

window.closeStockModal =
    closeStockModal;


// ============================================================
// END
// ============================================================

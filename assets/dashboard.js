// ============================================================
// NSE SMART MARKET DASHBOARD V2.1
// DASHBOARD FRONTEND ENGINE
// Created by Rakesh Nagapuri
//
// STEP 2:
// - Fixed duplicate market rendering
// - Fixed sector table rendering
// - Fixed watchlist rendering
// - Fixed market data mapping
// - Preserved stock detail / trade plans
// - Preserved Portfolio Builder initialization
// ============================================================

let dashboardData = null;

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

    momentum:
        "Momentum Watch",

    breakout:
        "Breakout Watch",

    options:
        "Options Watch"

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

    momentum:
        "momentum.xlsx",

    breakout:
        "breakout.xlsx",

    options:
        "options.xlsx"

};


// ============================================================
// INITIAL LOAD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    loadDashboard
);


async function loadDashboard() {

    try {

        const response = await fetch(

            "output/dashboard_data.json?v=" +
            Date.now(),

            {
                cache:
                    "no-store"
            }

        );


        if (!response.ok) {

            throw new Error(
                "Unable to load dashboard data."
            );

        }


        dashboardData =
            await response.json();


        normalizeDashboardData();


        renderDashboard();


        /*
         * Portfolio Builder must only be
         * initialized after dashboardData
         * is completely available.
         */
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

            "Dashboard data could not be loaded. " +
            "Please run the market scanner first."

        );

    }

}


// ============================================================
// DATA NORMALIZATION
// ============================================================

function normalizeDashboardData() {

    if (!dashboardData) {
        return;
    }


    // --------------------------------------------------------
    // MARKET
    // --------------------------------------------------------

    const source =
        dashboardData.market_regime ||
        dashboardData.market ||
        {};


    if (
        !dashboardData.market ||
        dashboardData.market ===
        dashboardData.market_regime
    ) {

        dashboardData.market = {

            regime:
                firstValue(
                    source.market_regime,
                    source.regime,
                    "Unavailable"
                ),

            market_score:
                firstValue(
                    source.market_score,
                    source.score
                ),


            nifty: {

                price:
                    firstValue(
                        source.nifty_price,
                        source.nifty_close,
                        source.nifty?.price
                    ),

                previous_close:
                    firstValue(
                        source.nifty_previous_close,
                        source.nifty?.previous_close
                    ),

                daily_return_pct:
                    firstValue(
                        source.nifty_daily_return_pct,
                        source.nifty_change_pct,
                        source.nifty?.daily_return_pct
                    ),

                open:
                    firstValue(
                        source.nifty_open,
                        source.nifty?.open
                    ),

                high:
                    firstValue(
                        source.nifty_high,
                        source.nifty?.high
                    ),

                low:
                    firstValue(
                        source.nifty_low,
                        source.nifty?.low
                    ),

                trend:
                    firstValue(
                        source.nifty_trend,
                        source.nifty?.trend
                    ),

                momentum:
                    firstValue(
                        source.nifty_momentum,
                        source.nifty?.momentum
                    ),

                rsi14:
                    firstValue(
                        source.nifty_rsi,
                        source.nifty?.rsi14
                    )

            },


            bank_nifty: {

                price:
                    firstValue(
                        source.bank_nifty_price,
                        source.bank_nifty_close,
                        source.bank_nifty?.price
                    ),

                previous_close:
                    firstValue(
                        source.bank_nifty_previous_close,
                        source.bank_nifty?.previous_close
                    ),

                daily_return_pct:
                    firstValue(
                        source.bank_nifty_daily_return_pct,
                        source.bank_nifty_change_pct,
                        source.bank_nifty?.daily_return_pct
                    ),

                open:
                    firstValue(
                        source.bank_nifty_open,
                        source.bank_nifty?.open
                    ),

                high:
                    firstValue(
                        source.bank_nifty_high,
                        source.bank_nifty?.high
                    ),

                low:
                    firstValue(
                        source.bank_nifty_low,
                        source.bank_nifty?.low
                    ),

                trend:
                    firstValue(
                        source.bank_nifty_trend,
                        source.bank_nifty?.trend
                    ),

                momentum:
                    firstValue(
                        source.bank_nifty_momentum,
                        source.bank_nifty?.momentum
                    ),

                rsi14:
                    firstValue(
                        source.bank_nifty_rsi,
                        source.bank_nifty?.rsi14
                    )

            },


            vix: {

                price:
                    firstValue(
                        source.vix,
                        source.vix?.price
                    ),

                previous_close:
                    firstValue(
                        source.vix_previous_close,
                        source.vix?.previous_close
                    ),

                daily_return_pct:
                    firstValue(
                        source.vix_daily_return_pct,
                        source.vix?.daily_return_pct
                    ),

                environment:
                    firstValue(
                        source.vix_interpretation,
                        source.vix?.environment
                    )

            },


            equity_environment:
                source.equity_environment,

            swing_environment:
                source.swing_environment,

            breakout_environment:
                source.breakout_environment,

            intraday_environment:
                source.intraday_environment,

            options_environment:
                source.options_environment,


            market_analysis:
                firstValue(
                    source.market_analysis,
                    source.next_day_analysis,
                    {}
                )

        };

    }
    else {

        /*
         * Make sure nested market objects
         * always exist.
         */

        dashboardData.market =
            dashboardData.market || {};

        dashboardData.market.nifty =
            dashboardData.market.nifty || {};

        dashboardData.market.bank_nifty =
            dashboardData.market.bank_nifty || {};

        dashboardData.market.vix =
            dashboardData.market.vix || {};

    }


    // --------------------------------------------------------
    // BREADTH
    // --------------------------------------------------------

    if (
        !dashboardData.breadth
    ) {

        const breadthSource =
            dashboardData.market_breadth ||
            {};


        dashboardData.breadth = {

            stocks_analyzed:
                firstValue(
                    breadthSource.stocks_analyzed,
                    breadthSource.total_stocks
                ),

            above_20_dma:
                firstValue(
                    breadthSource.above_20_dma,
                    breadthSource.above_20dma
                ),

            above_50_dma:
                firstValue(
                    breadthSource.above_50_dma,
                    breadthSource.above_50dma
                ),

            above_200_dma:
                firstValue(
                    breadthSource.above_200_dma,
                    breadthSource.above_200dma
                ),

            high_52w_count:
                firstValue(
                    breadthSource.high_52w_count,
                    breadthSource["52w_highs"]
                ),

            low_52w_count:
                firstValue(
                    breadthSource.low_52w_count,
                    breadthSource["52w_lows"]
                ),

            high_low_ratio:
                breadthSource.high_low_ratio,

            breadth_score:
                breadthSource.breadth_score,

            breadth_regime:
                breadthSource.breadth_regime

        };

    }


    // --------------------------------------------------------
    // SECTORS
    // --------------------------------------------------------

    if (
        !Array.isArray(
            dashboardData.sectors
        )
    ) {

        dashboardData.sectors =
            Array.isArray(
                dashboardData.sector_analysis
            )
                ? dashboardData.sector_analysis
                : [];

    }


    // --------------------------------------------------------
    // WATCHLISTS
    // --------------------------------------------------------

    if (
        !dashboardData.watchlists
        ||
        typeof dashboardData.watchlists !==
        "object"
    ) {

        dashboardData.watchlists = {};

    }


    // --------------------------------------------------------
    // STOCKS
    // --------------------------------------------------------

    if (
        !Array.isArray(
            dashboardData.stocks
        )
    ) {

        dashboardData.stocks = [];

    }

}


// ============================================================
// MAIN RENDER
// ============================================================

function renderDashboard() {

    if (!dashboardData) {
        return;
    }


    renderMarketRegime();

    renderMarketIndexCards();

    renderMarketEnvironments();

    renderMarketAnalysis();

    renderBreadth();

    renderSectors();

    renderWatchlists();

    bindModalEvents();

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


    container.innerHTML = `

        <div>

            <div
                class="regime-badge ${getRegimeClass(
                    regime
                )}"
            >
                ${escapeHtml(regime)}
            </div>

            <div class="regime-score">

                Market Score:
                <strong>
                    ${formatNumber(score)}
                </strong>

            </div>

        </div>

    `;

}


// ============================================================
// MARKET INDEX CARDS
// ============================================================

function renderMarketIndexCards() {

    const niftyContainer =
        document.getElementById(
            "niftyPrice"
        );

    const bankContainer =
        document.getElementById(
            "bankNiftyPrice"
        );

    const vixContainer =
        document.getElementById(
            "vixValue"
        );


    const market =
        dashboardData.market || {};


    const nifty =
        market.nifty || {};


    const bank =
        market.bank_nifty || {};


    const vix =
        market.vix || {};


    // --------------------------------------------------------
    // NIFTY
    // --------------------------------------------------------

    if (niftyContainer) {

        niftyContainer.textContent =
            formatPrice(
                nifty.price
            );

    }


    const niftySecondary =
        document.getElementById(
            "niftySecondary"
        );


    if (niftySecondary) {

        niftySecondary.innerHTML =

            isValidNumber(
                nifty.previous_close
            )

                ?

                `
                    Previous Close:
                    <strong>
                        ${formatPrice(
                            nifty.previous_close
                        )}
                    </strong>
                `

                :

                "Previous Close: —";

    }


    const niftyMeta =
        document.getElementById(
            "niftyMeta"
        );


    if (niftyMeta) {

        niftyMeta.innerHTML = `

            <span>
                Trend
                <strong>
                    ${escapeHtml(
                        nifty.trend ||
                        "—"
                    )}
                </strong>
            </span>

            <span>
                Momentum
                <strong>
                    ${escapeHtml(
                        nifty.momentum ||
                        "—"
                    )}
                </strong>
            </span>

            <span>
                RSI
                <strong>
                    ${formatNumber(
                        nifty.rsi14
                    )}
                </strong>
            </span>

        `;

    }


    if (niftySecondary) {

        const change =
            document.createElement(
                "div"
            );

        change.className =
            getChangeClass(
                nifty.daily_return_pct
            );

        change.textContent =
            formatSignedPercent(
                nifty.daily_return_pct
            );

        /*
         * Remove an old change element
         * if one exists.
         */
        const oldChange =
            document.getElementById(
                "niftyDailyChange"
            );

        if (oldChange) {
            oldChange.remove();
        }

        change.id =
            "niftyDailyChange";

        niftySecondary.parentNode.insertBefore(
            change,
            niftySecondary.nextSibling
        );

    }


    // --------------------------------------------------------
    // BANK NIFTY
    // --------------------------------------------------------

    if (bankContainer) {

        bankContainer.textContent =
            formatPrice(
                bank.price
            );

    }


    const bankSecondary =
        document.getElementById(
            "bankNiftySecondary"
        );


    if (bankSecondary) {

        bankSecondary.innerHTML =

            isValidNumber(
                bank.previous_close
            )

                ?

                `
                    Previous Close:
                    <strong>
                        ${formatPrice(
                            bank.previous_close
                        )}
                    </strong>
                `

                :

                "Previous Close: —";

    }


    const bankMeta =
        document.getElementById(
            "bankNiftyMeta"
        );


    if (bankMeta) {

        bankMeta.innerHTML = `

            <span>
                Trend
                <strong>
                    ${escapeHtml(
                        bank.trend ||
                        "—"
                    )}
                </strong>
            </span>

            <span>
                Momentum
                <strong>
                    ${escapeHtml(
                        bank.momentum ||
                        "—"
                    )}
                </strong>
            </span>

            <span>
                RSI
                <strong>
                    ${formatNumber(
                        bank.rsi14
                    )}
                </strong>
            </span>

        `;

    }


    if (bankSecondary) {

        const change =
            document.createElement(
                "div"
            );

        change.id =
            "bankNiftyDailyChange";

        change.className =
            getChangeClass(
                bank.daily_return_pct
            );

        change.textContent =
            formatSignedPercent(
                bank.daily_return_pct
            );

        const oldChange =
            document.getElementById(
                "bankNiftyDailyChange"
            );

        if (oldChange) {
            oldChange.remove();
        }

        bankSecondary.parentNode.insertBefore(
            change,
            bankSecondary.nextSibling
        );

    }


    // --------------------------------------------------------
    // VIX
    // --------------------------------------------------------

    if (vixContainer) {

        vixContainer.textContent =
            formatNumber(
                vix.price
            );

    }


    const vixInterpretation =
        document.getElementById(
            "vixInterpretation"
        );


    if (vixInterpretation) {

        vixInterpretation.innerHTML = `

            ${escapeHtml(
                vix.environment ||
                "Unavailable"
            )}

        `;

    }


    const vixMeta =
        document.getElementById(
            "vixMeta"
        );


    if (vixMeta) {

        vixMeta.innerHTML = `

            <span>
                Market
                <strong>
                    ${escapeHtml(
                        vix.environment ||
                        "—"
                    )}
                </strong>
            </span>

            <span>
                Risk
                <strong>
                    ${vixRiskLabel(
                        vix.price
                    )}
                </strong>
            </span>

            <span>
                Mode
                <strong>
                    ${isValidNumber(
                        vix.daily_return_pct
                    )
                        ? formatSignedPercent(
                            vix.daily_return_pct
                        )
                        : "—"
                    }
                </strong>
            </span>

        `;

    }

}


// ============================================================
// MARKET ENVIRONMENTS
// ============================================================

function renderMarketEnvironments() {

    const container =
        document.getElementById(
            "marketEnvironmentGrid"
        );


    if (!container) {
        return;
    }


    const market =
        dashboardData.market || {};


    container.innerHTML = `

        ${environmentCard(
            "Equity",
            market.equity_environment
        )}

        ${environmentCard(
            "Swing",
            market.swing_environment
        )}

        ${environmentCard(
            "Breakout",
            market.breakout_environment
        )}

        ${environmentCard(
            "Intraday",
            market.intraday_environment
        )}

        ${environmentCard(
            "Options",
            market.options_environment
        )}

    `;

}


function environmentCard(
    title,
    value
) {

    return `

        <div class="environment-card">

            <div class="environment-title">
                ${escapeHtml(title)}
            </div>

            <strong class="${getEnvironmentClass(
                value
            )}">
                ${escapeHtml(
                    value ||
                    "Unavailable"
                )}
            </strong>

        </div>

    `;

}


// ============================================================
// MARKET ANALYSIS
// ============================================================

function renderMarketAnalysis() {

    const grid =
        document.getElementById(
            "marketAnalysisGrid"
        );


    const scenario =
        document.getElementById(
            "marketScenario"
        );


    if (!grid) {
        return;
    }


    const market =
        dashboardData.market || {};


    const analysis =
        market.market_analysis ||
        {};


    const support =
        firstValue(
            analysis.support,
            analysis.support_zone,
            analysis.next_day_support,
            analysis.support_1
        );


    const resistance =
        firstValue(
            analysis.resistance,
            analysis.resistance_zone,
            analysis.next_day_resistance,
            analysis.resistance_1
        );


    const pivot =
        firstValue(
            analysis.pivot,
            analysis.pivot_point
        );


    const bullish =
        firstValue(
            analysis.bullish_trigger,
            analysis.bullish_trigger_level
        );


    const bearish =
        firstValue(
            analysis.bearish_trigger,
            analysis.bearish_trigger_level
        );


    grid.innerHTML = `

        ${analysisMetric(
            "Pivot",
            pivot
        )}

        ${analysisMetric(
            "Support",
            support
        )}

        ${analysisMetric(
            "Resistance",
            resistance
        )}

        ${analysisMetric(
            "Bullish Trigger",
            bullish
        )}

        ${analysisMetric(
            "Bearish Trigger",
            bearish
        )}

    `;


    if (scenario) {

        const text =
            firstValue(
                analysis.scenario,
                analysis.next_day_scenario,
                analysis.explanation
            );


        scenario.innerHTML = `

            <strong>
                Scenario
            </strong>

            <p>
                ${
                    text
                        ? escapeHtml(
                            text
                        )
                        :
                        "Market scenario will be generated from the latest market structure."
                }
            </p>

        `;

    }

}


function analysisMetric(
    label,
    value
) {

    return `

        <div class="analysis-metric">

            <span>
                ${escapeHtml(label)}
            </span>

            <strong>
                ${formatPrice(value)}
            </strong>

        </div>

    `;

}


// ============================================================
// BREADTH
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
        dashboardData.breadth ||
        {};


    if (
        Object.keys(
            breadth
        ).length === 0
    ) {

        container.innerHTML = `

            <div class="empty-state">
                Market breadth data unavailable.
            </div>

        `;

        return;

    }


    const total =
        breadth.stocks_analyzed;


    container.innerHTML = `

        ${breadthCard(
            "Stocks Analysed",
            formatInteger(
                total
            ),
            ""
        )}

        ${breadthCard(
            "Above 20 DMA",
            formatInteger(
                breadth.above_20_dma
            ),
            percentageOf(
                breadth.above_20_dma,
                total
            )
        )}

        ${breadthCard(
            "Above 50 DMA",
            formatInteger(
                breadth.above_50_dma
            ),
            percentageOf(
                breadth.above_50_dma,
                total
            )
        )}

        ${breadthCard(
            "Above 200 DMA",
            formatInteger(
                breadth.above_200_dma
            ),
            percentageOf(
                breadth.above_200_dma,
                total
            )
        )}

        ${breadthCard(
            "52W Highs",
            formatInteger(
                breadth.high_52w_count
            ),
            ""
        )}

        ${breadthCard(
            "52W Lows",
            formatInteger(
                breadth.low_52w_count
            ),
            ""
        )}

        ${breadthCard(
            "High / Low",
            formatNumber(
                breadth.high_low_ratio
            ),
            ""
        )}

        ${breadthCard(
            "Breadth Score",
            formatNumber(
                breadth.breadth_score
            ),
            breadth.breadth_regime ||
            ""
        )}

    `;

}


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
                    ?

                    `
                        <div class="breadth-subtitle">
                            ${escapeHtml(
                                subtitle
                            )}
                        </div>
                    `

                    :

                    ""
            }

        </div>

    `;

}


// ============================================================
// SECTORS
// ============================================================

function renderSectors() {

    const table =
        document.getElementById(
            "sectorTable"
        );


    if (!table) {
        return;
    }


    const tbody =
        table.querySelector(
            "tbody"
        );


    if (!tbody) {
        return;
    }


    const sectors =
        Array.isArray(
            dashboardData.sectors
        )
            ? dashboardData.sectors
            : [];


    if (
        sectors.length === 0
    ) {

        tbody.innerHTML = `

            <tr>

                <td
                    colspan="8"
                    class="empty-state"
                >
                    Sector data unavailable.
                </td>

            </tr>

        `;

        return;

    }


    tbody.innerHTML =

        sectors
            .slice(
                0,
                25
            )
            .map(
                (
                    sector,
                    index
                ) => {

                    const name =
                        sector.sector ||
                        sector.name ||
                        sector.index_name ||
                        "-";


                    const price =
                        firstValue(
                            sector.price,
                            sector.close,
                            sector.last
                        );


                    const performance =
                        firstValue(
                            sector.performance_20d_pct,
                            sector.return_20d_pct,
                            sector.performance_20d
                        );


                    const strength =
                        firstValue(
                            sector.strength,
                            sector.regime
                        );


                    return `

                        <tr>

                            <td>
                                ${index + 1}
                            </td>

                            <td>
                                <strong>
                                    ${escapeHtml(
                                        name
                                    )}
                                </strong>
                            </td>

                            <td>
                                ${formatPrice(
                                    price
                                )}
                            </td>

                            <td>
                                ${statusBadge(
                                    sector.trend
                                )}
                            </td>

                            <td>
                                ${statusBadge(
                                    sector.momentum
                                )}
                            </td>

                            <td class="${getChangeClass(
                                performance
                            )}">
                                ${formatSignedPercent(
                                    performance
                                )}
                            </td>

                            <td>
                                ${formatNumber(
                                    sector.score
                                )}
                            </td>

                            <td>
                                ${strength
                                    ? statusBadge(
                                        strength
                                    )
                                    : "—"
                                }
                            </td>

                        </tr>

                    `;

                }
            )
            .join("");

}


// ============================================================
// WATCHLISTS
// ============================================================

function renderWatchlists() {

    setupWatchlistTabs();


    const active =
        document.querySelector(
            ".watchlist-tab.active"
        );


    const name =
        active?.dataset.watchlist ||
        "next_day";


    renderWatchlist(
        name
    );

}


function setupWatchlistTabs() {

    const tabs =
        document.querySelectorAll(
            ".watchlist-tab"
        );


    tabs.forEach(
        tab => {

            if (
                tab.dataset.bound ===
                "true"
            ) {
                return;
            }


            tab.dataset.bound =
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


                    renderWatchlist(
                        tab.dataset.watchlist
                    );

                }
            );

        }
    );

}


function renderWatchlist(
    name
) {

    const table =
        document.getElementById(
            "stockTable"
        );


    const countContainer =
        document.getElementById(
            "watchlistCount"
        );


    if (!table) {
        return;
    }


    const tbody =
        table.querySelector(
            "tbody"
        );


    if (!tbody) {
        return;
    }


    const stocks =
        Array.isArray(
            dashboardData.watchlists?.[
                name
            ]
        )

            ?

            dashboardData.watchlists[
                name
            ]

            :

            [];


    if (countContainer) {

        countContainer.innerHTML = `

            ${formatInteger(
                stocks.length
            )}

            stocks in

            <strong>
                ${escapeHtml(
                    WATCHLIST_NAMES[
                        name
                    ] ||
                    name
                )}
            </strong>

        `;

    }


    updateWatchlistDownload(
        name
    );


    if (
        stocks.length === 0
    ) {

        tbody.innerHTML = `

            <tr>

                <td
                    colspan="15"
                    class="empty-state"
                >
                    No stocks currently match
                    this watchlist.
                </td>

            </tr>

        `;

        return;

    }


    tbody.innerHTML =

        stocks
            .slice(
                0,
                15
            )
            .map(
                (
                    stock,
                    index
                ) =>
                    renderStockRow(
                        stock,
                        index + 1
                    )
            )
            .join("");


    const note =
        document.getElementById(
            "watchlistTableNote"
        );


    if (note) {

        note.textContent =

            stocks.length > 15

                ?

                `Showing top 15 of ${stocks.length} stocks. Download Excel for the complete list.`

                :

                "Click any stock to open the detailed technical, fundamental and trade-plan view.";

    }

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
        firstValue(
            stock.price,
            stock.close
        );


    const change =
        firstValue(
            stock.daily_return_pct,
            stock.change_pct
        );


    const score =
        firstValue(
            stock.overall_score,
            stock.rating
        );


    const entry =
        tradeValue(
            stock,
            "entry_price"
        );


    const stop =
        tradeValue(
            stock,
            "stop_loss"
        );


    const target1 =
        tradeValue(
            stock,
            "target_1"
        );


    const target2 =
        tradeValue(
            stock,
            "target_2"
        );


    const rr =
        firstValue(
            stock.risk_reward_1,
            stock.risk_reward
        );


    const setup =
        stock.setup ||
        stock.trade_plan_type ||
        "—";


    return `

        <tr
            class="stock-row"
            onclick="openStockDetail('${escapeJs(
                symbol
            )}')"
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

                ${
                    stock.company_name
                        ?

                        `
                            <div class="stock-company">
                                ${escapeHtml(
                                    stock.company_name
                                )}
                            </div>
                        `

                        :

                        ""
                }

            </td>


            <td>
                ${formatPrice(
                    price
                )}
            </td>


            <td class="${getChangeClass(
                change
            )}">
                ${formatSignedPercent(
                    change
                )}
            </td>


            <td>
                <strong>
                    ${formatNumber(
                        score
                    )}
                </strong>
            </td>


            <td>
                ${statusBadge(
                    setup
                )}
            </td>


            <td class="trade-entry">
                ${formatPrice(
                    entry
                )}
            </td>


            <td class="trade-stop">
                ${formatPrice(
                    stop
                )}
            </td>


            <td class="trade-target">
                ${formatPrice(
                    target1
                )}
            </td>


            <td class="trade-target">
                ${formatPrice(
                    target2
                )}
            </td>


            <td class="${riskRewardClass(
                rr
            )}">
                ${formatRiskReward(
                    rr
                )}
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
                ${
                    isValidNumber(
                        stock.volume_ratio
                    )

                        ?

                        Number(
                            stock.volume_ratio
                        ).toFixed(2) +
                        "x"

                        :

                        "—"
                }
            </td>

        </tr>

    `;

}


// ============================================================
// WATCHLIST DOWNLOAD
// ============================================================

function updateWatchlistDownload(
    name
) {

    const button =
        document.getElementById(
            "downloadWatchlist"
        );


    if (!button) {
        return;
    }


    const file =
        WATCHLIST_FILES[
            name
        ];


    if (!file) {

        button.style.display =
            "none";

        return;

    }


    button.style.display =
        "inline-flex";


    button.onclick = () => {

        const link =
            document.createElement(
                "a"
            );


        link.href =
            "output/exports/" +
            file;


        link.download =
            file;


        link.target =
            "_blank";


        link.rel =
            "noopener";


        document.body.appendChild(
            link
        );


        link.click();


        link.remove();

    };

}


// ============================================================
// STOCK DETAIL
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


    let stock =
        stocks.find(
            item =>
                String(
                    item.symbol ||
                    item.nse_symbol ||
                    ""
                ).toUpperCase()
                ===
                String(
                    symbol
                ).toUpperCase()
        );


    /*
     * If the stock is not present in the
     * master list, search every watchlist.
     */

    if (!stock) {

        Object.values(
            dashboardData.watchlists ||
            {}
        ).forEach(
            list => {

                if (
                    stock ||
                    !Array.isArray(list)
                ) {
                    return;
                }


                const found =
                    list.find(
                        item =>
                            String(
                                item.symbol ||
                                item.nse_symbol ||
                                ""
                            ).toUpperCase()
                            ===
                            String(
                                symbol
                            ).toUpperCase()
                    );


                if (found) {
                    stock = found;
                }

            }
        );

    }


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


    if (
        !modal ||
        !detail
    ) {
        return;
    }


    detail.innerHTML =
        buildStockDetail(
            stock
        );


    modal.classList.add(
        "open"
    );


    modal.classList.add(
        "active"
    );


    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "modal-open"
    );

}


window.openStockDetail =
    openStockDetail;


function closeStockModal() {

    const modal =
        document.getElementById(
            "stockModal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove(
        "open"
    );


    modal.classList.remove(
        "active"
    );


    modal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "modal-open"
    );

}


window.closeStockModal =
    closeStockModal;


// ============================================================
// MODAL EVENTS
// ============================================================

function bindModalEvents() {

    const closeButton =
        document.getElementById(
            "stockModalClose"
        );


    if (
        closeButton &&
        closeButton.dataset.bound !==
        "true"
    ) {

        closeButton.dataset.bound =
            "true";


        closeButton.addEventListener(
            "click",
            closeStockModal
        );

    }


    const modal =
        document.getElementById(
            "stockModal"
        );


    if (
        modal &&
        modal.dataset.bound !==
        "true"
    ) {

        modal.dataset.bound =
            "true";


        modal.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    modal
                ) {

                    closeStockModal();

                }

            }
        );

    }

}


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
// STOCK DETAIL CONTENT
// ============================================================

function buildStockDetail(
    stock
) {

    const symbol =
        stock.symbol ||
        stock.nse_symbol ||
        "-";


    const company =
        stock.company_name ||
        symbol;


    const entry =
        tradeValue(
            stock,
            "entry_price"
        );


    const entryLow =
        tradeValue(
            stock,
            "entry_low"
        );


    const entryHigh =
        tradeValue(
            stock,
            "entry_high"
        );


    const stop =
        tradeValue(
            stock,
            "stop_loss"
        );


    const target1 =
        tradeValue(
            stock,
            "target_1"
        );


    const target2 =
        tradeValue(
            stock,
            "target_2"
        );


    const rr1 =
        firstValue(
            stock.risk_reward_1,
            stock.risk_reward
        );


    const rr2 =
        stock.risk_reward_2;


    const planStatus =
        stock.trade_plan_status ||
        "Unavailable";


    const planType =
        stock.trade_plan_type ||
        "No active plan";


    const planReason =
        stock.trade_plan_reason ||
        "";


    const invalidation =
        stock.invalidation ||
        "";


    const quality =
        stock.trade_plan_quality ||
        "";


    return `

        <div class="stock-detail-header">

            <div>

                <div class="section-kicker">
                    Stock Intelligence
                </div>

                <h2>
                    ${escapeHtml(
                        symbol
                    )}
                </h2>

                <p>
                    ${escapeHtml(
                        company
                    )}
                </p>

            </div>


            <div class="detail-rating">

                <span>
                    Overall Score
                </span>

                <strong>
                    ${formatNumber(
                        stock.overall_score
                    )}
                </strong>

            </div>

        </div>


        ${renderTradePlan(
            stock,
            {
                entry,
                entryLow,
                entryHigh,
                stop,
                target1,
                target2,
                rr1,
                rr2,
                planStatus,
                planType,
                planReason,
                invalidation,
                quality
            }
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
                ),

                detailItem(
                    "Setup",
                    stock.setup
                ),

                detailItem(
                    "Watchlist",
                    findWatchlistMembership(
                        symbol
                    )
                )

            ]
        )}


        ${detailSection(
            "Technical Scores",
            [

                detailItem(
                    "Technical Score",
                    formatNumber(
                        stock.technical_score
                    )
                ),

                detailItem(
                    "Fundamental Score",
                    formatNumber(
                        stock.fundamental_score
                    )
                ),

                detailItem(
                    "Sector Score",
                    formatNumber(
                        stock.sector_score
                    )
                ),

                detailItem(
                    "Overall Score",
                    formatNumber(
                        stock.overall_score
                    )
                ),

                detailItem(
                    "Technical Rating",
                    stock.technical_rating
                ),

                detailItem(
                    "Fundamental Status",
                    stock.fundamental_status
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
                    "RSI",
                    formatNumber(
                        stock.rsi14
                    )
                ),

                detailItem(
                    "ATR",
                    formatPrice(
                        stock.atr14
                    )
                ),

                detailItem(
                    "ATR %",
                    formatPercent(
                        stock.atr_pct
                    )
                ),

                detailItem(
                    "Volume",
                    formatLargeNumber(
                        stock.volume
                    )
                ),

                detailItem(
                    "Average Volume",
                    formatLargeNumber(
                        stock.avg_volume_20
                    )
                ),

                detailItem(
                    "Volume Ratio",
                    isValidNumber(
                        stock.volume_ratio
                    )
                        ? Number(
                            stock.volume_ratio
                        ).toFixed(2) + "x"
                        : "—"
                )

            ]
        )}


        ${detailSection(
            "52W & 200 DMA Structure",
            [

                detailItem(
                    "52W High",
                    formatPrice(
                        stock["52W_High"] ??
                        stock["52w_high"]
                    )
                ),

                detailItem(
                    "52W Low",
                    formatPrice(
                        stock["52W_Low"] ??
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
                    "200 DMA",
                    formatPrice(
                        stock.sma200
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
                ),

                detailItem(
                    "Previous Support",
                    formatPrice(
                        stock.support_20
                    )
                ),

                detailItem(
                    "Previous Resistance",
                    formatPrice(
                        stock.resistance_20
                    )
                )

            ]
        )}


        ${detailSection(
            "Company",
            [

                detailItem(
                    "Company",
                    stock.company_name
                ),

                detailItem(
                    "Sector",
                    stock.sector ||
                    stock.primary_sector
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
                        firstValue(
                            stock.revenue_cagr,
                            stock.revenue_cagr_3y,
                            stock.revenue_cagr_5y
                        )
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
                        firstValue(
                            stock.profit_cagr,
                            stock.profit_cagr_3y,
                            stock.profit_cagr_5y
                        )
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
                        firstValue(
                            stock.eps_cagr,
                            stock.eps_cagr_3y,
                            stock.eps_cagr_5y
                        )
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
                        stock.debt_to_equity
                    )
                ),

                detailItem(
                    "Current Ratio",
                    formatNumber(
                        stock.current_ratio
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
                        stock.pe_ratio
                    )
                ),

                detailItem(
                    "Forward PE",
                    formatNumber(
                        stock.forward_pe
                    )
                ),

                detailItem(
                    "PB",
                    formatNumber(
                        stock.pb_ratio
                    )
                ),

                detailItem(
                    "PEG",
                    formatNumber(
                        stock.peg_ratio
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
            "Why This Stock Is On Watch",
            [

                detailItem(
                    "Setup",
                    stock.setup
                ),

                detailItem(
                    "Technical Reason",
                    stock.technical_reason ||
                    stock.setup_reason
                ),

                detailItem(
                    "Fundamental Quality",
                    stock.fundamental_quality
                ),

                detailItem(
                    "Sector",
                    stock.primary_sector ||
                    stock.sector
                ),

                detailItem(
                    "Market Context",
                    dashboardData.market?.regime
                )

            ]
        )}

    `;

}


// ============================================================
// TRADE PLAN
// ============================================================

function renderTradePlan(
    stock,
    plan
) {

    const hasPlan =
        isValidNumber(
            plan.entry
        )
        &&
        isValidNumber(
            plan.stop
        )
        &&
        isValidNumber(
            plan.target1
        );


    if (!hasPlan) {

        return `

            <div class="trade-plan-panel">

                <div class="trade-plan-header">

                    <div>

                        <div class="trade-plan-label">
                            Trade Plan
                        </div>

                        <h3>
                            No Active Trade Plan
                        </h3>

                    </div>

                    <div class="trade-plan-status trade-plan-neutral">
                        ${escapeHtml(
                            plan.planStatus ||
                            "Neutral / Unavailable"
                        )}
                    </div>

                </div>

                <div class="trade-plan-reason">

                    Trade levels are not generated for
                    weak or neutral setups.

                </div>

            </div>

        `;

    }


    return `

        <div class="trade-plan-panel">

            <div class="trade-plan-header">

                <div>

                    <div class="trade-plan-label">
                        Engine Generated Trade Plan
                    </div>

                    <h3>
                        ${escapeHtml(
                            plan.planType
                        )}
                    </h3>

                </div>

                <div class="trade-plan-status ${getTradePlanClass(
                    plan.planStatus
                )}">
                    ${escapeHtml(
                        plan.planStatus ||
                        "Watch"
                    )}
                </div>

            </div>


            <div class="trade-plan-grid">

                <div class="trade-plan-card">

                    <span>
                        Entry
                    </span>

                    <strong class="trade-entry">

                        ${
                            isValidNumber(
                                plan.entryLow
                            )
                            &&
                            isValidNumber(
                                plan.entryHigh
                            )

                                ?

                                `${formatPrice(
                                    plan.entryLow
                                )} - ${formatPrice(
                                    plan.entryHigh
                                )}`

                                :

                                formatPrice(
                                    plan.entry
                                )
                        }

                    </strong>

                </div>


                <div class="trade-plan-card">

                    <span>
                        Stop Loss
                    </span>

                    <strong class="trade-stop">
                        ${formatPrice(
                            plan.stop
                        )}
                    </strong>

                </div>


                <div class="trade-plan-card">

                    <span>
                        Target 1
                    </span>

                    <strong class="trade-target">
                        ${formatPrice(
                            plan.target1
                        )}
                    </strong>

                </div>


                <div class="trade-plan-card">

                    <span>
                        Target 2
                    </span>

                    <strong class="trade-target">
                        ${formatPrice(
                            plan.target2
                        )}
                    </strong>

                </div>


                <div class="trade-plan-card">

                    <span>
                        Risk / Reward T1
                    </span>

                    <strong>
                        ${formatRiskReward(
                            plan.rr1
                        )}
                    </strong>

                </div>


                <div class="trade-plan-card">

                    <span>
                        Risk / Reward T2
                    </span>

                    <strong>
                        ${formatRiskReward(
                            plan.rr2
                        )}
                    </strong>

                </div>


                <div class="trade-plan-card">

                    <span>
                        Trade Quality
                    </span>

                    <strong>
                        ${escapeHtml(
                            plan.quality ||
                            "—"
                        )}
                    </strong>

                </div>

            </div>


            ${
                plan.planReason

                    ?

                    `
                        <div class="trade-plan-reason">

                            <strong>
                                Reason:
                            </strong>

                            ${escapeHtml(
                                plan.planReason
                            )}

                        </div>
                    `

                    :

                    ""
            }


            ${
                plan.invalidation

                    ?

                    `
                        <div class="trade-plan-reason">

                            <strong>
                                Invalidation:
                            </strong>

                            ${escapeHtml(
                                plan.invalidation
                            )}

                        </div>
                    `

                    :

                    ""
            }

        </div>

    `;

}


// ============================================================
// DETAIL HELPERS
// ============================================================

function detailSection(
    title,
    items
) {

    const valid =
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

                ${valid.join("")}

            </div>

        </div>

    `;

}


function detailItem(
    label,
    value
) {

    if (
        value === undefined ||
        value === null ||
        value === "" ||
        value === "NaN" ||
        value === "nan"
    ) {

        value =
            "Unavailable";

    }


    return `

        <div class="detail-item">

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

        </div>

    `;

}


// ============================================================
// WATCHLIST MEMBERSHIP
// ============================================================

function findWatchlistMembership(
    symbol
) {

    const names = [];


    Object.entries(
        dashboardData.watchlists ||
        {}
    ).forEach(
        ([key, list]) => {

            if (
                !Array.isArray(
                    list
                )
            ) {
                return;
            }


            const exists =
                list.some(
                    stock =>
                        String(
                            stock.symbol ||
                            stock.nse_symbol ||
                            ""
                        ).toUpperCase()
                        ===
                        String(
                            symbol
                        ).toUpperCase()
                );


            if (exists) {

                names.push(
                    WATCHLIST_NAMES[
                        key
                    ] ||
                    key
                );

            }

        }
    );


    return names.length
        ? names.join(", ")
        : "Master Ranking";

}


// ============================================================
// TRADE VALUES
// ============================================================

function tradeValue(
    stock,
    key
) {

    const aliases = {

        entry_price: [
            "entry_price",
            "entry",
            "Entry_Price"
        ],

        entry_low: [
            "entry_low",
            "Entry_Low"
        ],

        entry_high: [
            "entry_high",
            "Entry_High"
        ],

        stop_loss: [
            "stop_loss",
            "stop",
            "Stop_Loss"
        ],

        target_1: [
            "target_1",
            "target1",
            "Target_1"
        ],

        target_2: [
            "target_2",
            "target2",
            "Target_2"
        ]

    };


    const keys =
        aliases[key] ||
        [key];


    for (
        const field of keys
    ) {

        if (
            isValidNumber(
                stock[field]
            )
        ) {

            return Number(
                stock[field]
            );

        }

    }


    return null;

}


// ============================================================
// STATUS / BADGES
// ============================================================

function statusBadge(
    value
) {

    if (
        value === undefined ||
        value === null ||
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
        lower.includes("strong bullish") ||
        lower.includes("bullish") ||
        lower.includes("positive") ||
        lower.includes("breakout")
    ) {

        className =
            "badge-positive";

    }
    else if (
        lower.includes("bearish") ||
        lower.includes("negative") ||
        lower.includes("avoid") ||
        lower.includes("weak")
    ) {

        className =
            "badge-negative";

    }


    return `

        <span class="status-badge ${className}">
            ${escapeHtml(text)}
        </span>

    `;

}


function getRegimeClass(
    value
) {

    const text =
        String(
            value ||
            ""
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
        text.includes(
            "weak"
        )
        ||
        text.includes(
            "cautious"
        )
    ) {

        return "regime-caution";

    }


    return "regime-neutral";

}


function getEnvironmentClass(
    value
) {

    const text =
        String(
            value ||
            ""
        ).toLowerCase();


    if (
        text.includes(
            "favorable"
        )
        ||
        text.includes(
            "positive"
        )
        ||
        text.includes(
            "selective"
        )
    ) {

        return "positive";

    }


    if (
        text.includes(
            "avoid"
        )
        ||
        text.includes(
            "high risk"
        )
        ||
        text.includes(
            "very high"
        )
        ||
        text.includes(
            "defensive"
        )
    ) {

        return "negative";

    }


    return "neutral";

}


function getTradePlanClass(
    value
) {

    const text =
        String(
            value ||
            ""
        ).toLowerCase();


    if (
        text.includes(
            "strong"
        )
        ||
        text.includes(
            "active"
        )
        ||
        text.includes(
            "confirmed"
        )
    ) {

        return "trade-plan-positive";

    }


    if (
        text.includes(
            "poor"
        )
        ||
        text.includes(
            "avoid"
        )
        ||
        text.includes(
            "invalid"
        )
    ) {

        return "trade-plan-negative";

    }


    if (
        text.includes(
            "watch"
        )
        ||
        text.includes(
            "confirm"
        )
    ) {

        return "trade-plan-watch";

    }


    return "trade-plan-neutral";

}


function riskRewardClass(
    value
) {

    if (
        !isValidNumber(value)
    ) {

        return "neutral";

    }


    const number =
        Number(value);


    if (
        number >= 2
    ) {

        return "positive";

    }


    if (
        number >= 1.5
    ) {

        return "neutral";

    }


    return "negative";

}


// ============================================================
// FORMATTING
// ============================================================

function formatPrice(
    value
) {

    if (
        !isValidNumber(
            value
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
    value,
    decimals = 2
) {

    if (
        !isValidNumber(
            value
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
        !isValidNumber(
            value
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
        !isValidNumber(
            value
        )
    ) {

        return "—";

    }


    return (

        Number(
            value
        ).toFixed(2) +

        "%"

    );

}


function formatSignedPercent(
    value
) {

    if (
        !isValidNumber(
            value
        )
    ) {

        return "—";

    }


    const number =
        Number(value);


    return (

        (
            number > 0
                ? "+"
                : ""
        )

        +

        number.toFixed(2)

        +

        "%"

    );

}


function formatRiskReward(
    value
) {

    if (
        !isValidNumber(
            value
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


function formatLargeNumber(
    value
) {

    if (
        !isValidNumber(
            value
        )
    ) {

        return "—";

    }


    const number =
        Number(value);


    if (
        Math.abs(
            number
        ) >= 1e7
    ) {

        return (

            "₹" +

            (
                number /
                1e7
            ).toFixed(2)

            +

            " Cr"

        );

    }


    if (
        Math.abs(
            number
        ) >= 1e5
    ) {

        return (

            "₹" +

            (
                number /
                1e5
            ).toFixed(2)

            +

            " L"

        );

    }


    return (

        "₹" +

        number.toLocaleString(
            "en-IN",
            {
                maximumFractionDigits:
                    0
            }
        )

    );

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
        !isValidNumber(value)
        ||
        !isValidNumber(total)
        ||
        Number(total) === 0
    ) {

        return "";

    }


    return (

        (
            Number(value) /
            Number(total) *
            100
        ).toFixed(2)

        +

        "%"

    );

}


function isValidNumber(
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


    const number =
        Number(value);


    return Number.isFinite(
        number
    );

}


function firstValue(
    ...values
) {

    for (
        const value of values
    ) {

        if (
            value !== undefined &&
            value !== null &&
            value !== ""
        ) {

            return value;

        }

    }


    return null;

}


// ============================================================
// CHANGE / RISK
// ============================================================

function getChangeClass(
    value
) {

    if (
        !isValidNumber(
            value
        )
    ) {

        return "";

    }


    const number =
        Number(value);


    if (
        number > 0
    ) {

        return "positive";

    }


    if (
        number < 0
    ) {

        return "negative";

    }


    return "neutral";

}


function vixRiskLabel(
    value
) {

    if (
        !isValidNumber(
            value
        )
    ) {

        return "—";

    }


    const number =
        Number(value);


    if (
        number >= 25
    ) {

        return "Very High";

    }


    if (
        number >= 20
    ) {

        return "High";

    }


    if (
        number >= 15
    ) {

        return "Normal";

    }


    if (
        number >= 12
    ) {

        return "Low";

    }


    return "Very Low";

}


// ============================================================
// ESCAPING
// ============================================================

function escapeHtml(
    value
) {

    if (
        value === null ||
        value === undefined
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


function escapeJs(
    value
) {

    return String(
        value ||
        ""
    )
        .replace(
            /\\/g,
            "\\\\"
        )
        .replace(
            /'/g,
            "\\'"
        )
        .replace(
            /"/g,
            '\\"'
        );

}


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


    const marketDate =
        dashboardData.market?.market_data_date;


    let text = "";


    if (marketDate) {

        text +=
            "Market date: " +
            marketDate;

    }


    if (generated) {

        const date =
            new Date(
                generated
            );


        if (
            !isNaN(
                date.getTime()
            )
        ) {

            if (text) {
                text += " • ";
            }


            text +=
                "Dashboard updated: " +
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

    }


    element.textContent =
        text ||
        "Data timestamp unavailable.";

}


// ============================================================
// ERROR
// ============================================================

function showDashboardError(
    message
) {

    const ids = [

        "marketRegime",

        "marketIndexGrid",

        "marketEnvironmentGrid",

        "marketAnalysisGrid",

        "breadthCards",

        "stockTable"

    ];


    ids.forEach(
        id => {

            const element =
                document.getElementById(
                    id
                );


            if (!element) {
                return;
            }


            if (
                element.tagName
                ===
                "TBODY"
            ) {

                element.innerHTML = `

                    <tr>

                        <td
                            colspan="20"
                            class="error-state"
                        >
                            ${escapeHtml(
                                message
                            )}
                        </td>

                    </tr>

                `;

            }
            else {

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
// GLOBAL EXPORTS
// ============================================================

window.dashboardData =
    dashboardData;

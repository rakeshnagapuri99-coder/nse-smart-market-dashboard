/* =========================================================
   NSE SMART MARKET DASHBOARD V3
   Dashboard frontend
========================================================= */

(() => {

    "use strict";


    /* =====================================================
       CONFIG
    ===================================================== */

    const DATA_URL =
        "output/dashboard_data.json?v=" + Date.now();

    const TOP_ROWS = 15;

    let dashboardData = {};

    let allStocks = [];

    let watchlists = {};

    let currentWatchlist = "next_day";

    let currentWatchlistData = [];

    let currentFilteredData = [];


    const WATCHLIST_META = {

        next_day: {
            title: "Next Day Watchlist",
            short: "Next Day"
        },

        intraday: {
            title: "Intraday Watchlist",
            short: "Intraday"
        },

        swing: {
            title: "Equity Swing Watchlist",
            short: "Swing"
        },

        long_term: {
            title: "Long-Term Investment",
            short: "Long Term"
        },

        "52w_high": {
            title: "52W High Watchlist",
            short: "52W High"
        },

        dma_recovery: {
            title: "200 DMA Recovery",
            short: "200 DMA"
        },

        momentum: {
            title: "Momentum Watchlist",
            short: "Momentum"
        },

        breakout: {
            title: "Breakout Watchlist",
            short: "Breakout"
        },

        options: {
            title: "Options Underlying Watch",
            short: "Options"
        }

    };


    /* =====================================================
       HELPERS
    ===================================================== */

    function $(id) {

        return document.getElementById(id);

    }


    function number(value) {

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


    function text(value) {

        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {

            return "—";

        }

        return String(value);

    }


    function formatNumber(value, decimals = 2) {

        const n = number(value);

        if (n === null) return "—";

        return n.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }
        );

    }


    function formatPrice(value) {

        const n = number(value);

        if (n === null) return "—";

        return "₹" + formatNumber(n, 2);

    }


    function formatPercent(value) {

        const n = number(value);

        if (n === null) return "—";

        return (
            n > 0 ? "+" : ""
        ) + n.toFixed(2) + "%";

    }


    function formatScore(value) {

        const n = number(value);

        if (n === null) return "—";

        return n.toFixed(1);

    }


    function escapeHTML(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    function stockArray(value) {

        if (!value) return [];

        if (Array.isArray(value)) {

            return value;

        }

        if (Array.isArray(value.data)) {

            return value.data;

        }

        if (Array.isArray(value.stocks)) {

            return value.stocks;

        }

        if (typeof value === "object") {

            return Object.values(value)
                .filter(
                    item =>
                        item &&
                        typeof item === "object" &&
                        !Array.isArray(item)
                );

        }

        return [];

    }


    /* =====================================================
       STOCK NORMALIZATION
    ===================================================== */

    function normalizeStock(raw) {

        const s = {
            ...raw
        };


        s.symbol = text(
            first(
                s,
                [
                    "symbol",
                    "Symbol",
                    "ticker",
                    "Ticker",
                    "NSE_Symbol",
                    "Stock",
                    "stock"
                ]
            )
        )
        .replace(".NS", "")
        .trim();


        s.company_name = text(
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
            )
        );


        /*
         IMPORTANT:
         Technical engine uses Close.
         Therefore Close is explicitly included
         before generic price fields.
        */

        s.price = number(
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
                    "Current_Price",
                    "Last_Price"
                ]
            )
        );


        s.close = number(
            first(
                s,
                [
                    "Close",
                    "close",
                    "Price",
                    "price",
                    "LTP",
                    "ltp",
                    "CMP"
                ]
            )
        );


        s.previous_close = number(
            first(
                s,
                [
                    "Previous_Close",
                    "previous_close",
                    "Prev_Close",
                    "previousClose"
                ]
            )
        );


        s.daily_return_pct = number(
            first(
                s,
                [
                    "Daily_Return_Pct",
                    "daily_return_pct",
                    "Daily_Change_Pct",
                    "Change_Pct",
                    "change_pct",
                    "Change"
                ]
            )
        );


        s.sma20 = number(
            first(
                s,
                [
                    "SMA_20",
                    "SMA20",
                    "sma20"
                ]
            )
        );


        s.sma50 = number(
            first(
                s,
                [
                    "SMA_50",
                    "SMA50",
                    "sma50"
                ]
            )
        );


        s.sma100 = number(
            first(
                s,
                [
                    "SMA_100",
                    "SMA100",
                    "sma100"
                ]
            )
        );


        s.sma200 = number(
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


        s.high52 = number(
            first(
                s,
                [
                    "52W_High",
                    "52WHigh",
                    "Rolling_52W_High",
                    "High_52W",
                    "high_52w"
                ]
            )
        );


        s.low52 = number(
            first(
                s,
                [
                    "52W_Low",
                    "52WLow",
                    "Rolling_52W_Low",
                    "Low_52W",
                    "low_52w"
                ]
            )
        );


        s.rsi = number(
            first(
                s,
                [
                    "RSI14",
                    "RSI_14",
                    "rsi14",
                    "RSI"
                ]
            )
        );


        s.volume_ratio = number(
            first(
                s,
                [
                    "Volume_Ratio",
                    "volume_ratio",
                    "Vol_Ratio",
                    "VolumeRatio"
                ]
            )
        );


        s.technical_score = number(
            first(
                s,
                [
                    "Technical_Score",
                    "technical_score"
                ]
            )
        );


        s.fundamental_score = number(
            first(
                s,
                [
                    "Fundamental_Score",
                    "fundamental_score"
                ]
            )
        );


        s.overall_score = number(
            first(
                s,
                [
                    "Overall_Score",
                    "overall_score",
                    "Score",
                    "score",
                    "Rank_Score"
                ]
            )
        );


        s.trend = text(
            first(
                s,
                [
                    "Trend",
                    "trend"
                ]
            )
        );


        s.momentum = text(
            first(
                s,
                [
                    "Momentum",
                    "momentum"
                ]
            )
        );


        s.setup = text(
            first(
                s,
                [
                    "Setup",
                    "setup",
                    "Setup_Type",
                    "setup_type",
                    "Trade_Setup",
                    "trade_setup"
                ]
            )
        );


        s.sector = text(
            first(
                s,
                [
                    "Primary_Sector",
                    "primary_sector",
                    "Sector",
                    "sector"
                ]
            )
        );


        /* Trade plan */

        s.entry = number(
            first(
                s,
                [
                    "entry_price",
                    "Entry_Price",
                    "Entry",
                    "entry"
                ]
            )
        );


        s.entry_low = number(
            first(
                s,
                [
                    "entry_low",
                    "Entry_Low",
                    "Entry_Zone_Low"
                ]
            )
        );


        s.entry_high = number(
            first(
                s,
                [
                    "entry_high",
                    "Entry_High",
                    "Entry_Zone_High"
                ]
            )
        );


        s.stop = number(
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


        s.target1 = number(
            first(
                s,
                [
                    "target_1",
                    "Target_1",
                    "T1"
                ]
            )
        );


        s.target2 = number(
            first(
                s,
                [
                    "target_2",
                    "Target_2",
                    "T2"
                ]
            )
        );


        s.rr = number(
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


        s.plan_status = text(
            first(
                s,
                [
                    "trade_plan_status",
                    "Trade_Plan_Status",
                    "Plan_Status"
                ]
            )
        );


        s.plan_type = text(
            first(
                s,
                [
                    "trade_plan_type",
                    "Trade_Plan_Type",
                    "Plan_Type"
                ]
            )
        );


        s.plan_reason = text(
            first(
                s,
                [
                    "trade_plan_reason",
                    "Trade_Plan_Reason",
                    "Plan_Reason"
                ]
            )
        );


        s.invalidation = text(
            first(
                s,
                [
                    "trade_plan_invalidation",
                    "Trade_Plan_Invalidation",
                    "Invalidation"
                ]
            )
        );


        s.trade_quality = text(
            first(
                s,
                [
                    "trade_plan_quality",
                    "Trade_Plan_Quality",
                    "Trade_Quality"
                ]
            )
        );


        return s;

    }


    /* =====================================================
       DATA EXTRACTION
    ===================================================== */

    function normalizeDashboardData(data) {

        dashboardData = data || {};


        /*
         Try all common locations.
        */

        const possibleStocks = [

            data.stocks,

            data.stock_data,

            data.ranked_stocks,

            data.ranking,

            data.data?.stocks,

            data.dashboard?.stocks

        ];


        let rawStocks = [];


        for (const source of possibleStocks) {

            const arr = stockArray(source);

            if (arr.length > 0) {

                rawStocks = arr;

                break;

            }

        }


        allStocks = rawStocks
            .map(normalizeStock)
            .filter(
                stock =>
                    stock.symbol &&
                    stock.symbol !== "—"
            );


        /*
         Watchlists
        */

        const rawWatchlists =
            data.watchlists ||
            data.watchlist ||
            data.data?.watchlists ||
            data.dashboard?.watchlists ||
            {};


        watchlists = {};


        Object.keys(WATCHLIST_META).forEach(
            key => {

                const source =
                    rawWatchlists[key] ||
                    rawWatchlists[
                        WATCHLIST_META[key].title
                    ] ||
                    [];


                watchlists[key] =
                    stockArray(source)
                        .map(normalizeStock)
                        .filter(
                            stock =>
                                stock.symbol &&
                                stock.symbol !== "—"
                        );

            }
        );


        /*
         If backend has stocks but no watchlists,
         create practical fallback lists.
        */

        if (
            !Object.values(watchlists)
                .some(list => list.length > 0)
        ) {

            buildFallbackWatchlists();

        }

    }


    /* =====================================================
       FALLBACK WATCHLISTS
    ===================================================== */

    function sortedStocks() {

        return [...allStocks]
            .sort(
                (a, b) =>
                    (b.overall_score || 0) -
                    (a.overall_score || 0)
            );

    }


    function buildFallbackWatchlists() {

        const stocks = sortedStocks();


        const positiveTrend = stock =>
            /positive|strong|bull/i.test(
                stock.trend
            );


        const momentum = stock =>
            /positive|strong/i.test(
                stock.momentum
            );


        watchlists.next_day =
            stocks.filter(
                stock =>
                    /breakout|momentum|recovery/i.test(
                        stock.setup
                    ) ||
                    (
                        positiveTrend(stock) &&
                        stock.price !== null &&
                        stock.sma200 !== null &&
                        stock.price > stock.sma200
                    )
            );


        watchlists.intraday =
            stocks.filter(
                stock =>
                    /breakout|momentum/i.test(
                        stock.setup
                    ) &&
                    (stock.volume_ratio || 0) >= 1.2
            );


        watchlists.swing =
            stocks.filter(
                stock =>
                    /breakout|momentum|recovery|swing/i.test(
                        stock.setup
                    ) ||
                    positiveTrend(stock)
            );


        watchlists.long_term =
            stocks.filter(
                stock =>
                    stock.price !== null &&
                    stock.sma200 !== null &&
                    stock.price > stock.sma200 &&
                    (stock.overall_score || 0) >= 55
            );


        watchlists["52w_high"] =
            stocks.filter(
                stock =>
                    /52w|high/i.test(
                        stock.setup
                    ) ||
                    (
                        stock.price !== null &&
                        stock.high52 !== null &&
                        stock.price >=
                        stock.high52 * 0.97
                    )
            );


        watchlists.dma_recovery =
            stocks.filter(
                stock =>
                    /200|dma|recovery/i.test(
                        stock.setup
                    ) ||
                    (
                        stock.price !== null &&
                        stock.sma200 !== null &&
                        Math.abs(
                            stock.price /
                            stock.sma200 - 1
                        ) <= 0.03
                    )
            );


        watchlists.momentum =
            stocks.filter(
                stock =>
                    /momentum/i.test(
                        stock.setup
                    ) ||
                    momentum(stock)
            );


        watchlists.breakout =
            stocks.filter(
                stock =>
                    /breakout/i.test(
                        stock.setup
                    )
            );


        watchlists.options =
            stocks.filter(
                stock =>
                    /breakout|momentum|52w/i.test(
                        stock.setup
                    ) &&
                    (stock.overall_score || 0) >= 50
            );

    }


    /* =====================================================
       MARKET DATA
    ===================================================== */

    function getMarketObject() {

        return (
            dashboardData.market_regime ||
            dashboardData.market ||
            dashboardData.market_context ||
            dashboardData.dashboard?.market_regime ||
            {}
        );

    }


    function getBreadthObject() {

        return (
            dashboardData.market_breadth ||
            dashboardData.breadth ||
            dashboardData.dashboard?.market_breadth ||
            {}
        );

    }


    function getSectorData() {

        return stockArray(
            dashboardData.sector_analysis ||
            dashboardData.sectors ||
            dashboardData.dashboard?.sector_analysis ||
            []
        );

    }


    /* =====================================================
       MARKET REGIME
    ===================================================== */

    function regimeClass(regime) {

        const r =
            String(regime || "")
                .toLowerCase();


        if (
            r.includes("bull")
        ) {

            return "regime-bullish";

        }


        if (
            r.includes("bear")
        ) {

            return "regime-bearish";

        }


        if (
            r.includes("weak") ||
            r.includes("caution") ||
            r.includes("risk")
        ) {

            return "regime-caution";

        }


        return "regime-neutral";

    }


    function renderMarketRegime() {

        const container =
            $("marketRegime");

        if (!container) return;


        const market =
            getMarketObject();


        const regime =
            first(
                market,
                [
                    "market_regime",
                    "Market_Regime",
                    "regime",
                    "Regime"
                ]
            ) ||
            dashboardData.market_regime_name ||
            dashboardData.regime ||
            "Unavailable";


        const marketScore =
            number(
                first(
                    market,
                    [
                        "market_score",
                        "Market_Score",
                        "score",
                        "Score"
                    ]
                )
            );


        const description =
            first(
                market,
                [
                    "regime_description",
                    "market_description",
                    "description",
                    "interpretation"
                ]
            );


        container.innerHTML = `

            <div class="regime-main">

                <div>

                    <div class="regime-label">
                        CURRENT MARKET ENVIRONMENT
                    </div>

                    <div style="margin-top:8px">

                        <span class="regime-badge ${regimeClass(regime)}">
                            ${escapeHTML(regime)}
                        </span>

                    </div>

                    ${
                        description
                        ?
                        `<div class="regime-description">
                            ${escapeHTML(description)}
                        </div>`
                        :
                        ""
                    }

                </div>


                <div class="regime-score">

                    <strong>
                        ${marketScore === null
                            ? "—"
                            : marketScore.toFixed(2)}
                    </strong>

                    <small>
                        / 100
                    </small>

                </div>

            </div>

        `;

    }


    /* =====================================================
       MARKET INDEX
    ===================================================== */

    function getIndexData(prefix) {

        const market =
            getMarketObject();


        const result = {};


        if (prefix === "nifty") {

            result.price =
                number(
                    first(
                        market,
                        [
                            "nifty_price",
                            "Nifty_Price",
                            "nifty_close",
                            "nifty_last_close"
                        ]
                    )
                );


            result.previous =
                number(
                    first(
                        market,
                        [
                            "nifty_previous_close",
                            "Nifty_Previous_Close",
                            "nifty_prev_close"
                        ]
                    )
                );


            result.change =
                number(
                    first(
                        market,
                        [
                            "nifty_daily_return_pct",
                            "nifty_change_pct",
                            "nifty_daily_change"
                        ]
                    )
                );


            result.trend =
                first(
                    market,
                    [
                        "nifty_trend",
                        "Nifty_Trend"
                    ]
                );


            result.momentum =
                first(
                    market,
                    [
                        "nifty_momentum",
                        "Nifty_Momentum"
                    ]
                );


            result.rsi =
                number(
                    first(
                        market,
                        [
                            "nifty_rsi",
                            "Nifty_RSI"
                        ]
                    )
                );

        }


        if (prefix === "bank") {

            result.price =
                number(
                    first(
                        market,
                        [
                            "bank_nifty_price",
                            "Bank_Nifty_Price",
                            "bank_nifty_close"
                        ]
                    )
                );


            result.previous =
                number(
                    first(
                        market,
                        [
                            "bank_nifty_previous_close",
                            "Bank_Nifty_Previous_Close",
                            "bank_nifty_prev_close"
                        ]
                    )
                );


            result.change =
                number(
                    first(
                        market,
                        [
                            "bank_nifty_daily_return_pct",
                            "bank_nifty_change_pct",
                            "bank_nifty_daily_change"
                        ]
                    )
                );


            result.trend =
                first(
                    market,
                    [
                        "bank_nifty_trend",
                        "Bank_Nifty_Trend"
                    ]
                );


            result.momentum =
                first(
                    market,
                    [
                        "bank_nifty_momentum",
                        "Bank_Nifty_Momentum"
                    ]
                );


            result.rsi =
                number(
                    first(
                        market,
                        [
                            "bank_nifty_rsi",
                            "Bank_Nifty_RSI"
                        ]
                    )
                );

        }


        return result;

    }


    function renderMarketIndices() {

        const nifty =
            getIndexData("nifty");


        const bank =
            getIndexData("bank");


        if ($("niftyPrice")) {

            $("niftyPrice").textContent =
                formatPrice(nifty.price);

        }


        if ($("niftySecondary")) {

            let secondary = "Last completed close";

            if (nifty.change !== null) {

                secondary +=
                    " • " +
                    formatPercent(nifty.change);

            }

            $("niftySecondary").textContent =
                secondary;

            $("niftySecondary").className =
                "index-secondary " +
                (
                    nifty.change > 0
                        ? "positive"
                        : nifty.change < 0
                            ? "negative"
                            : "neutral"
                );

        }


        if ($("niftyTrend")) {

            $("niftyTrend").textContent =
                text(nifty.trend);

        }


        if ($("niftyMomentum")) {

            $("niftyMomentum").textContent =
                text(nifty.momentum);

        }


        if ($("niftyRSI")) {

            $("niftyRSI").textContent =
                nifty.rsi === null
                    ? "—"
                    : nifty.rsi.toFixed(1);

        }


        if ($("niftyMeta")) {

            $("niftyMeta").setAttribute(
                "title",
                nifty.previous !== null
                    ? "Previous close: " +
                      formatPrice(nifty.previous)
                    : ""
            );

        }


        if ($("bankNiftyPrice")) {

            $("bankNiftyPrice").textContent =
                formatPrice(bank.price);

        }


        if ($("bankNiftySecondary")) {

            let secondary =
                "Last completed close";

            if (bank.change !== null) {

                secondary +=
                    " • " +
                    formatPercent(bank.change);

            }

            $("bankNiftySecondary").textContent =
                secondary;

            $("bankNiftySecondary").className =
                "index-secondary " +
                (
                    bank.change > 0
                        ? "positive"
                        : bank.change < 0
                            ? "negative"
                            : "neutral"
                );

        }


        if ($("bankNiftyTrend")) {

            $("bankNiftyTrend").textContent =
                text(bank.trend);

        }


        if ($("bankNiftyMomentum")) {

            $("bankNiftyMomentum").textContent =
                text(bank.momentum);

        }


        if ($("bankNiftyRSI")) {

            $("bankNiftyRSI").textContent =
                bank.rsi === null
                    ? "—"
                    : bank.rsi.toFixed(1);

        }


        if ($("bankNiftyMeta")) {

            $("bankNiftyMeta").setAttribute(
                "title",
                bank.previous !== null
                    ? "Previous close: " +
                      formatPrice(bank.previous)
                    : ""
            );

        }


        const market =
            getMarketObject();


        const vix =
            number(
                first(
                    market,
                    [
                        "vix",
                        "india_vix",
                        "India_VIX",
                        "vix_value"
                    ]
                )
            );


        const vixInterpretation =
            first(
                market,
                [
                    "vix_interpretation",
                    "vix_status",
                    "vix_environment"
                ]
            );


        if ($("vixValue")) {

            $("vixValue").textContent =
                vix === null
                    ? "Unavailable"
                    : vix.toFixed(2);

        }


        if ($("vixInterpretation")) {

            $("vixInterpretation").textContent =
                text(vixInterpretation);

        }


        if ($("vixMarket")) {

            $("vixMarket").textContent =
                text(
                    first(
                        market,
                        [
                            "vix_market",
                            "vix_market_condition"
                        ]
                    )
                );

        }


        if ($("vixRisk")) {

            $("vixRisk").textContent =
                text(
                    first(
                        market,
                        [
                            "vix_risk",
                            "vix_risk_level"
                        ]
                    )
                );

        }


        if ($("vixMode")) {

            $("vixMode").textContent =
                text(
                    first(
                        market,
                        [
                            "vix_mode",
                            "volatility_mode"
                        ]
                    )
                );

        }

    }


    /* =====================================================
       ENVIRONMENT
    ===================================================== */

    function renderEnvironment() {

        const container =
            $("marketEnvironmentGrid");

        if (!container) return;


        const market =
            getMarketObject();


        const environments = [

            [
                "Equity",
                first(
                    market,
                    [
                        "equity_environment",
                        "Equity_Environment"
                    ]
                )
            ],

            [
                "Swing",
                first(
                    market,
                    [
                        "swing_environment",
                        "Swing_Environment"
                    ]
                )
            ],

            [
                "Breakout",
                first(
                    market,
                    [
                        "breakout_environment",
                        "Breakout_Environment"
                    ]
                )
            ],

            [
                "Intraday",
                first(
                    market,
                    [
                        "intraday_environment",
                        "Intraday_Environment"
                    ]
                )
            ],

            [
                "Options",
                first(
                    market,
                    [
                        "options_environment",
                        "Options_Environment"
                    ]
                )
            ]

        ];


        container.innerHTML =
            environments
                .map(
                    ([label, value]) => `

                        <div class="environment-card">

                            <span>
                                ${label}
                            </span>

                            <strong class="${valueClass(value)}">
                                ${escapeHTML(
                                    text(value)
                                )}
                            </strong>

                        </div>

                    `
                )
                .join("");

    }


    function valueClass(value) {

        const v =
            String(value || "")
                .toLowerCase();


        if (
            v.includes("bull") ||
            v.includes("positive") ||
            v.includes("strong") ||
            v.includes("selective")
        ) {

            return "positive";

        }


        if (
            v.includes("bear") ||
            v.includes("avoid") ||
            v.includes("weak") ||
            v.includes("high risk")
        ) {

            return "negative";

        }


        if (
            v.includes("caution") ||
            v.includes("moderate") ||
            v.includes("watch")
        ) {

            return "text-amber";

        }


        return "neutral";

    }


    /* =====================================================
       MARKET ANALYSIS
    ===================================================== */

    function renderMarketAnalysis() {

        const market =
            getMarketObject();


        const support =
            first(
                market,
                [
                    "nifty_support",
                    "support",
                    "support_zone",
                    "next_day_support"
                ]
            );


        const resistance =
            first(
                market,
                [
                    "nifty_resistance",
                    "resistance",
                    "resistance_zone",
                    "next_day_resistance"
                ]
            );


        const pivot =
            first(
                market,
                [
                    "nifty_pivot",
                    "pivot",
                    "pivot_level"
                ]
            );


        const bullish =
            first(
                market,
                [
                    "bullish_trigger",
                    "nifty_bullish_trigger",
                    "bullishTrigger"
                ]
            );


        const bearish =
            first(
                market,
                [
                    "bearish_trigger",
                    "nifty_bearish_trigger",
                    "bearishTrigger"
                ]
            );


        if ($("marketSupport")) {

            $("marketSupport").textContent =
                formatPossibleLevel(support);

        }


        if ($("marketResistance")) {

            $("marketResistance").textContent =
                formatPossibleLevel(resistance);

        }


        if ($("marketPivot")) {

            $("marketPivot").textContent =
                formatPossibleLevel(pivot);

        }


        if ($("bullishTrigger")) {

            $("bullishTrigger").textContent =
                formatPossibleLevel(bullish);

        }


        if ($("bearishTrigger")) {

            $("bearishTrigger").textContent =
                formatPossibleLevel(bearish);

        }


        const scenario =
            first(
                market,
                [
                    "market_scenario",
                    "scenario",
                    "next_day_scenario",
                    "scenario_explanation",
                    "market_analysis"
                ]
            );


        if ($("marketScenario")) {

            $("marketScenario").textContent =
                scenario
                    ? String(scenario)
                    : generateMarketScenario();

        }

    }


    function formatPossibleLevel(value) {

        if (value === null || value === undefined) {

            return "—";

        }


        const n = number(value);

        if (n !== null) {

            return formatPrice(n);

        }


        return String(value);

    }


    function generateMarketScenario() {

        const market =
            getMarketObject();


        const regime =
            String(
                first(
                    market,
                    [
                        "market_regime",
                        "regime"
                    ]
                ) || ""
            ).toLowerCase();


        const niftyTrend =
            String(
                first(
                    market,
                    [
                        "nifty_trend"
                    ]
                ) || ""
            ).toLowerCase();


        const niftyMomentum =
            String(
                first(
                    market,
                    [
                        "nifty_momentum"
                    ]
                ) || ""
            ).toLowerCase();


        if (
            regime.includes("bear") ||
            regime.includes("weak")
        ) {

            return (
                "Market context is weak. " +
                "Prioritise capital protection and confirmation. " +
                "Prefer stocks with strong relative strength, " +
                "volume confirmation and valid risk/reward. " +
                "Avoid chasing breakdowns or weak breakouts."
            );

        }


        if (
            regime.includes("bull") &&
            (
                niftyTrend.includes("positive") ||
                niftyTrend.includes("bull")
            )
        ) {

            return (
                "Market structure is supportive. " +
                "Prefer stocks above key moving averages " +
                "with positive momentum and volume confirmation. " +
                "Breakouts are more actionable when price sustains above the trigger."
            );

        }


        return (
            "Market conditions are mixed. " +
            "Wait for price and volume confirmation around important levels. " +
            "Use the stock-level trade plan and invalidation level rather than relying on score alone."
        );

    }


    /* =====================================================
       BREADTH
    ===================================================== */

    function renderBreadth() {

        const container =
            $("breadthCards");

        if (!container) return;


        const breadth =
            getBreadthObject();


        const stocks =
            number(
                first(
                    breadth,
                    [
                        "stocks_analyzed",
                        "Stocks_Analyzed",
                        "total_stocks",
                        "Total_Stocks"
                    ]
                )
            );


        const above20 =
            number(
                first(
                    breadth,
                    [
                        "above_20_dma",
                        "Above_20_DMA"
                    ]
                )
            );


        const above50 =
            number(
                first(
                    breadth,
                    [
                        "above_50_dma",
                        "Above_50_DMA"
                    ]
                )
            );


        const above200 =
            number(
                first(
                    breadth,
                    [
                        "above_200_dma",
                        "Above_200_DMA"
                    ]
                )
            );


        const highs =
            number(
                first(
                    breadth,
                    [
                        "52w_highs",
                        "52W_Highs",
                        "highs"
                    ]
                )
            );


        const lows =
            number(
                first(
                    breadth,
                    [
                        "52w_lows",
                        "52W_Lows",
                        "lows"
                    ]
                )
            );


        const scoreValue =
            number(
                first(
                    breadth,
                    [
                        "breadth_score",
                        "Breadth_Score",
                        "score",
                        "Score"
                    ]
                )
            );


        const regime =
            first(
                breadth,
                [
                    "breadth_regime",
                    "Breadth_Regime",
                    "regime"
                ]
            );


        const cards = [

            [
                "Stocks Analysed",
                stocks,
                "NSE equity universe"
            ],

            [
                "Above 20 DMA",
                above20,
                percentageOf(
                    above20,
                    stocks
                )
            ],

            [
                "Above 50 DMA",
                above50,
                percentageOf(
                    above50,
                    stocks
                )
            ],

            [
                "Above 200 DMA",
                above200,
                percentageOf(
                    above200,
                    stocks
                )
            ],

            [
                "52W Highs",
                highs,
                "Rolling 52-week"
            ],

            [
                "52W Lows",
                lows,
                "Rolling 52-week"
            ]

        ];


        container.innerHTML =
            cards
                .map(
                    ([label, value, sub]) => `

                        <div class="breadth-card">

                            <div class="breadth-label">
                                ${label}
                            </div>

                            <div class="breadth-value">
                                ${
                                    value === null
                                        ? "—"
                                        : formatNumber(
                                            value,
                                            0
                                        )
                                }
                            </div>

                            <div class="breadth-sub">
                                ${escapeHTML(
                                    text(sub)
                                )}
                            </div>

                        </div>

                    `
                )
                .join("");


        if (regime) {

            container.insertAdjacentHTML(
                "beforeend",
                `
                <div class="breadth-card">

                    <div class="breadth-label">
                        Breadth Regime
                    </div>

                    <div class="breadth-value">
                        ${escapeHTML(
                            String(regime)
                        )}
                    </div>

                    <div class="breadth-sub">
                        Score:
                        ${
                            scoreValue === null
                                ? "—"
                                : scoreValue.toFixed(2)
                        }
                    </div>

                </div>
                `
            );

        }

    }


    function percentageOf(part, total) {

        if (
            part === null ||
            total === null ||
            total === 0
        ) {

            return "—";

        }

        return (
            (part / total) * 100
        ).toFixed(1) + "%";

    }


    /* =====================================================
       SECTORS
    ===================================================== */

    function renderSectors() {

        const table =
            $("sectorTable");

        if (!table) return;


        const tbody =
            table.querySelector("tbody");


        if (!tbody) return;


        const sectors =
            getSectorData();


        if (!sectors.length) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        Sector data unavailable.
                    </td>
                </tr>
            `;

            return;

        }


        const normalized =
            sectors
                .map(row => {

                    const s = {...row};


                    s.name =
                        text(
                            first(
                                s,
                                [
                                    "sector",
                                    "Sector",
                                    "sector_name",
                                    "Sector_Name",
                                    "name",
                                    "Index"
                                ]
                            )
                        );


                    s.price =
                        number(
                            first(
                                s,
                                [
                                    "price",
                                    "Price",
                                    "Close",
                                    "close"
                                ]
                            )
                        );


                    s.trend =
                        text(
                            first(
                                s,
                                [
                                    "trend",
                                    "Trend"
                                ]
                            )
                        );


                    s.momentum =
                        text(
                            first(
                                s,
                                [
                                    "momentum",
                                    "Momentum"
                                ]
                            )
                        );


                    s.return20 =
                        number(
                            first(
                                s,
                                [
                                    "return_20d",
                                    "20D_Return",
                                    "20D_Return_Pct",
                                    "return_20d_pct",
                                    "performance_20d"
                                ]
                            )
                        );


                    s.score =
                        number(
                            first(
                                s,
                                [
                                    "score",
                                    "Score",
                                    "sector_score",
                                    "Sector_Score"
                                ]
                            )
                        );


                    return s;

                })
                .sort(
                    (a,b) =>
                        (b.score || 0) -
                        (a.score || 0)
                );


        tbody.innerHTML =
            normalized
                .map(
                    (s,index) => `

                    <tr>

                        <td>
                            ${index + 1}
                        </td>

                        <td>
                            <strong>
                                ${escapeHTML(s.name)}
                            </strong>
                        </td>

                        <td>
                            ${
                                s.price === null
                                    ? "—"
                                    : formatPrice(s.price)
                            }
                        </td>

                        <td class="${valueClass(s.trend)}">
                            ${escapeHTML(
                                s.trend
                            )}
                        </td>

                        <td class="${valueClass(s.momentum)}">
                            ${escapeHTML(
                                s.momentum
                            )}
                        </td>

                        <td class="${
                            s.return20 > 0
                                ? "positive"
                                : s.return20 < 0
                                    ? "negative"
                                    : "neutral"
                        }">
                            ${
                                s.return20 === null
                                    ? "—"
                                    : formatPercent(
                                        s.return20
                                    )
                            }
                        </td>

                        <td>
                            <strong>
                                ${
                                    s.score === null
                                        ? "—"
                                        : s.score.toFixed(1)
                                }
                            </strong>
                        </td>

                        <td>
                            <span class="status-badge ${
                                valueClass(s.trend)
                            }">
                                View
                            </span>
                        </td>

                    </tr>

                `
                )
                .join("");

    }


    /* =====================================================
       SETUP SUMMARY
    ===================================================== */

    function renderSetupSummary() {

        const counts =
            dashboardData.watchlist_counts ||
            dashboardData.watchlists_counts ||
            dashboardData.setup_counts ||
            {};


        const count =
            key => {

                if (
                    counts[key] !== undefined
                ) {

                    return number(
                        counts[key]
                    );

                }


                return (
                    watchlists[key]?.length || 0
                );

            };


        const mappings = {

            summary52wHigh: "52w_high",

            summaryDmaRecovery: "dma_recovery",

            summaryMomentum: "momentum",

            summaryBreakout: "breakout",

            summaryNextDay: "next_day",

            summaryOptions: "options"

        };


        Object.entries(mappings)
            .forEach(
                ([elementId,key]) => {

                    const el =
                        $(elementId);

                    if (!el) return;

                    el.textContent =
                        count(key);

                }
            );


        const cards =
            document.querySelectorAll(
                ".summary-card"
            );


        const mappingKeys = [
            "52w_high",
            "dma_recovery",
            "momentum",
            "breakout",
            "next_day",
            "options"
        ];


        cards.forEach(
            (card,index) => {

                const key =
                    mappingKeys[index];

                if (!key) return;


                card.onclick = () => {

                    switchWatchlist(
                        key
                    );

                    document
                        .getElementById(
                            "watchlistSection"
                        )
                        ?.scrollIntoView({
                            behavior:"smooth",
                            block:"start"
                        });

                };

            }
        );

    }


    /* =====================================================
       WATCHLIST TABS
    ===================================================== */

    function initializeWatchlistTabs() {

        const tabs =
            document.querySelectorAll(
                ".watchlist-tab"
            );


        tabs.forEach(
            tab => {

                tab.addEventListener(
                    "click",
                    () => {

                        const key =
                            tab.dataset.watchlist;

                        if (!key) return;

                        switchWatchlist(
                            key
                        );

                    }
                );

            }
        );

    }


    function switchWatchlist(key) {

        if (!WATCHLIST_META[key]) {

            key = "next_day";

        }


        currentWatchlist = key;


        document
            .querySelectorAll(
                ".watchlist-tab"
            )
            .forEach(
                tab => {

                    tab.classList.toggle(
                        "active",
                        tab.dataset.watchlist === key
                    );

                }
            );


        currentWatchlistData =
            Array.isArray(
                watchlists[key]
            )
                ? watchlists[key]
                : [];


        populateSetupFilter(
            currentWatchlistData
        );


        renderWatchlist();

    }


    function populateSetupFilter(stocks) {

        const select =
            $("setupFilter");

        if (!select) return;


        const current =
            select.value;


        const setups =
            [...new Set(
                stocks
                    .map(
                        stock =>
                            stock.setup
                    )
                    .filter(
                        value =>
                            value &&
                            value !== "—"
                    )
            )]
            .sort();


        select.innerHTML =
            `<option value="">
                All setups
             </option>`;


        setups.forEach(
            setup => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    setup;

                option.textContent =
                    setup;

                select.appendChild(
                    option
                );

            }
        );


        if (
            setups.includes(current)
        ) {

            select.value =
                current;

        }

    }


    function initializeWatchlistControls() {

        const search =
            $("stockSearch");

        const setup =
            $("setupFilter");


        if (search) {

            search.addEventListener(
                "input",
                renderWatchlist
            );

        }


        if (setup) {

            setup.addEventListener(
                "change",
                renderWatchlist
            );

        }


        const download =
            $("downloadWatchlist");


        if (download) {

            download.addEventListener(
                "click",
                exportCurrentWatchlist
            );

        }

    }


    /* =====================================================
       WATCHLIST RENDER
    ===================================================== */

    function renderWatchlist() {

        const table =
            $("stockTable");

        if (!table) return;


        const tbody =
            table.querySelector(
                "tbody"
            );


        if (!tbody) return;


        let stocks =
            Array.isArray(
                currentWatchlistData
            )
                ? [...currentWatchlistData]
                : [];


        const search =
            String(
                $("stockSearch")?.value || ""
            )
            .trim()
            .toLowerCase();


        const setup =
            $("setupFilter")?.value || "";


        if (search) {

            stocks =
                stocks.filter(
                    stock =>
                        stock.symbol
                            .toLowerCase()
                            .includes(search) ||

                        stock.company_name
                            .toLowerCase()
                            .includes(search)
                );

        }


        if (setup) {

            stocks =
                stocks.filter(
                    stock =>
                        stock.setup === setup
                );

        }


        currentFilteredData =
            stocks;


        const total =
            currentWatchlistData.length;


        if ($("watchlistTitle")) {

            $("watchlistTitle").textContent =
                WATCHLIST_META[
                    currentWatchlist
                ].title;

        }


        if ($("watchlistCount")) {

            $("watchlistCount").textContent =
                `${total} stocks`;

        }


        if ($("watchlistTableNote")) {

            $("watchlistTableNote").textContent =
                search || setup
                    ? `Showing ${Math.min(
                        stocks.length,
                        TOP_ROWS
                    )} filtered results.`
                    : `Showing top ${Math.min(
                        stocks.length,
                        TOP_ROWS
                    )} opportunities. Click any stock for complete analysis.`;

        }


        if (!stocks.length) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="17"
                        class="empty-state"
                    >
                        No stocks found in this watchlist.
                    </td>
                </tr>
            `;

            return;

        }


        const display =
            stocks.slice(
                0,
                TOP_ROWS
            );


        tbody.innerHTML =
            display
                .map(
                    (stock,index) =>
                        stockRowHTML(
                            stock,
                            index + 1
                        )
                )
                .join("");


        attachStockRowEvents(
            tbody
        );

    }


    function setupClass(setup) {

        const s =
            String(setup || "")
                .toLowerCase();


        if (
            s.includes("strong") ||
            s.includes("confirmed")
        ) {

            return "setup-positive";

        }


        if (
            s.includes("possible") ||
            s.includes("pre-") ||
            s.includes("watch")
        ) {

            return "setup-watch";

        }


        if (
            s.includes("weak") ||
            s.includes("avoid")
        ) {

            return "setup-negative";

        }


        return "setup-neutral";

    }


    function stockRowHTML(stock,index) {

        const price =
            stock.price;


        return `

            <tr class="stock-row">

                <td>
                    ${index}
                </td>

                <td>
                    <span
                        class="stock-symbol"
                        data-symbol="${escapeHTML(
                            stock.symbol
                        )}"
                    >
                        ${escapeHTML(
                            stock.symbol
                        )}
                    </span>
                </td>

                <td class="stock-company"
                    title="${escapeHTML(
                        stock.company_name
                    )}">
                    ${escapeHTML(
                        stock.company_name
                    )}
                </td>

                <td>
                    ${
                        price === null
                            ? "—"
                            : formatPrice(price)
                    }
                </td>

                <td>
                    ${
                        stock.sma200 === null
                            ? "—"
                            : formatPrice(
                                stock.sma200
                            )
                    }
                </td>

                <td>
                    ${
                        stock.high52 === null
                            ? "—"
                            : formatPrice(
                                stock.high52
                            )
                    }
                </td>

                <td>
                    ${
                        stock.rsi === null
                            ? "—"
                            : stock.rsi.toFixed(1)
                    }
                </td>

                <td>
                    ${
                        stock.volume_ratio === null
                            ? "—"
                            : stock.volume_ratio.toFixed(2) + "x"
                    }
                </td>

                <td>
                    ${
                        stock.technical_score === null
                            ? "—"
                            : stock.technical_score.toFixed(1)
                    }
                </td>

                <td>
                    ${
                        stock.fundamental_score === null
                            ? "—"
                            : stock.fundamental_score.toFixed(1)
                    }
                </td>

                <td>
                    <strong>
                        ${
                            stock.overall_score === null
                                ? "—"
                                : stock.overall_score.toFixed(1)
                        }
                    </strong>
                </td>

                <td>
                    <span
                        class="setup-badge ${
                            setupClass(
                                stock.setup
                            )
                        }"
                    >
                        ${escapeHTML(
                            stock.setup
                        )}
                    </span>
                </td>

                <td class="trade-entry">
                    ${
                        stock.entry === null
                            ? "—"
                            : formatPrice(
                                stock.entry
                            )
                    }
                </td>

                <td class="trade-stop">
                    ${
                        stock.stop === null
                            ? "—"
                            : formatPrice(
                                stock.stop
                            )
                    }
                </td>

                <td class="trade-target">
                    ${
                        stock.target1 === null
                            ? "—"
                            : formatPrice(
                                stock.target1
                            )
                    }
                </td>

                <td class="trade-target">
                    ${
                        stock.target2 === null
                            ? "—"
                            : formatPrice(
                                stock.target2
                            )
                    }
                </td>

                <td>
                    ${
                        stock.rr === null
                            ? "—"
                            : stock.rr.toFixed(2) + "x"
                    }
                </td>

            </tr>

        `;

    }


    function attachStockRowEvents(container) {

        container
            .querySelectorAll(
                ".stock-symbol"
            )
            .forEach(
                element => {

                    element.addEventListener(
                        "click",
                        event => {

                            event.stopPropagation();

                            openStockDetail(
                                element.dataset.symbol
                            );

                        }
                    );

                }
            );

    }


    /* =====================================================
       COMPLETE STOCK SCANNER
    ===================================================== */

    function renderAllStocks() {

        const tbody =
            $("allStocksTable");

        if (!tbody) return;


        const search =
            String(
                $("allStockSearch")?.value || ""
            )
            .trim()
            .toLowerCase();


        const setup =
            $("allSetupFilter")?.value || "";


        let stocks =
            [...allStocks];


        if (search) {

            stocks =
                stocks.filter(
                    stock =>
                        stock.symbol
                            .toLowerCase()
                            .includes(search) ||

                        stock.company_name
                            .toLowerCase()
                            .includes(search)
                );

        }


        if (setup) {

            stocks =
                stocks.filter(
                    stock =>
                        stock.setup === setup
                );

        }


        if ($("allStocksCount")) {

            $("allStocksCount").textContent =
                `${stocks.length} stocks`;

        }


        if (!stocks.length) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="12"
                        class="empty-state"
                    >
                        No stocks found.
                    </td>
                </tr>
            `;

            return;

        }


        tbody.innerHTML =
            stocks
                .slice(0,300)
                .map(
                    (stock,index) => `

                    <tr>

                        <td>
                            ${index + 1}
                        </td>

                        <td>
                            <span
                                class="stock-symbol"
                                data-symbol="${escapeHTML(
                                    stock.symbol
                                )}"
                            >
                                ${escapeHTML(
                                    stock.symbol
                                )}
                            </span>
                        </td>

                        <td class="stock-company">
                            ${escapeHTML(
                                stock.company_name
                            )}
                        </td>

                        <td>
                            ${
                                stock.price === null
                                    ? "—"
                                    : formatPrice(
                                        stock.price
                                    )
                            }
                        </td>

                        <td>
                            ${
                                stock.sma200 === null
                                    ? "—"
                                    : formatPrice(
                                        stock.sma200
                                    )
                            }
                        </td>

                        <td>
                            ${
                                stock.high52 === null
                                    ? "—"
                                    : formatPrice(
                                        stock.high52
                                    )
                            }
                        </td>

                        <td>
                            ${
                                stock.rsi === null
                                    ? "—"
                                    : stock.rsi.toFixed(1)
                            }
                        </td>

                        <td class="${valueClass(
                            stock.trend
                        )}">
                            ${escapeHTML(
                                stock.trend
                            )}
                        </td>

                        <td>
                            ${
                                stock.technical_score === null
                                    ? "—"
                                    : stock.technical_score.toFixed(1)
                            }
                        </td>

                        <td>
                            ${
                                stock.fundamental_score === null
                                    ? "—"
                                    : stock.fundamental_score.toFixed(1)
                            }
                        </td>

                        <td>
                            <strong>
                                ${
                                    stock.overall_score === null
                                        ? "—"
                                        : stock.overall_score.toFixed(1)
                                }
                            </strong>
                        </td>

                        <td>
                            <span
                                class="setup-badge ${
                                    setupClass(
                                        stock.setup
                                    )
                                }"
                            >
                                ${escapeHTML(
                                    stock.setup
                                )}
                            </span>
                        </td>

                    </tr>

                `
                )
                .join("");


        attachStockRowEvents(
            tbody
        );

    }


    function initializeAllStockControls() {

        const search =
            $("allStockSearch");


        if (search) {

            search.addEventListener(
                "input",
                renderAllStocks
            );

        }


        const filter =
            $("allSetupFilter");


        if (filter) {

            const setups =
                [...new Set(
                    allStocks
                        .map(
                            stock =>
                                stock.setup
                        )
                        .filter(
                            value =>
                                value &&
                                value !== "—"
                        )
                )]
                .sort();


            setups.forEach(
                setup => {

                    const option =
                        document.createElement(
                            "option"
                        );

                    option.value =
                        setup;

                    option.textContent =
                        setup;

                    filter.appendChild(
                        option
                    );

                }
            );


            filter.addEventListener(
                "change",
                renderAllStocks
            );

        }

    }


    /* =====================================================
       STOCK DETAIL
    ===================================================== */

    function findStock(symbol) {

        const target =
            String(symbol || "")
                .replace(".NS","")
                .toUpperCase();


        let stock =
            allStocks.find(
                item =>
                    item.symbol.toUpperCase() ===
                    target
            );


        if (stock) return stock;


        for (const list of Object.values(
            watchlists
        )) {

            stock =
                list.find(
                    item =>
                        item.symbol.toUpperCase() ===
                        target
                );


            if (stock) return stock;

        }


        return null;

    }


    function openStockDetail(symbol) {

        const stock =
            findStock(symbol);


        const modal =
            $("stockModal");


        const detail =
            $("stockDetail");


        if (!modal || !detail) return;


        if (!stock) {

            detail.innerHTML = `
                <div class="error-state">
                    Stock analysis unavailable.
                </div>
            `;

        } else {

            detail.innerHTML =
                stockDetailHTML(
                    stock
                );

        }


        modal.classList.add("open");

        modal.classList.add("active");

        modal.setAttribute(
            "aria-hidden",
            "false"
        );


        document.body.style.overflow =
            "hidden";

    }


    function closeStockModal() {

        const modal =
            $("stockModal");


        if (!modal) return;


        modal.classList.remove(
            "open",
            "active"
        );


        modal.setAttribute(
            "aria-hidden",
            "true"
        );


        document.body.style.overflow =
            "";

    }


    function stockDetailHTML(stock) {

        const price =
            stock.price;


        const priceVs200 =
            price !== null &&
            stock.sma200 !== null
                ?
                    (
                        (
                            price /
                            stock.sma200
                        ) - 1
                    ) * 100
                :
                    null;


        const distanceHigh =
            price !== null &&
            stock.high52 !== null
                ?
                    (
                        (
                            price /
                            stock.high52
                        ) - 1
                    ) * 100
                :
                    null;


        return `

            <div class="stock-detail-header">

                <div>

                    <div class="detail-symbol">
                        ${escapeHTML(
                            stock.symbol
                        )}
                    </div>

                    <div class="detail-company">
                        ${escapeHTML(
                            stock.company_name
                        )}
                    </div>

                    <div style="margin-top:10px">

                        <span class="setup-badge ${
                            setupClass(
                                stock.setup
                            )
                        }">
                            ${escapeHTML(
                                stock.setup
                            )}
                        </span>

                    </div>

                </div>


                <div class="detail-rating">

                    Overall Score:
                    <strong>
                        ${
                            stock.overall_score === null
                                ? "—"
                                : stock.overall_score.toFixed(1)
                        }
                    </strong>

                </div>

            </div>


            <div class="detail-grid">

                ${detailItem(
                    "LTP / Last Close",
                    formatPrice(price)
                )}

                ${detailItem(
                    "Daily Change",
                    formatPercent(
                        stock.daily_return_pct
                    )
                )}

                ${detailItem(
                    "200 DMA",
                    formatPrice(
                        stock.sma200
                    )
                )}

                ${detailItem(
                    "Distance vs 200 DMA",
                    formatPercent(
                        priceVs200
                    )
                )}

                ${detailItem(
                    "52W High",
                    formatPrice(
                        stock.high52
                    )
                )}

                ${detailItem(
                    "Distance from 52W High",
                    formatPercent(
                        distanceHigh
                    )
                )}

                ${detailItem(
                    "RSI",
                    stock.rsi === null
                        ? "—"
                        : stock.rsi.toFixed(1)
                )}

                ${detailItem(
                    "Volume Ratio",
                    stock.volume_ratio === null
                        ? "—"
                        : stock.volume_ratio.toFixed(2) + "x"
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
                    "Technical Score",
                    stock.technical_score === null
                        ? "—"
                        : stock.technical_score.toFixed(1)
                )}

                ${detailItem(
                    "Fundamental Score",
                    stock.fundamental_score === null
                        ? "—"
                        : stock.fundamental_score.toFixed(1)
                )}

            </div>


            ${tradePlanHTML(stock)}


            <div class="detail-section">

                <h3>
                    Why is this stock on the watchlist?
                </h3>

                <p>
                    ${escapeHTML(
                        stock.plan_reason !== "—"
                            ? stock.plan_reason
                            : generateStockReason(
                                stock
                            )
                    )}
                </p>

            </div>


            <div class="detail-section">

                <h3>
                    Decision Framework
                </h3>

                <p>
                    ${
                        generateDecisionText(
                            stock
                        )
                    }
                </p>

            </div>


            <div class="detail-section">

                <h3>
                    Invalidation / Risk
                </h3>

                <p>
                    ${escapeHTML(
                        stock.invalidation !== "—"
                            ? stock.invalidation
                            : (
                                stock.stop !== null
                                    ?
                                    "Trade thesis weakens below the calculated stop-loss."
                                    :
                                    "No engine-generated trade plan is currently available."
                            )
                    )}
                </p>

            </div>

        `;

    }


    function detailItem(label,value) {

        return `

            <div class="detail-item">

                <span>
                    ${escapeHTML(label)}
                </span>

                <b>
                    ${escapeHTML(
                        text(value)
                    )}
                </b>

            </div>

        `;

    }


    function tradePlanHTML(stock) {

        if (
            stock.entry === null &&
            stock.stop === null &&
            stock.target1 === null
        ) {

            return `

                <div class="trade-plan-panel">

                    <div class="trade-plan-header">

                        <div class="trade-plan-label">
                            Trade Plan
                        </div>

                        <div class="trade-plan-status neutral">
                            Confirmation Required
                        </div>

                    </div>

                    <div class="trade-plan-reason">
                        The ranking engine has not generated
                        a complete actionable trade plan for
                        this stock.
                    </div>

                </div>

            `;

        }


        return `

            <div class="trade-plan-panel">

                <div class="trade-plan-header">

                    <div class="trade-plan-label">
                        Engine-Generated Trade Plan
                    </div>

                    <div class="trade-plan-status ${
                        setupClass(
                            stock.setup
                        )
                    }">
                        ${escapeHTML(
                            stock.plan_status !== "—"
                                ? stock.plan_status
                                : stock.trade_quality
                        )}
                    </div>

                </div>


                <div class="trade-plan-grid">

                    ${detailItem(
                        "Entry",
                        stock.entry === null
                            ? (
                                stock.entry_low !== null &&
                                stock.entry_high !== null
                                    ?
                                    `${formatPrice(stock.entry_low)} – ${formatPrice(stock.entry_high)}`
                                    :
                                    "—"
                            )
                            :
                            formatPrice(
                                stock.entry
                            )
                    )}

                    ${detailItem(
                        "Stop Loss",
                        formatPrice(
                            stock.stop
                        )
                    )}

                    ${detailItem(
                        "Target 1",
                        formatPrice(
                            stock.target1
                        )
                    )}

                    ${detailItem(
                        "Target 2",
                        formatPrice(
                            stock.target2
                        )
                    )}

                    ${detailItem(
                        "Risk / Reward",
                        stock.rr === null
                            ? "—"
                            : stock.rr.toFixed(2) + "x"
                    )}

                </div>


                ${
                    stock.plan_reason !== "—"
                        ?
                        `<div class="trade-plan-reason">
                            <strong>Reason:</strong>
                            ${escapeHTML(
                                stock.plan_reason
                            )}
                        </div>`
                        :
                        ""
                }

            </div>

        `;

    }


    function generateStockReason(stock) {

        const reasons = [];


        if (
            stock.price !== null &&
            stock.sma200 !== null &&
            stock.price > stock.sma200
        ) {

            reasons.push(
                "price is above the 200 DMA"
            );

        }


        if (
            stock.rsi !== null &&
            stock.rsi >= 50 &&
            stock.rsi <= 70
        ) {

            reasons.push(
                "RSI supports positive momentum without being extremely overbought"
            );

        }


        if (
            stock.volume_ratio !== null &&
            stock.volume_ratio >= 1.2
        ) {

            reasons.push(
                "volume is above normal"
            );

        }


        if (
            stock.overall_score !== null &&
            stock.overall_score >= 60
        ) {

            reasons.push(
                "overall ranking score is strong"
            );

        }


        if (!reasons.length) {

            return (
                "The stock meets the ranking engine's " +
                "current watchlist criteria."
            );

        }


        return (
            "The stock is being watched because " +
            reasons.join(", ") +
            "."
        );

    }


    function generateDecisionText(stock) {

        const score =
            stock.overall_score;


        const rr =
            stock.rr;


        if (
            rr !== null &&
            rr >= 2 &&
            score !== null &&
            score >= 65
        ) {

            return (
                "This is a relatively strong setup. " +
                "The preferred approach is to wait for the " +
                "engine-defined entry/confirmation condition " +
                "and maintain the calculated invalidation level."
            );

        }


        if (
            rr !== null &&
            rr >= 1.5
        ) {

            return (
                "The risk/reward is acceptable, but confirmation " +
                "is still important. Do not chase price away from " +
                "the calculated entry zone."
            );

        }


        return (
            "Treat this as a watch candidate rather than an automatic buy. " +
            "Wait for confirmation and reassess the setup if price " +
            "moves through the invalidation level."
        );

    }


    /* =====================================================
       MODAL EVENTS
    ===================================================== */

    function initializeModal() {

        const close =
            $("stockModalClose");


        if (close) {

            close.addEventListener(
                "click",
                closeStockModal
            );

        }


        const overlay =
            document.querySelector(
                ".stock-modal-overlay"
            );


        if (overlay) {

            overlay.addEventListener(
                "click",
                closeStockModal
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


    /* =====================================================
       EXPORT
    ===================================================== */

    function exportCurrentWatchlist() {

        const stocks =
            currentWatchlistData;


        if (!stocks.length) {

            alert(
                "No stocks available for export."
            );

            return;

        }


        const rows =
            stocks.map(
                (s,index) => ({

                    Rank: index + 1,

                    Symbol: s.symbol,

                    Company: s.company_name,

                    "LTP / Last Close":
                        s.price,

                    "Daily Change %":
                        s.daily_return_pct,

                    "200 DMA":
                        s.sma200,

                    "52W High":
                        s.high52,

                    RSI:
                        s.rsi,

                    "Volume Ratio":
                        s.volume_ratio,

                    "Technical Score":
                        s.technical_score,

                    "Fundamental Score":
                        s.fundamental_score,

                    "Overall Score":
                        s.overall_score,

                    Setup:
                        s.setup,

                    Entry:
                        s.entry,

                    "Stop Loss":
                        s.stop,

                    "Target 1":
                        s.target1,

                    "Target 2":
                        s.target2,

                    "Risk Reward":
                        s.rr,

                    "Trade Plan Status":
                        s.plan_status,

                    Reason:
                        s.plan_reason,

                    Invalidation:
                        s.invalidation

                })
            );


        downloadExcelOrCSV(
            rows,
            `NSE_${currentWatchlist}_watchlist`
        );

    }


    function downloadExcelOrCSV(
        rows,
        filename
    ) {

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
                "Watchlist"
            );


            XLSX.writeFile(
                workbook,
                filename + ".xlsx"
            );


            return;

        }


        const headers =
            Object.keys(
                rows[0]
            );


        const csv = [

            headers.join(","),

            ...rows.map(
                row =>
                    headers
                        .map(
                            h =>
                                csvValue(
                                    row[h]
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


        const a =
            document.createElement(
                "a"
            );


        a.href = url;

        a.download =
            filename + ".csv";


        document.body.appendChild(a);

        a.click();

        a.remove();

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


        const str =
            String(value)
                .replace(
                    /"/g,
                    '""'
                );


        return `"${str}"`;

    }


    /* =====================================================
       HEADER STATUS
    ===================================================== */

    function renderLastUpdated() {

        const element =
            $("lastUpdated");


        if (!element) return;


        const generated =
            first(
                dashboardData,
                [
                    "generated_at",
                    "Generated_At",
                    "updated_at",
                    "last_updated"
                ]
            );


        if (!generated) {

            element.textContent =
                "Data loaded";

            return;

        }


        const date =
            new Date(
                generated
            );


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {

            element.textContent =
                String(generated);

            return;

        }


        element.textContent =
            "Updated " +
            date.toLocaleString(
                "en-IN",
                {
                    dateStyle:"medium",
                    timeStyle:"short"
                }
            );

    }


    /* =====================================================
       PORTFOLIO INITIALIZATION
    ===================================================== */

    function initializePortfolio() {

        /*
         portfolio.js is loaded after this file.
         It exposes initializePortfolioBuilder().
        */

        if (
            typeof window.initializePortfolioBuilder ===
            "function"
        ) {

            try {

                window.initializePortfolioBuilder(
                    dashboardData
                );

            } catch (error) {

                console.error(
                    "Portfolio initialization error:",
                    error
                );

            }

        }

    }


    /* =====================================================
       MAIN LOAD
    ===================================================== */

    async function loadDashboard() {

        try {

            if ($("marketStatusText")) {

                $("marketStatusText").textContent =
                    "LOADING MARKET DATA";

            }


            const response =
                await fetch(
                    DATA_URL,
                    {
                        cache:"no-store"
                    }
                );


            if (!response.ok) {

                throw new Error(
                    `Dashboard data HTTP ${response.status}`
                );

            }


            const data =
                await response.json();


            normalizeDashboardData(
                data
            );


            renderLastUpdated();

            renderMarketRegime();

            renderMarketIndices();

            renderEnvironment();

            renderMarketAnalysis();

            renderBreadth();

            renderSetupSummary();

            renderSectors();


            initializeWatchlistTabs();

            initializeWatchlistControls();

            initializeAllStockControls();

            initializeModal();


            switchWatchlist(
                "next_day"
            );


            renderAllStocks();


            initializePortfolio();


            if ($("marketStatusText")) {

                $("marketStatusText").textContent =
                    "DATA LOADED";

            }


            const dot =
                document.querySelector(
                    ".live-dot"
                );


            if (dot) {

                dot.style.background =
                    "#18c987";

            }


            console.info(
                "NSE Dashboard loaded:",
                {
                    stocks:
                        allStocks.length,

                    watchlists:
                        Object.fromEntries(
                            Object.entries(
                                watchlists
                            )
                            .map(
                                ([key,list]) =>
                                    [
                                        key,
                                        list.length
                                    ]
                            )
                        )
                }
            );

        } catch (error) {

            console.error(
                "Dashboard loading failed:",
                error
            );


            showDashboardError(
                error
            );

        }

    }


    /* =====================================================
       ERROR
    ===================================================== */

    function showDashboardError(error) {

        const message =
            error?.message ||
            "Unknown error";


        if ($("marketRegime")) {

            $("marketRegime").innerHTML = `

                <div class="error-state">

                    <strong>
                        Dashboard data could not be loaded.
                    </strong>

                    ${escapeHTML(
                        message
                    )}

                </div>

            `;

        }


        const bodies =
            document.querySelectorAll(
                "#stockTable tbody, #sectorTable tbody, #allStocksTable"
            );


        bodies.forEach(
            body => {

                body.innerHTML = `

                    <tr>

                        <td
                            colspan="20"
                            class="error-state"
                        >
                            Dashboard data unavailable.
                        </td>

                    </tr>

                `;

            }
        );


        if ($("marketStatusText")) {

            $("marketStatusText").textContent =
                "DATA ERROR";

        }

    }


    /* =====================================================
       GLOBAL FUNCTIONS
    ===================================================== */

    window.openStockDetail =
        openStockDetail;

    window.closeStockModal =
        closeStockModal;

    window.exportCurrentWatchlist =
        exportCurrentWatchlist;

    window.switchWatchlist =
        switchWatchlist;


    /* =====================================================
       START
    ===================================================== */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            loadDashboard
        );

    } else {

        loadDashboard();

    }

})();

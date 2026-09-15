/* ============================================================
   NSE SMART MARKET DASHBOARD
   DASHBOARD ENGINE — V1
============================================================ */


/* ============================================================
   CONFIGURATION
============================================================ */

const DATA_PATH = "output/";


let currentWatchlist = "next_day";


let stockData = [];

let marketData = {};

let breadthData = {};

let sectorData = [];


/* ============================================================
   HELPERS
============================================================ */

function formatNumber(value, decimals = 2) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        Number.isNaN(Number(value))
    ) {
        return "--";
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
        value === ""
    ) {
        return "--";
    }

    return "₹" + formatNumber(value, 2);
}


function formatPercent(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "--";
    }

    const number = Number(value);

    return (
        number >= 0 ? "+" : ""
    )
    + number.toFixed(2)
    + "%";
}


function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ============================================================
   BADGE
============================================================ */

function badgeClass(value) {

    const text = String(
        value || ""
    ).toLowerCase();


    if (
        text.includes("strong")
        || text.includes("leading")
        || text.includes("positive")
        || text.includes("confirmed")
        || text.includes("bullish")
        || text.includes("favorable")
    ) {

        return "badge-green";
    }


    if (
        text.includes("bearish")
        || text.includes("negative")
        || text.includes("downtrend")
        || text.includes("lagging")
        || text.includes("avoid")
    ) {

        return "badge-red";
    }


    if (
        text.includes("cautious")
        || text.includes("required")
        || text.includes("selective")
        || text.includes("weak")
    ) {

        return "badge-orange";
    }


    if (
        text.includes("neutral")
        || text.includes("sideways")
    ) {

        return "badge-yellow";
    }


    return "badge-blue";
}


function createBadge(value) {

    return `
        <span class="badge ${badgeClass(value)}">
            ${escapeHTML(value || "--")}
        </span>
    `;
}


/* ============================================================
   LOAD CSV
============================================================ */

async function loadCSV(fileName) {

    try {

        const response = await fetch(
            DATA_PATH + fileName
        );

        if (!response.ok) {

            return [];
        }

        const text = await response.text();

        return parseCSV(text);

    } catch (error) {

        console.error(
            "Unable to load",
            fileName,
            error
        );

        return [];
    }
}


/* ============================================================
   CSV PARSER
============================================================ */

function parseCSV(text) {

    const lines = text
        .trim()
        .split(/\r?\n/);

    if (lines.length < 2) {

        return [];
    }


    const headers = parseCSVLine(
        lines[0]
    );


    return lines
        .slice(1)
        .filter(line => line.trim() !== "")
        .map(line => {

            const values =
                parseCSVLine(line);

            const row = {};

            headers.forEach(
                (header, index) => {

                    row[header] =
                        values[index] ?? "";
                }
            );

            return row;
        });
}


function parseCSVLine(line) {

    const result = [];

    let current = "";

    let insideQuotes = false;


    for (
        let i = 0;
        i < line.length;
        i++
    ) {

        const char = line[i];

        const next = line[i + 1];


        if (
            char === '"'
            && insideQuotes
            && next === '"'
        ) {

            current += '"';

            i++;

            continue;
        }


        if (char === '"') {

            insideQuotes =
                !insideQuotes;

            continue;
        }


        if (
            char === ","
            && !insideQuotes
        ) {

            result.push(current);

            current = "";

            continue;
        }


        current += char;
    }


    result.push(current);

    return result;
}


/* ============================================================
   LOAD MARKET
============================================================ */

async function loadMarket() {

    const rows =
        await loadCSV(
            "market_regime_test.csv"
        );


    if (!rows.length) {

        return;
    }


    marketData = rows[0];


    document.getElementById(
        "marketRegime"
    ).innerHTML =
        createBadge(
            marketData.market_regime
        );


    document.getElementById(
        "marketScore"
    ).textContent =
        "Score: "
        + formatNumber(
            marketData.market_score
        );


    document.getElementById(
        "niftyPrice"
    ).textContent =
        formatPrice(
            marketData.nifty_price
        );


    document.getElementById(
        "niftyTrend"
    ).innerHTML =
        createBadge(
            marketData.nifty_trend
        );


    document.getElementById(
        "bankPrice"
    ).textContent =
        formatPrice(
            marketData.bank_nifty_price
        );


    document.getElementById(
        "bankTrend"
    ).innerHTML =
        createBadge(
            marketData.bank_nifty_trend
        );


    document.getElementById(
        "vixValue"
    ).textContent =
        formatNumber(
            marketData.vix
        );


    document.getElementById(
        "vixStatus"
    ).innerHTML =
        createBadge(
            marketData.vix_interpretation
        );


    document.getElementById(
        "breadthScore"
    ).textContent =
        formatNumber(
            marketData.breadth_score
        );
}


/* ============================================================
   LOAD BREADTH
============================================================ */

async function loadBreadth() {

    const rows =
        await loadCSV(
            "market_breadth.csv"
        );


    if (!rows.length) {

        return;
    }


    breadthData = rows[0];


    document.getElementById(
        "above20"
    ).textContent =
        formatNumber(
            breadthData.pct_above_20dma
        )
        + "%";


    document.getElementById(
        "above50"
    ).textContent =
        formatNumber(
            breadthData.pct_above_50dma
        )
        + "%";


    document.getElementById(
        "above200"
    ).textContent =
        formatNumber(
            breadthData.pct_above_200dma
        )
        + "%";


    document.getElementById(
        "highs52"
    ).textContent =
        formatNumber(
            breadthData["52w_highs"],
        0);


    document.getElementById(
        "lows52"
    ).textContent =
        formatNumber(
            breadthData["52w_lows"],
        0);


    document.getElementById(
        "highLowRatio"
    ).textContent =
        formatNumber(
            breadthData.high_low_ratio
        );


    document.getElementById(
        "breadthStatus"
    ).innerHTML =
        createBadge(
            breadthData.breadth_regime
        );
}


/* ============================================================
   LOAD SECTORS
============================================================ */

async function loadSectors() {

    sectorData =
        await loadCSV(
            "sector_analysis.csv"
        );


    renderSectorTable();
}


function renderSectorTable() {

    const table =
        document.getElementById(
            "sectorTable"
        );


    if (!sectorData.length) {

        table.innerHTML = `
            <tr>
                <td
                    colspan="10"
                    class="loading-cell"
                >
                    Sector data unavailable
                </td>
            </tr>
        `;

        return;
    }


    table.innerHTML =
        sectorData
            .map(row => {

                return `
                    <tr>

                        <td>
                            ${escapeHTML(
                                row.sector_rank
                            )}
                        </td>

                        <td>
                            <strong>
                                ${escapeHTML(
                                    row.sector
                                )}
                            </strong>
                        </td>

                        <td>
                            ${createBadge(
                                row.type
                            )}
                        </td>

                        <td>
                            <strong>
                                ${formatNumber(
                                    row.sector_score
                                )}
                            </strong>
                        </td>

                        <td>
                            ${createBadge(
                                row.classification
                            )}
                        </td>

                        <td>
                            ${createBadge(
                                row.trend
                            )}
                        </td>

                        <td>
                            ${createBadge(
                                row.momentum
                            )}
                        </td>

                        <td>
                            ${formatPercent(
                                row.return_20d_pct
                            )}
                        </td>

                        <td>
                            ${formatPercent(
                                row.return_60d_pct
                            )}
                        </td>

                        <td>
                            ${formatNumber(
                                row.rsi14
                            )}
                        </td>

                    </tr>
                `;
            })
            .join("");
}


/* ============================================================
   LOAD STOCK DATA
============================================================ */

async function loadStocks() {

    stockData =
        await loadCSV(
            "technical_ranked_test.csv"
        );


    renderStockTable();
}


/* ============================================================
   STOCK TABLE
============================================================ */

function renderStockTable() {

    const table =
        document.getElementById(
            "stockTable"
        );


    if (!stockData.length) {

        table.innerHTML = `
            <tr>
                <td
                    colspan="10"
                    class="loading-cell"
                >
                    Stock data unavailable
                </td>
            </tr>
        `;

        return;
    }


    let filtered =
        getWatchlistData();


    if (!filtered.length) {

        filtered =
            stockData;
    }


    table.innerHTML =
        filtered
            .slice(0, 15)
            .map(
                (row, index) => {

                    return `
                        <tr>

                            <td>
                                ${index + 1}
                            </td>

                            <td>

                                <span
                                    class="stock-link"
                                    onclick="openStock(
                                        '${escapeHTML(
                                            row.symbol
                                        )}'
                                    )"
                                >
                                    ${escapeHTML(
                                        cleanSymbol(
                                            row.symbol
                                        )
                                    )}
                                </span>

                            </td>

                            <td>
                                ${escapeHTML(
                                    row.sector || "--"
                                )}
                            </td>

                            <td>
                                ${formatPrice(
                                    row.price
                                )}
                            </td>

                            <td>
                                ${createBadge(
                                    row.setup
                                )}
                            </td>

                            <td>
                                ${createBadge(
                                    row.trend
                                )}
                            </td>

                            <td>
                                ${createBadge(
                                    row.momentum
                                )}
                            </td>

                            <td>
                                ${formatNumber(
                                    row.rsi14
                                )}
                            </td>

                            <td>
                                ${formatNumber(
                                    row.volume_ratio
                                )}x
                            </td>

                            <td>
                                ${createRating(
                                    row
                                )}
                            </td>

                        </tr>
                    `;
                }
            )
            .join("");
}


/* ============================================================
   WATCHLIST FILTER
============================================================ */

function getWatchlistData() {

    if (!stockData.length) {

        return [];
    }


    switch (currentWatchlist) {

        case "52w_high":

            return stockData.filter(
                row =>
                    Number(
                        row.distance_from_52w_high_pct
                    ) >= -5
            );


        case "dma_recovery":

            return stockData.filter(
                row => {

                    const distance =
                        Number(
                            row.distance_from_200dma_pct
                        );

                    return (
                        distance >= -5
                        && distance <= 5
                    );
                }
            );


        case "next_day":

            return stockData.filter(
                row =>
                    row.setup
                    &&
                    !String(
                        row.setup
                    ).toLowerCase()
                    .includes("avoid")
            );


        case "swing":

            return stockData.filter(
                row =>
                    row.trend
                    &&
                    (
                        String(
                            row.trend
                        ).includes(
                            "Uptrend"
                        )
                        ||
                        String(
                            row.trend
                        ).includes(
                            "Bullish"
                        )
                    )
            );


        case "long_term":

            return stockData.filter(
                row =>
                    Number(
                        row.distance_from_200dma_pct
                    ) > 0
            );


        case "intraday":

            return stockData.filter(
                row =>
                    Number(
                        row.volume_ratio
                    ) >= 1.2
            );


        case "options":

            return stockData.filter(
                row =>
                    Number(
                        row.volume_ratio
                    ) >= 1.2
            );


        default:

            return stockData;
    }
}


/* ============================================================
   RATING
============================================================ */

function createRating(row) {

    let rating =
        Number(
            row.total_score
            || row.technical_score
            || row.score
            || 0
        );


    if (
        !rating
        && row.trend
    ) {

        rating =
            calculateFallbackRating(
                row
            );
    }


    let ratingClass =
        "badge-blue";


    if (rating >= 75) {

        ratingClass =
            "badge-green";

    } else if (rating >= 60) {

        ratingClass =
            "badge-blue";

    } else if (rating >= 45) {

        ratingClass =
            "badge-yellow";

    } else if (rating >= 30) {

        ratingClass =
            "badge-orange";

    } else {

        ratingClass =
            "badge-red";
    }


    return `
        <span
            class="badge ${ratingClass}"
        >
            ${Math.round(rating)}
        </span>
    `;
}


function calculateFallbackRating(row) {

    let score = 0;


    const trend =
        String(
            row.trend || ""
        );


    const momentum =
        String(
            row.momentum || ""
        );


    if (
        trend.includes(
            "Strong Uptrend"
        )
    ) {

        score += 40;

    } else if (
        trend.includes(
            "Uptrend"
        )
    ) {

        score += 32;

    } else if (
        trend.includes(
            "Sideways"
        )
    ) {

        score += 20;

    } else if (
        trend.includes(
            "Downtrend"
        )
    ) {

        score += 8;
    }


    if (
        momentum.includes(
            "Strong Positive"
        )
    ) {

        score += 30;

    } else if (
        momentum.includes(
            "Positive"
        )
    ) {

        score += 23;

    } else if (
        momentum.includes(
            "Neutral"
        )
    ) {

        score += 15;

    } else {

        score += 5;
    }


    const rsi =
        Number(
            row.rsi14
        );


    if (
        rsi >= 50
        && rsi <= 70
    ) {

        score += 20;

    } else if (
        rsi >= 45
    ) {

        score += 12;

    } else {

        score += 5;
    }


    const volume =
        Number(
            row.volume_ratio
        );


    if (
        volume >= 1.5
    ) {

        score += 10;

    } else if (
        volume >= 1
    ) {

        score += 7;

    } else {

        score += 3;
    }


    return Math.min(
        score,
        100
    );
}


/* ============================================================
   CLEAN SYMBOL
============================================================ */

function cleanSymbol(symbol) {

    return String(
        symbol || ""
    )
    .replace(
        ".NS",
        ""
    );
}


/* ============================================================
   OPEN STOCK
============================================================ */

function openStock(symbol) {

    const row =
        stockData.find(
            item =>
                item.symbol === symbol
        );


    if (!row) {

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


    const rating =
        calculateFallbackRating(
            row
        );


    detail.innerHTML = `

        <div class="stock-detail-header">

            <div class="stock-detail-title">

                ${escapeHTML(
                    cleanSymbol(
                        row.symbol
                    )
                )}

            </div>

            <div class="stock-detail-subtitle">

                ${escapeHTML(
                    row.sector || "NSE Equity"
                )}

            </div>

        </div>


        <div class="rating-card">

            <div>

                <div class="card-label">
                    OVERALL RATING
                </div>

                <div class="rating-number">
                    ${Math.round(
                        rating
                    )}
                    / 100
                </div>

            </div>

            <div>

                <div class="card-label">
                    SETUP
                </div>

                <div>
                    ${createBadge(
                        row.setup
                        || "Watch"
                    )}
                </div>

            </div>

            <div>

                <div class="card-label">
                    TREND
                </div>

                <div>
                    ${createBadge(
                        row.trend
                    )}
                </div>

            </div>

            <div>

                <div class="card-label">
                    MOMENTUM
                </div>

                <div>
                    ${createBadge(
                        row.momentum
                    )}
                </div>

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Technical Analysis
            </h3>


            <div class="detail-grid">

                ${detailItem(
                    "Price",
                    formatPrice(
                        row.price
                    )
                )}

                ${detailItem(
                    "SMA 20",
                    formatPrice(
                        row.sma20
                    )
                )}

                ${detailItem(
                    "SMA 50",
                    formatPrice(
                        row.sma50
                    )
                )}

                ${detailItem(
                    "SMA 100",
                    formatPrice(
                        row.sma100
                    )
                )}

                ${detailItem(
                    "SMA 200",
                    formatPrice(
                        row.sma200
                    )
                )}

                ${detailItem(
                    "EMA 9",
                    formatPrice(
                        row.ema9
                    )
                )}

                ${detailItem(
                    "EMA 20",
                    formatPrice(
                        row.ema20
                    )
                )}

                ${detailItem(
                    "EMA 50",
                    formatPrice(
                        row.ema50
                    )
                )}

                ${detailItem(
                    "RSI 14",
                    formatNumber(
                        row.rsi14
                    )
                )}

                ${detailItem(
                    "ATR 14",
                    formatNumber(
                        row.atr14
                    )
                )}

                ${detailItem(
                    "ATR %",
                    formatPercent(
                        row.atr_percent
                    )
                )}

                ${detailItem(
                    "Volume Ratio",
                    formatNumber(
                        row.volume_ratio
                    ) + "x"
                )}

                ${detailItem(
                    "52W High",
                    formatPrice(
                        row["52w_high"]
                    )
                )}

                ${detailItem(
                    "52W Low",
                    formatPrice(
                        row["52w_low"]
                    )
                )}

                ${detailItem(
                    "Distance from 52W High",
                    formatPercent(
                        row.distance_from_52w_high_pct
                    )
                )}

                ${detailItem(
                    "Distance from 200 DMA",
                    formatPercent(
                        row.distance_from_200dma_pct
                    )
                )}

                ${detailItem(
                    "Support",
                    formatPrice(
                        row.support
                    )
                )}

                ${detailItem(
                    "Resistance",
                    formatPrice(
                        row.resistance
                    )
                )}

                ${detailItem(
                    "Breakout",
                    row.breakout_status
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Technical Assessment
            </h3>

            <div>

                ${createBadge(
                    row.trend
                )}

                ${createBadge(
                    row.momentum
                )}

                ${createBadge(
                    row.breakout_status
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Risk &amp; Setup
            </h3>

            <div class="detail-grid">

                ${detailItem(
                    "Setup",
                    row.setup || "--"
                )}

                ${detailItem(
                    "Support",
                    formatPrice(
                        row.support
                    )
                )}

                ${detailItem(
                    "Resistance",
                    formatPrice(
                        row.resistance
                    )
                )}

                ${detailItem(
                    "Risk / Reward",
                    formatNumber(
                        row.risk_reward
                    )
                )}

            </div>

        </div>


        <div class="detail-section">

            <h3>
                Assessment
            </h3>

            <p>

                The stock is currently classified as

                <strong>
                    ${escapeHTML(
                        row.setup
                        || "Watch"
                    )}
                </strong>

                based on the available technical
                indicators and ranking model.

            </p>

        </div>

    `;


    modal.classList.remove(
        "hidden"
    );
}


/* ============================================================
   DETAIL ITEM
============================================================ */

function detailItem(
    label,
    value
) {

    return `

        <div class="detail-item">

            <div class="detail-item-label">
                ${escapeHTML(
                    label
                )}
            </div>

            <div class="detail-item-value">
                ${escapeHTML(
                    value
                )}
            </div>

        </div>

    `;
}


/* ============================================================
   MODAL
============================================================ */

function closeModal() {

    document
        .getElementById(
            "stockModal"
        )
        .classList.add(
            "hidden"
        );
}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        document
            .getElementById(
                "closeModal"
            )
            .addEventListener(
                "click",
                closeModal
            );


        document
            .querySelector(
                ".modal-overlay"
            )
            .addEventListener(
                "click",
                closeModal
            );


        document
            .querySelectorAll(
                ".tab-button"
            )
            .forEach(
                button => {

                    button.addEventListener(
                        "click",
                        () => {

                            document
                                .querySelectorAll(
                                    ".tab-button"
                                )
                                .forEach(
                                    item =>
                                        item.classList.remove(
                                            "active"
                                        )
                                );


                            button.classList.add(
                                "active"
                            );


                            currentWatchlist =
                                button.dataset.watchlist;


                            renderStockTable();
                        }
                    );
                }
            );


        loadDashboard();

    }
);


/* ============================================================
   LOAD COMPLETE DASHBOARD
============================================================ */

async function loadDashboard() {

    document.getElementById(
        "lastUpdated"
    ).textContent =
        "Updated: "
        + new Date()
            .toLocaleString(
                "en-IN"
            );


    await Promise.all([
        loadMarket(),
        loadBreadth(),
        loadSectors(),
        loadStocks()
    ]);
}

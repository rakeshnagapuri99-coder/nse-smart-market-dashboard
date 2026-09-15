from pathlib import Path
import time
import numpy as np
import pandas as pd
import yfinance as yf

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def _flatten_yf(df, ticker):
    if df is None or df.empty:
        return pd.DataFrame()
    x = df.copy()
    if isinstance(x.columns, pd.MultiIndex):
        # Handle both (Price, Ticker) and (Ticker, Price).
        levels = [list(map(str, x.columns.get_level_values(i))) for i in range(x.columns.nlevels)]
        selected = None
        for level in range(x.columns.nlevels):
            if ticker in levels[level]:
                selected = x.xs(ticker, axis=1, level=level)
                break
        if selected is not None:
            x = selected
        else:
            # Single ticker sometimes has one ticker level that differs in formatting.
            x.columns = [str(c[-1]) if isinstance(c, tuple) else str(c) for c in x.columns]
    x.columns = [str(c).strip().lower().replace("adj close","adj_close") for c in x.columns]
    x = x.reset_index()
    date_col = "date" if "date" in x.columns else x.columns[0]
    x["date"] = pd.to_datetime(x[date_col], errors="coerce", utc=True).dt.tz_localize(None)
    for c in ["open","high","low","close","volume"]:
        if c in x.columns:
            x[c] = pd.to_numeric(x[c], errors="coerce")
    required = {"date","open","high","low","close","volume"}
    if not required.issubset(x.columns):
        return pd.DataFrame()
    return x.dropna(subset=["date","close"]).sort_values("date").drop_duplicates("date")

def _rsi(s, n=14):
    d = s.diff()
    gain = d.clip(lower=0)
    loss = -d.clip(upper=0)
    ag = gain.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    al = loss.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    rs = ag / al.replace(0, np.nan)
    return 100 - 100/(1+rs)

def _atr(x, n=14):
    pc = x["close"].shift(1)
    tr = pd.concat([
        x["high"]-x["low"],
        (x["high"]-pc).abs(),
        (x["low"]-pc).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False, min_periods=n).mean()

def _analyse(ticker, raw):
    x = _flatten_yf(raw, ticker)
    if len(x) < 220:
        return None

    x["sma20"] = x.close.rolling(20).mean()
    x["sma50"] = x.close.rolling(50).mean()
    x["sma100"] = x.close.rolling(100).mean()
    x["sma200"] = x.close.rolling(200).mean()
    x["ema9"] = x.close.ewm(span=9, adjust=False).mean()
    x["ema20"] = x.close.ewm(span=20, adjust=False).mean()
    x["ema50"] = x.close.ewm(span=50, adjust=False).mean()
    x["rsi14"] = _rsi(x.close)
    x["atr14"] = _atr(x)
    x["vol20"] = x.volume.rolling(20).mean()
    x["volume_ratio"] = x.volume / x.vol20.replace(0, np.nan)
    x["high52w"] = x.high.rolling(252, min_periods=100).max()
    x["low52w"] = x.low.rolling(252, min_periods=100).min()
    x["resistance20"] = x.high.shift(1).rolling(20).max()
    x["support20"] = x.low.shift(1).rolling(20).min()
    x["pivot"] = (x.high.shift(1)+x.low.shift(1)+x.close.shift(1))/3
    x["return5"] = x.close.pct_change(5)*100
    x["return20"] = x.close.pct_change(20)*100
    x["return60"] = x.close.pct_change(60)*100
    x["distance200"] = (x.close/x.sma200-1)*100
    x["distance52high"] = (x.close/x.high52w-1)*100

    cur = x.iloc[-1]
    prev = x.iloc[-2]
    if pd.isna(cur.sma200):
        return None

    cross_down = (x.close.shift(1) > x.sma200.shift(1)) & (x.close <= x.sma200)
    recent_cross = cross_down.tail(90).any()
    above200 = bool(cur.close >= cur.sma200)
    near200 = abs(float(cur.distance200)) <= 3

    breakout = bool(
        not pd.isna(cur.resistance20) and cur.close > cur.resistance20
        and cur.volume_ratio >= 1.2
    )
    near_breakout = bool(
        not pd.isna(cur.resistance20) and cur.close >= cur.resistance20*0.98
    )
    trend_score = (
        (cur.close > cur.sma20) + (cur.sma20 > cur.sma50) +
        (cur.sma50 > cur.sma200) + (cur.ema20 > cur.ema50)
    ) * 25
    momentum_score = np.clip(
        50 + cur.return20*2 + cur.return60*0.8, 0, 100
    )
    rsi_score = 100 - abs(cur.rsi14-58)*2 if not pd.isna(cur.rsi14) else 50
    rsi_score = float(np.clip(rsi_score, 0, 100))
    volume_score = float(np.clip(50 + (cur.volume_ratio-1)*35, 0, 100))
    position_score = float(np.clip(50 + cur.distance200*8, 0, 100))
    breakout_score = 100 if breakout else (75 if near_breakout else 35)
    technical_score = (
        trend_score*.20 + momentum_score*.15 + rsi_score*.15 +
        volume_score*.15 + position_score*.15 + breakout_score*.20
    )

    if breakout:
        setup = "Strong Breakout Watch"
    elif near_breakout:
        setup = "Pre-Breakout Watch"
    elif recent_cross and near200:
        setup = "200 DMA Recovery Watch"
    elif cur.distance52high >= -5:
        setup = "52W High Watch"
    elif momentum_score >= 70:
        setup = "Momentum Watch"
    elif technical_score < 40:
        setup = "Weak / Avoid"
    else:
        setup = "Neutral Watch"

    return {
        "Symbol": ticker.replace(".NS",""),
        "Yahoo_Symbol": ticker,
        "Date": cur.date.strftime("%Y-%m-%d"),
        "Open": float(cur.open), "High": float(cur.high), "Low": float(cur.low),
        "Close": float(cur.close), "Volume": float(cur.volume),
        "SMA20": float(cur.sma20), "SMA50": float(cur.sma50),
        "SMA100": float(cur.sma100), "SMA200": float(cur.sma200),
        "EMA9": float(cur.ema9), "EMA20": float(cur.ema20), "EMA50": float(cur.ema50),
        "RSI14": float(cur.rsi14), "ATR14": float(cur.atr14),
        "ATR_Pct": float(cur.atr14/cur.close*100),
        "Volume_Ratio": float(cur.volume_ratio),
        "52W_High": float(cur.high52w), "52W_Low": float(cur.low52w),
        "Distance_200DMA_Pct": float(cur.distance200),
        "Distance_52W_High_Pct": float(cur.distance52high),
        "Support": float(cur.support20), "Resistance": float(cur.resistance20),
        "Pivot": float(cur.pivot),
        "Return_5D_Pct": float(cur.return5), "Return_20D_Pct": float(cur.return20),
        "Return_60D_Pct": float(cur.return60),
        "Above_200DMA": above200,
        "Near_200DMA": near200,
        "Recent_200DMA_Cross_Down": bool(recent_cross),
        "Breakout": breakout, "Near_Breakout": near_breakout,
        "Technical_Score": round(float(technical_score),2),
        "Trend_Score": round(float(trend_score),2),
        "Momentum_Score": round(float(momentum_score),2),
        "RSI_Score": round(float(rsi_score),2),
        "Volume_Score": round(float(volume_score),2),
        "Position_Score": round(float(position_score),2),
        "Breakout_Score": round(float(breakout_score),2),
        "Setup": setup,
    }

def calculate_technical_indicators(universe, period="2y", batch_size=100):
    """Download Yahoo EOD data for the NSE universe and return latest technical rows."""
    u = universe.copy()
    symbol_col = next((c for c in u.columns if str(c).lower()=="symbol"), None)
    yahoo_col = next((c for c in u.columns if str(c).lower() in {"yahoo_symbol","yahoo symbol"}), None)
    if not symbol_col:
        raise ValueError("Technical engine requires Symbol/symbol in universe.")
    if not yahoo_col:
        u["yahoo_symbol"] = u[symbol_col].astype(str).str.upper()+".NS"
        yahoo_col = "yahoo_symbol"

    tickers = u[yahoo_col].dropna().astype(str).unique().tolist()
    results = []
    failures = []
    print(f"Downloading historical OHLCV for {len(tickers):,} NSE stocks...")
    for start in range(0, len(tickers), batch_size):
        batch = tickers[start:start+batch_size]
        try:
            raw = yf.download(
                batch, period=period, interval="1d",
                auto_adjust=False, progress=False, group_by="ticker",
                threads=True
            )
        except Exception as e:
            failures.extend([(t, str(e)) for t in batch])
            continue

        for ticker in batch:
            try:
                row = _analyse(ticker, raw if len(batch)>1 else raw)
                if row:
                    results.append(row)
                else:
                    failures.append((ticker, "insufficient or invalid OHLCV"))
            except Exception as e:
                failures.append((ticker, str(e)))

        done = min(start+len(batch), len(tickers))
        print(f"Technical progress: {done:,}/{len(tickers):,}")
        time.sleep(0.2)

    out = pd.DataFrame(results)
    if not out.empty:
        names = u[[symbol_col] + ([c for c in ["name","series","isin"] if c in u.columns])].copy()
        names = names.rename(columns={symbol_col:"Symbol"})
        out = out.merge(names.drop_duplicates("Symbol"), on="Symbol", how="left")
    pd.DataFrame(failures, columns=["Yahoo_Symbol","Reason"]).to_csv(
        OUTPUT_DIR/"technical_failures.csv", index=False
    )
    out.to_csv(OUTPUT_DIR/"technical_scan.csv", index=False)
    print(f"Technical records: {len(out):,}")
    return out

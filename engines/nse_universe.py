from pathlib import Path
import io
import requests
import pandas as pd

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

NSE_URL = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"

def _session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 Chrome/140 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    })
    return s

def get_nse_universe():
    """Return the official NSE equity master with a Yahoo Finance symbol."""
    out = DATA_DIR / "nse_universe.csv"
    try:
        s = _session()
        s.get("https://www.nseindia.com/", timeout=20)
        r = s.get("https://www.nseindia.com/api/equity-master", timeout=30)
        if r.ok:
            payload = r.json()
            rows = payload.get("data", payload if isinstance(payload, list) else [])
            df = pd.DataFrame(rows)
            if not df.empty:
                # NSE's equity-master response can change shape. Prefer common fields.
                sym = next((c for c in df.columns if str(c).lower() in {"symbol","sym"}), None)
                if sym:
                    df["symbol"] = df[sym].astype(str).str.strip().str.upper()
                else:
                    df = pd.DataFrame()
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        try:
            r = _session().get(
                "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
                timeout=30,
            )
            r.raise_for_status()
            df = pd.read_csv(io.BytesIO(r.content))
        except Exception:
            if out.exists():
                df = pd.read_csv(out)
            else:
                raise RuntimeError("Unable to download NSE equity universe.")

    rename = {}
    for c in df.columns:
        k = str(c).strip().lower()
        if k == "symbol":
            rename[c] = "symbol"
        elif k in {"name of company", "company name"}:
            rename[c] = "name"
        elif k == "series":
            rename[c] = "series"
        elif k == "isin number":
            rename[c] = "isin"
    df = df.rename(columns=rename)

    if "symbol" not in df.columns:
        raise RuntimeError("NSE universe does not contain SYMBOL.")

    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    if "series" in df.columns:
        df["series"] = df["series"].astype(str).str.upper()
        df = df[df["series"].isin(["EQ","BE","BZ"])].copy()

    df = df[df["symbol"].str.len().between(1, 30)]
    df = df.drop_duplicates("symbol").reset_index(drop=True)
    df["yahoo_symbol"] = df["symbol"] + ".NS"

    cols = [c for c in ["symbol","name","series","isin","yahoo_symbol"] if c in df.columns]
    df[cols].to_csv(out, index=False)
    print(f"Valid NSE equity securities: {len(df):,}")
    return df[cols]

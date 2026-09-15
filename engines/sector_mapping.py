import pandas as pd
from pathlib import Path

OUTPUT=Path("output"); OUTPUT.mkdir(exist_ok=True)

def load_sector_mapping():
    p=Path("data/sector_mapping.csv")
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame(columns=["Symbol","Primary_Sector","Primary_Sector_Index"])

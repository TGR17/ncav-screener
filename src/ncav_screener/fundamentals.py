from __future__ import annotations

from pathlib import Path

import pandas as pd


TICKER_COLUMN = "\uc885\ubaa9\ucf54\ub4dc"
NAME_COLUMN = "\uc885\ubaa9\uba85"
CLOSE_COLUMN = "\uc885\uac00"
EPS_COLUMN = "EPS"
PER_COLUMN = "PER"
BPS_COLUMN = "BPS"
PBR_COLUMN = "PBR"
DIVIDEND_PER_SHARE_COLUMN = "\uc8fc\ub2f9\ubc30\ub2f9\uae08"
DIVIDEND_YIELD_COLUMN = "\ubc30\ub2f9\uc218\uc775\ub960"


def read_krx_fundamental_csv(path: Path) -> pd.DataFrame:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=encoding, dtype={TICKER_COLUMN: str})
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Could not read KRX fundamental CSV: {path}")


def load_fundamentals(path: Path) -> pd.DataFrame:
    raw = read_krx_fundamental_csv(path)
    required = {TICKER_COLUMN, EPS_COLUMN, PER_COLUMN, BPS_COLUMN, PBR_COLUMN}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Fundamental file is missing columns: {sorted(missing)}")

    output = pd.DataFrame(
        {
            "ticker": raw[TICKER_COLUMN].astype(str).str.zfill(6),
            "fundamental_name": raw.get(NAME_COLUMN, ""),
            "fundamental_close": pd.to_numeric(raw.get(CLOSE_COLUMN, ""), errors="coerce"),
            "eps": pd.to_numeric(raw[EPS_COLUMN], errors="coerce"),
            "per": pd.to_numeric(raw[PER_COLUMN], errors="coerce"),
            "bps": pd.to_numeric(raw[BPS_COLUMN], errors="coerce"),
            "pbr": pd.to_numeric(raw[PBR_COLUMN], errors="coerce"),
            "dividend_per_share": pd.to_numeric(raw.get(DIVIDEND_PER_SHARE_COLUMN, ""), errors="coerce"),
            "dividend_yield": pd.to_numeric(raw.get(DIVIDEND_YIELD_COLUMN, ""), errors="coerce"),
        }
    )
    return output


def merge_fundamentals(results: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.DataFrame:
    output = results.copy()
    output["ticker"] = output["ticker"].astype(str).str.zfill(6)
    return output.merge(fundamentals, on="ticker", how="left")

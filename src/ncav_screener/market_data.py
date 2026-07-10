from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


KRX_TICKER_COLUMN = "\uc885\ubaa9\ucf54\ub4dc"
KRX_NAME_COLUMN = "\uc885\ubaa9\uba85"
KRX_MARKET_COLUMN = "\uc2dc\uc7a5\uad6c\ubd84"
KRX_SECTION_COLUMN = "\uc18c\uc18d\ubd80"
KRX_CLOSE_COLUMN = "\uc885\uac00"
KRX_VOLUME_COLUMN = "\uac70\ub798\ub7c9"
KRX_TRADING_VALUE_COLUMN = "\uac70\ub798\ub300\uae08"
KRX_MARKET_CAP_COLUMN = "\uc2dc\uac00\ucd1d\uc561"
KRX_LISTED_SHARES_COLUMN = "\uc0c1\uc7a5\uc8fc\uc2dd\uc218"

PREFERRED_SHARE_PATTERN = r"(?:\d*\uc6b0B?$|\uc6b0\(\uc804\ud658\)$|\uc804\ud658\)$|\uc6b0\uc120\uc8fc$)"
SPAC_PATTERN = r"(?:\uc2a4\ud329|SPAC)"
FINANCIAL_PATTERN = r"(?:\uae08\uc735\uc9c0\uc8fc|\uae08\uc735|\uc740\ud589|\uc99d\uad8c|\uc190\ud574\ubcf4\ud5d8|\uc0dd\uba85\ubcf4\ud5d8|\ubcf4\ud5d8)"
HOLDING_PATTERN = r"(?:\ud640\ub529\uc2a4|\uc9c0\uc8fc|Holdings)"
RISK_SECTION_PATTERN = r"(?:\uad00\ub9ac|\ud22c\uc790\uc8fc\uc758|\ud658\uae30|\uac70\ub798\uc815\uc9c0|\uc815\ub9ac\ub9e4\ub9e4)"
EXCLUDED_INDUSTRY_PATTERN = (
    r"(?:\uae08\uc735|\uc740\ud589|\uc99d\uad8c|\ubcf4\ud5d8|\uc2e0\ud0c1|\uc5ec\uc2e0|"
    r"\uce74\ub4dc|\uc804\uae30|\uac00\uc2a4|\uc218\ub3c4|\uc99d\uae30|\uc804\ub825|"
    r"\ubc1c\uc804|\ub3c4\uc2dc\uac00\uc2a4)"
)


@dataclass(frozen=True)
class MarketDataRow:
    ticker: str
    name: str
    market_cap: float
    shares_outstanding: float
    source_date: str | None = None
    source: str | None = None


def load_market_data(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"ticker": str})
    required = {"ticker", "market_cap", "shares_outstanding"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Market data file is missing columns: {sorted(missing)}")
    return frame


def get_market_data_row(path: Path, ticker: str) -> MarketDataRow:
    frame = load_market_data(path)
    matches = frame.loc[frame["ticker"] == ticker]
    if matches.empty:
        raise LookupError(f"No market data found for ticker: {ticker}")

    row = matches.iloc[0]
    return MarketDataRow(
        ticker=str(row["ticker"]),
        name=str(row.get("name", "")),
        market_cap=float(row["market_cap"]),
        shares_outstanding=float(row["shares_outstanding"]),
        source_date=None if pd.isna(row.get("source_date")) else str(row.get("source_date")),
        source=None if pd.isna(row.get("source")) else str(row.get("source")),
    )


def convert_krx_raw_to_market_data(
    raw_path: Path,
    output_path: Path,
    source_date: str | None = None,
) -> pd.DataFrame:
    raw = read_krx_raw_csv(raw_path)
    required = {
        KRX_TICKER_COLUMN,
        KRX_NAME_COLUMN,
        KRX_MARKET_CAP_COLUMN,
        KRX_LISTED_SHARES_COLUMN,
    }
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"KRX raw file is missing columns: {sorted(missing)}")

    output = pd.DataFrame(
        {
            "ticker": raw[KRX_TICKER_COLUMN].astype(str).str.zfill(6),
            "name": raw[KRX_NAME_COLUMN],
            "market": raw.get(KRX_MARKET_COLUMN, ""),
            "section": raw.get(KRX_SECTION_COLUMN, ""),
            "close": pd.to_numeric(raw.get(KRX_CLOSE_COLUMN, ""), errors="coerce"),
            "volume": pd.to_numeric(raw.get(KRX_VOLUME_COLUMN, ""), errors="coerce"),
            "trading_value": pd.to_numeric(raw.get(KRX_TRADING_VALUE_COLUMN, ""), errors="coerce"),
            "market_cap": pd.to_numeric(raw[KRX_MARKET_CAP_COLUMN], errors="coerce"),
            "shares_outstanding": pd.to_numeric(raw[KRX_LISTED_SHARES_COLUMN], errors="coerce"),
            "source_date": source_date or "",
            "source": raw_path.name,
        }
    )
    output = output.dropna(subset=["market_cap", "shares_outstanding"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output


def filter_screening_universe(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()
    names = filtered["name"].fillna("").astype(str)

    preferred_share_mask = (
        names.str.contains(PREFERRED_SHARE_PATTERN, regex=True)
        | filtered["ticker"].astype(str).str.contains(r"[A-Za-z]", regex=True)
    )
    spac_mask = names.str.contains(SPAC_PATTERN, case=False, regex=True)
    financial_mask = names.str.contains(FINANCIAL_PATTERN, regex=True)
    holding_mask = names.str.contains(HOLDING_PATTERN, case=False, regex=True)
    return filtered.loc[
        ~(preferred_share_mask | spac_mask | financial_mask | holding_mask)
    ].copy()


def filter_korean_statement_universe(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()
    if "industry_name" not in filtered.columns:
        return filtered

    industries = filtered["industry_name"].fillna("").astype(str)
    excluded_industry_mask = industries.str.contains(EXCLUDED_INDUSTRY_PATTERN, regex=True)
    return filtered.loc[~excluded_industry_mask].copy()


def read_krx_raw_csv(raw_path: Path) -> pd.DataFrame:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(raw_path, dtype={KRX_TICKER_COLUMN: str}, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Could not read KRX raw CSV: {raw_path}")

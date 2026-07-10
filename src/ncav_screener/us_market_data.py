from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from .sec_client import normalize_sec_ticker


REQUIRED_COLUMNS = {"ticker", "market_cap"}
OPTIONAL_COLUMNS = ["name", "exchange", "price", "shares_outstanding"]
DEFAULT_EXCLUDED_SECTORS = {"Finance", "Real Estate"}
DEFAULT_EXCLUDED_NAME_KEYWORDS = (
    "acquisition",
    "adr",
    "american depositary",
    "bond",
    "closed end",
    "depositary shares",
    "etf",
    "exchange traded",
    "fund",
    "note",
    "preferred",
    "right",
    "spac",
    "trust",
    "unit",
    "warrant",
)
NASDAQ_SCREENER_URL = "https://api.nasdaq.com/api/screener/stocks"
NASDAQ_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/market-activity/stocks/screener",
}


def load_us_market_data(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"ticker": str})
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"US market data is missing columns: {sorted(missing)}")

    output = frame.copy()
    output = output.dropna(subset=["ticker"])
    output["ticker"] = output["ticker"].map(lambda value: normalize_sec_ticker(str(value)))
    output = output.loc[output["ticker"] != ""].copy()
    output["market_cap"] = pd.to_numeric(output["market_cap"], errors="coerce")
    if "shares_outstanding" in output.columns:
        output["shares_outstanding"] = pd.to_numeric(output["shares_outstanding"], errors="coerce")
    if "price" in output.columns:
        output["price"] = pd.to_numeric(output["price"], errors="coerce")

    output = output.dropna(subset=["ticker", "market_cap"])
    output = output.loc[output["market_cap"] > 0].copy()
    output = output.drop_duplicates("ticker", keep="first")

    for column in OPTIONAL_COLUMNS:
        if column not in output.columns:
            output[column] = pd.NA
    extra_columns = [column for column in ["sector", "industry", "volume", "country"] if column in output.columns]
    return output[["ticker", *OPTIONAL_COLUMNS, "market_cap", *extra_columns]]


def download_nasdaq_us_market_data(
    output_path: Path,
    *,
    limit: int = 10000,
    timeout_seconds: float = 30.0,
) -> pd.DataFrame:
    response = requests.get(
        NASDAQ_SCREENER_URL,
        params={"tableonly": "true", "limit": str(limit), "download": "true"},
        headers=NASDAQ_HEADERS,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("data", {}).get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("Nasdaq screener payload is missing data.rows")

    frame = pd.DataFrame([_parse_nasdaq_row(row) for row in rows])
    frame = frame.dropna(subset=["ticker", "price", "market_cap"])
    frame = frame.loc[(frame["price"] > 0) & (frame["market_cap"] > 0)].copy()
    frame["shares_outstanding"] = frame["market_cap"] / frame["price"]
    frame = frame.drop_duplicates("ticker", keep="first")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False, encoding="utf-8-sig")
    return frame


def filter_us_screening_universe(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if "sector" in output.columns:
        output = output.loc[~output["sector"].isin(DEFAULT_EXCLUDED_SECTORS)].copy()

    name = output["name"].fillna("").astype(str).str.lower() if "name" in output.columns else pd.Series("", index=output.index)
    keyword_pattern = "|".join(DEFAULT_EXCLUDED_NAME_KEYWORDS)
    output = output.loc[~name.str.contains(keyword_pattern, regex=True)].copy()
    return output.reset_index(drop=True)


def _parse_nasdaq_row(row: dict) -> dict:
    ticker = normalize_sec_ticker(str(row.get("symbol", "")))
    return {
        "ticker": ticker,
        "name": _clean_text(row.get("name")),
        "exchange": pd.NA,
        "price": _parse_number(row.get("lastsale")),
        "shares_outstanding": pd.NA,
        "market_cap": _parse_number(row.get("marketCap")),
        "volume": _parse_number(row.get("volume")),
        "sector": _clean_text(row.get("sector")),
        "industry": _clean_text(row.get("industry")),
        "country": _clean_text(row.get("country")),
    }


def _parse_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).replace("$", "").replace(",", "").replace("%", "").strip()
    if not text or text.upper() in {"N/A", "NA", "NONE"}:
        return None
    return float(text)


def _clean_text(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from pykrx import stock


MARKET_CAP_COLUMN = "\uc2dc\uac00\ucd1d\uc561"
LISTED_SHARES_COLUMN = "\uc0c1\uc7a5\uc8fc\uc2dd\uc218"


def get_market_cap_by_ticker(date: str, market: str = "ALL") -> pd.DataFrame:
    return stock.get_market_cap_by_ticker(date, market=market)


def get_tickers(date: str, market: str = "ALL") -> list[str]:
    return stock.get_market_ticker_list(date, market=market)


def get_ticker_name(ticker: str) -> str:
    return stock.get_market_ticker_name(ticker)


def get_market_cap_row(
    ticker: str,
    date: str,
    markets: tuple[str, ...] = ("ALL", "KOSDAQ", "KOSPI"),
    lookback_days: int = 10,
) -> tuple[pd.Series, str, str]:
    target = datetime.strptime(date.replace("-", ""), "%Y%m%d")
    last_error: Exception | None = None

    for offset in range(lookback_days + 1):
        query_date = (target - timedelta(days=offset)).strftime("%Y%m%d")
        for market in markets:
            try:
                frame = stock.get_market_cap_by_ticker(
                    query_date,
                    market=market,
                    alternative=True,
                )
                if frame.empty or ticker not in frame.index:
                    continue
                return frame.loc[ticker], query_date, market
            except Exception as exc:
                last_error = exc

        try:
            row = get_market_cap_row_by_ticker_range(ticker, query_date)
            return row, query_date, "TICKER_RANGE"
        except Exception as exc:
            last_error = exc

    message = f"Could not find market cap for {ticker} near {date}"
    if last_error is not None:
        message = f"{message}. Last error: {last_error}"
    raise LookupError(message)


def get_market_cap_row_by_ticker_range(ticker: str, date: str) -> pd.Series:
    frame = stock.get_market_cap(date, date, ticker)
    if frame.empty:
        raise LookupError(f"No market cap range data for {ticker} on {date}")

    row = frame.iloc[-1].copy()
    required_columns = {MARKET_CAP_COLUMN, LISTED_SHARES_COLUMN}
    if not required_columns.issubset(set(row.index)):
        raise LookupError(f"Missing market cap columns for {ticker} on {date}: {list(row.index)}")
    return row

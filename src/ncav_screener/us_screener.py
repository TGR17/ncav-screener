from __future__ import annotations

from pathlib import Path
import time
from zipfile import ZipFile

import pandas as pd

from .sec_client import (
    SecCompany,
    companyfacts_cache_path,
    download_companyfacts,
    find_company_by_ticker,
    load_companyfacts,
    load_companyfacts_from_archive,
)
from .us_facts import add_us_market_metrics, build_us_financial_snapshot


MISSING_COMPANYFACTS_NOTE = "SEC companyfacts ZIP에 재무자료 없음"


def build_us_screener_results(
    market_data: pd.DataFrame,
    companies: list[SecCompany],
    facts_dir: Path,
    *,
    refresh_facts: bool = False,
    user_agent: str | None = None,
    limit: int | None = None,
    request_delay_seconds: float = 0.0,
    companyfacts_zip: Path | None = None,
    financial_cache: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if financial_cache is not None:
        return build_us_screener_results_from_financial_cache(market_data, financial_cache, limit=limit)

    rows = []
    universe = market_data.head(limit) if limit is not None else market_data
    archive = ZipFile(companyfacts_zip) if companyfacts_zip is not None and companyfacts_zip.exists() and not refresh_facts else None
    try:
        for market_row in universe.to_dict("records"):
            ticker = str(market_row["ticker"])
            company = find_company_by_ticker(ticker, companies)
            if company is None:
                rows.append(_error_row(market_row, "SEC ticker not found"))
                continue

            facts_path = companyfacts_cache_path(facts_dir, company.cik)
            try:
                if archive is not None:
                    payload = load_companyfacts_from_archive(archive, company.cik)
                elif refresh_facts or not facts_path.exists():
                    payload = download_companyfacts(company.cik, facts_path, user_agent=user_agent)
                else:
                    payload = load_companyfacts(facts_path)

                snapshot = build_us_financial_snapshot(payload)
                metrics = add_us_market_metrics(
                    snapshot,
                    market_cap=float(market_row["market_cap"]),
                    shares_outstanding=_optional_float(market_row.get("shares_outstanding")),
                )
                rows.append(
                    {
                        "ticker": ticker,
                        "name": _optional_text(market_row.get("name")) or company.name,
                        "exchange": _optional_text(market_row.get("exchange")) or company.exchange,
                        "cik": company.cik,
                        "cik10": company.cik10,
                        "price": _optional_float(market_row.get("price")),
                        "volume": _optional_float(market_row.get("volume")),
                        "sector": _optional_text(market_row.get("sector")),
                        "industry": _optional_text(market_row.get("industry")),
                        "country": _optional_text(market_row.get("country")),
                        **metrics,
                        "data_status": "ok",
                        "data_note": "",
                    }
                )
            except Exception as exc:  # noqa: BLE001 - keep batch output usable per ticker
                rows.append(_error_row(market_row, _format_companyfacts_error(exc), company=company))
            if archive is None and request_delay_seconds > 0:
                time.sleep(request_delay_seconds)
    finally:
        if archive is not None:
            archive.close()

    return pd.DataFrame(rows)


def build_us_screener_results_from_financial_cache(
    market_data: pd.DataFrame,
    financial_cache: pd.DataFrame,
    *,
    limit: int | None = None,
) -> pd.DataFrame:
    rows = []
    universe = market_data.head(limit) if limit is not None else market_data
    cache_by_ticker = {
        str(row["ticker"]).upper(): row
        for row in financial_cache.to_dict("records")
        if row.get("ticker") is not None and not pd.isna(row.get("ticker"))
    }

    for market_row in universe.to_dict("records"):
        ticker = str(market_row["ticker"])
        cached = cache_by_ticker.get(ticker.upper())
        if cached is None:
            rows.append(_error_row(market_row, _format_cached_error_note("SEC financial cache not found")))
            continue

        if str(cached.get("data_status", "")).lower() == "error":
            rows.append(
                _error_row(
                    market_row,
                    _format_cached_error_note(_optional_text(cached.get("data_note")) or "SEC financial cache error"),
                    company=_cached_company(cached),
                )
            )
            continue

        snapshot = {
            key: _none_if_missing(value)
            for key, value in cached.items()
            if key not in {"ticker", "name", "exchange", "cik", "cik10", "data_status", "data_note"}
        }
        metrics = add_us_market_metrics(
            snapshot,
            market_cap=float(market_row["market_cap"]),
            shares_outstanding=_optional_float(market_row.get("shares_outstanding")),
        )
        rows.append(
            {
                "ticker": ticker,
                "name": _optional_text(market_row.get("name")) or _optional_text(cached.get("name")),
                "exchange": _optional_text(market_row.get("exchange")) or _optional_text(cached.get("exchange")),
                "cik": _optional_int(cached.get("cik")),
                "cik10": _optional_text(cached.get("cik10")),
                "price": _optional_float(market_row.get("price")),
                "volume": _optional_float(market_row.get("volume")),
                "sector": _optional_text(market_row.get("sector")),
                "industry": _optional_text(market_row.get("industry")),
                "country": _optional_text(market_row.get("country")),
                **metrics,
                "data_status": "ok",
                "data_note": "",
            }
        )

    return pd.DataFrame(rows)


def _optional_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _optional_int(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(float(value))


def _optional_text(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _none_if_missing(value: object) -> object:
    if value is None or pd.isna(value):
        return None
    return value


def _cached_company(row: dict) -> SecCompany | None:
    cik = _optional_int(row.get("cik"))
    ticker = _optional_text(row.get("ticker"))
    if cik is None or ticker is None:
        return None
    return SecCompany(
        cik=cik,
        name=_optional_text(row.get("name")) or "",
        ticker=ticker,
        exchange=_optional_text(row.get("exchange")) or "",
    )


def _error_row(market_row: dict, note: str, company: SecCompany | None = None) -> dict:
    return {
        "ticker": market_row.get("ticker"),
        "name": _optional_text(market_row.get("name")) or (company.name if company else None),
        "exchange": _optional_text(market_row.get("exchange")) or (company.exchange if company else None),
        "cik": company.cik if company else None,
        "cik10": company.cik10 if company else None,
        "price": _optional_float(market_row.get("price")),
        "volume": _optional_float(market_row.get("volume")),
        "sector": _optional_text(market_row.get("sector")),
        "industry": _optional_text(market_row.get("industry")),
        "country": _optional_text(market_row.get("country")),
        "market_cap": _optional_float(market_row.get("market_cap")),
        "shares_outstanding": _optional_float(market_row.get("shares_outstanding")),
        "data_status": "error",
        "data_note": note,
    }


def _format_companyfacts_error(exc: Exception) -> str:
    if isinstance(exc, KeyError) and "There is no item named" in str(exc):
        return MISSING_COMPANYFACTS_NOTE
    return str(exc)


def _format_cached_error_note(note: str) -> str:
    if "There is no item named" in note and "in the archive" in note:
        return MISSING_COMPANYFACTS_NOTE
    if note == "SEC financial cache not found":
        return "SEC 재무 캐시에 자료 없음"
    return note

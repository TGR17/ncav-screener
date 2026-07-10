from __future__ import annotations

from pathlib import Path
import time
from zipfile import ZipFile

import pandas as pd

from .sec_client import (
    SecCompany,
    companyfacts_cache_path,
    download_companyfacts,
    load_companyfacts,
    load_companyfacts_from_archive,
)
from .us_facts import build_us_financial_snapshot


def build_us_financial_cache(
    companies: list[SecCompany],
    facts_dir: Path,
    *,
    refresh_facts: bool = False,
    user_agent: str | None = None,
    limit: int | None = None,
    request_delay_seconds: float = 0.0,
    companyfacts_zip: Path | None = None,
) -> pd.DataFrame:
    rows = []
    universe = companies[:limit] if limit is not None else companies
    archive = ZipFile(companyfacts_zip) if companyfacts_zip is not None and companyfacts_zip.exists() and not refresh_facts else None
    try:
        for company in universe:
            try:
                facts_path = companyfacts_cache_path(facts_dir, company.cik)
                if archive is not None:
                    payload = load_companyfacts_from_archive(archive, company.cik)
                elif refresh_facts or not facts_path.exists():
                    payload = download_companyfacts(company.cik, facts_path, user_agent=user_agent)
                else:
                    payload = load_companyfacts(facts_path)

                rows.append(
                    {
                        "ticker": company.ticker,
                        "name": company.name,
                        "exchange": company.exchange,
                        "cik": company.cik,
                        "cik10": company.cik10,
                        **build_us_financial_snapshot(payload),
                        "data_status": "ok",
                        "data_note": "",
                    }
                )
            except Exception as exc:  # noqa: BLE001 - keep batch output usable per company
                rows.append(
                    {
                        "ticker": company.ticker,
                        "name": company.name,
                        "exchange": company.exchange,
                        "cik": company.cik,
                        "cik10": company.cik10,
                        "data_status": "error",
                        "data_note": _format_companyfacts_error(exc),
                    }
                )
            if archive is None and request_delay_seconds > 0:
                time.sleep(request_delay_seconds)
    finally:
        if archive is not None:
            archive.close()

    return pd.DataFrame(rows)


def _format_companyfacts_error(exc: Exception) -> str:
    if isinstance(exc, KeyError) and "There is no item named" in str(exc):
        return "SEC companyfacts ZIP에 재무자료 없음"
    return str(exc)


def save_us_financial_cache(frame: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False, encoding="utf-8-sig")
    return frame


def load_us_financial_cache(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"ticker": str, "cik10": str})
    if "ticker" not in frame.columns:
        raise ValueError("US financial cache is missing ticker column")
    output = frame.dropna(subset=["ticker"]).copy()
    output["ticker"] = output["ticker"].astype(str).str.upper().str.strip()
    output = output.loc[output["ticker"] != ""].copy()
    return output.drop_duplicates("ticker", keep="first")

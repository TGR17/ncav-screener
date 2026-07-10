from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from zipfile import ZipFile

import requests


SEC_COMPANY_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
DEFAULT_SEC_USER_AGENT = "ncav-screener contact@example.com"
CORE_US_GAAP_TAGS = [
    "AssetsCurrent",
    "Liabilities",
    "CashAndCashEquivalentsAtCarryingValue",
    "OperatingIncomeLoss",
    "NetIncomeLoss",
    "Assets",
    "StockholdersEquity",
    "NetCashProvidedByUsedInOperatingActivities",
    "CurrentLiabilities",
    "GrossProfit",
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "ShortTermBorrowings",
    "ShortTermDebtCurrent",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
    "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
    "FinanceLeaseLiabilityCurrent",
    "FinanceLeaseLiabilityNoncurrent",
]


@dataclass(frozen=True)
class SecCompany:
    cik: int
    name: str
    ticker: str
    exchange: str

    @property
    def cik10(self) -> str:
        return format_cik(self.cik)

    @property
    def companyfacts_url(self) -> str:
        return build_companyfacts_url(self.cik)


def normalize_sec_ticker(ticker: str) -> str:
    return ticker.strip().upper().replace(".", "-")


def format_cik(cik: int | str) -> str:
    return str(cik).strip().zfill(10)


def build_companyfacts_url(cik: int | str) -> str:
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{format_cik(cik)}.json"


def companyfacts_cache_path(cache_dir: Path, cik: int | str) -> Path:
    return cache_dir / f"CIK{format_cik(cik)}.json"


def companyfacts_zip_member(cik: int | str) -> str:
    return f"CIK{format_cik(cik)}.json"


def parse_company_tickers_exchange(payload: dict) -> list[SecCompany]:
    fields = payload.get("fields")
    rows = payload.get("data")
    if not isinstance(fields, list) or not isinstance(rows, list):
        raise ValueError("SEC ticker payload must contain fields and data arrays")

    required = {"cik", "name", "ticker", "exchange"}
    missing = required.difference(fields)
    if missing:
        raise ValueError(f"SEC ticker payload is missing fields: {sorted(missing)}")

    companies = []
    for row in rows:
        item = dict(zip(fields, row))
        companies.append(
            SecCompany(
                cik=int(item["cik"]),
                name=str(item["name"]),
                ticker=normalize_sec_ticker(str(item["ticker"])),
                exchange=str(item["exchange"]),
            )
        )
    return companies


def load_company_tickers_exchange(path: Path) -> list[SecCompany]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return parse_company_tickers_exchange(payload)


def download_company_tickers_exchange(
    output_path: Path,
    *,
    user_agent: str | None = None,
    timeout_seconds: float = 30.0,
) -> list[SecCompany]:
    headers = {"User-Agent": user_agent or DEFAULT_SEC_USER_AGENT}
    response = requests.get(SEC_COMPANY_TICKERS_EXCHANGE_URL, headers=headers, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False)

    return parse_company_tickers_exchange(payload)


def load_companyfacts(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_companyfacts_from_zip(zip_path: Path, cik: int | str) -> dict:
    member = companyfacts_zip_member(cik)
    with ZipFile(zip_path) as archive:
        return load_companyfacts_from_archive(archive, cik)


def load_companyfacts_from_archive(archive: ZipFile, cik: int | str) -> dict:
    member = companyfacts_zip_member(cik)
    with archive.open(member) as file:
        return json.load(file)


def companyfacts_exists_in_zip(zip_path: Path, cik: int | str) -> bool:
    member = companyfacts_zip_member(cik)
    with ZipFile(zip_path) as archive:
        return member in archive.namelist()


def download_companyfacts(
    cik: int | str,
    output_path: Path,
    *,
    user_agent: str | None = None,
    timeout_seconds: float = 30.0,
) -> dict:
    headers = {"User-Agent": user_agent or DEFAULT_SEC_USER_AGENT}
    response = requests.get(build_companyfacts_url(cik), headers=headers, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False)

    return payload


def find_company_by_ticker(ticker: str, companies: list[SecCompany]) -> SecCompany | None:
    normalized = normalize_sec_ticker(ticker)
    for company in companies:
        if company.ticker == normalized:
            return company
    return None


def summarize_us_gaap_tags(payload: dict, tags: list[str] | None = None) -> list[dict[str, object]]:
    facts = payload.get("facts", {})
    us_gaap = facts.get("us-gaap", {}) if isinstance(facts, dict) else {}
    summary = []
    for tag in tags or CORE_US_GAAP_TAGS:
        fact = us_gaap.get(tag)
        units = fact.get("units", {}) if isinstance(fact, dict) else {}
        unit_names = sorted(units.keys())
        point_count = sum(len(points) for points in units.values() if isinstance(points, list))
        latest = find_latest_usd_fact(fact) if isinstance(fact, dict) else None
        summary.append(
            {
                "tag": tag,
                "available": fact is not None,
                "units": ", ".join(unit_names),
                "points": point_count,
                "latest_value": latest.get("val") if latest else None,
                "latest_end": latest.get("end") if latest else None,
                "latest_form": latest.get("form") if latest else None,
                "latest_frame": latest.get("frame") if latest else None,
            }
        )
    return summary


def find_latest_usd_fact(fact: dict) -> dict | None:
    units = fact.get("units", {})
    points = units.get("USD")
    if not isinstance(points, list):
        return None

    usable = [point for point in points if isinstance(point, dict) and point.get("end") and point.get("val") is not None]
    if not usable:
        return None
    return max(usable, key=lambda point: (str(point.get("end", "")), str(point.get("filed", ""))))

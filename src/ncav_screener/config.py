from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = DATA_DIR / "output"
CORP_CODE_ZIP = CACHE_DIR / "corpCode.zip"
INPUT_DIR = DATA_DIR / "input"
MARKET_DATA_CSV = INPUT_DIR / "market_data.csv"
US_MARKET_DATA_CSV = INPUT_DIR / "us_market_data.csv"
SEC_BULK_DIR = INPUT_DIR / "sec_bulk"
SEC_COMPANYFACTS_ZIP = SEC_BULK_DIR / "companyfacts.zip"
SEC_COMPANY_TICKERS_EXCHANGE_JSON = CACHE_DIR / "sec_company_tickers_exchange.json"
SEC_COMPANYFACTS_DIR = CACHE_DIR / "sec_companyfacts"
US_FINANCIAL_CACHE_CSV = CACHE_DIR / "us_financial_snapshot.csv"


@dataclass(frozen=True)
class Settings:
    dart_api_key: str | None
    sec_user_agent: str | None


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    return Settings(
        dart_api_key=os.getenv("DART_API_KEY"),
        sec_user_agent=os.getenv("SEC_USER_AGENT"),
    )

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


@dataclass(frozen=True)
class Settings:
    dart_api_key: str | None


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    return Settings(dart_api_key=os.getenv("DART_API_KEY"))

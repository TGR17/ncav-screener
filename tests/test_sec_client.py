from pathlib import Path
import json
from zipfile import ZipFile

from ncav_screener.sec_client import (
    build_companyfacts_url,
    companyfacts_cache_path,
    companyfacts_zip_member,
    find_company_by_ticker,
    format_cik,
    load_companyfacts_from_zip,
    parse_company_tickers_exchange,
    summarize_us_gaap_tags,
)


def test_parse_and_find_sec_company_by_ticker() -> None:
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [
            [320193, "Apple Inc.", "AAPL", "Nasdaq"],
            [1067983, "BERKSHIRE HATHAWAY INC", "BRK-B", "NYSE"],
        ],
    }

    companies = parse_company_tickers_exchange(payload)
    apple = find_company_by_ticker("aapl", companies)
    berkshire = find_company_by_ticker("brk.b", companies)

    assert apple is not None
    assert apple.cik == 320193
    assert apple.cik10 == "0000320193"
    assert apple.companyfacts_url == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    assert berkshire is not None
    assert berkshire.ticker == "BRK-B"


def test_format_cik_and_companyfacts_url() -> None:
    assert format_cik(320193) == "0000320193"
    assert build_companyfacts_url("320193") == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    assert companyfacts_cache_path(Path("cache"), 320193) == Path("cache") / "CIK0000320193.json"
    assert companyfacts_zip_member(320193) == "CIK0000320193.json"


def test_summarize_us_gaap_tags_reports_latest_usd_fact() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "AssetsCurrent": {
                    "units": {
                        "USD": [
                            {"val": 100, "end": "2023-12-31", "filed": "2024-02-01", "form": "10-K"},
                            {"val": 120, "end": "2024-03-31", "filed": "2024-05-01", "form": "10-Q"},
                        ]
                    }
                }
            }
        }
    }

    summary = summarize_us_gaap_tags(payload, ["AssetsCurrent", "Liabilities"])

    assert summary[0]["available"] is True
    assert summary[0]["latest_value"] == 120
    assert summary[0]["latest_end"] == "2024-03-31"
    assert summary[1]["available"] is False


def test_load_companyfacts_from_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "companyfacts.zip"
    payload = {"cik": 320193, "facts": {"us-gaap": {}}}
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("CIK0000320193.json", json.dumps(payload))

    assert load_companyfacts_from_zip(zip_path, 320193)["cik"] == 320193

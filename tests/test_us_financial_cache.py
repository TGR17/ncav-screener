import json
from zipfile import ZipFile

from ncav_screener.sec_client import SecCompany
from ncav_screener.us_financial_cache import build_us_financial_cache


def test_build_us_financial_cache_extracts_snapshot_from_companyfacts_zip(tmp_path) -> None:
    facts_zip = tmp_path / "companyfacts.zip"
    payload = {
        "facts": {
            "us-gaap": {
                "AssetsCurrent": {"units": {"USD": [{"val": 500, "end": "2024-06-30"}]}},
                "Liabilities": {"units": {"USD": [{"val": 300, "end": "2024-06-30"}]}},
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [{"val": 80, "end": "2024-06-30"}]}
                },
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "val": 100,
                                "form": "10-K",
                                "fp": "FY",
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                            }
                        ]
                    }
                },
            }
        }
    }
    with ZipFile(facts_zip, "w") as archive:
        archive.writestr("CIK0000320193.json", json.dumps(payload))

    companies = [SecCompany(cik=320193, name="Apple Inc.", ticker="AAPL", exchange="Nasdaq")]

    result = build_us_financial_cache(companies, tmp_path / "facts", companyfacts_zip=facts_zip)

    assert result.loc[0, "ticker"] == "AAPL"
    assert result.loc[0, "data_status"] == "ok"
    assert result.loc[0, "current_assets"] == 500
    assert result.loc[0, "ncav"] == 200


def test_build_us_financial_cache_formats_missing_companyfacts_member(tmp_path) -> None:
    facts_zip = tmp_path / "companyfacts.zip"
    with ZipFile(facts_zip, "w"):
        pass

    companies = [SecCompany(cik=1548536, name="Santacruz Silver Mining Ltd.", ticker="SCZM", exchange="NYSE")]

    result = build_us_financial_cache(companies, tmp_path / "facts", companyfacts_zip=facts_zip)

    assert result.loc[0, "data_status"] == "error"
    assert result.loc[0, "data_note"] == "SEC companyfacts ZIP에 재무자료 없음"

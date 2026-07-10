import json
from zipfile import ZipFile

import pandas as pd

from ncav_screener.sec_client import SecCompany
from ncav_screener.us_screener import build_us_screener_results


def test_build_us_screener_results_joins_market_data_and_cached_facts(tmp_path) -> None:
    facts_dir = tmp_path / "facts"
    facts_dir.mkdir()
    (facts_dir / "CIK0000320193.json").write_text(
        json.dumps(
            {
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
                        "ShortTermDebtCurrent": {"units": {"USD": [{"val": 20, "end": "2024-06-30"}]}},
                        "OperatingLeaseLiabilityCurrent": {"units": {"USD": [{"val": 5, "end": "2024-06-30"}]}},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    market_data = pd.DataFrame(
        [{"ticker": "AAPL", "name": pd.NA, "exchange": pd.NA, "price": 30, "shares_outstanding": 10, "market_cap": 300}]
    )
    companies = [SecCompany(cik=320193, name="Apple Inc.", ticker="AAPL", exchange="Nasdaq")]

    result = build_us_screener_results(market_data, companies, facts_dir)

    assert len(result) == 1
    assert result.loc[0, "data_status"] == "ok"
    assert result.loc[0, "name"] == "Apple Inc."
    assert result.loc[0, "ncav"] == 200
    assert result.loc[0, "ev"] == 240
    assert result.loc[0, "ev_ebit"] == 2.4
    assert result.loc[0, "conservative_ev"] == 245
    assert result.loc[0, "conservative_ev_ebit"] == 2.45


def test_build_us_screener_results_can_read_companyfacts_zip(tmp_path) -> None:
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
    market_data = pd.DataFrame(
        [{"ticker": "AAPL", "name": pd.NA, "exchange": pd.NA, "price": 30, "shares_outstanding": 10, "market_cap": 300}]
    )
    companies = [SecCompany(cik=320193, name="Apple Inc.", ticker="AAPL", exchange="Nasdaq")]

    result = build_us_screener_results(market_data, companies, tmp_path / "facts", companyfacts_zip=facts_zip)

    assert result.loc[0, "data_status"] == "ok"
    assert result.loc[0, "ncav"] == 200


def test_build_us_screener_results_can_reuse_financial_cache(tmp_path) -> None:
    market_data = pd.DataFrame(
        [{"ticker": "AAPL", "name": pd.NA, "exchange": pd.NA, "price": 30, "shares_outstanding": 10, "market_cap": 300}]
    )
    financial_cache = pd.DataFrame(
        [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "exchange": "Nasdaq",
                "cik": 320193,
                "cik10": "0000320193",
                "current_assets": 500,
                "total_liabilities": 300,
                "cash_and_equivalents": 80,
                "interest_bearing_debt": 20,
                "other_financial_liabilities": 5,
                "ebit_ttm": 100,
                "ncav": 200,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    result = build_us_screener_results(market_data, [], tmp_path, financial_cache=financial_cache)

    assert result.loc[0, "data_status"] == "ok"
    assert result.loc[0, "name"] == "Apple Inc."
    assert result.loc[0, "cik"] == 320193
    assert result.loc[0, "ev"] == 240
    assert result.loc[0, "ev_ebit"] == 2.4
    assert result.loc[0, "conservative_ev"] == 245


def test_build_us_screener_results_formats_cached_missing_companyfacts_member(tmp_path) -> None:
    market_data = pd.DataFrame(
        [{"ticker": "SCZM", "name": "Santacruz", "exchange": "NYSE", "price": 10, "market_cap": 1000}]
    )
    financial_cache = pd.DataFrame(
        [
            {
                "ticker": "SCZM",
                "name": "Santacruz Silver Mining Ltd.",
                "exchange": "NYSE",
                "cik": 1548536,
                "cik10": "0001548536",
                "data_status": "error",
                "data_note": "\"There is no item named 'CIK0001548536.json' in the archive\"",
            }
        ]
    )

    result = build_us_screener_results(market_data, [], tmp_path, financial_cache=financial_cache)

    assert result.loc[0, "data_status"] == "error"
    assert result.loc[0, "data_note"] == "SEC companyfacts ZIP에 재무자료 없음"


def test_build_us_screener_results_formats_missing_financial_cache_row(tmp_path) -> None:
    market_data = pd.DataFrame(
        [{"ticker": "BRK/A", "name": "Berkshire Hathaway Inc.", "exchange": "NYSE", "price": 10, "market_cap": 1000}]
    )
    financial_cache = pd.DataFrame(
        [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "exchange": "Nasdaq",
                "cik": 320193,
                "cik10": "0000320193",
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    result = build_us_screener_results(market_data, [], tmp_path, financial_cache=financial_cache)

    assert result.loc[0, "data_status"] == "error"
    assert result.loc[0, "data_note"] == "SEC 재무 캐시에 자료 없음"


def test_build_us_screener_results_formats_missing_companyfacts_member(tmp_path) -> None:
    facts_zip = tmp_path / "companyfacts.zip"
    with ZipFile(facts_zip, "w"):
        pass
    market_data = pd.DataFrame(
        [{"ticker": "SCZM", "name": "Santacruz", "exchange": "NYSE", "price": 10, "market_cap": 1000}]
    )
    companies = [SecCompany(cik=1548536, name="Santacruz Silver Mining Ltd.", ticker="SCZM", exchange="NYSE")]

    result = build_us_screener_results(market_data, companies, tmp_path / "facts", companyfacts_zip=facts_zip)

    assert result.loc[0, "data_status"] == "error"
    assert result.loc[0, "data_note"] == "SEC companyfacts ZIP에 재무자료 없음"

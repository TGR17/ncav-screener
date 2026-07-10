import pandas as pd

from ncav_screener.us_reporting import build_us_app_report


def test_build_us_app_report_orders_columns_and_marks_normal_row() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "exchange": "Nasdaq",
                "market_cap": 300,
                "current_assets": 500,
                "total_liabilities": 300,
                "ncav": 200,
                "ncav_ratio": 1.5,
                "cash_and_equivalents": 80,
                "ebit_ttm": 50,
                "ev": 240,
                "ev_ebit": 4.8,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert list(report.columns[:3]) == ["ticker", "name", "exchange"]
    assert report.loc[0, "data_status"] == "정상"
    assert report.loc[0, "data_note"] == ""


def test_build_us_app_report_marks_missing_core_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "MISS",
                "name": "Missing Co",
                "market_cap": 100,
                "current_assets": pd.NA,
                "total_liabilities": 50,
                "cash_and_equivalents": pd.NA,
                "ebit_ttm": pd.NA,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "확인 필요"
    assert "SEC 유동자산 누락" in report.loc[0, "data_note"]
    assert "재무상태표 핵심값 누락: TTM EBIT 산출 불가" in report.loc[0, "data_note"]


def test_build_us_app_report_marks_negative_ttm_ebit_as_excluded() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "NEG",
                "name": "Negative EBIT Co",
                "market_cap": 300,
                "current_assets": 500,
                "total_liabilities": 300,
                "ncav": 200,
                "ncav_ratio": 1.5,
                "cash_and_equivalents": 80,
                "ebit_ttm": -50,
                "ev": 240,
                "ev_ebit": pd.NA,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "계산 제외 있음"
    assert report.loc[0, "data_note"] == "TTM EBIT이 음수"


def test_build_us_app_report_marks_missing_quarterly_report() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "FPI",
                "name": "Foreign Private Issuer",
                "market_cap": 300,
                "current_assets": 500,
                "total_liabilities": 300,
                "ncav": 200,
                "ncav_ratio": 1.5,
                "cash_and_equivalents": 80,
                "ebit_ttm": 50,
                "ev": 240,
                "ev_ebit": 4.8,
                "financial_statement_form": "20-F",
                "has_quarterly_financials": False,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "계산 제외 있음"
    assert "분기보고서 없음(20-F 연간보고서 기준)" in report.loc[0, "data_note"]


def test_build_us_app_report_marks_missing_ebit_due_to_missing_quarterly_report() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "FPI",
                "name": "Foreign Private Issuer",
                "market_cap": 300,
                "current_assets": 500,
                "total_liabilities": 300,
                "ncav": 200,
                "ncav_ratio": 1.5,
                "cash_and_equivalents": 80,
                "ebit_ttm": pd.NA,
                "ev": 240,
                "ev_ebit": pd.NA,
                "financial_statement_form": "20-F",
                "has_quarterly_financials": False,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "확인 필요"
    assert "분기보고서 없음(20-F 연간보고서 기준)" in report.loc[0, "data_note"]
    assert "분기보고서 없음: TTM EBIT 산출 불가" in report.loc[0, "data_note"]


def test_build_us_app_report_marks_missing_ebit_due_to_annual_income_gap() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "IPO",
                "name": "Recent IPO",
                "market_cap": 300,
                "current_assets": 500,
                "total_liabilities": 300,
                "ncav": 200,
                "ncav_ratio": 1.5,
                "cash_and_equivalents": 80,
                "ebit_ttm": pd.NA,
                "ebit_ttm_method": "missing annual operating income",
                "ev": 240,
                "ev_ebit": pd.NA,
                "has_quarterly_financials": True,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "확인 필요"
    assert "연간 손익 기준 부족: TTM EBIT 산출 불가" in report.loc[0, "data_note"]


def test_build_us_app_report_marks_missing_ebit_due_to_missing_tag() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "IFRS",
                "name": "IFRS Reporter",
                "market_cap": 300,
                "current_assets": 500,
                "total_liabilities": 300,
                "ncav": 200,
                "ncav_ratio": 1.5,
                "cash_and_equivalents": 80,
                "ebit_ttm": pd.NA,
                "ebit_ttm_method": "IFRS operating income tag missing",
                "ev": 240,
                "ev_ebit": pd.NA,
                "has_quarterly_financials": True,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "확인 필요"
    assert "EBIT 대응 항목 없음: 추정 EBIT 불가" in report.loc[0, "data_note"]


def test_build_us_app_report_marks_estimated_ebit() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "EST",
                "name": "Estimated EBIT Co",
                "market_cap": 300,
                "current_assets": 500,
                "total_liabilities": 300,
                "ncav": 200,
                "ncav_ratio": 1.5,
                "cash_and_equivalents": 80,
                "ebit_ttm": 50,
                "ebit_ttm_method": "estimated EBIT from pretax income + finance costs (ifrs-full)",
                "ev": 240,
                "ev_ebit": 4.8,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "확인 필요"
    assert "추정 EBIT 사용" in report.loc[0, "data_note"]


def test_build_us_app_report_collapses_non_usd_financial_statement_notes() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "CAD",
                "name": "CAD Reporter",
                "market_cap": 300,
                "financial_statement_currency": "CAD",
                "financial_statement_form": "40-F",
                "has_quarterly_financials": False,
                "current_assets": pd.NA,
                "total_liabilities": pd.NA,
                "cash_and_equivalents": pd.NA,
                "ebit_ttm": pd.NA,
                "ev": pd.NA,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "확인 필요"
    assert report.loc[0, "data_note"] == "비USD 재무제표"


def test_build_us_app_report_collapses_missing_companyfacts_statement_body() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "YMAT",
                "name": "J-Star Holding",
                "market_cap": 100,
                "financial_statement_currency": pd.NA,
                "financial_statement_form": pd.NA,
                "financial_statement_end": pd.NA,
                "current_assets": pd.NA,
                "total_liabilities": pd.NA,
                "cash_and_equivalents": pd.NA,
                "ebit_ttm": pd.NA,
                "ev": pd.NA,
                "data_status": "ok",
                "data_note": "",
            }
        ]
    )

    report = build_us_app_report(frame)

    assert report.loc[0, "data_status"] == "확인 필요"
    assert report.loc[0, "data_note"] == "SEC companyfacts 재무제표 본문 없음"

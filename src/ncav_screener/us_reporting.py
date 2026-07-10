from __future__ import annotations

from pathlib import Path

import pandas as pd


APP_COLUMNS = [
    "ticker",
    "name",
    "exchange",
    "sector",
    "industry",
    "country",
    "data_status",
    "data_note",
    "financial_taxonomy",
    "financial_statement_currency",
    "financial_statement_form",
    "financial_statement_end",
    "financial_statement_filed",
    "price",
    "volume",
    "market_cap",
    "shares_outstanding",
    "current_assets",
    "total_liabilities",
    "ncav",
    "ncav_per_share",
    "ncav_ratio",
    "cash_and_equivalents",
    "interest_bearing_debt",
    "other_financial_liabilities",
    "interest_bearing_debt_tags",
    "other_financial_liability_tags",
    "ebit_ttm",
    "ebit_ttm_method",
    "ebit_ttm_annual",
    "ebit_ttm_previous_ytd",
    "ebit_ttm_current_ytd",
    "ev",
    "ev_ebit",
    "conservative_ev",
    "conservative_ev_ebit",
    "cik",
    "cik10",
]


def add_us_data_notes(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    statuses = []
    notes = []

    for _, row in output.iterrows():
        row_notes = []
        has_missing = False

        if str(row.get("data_status", "")).lower() == "error":
            statuses.append("확인 필요")
            notes.append(str(row.get("data_note", "")))
            continue

        if pd.isna(row.get("market_cap")):
            has_missing = True
            row_notes.append("미국 시가총액 누락")
        currency = row.get("financial_statement_currency")
        is_non_usd = pd.notna(currency) and str(currency).upper() != "USD"
        if is_non_usd:
            has_missing = True
            row_notes.append("비USD 재무제표")
            statuses.append("확인 필요")
            notes.append(" | ".join(dict.fromkeys(row_notes)))
            continue
        if _has_no_structured_financial_statement(row):
            statuses.append("확인 필요")
            notes.append("SEC companyfacts 재무제표 본문 없음")
            continue
        if pd.isna(row.get("current_assets")):
            has_missing = True
            row_notes.append("SEC 유동자산 누락")
        if pd.isna(row.get("total_liabilities")):
            has_missing = True
            row_notes.append("SEC 부채총계 누락")
        if pd.isna(row.get("cash_and_equivalents")):
            has_missing = True
            row_notes.append("SEC 현금성자산 누락")
        has_quarterly = row.get("has_quarterly_financials")
        if has_quarterly is False or str(has_quarterly).lower() == "false":
            form = row.get("financial_statement_form")
            form_text = f"{form} " if pd.notna(form) else ""
            row_notes.append(f"분기보고서 없음({form_text}연간보고서 기준)")
        ebit_ttm = row.get("ebit_ttm")
        if pd.isna(ebit_ttm):
            has_missing = True
            row_notes.append(_missing_ebit_note(row, row_notes))
        elif ebit_ttm < 0:
            row_notes.append("TTM EBIT이 음수")
        elif "estimated EBIT" in str(row.get("ebit_ttm_method", "")):
            has_missing = True
            row_notes.append("추정 EBIT 사용")
        if pd.isna(row.get("ev")) and pd.notna(row.get("market_cap")):
            has_missing = True
            row_notes.append("EV 산출 데이터 누락")
        if pd.isna(row.get("ev_ebit")) and pd.notna(ebit_ttm) and ebit_ttm >= 0:
            has_missing = True
            row_notes.append("EV/EBIT 산출 데이터 누락")

        ncav = row.get("ncav")
        if pd.notna(ncav) and ncav <= 0:
            row_notes.append("NCAV가 0 이하")
        elif pd.isna(row.get("ncav_ratio")) and pd.notna(ncav):
            has_missing = True
            row_notes.append("NCAV 배율 산출 데이터 누락")

        if has_missing:
            statuses.append("확인 필요")
        elif row_notes:
            statuses.append("계산 제외 있음")
        else:
            statuses.append("정상")
        notes.append(" | ".join(dict.fromkeys(row_notes)) if row_notes else "")

    output["data_status"] = statuses
    output["data_note"] = notes
    return output


def _has_no_structured_financial_statement(row: pd.Series) -> bool:
    return (
        pd.isna(row.get("financial_statement_currency"))
        and pd.isna(row.get("financial_statement_form"))
        and pd.isna(row.get("financial_statement_end"))
        and pd.isna(row.get("current_assets"))
        and pd.isna(row.get("total_liabilities"))
        and pd.isna(row.get("cash_and_equivalents"))
    )


def _missing_ebit_note(row: pd.Series, row_notes: list[str]) -> str:
    note = str(row.get("data_note", ""))
    if "companyfacts ZIP에 재무자료 없음" in note:
        return "SEC companyfacts ZIP에 재무자료 없음"

    has_quarterly = row.get("has_quarterly_financials")
    if has_quarterly is False or str(has_quarterly).lower() == "false":
        return "분기보고서 없음: TTM EBIT 산출 불가"

    missing_balance_sheet_notes = {
        "SEC 유동자산 누락",
        "SEC 부채총계 누락",
        "SEC 현금성자산 누락",
    }
    if any(note in row_notes for note in missing_balance_sheet_notes):
        return "재무상태표 핵심값 누락: TTM EBIT 산출 불가"

    method = str(row.get("ebit_ttm_method", ""))
    if "missing annual operating income" in method:
        return "연간 손익 기준 부족: TTM EBIT 산출 불가"
    if "estimated EBIT unavailable" in method or "operating income tag missing" in method:
        return "EBIT 대응 항목 없음: 추정 EBIT 불가"

    return "SEC TTM EBIT 산출 데이터 누락"


def build_us_app_report(frame: pd.DataFrame) -> pd.DataFrame:
    report = add_us_data_notes(frame)
    ordered = [column for column in APP_COLUMNS if column in report.columns]
    remaining = [column for column in report.columns if column not in ordered]
    return report[ordered + remaining]


def save_us_app_report(input_path: Path, output_path: Path) -> pd.DataFrame:
    frame = pd.read_csv(input_path, dtype={"ticker": str, "cik10": str})
    report = build_us_app_report(frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False, encoding="utf-8-sig")
    return report

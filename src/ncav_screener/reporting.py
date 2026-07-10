from __future__ import annotations

from pathlib import Path

import pandas as pd


KOREAN_COLUMN_NAMES = {
    "ticker": "\uc885\ubaa9\ucf54\ub4dc",
    "name": "\uc885\ubaa9\uba85",
    "market": "\uc2dc\uc7a5",
    "industry_code": "\uc5c5\uc885\ucf54\ub4dc",
    "industry_name": "\uc5c5\uc885\uba85",
    "section": "\uc18c\uc18d\ubd80",
    "close": "\uc885\uac00",
    "volume": "\uac70\ub798\ub7c9",
    "trading_value": "\uac70\ub798\ub300\uae08",
    "market_cap": "\uc2dc\uac00\ucd1d\uc561",
    "shares_outstanding": "\uc0c1\uc7a5\uc8fc\uc2dd\uc218",
    "market_data_found": "KRX \uc2dc\uc138 \ub9e4\uce6d",
    "current_assets": "\uc720\ub3d9\uc790\uc0b0",
    "total_liabilities": "\ubd80\ucc44\ucd1d\uacc4",
    "ncav": "NCAV",
    "ncav_per_share": "\uc8fc\ub2f9 NCAV",
    "ncav_ratio": "NCAV \ubc30\uc728",
    "cash_and_equivalents": "\ud604\uae08\ubc0f\ud604\uae08\uc131\uc790\uc0b0",
    "interest_bearing_debt": "\uc774\uc790\ubc1c\uc0dd\ubd80\ucc44",
    "other_financial_liabilities": "\uae30\ud0c0\uae08\uc735\ubd80\ucc44",
    "operating_income_annual": "2025 \uc5f0\uac04 \uc601\uc5c5\uc774\uc775",
    "operating_income_previous_q1": "2025 1\ubd84\uae30 \uc601\uc5c5\uc774\uc775",
    "operating_income_current_q1": "2026 1\ubd84\uae30 \uc601\uc5c5\uc774\uc775",
    "ebit_ttm": "TTM EBIT",
    "ev": "EV",
    "ev_ebit": "EV/EBIT",
    "conservative_ev": "\ubcf4\uc218 EV",
    "conservative_ev_ebit": "\ubcf4\uc218 EV/EBIT",
    "fundamental_close": "\ud22c\uc790\uc9c0\ud45c \uae30\uc900 \uc885\uac00",
    "eps": "EPS",
    "per": "PER",
    "bps": "BPS",
    "pbr": "PBR",
    "dividend_per_share": "\uc8fc\ub2f9\ubc30\ub2f9\uae08",
    "dividend_yield": "\ubc30\ub2f9\uc218\uc775\ub960",
    "f_score": "F-score",
    "f_score_max": "F-score \ub9cc\uc810",
    "f_score_ratio": "F-score \ube44\uc728",
    "f_roa_positive": "F-score ROA \uc591\uc218",
    "f_cfo_positive": "F-score CFO \uc591\uc218",
    "f_roa_up": "F-score ROA \uac1c\uc120",
    "f_cfo_gt_net_income": "F-score CFO>\uc21c\uc774\uc775",
    "f_debt_ratio_down": "F-score \ubd80\ucc44\ube44\uc728 \uac1c\uc120",
    "f_current_ratio_up": "F-score \uc720\ub3d9\ube44\uc728 \uac1c\uc120",
    "f_gross_margin_up": "F-score \ub9e4\ucd9c\ucd1d\uc774\uc775\ub960 \uac1c\uc120",
    "f_asset_turnover_up": "F-score \uc790\uc0b0\ud68c\uc804\uc728 \uac1c\uc120",
    "roe_current": "ROE",
    "roa_current": "ROA",
    "roic_current": "ROIC",
    "invested_capital": "\ud22c\ud558\uc790\ubcf8",
    "operating_margin_current": "\uc601\uc5c5\uc774\uc775\ub960",
    "data_status": "\ub370\uc774\ud130 \uc0c1\ud0dc",
    "data_note": "\uacc4\uc0b0 \uc81c\uc678/\ub204\ub77d \uc0ac\uc720",
    "status": "\uc0c1\ud0dc",
    "error": "\uc624\ub958",
}

PREFERRED_COLUMN_ORDER = [
    "\uc885\ubaa9\ucf54\ub4dc",
    "\uc885\ubaa9\uba85",
    "\uc2dc\uc7a5",
    "\uc5c5\uc885\ucf54\ub4dc",
    "\uc5c5\uc885\uba85",
    "\ub370\uc774\ud130 \uc0c1\ud0dc",
    "\uacc4\uc0b0 \uc81c\uc678/\ub204\ub77d \uc0ac\uc720",
    "\uc18c\uc18d\ubd80",
    "KRX \uc2dc\uc138 \ub9e4\uce6d",
    "\uc885\uac00",
    "\uac70\ub798\ub7c9",
    "\uac70\ub798\ub300\uae08",
    "\uc2dc\uac00\ucd1d\uc561",
    "\uc0c1\uc7a5\uc8fc\uc2dd\uc218",
    "\uc720\ub3d9\uc790\uc0b0",
    "\ubd80\ucc44\ucd1d\uacc4",
    "NCAV",
    "\uc8fc\ub2f9 NCAV",
    "NCAV \ubc30\uc728",
    "\ud604\uae08\ubc0f\ud604\uae08\uc131\uc790\uc0b0",
    "\uc774\uc790\ubc1c\uc0dd\ubd80\ucc44",
    "\uae30\ud0c0\uae08\uc735\ubd80\ucc44",
    "2025 \uc5f0\uac04 \uc601\uc5c5\uc774\uc775",
    "2025 1\ubd84\uae30 \uc601\uc5c5\uc774\uc775",
    "2026 1\ubd84\uae30 \uc601\uc5c5\uc774\uc775",
    "TTM EBIT",
    "EV",
    "EV/EBIT",
    "\ubcf4\uc218 EV",
    "\ubcf4\uc218 EV/EBIT",
    "PER",
    "PBR",
    "F-score",
    "F-score \ub9cc\uc810",
    "F-score \ube44\uc728",
    "ROE",
    "ROA",
    "ROIC",
    "\uc601\uc5c5\uc774\uc775\ub960",
    "EPS",
    "BPS",
    "\ubc30\ub2f9\uc218\uc775\ub960",
    "\uc8fc\ub2f9\ubc30\ub2f9\uae08",
]


def add_data_notes(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    notes = []
    statuses = []

    for _, row in output.iterrows():
        row_notes = []
        has_missing = False

        market_cap = row.get("market_cap")
        market_data_found = row.get("market_data_found")
        ncav = row.get("ncav")
        ebit_ttm = row.get("ebit_ttm")
        ev = row.get("ev")
        per = row.get("per")
        operating_margin = row.get("operating_margin_current")

        if pd.isna(market_cap):
            has_missing = True
            if market_data_found is False or str(market_data_found).lower() == "false":
                row_notes.append("KRX 시세 파일에 종목코드 없음")
            else:
                row_notes.append("KRX 시가총액 값 누락")
        if pd.isna(ebit_ttm):
            has_missing = True
            row_notes.append("DART TTM EBIT 산출 데이터 누락")
        if pd.isna(ev) and pd.notna(ebit_ttm):
            has_missing = True
            row_notes.append("EV 산출 데이터 누락")

        if pd.notna(ncav) and ncav <= 0:
            row_notes.append("NCAV가 0 이하라 NCAV 배율 제외")
        elif pd.isna(row.get("ncav_ratio")) and pd.notna(ncav):
            has_missing = True
            row_notes.append("NCAV 배율 산출 데이터 누락")

        if pd.notna(ebit_ttm) and ebit_ttm < 0:
            row_notes.append("TTM EBIT이 음수")
        elif pd.notna(ebit_ttm) and ebit_ttm == 0:
            row_notes.append("TTM EBIT가 0이라 EV/EBIT 제외")
        elif pd.isna(row.get("ev_ebit")) and pd.notna(ebit_ttm):
            has_missing = True
            row_notes.append("EV/EBIT 산출 데이터 누락")

        if pd.isna(per):
            row_notes.append("KRX PER 미제공")
        if pd.isna(operating_margin):
            row_notes.append("매출액 또는 영업이익률 산출 데이터 누락")

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


def save_korean_report(input_path: Path, output_path: Path) -> pd.DataFrame:
    frame = pd.read_csv(input_path, dtype={"ticker": str})
    frame = add_data_notes(frame)
    report = frame.rename(columns=KOREAN_COLUMN_NAMES)

    ordered = [column for column in PREFERRED_COLUMN_ORDER if column in report.columns]
    remaining = [column for column in report.columns if column not in ordered]
    report = report[ordered + remaining]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False, encoding="utf-8-sig")
    return report

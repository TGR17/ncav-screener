from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from .dart_bulk import (
    ACCOUNT_CODE_COLUMN,
    ANNUAL_CURRENT_PERIOD_COLUMN,
    COMPANY_NAME_COLUMN,
    CURRENT_ASSETS_CODE,
    CURRENT_PERIOD_COLUMN,
    DEBT_CODES,
    OPERATING_INCOME_CODE,
    Q1_CUMULATIVE_COLUMN,
    STOCK_CODE_COLUMN,
    parse_amount,
    read_dart_bulk_statement,
)


ASSETS_CODE = "ifrs-full_Assets"
EQUITY_CODE = "ifrs-full_Equity"
CURRENT_LIABILITIES_CODE = "ifrs-full_CurrentLiabilities"
NET_INCOME_CODE = "ifrs-full_ProfitLoss"
REVENUE_CODE = "ifrs-full_Revenue"
GROSS_PROFIT_CODE = "ifrs-full_GrossProfit"
CFO_CODE = "ifrs-full_CashFlowsFromUsedInOperatingActivities"
CF_Q1_COLUMN = "\ub2f9\uae301\ubd84\uae30"


def build_f_score_from_bulk(
    *,
    current_balance_sheet_path: Path,
    previous_balance_sheet_path: Path,
    annual_income_path: Path | Sequence[Path],
    current_income_path: Path | Sequence[Path],
    previous_income_path: Path | Sequence[Path],
    current_cash_flow_path: Path,
    previous_cash_flow_path: Path,
) -> pd.DataFrame:
    current_bs = _build_statement_values(
        current_balance_sheet_path,
        CURRENT_PERIOD_COLUMN,
        {
            ASSETS_CODE,
            EQUITY_CODE,
            CURRENT_ASSETS_CODE,
            CURRENT_LIABILITIES_CODE,
            *DEBT_CODES,
        },
    )
    previous_bs = _build_statement_values(
        previous_balance_sheet_path,
        CURRENT_PERIOD_COLUMN,
        {
            ASSETS_CODE,
            EQUITY_CODE,
            CURRENT_ASSETS_CODE,
            CURRENT_LIABILITIES_CODE,
            *DEBT_CODES,
        },
    )
    current_income = _build_statement_values_with_fallback(
        current_income_path,
        Q1_CUMULATIVE_COLUMN,
        {NET_INCOME_CODE, REVENUE_CODE, GROSS_PROFIT_CODE, OPERATING_INCOME_CODE},
    )
    previous_income = _build_statement_values_with_fallback(
        previous_income_path,
        Q1_CUMULATIVE_COLUMN,
        {NET_INCOME_CODE, REVENUE_CODE, GROSS_PROFIT_CODE, OPERATING_INCOME_CODE},
    )
    annual_income = _build_statement_values_with_fallback(
        annual_income_path,
        ANNUAL_CURRENT_PERIOD_COLUMN,
        {NET_INCOME_CODE},
    )
    current_cf = _build_statement_values(
        current_cash_flow_path,
        (Q1_CUMULATIVE_COLUMN, CF_Q1_COLUMN),
        {CFO_CODE},
    )
    previous_cf = _build_statement_values(
        previous_cash_flow_path,
        (Q1_CUMULATIVE_COLUMN, CF_Q1_COLUMN),
        {CFO_CODE},
    )

    current = _combine_period(current_bs, current_income, current_cf, "current")
    previous = _combine_period(previous_bs, previous_income, previous_cf, "previous")
    output = current.merge(previous, on="ticker", how="outer", suffixes=("", "_previous_name"))
    annual = annual_income.rename(columns={NET_INCOME_CODE: "net_income_annual"})
    output = output.merge(annual[["ticker", "net_income_annual"]], on="ticker", how="left")

    output["net_income_ttm"] = (
        output["net_income_annual"]
        - output["net_income_previous"]
        + output["net_income_current"]
    )
    output["average_assets_ttm"] = (output["assets_current"] + output["assets_previous"]) / 2
    output["average_equity_ttm"] = (output["equity_current"] + output["equity_previous"]) / 2
    output["average_debt_ttm"] = (output["debt_current"] + output["debt_previous"]) / 2
    output["roa_quarter_current"] = _safe_divide(output["net_income_current"], output["assets_current"])
    output["roa_previous"] = _safe_divide(output["net_income_previous"], output["assets_previous"])
    output["roe_quarter_current"] = _safe_divide(output["net_income_current"], output["equity_current"])
    output["roe_previous"] = _safe_divide(output["net_income_previous"], output["equity_previous"])
    output["roa_current"] = _safe_divide(output["net_income_ttm"], output["average_assets_ttm"])
    output["roe_current"] = _safe_divide(output["net_income_ttm"], output["average_equity_ttm"])
    output["operating_margin_current"] = _safe_divide(
        output["operating_income_current"],
        output["revenue_current"],
    )
    output["operating_margin_previous"] = _safe_divide(
        output["operating_income_previous"],
        output["revenue_previous"],
    )
    output["debt_ratio_current"] = _safe_divide(output["debt_current"], output["assets_current"])
    output["debt_ratio_previous"] = _safe_divide(output["debt_previous"], output["assets_previous"])
    output["current_ratio_current"] = _safe_divide(
        output["current_assets_current"],
        output["current_liabilities_current"],
    )
    output["current_ratio_previous"] = _safe_divide(
        output["current_assets_previous"],
        output["current_liabilities_previous"],
    )
    output["gross_margin_current"] = _safe_divide(
        output["gross_profit_current"],
        output["revenue_current"],
    )
    output["gross_margin_previous"] = _safe_divide(
        output["gross_profit_previous"],
        output["revenue_previous"],
    )
    output["asset_turnover_current"] = _safe_divide(
        output["revenue_current"],
        output["assets_current"],
    )
    output["asset_turnover_previous"] = _safe_divide(
        output["revenue_previous"],
        output["assets_previous"],
    )

    criteria = {
        "f_roa_positive": _criterion(output["roa_quarter_current"] > 0, output["roa_quarter_current"]),
        "f_cfo_positive": _criterion(output["cfo_current"] > 0, output["cfo_current"]),
        "f_roa_up": _criterion(
            output["roa_quarter_current"] > output["roa_previous"],
            output["roa_quarter_current"],
            output["roa_previous"],
        ),
        "f_cfo_gt_net_income": _criterion(
            output["cfo_current"] > output["net_income_current"],
            output["cfo_current"],
            output["net_income_current"],
        ),
        "f_debt_ratio_down": _criterion(
            output["debt_ratio_current"] < output["debt_ratio_previous"],
            output["debt_ratio_current"],
            output["debt_ratio_previous"],
        ),
        "f_current_ratio_up": _criterion(
            output["current_ratio_current"] > output["current_ratio_previous"],
            output["current_ratio_current"],
            output["current_ratio_previous"],
        ),
        "f_gross_margin_up": _criterion(
            output["gross_margin_current"] > output["gross_margin_previous"],
            output["gross_margin_current"],
            output["gross_margin_previous"],
        ),
        "f_asset_turnover_up": _criterion(
            output["asset_turnover_current"] > output["asset_turnover_previous"],
            output["asset_turnover_current"],
            output["asset_turnover_previous"],
        ),
    }
    for column, values in criteria.items():
        output[column] = values.where(values.notna(), pd.NA).astype("Int64")

    criterion_columns = list(criteria)
    output["f_score_max"] = output[criterion_columns].notna().sum(axis=1)
    output["f_score"] = output[criterion_columns].fillna(0).sum(axis=1).astype("Int64")
    output["f_score_ratio"] = output["f_score"] / output["f_score_max"]
    output.loc[output["f_score_max"] == 0, "f_score_ratio"] = pd.NA

    columns = [
        "ticker",
        "f_score",
        "f_score_max",
        "f_score_ratio",
        *criterion_columns,
        "roa_current",
        "roa_quarter_current",
        "roa_previous",
        "roe_current",
        "roe_quarter_current",
        "roe_previous",
        "operating_margin_current",
        "operating_margin_previous",
        "operating_income_current",
        "revenue_current",
        "net_income_annual",
        "net_income_ttm",
        "average_assets_ttm",
        "average_equity_ttm",
        "average_debt_ttm",
        "cfo_current",
        "net_income_current",
        "debt_ratio_current",
        "debt_ratio_previous",
        "current_ratio_current",
        "current_ratio_previous",
        "gross_margin_current",
        "gross_margin_previous",
        "asset_turnover_current",
        "asset_turnover_previous",
    ]
    return output[columns]


def merge_f_score(results: pd.DataFrame, f_score: pd.DataFrame) -> pd.DataFrame:
    output = results.copy()
    output["ticker"] = output["ticker"].astype(str).str.zfill(6)
    scores = f_score.copy()
    scores["ticker"] = scores["ticker"].astype(str).str.zfill(6)
    output = output.merge(scores, on="ticker", how="left")
    output["invested_capital"] = (
        output["average_equity_ttm"]
        + output["average_debt_ttm"].fillna(0)
        - output["cash_and_equivalents"].fillna(0)
    )
    output["roic_current"] = _safe_divide(output["ebit_ttm"], output["invested_capital"])
    output.loc[output["invested_capital"] <= 0, "roic_current"] = pd.NA
    return output


def _build_statement_values(path: Path, value_column: str | tuple[str, ...], account_codes: set[str]) -> pd.DataFrame:
    raw = read_dart_bulk_statement(path)
    value_column_name = _resolve_value_column(raw, value_column)
    required = {STOCK_CODE_COLUMN, COMPANY_NAME_COLUMN, ACCOUNT_CODE_COLUMN, value_column_name}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"DART bulk file is missing columns: {sorted(missing)}")

    frame = raw.loc[raw[ACCOUNT_CODE_COLUMN].isin(account_codes)].copy()
    frame["ticker"] = frame[STOCK_CODE_COLUMN].str.replace(r"[\[\]]", "", regex=True).str.zfill(6)
    frame["amount"] = frame[value_column_name].map(parse_amount)

    base = frame[["ticker", COMPANY_NAME_COLUMN]].drop_duplicates("ticker")
    pivot = frame.pivot_table(
        index="ticker",
        columns=ACCOUNT_CODE_COLUMN,
        values="amount",
        aggfunc="first",
    )
    return base.set_index("ticker").join(pivot, how="left").reset_index()


def _build_statement_values_with_fallback(
    paths: Path | Sequence[Path],
    value_column: str | tuple[str, ...],
    account_codes: set[str],
) -> pd.DataFrame:
    if isinstance(paths, (str, Path)):
        path_list = [Path(paths)]
    else:
        path_list = [Path(path) for path in paths]

    frames = []
    for priority, path in enumerate(path_list):
        frame = _build_statement_values(path, value_column, account_codes).copy()
        frame["source_priority"] = priority
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["ticker", COMPANY_NAME_COLUMN])

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["ticker", "source_priority"])
    combined = combined.drop_duplicates("ticker", keep="first")
    return combined.drop(columns=["source_priority"])


def _combine_period(
    balance_sheet: pd.DataFrame,
    income: pd.DataFrame,
    cash_flow: pd.DataFrame,
    suffix: str,
) -> pd.DataFrame:
    output = balance_sheet.merge(income.drop(columns=[COMPANY_NAME_COLUMN], errors="ignore"), on="ticker", how="outer")
    output = output.merge(cash_flow.drop(columns=[COMPANY_NAME_COLUMN], errors="ignore"), on="ticker", how="outer")

    debt_columns = [column for column in DEBT_CODES if column in output.columns]
    if debt_columns:
        output["debt"] = output[debt_columns].fillna(0).sum(axis=1)
    else:
        output["debt"] = pd.NA

    output = output.rename(
        columns={
            ASSETS_CODE: "assets",
            EQUITY_CODE: "equity",
            CURRENT_ASSETS_CODE: "current_assets",
            CURRENT_LIABILITIES_CODE: "current_liabilities",
            NET_INCOME_CODE: "net_income",
            REVENUE_CODE: "revenue",
            GROSS_PROFIT_CODE: "gross_profit",
            OPERATING_INCOME_CODE: "operating_income",
            CFO_CODE: "cfo",
        }
    )

    keep = [
        "ticker",
        "assets",
        "equity",
        "current_assets",
        "current_liabilities",
        "debt",
        "net_income",
        "revenue",
        "gross_profit",
        "operating_income",
        "cfo",
    ]
    output = output[[column for column in keep if column in output.columns]]
    rename = {column: f"{column}_{suffix}" for column in output.columns if column != "ticker"}
    return output.rename(columns=rename)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator / denominator
    result = result.where(denominator != 0, pd.NA)
    return result


def _resolve_value_column(raw: pd.DataFrame, value_column: str | tuple[str, ...]) -> str:
    if isinstance(value_column, str):
        return value_column
    for column in value_column:
        if column in raw.columns:
            return column
    return value_column[0]


def _criterion(condition: pd.Series, *required_values: pd.Series) -> pd.Series:
    available = pd.Series(True, index=condition.index)
    for value in required_values:
        available = available & value.notna()
    return condition.where(available, pd.NA)

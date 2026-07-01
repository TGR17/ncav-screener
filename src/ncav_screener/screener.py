from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from time import sleep

import pandas as pd

from .config import CORP_CODE_ZIP
from .dart_client import DartClient
from .financials import (
    extract_interest_bearing_debt,
    extract_standard_accounts,
)
from .mapper import find_corp_by_stock_code, parse_corp_code_zip
from .market_data import filter_screening_universe, load_market_data
from .metrics import EvEbitInputs, NcavInputs, calculate_basic_ncav, calculate_ev_ebit_metrics


@dataclass(frozen=True)
class SingleStockResult:
    ticker: str
    corp_code: str
    corp_name: str
    market_cap: float
    shares_outstanding: float
    current_assets: float
    total_liabilities: float
    ncav: float
    ncav_per_share: float | None
    ncav_ratio: float | None
    cash_and_equivalents: float
    interest_bearing_debt: float
    ebit_ttm: float | None
    ev: float | None
    ev_ebit: float | None


def calculate_company_metrics(
    *,
    current_assets: float,
    total_liabilities: float,
    market_cap: float,
    shares_outstanding: float | None = None,
    cash_and_equivalents: float | None = None,
    interest_bearing_debt: float | None = None,
    ebit_ttm: float | None = None,
) -> dict[str, float | None]:
    result = calculate_basic_ncav(
        NcavInputs(
            current_assets=current_assets,
            total_liabilities=total_liabilities,
            market_cap=market_cap,
            shares_outstanding=shares_outstanding,
        )
    )

    if (
        cash_and_equivalents is not None
        and interest_bearing_debt is not None
        and ebit_ttm is not None
    ):
        result.update(
            calculate_ev_ebit_metrics(
                EvEbitInputs(
                    market_cap=market_cap,
                    interest_bearing_debt=interest_bearing_debt,
                    cash_and_equivalents=cash_and_equivalents,
                    ebit_ttm=ebit_ttm,
                )
            )
        )

    return result


def screen_single_stock_from_dart(
    *,
    ticker: str,
    corp_code: str,
    corp_name: str,
    dart_client: DartClient,
    market_cap: float,
    shares_outstanding: float,
    business_year: int,
    report_code: str = "11011",
    ttm_next_year: int | None = None,
) -> SingleStockResult:
    payload, _ = dart_client.get_financial_statement_with_fallback(
        corp_code=corp_code,
        business_year=business_year,
        report_code=report_code,
    )
    rows = payload.get("list", [])
    accounts = extract_standard_accounts(rows)
    missing = [key for key in ("current_assets", "total_liabilities", "cash_and_equivalents") if accounts[key] is None]
    if missing:
        raise RuntimeError(f"Missing required DART accounts for {ticker}: {missing}")

    interest_bearing_debt, _ = extract_interest_bearing_debt(rows)
    ebit_ttm = None
    if ttm_next_year is not None:
        ebit_ttm = estimate_q1_ttm_operating_income(
            dart_client=dart_client,
            corp_code=corp_code,
            annual_year=business_year,
            next_year=ttm_next_year,
        )

    metrics = calculate_company_metrics(
        current_assets=accounts["current_assets"],
        total_liabilities=accounts["total_liabilities"],
        market_cap=market_cap,
        shares_outstanding=shares_outstanding,
        cash_and_equivalents=accounts["cash_and_equivalents"],
        interest_bearing_debt=interest_bearing_debt,
        ebit_ttm=ebit_ttm,
    )

    return SingleStockResult(
        ticker=ticker,
        corp_code=corp_code,
        corp_name=corp_name,
        market_cap=market_cap,
        shares_outstanding=shares_outstanding,
        current_assets=accounts["current_assets"],
        total_liabilities=accounts["total_liabilities"],
        ncav=metrics["ncav"],
        ncav_per_share=metrics["ncav_per_share"],
        ncav_ratio=metrics["ncav_ratio"],
        cash_and_equivalents=accounts["cash_and_equivalents"],
        interest_bearing_debt=interest_bearing_debt,
        ebit_ttm=ebit_ttm,
        ev=metrics.get("ev"),
        ev_ebit=metrics.get("ev_ebit"),
    )


def estimate_q1_ttm_operating_income(
    *,
    dart_client: DartClient,
    corp_code: str,
    annual_year: int,
    next_year: int,
) -> float:
    annual = get_operating_income(dart_client, corp_code, annual_year, "11011")
    previous_q1 = get_operating_income(dart_client, corp_code, annual_year, "11013")
    next_q1 = get_operating_income(dart_client, corp_code, next_year, "11013")
    return annual - previous_q1 + next_q1


def get_operating_income(
    dart_client: DartClient,
    corp_code: str,
    business_year: int,
    report_code: str,
) -> float:
    payload, _ = dart_client.get_financial_statement_with_fallback(
        corp_code=corp_code,
        business_year=business_year,
        report_code=report_code,
    )
    value = extract_standard_accounts(payload.get("list", []))["operating_income"]
    if value is None:
        raise RuntimeError(f"Missing operating income: {business_year} {report_code}")
    return value


def screen_market_data_file(
    *,
    dart_client: DartClient,
    market_data_path: Path,
    output_path: Path,
    business_year: int,
    ttm_next_year: int | None = None,
    limit: int | None = None,
    request_delay_seconds: float = 0.0,
    apply_default_filters: bool = True,
) -> pd.DataFrame:
    if not CORP_CODE_ZIP.exists():
        dart_client.download_corp_code_zip(CORP_CODE_ZIP)

    corp_codes = parse_corp_code_zip(CORP_CODE_ZIP)
    market_data = load_market_data(market_data_path)
    if apply_default_filters:
        market_data = filter_screening_universe(market_data)
    if limit is not None:
        market_data = market_data.head(limit)

    rows = []
    for market_row in market_data.itertuples(index=False):
        ticker = str(market_row.ticker).zfill(6)
        try:
            corp = find_corp_by_stock_code(corp_codes, ticker)
            result = screen_single_stock_from_dart(
                ticker=ticker,
                corp_code=corp["corp_code"],
                corp_name=corp["corp_name"],
                dart_client=dart_client,
                market_cap=float(market_row.market_cap),
                shares_outstanding=float(market_row.shares_outstanding),
                business_year=business_year,
                ttm_next_year=ttm_next_year,
            )
            rows.append(
                {
                    "ticker": result.ticker,
                    "name": result.corp_name,
                    "market": getattr(market_row, "market", ""),
                    "market_cap": result.market_cap,
                    "shares_outstanding": result.shares_outstanding,
                    "current_assets": result.current_assets,
                    "total_liabilities": result.total_liabilities,
                    "ncav": result.ncav,
                    "ncav_per_share": result.ncav_per_share,
                    "ncav_ratio": result.ncav_ratio,
                    "cash_and_equivalents": result.cash_and_equivalents,
                    "interest_bearing_debt": result.interest_bearing_debt,
                    "ebit_ttm": result.ebit_ttm,
                    "ev": result.ev,
                    "ev_ebit": result.ev_ebit,
                    "status": "ok",
                    "error": "",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "ticker": ticker,
                    "name": getattr(market_row, "name", ""),
                    "market": getattr(market_row, "market", ""),
                    "market_cap": getattr(market_row, "market_cap", None),
                    "shares_outstanding": getattr(market_row, "shares_outstanding", None),
                    "status": "error",
                    "error": sanitize_error_message(str(exc)),
                }
            )
        if request_delay_seconds > 0:
            sleep(request_delay_seconds)

    output = pd.DataFrame(rows)
    if "ncav_ratio" in output.columns:
        output = output.sort_values(["status", "ncav_ratio"], na_position="last")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output


def save_ncav_candidates(
    results: pd.DataFrame,
    output_path: Path,
    max_ratio: float = 1.0,
) -> pd.DataFrame:
    if "ncav_ratio" not in results.columns:
        candidates = results.head(0).copy()
    else:
        candidates = results.loc[
            (results["status"] == "ok")
            & (results["ncav_ratio"].notna())
            & (results["ncav_ratio"] <= max_ratio)
        ].copy()
        candidates = candidates.sort_values("ncav_ratio", na_position="last")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output_path, index=False, encoding="utf-8-sig")
    return candidates


def save_value_candidates(
    results: pd.DataFrame,
    output_path: Path,
    max_ncav_ratio: float = 1.0,
    max_ev_ebit: float = 10.0,
) -> pd.DataFrame:
    required = {"status", "ncav_ratio", "ebit_ttm", "ev_ebit"}
    if not required.issubset(results.columns):
        candidates = results.head(0).copy()
    else:
        candidates = results.loc[
            (results["status"] == "ok")
            & (results["ncav_ratio"].notna())
            & (results["ncav_ratio"] <= max_ncav_ratio)
            & (results["ebit_ttm"].notna())
            & (results["ebit_ttm"] > 0)
            & (results["ev_ebit"].notna())
            & (results["ev_ebit"] > 0)
            & (results["ev_ebit"] <= max_ev_ebit)
        ].copy()
        candidates = candidates.sort_values(["ncav_ratio", "ev_ebit"], na_position="last")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output_path, index=False, encoding="utf-8-sig")
    return candidates


def sanitize_error_message(message: str) -> str:
    return re.sub(r"crtfc_key=[^&\s]+", "crtfc_key=<hidden>", message)

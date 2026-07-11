from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NcavInputs:
    current_assets: float
    total_liabilities: float
    market_cap: float
    shares_outstanding: float | None = None


@dataclass(frozen=True)
class EvEbitInputs:
    market_cap: float
    interest_bearing_debt: float
    cash_and_equivalents: float
    ebit_ttm: float


def calculate_ncav(current_assets: float, total_liabilities: float) -> float:
    return current_assets - total_liabilities


def calculate_ncav_per_share(ncav: float, shares_outstanding: float) -> float:
    if shares_outstanding <= 0:
        raise ValueError("shares_outstanding must be positive")
    return ncav / shares_outstanding


def calculate_ncav_ratio(market_cap: float, ncav: float) -> float | None:
    if ncav <= 0:
        return None
    return market_cap / ncav


def calculate_ev(
    market_cap: float,
    interest_bearing_debt: float,
    cash_and_equivalents: float,
) -> float:
    return market_cap + interest_bearing_debt - cash_and_equivalents


def calculate_ev_ebit(ev: float, ebit_ttm: float) -> float | None:
    if ebit_ttm == 0:
        return None
    return ev / ebit_ttm


def calculate_basic_ncav(inputs: NcavInputs) -> dict[str, float | None]:
    ncav = calculate_ncav(inputs.current_assets, inputs.total_liabilities)
    ncav_per_share = None
    if inputs.shares_outstanding is not None:
        ncav_per_share = calculate_ncav_per_share(ncav, inputs.shares_outstanding)

    return {
        "ncav": ncav,
        "ncav_per_share": ncav_per_share,
        "ncav_ratio": calculate_ncav_ratio(inputs.market_cap, ncav),
    }


def calculate_ev_ebit_metrics(inputs: EvEbitInputs) -> dict[str, float | None]:
    ev = calculate_ev(
        market_cap=inputs.market_cap,
        interest_bearing_debt=inputs.interest_bearing_debt,
        cash_and_equivalents=inputs.cash_and_equivalents,
    )
    return {
        "ev": ev,
        "ev_ebit": calculate_ev_ebit(ev, inputs.ebit_ttm),
    }

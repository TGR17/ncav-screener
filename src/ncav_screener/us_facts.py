from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


CURRENT_ASSETS_TAGS = ("AssetsCurrent",)
TOTAL_LIABILITIES_TAGS = ("Liabilities",)
LIABILITY_COMPONENT_TAGS = ("LiabilitiesCurrent", "LiabilitiesNoncurrent")
CASH_TAGS = (
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
)
OPERATING_INCOME_TAGS = ("OperatingIncomeLoss",)
PRETAX_INCOME_TAGS = (
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
)
FINANCE_COST_TAGS = (
    "InterestExpenseNonOperating",
    "InterestExpense",
    "InterestAndDebtExpense",
)
DEBT_TAGS = (
    "ShortTermBorrowings",
    "ShortTermDebtCurrent",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebtAndFinanceLeaseObligationsCurrent",
    "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
    "FinanceLeaseLiabilityCurrent",
    "FinanceLeaseLiabilityNoncurrent",
)
OTHER_FINANCIAL_LIABILITY_TAGS = (
    "OperatingLeaseLiabilityCurrent",
    "OperatingLeaseLiabilityNoncurrent",
    "OperatingLeaseLiabilities",
    "DerivativeLiabilitiesCurrent",
    "DerivativeLiabilitiesNoncurrent",
    "DerivativeLiabilities",
)
IFRS_CURRENT_ASSETS_TAGS = ("CurrentAssets",)
IFRS_TOTAL_LIABILITIES_TAGS = ("Liabilities",)
IFRS_CASH_TAGS = ("CashAndCashEquivalents", "Cash")
IFRS_OPERATING_INCOME_TAGS = (
    "OperatingProfitLoss",
    "OperatingProfit",
    "ProfitLossFromOperatingActivities",
)
IFRS_PRETAX_INCOME_TAGS = (
    "ProfitLossBeforeTax",
    "ProfitLossFromContinuingOperationsBeforeTax",
    "AccountingProfit",
)
IFRS_NET_INCOME_TAGS = (
    "ProfitLoss",
    "ProfitLossAttributableToOwnersOfParent",
)
IFRS_INCOME_TAX_TAGS = (
    "IncomeTaxExpenseContinuingOperations",
    "IncomeTaxExpenseIncome",
    "TaxExpenseIncome",
)
IFRS_FINANCE_COST_TAGS = (
    "FinanceCosts",
    "FinanceCost",
    "AdjustmentsForFinanceCosts",
    "InterestExpense",
    "InterestExpenseOnBorrowings",
)
IFRS_DEBT_TAG_GROUPS = (
    ("Borrowings", "CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings", "CurrentPortionOfLongtermBorrowings", "NoncurrentBorrowings"),
    ("LeaseLiabilities", "CurrentLeaseLiabilities", "NoncurrentLeaseLiabilities"),
)


@dataclass(frozen=True)
class UsFactValue:
    tag: str
    value: float
    end: str
    form: str | None = None
    filed: str | None = None
    frame: str | None = None


@dataclass(frozen=True)
class UsFactPeriod(UsFactValue):
    start: str | None = None
    fy: int | None = None
    fp: str | None = None

    @property
    def end_date(self) -> date:
        return date.fromisoformat(self.end)

    @property
    def filed_date(self) -> date | None:
        if self.filed is None:
            return None
        return date.fromisoformat(self.filed)

    @property
    def duration_days(self) -> int | None:
        if self.start is None:
            return None
        return (self.end_date - date.fromisoformat(self.start)).days + 1


def build_us_financial_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    facts = payload.get("facts", {})
    if isinstance(facts, dict) and "ifrs-full" in facts and not _has_core_us_gaap_facts(payload):
        return build_ifrs_financial_snapshot(payload)

    report = _financial_report_metadata(payload, CURRENT_ASSETS_TAGS + TOTAL_LIABILITIES_TAGS + CASH_TAGS, taxonomy="us-gaap")
    current_assets = latest_usd_value(payload, CURRENT_ASSETS_TAGS)
    total_liabilities = latest_usd_value(payload, TOTAL_LIABILITIES_TAGS) or _sum_latest_values_same_end(
        payload,
        LIABILITY_COMPONENT_TAGS,
        taxonomy="us-gaap",
        tag_label="LiabilitiesCurrent + LiabilitiesNoncurrent",
    )
    cash = latest_usd_value(payload, CASH_TAGS)
    operating_income = latest_usd_value(payload, OPERATING_INCOME_TAGS)
    ebit_ttm = calculate_ttm_operating_income(payload)
    debt_components = [value for tag in DEBT_TAGS if (value := latest_usd_value(payload, (tag,))) is not None]
    other_financial_liability_components = [
        value for tag in OTHER_FINANCIAL_LIABILITY_TAGS if (value := latest_usd_value(payload, (tag,))) is not None
    ]

    interest_bearing_debt = sum(value.value for value in debt_components) if debt_components else 0.0
    other_financial_liabilities = (
        sum(value.value for value in other_financial_liability_components)
        if other_financial_liability_components
        else 0.0
    )
    ncav = None
    if current_assets is not None and total_liabilities is not None:
        ncav = current_assets.value - total_liabilities.value

    return {
        "financial_taxonomy": "us-gaap",
        **report,
        "current_assets": current_assets.value if current_assets else None,
        "current_assets_tag": current_assets.tag if current_assets else None,
        "total_liabilities": total_liabilities.value if total_liabilities else None,
        "total_liabilities_tag": total_liabilities.tag if total_liabilities else None,
        "cash_and_equivalents": cash.value if cash else None,
        "cash_and_equivalents_tag": cash.tag if cash else None,
        "operating_income_latest": operating_income.value if operating_income else None,
        "operating_income_latest_tag": operating_income.tag if operating_income else None,
        "operating_income_latest_end": operating_income.end if operating_income else None,
        "ebit_ttm": ebit_ttm["ebit_ttm"],
        "ebit_ttm_method": ebit_ttm["method"],
        "ebit_ttm_annual": ebit_ttm["annual"],
        "ebit_ttm_previous_ytd": ebit_ttm["previous_ytd"],
        "ebit_ttm_current_ytd": ebit_ttm["current_ytd"],
        "interest_bearing_debt": interest_bearing_debt,
        "interest_bearing_debt_tags": ", ".join(value.tag for value in debt_components),
        "other_financial_liabilities": other_financial_liabilities,
        "other_financial_liability_tags": ", ".join(value.tag for value in other_financial_liability_components),
        "ncav": ncav,
    }


def build_ifrs_financial_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    report = _financial_report_metadata(
        payload,
        IFRS_CURRENT_ASSETS_TAGS + IFRS_TOTAL_LIABILITIES_TAGS + IFRS_CASH_TAGS,
        taxonomy="ifrs-full",
    )
    current_assets = latest_usd_value(payload, IFRS_CURRENT_ASSETS_TAGS, taxonomy="ifrs-full")
    total_liabilities = latest_usd_value(payload, IFRS_TOTAL_LIABILITIES_TAGS, taxonomy="ifrs-full")
    cash = latest_usd_value(payload, IFRS_CASH_TAGS, taxonomy="ifrs-full")
    operating_income = latest_usd_value(payload, IFRS_OPERATING_INCOME_TAGS, taxonomy="ifrs-full")
    ebit_ttm = calculate_ttm_ifrs_operating_income(payload)
    debt_components = _ifrs_debt_components(payload)

    interest_bearing_debt = sum(value.value for value in debt_components) if debt_components else 0.0
    ncav = None
    if current_assets is not None and total_liabilities is not None:
        ncav = current_assets.value - total_liabilities.value

    return {
        "financial_taxonomy": "ifrs-full",
        **report,
        "current_assets": current_assets.value if current_assets else None,
        "current_assets_tag": current_assets.tag if current_assets else None,
        "total_liabilities": total_liabilities.value if total_liabilities else None,
        "total_liabilities_tag": total_liabilities.tag if total_liabilities else None,
        "cash_and_equivalents": cash.value if cash else None,
        "cash_and_equivalents_tag": cash.tag if cash else None,
        "operating_income_latest": operating_income.value if operating_income else None,
        "operating_income_latest_tag": operating_income.tag if operating_income else None,
        "operating_income_latest_end": operating_income.end if operating_income else None,
        "ebit_ttm": ebit_ttm["ebit_ttm"],
        "ebit_ttm_method": ebit_ttm["method"],
        "ebit_ttm_annual": ebit_ttm["annual"],
        "ebit_ttm_previous_ytd": ebit_ttm["previous_ytd"],
        "ebit_ttm_current_ytd": ebit_ttm["current_ytd"],
        "interest_bearing_debt": interest_bearing_debt,
        "interest_bearing_debt_tags": ", ".join(value.tag for value in debt_components),
        "other_financial_liabilities": 0.0,
        "other_financial_liability_tags": "",
        "ncav": ncav,
    }


def add_us_market_metrics(
    snapshot: dict[str, Any],
    *,
    market_cap: float,
    shares_outstanding: float | None = None,
) -> dict[str, Any]:
    output = dict(snapshot)
    output["market_cap"] = market_cap
    output["shares_outstanding"] = shares_outstanding

    ncav = output.get("ncav")
    cash = output.get("cash_and_equivalents")
    debt = output.get("interest_bearing_debt")
    other_financial_liabilities = output.get("other_financial_liabilities")
    ebit_ttm = output.get("ebit_ttm")

    output["ncav_ratio"] = market_cap / ncav if ncav not in (None, 0) else None
    output["ncav_per_share"] = (
        ncav / shares_outstanding
        if ncav is not None and shares_outstanding is not None and shares_outstanding > 0
        else None
    )
    output["ev"] = market_cap + (debt or 0) - (cash or 0) if cash is not None else None
    output["ev_ebit"] = (
        output["ev"] / ebit_ttm
        if output["ev"] is not None and ebit_ttm is not None and ebit_ttm > 0
        else None
    )
    output["conservative_ev"] = (
        output["ev"] + (other_financial_liabilities or 0)
        if output["ev"] is not None
        else None
    )
    output["conservative_ev_ebit"] = (
        output["conservative_ev"] / ebit_ttm
        if output["conservative_ev"] is not None and ebit_ttm is not None and ebit_ttm > 0
        else None
    )
    return output


def calculate_ttm_operating_income(payload: dict[str, Any]) -> dict[str, float | str | None]:
    periods = usd_periods_for_tags(payload, OPERATING_INCOME_TAGS)
    annuals = [
        period
        for period in periods
        if period.form in {"10-K", "20-F", "40-F"} and period.fp == "FY" and _duration_at_least(period, 300)
    ]
    ytd_quarters = [
        period
        for period in periods
        if period.form in {"10-Q", "6-K"} and (period.fp in {"Q1", "Q2", "Q3"} or period.form == "6-K") and _looks_like_ytd(period)
    ]

    annual = _latest_period(annuals)
    current_ytd = _latest_period(ytd_quarters)
    if annual is None:
        estimated = calculate_estimated_annual_ebit(
            payload,
            pretax_tags=PRETAX_INCOME_TAGS,
            finance_cost_tags=FINANCE_COST_TAGS,
            taxonomy="us-gaap",
            forms={"10-K", "20-F", "40-F", "F-1", "F-1/A", "S-1", "S-1/A"},
        )
        if estimated["ebit_ttm"] is not None:
            return estimated
        return {"ebit_ttm": None, "method": "missing annual operating income", "annual": None, "previous_ytd": None, "current_ytd": None}
    if current_ytd is None or current_ytd.end_date <= annual.end_date:
        return {
            "ebit_ttm": annual.value,
            "method": "latest annual operating income",
            "annual": annual.value,
            "previous_ytd": None,
            "current_ytd": None,
        }

    previous_ytd = _latest_period(
        [
            period
            for period in ytd_quarters
            if period.fp == current_ytd.fp
            and period.end_date < current_ytd.end_date
            and period.end_date <= annual.end_date
        ]
    )
    if previous_ytd is None:
        return {
            "ebit_ttm": annual.value,
            "method": "latest annual operating income; missing comparable prior YTD",
            "annual": annual.value,
            "previous_ytd": None,
            "current_ytd": current_ytd.value,
        }

    return {
        "ebit_ttm": annual.value - previous_ytd.value + current_ytd.value,
        "method": f"annual FY - prior {current_ytd.fp} YTD + current {current_ytd.fp} YTD",
        "annual": annual.value,
        "previous_ytd": previous_ytd.value,
        "current_ytd": current_ytd.value,
    }


def calculate_ttm_ifrs_operating_income(payload: dict[str, Any]) -> dict[str, float | str | None]:
    periods = usd_periods_for_tags(payload, IFRS_OPERATING_INCOME_TAGS, taxonomy="ifrs-full")
    annuals = [
        period
        for period in periods
        if period.fp == "FY" and period.form in {"20-F", "40-F", "10-K"} and _duration_at_least(period, 300)
    ]
    annual = _latest_period(annuals)
    if annual is None:
        estimated = calculate_estimated_annual_ebit(
            payload,
            pretax_tags=IFRS_PRETAX_INCOME_TAGS,
            finance_cost_tags=IFRS_FINANCE_COST_TAGS,
            net_income_tags=IFRS_NET_INCOME_TAGS,
            income_tax_tags=IFRS_INCOME_TAX_TAGS,
            taxonomy="ifrs-full",
            forms={"20-F", "40-F", "10-K", "6-K", "20-F/A", "40-F/A", "6-K/A"},
        )
        if estimated["ebit_ttm"] is not None:
            return estimated
        return {
            "ebit_ttm": None,
            "method": "IFRS operating income tag missing",
            "annual": None,
            "previous_ytd": None,
            "current_ytd": None,
        }

    return {
        "ebit_ttm": annual.value,
        "method": "latest IFRS annual operating income",
        "annual": annual.value,
        "previous_ytd": None,
        "current_ytd": None,
    }


def calculate_estimated_annual_ebit(
    payload: dict[str, Any],
    *,
    pretax_tags: tuple[str, ...],
    finance_cost_tags: tuple[str, ...],
    taxonomy: str,
    forms: set[str],
    net_income_tags: tuple[str, ...] = (),
    income_tax_tags: tuple[str, ...] = (),
) -> dict[str, float | str | None]:
    pretax = _latest_annual_period(payload, pretax_tags, taxonomy=taxonomy, forms=forms)
    if pretax is None:
        net_income = _latest_annual_period(payload, net_income_tags, taxonomy=taxonomy, forms=forms)
        if net_income is None:
            return {
                "ebit_ttm": None,
                "method": "estimated EBIT unavailable",
                "annual": None,
                "previous_ytd": None,
                "current_ytd": None,
            }
        income_tax = _matching_annual_period(
            payload,
            income_tax_tags,
            taxonomy=taxonomy,
            forms=forms,
            end=net_income.end,
        )
        finance_cost = _matching_annual_period(
            payload,
            finance_cost_tags,
            taxonomy=taxonomy,
            forms=forms,
            end=net_income.end,
        )
        if income_tax is None or finance_cost is None:
            return {
                "ebit_ttm": None,
                "method": "estimated EBIT unavailable",
                "annual": None,
                "previous_ytd": None,
                "current_ytd": None,
            }
        estimated = net_income.value + income_tax.value + abs(finance_cost.value)
        return {
            "ebit_ttm": estimated,
            "method": f"estimated EBIT from net income + income tax + finance costs ({taxonomy})",
            "annual": estimated,
            "previous_ytd": None,
            "current_ytd": None,
        }

    finance_cost = _matching_annual_period(
        payload,
        finance_cost_tags,
        taxonomy=taxonomy,
        forms=forms,
        end=pretax.end,
    )
    if finance_cost is None:
        return {
            "ebit_ttm": pretax.value,
            "method": f"estimated EBIT from pretax income only ({taxonomy}; finance cost missing)",
            "annual": pretax.value,
            "previous_ytd": None,
            "current_ytd": None,
        }

    estimated = pretax.value + abs(finance_cost.value)
    return {
        "ebit_ttm": estimated,
        "method": f"estimated EBIT from pretax income + finance costs ({taxonomy})",
        "annual": estimated,
        "previous_ytd": None,
        "current_ytd": None,
    }


def latest_usd_value(payload: dict[str, Any], tags: tuple[str, ...], *, taxonomy: str = "us-gaap") -> UsFactValue | None:
    latest = _latest_period(usd_periods_for_tags(payload, tags, taxonomy=taxonomy))
    if latest is None:
        return None
    return UsFactValue(
        tag=latest.tag,
        value=latest.value,
        end=latest.end,
        form=latest.form,
        filed=latest.filed,
        frame=latest.frame,
    )


def usd_periods_for_tags(payload: dict[str, Any], tags: tuple[str, ...], *, taxonomy: str = "us-gaap") -> list[UsFactPeriod]:
    return fact_periods_for_tags(payload, tags, taxonomy=taxonomy, unit="USD")


def fact_periods_for_tags(
    payload: dict[str, Any],
    tags: tuple[str, ...],
    *,
    taxonomy: str = "us-gaap",
    unit: str | None = "USD",
) -> list[UsFactPeriod]:
    facts = payload.get("facts", {})
    taxonomy_facts = facts.get(taxonomy, {}) if isinstance(facts, dict) else {}
    periods = []
    for tag in tags:
        fact = taxonomy_facts.get(tag)
        if not isinstance(fact, dict):
            continue
        units = fact.get("units", {})
        if not isinstance(units, dict):
            continue
        unit_points = [units.get(unit)] if unit is not None else units.values()
        for points in unit_points:
            if not isinstance(points, list):
                continue
            for point in points:
                if not isinstance(point, dict):
                    continue
                if point.get("val") is None or not point.get("end"):
                    continue
                periods.append(
                    UsFactPeriod(
                        tag=tag,
                        value=float(point["val"]),
                        end=str(point["end"]),
                        form=str(point["form"]) if point.get("form") is not None else None,
                        filed=str(point["filed"]) if point.get("filed") is not None else None,
                        frame=str(point["frame"]) if point.get("frame") is not None else None,
                        start=str(point["start"]) if point.get("start") is not None else None,
                        fy=int(point["fy"]) if point.get("fy") is not None else None,
                        fp=str(point["fp"]) if point.get("fp") is not None else None,
                    )
                )

    return periods


def _ifrs_debt_components(payload: dict[str, Any]) -> list[UsFactValue]:
    components = []
    for tag_group in IFRS_DEBT_TAG_GROUPS:
        aggregate = latest_usd_value(payload, (tag_group[0],), taxonomy="ifrs-full")
        if aggregate is not None:
            components.append(aggregate)
            continue
        components.extend(
            value
            for tag in tag_group[1:]
            if (value := latest_usd_value(payload, (tag,), taxonomy="ifrs-full")) is not None
        )
    return components


def _sum_latest_values_same_end(
    payload: dict[str, Any],
    tags: tuple[str, ...],
    *,
    taxonomy: str,
    tag_label: str,
) -> UsFactValue | None:
    values = [latest_usd_value(payload, (tag,), taxonomy=taxonomy) for tag in tags]
    if any(value is None for value in values):
        return None
    present_values = [value for value in values if value is not None]
    ends = {value.end for value in present_values}
    if len(ends) != 1:
        return None
    latest_filed = max((value.filed for value in present_values if value.filed is not None), default=None)
    return UsFactValue(
        tag=tag_label,
        value=sum(value.value for value in present_values),
        end=present_values[0].end,
        form=present_values[0].form,
        filed=latest_filed,
        frame=present_values[0].frame,
    )


def _latest_period(periods: list[UsFactPeriod]) -> UsFactPeriod | None:
    if not periods:
        return None
    return max(periods, key=lambda value: (value.end, value.filed or ""))


def _latest_annual_period(
    payload: dict[str, Any],
    tags: tuple[str, ...],
    *,
    taxonomy: str,
    forms: set[str],
) -> UsFactPeriod | None:
    periods = [
        period
        for period in usd_periods_for_tags(payload, tags, taxonomy=taxonomy)
        if period.form in forms and period.fp == "FY" and _duration_at_least(period, 300)
    ]
    return _latest_period(periods)


def _matching_annual_period(
    payload: dict[str, Any],
    tags: tuple[str, ...],
    *,
    taxonomy: str,
    forms: set[str],
    end: str,
) -> UsFactPeriod | None:
    periods = [
        period
        for period in usd_periods_for_tags(payload, tags, taxonomy=taxonomy)
        if period.form in forms and period.fp == "FY" and period.end == end and _duration_at_least(period, 300)
    ]
    return _latest_period(periods)


def _financial_report_metadata(payload: dict[str, Any], tags: tuple[str, ...], *, taxonomy: str) -> dict[str, Any]:
    periods = fact_periods_for_tags(payload, tags, taxonomy=taxonomy, unit=None)
    latest = _latest_period(periods)
    has_quarterly = any(_is_quarterly_period(period) for period in periods)
    return {
        "financial_statement_currency": _financial_statement_currency(payload, tags, taxonomy=taxonomy),
        "financial_statement_form": latest.form if latest else None,
        "financial_statement_end": latest.end if latest else None,
        "financial_statement_filed": latest.filed if latest else None,
        "has_quarterly_financials": has_quarterly,
    }


def _financial_statement_currency(payload: dict[str, Any], tags: tuple[str, ...], *, taxonomy: str) -> str | None:
    units = _units_for_tags(payload, tags, taxonomy=taxonomy)
    if "USD" in units:
        return "USD"
    currency_units = [unit for unit in units if _looks_like_currency_unit(unit)]
    return sorted(currency_units)[0] if currency_units else None


def _units_for_tags(payload: dict[str, Any], tags: tuple[str, ...], *, taxonomy: str) -> set[str]:
    facts = payload.get("facts", {})
    taxonomy_facts = facts.get(taxonomy, {}) if isinstance(facts, dict) else {}
    units: set[str] = set()
    for tag in tags:
        fact = taxonomy_facts.get(tag)
        if not isinstance(fact, dict):
            continue
        fact_units = fact.get("units", {})
        if isinstance(fact_units, dict):
            units.update(str(unit) for unit in fact_units)
    return units


def _looks_like_currency_unit(unit: str) -> bool:
    return len(unit) == 3 and unit.isalpha() and unit.isupper()


def _is_quarterly_period(period: UsFactPeriod) -> bool:
    return period.form == "10-Q" or period.fp in {"Q1", "Q2", "Q3"}


def _duration_at_least(period: UsFactPeriod, days: int) -> bool:
    return period.duration_days is not None and period.duration_days >= days


def _looks_like_ytd(period: UsFactPeriod) -> bool:
    if period.fp == "Q1":
        return _duration_at_least(period, 60)
    if period.fp == "Q2":
        return _duration_at_least(period, 120)
    if period.fp == "Q3":
        return _duration_at_least(period, 200)
    return False


def _has_core_us_gaap_facts(payload: dict[str, Any]) -> bool:
    core_tags = (
        *CURRENT_ASSETS_TAGS,
        *TOTAL_LIABILITIES_TAGS,
        *CASH_TAGS,
        *OPERATING_INCOME_TAGS,
    )
    return bool(usd_periods_for_tags(payload, core_tags))

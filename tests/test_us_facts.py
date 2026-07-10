from ncav_screener.us_facts import (
    add_us_market_metrics,
    build_us_financial_snapshot,
    calculate_ttm_operating_income,
    latest_usd_value,
)


def test_latest_usd_value_uses_first_available_tag_and_latest_date() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "AssetsCurrent": {
                    "units": {
                        "USD": [
                            {"val": 100, "end": "2024-03-31", "filed": "2024-05-01", "form": "10-Q"},
                            {"val": 140, "end": "2024-06-30", "filed": "2024-08-01", "form": "10-Q"},
                        ]
                    }
                }
            }
        }
    }

    value = latest_usd_value(payload, ("AssetsCurrent",))

    assert value is not None
    assert value.tag == "AssetsCurrent"
    assert value.value == 140
    assert value.end == "2024-06-30"


def test_build_us_financial_snapshot_calculates_ncav_and_debt() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "AssetsCurrent": {"units": {"USD": [{"val": 500, "end": "2024-06-30"}]}},
                "Liabilities": {"units": {"USD": [{"val": 300, "end": "2024-06-30"}]}},
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [{"val": 80, "end": "2024-06-30"}]}
                },
                "OperatingIncomeLoss": {"units": {"USD": [{"val": 40, "end": "2024-06-30"}]}},
                "ShortTermDebtCurrent": {"units": {"USD": [{"val": 20, "end": "2024-06-30"}]}},
                "LongTermDebtNoncurrent": {"units": {"USD": [{"val": 50, "end": "2024-06-30"}]}},
                "OperatingLeaseLiabilityCurrent": {"units": {"USD": [{"val": 5, "end": "2024-06-30"}]}},
                "DerivativeLiabilitiesNoncurrent": {"units": {"USD": [{"val": 7, "end": "2024-06-30"}]}},
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)

    assert snapshot["current_assets"] == 500
    assert snapshot["total_liabilities"] == 300
    assert snapshot["cash_and_equivalents"] == 80
    assert snapshot["interest_bearing_debt"] == 70
    assert snapshot["other_financial_liabilities"] == 12
    assert snapshot["other_financial_liability_tags"] == "OperatingLeaseLiabilityCurrent, DerivativeLiabilitiesNoncurrent"
    assert snapshot["ncav"] == 200
    assert snapshot["financial_taxonomy"] == "us-gaap"
    assert snapshot["has_quarterly_financials"] is False


def test_calculate_ttm_operating_income_from_annual_and_ytd_quarters() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "val": 1000,
                                "form": "10-K",
                                "fp": "FY",
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "filed": "2024-02-15",
                            },
                            {
                                "val": 300,
                                "form": "10-Q",
                                "fp": "Q2",
                                "start": "2023-01-01",
                                "end": "2023-06-30",
                                "filed": "2023-08-01",
                            },
                            {
                                "val": 450,
                                "form": "10-Q",
                                "fp": "Q2",
                                "start": "2024-01-01",
                                "end": "2024-06-30",
                                "filed": "2024-08-01",
                            },
                            {
                                "val": 200,
                                "form": "10-Q",
                                "fp": "Q2",
                                "start": "2024-04-01",
                                "end": "2024-06-30",
                                "filed": "2024-08-01",
                                "frame": "CY2024Q2",
                            },
                        ]
                    }
                }
            }
        }
    }

    result = calculate_ttm_operating_income(payload)

    assert result["ebit_ttm"] == 1150
    assert result["annual"] == 1000
    assert result["previous_ytd"] == 300
    assert result["current_ytd"] == 450


def test_build_us_financial_snapshot_accepts_20f_operating_income_and_liability_components() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "AssetsCurrent": {"units": {"USD": [{"val": 500, "end": "2025-12-31"}]}},
                "LiabilitiesCurrent": {"units": {"USD": [{"val": 120, "end": "2025-12-31"}]}},
                "LiabilitiesNoncurrent": {"units": {"USD": [{"val": 180, "end": "2025-12-31"}]}},
                "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [{"val": 80, "end": "2025-12-31"}]}},
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "val": 100,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)

    assert snapshot["total_liabilities"] == 300
    assert snapshot["total_liabilities_tag"] == "LiabilitiesCurrent + LiabilitiesNoncurrent"
    assert snapshot["ncav"] == 200
    assert snapshot["ebit_ttm"] == 100
    assert snapshot["ebit_ttm_method"] == "latest annual operating income"


def test_add_us_market_metrics_calculates_ev_and_ratios() -> None:
    result = add_us_market_metrics(
        {
            "ncav": 200,
            "cash_and_equivalents": 80,
            "interest_bearing_debt": 70,
            "other_financial_liabilities": 12,
            "ebit_ttm": 50,
        },
        market_cap=300,
        shares_outstanding=10,
    )

    assert result["ncav_ratio"] == 1.5
    assert result["ncav_per_share"] == 20
    assert result["ev"] == 290
    assert result["ev_ebit"] == 5.8
    assert result["conservative_ev"] == 302
    assert result["conservative_ev_ebit"] == 6.04


def test_add_us_market_metrics_excludes_ev_ebit_when_ttm_ebit_is_negative() -> None:
    result = add_us_market_metrics(
        {
            "ncav": 200,
            "cash_and_equivalents": 80,
            "interest_bearing_debt": 70,
            "other_financial_liabilities": 12,
            "ebit_ttm": -50,
        },
        market_cap=300,
        shares_outstanding=10,
    )

    assert result["ev"] == 290
    assert result["conservative_ev"] == 302
    assert result["ev_ebit"] is None
    assert result["conservative_ev_ebit"] is None


def test_build_us_financial_snapshot_reads_ifrs_balance_sheet_values() -> None:
    payload = {
        "facts": {
            "ifrs-full": {
                "CurrentAssets": {
                    "units": {"USD": [{"val": 2600, "end": "2025-12-31", "form": "40-F", "filed": "2026-03-24"}]}
                },
                "Liabilities": {
                    "units": {"USD": [{"val": 6900, "end": "2025-12-31", "form": "40-F", "filed": "2026-03-24"}]}
                },
                "CashAndCashEquivalents": {
                    "units": {"USD": [{"val": 1050, "end": "2025-12-31", "form": "40-F", "filed": "2026-03-24"}]}
                },
                "Borrowings": {"units": {"USD": [{"val": 90, "end": "2025-12-31"}]}},
                "LeaseLiabilities": {"units": {"USD": [{"val": 5600, "end": "2025-12-31"}]}},
                "ProfitLoss": {
                    "units": {
                        "USD": [
                            {
                                "val": 480,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)
    metrics = add_us_market_metrics(snapshot, market_cap=3000, shares_outstanding=100)

    assert snapshot["financial_taxonomy"] == "ifrs-full"
    assert snapshot["financial_statement_currency"] == "USD"
    assert snapshot["financial_statement_form"] == "40-F"
    assert snapshot["financial_statement_end"] == "2025-12-31"
    assert snapshot["financial_statement_filed"] == "2026-03-24"
    assert snapshot["has_quarterly_financials"] is False
    assert snapshot["current_assets"] == 2600
    assert snapshot["total_liabilities"] == 6900
    assert snapshot["cash_and_equivalents"] == 1050
    assert snapshot["interest_bearing_debt"] == 5690
    assert snapshot["interest_bearing_debt_tags"] == "Borrowings, LeaseLiabilities"
    assert snapshot["ncav"] == -4300
    assert snapshot["ebit_ttm"] is None
    assert snapshot["ebit_ttm_method"] == "IFRS operating income tag missing"
    assert metrics["ev"] == 7640
    assert metrics["ev_ebit"] is None


def test_build_us_financial_snapshot_uses_ifrs_when_us_gaap_has_only_nonfinancial_tags() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "NumberOfOperatingSegments": {"units": {"segment": [{"val": 4, "end": "2024-12-31"}]}}
            },
            "ifrs-full": {
                "CurrentAssets": {"units": {"USD": [{"val": 2600, "end": "2025-12-31"}]}},
                "Liabilities": {"units": {"USD": [{"val": 6900, "end": "2025-12-31", "form": "40-F", "filed": "2026-03-24"}]}},
                "CashAndCashEquivalents": {"units": {"USD": [{"val": 1050, "end": "2025-12-31"}]}},
            },
        }
    }

    snapshot = build_us_financial_snapshot(payload)

    assert snapshot["financial_taxonomy"] == "ifrs-full"
    assert snapshot["current_assets"] == 2600
    assert snapshot["total_liabilities"] == 6900
    assert snapshot["cash_and_equivalents"] == 1050


def test_build_us_financial_snapshot_uses_clear_ifrs_operating_income_tag() -> None:
    payload = {
        "facts": {
            "ifrs-full": {
                "CurrentAssets": {"units": {"USD": [{"val": 500, "end": "2025-12-31"}]}},
                "Liabilities": {"units": {"USD": [{"val": 300, "end": "2025-12-31"}]}},
                "CashAndCashEquivalents": {"units": {"USD": [{"val": 80, "end": "2025-12-31"}]}},
                "OperatingProfitLoss": {
                    "units": {
                        "USD": [
                            {
                                "val": 120,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)

    assert snapshot["ebit_ttm"] == 120
    assert snapshot["ebit_ttm_method"] == "latest IFRS annual operating income"


def test_build_us_financial_snapshot_estimates_ifrs_ebit_from_pretax_and_finance_costs() -> None:
    payload = {
        "facts": {
            "ifrs-full": {
                "CurrentAssets": {"units": {"USD": [{"val": 500, "end": "2025-12-31"}]}},
                "Liabilities": {"units": {"USD": [{"val": 300, "end": "2025-12-31"}]}},
                "CashAndCashEquivalents": {"units": {"USD": [{"val": 80, "end": "2025-12-31"}]}},
                "ProfitLossBeforeTax": {
                    "units": {
                        "USD": [
                            {
                                "val": 100,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
                "FinanceCosts": {
                    "units": {
                        "USD": [
                            {
                                "val": 20,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)

    assert snapshot["ebit_ttm"] == 120
    assert snapshot["ebit_ttm_method"] == "estimated EBIT from pretax income + finance costs (ifrs-full)"


def test_build_us_financial_snapshot_estimates_ifrs_ebit_from_net_income_tax_and_finance_costs() -> None:
    payload = {
        "facts": {
            "ifrs-full": {
                "CurrentAssets": {"units": {"USD": [{"val": 500, "end": "2025-12-31"}]}},
                "Liabilities": {"units": {"USD": [{"val": 300, "end": "2025-12-31"}]}},
                "CashAndCashEquivalents": {"units": {"USD": [{"val": 80, "end": "2025-12-31"}]}},
                "ProfitLoss": {
                    "units": {
                        "USD": [
                            {
                                "val": -2343,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
                "IncomeTaxExpenseContinuingOperations": {
                    "units": {
                        "USD": [
                            {
                                "val": -13,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
                "InterestExpense": {
                    "units": {
                        "USD": [
                            {
                                "val": 469,
                                "form": "20-F",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)
    metrics = add_us_market_metrics(snapshot, market_cap=1000, shares_outstanding=100)

    assert snapshot["ebit_ttm"] == -1887
    assert snapshot["ebit_ttm_method"] == "estimated EBIT from net income + income tax + finance costs (ifrs-full)"
    assert metrics["ev_ebit"] is None


def test_build_us_financial_snapshot_estimates_us_gaap_ebit_from_pretax_only() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "AssetsCurrent": {"units": {"USD": [{"val": 500, "end": "2025-12-31"}]}},
                "Liabilities": {"units": {"USD": [{"val": 300, "end": "2025-12-31"}]}},
                "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [{"val": 80, "end": "2025-12-31"}]}},
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxes": {
                    "units": {
                        "USD": [
                            {
                                "val": 100,
                                "form": "10-K",
                                "fp": "FY",
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                            }
                        ]
                    }
                },
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)

    assert snapshot["ebit_ttm"] == 100
    assert snapshot["ebit_ttm_method"] == "estimated EBIT from pretax income only (us-gaap; finance cost missing)"


def test_build_us_financial_snapshot_marks_non_usd_ifrs_financials() -> None:
    payload = {
        "facts": {
            "ifrs-full": {
                "CurrentAssets": {
                    "units": {"CAD": [{"val": 500, "end": "2025-12-31", "form": "40-F", "filed": "2026-03-24"}]}
                },
                "Liabilities": {
                    "units": {"CAD": [{"val": 300, "end": "2025-12-31", "form": "40-F", "filed": "2026-03-24"}]}
                },
                "CashAndCashEquivalents": {
                    "units": {"CAD": [{"val": 80, "end": "2025-12-31", "form": "40-F", "filed": "2026-03-24"}]}
                },
            }
        }
    }

    snapshot = build_us_financial_snapshot(payload)

    assert snapshot["financial_taxonomy"] == "ifrs-full"
    assert snapshot["financial_statement_currency"] == "CAD"
    assert snapshot["financial_statement_form"] == "40-F"
    assert snapshot["current_assets"] is None
    assert snapshot["total_liabilities"] is None
    assert snapshot["cash_and_equivalents"] is None

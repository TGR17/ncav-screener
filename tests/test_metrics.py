from ncav_screener.metrics import (
    calculate_ev,
    calculate_ev_ebit,
    calculate_ncav,
    calculate_ncav_per_share,
    calculate_ncav_ratio,
)


def test_suprema_example_from_handoff_document() -> None:
    market_cap = 307_200_000_000
    current_assets = 177_500_000_000
    total_liabilities = 19_700_000_000
    cash_and_equivalents = 51_290_000_000
    interest_bearing_debt = 2_300_000_000
    ebit_ttm = 32_500_000_000
    shares_outstanding = 6_974_311

    ncav = calculate_ncav(current_assets, total_liabilities)
    ncav_per_share = calculate_ncav_per_share(ncav, shares_outstanding)
    ncav_ratio = calculate_ncav_ratio(market_cap, ncav)
    ev = calculate_ev(market_cap, interest_bearing_debt, cash_and_equivalents)
    ev_ebit = calculate_ev_ebit(ev, ebit_ttm)

    assert ncav == 157_800_000_000
    assert round(ncav_per_share) == 22626
    assert round(ncav_ratio, 2) == 1.95
    assert ev == 258_210_000_000
    assert round(ev_ebit, 1) == 7.9


def test_ncav_ratio_is_none_when_ncav_is_not_positive() -> None:
    assert calculate_ncav_ratio(market_cap=100, ncav=0) is None
    assert calculate_ncav_ratio(market_cap=100, ncav=-1) is None

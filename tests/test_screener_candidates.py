import pandas as pd

from ncav_screener.screener import save_ncav_candidates, save_value_candidates


def test_candidate_exports_exclude_cny_financial_statements(tmp_path) -> None:
    results = pd.DataFrame(
        [
            {
                "ticker": "000001",
                "status": "ok",
                "financial_currency": "KRW",
                "ncav_ratio": 0.5,
                "ebit_ttm": 100,
                "ev_ebit": 3.0,
            },
            {
                "ticker": "000002",
                "status": "ok",
                "financial_currency": "CNY",
                "ncav_ratio": 0.4,
                "ebit_ttm": 100,
                "ev_ebit": 2.0,
            },
        ]
    )

    ncav_candidates = save_ncav_candidates(results, tmp_path / "ncav.csv")
    value_candidates = save_value_candidates(results, tmp_path / "value.csv")

    assert ncav_candidates["ticker"].tolist() == ["000001"]
    assert value_candidates["ticker"].tolist() == ["000001"]

from __future__ import annotations

import pandas as pd

from ncav_screener.reporting import add_data_notes


def test_add_data_notes_flags_krx_risk_section_without_dropping_row() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "035610",
                "section": "투자주의환기종목(소속부없음)",
                "market_cap": 100.0,
                "market_data_found": True,
                "ncav": 200.0,
                "ncav_ratio": 0.5,
                "ebit_ttm": 10.0,
                "ev": 20.0,
                "ev_ebit": 2.0,
                "per": 1.0,
                "operating_margin_current": 0.1,
            }
        ]
    )

    result = add_data_notes(frame)

    assert len(result) == 1
    assert result.loc[0, "data_status"] == "계산 제외 있음"
    assert result.loc[0, "data_note"] == "KRX 리스크 소속부: 투자주의환기종목(소속부없음)"

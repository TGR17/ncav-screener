from __future__ import annotations

import pandas as pd

from ncav_screener.market_data import filter_korean_statement_universe, filter_screening_universe


def test_filter_screening_universe_excludes_korean_financial_and_holding_names() -> None:
    frame = pd.DataFrame(
        [
            {"ticker": "000001", "name": "정상전자", "section": ""},
            {"ticker": "000002", "name": "테스트홀딩스", "section": ""},
            {"ticker": "000003", "name": "샘플금융지주", "section": ""},
            {"ticker": "000004", "name": "샘플은행", "section": ""},
        ]
    )

    result = filter_screening_universe(frame)

    assert result["ticker"].tolist() == ["000001"]


def test_filter_screening_universe_does_not_treat_inner_woo_as_preferred_share() -> None:
    frame = pd.DataFrame(
        [
            {"ticker": "088910", "name": "동우팜투테이블", "section": ""},
            {"ticker": "005935", "name": "삼성전자우", "section": ""},
            {"ticker": "000995", "name": "DB하이텍1우", "section": ""},
            {"ticker": "005387", "name": "현대차2우B", "section": ""},
        ]
    )

    result = filter_screening_universe(frame)

    assert result["ticker"].tolist() == ["088910"]


def test_filter_korean_statement_universe_excludes_financial_and_utility_industries() -> None:
    frame = pd.DataFrame(
        [
            {"ticker": "000001", "industry_name": "반도체 제조업"},
            {"ticker": "000002", "industry_name": "기타 금융업"},
            {"ticker": "000003", "industry_name": "보험업"},
            {"ticker": "000004", "industry_name": "전기, 가스, 증기 및 공기 조절 공급업"},
        ]
    )

    result = filter_korean_statement_universe(frame)

    assert result["ticker"].tolist() == ["000001"]

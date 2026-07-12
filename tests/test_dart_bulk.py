from __future__ import annotations

from ncav_screener.dart_bulk import convert_amount_to_krw, currency_rate_to_krw


def test_convert_amount_to_krw_uses_supported_dart_currency_rates() -> None:
    assert convert_amount_to_krw("1,000", "KRW") == 1_000
    assert convert_amount_to_krw("1,000", "USD") == 1_500_000
    assert convert_amount_to_krw("1,000", "CNY") == 220_000


def test_convert_amount_to_krw_returns_none_for_unknown_currency() -> None:
    assert currency_rate_to_krw("EUR") is None
    assert convert_amount_to_krw("1,000", "EUR") is None

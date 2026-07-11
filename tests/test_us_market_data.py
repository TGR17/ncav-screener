from pathlib import Path

from ncav_screener.us_market_data import _parse_nasdaq_row, filter_us_screening_universe, load_us_market_data


def test_load_us_market_data_normalizes_tickers_and_numeric_columns(tmp_path: Path) -> None:
    path = tmp_path / "us_market_data.csv"
    path.write_text(
        "ticker,name,exchange,price,shares_outstanding,market_cap\n"
        "brk.b,Berkshire,NYSE,400,10,4000\n"
        "AAPL,Apple,Nasdaq,200,20,4000\n",
        encoding="utf-8",
    )

    frame = load_us_market_data(path)

    assert frame.loc[0, "ticker"] == "BRK-B"
    assert frame.loc[1, "ticker"] == "AAPL"
    assert frame.loc[1, "market_cap"] == 4000
    assert frame.loc[1, "shares_outstanding"] == 20


def test_parse_nasdaq_row_cleans_market_data_values() -> None:
    row = _parse_nasdaq_row(
        {
            "symbol": "brk.b",
            "name": "Berkshire Hathaway Inc.",
            "lastsale": "$400.50",
            "marketCap": "800000000000.00",
            "volume": "123,456",
            "sector": "Finance",
            "industry": "Property-Casualty Insurers",
            "country": "United States",
        }
    )

    assert row["ticker"] == "BRK-B"
    assert row["price"] == 400.50
    assert row["market_cap"] == 800000000000.0
    assert row["volume"] == 123456.0


def test_filter_us_screening_universe_excludes_financial_and_special_securities() -> None:
    import pandas as pd

    frame = pd.DataFrame(
        [
            {"ticker": "AAPL", "name": "Apple Inc. Common Stock", "sector": "Technology"},
            {"ticker": "BANK", "name": "Bank Co Common Stock", "sector": "Finance"},
            {"ticker": "SPACU", "name": "Example Acquisition Corp Unit", "sector": "Industrials"},
            {"ticker": "ADRX", "name": "Example American Depositary Shares", "sector": "Health Care"},
        ]
    )

    filtered = filter_us_screening_universe(frame)

    assert filtered["ticker"].tolist() == ["AAPL"]

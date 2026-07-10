from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from .config import (
    INPUT_DIR,
    MARKET_DATA_CSV,
    OUTPUT_DIR,
    SEC_COMPANY_TICKERS_EXCHANGE_JSON,
    SEC_COMPANYFACTS_DIR,
    SEC_COMPANYFACTS_ZIP,
    US_FINANCIAL_CACHE_CSV,
    US_MARKET_DATA_CSV,
    load_settings,
)
from .dart_bulk import (
    add_ev_ebit,
    build_ncav_from_bulk_balance_sheet,
    build_ttm_ebit_from_bulk,
    find_bulk_file_by_keywords,
    find_bulk_statement_file,
    merge_bulk_ncav_with_market_data,
)
from .dart_client import DartClient
from .fundamentals import load_fundamentals, merge_fundamentals
from .f_score import build_f_score_from_bulk, merge_f_score
from .market_data import filter_screening_universe, get_market_data_row, load_market_data
from .reporting import save_korean_report
from .sec_client import (
    companyfacts_cache_path,
    download_companyfacts,
    download_company_tickers_exchange,
    find_company_by_ticker,
    load_companyfacts,
    load_company_tickers_exchange,
    summarize_us_gaap_tags,
)
from .us_facts import build_us_financial_snapshot
from .us_financial_cache import build_us_financial_cache, load_us_financial_cache, save_us_financial_cache
from .us_market_data import download_nasdaq_us_market_data, filter_us_screening_universe, load_us_market_data
from .us_reporting import save_us_app_report
from .us_screener import build_us_screener_results
from .screener import (
    save_ncav_candidates,
    save_value_candidates,
    screen_market_data_file,
    screen_single_stock_from_dart,
)


NON_FINANCIAL_EXCLUDE_KEYWORDS = ("\uae08\uc735\uae30\ud0c0", "\ubcf4\ud5d8", "\uc740\ud589", "\uc99d\uad8c")
COMPREHENSIVE_INCOME_KEYWORD = "\ud3ec\uad04\uc190\uc775\uacc4\uc0b0\uc11c"
INCOME_STATEMENT_KEYWORD = "\uc190\uc775\uacc4\uc0b0\uc11c"


def find_income_files_with_separate_fallback(input_dir: Path, base_keywords: tuple[str, ...]) -> list[Path]:
    paths = []
    statement_variants = [
        (INCOME_STATEMENT_KEYWORD, (*NON_FINANCIAL_EXCLUDE_KEYWORDS, COMPREHENSIVE_INCOME_KEYWORD)),
        (COMPREHENSIVE_INCOME_KEYWORD, NON_FINANCIAL_EXCLUDE_KEYWORDS),
    ]
    for statement_keyword, exclude_keywords in statement_variants:
        for consolidated in (True, False):
            required_keywords = (*base_keywords, statement_keyword)
            if consolidated:
                required_keywords = (*required_keywords, "\uc5f0\uacb0")
                excludes = exclude_keywords
            else:
                excludes = (*exclude_keywords, "\uc5f0\uacb0")
            try:
                path = find_bulk_file_by_keywords(
                    input_dir,
                    required_keywords,
                    exclude_keywords=excludes,
                )
            except FileNotFoundError:
                continue
            if path not in paths:
                paths.append(path)

    if not paths:
        raise FileNotFoundError(f"No income files found for keywords: {base_keywords}")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ncav-screener")
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="Run screener for one ticker")
    single.add_argument("ticker")
    single.add_argument("--corp-code", required=True)
    single.add_argument("--corp-name", default="")
    single.add_argument("--market-cap", type=float)
    single.add_argument("--shares", type=float)
    single.add_argument("--market-data", type=Path, default=MARKET_DATA_CSV)
    single.add_argument("--business-year", type=int, default=2025)
    single.add_argument("--ttm-next-year", type=int, default=None)

    screen = subparsers.add_parser("screen", help="Run screener for listed companies")
    screen.add_argument("--date", required=False)
    screen.add_argument("--max-ratio", type=float, default=1.0)
    screen.add_argument("--market-data", type=Path, default=MARKET_DATA_CSV)
    screen.add_argument("--output", type=Path, default=OUTPUT_DIR / "screen_results.csv")
    screen.add_argument("--candidates-output", type=Path, default=OUTPUT_DIR / "ncav_candidates.csv")
    screen.add_argument("--business-year", type=int, default=2025)
    screen.add_argument("--ttm-next-year", type=int, default=None)
    screen.add_argument("--limit", type=int, default=None)
    screen.add_argument("--request-delay", type=float, default=0.0)
    screen.add_argument("--no-default-filters", action="store_true")

    sec_cik = subparsers.add_parser("sec-cik", help="Find SEC CIK by US ticker")
    sec_cik.add_argument("ticker")
    sec_cik.add_argument("--cache", type=Path, default=SEC_COMPANY_TICKERS_EXCHANGE_JSON)
    sec_cik.add_argument("--refresh", action="store_true", help="Download the latest SEC ticker map")
    sec_cik.add_argument(
        "--user-agent",
        default=None,
        help="SEC request User-Agent. Defaults to SEC_USER_AGENT from .env or a project default.",
    )

    sec_facts = subparsers.add_parser("sec-facts", help="Download and summarize SEC companyfacts for a ticker")
    sec_facts.add_argument("ticker")
    sec_facts.add_argument("--ticker-cache", type=Path, default=SEC_COMPANY_TICKERS_EXCHANGE_JSON)
    sec_facts.add_argument("--facts-dir", type=Path, default=SEC_COMPANYFACTS_DIR)
    sec_facts.add_argument("--refresh-tickers", action="store_true", help="Download the latest SEC ticker map")
    sec_facts.add_argument("--refresh-facts", action="store_true", help="Download the latest companyfacts JSON")
    sec_facts.add_argument(
        "--user-agent",
        default=None,
        help="SEC request User-Agent. Defaults to SEC_USER_AGENT from .env or a project default.",
    )

    us_screen = subparsers.add_parser("us-screen", help="Build US screener CSV from SEC facts and US market data")
    us_screen.add_argument("--market-data", type=Path, default=US_MARKET_DATA_CSV)
    us_screen.add_argument("--ticker-cache", type=Path, default=SEC_COMPANY_TICKERS_EXCHANGE_JSON)
    us_screen.add_argument("--facts-dir", type=Path, default=SEC_COMPANYFACTS_DIR)
    us_screen.add_argument("--companyfacts-zip", type=Path, default=SEC_COMPANYFACTS_ZIP)
    us_screen.add_argument("--financial-cache", type=Path, default=US_FINANCIAL_CACHE_CSV)
    us_screen.add_argument("--no-financial-cache", action="store_true")
    us_screen.add_argument("--output", type=Path, default=OUTPUT_DIR / "screener_results_us.csv")
    us_screen.add_argument("--app-output", type=Path, default=Path("data/app/screener_results_us.csv"))
    us_screen.add_argument("--refresh-tickers", action="store_true", help="Download the latest SEC ticker map")
    us_screen.add_argument("--refresh-facts", action="store_true", help="Download companyfacts JSON for each ticker")
    us_screen.add_argument("--limit", type=int, default=None)
    us_screen.add_argument("--request-delay", type=float, default=0.2)
    us_screen.add_argument("--no-default-filters", action="store_true")
    us_screen.add_argument(
        "--user-agent",
        default=None,
        help="SEC request User-Agent. Defaults to SEC_USER_AGENT from .env or a project default.",
    )

    us_market = subparsers.add_parser("us-market-data", help="Download US market data CSV from Nasdaq screener")
    us_market.add_argument("--output", type=Path, default=US_MARKET_DATA_CSV)
    us_market.add_argument("--limit", type=int, default=10000)

    us_cache = subparsers.add_parser("us-financial-cache", help="Build reusable US financial snapshot CSV from SEC facts")
    us_cache.add_argument("--ticker-cache", type=Path, default=SEC_COMPANY_TICKERS_EXCHANGE_JSON)
    us_cache.add_argument("--facts-dir", type=Path, default=SEC_COMPANYFACTS_DIR)
    us_cache.add_argument("--companyfacts-zip", type=Path, default=SEC_COMPANYFACTS_ZIP)
    us_cache.add_argument("--output", type=Path, default=US_FINANCIAL_CACHE_CSV)
    us_cache.add_argument("--refresh-tickers", action="store_true", help="Download the latest SEC ticker map")
    us_cache.add_argument("--refresh-facts", action="store_true", help="Download companyfacts JSON for each ticker")
    us_cache.add_argument("--limit", type=int, default=None)
    us_cache.add_argument("--request-delay", type=float, default=0.0)
    us_cache.add_argument(
        "--user-agent",
        default=None,
        help="SEC request User-Agent. Defaults to SEC_USER_AGENT from .env or a project default.",
    )

    bulk = subparsers.add_parser("bulk-ncav", help="Run NCAV screener from DART bulk TXT files")
    bulk.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    bulk.add_argument("--balance-sheet", type=Path, default=None)
    bulk.add_argument("--market-data", type=Path, default=MARKET_DATA_CSV)
    bulk.add_argument("--output", type=Path, default=OUTPUT_DIR / "bulk_ncav_results.csv")
    bulk.add_argument("--candidates-output", type=Path, default=OUTPUT_DIR / "bulk_ncav_candidates.csv")
    bulk.add_argument("--value-candidates-output", type=Path, default=OUTPUT_DIR / "bulk_value_candidates.csv")
    bulk.add_argument("--korean-output", type=Path, default=OUTPUT_DIR / "bulk_value_candidates_kr.csv")
    bulk.add_argument("--max-ratio", type=float, default=1.0)
    bulk.add_argument("--max-ev-ebit", type=float, default=10.0)
    bulk.add_argument("--no-default-filters", action="store_true")
    bulk.add_argument("--with-ev-ebit", action="store_true")
    bulk.add_argument("--annual-income", type=Path, default=None)
    bulk.add_argument("--previous-q1-income", type=Path, default=None)
    bulk.add_argument("--current-q1-income", type=Path, default=None)
    bulk.add_argument("--fundamentals", type=Path, default=INPUT_DIR / "krx_fundamental.csv")
    bulk.add_argument("--no-fundamentals", action="store_true")
    bulk.add_argument("--with-f-score", action="store_true")
    bulk.add_argument("--current-balance-sheet", type=Path, default=None)
    bulk.add_argument("--previous-balance-sheet", type=Path, default=None)
    bulk.add_argument("--current-income", type=Path, default=None)
    bulk.add_argument("--previous-income", type=Path, default=None)
    bulk.add_argument("--current-cash-flow", type=Path, default=None)
    bulk.add_argument("--previous-cash-flow", type=Path, default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings()

    if args.command == "single":
        if not settings.dart_api_key:
            raise SystemExit("DART_API_KEY is missing. Create .env from .env.example.")
        market_cap = args.market_cap
        shares = args.shares
        if market_cap is None or shares is None:
            market_row = get_market_data_row(args.market_data, args.ticker)
            market_cap = market_row.market_cap
            shares = market_row.shares_outstanding
            if not args.corp_name and market_row.name:
                args.corp_name = market_row.name

        client = DartClient(api_key=settings.dart_api_key)
        result = screen_single_stock_from_dart(
            ticker=args.ticker,
            corp_code=args.corp_code,
            corp_name=args.corp_name,
            dart_client=client,
            market_cap=market_cap,
            shares_outstanding=shares,
            business_year=args.business_year,
            ttm_next_year=args.ttm_next_year,
        )
        for key, value in asdict(result).items():
            if isinstance(value, float):
                print(f"{key}: {value:,.2f}")
            else:
                print(f"{key}: {value}")
        return

    if args.command == "screen":
        if not settings.dart_api_key:
            raise SystemExit("DART_API_KEY is missing. Create .env from .env.example.")
        client = DartClient(api_key=settings.dart_api_key)
        result = screen_market_data_file(
            dart_client=client,
            market_data_path=args.market_data,
            output_path=args.output,
            business_year=args.business_year,
            ttm_next_year=args.ttm_next_year,
            limit=args.limit,
            request_delay_seconds=args.request_delay,
            apply_default_filters=not args.no_default_filters,
        )
        ok = int((result["status"] == "ok").sum()) if "status" in result.columns else 0
        errors = int((result["status"] == "error").sum()) if "status" in result.columns else 0
        candidates = save_ncav_candidates(
            result,
            args.candidates_output,
            max_ratio=args.max_ratio,
        )
        print(f"rows: {len(result)}")
        print(f"ok: {ok}")
        print(f"errors: {errors}")
        print(f"candidates <= {args.max_ratio}: {len(candidates)}")
        print(f"output: {args.output}")
        print(f"candidates output: {args.candidates_output}")
        return

    if args.command == "sec-cik":
        if args.refresh or not args.cache.exists():
            companies = download_company_tickers_exchange(
                args.cache,
                user_agent=args.user_agent or settings.sec_user_agent,
            )
        else:
            companies = load_company_tickers_exchange(args.cache)

        company = find_company_by_ticker(args.ticker, companies)
        if company is None:
            raise SystemExit(f"SEC ticker not found: {args.ticker}")

        print(f"name: {company.name}")
        print(f"ticker: {company.ticker}")
        print(f"exchange: {company.exchange}")
        print(f"cik: {company.cik}")
        print(f"cik10: {company.cik10}")
        print(f"companyfacts: {company.companyfacts_url}")
        print(f"cache: {args.cache}")
        return

    if args.command == "sec-facts":
        if args.refresh_tickers or not args.ticker_cache.exists():
            companies = download_company_tickers_exchange(
                args.ticker_cache,
                user_agent=args.user_agent or settings.sec_user_agent,
            )
        else:
            companies = load_company_tickers_exchange(args.ticker_cache)

        company = find_company_by_ticker(args.ticker, companies)
        if company is None:
            raise SystemExit(f"SEC ticker not found: {args.ticker}")

        facts_path = companyfacts_cache_path(args.facts_dir, company.cik)
        if args.refresh_facts or not facts_path.exists():
            payload = download_companyfacts(
                company.cik,
                facts_path,
                user_agent=args.user_agent or settings.sec_user_agent,
            )
        else:
            payload = load_companyfacts(facts_path)

        print(f"name: {company.name}")
        print(f"ticker: {company.ticker}")
        print(f"exchange: {company.exchange}")
        print(f"cik10: {company.cik10}")
        print(f"companyfacts cache: {facts_path}")
        print("")
        print("financial snapshot:")
        snapshot = build_us_financial_snapshot(payload)
        for key, value in snapshot.items():
            if isinstance(value, float):
                print(f"{key}: {value:,.0f}")
            else:
                print(f"{key}: {value}")
        print("")
        print("core us-gaap tags:")
        for item in summarize_us_gaap_tags(payload):
            status = "yes" if item["available"] else "no"
            value = item["latest_value"]
            value_text = "-" if value is None else f"{float(value):,.0f}"
            print(
                f"{item['tag']}: {status}"
                f" | units={item['units'] or '-'}"
                f" | points={item['points']}"
                f" | latest={value_text}"
                f" | end={item['latest_end'] or '-'}"
                f" | form={item['latest_form'] or '-'}"
            )
        return

    if args.command == "us-screen":
        if args.refresh_tickers or not args.ticker_cache.exists():
            companies = download_company_tickers_exchange(
                args.ticker_cache,
                user_agent=args.user_agent or settings.sec_user_agent,
            )
        else:
            companies = load_company_tickers_exchange(args.ticker_cache)

        market_data = load_us_market_data(args.market_data)
        if not args.no_default_filters:
            market_data = filter_us_screening_universe(market_data)
        financial_cache = (
            load_us_financial_cache(args.financial_cache)
            if not args.no_financial_cache and args.financial_cache.exists() and not args.refresh_facts
            else None
        )
        result = build_us_screener_results(
            market_data,
            companies,
            args.facts_dir,
            refresh_facts=args.refresh_facts,
            user_agent=args.user_agent or settings.sec_user_agent,
            limit=args.limit,
            request_delay_seconds=args.request_delay,
            companyfacts_zip=args.companyfacts_zip,
            financial_cache=financial_cache,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False, encoding="utf-8-sig")
        app_report = save_us_app_report(args.output, args.app_output)

        ok = int((result["data_status"] == "ok").sum()) if "data_status" in result.columns else 0
        errors = int((result["data_status"] == "error").sum()) if "data_status" in result.columns else 0
        print(f"rows: {len(result)}")
        print(f"ok: {ok}")
        print(f"errors: {errors}")
        print(f"market data: {args.market_data}")
        if financial_cache is not None:
            print(f"financial cache: {args.financial_cache}")
        print(f"output: {args.output}")
        print(f"app output: {args.app_output} ({len(app_report)} rows)")
        return

    if args.command == "us-financial-cache":
        if args.refresh_tickers or not args.ticker_cache.exists():
            companies = download_company_tickers_exchange(
                args.ticker_cache,
                user_agent=args.user_agent or settings.sec_user_agent,
            )
        else:
            companies = load_company_tickers_exchange(args.ticker_cache)

        result = build_us_financial_cache(
            companies,
            args.facts_dir,
            refresh_facts=args.refresh_facts,
            user_agent=args.user_agent or settings.sec_user_agent,
            limit=args.limit,
            request_delay_seconds=args.request_delay,
            companyfacts_zip=args.companyfacts_zip,
        )
        save_us_financial_cache(result, args.output)
        ok = int((result["data_status"] == "ok").sum()) if "data_status" in result.columns else 0
        errors = int((result["data_status"] == "error").sum()) if "data_status" in result.columns else 0
        print(f"rows: {len(result)}")
        print(f"ok: {ok}")
        print(f"errors: {errors}")
        print(f"companyfacts zip: {args.companyfacts_zip}")
        print(f"output: {args.output}")
        return

    if args.command == "us-market-data":
        result = download_nasdaq_us_market_data(args.output, limit=args.limit)
        print(f"rows: {len(result)}")
        print(f"output: {args.output}")
        return

    if args.command == "bulk-ncav":
        balance_sheet = args.balance_sheet or find_bulk_file_by_keywords(
            args.input_dir,
            ("2026_1\ubd84\uae30\ubcf4\uace0\uc11c", "\uc7ac\ubb34\uc0c1\ud0dc\ud45c", "\uc5f0\uacb0"),
        )
        market_data = load_market_data(args.market_data)
        if not args.no_default_filters:
            market_data = filter_screening_universe(market_data)

        bulk_ncav = build_ncav_from_bulk_balance_sheet(balance_sheet)
        result = merge_bulk_ncav_with_market_data(bulk_ncav, market_data)
        if args.with_ev_ebit:
            annual_income = [args.annual_income] if args.annual_income else find_income_files_with_separate_fallback(
                args.input_dir,
                ("2025_\uc0ac\uc5c5\ubcf4\uace0\uc11c",),
            )
            previous_q1_income = [args.previous_q1_income] if args.previous_q1_income else find_income_files_with_separate_fallback(
                args.input_dir,
                ("2025_1\ubd84\uae30\ubcf4\uace0\uc11c",),
            )
            current_q1_income = [args.current_q1_income] if args.current_q1_income else find_income_files_with_separate_fallback(
                args.input_dir,
                ("2026_1\ubd84\uae30\ubcf4\uace0\uc11c",),
            )
            ttm_ebit = build_ttm_ebit_from_bulk(
                annual_income,
                previous_q1_income,
                current_q1_income,
            )
            result = add_ev_ebit(result, ttm_ebit)

        if not args.no_fundamentals and args.fundamentals.exists():
            fundamentals = load_fundamentals(args.fundamentals)
            result = merge_fundamentals(result, fundamentals)

        if args.with_f_score:
            current_balance_sheet = args.current_balance_sheet or find_bulk_file_by_keywords(
                args.input_dir,
                ("2026_1\ubd84\uae30\ubcf4\uace0\uc11c", "\uc7ac\ubb34\uc0c1\ud0dc\ud45c", "\uc5f0\uacb0"),
            )
            previous_balance_sheet = args.previous_balance_sheet or find_bulk_file_by_keywords(
                args.input_dir,
                ("2025_1\ubd84\uae30\ubcf4\uace0\uc11c", "\uc7ac\ubb34\uc0c1\ud0dc\ud45c", "\uc5f0\uacb0"),
            )
            f_score_annual_income = [args.annual_income] if args.annual_income else find_income_files_with_separate_fallback(
                args.input_dir,
                ("2025_\uc0ac\uc5c5\ubcf4\uace0\uc11c",),
            )
            current_income = [args.current_income] if args.current_income else find_income_files_with_separate_fallback(
                args.input_dir,
                ("2026_1\ubd84\uae30\ubcf4\uace0\uc11c",),
            )
            previous_income = [args.previous_income] if args.previous_income else find_income_files_with_separate_fallback(
                args.input_dir,
                ("2025_1\ubd84\uae30\ubcf4\uace0\uc11c",),
            )
            current_cash_flow = args.current_cash_flow or find_bulk_file_by_keywords(
                args.input_dir,
                ("2026_1\ubd84\uae30\ubcf4\uace0\uc11c", "\ud604\uae08\ud750\ub984\ud45c", "\uc5f0\uacb0"),
            )
            previous_cash_flow = args.previous_cash_flow or find_bulk_file_by_keywords(
                args.input_dir,
                ("2025_1\ubd84\uae30\ubcf4\uace0\uc11c", "\ud604\uae08\ud750\ub984\ud45c", "\uc5f0\uacb0"),
            )
            f_score = build_f_score_from_bulk(
                current_balance_sheet_path=current_balance_sheet,
                previous_balance_sheet_path=previous_balance_sheet,
                annual_income_path=f_score_annual_income,
                current_income_path=current_income,
                previous_income_path=previous_income,
                current_cash_flow_path=current_cash_flow,
                previous_cash_flow_path=previous_cash_flow,
            )
            result = merge_f_score(result, f_score)

        result.to_csv(args.output, index=False, encoding="utf-8-sig")
        result_with_status = result.assign(status="ok")
        candidates = save_ncav_candidates(result_with_status, args.candidates_output, args.max_ratio)
        value_candidates = save_value_candidates(
            result_with_status,
            args.value_candidates_output,
            max_ncav_ratio=args.max_ratio,
            max_ev_ebit=args.max_ev_ebit,
        )
        korean_report = save_korean_report(args.value_candidates_output, args.korean_output)

        print(f"balance sheet: {balance_sheet}")
        if args.with_ev_ebit:
            print(f"annual income: {annual_income}")
            print(f"previous q1 income: {previous_q1_income}")
            print(f"current q1 income: {current_q1_income}")
        if not args.no_fundamentals and args.fundamentals.exists():
            print(f"fundamentals: {args.fundamentals}")
        if args.with_f_score:
            print(f"f-score current balance sheet: {current_balance_sheet}")
            print(f"f-score previous balance sheet: {previous_balance_sheet}")
            print(f"f-score current income: {current_income}")
            print(f"f-score previous income: {previous_income}")
            print(f"f-score current cash flow: {current_cash_flow}")
            print(f"f-score previous cash flow: {previous_cash_flow}")
        print(f"rows: {len(result)}")
        print(f"candidates <= {args.max_ratio}: {len(candidates)}")
        print(f"value candidates: {len(value_candidates)}")
        print(f"output: {args.output}")
        print(f"candidates output: {args.candidates_output}")
        print(f"value candidates output: {args.value_candidates_output}")
        print(f"korean output: {args.korean_output} ({len(korean_report)} rows)")


if __name__ == "__main__":
    main()

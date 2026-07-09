from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

import pandas as pd


STOCK_CODE_COLUMN = "\uc885\ubaa9\ucf54\ub4dc"
COMPANY_NAME_COLUMN = "\ud68c\uc0ac\uba85"
MARKET_COLUMN = "\uc2dc\uc7a5\uad6c\ubd84"
INDUSTRY_CODE_COLUMN = "\uc5c5\uc885"
INDUSTRY_NAME_COLUMN = "\uc5c5\uc885\uba85"
ACCOUNT_CODE_COLUMN = "\ud56d\ubaa9\ucf54\ub4dc"
ACCOUNT_NAME_COLUMN = "\ud56d\ubaa9\uba85"
CURRENT_PERIOD_COLUMN = "\ub2f9\uae30 1\ubd84\uae30\ub9d0"
ANNUAL_CURRENT_PERIOD_COLUMN = "\ub2f9\uae30"
Q1_CUMULATIVE_COLUMN = "\ub2f9\uae30 1\ubd84\uae30 \ub204\uc801 "

CURRENT_ASSETS_CODE = "ifrs-full_CurrentAssets"
LIABILITIES_CODE = "ifrs-full_Liabilities"
CASH_CODE = "ifrs-full_CashAndCashEquivalents"
OPERATING_INCOME_CODE = "dart_OperatingIncomeLoss"
OTHER_FINANCIAL_LIABILITY_CODES = {
    "ifrs-full_OtherCurrentFinancialLiabilities",
    "ifrs-full_OtherNoncurrentFinancialLiabilities",
}

DEBT_CODES = {
    "ifrs-full_ShorttermBorrowings",
    "ifrs-full_Borrowings",
    "ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
    "ifrs-full_CurrentPortionOfLongtermBorrowings",
    "ifrs-full_CurrentPortionOfBondsIssued",
    "ifrs-full_CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued",
    "ifrs-full_CurrentNotesAndDebenturesIssuedAndCurrentPortionOfNoncurrentNotesAndDebenturesIssued",
    "ifrs-full_CurrentLeaseLiabilities",
    "ifrs-full_LongtermBorrowings",
    "ifrs-full_BondsIssued",
    "ifrs-full_NoncurrentDebtInstrumentsIssued",
    "ifrs-full_NoncurrentLeaseLiabilities",
    "ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued",
    "ifrs-full_NoncurrentPortionOfNoncurrentNotesAndDebenturesIssued",
    "dart_BondWithWarrant",
    "dart_BondWithWarrantNet",
    "dart_ConvertibleBonds",
    "dart_ConvertibleBondsNet",
    "dart_ConvertibleRedeemablePreferredStockLiabilities",
    "dart_ConvertibleRedeemablePreferredStockLiabilitiesNet",
    "dart_CurentPortionOfFinanceLeaseLiabilities",
    "dart_CurrentPortionOfBondWithWarrant",
    "dart_CurrentPortionOfBonds",
    "dart_CurrentPortionOfConvertibleBonds",
    "dart_CurrentPortionOfConvertibleRedeemablePreferredStockLiabilities",
    "dart_CurrentPortionOfExchangeableBond",
    "dart_ExchangeableBonds",
    "dart_ExchangeableBondsNet",
    "dart_NonCurrentFinanceLeaseLiabilities",
}

DEBT_CODE_KEYWORDS = (
    "borrowings",
    "borrowing",
    "loansreceived",
    "loanspayable",
    "longtermdebt",
    "debentures",
    "bondsissued",
    "bondissued",
    "bondspayable",
    "corporatebond",
    "convertiblebond",
    "convertiblebonds",
    "bondwithwarrant",
    "exchangeablebond",
    "leaseabilities",
    "leaseliabilities",
    "leaseliability",
    "financeleaseliabilities",
    "redeemableconvertiblepreferredstockliabilities",
    "convertiblepreferredstockliabilities",
)

DEBT_CODE_EXCLUDE_KEYWORDS = (
    "assets",
    "asset",
    "receivable",
    "receivables",
    "equity",
    "capitalsurplus",
    "rightsadjustment",
    "discount",
    "redemptionpremium",
    "warranty",
    "provision",
    "allowance",
    "securitiesheld",
    "nominalvalue",
    "held",
    "trust",
    "abstract",
)

DEBT_NAME_KEYWORDS = (
    "차입금",
    "사채",
    "전환사채",
    "교환사채",
    "신주인수권부사채",
    "리스부채",
)

DEBT_NAME_EXCLUDE_KEYWORDS = (
    "채권",
    "자산",
    "자본",
    "충당",
    "법인세",
    "매입채무",
    "미지급",
    "평가",
    "할인",
    "상환할증금",
)

INTEREST_BEARING_DEBT_COLUMN = "__interest_bearing_debt__"
OTHER_FINANCIAL_LIABILITIES_COLUMN = "__other_financial_liabilities__"


def is_interest_bearing_debt_code(account_code: object) -> bool:
    if account_code is None or pd.isna(account_code):
        return False

    code = str(account_code)
    if code in DEBT_CODES:
        return True

    normalized = code.replace("_", "").replace("-", "").lower()
    if any(keyword in normalized for keyword in DEBT_CODE_EXCLUDE_KEYWORDS):
        return False
    return any(keyword in normalized for keyword in DEBT_CODE_KEYWORDS)


def is_interest_bearing_debt_account(account_code: object, account_name: object = None) -> bool:
    if is_interest_bearing_debt_code(account_code):
        return True
    if account_name is None or pd.isna(account_name):
        return False

    name = str(account_name).replace(" ", "")
    if any(keyword in name for keyword in DEBT_NAME_EXCLUDE_KEYWORDS):
        return False
    return any(keyword in name for keyword in DEBT_NAME_KEYWORDS)


def read_dart_bulk_statement(path: Path) -> pd.DataFrame:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("cp949", "utf-8-sig", "utf-8", "euc-kr"):
        try:
            return pd.read_csv(path, sep="\t", encoding=encoding, dtype=str)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Could not read DART bulk statement: {path}")


def find_bulk_statement_file(
    input_dir: Path,
    statement_keyword: str,
    consolidated: bool = True,
    exclude_financial: bool = True,
) -> Path:
    files = sorted(input_dir.rglob("*.txt"))
    candidates = []
    for path in files:
        name = path.name
        if statement_keyword not in name:
            continue
        if consolidated and "\uc5f0\uacb0" not in name:
            continue
        if not consolidated and "\uc5f0\uacb0" in name:
            continue
        if exclude_financial and any(keyword in name for keyword in ("\uae08\uc735\uae30\ud0c0", "\ubcf4\ud5d8", "\uc740\ud589", "\uc99d\uad8c")):
            continue
        candidates.append(path)

    if not candidates:
        raise FileNotFoundError(
            f"No bulk statement file found: keyword={statement_keyword}, consolidated={consolidated}"
        )
    if len(candidates) > 1:
        return max(candidates, key=lambda path: path.stat().st_size)
    return candidates[0]


def find_bulk_file_by_keywords(
    input_dir: Path,
    required_keywords: tuple[str, ...],
    exclude_keywords: tuple[str, ...] = ("\uae08\uc735\uae30\ud0c0", "\ubcf4\ud5d8", "\uc740\ud589", "\uc99d\uad8c"),
) -> Path:
    candidates = []
    for path in sorted(input_dir.rglob("*.txt")):
        name = path.name
        if all(keyword in name for keyword in required_keywords) and not any(
            keyword in name for keyword in exclude_keywords
        ):
            candidates.append(path)

    if not candidates:
        raise FileNotFoundError(f"No bulk file found for keywords: {required_keywords}")
    return max(candidates, key=lambda path: path.stat().st_size)


def build_ncav_from_bulk_balance_sheet(path: Path) -> pd.DataFrame:
    raw = read_dart_bulk_statement(path)
    required = {
        STOCK_CODE_COLUMN,
        COMPANY_NAME_COLUMN,
        MARKET_COLUMN,
        INDUSTRY_CODE_COLUMN,
        INDUSTRY_NAME_COLUMN,
        ACCOUNT_CODE_COLUMN,
        CURRENT_PERIOD_COLUMN,
    }
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"DART bulk file is missing columns: {sorted(missing)}")

    frame = raw.copy()
    frame["ticker"] = frame[STOCK_CODE_COLUMN].str.replace(r"[\[\]]", "", regex=True).str.strip()
    frame = frame.loc[frame["ticker"].str.fullmatch(r"\d{6}", na=False)].copy()
    frame["amount"] = frame[CURRENT_PERIOD_COLUMN].map(parse_amount)

    key_codes = {
        CURRENT_ASSETS_CODE,
        LIABILITIES_CODE,
        CASH_CODE,
        *OTHER_FINANCIAL_LIABILITY_CODES,
    }
    debt_mask = frame.apply(
        lambda row: is_interest_bearing_debt_account(row[ACCOUNT_CODE_COLUMN], row[ACCOUNT_NAME_COLUMN]),
        axis=1,
    )
    selected = frame.loc[frame[ACCOUNT_CODE_COLUMN].isin(key_codes) | debt_mask].copy()
    base = selected[
        [
            STOCK_CODE_COLUMN,
            "ticker",
            COMPANY_NAME_COLUMN,
            MARKET_COLUMN,
            INDUSTRY_CODE_COLUMN,
            INDUSTRY_NAME_COLUMN,
        ]
    ].drop_duplicates("ticker")

    pivot = selected.pivot_table(
        index="ticker",
        columns=ACCOUNT_CODE_COLUMN,
        values="amount",
        aggfunc="first",
    )

    debt_by_ticker = selected.loc[
        selected.apply(
            lambda row: is_interest_bearing_debt_account(row[ACCOUNT_CODE_COLUMN], row[ACCOUNT_NAME_COLUMN]),
            axis=1,
        )
    ].groupby("ticker")["amount"].sum(min_count=1)
    other_financial_liabilities = selected.loc[
        selected[ACCOUNT_CODE_COLUMN].isin(OTHER_FINANCIAL_LIABILITY_CODES)
    ].groupby("ticker")["amount"].sum(min_count=1)

    output = (
        base.set_index("ticker")
        .join(pivot, how="left")
        .join(debt_by_ticker.rename(INTEREST_BEARING_DEBT_COLUMN), how="left")
        .join(other_financial_liabilities.rename(OTHER_FINANCIAL_LIABILITIES_COLUMN), how="left")
        .reset_index()
    )
    output = output.rename(
        columns={
            COMPANY_NAME_COLUMN: "name",
            MARKET_COLUMN: "market",
            INDUSTRY_CODE_COLUMN: "industry_code",
            INDUSTRY_NAME_COLUMN: "industry_name",
            CURRENT_ASSETS_CODE: "current_assets",
            LIABILITIES_CODE: "total_liabilities",
            CASH_CODE: "cash_and_equivalents",
        }
    )

    output["interest_bearing_debt"] = output[INTEREST_BEARING_DEBT_COLUMN].fillna(0)
    output["other_financial_liabilities"] = output[OTHER_FINANCIAL_LIABILITIES_COLUMN].fillna(0)

    output["ncav"] = output["current_assets"] - output["total_liabilities"]
    keep = [
        "ticker",
        "name",
        "market",
        "industry_code",
        "industry_name",
        "current_assets",
        "total_liabilities",
        "ncav",
        "cash_and_equivalents",
        "interest_bearing_debt",
        "other_financial_liabilities",
    ]
    return output[keep]


def merge_bulk_ncav_with_market_data(bulk_ncav: pd.DataFrame, market_data: pd.DataFrame) -> pd.DataFrame:
    market = market_data.copy()
    market["ticker"] = market["ticker"].astype(str).str.zfill(6)
    market["market_data_found"] = True
    merged = bulk_ncav.merge(
        market[["ticker", "market_cap", "shares_outstanding", "market_data_found"]],
        on="ticker",
        how="inner",
    )
    merged["market_data_found"] = merged["market_data_found"].astype(bool)
    merged["ncav_per_share"] = merged["ncav"] / merged["shares_outstanding"]
    merged["ncav_ratio"] = merged["market_cap"] / merged["ncav"]
    merged.loc[merged["ncav"] <= 0, "ncav_ratio"] = pd.NA
    return merged


def build_operating_income_from_bulk(path: Path, value_column: str) -> pd.DataFrame:
    raw = read_dart_bulk_statement(path)
    required = {STOCK_CODE_COLUMN, COMPANY_NAME_COLUMN, ACCOUNT_CODE_COLUMN, value_column}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"DART income file is missing columns: {sorted(missing)}")

    frame = raw.loc[raw[ACCOUNT_CODE_COLUMN] == OPERATING_INCOME_CODE].copy()
    frame["ticker"] = frame[STOCK_CODE_COLUMN].str.replace(r"[\[\]]", "", regex=True).str.zfill(6)
    frame["operating_income"] = frame[value_column].map(parse_amount)
    frame = frame.dropna(subset=["operating_income"])
    output = frame[["ticker", COMPANY_NAME_COLUMN, "operating_income"]].rename(
        columns={COMPANY_NAME_COLUMN: "name"}
    )
    return output.sort_values("operating_income", ascending=False).drop_duplicates("ticker")


def build_operating_income_from_bulk_with_fallback(
    paths: Path | Sequence[Path],
    value_column: str,
) -> pd.DataFrame:
    if isinstance(paths, (str, Path)):
        path_list = [Path(paths)]
    else:
        path_list = [Path(path) for path in paths]

    frames = []
    for priority, path in enumerate(path_list):
        frame = build_operating_income_from_bulk(path, value_column).copy()
        frame["source_priority"] = priority
        frame["source_file"] = str(path)
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["ticker", "name", "operating_income", "source_file"])

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["ticker", "source_priority"])
    combined = combined.drop_duplicates("ticker", keep="first")
    return combined.drop(columns=["source_priority"])


def build_ttm_ebit_from_bulk(
    annual_income_path: Path | Sequence[Path],
    previous_q1_income_path: Path | Sequence[Path],
    current_q1_income_path: Path | Sequence[Path],
) -> pd.DataFrame:
    annual = build_operating_income_from_bulk_with_fallback(
        annual_income_path,
        ANNUAL_CURRENT_PERIOD_COLUMN,
    ).rename(columns={"operating_income": "operating_income_annual", "source_file": "operating_income_annual_source"})
    previous_q1 = build_operating_income_from_bulk_with_fallback(
        previous_q1_income_path,
        Q1_CUMULATIVE_COLUMN,
    ).rename(columns={"operating_income": "operating_income_previous_q1", "source_file": "operating_income_previous_q1_source"})
    current_q1 = build_operating_income_from_bulk_with_fallback(
        current_q1_income_path,
        Q1_CUMULATIVE_COLUMN,
    ).rename(columns={"operating_income": "operating_income_current_q1", "source_file": "operating_income_current_q1_source"})

    merged = annual.merge(
        previous_q1[["ticker", "operating_income_previous_q1", "operating_income_previous_q1_source"]],
        on="ticker",
        how="outer",
    )
    merged = merged.merge(
        current_q1[["ticker", "operating_income_current_q1", "operating_income_current_q1_source"]],
        on="ticker",
        how="outer",
    )
    merged["ebit_ttm"] = (
        merged["operating_income_annual"]
        - merged["operating_income_previous_q1"]
        + merged["operating_income_current_q1"]
    )
    return merged


def add_ev_ebit(results: pd.DataFrame, ttm_ebit: pd.DataFrame) -> pd.DataFrame:
    output = results.merge(
        ttm_ebit[
            [
                "ticker",
                "operating_income_annual",
                "operating_income_previous_q1",
                "operating_income_current_q1",
                "operating_income_annual_source",
                "operating_income_previous_q1_source",
                "operating_income_current_q1_source",
                "ebit_ttm",
            ]
        ],
        on="ticker",
        how="left",
    )
    output["ev"] = (
        output["market_cap"]
        + output["interest_bearing_debt"].fillna(0)
        - output["cash_and_equivalents"].fillna(0)
    )
    output["ev_ebit"] = output["ev"] / output["ebit_ttm"]
    output["conservative_ev"] = output["ev"] + output["other_financial_liabilities"].fillna(0)
    output["conservative_ev_ebit"] = output["conservative_ev"] / output["ebit_ttm"]
    output.loc[output["ebit_ttm"] <= 0, "ev_ebit"] = pd.NA
    output.loc[output["ebit_ttm"] <= 0, "conservative_ev_ebit"] = pd.NA
    return output


def parse_amount(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).replace(",", "").strip()
    if not text or text == "-":
        return None
    return float(text)

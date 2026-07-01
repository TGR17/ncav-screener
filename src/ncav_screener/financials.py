from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable


ACCOUNT_NAME_CANDIDATES = {
    "current_assets": [
        "유동자산",
        "Current assets",
    ],
    "total_liabilities": [
        "부채총계",
        "부채 총계",
        "Total liabilities",
    ],
    "cash_and_equivalents": [
        "현금및현금성자산",
        "현금 및 현금성자산",
        "Cash and cash equivalents",
    ],
    "operating_income": [
        "영업이익",
        "영업이익(손실)",
        "Operating income",
        "Profit (loss) from operations",
    ],
}

INTEREST_BEARING_DEBT_CANDIDATES = [
    "단기차입금",
    "유동성장기차입금",
    "유동성사채",
    "유동성리스부채",
    "장기차입금",
    "사채",
    "리스부채",
    "Short-term borrowings",
    "Current portion of long-term borrowings",
    "Current portion of bonds",
    "Lease liabilities",
    "Long-term borrowings",
    "Bonds issued",
]


def parse_dart_amount(value: str | int | float | None) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text or text == "-":
        return None
    try:
        return float(Decimal(text))
    except InvalidOperation:
        return None


def find_account_amount(
    rows: Iterable[dict],
    account_names: Iterable[str],
    field: str = "thstrm_amount",
) -> float | None:
    wanted = {normalize_account_name(name) for name in account_names}
    for row in rows:
        row_name = normalize_account_name(str(row.get("account_nm", "")))
        if row_name in wanted:
            return parse_dart_amount(row.get(field))
    return None


def find_account_amounts(
    rows: Iterable[dict],
    account_names: Iterable[str],
    field: str = "thstrm_amount",
) -> list[tuple[str, float]]:
    wanted = {normalize_account_name(name) for name in account_names}
    matches = []
    for row in rows:
        account_name = str(row.get("account_nm", ""))
        row_name = normalize_account_name(account_name)
        if row_name in wanted:
            amount = parse_dart_amount(row.get(field))
            if amount is not None:
                matches.append((account_name, amount))
    return matches


def normalize_account_name(name: str) -> str:
    return "".join(name.split()).lower()


def extract_standard_accounts(rows: Iterable[dict]) -> dict[str, float | None]:
    row_list = list(rows)
    return {
        key: find_account_amount(row_list, names)
        for key, names in ACCOUNT_NAME_CANDIDATES.items()
    }


def extract_interest_bearing_debt(rows: Iterable[dict]) -> tuple[float, list[tuple[str, float]]]:
    matches = find_account_amounts(rows, INTEREST_BEARING_DEBT_CANDIDATES)
    return sum(amount for _, amount in matches), matches

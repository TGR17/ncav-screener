from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd


def parse_corp_code_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        xml_name = next(name for name in archive.namelist() if name.lower().endswith(".xml"))
        xml_bytes = archive.read(xml_name)

    root = ElementTree.fromstring(xml_bytes)
    rows = []
    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        if not stock_code:
            continue
        rows.append(
            {
                "corp_code": (item.findtext("corp_code") or "").strip(),
                "corp_name": (item.findtext("corp_name") or "").strip(),
                "stock_code": stock_code,
                "modify_date": (item.findtext("modify_date") or "").strip(),
            }
        )
    return pd.DataFrame(rows)


def find_corp_by_stock_code(corp_codes: pd.DataFrame, stock_code: str) -> pd.Series:
    matches = corp_codes.loc[corp_codes["stock_code"] == stock_code]
    if matches.empty:
        raise LookupError(f"No DART corp code found for stock code: {stock_code}")
    if len(matches) > 1:
        matches = matches.sort_values("modify_date", ascending=False)
    return matches.iloc[0]

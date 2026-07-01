from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests


DART_BASE_URL = "https://opendart.fss.or.kr/api"


@dataclass(frozen=True)
class DartClient:
    api_key: str
    timeout: int = 20

    def get_financial_statement(
        self,
        corp_code: str,
        business_year: int,
        report_code: str,
        fs_div: str = "CFS",
    ) -> dict:
        response = requests.get(
            f"{DART_BASE_URL}/fnlttSinglAcntAll.json",
            params={
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": str(business_year),
                "reprt_code": report_code,
                "fs_div": fs_div,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") not in {"000", "013"}:
            raise RuntimeError(f"DART API error: {payload.get('status')} {payload.get('message')}")
        return payload

    def get_financial_statement_with_fallback(
        self,
        corp_code: str,
        business_year: int,
        report_code: str,
    ) -> tuple[dict, str]:
        for fs_div in ("CFS", "OFS"):
            payload = self.get_financial_statement(
                corp_code=corp_code,
                business_year=business_year,
                report_code=report_code,
                fs_div=fs_div,
            )
            if payload.get("status") == "000" and payload.get("list"):
                return payload, fs_div
        return payload, fs_div

    def download_corp_code_zip(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(
            f"{DART_BASE_URL}/corpCode.xml",
            params={"crtfc_key": self.api_key},
            timeout=self.timeout,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "zip" not in content_type and not response.content.startswith(b"PK"):
            text = response.text[:500]
            raise RuntimeError(f"Unexpected DART corp code response: {text}")

        output_path.write_bytes(response.content)
        return output_path

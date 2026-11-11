"""Adapters for official exchange catalogs and disclosure pages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "financial-report-agent-research/0.1 (+local academic project)"


@dataclass(frozen=True)
class ExchangeCompany:
    code: str
    name: str
    industry: str
    exchange: str


@dataclass(frozen=True)
class ExchangeAdapter:
    name: str
    catalog_url: str
    disclosure_endpoint: str
    allowed_domains: tuple[str, ...]

    def disclosure_url(self, code: str) -> str:
        return f"{self.disclosure_endpoint}?{urlencode({'symbol': code})}"


# Isolate exchange-specific URLs here; no manual candidate catalog is used.
EXCHANGES = {
    "HOSE": ExchangeAdapter("HOSE", "https://api.hsx.vn/l/api/v1/securities/list", "https://api.hsx.vn/n/api/v1/news/securities", ("hsx.vn",)),
    "HNX": ExchangeAdapter("HNX", "https://www.hnx.vn/vi-vn/cophieu-etfs.html", "https://www.hnx.vn/vi-vn/cong-bo-thong-tin.html", ("hnx.vn",)),
    "UPCOM": ExchangeAdapter("UPCOM", "https://www.hnx.vn/vi-vn/co-phieu-upcom.html", "https://www.hnx.vn/vi-vn/cong-bo-thong-tin.html", ("hnx.vn",)),
}


def _first(item: dict[str, Any], *names: str) -> str:
    return next((str(item[name]).strip() for name in names if item.get(name) is not None and str(item[name]).strip()), "")


def _records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("items", "data", "rows", "content", "result"):
            records = _records(value.get(key))
            if records:
                return records
    return []


def fetch_catalog(adapter: ExchangeAdapter, catalog_url: str | None = None, timeout: int = 30) -> list[ExchangeCompany]:
    """Read an official JSON catalog; endpoint overrides avoid manual files."""
    url = catalog_url or adapter.catalog_url
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}), timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8-sig"))
    companies = []
    for record in _records(payload):
        code = _first(record, "symbol", "code", "stockCode", "secCode", "ticker").upper()
        name = _first(record, "companyName", "name", "issuerName", "organizationName")
        industry = _first(record, "industry", "industryName", "sector", "sectorName")
        if code and name and industry:
            companies.append(ExchangeCompany(code, name, industry, adapter.name))
    if not companies:
        raise ValueError(f"{adapter.name} catalog returned no code/name/industry records: {url}. Supply its current official JSON endpoint with --catalog-url.")
    return companies

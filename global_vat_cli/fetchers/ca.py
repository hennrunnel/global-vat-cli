from typing import Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from . import BaseFetcher


class CanadaFetcher(BaseFetcher):
    name = "Canada (CRA)"
    source_url = "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/gst-hst-rates.html"
    fallback_urls = [
        # Historic/alternate CRA pages listing province rates
        "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/charge-collect-which-rate.html",
        # Bypass scripts feature flag occasionally helps
        "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/gst-hst-rates.html?wbdisable=true",
    ]
    search_url = "https://www.canada.ca/en/sr/srb.html?q=gst+hst+rates"

    def fetch(self) -> List[Dict]:
        try:
            # CRA authoritative GST/HST summary page (stable URL) with UA and retries
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                "Accept-Language": "en-CA,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            session = requests.Session()
            retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            tried_urls = [self.source_url] + self.fallback_urls
            soup = None
            for url in tried_urls:
                resp = session.get(url, headers=headers, timeout=30, allow_redirects=True)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                self._last_url = url  # type: ignore[attr-defined]
                break
            if soup is None:
                # Try official search to discover the current page
                sr = session.get(self.search_url, headers=headers, timeout=30, allow_redirects=True)
                if sr.ok:
                    s_soup = BeautifulSoup(sr.text, "lxml")
                    target = None
                    for a in s_soup.find_all("a", href=True):
                        href = a["href"]
                        if (
                            "canada.ca" in href
                            and "revenue-agency" in href
                            and "gst" in href.lower()
                            and "hst" in href.lower()
                            and "rate" in href.lower()
                        ):
                            target = href
                            break
                    if target:
                        resp = session.get(target, headers=headers, timeout=30, allow_redirects=True)
                        resp.raise_for_status()
                        soup = BeautifulSoup(resp.text, "lxml")
                        self._last_url = target  # type: ignore[attr-defined]
                if soup is None:
                    # Fall back to authoritative static mapping (from CRA) for dry-run/continuity
                    import os as _os
                    if _os.environ.get("VATCLI_DRY_RUN") == "1" or _os.environ.get("VATCLI_ALLOW_FALLBACKS") == "1":
                        return _fallback_from_static()
                    return []
        except Exception:
            import os as _os
            if _os.environ.get("VATCLI_DRY_RUN") == "1" or _os.environ.get("VATCLI_ALLOW_FALLBACKS") == "1":
                return _fallback_from_static()
            return []
        results: List[Dict] = []

        province_map = {
            "Alberta": ("CA-AB", "GST"),
            "Ontario": ("CA-ON", "HST"),
            "British Columbia": ("CA-BC", "GST"),
            "Manitoba": ("CA-MB", "GST"),
            "New Brunswick": ("CA-NB", "HST"),
            "Newfoundland and Labrador": ("CA-NL", "HST"),
            "Nova Scotia": ("CA-NS", "HST"),
            "Prince Edward Island": ("CA-PE", "HST"),
            "Quebec": ("CA-QC", "GST"),
            "Saskatchewan": ("CA-SK", "GST"),
            "Northwest Territories": ("CA-NT", "GST"),
            "Nunavut": ("CA-NU", "GST"),
            "Yukon": ("CA-YT", "GST"),
        }

        # Find province rate list items or table rows; CRA page typically has a list or table of provinces with rates
        text = soup.get_text(" ")
        for prov, (region_code, tax_type) in province_map.items():
            # Look for patterns like "Ontario (HST) 13%" or "Ontario – 13%"
            rate = _extract_rate_for_province(text, prov)
            if rate is None:
                continue
            results.append(
                {
                    "region_code": region_code,
                    "country_iso": "CA",
                    "country_name": "Canada",
                    "jurisdiction_level": "Province",
                    "jurisdiction_name": prov,
                    "tax_authority_name": "Canada Revenue Agency",
                    "tax_authority_url": getattr(self, "_last_url", self.source_url),
                    "tax_type": tax_type,
                    "rate_type": "Standard",
                    "rate_percent": rate,
                    "category_source_label": "Standard",
                    "primary_source_url": getattr(self, "_last_url", self.source_url),
                }
            )
        # Add nationwide zero-rated categories where applicable (mapped to provinces for UI consistency)
        zero_labels = ["Foodstuffs", "Pharmaceutical Products", "Medical Equipment", "Books"]
        for prov, (region_code, tax_type) in province_map.items():
            for zl in zero_labels:
                results.append(
                    {
                        "region_code": region_code,
                        "country_iso": "CA",
                        "country_name": "Canada",
                        "jurisdiction_level": "Province",
                        "jurisdiction_name": prov,
                        "tax_authority_name": "Canada Revenue Agency",
                        "tax_authority_url": getattr(self, "_last_url", self.source_url),
                        "tax_type": tax_type,
                        "rate_type": "Zero",
                        "rate_percent": 0.0,
                        "category_source_label": zl,
                        "primary_source_url": getattr(self, "_last_url", self.source_url),
                    }
                )
        return results


def _extract_rate_for_province(text: str, province: str) -> float:
    # Simple heuristic: find the province name and capture the nearest percentage within the next 40 chars
    idx = text.find(province)
    if idx == -1:
        return None  # type: ignore
    window = text[idx : idx + 160]
    import re

    m = re.search(r"(\d{1,2}(?:[\.,]\d)?)\s*%", window)
    if not m:
        return None  # type: ignore
    try:
        return float(m.group(1).replace(",", "."))
    except Exception:
        return None  # type: ignore


# Static fallback derived from regional-vat-datasets (authoritative CRA values)
PROVINCE_GST_HST = [
    ("Alberta", "CA-AB", "GST", 5.0),
    ("British Columbia", "CA-BC", "GST", 5.0),
    ("Manitoba", "CA-MB", "GST", 5.0),
    ("New Brunswick", "CA-NB", "HST", 15.0),
    ("Newfoundland and Labrador", "CA-NL", "HST", 15.0),
    ("Nova Scotia", "CA-NS", "HST", 15.0),
    ("Northwest Territories", "CA-NT", "GST", 5.0),
    ("Nunavut", "CA-NU", "GST", 5.0),
    ("Ontario", "CA-ON", "HST", 13.0),
    ("Prince Edward Island", "CA-PE", "HST", 15.0),
    ("Quebec", "CA-QC", "GST", 5.0),
    ("Saskatchewan", "CA-SK", "GST", 5.0),
    ("Yukon", "CA-YT", "GST", 5.0),
]


def _fallback_from_static() -> List[Dict]:
    out: List[Dict] = []
    for prov, region_code, tax_type, rate in PROVINCE_GST_HST:
        out.append(
            {
                "region_code": region_code,
                "country_iso": "CA",
                "country_name": "Canada",
                "jurisdiction_level": "Province",
                "jurisdiction_name": prov,
                "tax_authority_name": "Canada Revenue Agency",
                "tax_authority_url": "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/gst-hst-rates.html",
                "tax_type": tax_type,
                "rate_type": "Standard",
                "rate_percent": rate,
                "category_source_label": "Standard",
                "primary_source_url": "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/gst-hst-rates.html",
            }
        )
        for zl in ["Basic Groceries", "Prescription Drugs", "Medical Devices", "Books"]:
            out.append(
                {
                    "region_code": region_code,
                    "country_iso": "CA",
                    "country_name": "Canada",
                    "jurisdiction_level": "Province",
                    "jurisdiction_name": prov,
                    "tax_authority_name": "Canada Revenue Agency",
                    "tax_authority_url": "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/gst-hst-rates.html",
                    "tax_type": tax_type,
                    "rate_type": "Zero",
                    "rate_percent": 0.0,
                    "category_source_label": zl,
                    "primary_source_url": "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/gst-hst-rates.html",
                }
            )
    return out



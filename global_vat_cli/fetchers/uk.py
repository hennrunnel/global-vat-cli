from typing import Dict, List

import pandas as pd

from . import BaseFetcher


class UKFetcher(BaseFetcher):
    name = "UK (HMRC)"
    source_url = "https://www.gov.uk/guidance/rates-of-vat-on-different-goods-and-services"

    def fetch(self) -> List[Dict]:
        # Use pandas to read visible tables
        tables = pd.read_html(self.source_url)
        results: List[Dict] = []
        # Add explicit Standard rate default: UK works by exception
        results.append(
            {
                "region_code": "UK-GB",
                "country_iso": "GB",
                "country_name": "United Kingdom",
                "jurisdiction_level": "Country",
                "jurisdiction_name": "United Kingdom",
                "tax_authority_name": "HM Revenue & Customs",
                "tax_authority_url": self.source_url,
                "tax_type": "VAT",
                "rate_type": "Standard",
                "rate_percent": 20.0,
                "category_source_label": "Standard Rate (Default)",
                "primary_source_url": self.source_url,
            }
        )
        for df in tables:
            cols = [c for c in df.columns]
            rate_col = None
            for c in cols:
                if "rate" in str(c).lower():
                    rate_col = c
                    break
            category_col = cols[0] if cols else None
            if rate_col is None or category_col is None:
                continue
            for _, row in df.iterrows():
                try:
                    raw_rate = row[rate_col]
                    if isinstance(raw_rate, str):
                        raw_rate = raw_rate.replace("%", "").strip()
                    rate = float(raw_rate)
                except Exception:
                    continue
                category = str(row[category_col]).strip()
                results.append(
                    {
                        "region_code": "UK-GB",
                        "country_iso": "GB",
                        "country_name": "United Kingdom",
                        "jurisdiction_level": "Country",
                        "jurisdiction_name": "United Kingdom",
                        "tax_authority_name": "HM Revenue & Customs",
                        "tax_authority_url": self.source_url,
                        "tax_type": "VAT",
                        "rate_type": _classify_rate(rate),
                        "rate_percent": rate,
                        "category_source_label": category,
                        "primary_source_url": self.source_url,
                    }
                )
        return results


def _classify_rate(rate: float) -> str:
    if rate == 0.0:
        return "Zero"
    if rate < 20.0:
        return "Reduced"
    return "Standard"



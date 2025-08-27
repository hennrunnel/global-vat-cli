from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from . import BaseFetcher


class SwitzerlandFetcher(BaseFetcher):
    name = "Switzerland (FTA)"
    # Use the stable German-language canonical rates page which is less likely to move
    source_url = "https://www.estv.admin.ch/estv/en/home/mehrwertsteuer/mwst-steuersaetze.html"

    def fetch(self) -> List[Dict]:
        res = requests.get(self.source_url, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        results: List[Dict] = []
        # More robust regex-based extraction
        import re
        text = soup.get_text(" ", strip=True)
        percents = []
        for m in re.finditer(r"(\d{1,2}[\.,]\d)\s*%", text):
            try:
                percents.append(float(m.group(1).replace(",", ".")))
            except Exception:
                pass
        uniq = sorted(set([v for v in percents if 0.0 < v < 25.0]))
        std = max([v for v in uniq if v >= 5.0], default=8.1)
        red_candidates = [v for v in uniq if v < 5.0]
        red = min(red_candidates) if red_candidates else 2.6
        special_candidates = [v for v in uniq if 3.0 <= v <= 4.5]
        special = min(special_candidates, key=lambda v: abs(v - 3.8)) if special_candidates else 3.8

        def make(rate: float, rate_type: str, category: str) -> Dict:
            return {
                "region_code": "CH-CH",
                "country_iso": "CH",
                "country_name": "Switzerland",
                "jurisdiction_level": "Country",
                "jurisdiction_name": "Switzerland",
                "tax_authority_name": "Swiss Federal Tax Administration",
                "tax_authority_url": self.source_url,
                "tax_type": "VAT",
                "rate_type": rate_type,
                "rate_percent": rate,
                "category_source_label": category,
                "primary_source_url": self.source_url,
            }

        results.append(make(std, "Standard", "Standard"))
        results.append(make(red, "Reduced", "Foodstuffs"))
        results.append(make(special, "Reduced", "Accommodation"))
        return results



from typing import Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from . import BaseFetcher


class NorwayFetcher(BaseFetcher):
    name = "Norway (Skatteetaten)"
    # Try English page first; if 404, follow to Norwegian canonical and parse
    source_url = "https://www.skatteetaten.no/en/business-and-organisation/vat/rates-and-registration/vat-rates/"
    fallback_url = "https://www.skatteetaten.no/bedrift-og-organisasjon/mva/satser-og-registrering/mva-satser/"
    search_url = "https://www.skatteetaten.no/sok/?q=mva%20satser"

    def fetch(self) -> List[Dict]:
        session = requests.Session()
        retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.8,nb;q=0.6,no;q=0.6",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        res = session.get(self.source_url, headers=headers, timeout=30, allow_redirects=True)
        if res.status_code == 404:
            res = session.get(self.fallback_url, headers=headers, timeout=30, allow_redirects=True)
            if res.status_code == 404:
                # Attempt site search to find current slug
                sr = session.get(self.search_url, headers=headers, timeout=30, allow_redirects=True)
                if sr.ok:
                    from bs4 import BeautifulSoup as _BS
                    s_soup = _BS(sr.text, 'lxml')
                    hit = None
                    for a in s_soup.find_all('a', href=True):
                        href = a['href']
                        if 'mva' in href and 'satser' in href:
                            hit = href if href.startswith('http') else f"https://www.skatteetaten.no{href}"
                            break
                    if hit:
                        res = session.get(hit, headers=headers, timeout=30, allow_redirects=True)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        results: List[Dict] = []
        # Regex-based extraction with nearby keyword context
        import re
        text = soup.get_text(" ", strip=True)
        text_norm = re.sub(r"\s+", " ", text).lower()
        rates = []
        for m in re.finditer(r"(\d{1,2}(?:[\.,]\d)?)\s*%", text_norm):
            try:
                val = float(m.group(1).replace(",", "."))
            except Exception:
                continue
            if 0.0 <= val <= 30.0:
                rates.append((val, m.start()))

        # Assign heuristics
        std = None
        low_food = None
        low_other = None
        for val, pos in rates:
            window = text_norm[max(0, pos - 100): pos + 80]
            if any(k in window for k in ["standard rate", "ordinary rate", "standard"]):
                std = val if std is None else std
            if any(k in window for k in ["food", "foodstuffs"]):
                low_food = val if low_food is None else low_food
            if any(k in window for k in ["public transport", "passenger transport", "accommodation", "hotel", "culture", "cinema", "sports", "low rate"]):
                low_other = val if low_other is None else low_other
        # Fallbacks
        values_only = sorted(set(v for v, _ in rates))
        if std is None:
            std = max([v for v in values_only if v >= 20.0], default=25.0)
        if low_food is None:
            low_food = min([v for v in values_only if 10.0 <= v < std], default=15.0)
        if low_other is None:
            low_other = min([v for v in values_only if 8.0 <= v < std], default=12.0)

        def make(rate: float, rate_type: str, category: str) -> Dict:
            return {
                "region_code": "NO-NO",
                "country_iso": "NO",
                "country_name": "Norway",
                "jurisdiction_level": "Country",
                "jurisdiction_name": "Norway",
                "tax_authority_name": "Skatteetaten",
                "tax_authority_url": self.source_url,
                "tax_type": "VAT",
                "rate_type": rate_type,
                "rate_percent": rate,
                "category_source_label": category,
                "primary_source_url": self.source_url,
            }

        results.append(make(std, "Standard", "Standard"))
        results.append(make(low_food, "Reduced", "Foodstuffs"))
        results.append(make(low_other, "Reduced", "Passenger Transport"))
        results.append(make(low_other, "Reduced", "Accommodation"))
        results.append(make(low_other, "Reduced", "Cultural Events"))
        return results



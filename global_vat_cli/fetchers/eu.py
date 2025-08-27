from typing import Dict, List, Any, Optional

from zeep import Client  # network used only at runtime, not in unit tests
from zeep.helpers import serialize_object

from . import BaseFetcher


class EUFetcher(BaseFetcher):
    name = "EU (European Commission TEDB)"
    source_url = "https://ec.europa.eu/taxation_customs/tedb/ws/VatRetrievalService.wsdl"

    def fetch(self) -> List[Dict]:
        client = Client(self.source_url)
        svc = client.service
        try:
            # Retrieve rates from the last known window; pass args via kwargs to keep 'from' key
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc).date().isoformat()
            # First try snapshot on today's date
            req = {"memberStates": {"isoCode": EU_STATES}, "from": "2020-01-01", "situationOn": today}
            try:
                res = svc.retrieveVatRates(**req)  # type: ignore
            except Exception:
                # Fallback to range [from, to]
                req = {"memberStates": {"isoCode": EU_STATES}, "from": "2020-01-01", "to": today}
                res = svc.retrieveVatRates(**req)  # type: ignore
            doc = serialize_object(res)
        except Exception:
            doc = {}
        return map_tedb_doc_to_records(doc, self.source_url)


EU_STATES = [
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"
]


def _label_for(item: Dict[str, Any]) -> str:
    rate = (item.get("rate") or {}).get("type") or ""
    cat = item.get("category") or {}
    identifier = str(cat.get("identifier", "")).strip()
    description = str(cat.get("description", "")).strip()
    if str(rate).upper() == "STANDARD_RATE":
        return "Standard"
    if identifier:
        return identifier.replace("_", " ").title()
    if description:
        return description
    t = str(item.get("type", "")).title()
    return t or "Rate"


def _rate_type_for(rate_type_raw: Optional[str], value: float) -> str:
    rt = (rate_type_raw or "").upper().replace(" ", "_")
    if value == 0.0:
        return "Zero"
    if rt in {"STANDARD_RATE", "STANDARD"}:
        return "Standard"
    # Map all other non-zero types to Reduced
    return "Reduced"


def map_tedb_doc_to_records(doc: Dict[str, Any], source_url: str) -> List[Dict]:
    results = doc.get("vatRateResults", []) or []
    by_state: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for item in results:
        iso2 = str(item.get("memberState", "")).upper()
        if not iso2:
            continue
        try:
            value = float(((item.get("rate") or {}).get("value")))
        except Exception:
            continue
        if value < 0 or value > 50:
            continue
        label = _label_for(item)
        date_s = (item.get("situationOn") or "")
        state_map = by_state.setdefault(iso2, {})
        prev = state_map.get(label)
        if prev is None or date_s > prev.get("_date", ""):
            state_map[label] = {"_date": date_s, "value": value, "rate_type": (item.get("rate") or {}).get("type")}

    out: List[Dict] = []
    for iso2, cats in by_state.items():
        country_iso = "GR" if iso2 == "EL" else iso2
        country_name = ISO2_TO_COUNTRY.get(country_iso, country_iso)
        for label, entry in cats.items():
            value = float(entry.get("value", 0.0))
            rate_type = _rate_type_for(entry.get("rate_type"), value)
            out.append(
                {
                    "region_code": f"EU-{country_iso}",
                    "country_iso": country_iso,
                    "country_name": country_name,
                    "jurisdiction_level": "Country",
                    "jurisdiction_name": country_name,
                    "tax_authority_name": "European Commission (TEDB)",
                    "tax_authority_url": "https://ec.europa.eu/taxation_customs/tedb/#/home",
                    "tax_type": "VAT",
                    "rate_type": rate_type,
                    "rate_percent": value,
                    "category_source_label": label,
                    "primary_source_url": source_url,
                }
            )
    return out


ISO2_TO_COUNTRY = {
    'AT': 'Austria','BE':'Belgium','BG':'Bulgaria','HR':'Croatia','CY':'Cyprus','CZ':'Czech Republic','DK':'Denmark',
    'EE':'Estonia','FI':'Finland','FR':'France','DE':'Germany','EL':'Greece','GR':'Greece','HU':'Hungary','IE':'Ireland',
    'IT':'Italy','LV':'Latvia','LT':'Lithuania','LU':'Luxembourg','MT':'Malta','NL':'Netherlands','PL':'Poland','PT':'Portugal',
    'RO':'Romania','SK':'Slovakia','SI':'Slovenia','ES':'Spain','SE':'Sweden'
}


# Back-compat helper used in tests: parses a simplified list of SOAP-like items
def parse_eu_items(items: List[object], source_url: str) -> List[Dict]:
    out: List[Dict] = []
    for item in items:
        country_iso = getattr(item, "countryCode", "") or getattr(item, "memberState", "")
        country_iso = "GR" if str(country_iso).upper() in ("EL",) else str(country_iso).upper()
        country_name = ISO2_TO_COUNTRY.get(country_iso, country_iso)
        category = getattr(item, "goodsCategory", None) or getattr(item, "category", None) or "Standard"
        if hasattr(category, "get"):
            category = (category.get("identifier") or category.get("description") or "Standard")  # type: ignore
        rate_type_raw = getattr(item, "rateType", None) or (getattr(item, "rate", None) or {}).get("type")
        rate_val = getattr(item, "rate", None)
        if isinstance(rate_val, dict):
            rate_val = rate_val.get("value")
        try:
            value = float(rate_val or 0.0)
        except Exception:
            value = 0.0
        rate_type = _rate_type_for(str(rate_type_raw) if rate_type_raw else None, value)
        out.append(
            {
                "region_code": f"EU-{country_iso}",
                "country_iso": country_iso,
                "country_name": country_name,
                "jurisdiction_level": "Country",
                "jurisdiction_name": country_name,
                "tax_authority_name": "European Commission (TEDB)",
                "tax_authority_url": "https://ec.europa.eu/taxation_customs/tedb/#/home",
                "tax_type": "VAT",
                "rate_type": rate_type,
                "rate_percent": value,
                "category_source_label": str(category),
                "primary_source_url": source_url,
            }
        )
    return out



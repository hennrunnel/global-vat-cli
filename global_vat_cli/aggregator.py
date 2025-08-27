from collections import defaultdict
from typing import Dict, List

from .normalizer import map_category
from .schema import DataRecord


def assemble_records(raw_records: List[Dict], timestamp_utc: str) -> List[DataRecord]:
    normalized: List[DataRecord] = []
    for rec in raw_records:
        ui_label = map_category(rec.get("category_source_label", ""))
        normalized.append(
            DataRecord(
                region_code=rec["region_code"],
                country_iso=rec["country_iso"],
                country_name=rec["country_name"],
                jurisdiction_level=rec.get("jurisdiction_level", "Country"),
                jurisdiction_name=rec.get("jurisdiction_name", rec["country_name"]),
                tax_authority_name=rec["tax_authority_name"],
                tax_authority_url=rec["tax_authority_url"],
                tax_type=rec["tax_type"],
                rate_type=rec["rate_type"],
                rate_percent=float(rec["rate_percent"]),
                category_source_label=rec.get("category_source_label", "Standard"),
                category_ui_label=ui_label,
                primary_source_url=rec["primary_source_url"],
                last_validated_utc=timestamp_utc,
            )
        )

    # Safe default: highest reduced rate when multiple reduced rates exist per country/category
    key_to_best: Dict[tuple, DataRecord] = {}
    for item in normalized:
        if item.rate_type.lower() != "reduced":
            # Keep all non-reduced entries as-is
            key = (
                item.country_iso,
                item.category_ui_label,
                item.rate_type,
                item.region_code,
            )
            if key not in key_to_best:
                key_to_best[key] = item
            else:
                # If duplicate non-reduced entries, keep the highest rate as a conservative default
                if item.rate_percent > key_to_best[key].rate_percent:
                    key_to_best[key] = item
            continue

        key = (item.country_iso, item.category_ui_label, "Reduced", item.region_code)
        if key not in key_to_best:
            key_to_best[key] = item
        else:
            if item.rate_percent > key_to_best[key].rate_percent:
                key_to_best[key] = item

    return list(key_to_best.values())



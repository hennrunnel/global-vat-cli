import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .schema import DataRecord


def write_json(records: List[DataRecord], out_path: str) -> None:
    data = [r.model_dump() for r in records]
    Path(out_path).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {len(records)} records to {out_path}")


def write_readme(records: List[DataRecord], out_path: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    lines: List[str] = []
    lines.append("Global VAT/GST Dataset for E-commerce")
    lines.append(f"Last Updated: {now}")
    lines.append("Context: Public datasets that feed Voog's multi-VAT support.")
    lines.append("This document contains VAT/GST rates for physical goods, compiled from official government sources.")
    lines.append("")
    lines.append("Summary of Primary Sources")
    lines.append("Country | Tax Authority | Official Source URL")
    lines.append("--- | --- | ---")
    lines.append("European Union | European Commission | https://ec.europa.eu/taxation_customs/tedb/#/home")
    lines.append("United Kingdom | HM Revenue & Customs | https://www.gov.uk/guidance/rates-of-vat-on-different-goods-and-services")
    lines.append("Canada | Canada Revenue Agency | https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst/charge-collect-which-rate.html")
    lines.append("Switzerland | Swiss Federal Tax Administration | https://www.estv.admin.ch/estv/en/home/value-added-tax/vat-rates-switzerland.html")
    lines.append("Norway | Skatteetaten | https://www.skatteetaten.no/en/business-and-organisation/vat/rates-and-registration/vat-rates/")
    lines.append("")

    lines.append("Normalized Tax Categories")
    lines.append("UI Label | Description")
    lines.append("--- | ---")
    lines.append("Standard Rate | Default VAT/GST rate when no reduced/zero applies")
    lines.append("Food & Groceries | Foodstuffs for human consumption, seeds, plants, etc.")
    lines.append("Books & Publications | Physical books, newspapers, and periodicals.")
    lines.append("Pharmaceuticals & Medical Goods | Medicines, medical devices, child car seats.")
    lines.append("Agricultural Supplies | Fertilizers, pesticides, agricultural inputs/equipment.")
    lines.append("Art & Collectibles | Antiques, sculptures, photographs, etc.")
    lines.append("Energy & Eco-Friendly Goods | Solar panels, sustainable energy equipment, wood.")
    lines.append("Other Physical Goods | Items not covered above.")
    lines.append("")

    # Regional sections
    by_region: dict = defaultdict(list)
    for r in records:
        if r.region_code.startswith("EU-"):
            by_region["European Union (EU)"].append(r)
        elif r.region_code.startswith("UK-"):
            by_region["United Kingdom (UK)"].append(r)
        elif r.region_code.startswith("CA-"):
            by_region["Canada (CA)"].append(r)
        elif r.region_code.startswith("CH-"):
            by_region["Switzerland (CH)"].append(r)
        elif r.region_code.startswith("NO-"):
            by_region["Norway (NO)"].append(r)
        else:
            by_region["Other"].append(r)

    for title, items in by_region.items():
        lines.append(title)
        if title == "European Union (EU)":
            lines.append("Country | Source Category | Normalized Category | Rate (%)")
            lines.append("--- | --- | --- | ---")
            for r in sorted(items, key=lambda x: (x.country_iso, x.category_ui_label)):
                lines.append(f"{r.country_iso} | {r.category_source_label} | {r.category_ui_label} | {r.rate_percent}")
        elif title == "United Kingdom (UK)":
            lines.append("Source Category | Normalized Category | Rate (%)")
            lines.append("--- | --- | ---")
            for r in sorted(items, key=lambda x: (x.category_ui_label, x.rate_percent)):
                lines.append(f"{r.category_source_label} | {r.category_ui_label} | {r.rate_percent}")
        else:
            if title.startswith("Canada"):
                program_prefixes = {"Federal (GST)", "Standard (HST)", "Provincial (PST)", "Provincial (QST)"}
                zero_labels = {"Basic Groceries", "Prescription Drugs", "Medical Devices", "Books"}

                program_rows = [r for r in items if r.category_source_label in program_prefixes]
                zero_rows = [r for r in items if r.category_source_label in zero_labels]

                lines.append("Tax Programs by Province")
                lines.append("Province | Program | Rate (%)")
                lines.append("--- | --- | ---")
                for r in sorted(program_rows, key=lambda x: (x.jurisdiction_name, x.category_source_label)):
                    lines.append(f"{r.jurisdiction_name} | {r.category_source_label} | {r.rate_percent}")
                lines.append("")

                lines.append("Zero-rated Categories (Federal) by Province")
                lines.append("Province | Category | Normalized Category | Rate (%)")
                lines.append("--- | --- | --- | ---")
                for r in sorted(zero_rows, key=lambda x: (x.jurisdiction_name, x.category_ui_label)):
                    lines.append(f"{r.jurisdiction_name} | {r.category_source_label} | {r.category_ui_label} | {r.rate_percent}")
            else:
                lines.append("Country | Source Category | Normalized Category | Rate (%)")
                lines.append("--- | --- | --- | ---")
                for r in sorted(items, key=lambda x: (x.country_iso, x.category_ui_label)):
                    lines.append(f"{r.country_iso} | {r.category_source_label} | {r.category_ui_label} | {r.rate_percent}")
        lines.append("")

    Path(out_path).write_text("\n".join(lines))
    print(f"Wrote README to {out_path}")


def summarize_to_console(records: Iterable[DataRecord]) -> None:
    counts = defaultdict(int)
    sample_by_region = defaultdict(list)
    for r in records:
        region = r.region_code.split("-")[0]
        counts[region] += 1
        if len(sample_by_region[region]) < 5:
            sample_by_region[region].append(r)

    print("Dry run summary:")
    for region, count in counts.items():
        print(f"  {region}: {count} records")
        for s in sample_by_region[region]:
            print(
                f"    {s.country_iso} {s.category_source_label} -> {s.category_ui_label} {s.rate_percent}% ({s.rate_type})"
            )



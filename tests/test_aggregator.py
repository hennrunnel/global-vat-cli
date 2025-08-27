from global_vat_cli.aggregator import assemble_records


def test_safe_default_highest_reduced_kept():
    raw = [
        {
            "region_code": "EU-AT",
            "country_iso": "AT",
            "country_name": "Austria",
            "tax_authority_name": "EC TEDB",
            "tax_authority_url": "https://ec.europa.eu/taxation_customs/tedb/#/home",
            "tax_type": "VAT",
            "rate_type": "Reduced",
            "rate_percent": 5.0,
            "category_source_label": "Foodstuffs",
            "primary_source_url": "https://example.com",
        },
        {
            "region_code": "EU-AT",
            "country_iso": "AT",
            "country_name": "Austria",
            "tax_authority_name": "EC TEDB",
            "tax_authority_url": "https://ec.europa.eu/taxation_customs/tedb/#/home",
            "tax_type": "VAT",
            "rate_type": "Reduced",
            "rate_percent": 10.0,
            "category_source_label": "Foodstuffs",
            "primary_source_url": "https://example.com",
        },
    ]

    out = assemble_records(raw, "2025-01-01T00:00:00Z")
    assert len(out) == 1
    assert out[0].rate_percent == 10.0
    assert out[0].category_ui_label == "Food & Groceries"



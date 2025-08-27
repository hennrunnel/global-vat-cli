from types import SimpleNamespace

from global_vat_cli.fetchers.eu import parse_eu_items


def test_parse_eu_items_basic():
    items = [
        SimpleNamespace(
            countryCode="AT",
            countryName="Austria",
            goodsCategory="Foodstuffs",
            rateType="Reduced",
            rate=10.0,
        ),
        SimpleNamespace(
            countryCode="AT",
            countryName="Austria",
            goodsCategory="Standard",
            rateType="Standard",
            rate=20.0,
        ),
    ]
    out = parse_eu_items(items, "https://example.com")
    assert len(out) == 2
    assert out[0]["country_iso"] == "AT"
    assert out[0]["category_source_label"] == "Foodstuffs"
    assert out[1]["rate_type"] == "Standard"



from global_vat_cli.normalizer import map_category


def test_map_category_known():
    assert map_category("Foodstuffs") == "Food & Groceries"


def test_map_category_unknown_defaults_to_other():
    assert map_category("Nonexistent Category") == "Other Physical Goods"



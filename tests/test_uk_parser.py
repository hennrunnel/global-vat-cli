import pandas as pd

from global_vat_cli.fetchers.uk import _classify_rate


def test_uk_rate_classification():
    assert _classify_rate(0.0) == "Zero"
    assert _classify_rate(5.0) == "Reduced"
    assert _classify_rate(20.0) == "Standard"



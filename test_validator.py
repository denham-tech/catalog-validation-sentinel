import pandas as pd
from schema_validator import CatalogValidator

def test_clean_dataset_passes():
    validator = CatalogValidator()
    df = pd.DataFrame({
        "variant_id": [1, 2],
        "title": ["Item A", "Item B"],
        "sku": ["SKU-A", "SKU-B"],
        "price": [25.0, 50.0],
        "available": [True, False]
    })
    passed, report = validator.validate_dataset(df)
    assert passed is True
    assert report["hygiene_score"] == 1.0
    assert report["status"] == "PASSED"

def test_defects_and_duplicates_flagged():
    validator = CatalogValidator()
    df = pd.DataFrame({
        "variant_id": [101, 101],
        "title": ["Item X", "Item X"],
        "sku": ["SKU-X", ""],
        "price": [30.0, -5.0],
        "available": [True, True]
    })
    passed, report = validator.validate_dataset(df)
    assert passed is False
    assert report["status"] == "FLAGGED"
    assert report["breakdown"]["duplicate_variants"] == 1
    assert report["breakdown"]["non_positive_prices"] == 1
    assert report["breakdown"]["invalid_skus"] == 1
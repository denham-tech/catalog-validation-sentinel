"""
E-Commerce Catalog Schema & Quality Validator
Parses scraped storefront catalogs, validates relational schema constraints,
and enforces data hygiene standards prior to database ingestion.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CatalogSentinel")


class CatalogValidator:
    def __init__(self, min_hygiene_score: float = 0.90):
        self.min_hygiene_score = min_hygiene_score
        self.required_fields = ["variant_id", "title", "sku", "price", "available"]

    def validate_dataset(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        total_records = len(df)
        if total_records == 0:
            logger.error("Empty dataset provided for ingestion.")
            return False, {"error": "Dataset is empty", "hygiene_score": 0.0}

        defects = {
            "missing_fields": [],
            "duplicate_variants": 0,
            "invalid_skus": 0,
            "non_positive_prices": 0,
            "null_values": 0
        }

        # 1. Structural Schema Check
        for field in self.required_fields:
            if field not in df.columns:
                defects["missing_fields"].append(field)

        if defects["missing_fields"]:
            logger.critical(f"Schema mismatch. Missing required columns: {defects['missing_fields']}")
            return False, {"defects": defects, "hygiene_score": 0.0}

        # 2. Data Integrity Checks
        defects["duplicate_variants"] = int(df["variant_id"].duplicated().sum())
        defects["invalid_skus"] = int(df["sku"].astype(str).str.strip().isin(["", "nan", "None"]).sum())
        defects["non_positive_prices"] = int((pd.to_numeric(df["price"], errors="coerce").fillna(0) <= 0).sum())
        defects["null_values"] = int(df[self.required_fields].isnull().sum().sum())

        total_defects = (
            defects["duplicate_variants"]
            + defects["invalid_skus"]
            + defects["non_positive_prices"]
            + defects["null_values"]
        )

        hygiene_score = max(0.0, round(1.0 - (total_defects / (total_records * len(self.required_fields))), 4))
        passed = hygiene_score >= self.min_hygiene_score and defects["duplicate_variants"] == 0

        audit_report = {
            "total_records": total_records,
            "total_defects": total_defects,
            "hygiene_score": hygiene_score,
            "status": "PASSED" if passed else "FLAGGED",
            "breakdown": defects
        }

        return passed, audit_report

    def export_report(self, report: Dict[str, Any], output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Audit report written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Audit e-commerce catalog scrape feeds.")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input CSV or JSON catalog file")
    parser.add_argument("--output", "-o", type=str, default="audit_report.json", help="Path to output validation JSON")
    parser.add_argument("--threshold", "-t", type=float, default=0.90, help="Minimum hygiene score threshold (0.0 - 1.0)")

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        logger.error(f"Input target does not exist: {input_path}")
        sys.exit(1)

    try:
        if input_path.suffix == ".csv":
            df = pd.read_csv(input_path)
        elif input_path.suffix == ".json":
            df = pd.read_json(input_path)
        else:
            logger.error("Unsupported file extension. Provide .csv or .json")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to read input file: {e}")
        sys.exit(1)

    validator = CatalogValidator(min_hygiene_score=args.threshold)
    passed, report = validator.validate_dataset(df)
    validator.export_report(report, args.output)

    logger.info(f"Validation Result: {report['status']} | Score: {report['hygiene_score'] * 100:.1f}%")

    # Deterministic exit code for pipeline coordination
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
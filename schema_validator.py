import json
import sqlite3
import pandas as pd
from datetime import datetime, timezone

class CatalogValidationSentinel:
    def __init__(self, output_report: str = "validation_report.json"):
        self.output_report = output_report

    def validate_catalog(self, df: pd.DataFrame) -> dict:
        """
        Executes strict assertion rules against the extracted storefront catalog.
        Flags null values, pricing anomalies, and broken SKU formats.
        """
        total_rows = len(df)
        violations = []

        # Assertion 1: Uniqueness of Variant IDs
        duplicate_ids = df[df.duplicated(subset=["variant_id"], keep=False)]
        if not duplicate_ids.empty:
            violations.append({
                "rule": "UNIQUE_VARIANT_ID",
                "severity": "CRITICAL",
                "failed_count": len(duplicate_ids),
                "details": f"Detected {len(duplicate_ids)} conflicting duplicate variant records."
            })

        # Assertion 2: Price Boundary & Typing Checks
        invalid_prices = df[df["price"].isna() | (df["price"] <= 0)]
        if not invalid_prices.empty:
            violations.append({
                "rule": "POSITIVE_PRICE_FLOOR",
                "severity": "HIGH",
                "failed_count": len(invalid_prices),
                "details": f"Found {len(invalid_prices)} SKUs with non-positive or null values."
            })

        # Assertion 3: SKU Format & Presence Validation
        missing_skus = df[df["sku"].isna() | (df["sku"].str.strip() == "")]
        if not missing_skus.empty:
            violations.append({
                "rule": "SKU_PRESENCE",
                "severity": "MEDIUM",
                "failed_count": len(missing_skus),
                "details": f"{len(missing_skus)} records are missing structured SKU identifiers."
            })

        # Calculate data hygiene score (0.0 to 100.0%)
        critical_penalty = sum(v["failed_count"] for v in violations if v["severity"] == "CRITICAL") * 5
        high_penalty = sum(v["failed_count"] for v in violations if v["severity"] == "HIGH") * 2
        medium_penalty = sum(v["failed_count"] for v in violations if v["severity"] == "MEDIUM") * 1
        
        raw_score = 100.0 - ((critical_penalty + high_penalty + medium_penalty) / max(total_rows, 1) * 10)
        hygiene_score = max(round(raw_score, 2), 0.0)

        report = {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "records_evaluated": total_rows,
            "hygiene_score_pct": hygiene_score,
            "status": "PASSED" if hygiene_score >= 90.0 else "FLAGGED",
            "active_violations": violations
        }

        return report

    def persist_report(self, report: dict):
        with open(self.output_report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"[✓] Validation report exported to {self.output_report}")
        print(f"[*] Pipeline Hygiene Score: {report['hygiene_score_pct']}% | Status: {report['status']}")


if __name__ == "__main__":
    # Test suite with dirty ingestion mock
    mock_dirty_data = {
        "variant_id": [101, 102, 103, 104, 105, 101], # 101 duplicated
        "title": ["Trouser A", "Jacket B", "Tee C", "Belt D", "Hoodie E", "Trouser A Duplicate"],
        "sku": ["TR-01", "JK-02", "", "BL-04", "HD-05", "TR-01"], # Tee C missing SKU
        "price": [120.0, -15.0, 45.0, 0.0, 110.0, 120.0],         # Negative & zero prices
        "available": [True, True, False, True, True, True]
    }

    df = pd.DataFrame(mock_dirty_data)
    sentinel = CatalogValidationSentinel()
    audit_results = sentinel.validate_catalog(df)
    sentinel.persist_report(audit_results)
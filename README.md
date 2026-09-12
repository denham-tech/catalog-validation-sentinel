# Autonomous Catalog Schema & Data Quality Sentinel

Enterprise-grade data quality assertion engine engineered in **Python** and **Pandas**. Executes deterministic schema validation, duplicate variant detection, price boundary enforcement, and hygiene scoring prior to downstream warehouse ingestion.

## Validation Assertions
- **Variant ID Uniqueness:** Isolates duplicated primary keys across dynamic catalog crawls.
- **Price Boundary Checks:** Intercepts null values, zero prices, and negative pricing errors.
- **SKU Schema Presence:** Identifies missing or malformed variant SKUs.
- **Automated Hygiene Scoring:** Calculates a weighted composite reliability index (0–100%) and triggers automated pipeline flags when quality drops below operational thresholds.

## Architecture
- `schema_validator.py` - Core assertion logic and audit engine.
- `validation_report.json` - Timestamped JSON diagnostic deliverable for downstream ingestion gates (untracked).
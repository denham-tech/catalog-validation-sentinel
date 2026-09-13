# Catalog Validation Sentinel

CLI-based data quality assertion tool for e-commerce catalog ingestion pipelines. 
Validates schema conformity, isolates primary key collisions, flags pricing anomalies, and computes a dataset hygiene score prior to warehouse insertion.

## Features
- **Deterministic Schema Validation:** Enforces presence and typing of required storefront fields (`variant_id`, `sku`, `price`, `available`).
- **Anomaly Interception:** Flags empty strings, duplicated variant IDs, null attributes, and non-positive prices.
- **Configurable Hygiene Scoring:** Computes a normalized quality metric (0.0 to 1.0) and returns system exit code `1` when thresholds are breached.
- **Pipeline Ready:** Accepts CSV/JSON feeds and outputs JSON diagnostic reports for downstream orchestrators.

## Usage

```bash
# Validate an extracted catalog crawl
python schema_validator.py --input data/sample_crawl.csv --output audit_report.json --threshold 0.90
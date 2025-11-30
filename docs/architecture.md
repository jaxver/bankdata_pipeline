# Architecture Overview

## High-Level Flow
1. **Configuration Load** – `bankdata_pipeline.config.load_settings` reads environment variables (optionally from a file referenced by `BANKDATA_ENV_FILE`). Storage directories under `runtime/` are created on the fly so the repo stays clean.
2. **Token Validation** – `token_service.TokenService` reads the cached token JSON (if present) and checks the embedded expiry windows. It refreshes or requests new tokens as needed via the GoCardless Bank Account Data API.
3. **Transaction Download** – `transactions.fetch_transactions` calls `/accounts/{account_id}/transactions/` using the valid access token. In demo mode (`BANKDATA_SAMPLE_MODE=true`) it loads the bundled sample payload instead.
4. **Extract Persistence** – `transactions.persist_transactions` writes the raw JSON under `runtime/extracts/<timestamp>_transactions_summary.json` so every run is auditable.
5. **Dataset Build & Key Extraction** – `dataset.build_dataset` normalizes all JSON extracts into a single DataFrame, removes duplicates, and enriches the rows with:
   - Remittance key/value pairs (IBAN, BIC, Naam, etc.)
   - Payment method detection
   - `merge_key`, `Income/Expense`, `Absolute`
6. **Key Validation** – `key_validation.validate_keys` computes coverage statistics per key and produces a JSON report used downstream (e.g., DB loads, dashboards).
7. **Outputs** – The orchestrator saves:
   - `transactions_dataset.csv`
   - `key_validation_report.json`
   Both live under `runtime/analysis/`.

## Important Design Choices
- **Secrets Outside Repo** – All runtime secrets live in a sibling `.env` (or pure environment variables). The module never writes credentials to disk unless you explicitly point `BANKDATA_TOKEN_CACHE` to a secure path.
- **Stateless Runs** – The extracts directory accrues timestamped payloads so data lineage is preserved. Downstream systems can re-ingest historical files without re-running the API call.
- **Key Quality as a First-Class Concern** – Many consumers only care about transactions with valid `IBAN/BIC/Naam`. The `key_validation` output makes it trivial to gate loads or raise alerts when coverage dips.
- **Pluggable Storage Roots** – Override `BANKDATA_STORAGE_ROOT` to redirect runtime files to an external volume or object store.

## Extending the Module
- Add new validators by extending `key_validation.validate_keys` or creating sibling functions.
- Integrate DB writes by consuming the CSV/JSON outputs and reusing the sanitized DataFrame.
- Hook into CI by running `python scripts/run_pipeline.py` on a schedule and archiving the runtime folder as an artifact.

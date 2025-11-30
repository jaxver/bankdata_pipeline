# BankData Production Pipeline

A production-ready subset of the BankData automation project designed for public consumption. This module exposes a clean transaction ingestion pipeline that validates API credentials, downloads account transactions, extracts remittance keys (IBAN, BIC, Naam, etc.), and produces downstream-ready data sets with automated key quality reports.

> **Why a separate module?**  
> This folder is intended to live as a Git submodule in a public repository. Runtime secrets, access tokens, and instance-specific configuration stay outside of `prod_module`, keeping the published code safe while still offering a complete, reproducible pipeline.

## Highlights
- Token lifecycle management (request + refresh) with pluggable storage paths.
- Transaction download client for the GoCardless Bank Account Data API.
- Deterministic remittance key extraction shared across the pipeline.
- Automated key validation reports to flag missing/invalid IBAN, BIC, Naam, etc.
- Tidy storage layout (`runtime/`) for extracts and analysis outputs.
- CLI runner plus unit tests to keep the core logic verifiable.

## Repository Layout
```
prod_module/
├── bankdata_pipeline/          # Source package
│   ├── dataset.py              # Dataset builder + key extraction helpers
│   ├── config.py               # Environment & storage configuration loader
│   ├── key_validation.py       # Key quality checks shared downstream
│   ├── pipeline.py             # Orchestrates the full run
│   ├── token_service.py        # Access/refresh token lifecycle
│   ├── transactions.py         # API client + persistence helpers
│   └── __init__.py
├── scripts/
│   └── run_pipeline.py         # Minimal CLI wrapper
├── data/
│   └── samples/
│       └── transactions_sample.json
├── docs/
│   └── architecture.md         # Detailed design notes
├── tests/
│   └── test_extract_fields.py  # Ensures key extraction never regresses
├── examples/
│   └── env.template            # Document required environment variables
├── requirements.txt
└── README.md
```

## Environment & Secrets
Actual credentials **must live outside** this module. Recommended setup:

1. Copy `examples/env.template` to a secure location that is *not* tracked by Git (e.g. `../bankdata.local.env`).
2. Populate the values (API base URL, account id, secret id/key).
3. Export `BANKDATA_ENV_FILE=/absolute/path/to/bankdata.local.env` **before** running the pipeline. The loader also respects existing process environment variables, so CI/CD can inject them directly without a file.

The `.gitignore` file already excludes generic `.env` artifacts and the runtime/token folders.

## Quick Start
1. **Install dependencies**
   ```bash
   cd prod_module
   python -m venv .venv
   .venv/Scripts/activate  # or source .venv/bin/activate on macOS/Linux
   pip install -r requirements.txt
   ```
2. **Provide configuration outside the module**
   ```bash
   cp examples/env.template ../bankdata.local.env
   # edit ../bankdata.local.env with your credentials
   set BANKDATA_ENV_FILE=../bankdata.local.env  # Windows PowerShell
   # or export BANKDATA_ENV_FILE=../bankdata.local.env on macOS/Linux
   ```
3. **Run the pipeline**
   ```bash
   python scripts/run_pipeline.py
   ```
   Outputs land under `runtime/`:
   - `runtime/extracts/<timestamp>_transactions.json`
   - `runtime/analysis/transactions_dataset.csv`
   - `runtime/analysis/key_validation_report.json`

## Key Validation Flow
1. Each transaction’s `remittanceInformationUnstructuredArray` is parsed for the standard key/value schema (`IBAN`, `BIC`, `Naam`, `Omschrijving`, etc.).
2. The parser tolerates multi-line values and noisy payment method lines.
3. `key_validation.py` asserts the presence and format of each key. The report includes:
   - Percent of rows with every key present.
   - Detailed failure breakdown per key.
   - Sample offending records to accelerate troubleshooting.
4. The enriched columns (`merge_key`, `Income/Expense`, `Absolute`) mirror the internal pipeline so downstream BI / DB loads work without custom patches.

## Tests & Samples
- `tests/test_extract_fields.py` ensures edge-case coverage for the parser.
- `data/samples/transactions_sample.json` provides a synthetic payload you can point the pipeline to (set `BANKDATA_SAMPLE_MODE=true`) for quick demos.

## Next Steps
- Wire this module into your main repo as a Git submodule.
- Point your CI to `scripts/run_pipeline.py` for automated ingestion.
- Extend `docs/architecture.md` with organization-specific diagrams or SOPs.

Feel free to tailor the structure, but keep the secrets outside of `prod_module` when publishing to GitHub.

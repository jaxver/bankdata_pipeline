# BankData Production Pipeline

A production-ready subset of the BankData PSD2 API designed for personal use. This repo contains a clean transaction ingestion pipeline that validates API credentials, downloads account transactions, extracts important info and produces downstream-ready data sets with automated key quality reports.

## Highlights
- Token lifecycle management (request + refresh) with pluggable storage paths.
- Transaction download client for the GoCardless Bank Account Data API.
- Deterministic remittance key extraction shared across the pipeline.
- Automated key validation reports to flag missing/invalid IBAN, BIC, Naam, etc.
- Tidy storage layout (`runtime/`) for extracts and analysis outputs.
- CLI runner plus unit tests to keep the core logic verifiable.

## Repository Layout
```
bankdata_pipeline/
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
Recommended setup:

1. Copy `examples/env.template` to a secure location.
2. Populate the values (API base URL, account id, secret id/key).
3. Export `BANKDATA_ENV_FILE=/absolute/path/to/bankdata.local.env` **before** running the pipeline. The loader also respects existing process environment variables, so CI/CD can inject them directly without a file.

The `.gitignore` file already excludes generic `.env` artifacts and the runtime/token folders.

## Quick Start
1. **Install dependencies**
   ```bash
   cd bankdata_pipeline
   python -m venv .venv
   .venv/Scripts/activate  # or source .venv/bin/activate on macOS/Linux
   pip install -r requirements.txt
   ```
2. **Provide configuration outside the repo**
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
1. For Dutch banks, each transaction’s `remittanceInformationUnstructuredArray` is parsed for the standard key/value schema (`IBAN`, `BIC`, `Naam`, `Omschrijving`, etc.).
2. The parser tolerates multi-line values and noisy payment method lines.
3. `key_validation.py` asserts the presence and format of each key. The report includes:
   - Percent of rows with every key present.
   - Detailed failure breakdown per key.
   - Sample offending records to accelerate troubleshooting.
4. The enriched columns (`merge_key`, `Income/Expense`, `Absolute`) mirror the internal pipeline so downstream BI / DB loads work without custom patches.

## Tests & Samples
- `tests/test_extract_fields.py` ensures edge-case coverage for the parser.
- `data/samples/transactions_sample.json` provides a synthetic payload you can point the pipeline to (set `BANKDATA_SAMPLE_MODE=true`) for quick demos.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

Feel free to tailor the structure to your liking!
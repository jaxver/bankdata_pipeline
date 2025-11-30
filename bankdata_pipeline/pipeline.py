from __future__ import annotations

from typing import Dict, Optional

from .dataset import build_dataset
from .config import PipelineSettings, load_settings
from .key_validation import validate_keys, write_report
from .token_service import TokenService
from .transactions import fetch_transactions, persist_transactions


def run_pipeline(settings: Optional[PipelineSettings] = None) -> Dict[str, str]:
    """Run the full ingestion pipeline and return important artifact paths."""

    settings = settings or load_settings()

    token_service = TokenService(settings)
    access_token = token_service.ensure_access_token()

    payload = fetch_transactions(access_token, settings)
    extract_path = persist_transactions(payload, settings)
    print(f"Saved raw extract to {extract_path}")

    dataset = build_dataset(settings.storage.extracts_dir)
    summary_path = settings.storage.analysis_dir / "transactions_dataset.csv"
    dataset.to_csv(summary_path, index=False)
    print(f"Wrote transaction dataset to {summary_path}")

    report = validate_keys(dataset)
    report_path = settings.storage.analysis_dir / "key_validation_report.json"
    write_report(report, report_path)
    print(f"Key validation summary saved to {report_path}")

    return {
        "extract": str(extract_path),
        "dataset_csv": str(summary_path),
        "key_report": str(report_path),
        "key_report_summary": report.to_dict(),
    }


__all__ = ["run_pipeline"]

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .dataset import KEY_COLUMNS


@dataclass
class KeyResult:
    key: str
    coverage_pct: float
    missing_count: int
    sample_missing: List[int]


@dataclass
class ValidationReport:
    total_rows: int
    all_keys_complete_pct: float
    per_key: List[KeyResult]

    def to_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "all_keys_complete_pct": self.all_keys_complete_pct,
            "per_key": [asdict(result) for result in self.per_key],
        }


def validate_keys(df: pd.DataFrame, keys: Iterable[str] = KEY_COLUMNS, sample_size: int = 10) -> ValidationReport:
    if df.empty:
        return ValidationReport(total_rows=0, all_keys_complete_pct=0.0, per_key=[])

    total_rows = len(df)
    per_key: List[KeyResult] = []
    all_complete_mask = pd.Series(True, index=df.index)

    for key in keys:
        series = df.get(key)
        if series is None:
            missing_mask = pd.Series(True, index=df.index)
        else:
            normalized = series.fillna("").astype(str).str.strip()
            missing_mask = normalized.eq("")
        coverage = 100.0 * (total_rows - missing_mask.sum()) / total_rows
        all_complete_mask &= ~missing_mask
        missing_indices = missing_mask[missing_mask].index.tolist()[:sample_size]
        per_key.append(
            KeyResult(
                key=key,
                coverage_pct=round(coverage, 2),
                missing_count=int(missing_mask.sum()),
                sample_missing=[int(i) for i in missing_indices],
            )
        )

    all_keys_complete_pct = round(100.0 * all_complete_mask.sum() / total_rows, 2)
    return ValidationReport( total_rows=total_rows, all_keys_complete_pct=all_keys_complete_pct, per_key=per_key)


def write_report(report: ValidationReport, path: Path) -> Path:
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return path


__all__ = ["validate_keys", "write_report", "ValidationReport", "KeyResult"]

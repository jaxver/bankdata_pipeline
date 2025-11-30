from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Common Dutch remittance information keys to extract
KEY_COLUMNS = ["IBAN", "BIC", "Naam", "Omschrijving", "Kenmerk", "NR", "Incassant", "Machtiging", "Land"]
PAYMENT_METHODS = [
	"SEPA iDEAL",
	"SEPA Incasso",
	"SEPA Overboeking",
	"SEPA Periodieke overb.",
	"SEPA PINSPAREN",
	"BEA",
	"Apple Pay",
	"iDEAL",
]
AMOUNT_COL = "transactionAmount.amount"
BALANCE_COL = "balanceAfterTransaction.balanceAmount.amount"


def load_transaction_frames(extracts_dir: Path) -> List[pd.DataFrame]:
	frames: List[pd.DataFrame] = []
	for path in sorted(extracts_dir.glob("*_transactions_summary.json")):
		data = json.loads(path.read_text("utf-8"))
		booked = data.get("transactions", {}).get("booked")
		if not booked:
			continue
		frames.append(pd.json_normalize(booked))
	return frames


def extract_fields(text_list) -> dict:
	if not isinstance(text_list, list):
		if text_list is None or (hasattr(pd, "isna") and pd.isna(text_list)):
			text_list = []
		else:
			text_list = [str(text_list)]
	cleaned = [str(x).strip() for x in text_list if str(x).strip()]
	result: dict[str, Optional[str]] = {k: None for k in KEY_COLUMNS}
	result["PaymentMethod"] = None

	for item in cleaned:
		for pm in PAYMENT_METHODS:
			if item == pm or item.startswith(pm + ",") or pm in item:
				result["PaymentMethod"] = pm
				break
		if result["PaymentMethod"]:
			break

	i = 0
	while i < len(cleaned):
		line = cleaned[i]
		matched = next((k for k in KEY_COLUMNS if line.startswith(f"{k}:")), None)
		if matched:
			value_parts = [line.split(":", 1)[1].strip()]
			j = i + 1
			while j < len(cleaned):
				candidate = cleaned[j]
				if any(candidate.startswith(f"{k}:") for k in KEY_COLUMNS):
					break
				if any(candidate == pm or candidate.startswith(pm + ",") for pm in PAYMENT_METHODS):
					break
				value_parts.append(candidate.strip())
				j += 1
			result[matched] = " ".join(filter(None, value_parts)) or None
			i = j
		else:
			i += 1
	return result


def build_dataset(extracts_dir: Path) -> pd.DataFrame:
	frames = load_transaction_frames(extracts_dir)
	if not frames:
		raise RuntimeError("No transaction extracts found. Download data first.")

	dataset = pd.concat(frames, ignore_index=True)
	if "transactionId" in dataset.columns:
		dataset = dataset.drop_duplicates(subset=["transactionId"], ignore_index=True)
	dataset = dataset.reset_index(drop=True)

	if "remittanceInformationUnstructuredArray" in dataset.columns:
		extracted = dataset["remittanceInformationUnstructuredArray"].apply(extract_fields)
	else:
		extracted = pd.Series([{k: None for k in KEY_COLUMNS} for _ in range(len(dataset))])
	extracted_df = pd.DataFrame(list(extracted))
	dataset = pd.concat([dataset, extracted_df], axis=1)

	for column in (AMOUNT_COL, BALANCE_COL):
		if column in dataset.columns:
			dataset[column] = pd.to_numeric(dataset[column], errors="coerce")

	if "bookingDate" in dataset.columns:
		dataset["bookingDate"] = dataset["bookingDate"].astype(str)

	dataset["merge_key"] = dataset.apply(_build_merge_key, axis=1)

	if AMOUNT_COL in dataset.columns:
		dataset["Income/Expense"] = dataset[AMOUNT_COL].apply(
			lambda value: "Income" if pd.notnull(value) and value >= 0 else ("Expense" if pd.notnull(value) else None)
		)
		dataset["Absolute"] = dataset[AMOUNT_COL].abs()
	else:
		dataset["Income/Expense"] = None
		dataset["Absolute"] = None

	return dataset


def _build_merge_key(row) -> str:
	booking = row.get("bookingDate") or ""
	amount = row.get(AMOUNT_COL)
	balance = row.get(BALANCE_COL)
	amount_part = "" if pd.isna(amount) else str(amount)
	balance_part = "" if pd.isna(balance) else str(balance)
	return f"{booking}_{amount_part}_{balance_part}"


__all__ = ["build_dataset", "extract_fields", "KEY_COLUMNS", "AMOUNT_COL", "BALANCE_COL"]
"""Public entry points for the BankData production pipeline."""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
	from .config import PipelineSettings


def load_settings(*args, **kwargs):  # type: ignore[override]
	from .config import load_settings as _load_settings

	return _load_settings(*args, **kwargs)


def run_pipeline(settings: Optional["PipelineSettings"] = None):
	from .pipeline import run_pipeline as _run_pipeline

	return _run_pipeline(settings)


def __getattr__(name: str):  # pragma: no cover
	if name == "PipelineSettings":
		from .config import PipelineSettings

		return PipelineSettings
	raise AttributeError(name)


__all__ = ["load_settings", "run_pipeline", "PipelineSettings"]

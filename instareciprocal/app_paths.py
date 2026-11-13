"""Resolve application data paths independently of the current working directory."""

from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def app_path(*parts: str) -> Path:
    return application_root().joinpath(*parts)


def ensure_app_directories() -> None:
    app_path("data").mkdir(parents=True, exist_ok=True)
    app_path("exports").mkdir(parents=True, exist_ok=True)

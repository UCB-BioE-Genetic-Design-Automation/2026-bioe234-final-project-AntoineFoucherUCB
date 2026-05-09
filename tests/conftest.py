"""Shared pytest fixtures for biosafety tools."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest

from modules.biosafety.tools import questionnaire_parsing as qp_module


@pytest.fixture
def isolated_questionnaire_parser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Fresh BUA snapshot path + empty form for each test."""
    snap = tmp_path / "bua_state_snapshot.json"
    monkeypatch.setattr(qp_module, "_state_file", lambda: snap)
    qp_module._reset_state()
    yield qp_module.questionnaire_parsing

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture(autouse=True)
def airtime_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRTIME_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AIRTIME_RUNS", str(tmp_path / "runs"))
    return tmp_path

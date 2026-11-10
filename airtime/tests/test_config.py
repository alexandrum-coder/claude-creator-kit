from __future__ import annotations

import json
import stat
from datetime import date
from pathlib import Path

import airtime_config as c


def test_defaults_when_no_file():
    p = c.load_profile()
    assert p == c.DEFAULTS
    assert p is not c.DEFAULTS


def test_profile_overrides_defaults():
    c.save_profile("principal", {"channel": "Canalul meu", "shorts": True})
    p = c.load_profile("principal")
    assert p["channel"] == "Canalul meu"
    assert p["shorts"] is True
    assert p["language"] == "ro"


def test_default_profile_from_config():
    c.home().mkdir(parents=True)
    (c.home() / "config.json").write_text(json.dumps({"default_profile": "altul"}))
    c.save_profile("altul", {"channel": "Altul"})
    assert c.load_profile()["channel"] == "Altul"


def test_slug_diacritics():
    assert c.slugify("Antrenament spate – partea 1, ședință") == "antrenament-spate-partea-1-sedinta"
    assert len(c.slugify("a" * 100)) <= 40


def test_run_dir_suffix():
    d1 = c.new_run_dir(Path("/x/Clip Nou.mp4"), date(2026, 11, 10))
    d2 = c.new_run_dir(Path("/x/Clip Nou.mp4"), date(2026, 11, 10))
    assert d1.name == "2026-11-10-clip-nou"
    assert d2.name == "2026-11-10-clip-nou-2"
    assert d1.is_dir() and d2.is_dir()


def test_save_profile_mode_600_for_tokens_dir():
    c.save_profile("principal", {})
    tokens = c.token_path("principal").parent
    assert tokens.is_dir()
    assert stat.S_IMODE(tokens.stat().st_mode) == 0o700
    assert c.token_path("principal").name == "principal-youtube.json"
    assert c.client_path().name == "google-client.json"

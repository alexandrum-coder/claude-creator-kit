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


def _speed(content: str) -> None:
    c.home().mkdir(parents=True, exist_ok=True)
    (c.home() / "speed.json").write_text(content)


def test_whisper_model_speed_json_wins():
    _speed(json.dumps({"model": "small", "sec_per_min": 40.0}))
    assert c.whisper_model("principal") == "small"


def test_whisper_model_ro_without_speed_json_is_medium():
    assert c.whisper_model("principal") == "medium"


def test_whisper_model_other_language_is_small():
    c.save_profile("en", {"language": "en"})
    assert c.whisper_model("en") == "small"


def test_whisper_model_speed_json_without_model_falls_back():
    _speed(json.dumps({"sec_per_min": 40.0}))
    assert c.whisper_model("principal") == "medium"
    _speed(json.dumps({"model": ""}))
    assert c.whisper_model("principal") == "medium"


def test_whisper_model_broken_speed_json_falls_back():
    _speed("{not json")
    assert c.whisper_model("principal") == "medium"
    c.save_profile("en", {"language": "en"})
    assert c.whisper_model("en") == "small"


def test_whisper_model_broken_profile_falls_back_to_ro():
    c.save_profile("stricat", {})
    (c.home() / "profiles" / "stricat.json").write_text("{not json")
    assert c.whisper_model("stricat") == "medium"


def test_run_dir_in_chosen_folder_created_with_suffix(tmp_path):
    root = tmp_path / "ales" / "adanc"
    d1 = c.new_run_dir(Path("/x/Clip Nou.mp4"), date(2026, 11, 10), root=root)
    d2 = c.new_run_dir(Path("/x/Clip Nou.mp4"), date(2026, 11, 10), root=str(root))
    assert d1 == root / "2026-11-10-clip-nou"
    assert d2 == root / "2026-11-10-clip-nou-2"
    assert d1.is_dir() and d2.is_dir()
    assert not c.runs_root().exists()


def test_run_dir_tilde_and_short_path_are_in_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "eu"))
    d1 = c.new_run_dir(Path("/x/a.mp4"), date(2026, 11, 10), root="~/Desktop/X")
    d2 = c.new_run_dir(Path("/x/a.mp4"), date(2026, 11, 10), root="Clipuri")
    assert d1 == tmp_path / "eu" / "Desktop" / "X" / "2026-11-10-a"
    assert d2 == tmp_path / "eu" / "Clipuri" / "2026-11-10-a"


def test_run_dir_without_folder_stays_in_runs_root():
    d = c.new_run_dir(Path("/x/a.mp4"), date(2026, 11, 10), root=None)
    assert d.parent == c.runs_root()

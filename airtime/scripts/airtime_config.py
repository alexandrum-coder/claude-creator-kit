"""Configurație și profiluri AirTime: foundation importat de celelalte scripturi."""
from __future__ import annotations

import copy
import json
import os
import re
import unicodedata
from datetime import date
from pathlib import Path

DEFAULTS = {
    "language": "ro",
    "channel": "",
    "intro_text": "",
    "colors": {"primary": "#111111", "accent": "#FF5A1F"},
    "youtube_time": "18:00",
    "reels_time": "19:00",
    "facebook": False,
    "shorts": False,
    "keywords": [],
    "clip_type": "demonstratii",  # demonstratii | culise | vorbit
    "timezone": "Europe/Bucharest",
    "business_suite_login": "",
}


def home() -> Path:
    return Path(os.environ.get("AIRTIME_HOME") or Path.home() / ".airtime")


def runs_root() -> Path:
    return Path(os.environ.get("AIRTIME_RUNS") or Path.home() / "AirTime")


def _profile_file(name: str) -> Path:
    return home() / "profiles" / f"{name}.json"


def load_profile(name: str | None = None) -> dict:
    if name is None:
        name = "principal"
        cfg = home() / "config.json"
        if cfg.exists():
            name = json.loads(cfg.read_text(encoding="utf-8")).get("default_profile", name)
    profile = copy.deepcopy(DEFAULTS)
    f = _profile_file(name)
    if f.exists():
        profile.update(json.loads(f.read_text(encoding="utf-8")))
    return profile


def save_profile(name: str, data: dict) -> Path:
    h = home()
    h.mkdir(parents=True, exist_ok=True)
    (h / "profiles").mkdir(exist_ok=True)
    tokens = h / "tokens"
    tokens.mkdir(exist_ok=True)
    os.chmod(tokens, 0o700)
    f = _profile_file(name)
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


def token_path(profile: str) -> Path:
    return home() / "tokens" / f"{profile}-youtube.json"


def client_path() -> Path:
    return home() / "google-client.json"


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:40].strip("-")


def new_run_dir(video: Path, when: date) -> Path:
    base = f"{when:%Y-%m-%d}-{slugify(Path(video).stem) or 'clip'}"
    root = runs_root()
    root.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        d = root / (base if n == 1 else f"{base}-{n}")
        try:
            d.mkdir()
            return d
        except FileExistsError:
            n += 1

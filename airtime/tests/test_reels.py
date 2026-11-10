from __future__ import annotations

import json
import sys

import pytest

import reels


def test_clean_captions_ro():
    tr = {
        "segments": [{"start": 0, "end": 3, "text": "ăă salut", "words": []}],
        "captions": [
            {"text": "ăă", "startMs": 0, "endMs": 200},
            {"text": " salut", "startMs": 300, "endMs": 700},
            {"text": " Mmm,", "startMs": 800, "endMs": 900},
            {"text": " îîî", "startMs": 900, "endMs": 1000},
            {"text": " ăm", "startMs": 1000, "endMs": 1100},
            {"text": " mămăligă", "startMs": 1100, "endMs": 1500},
        ],
    }
    before = json.dumps(tr["segments"])
    out = reels.clean_captions(tr)
    assert [c["text"].strip() for c in out["captions"]] == ["salut", "mămăligă"]
    assert json.dumps(out["segments"]) == before
    assert len(tr["captions"]) == 6  # input untouched


def test_vertical_reframe_full_frame(tmp_path, monkeypatch):
    clips = tmp_path / "clips"
    clips.mkdir()
    (clips / "clip_01.mp4").write_bytes(b"")
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 12.5))
    out = tmp_path / "reframe.json"
    reels.write_vertical_reframe(clips, out)
    data = json.loads(out.read_text())
    entry = data["clips"]["clip_01.mp4"]
    assert entry["crop"] == {"x": 0, "y": 0, "w": 1080, "h": 1920}
    assert entry["source_resolution"] == "1080x1920"
    assert entry["output_resolution"] == "1080x1920"
    assert entry["strategy"] == "full-frame"
    assert data["content_type"] == "vertical"


def test_shorts_root_order(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "h"))
    monkeypatch.delenv("SHORTS_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    home_dir = tmp_path / "h" / ".claude" / "skills" / "shorts"
    cfg = tmp_path / "cfg"
    cfg_dir = cfg / "skills" / "shorts"
    env_dir = tmp_path / "env"
    # none exists: last candidate
    assert reels.shorts_root() == home_dir
    home_dir.mkdir(parents=True)
    assert reels.shorts_root() == home_dir
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    assert reels.shorts_root() == home_dir  # config dir candidate missing
    cfg_dir.mkdir(parents=True)
    assert reels.shorts_root() == cfg_dir
    monkeypatch.setenv("SHORTS_ROOT", str(env_dir))
    assert reels.shorts_root() == cfg_dir  # env path missing
    env_dir.mkdir()
    assert reels.shorts_root() == env_dir


def test_shorts_python_order(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    a = tmp_path / ".video-skill" / "bin" / "python3"
    b = tmp_path / ".shorts-skill" / "bin" / "python3"
    b.parent.mkdir(parents=True)
    b.write_text("")
    assert reels.shorts_python() == b
    a.parent.mkdir(parents=True)
    a.write_text("")
    assert reels.shorts_python() == a


def test_step_failure_carries_name_and_stderr(tmp_path):
    with pytest.raises(reels.StepError) as e:
        reels.run_step("demo", [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"])
    assert e.value.step == "demo"
    assert "boom" in str(e.value)

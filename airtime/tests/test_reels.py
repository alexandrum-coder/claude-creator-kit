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


def _fake_run_factory(calls, n_render, n_export):
    def fake(step, args, cwd=None):
        args = [str(a) for a in args]
        calls.append((step, args))
        if step == "snap_boundaries":
            segs = [{"id": i, "start": 0.0, "end": 5.0} for i in range(1, 4)]
            from pathlib import Path
            Path(args[args.index("--output") + 1]).write_text(json.dumps({"segments": segs}))
        elif step == "extract_clip":
            from pathlib import Path
            Path(args[-1]).write_bytes(b"")
        elif step == "render":
            from pathlib import Path
            d = Path(args[args.index("--output-dir") + 1])
            for i in range(1, n_render + 1):
                (d / f"short_{i:02d}.mp4").write_bytes(b"")
        elif step == "export":
            from pathlib import Path
            d = Path(args[args.index("--output-dir") + 1])
            for i in range(1, n_export + 1):
                (d / f"short_{i:02d}_ig.mp4").write_bytes(b"")
        return ""
    return fake


def _inputs(tmp_path):
    tr = tmp_path / "t.json"
    tr.write_text(json.dumps({"segments": [], "captions": []}))
    return tmp_path / "curat.mp4", tr, tmp_path / "approved.json"


def test_build_steps_in_order(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(reels, "run_step", _fake_run_factory(calls, 3, 3))
    curat, tr, ap = _inputs(tmp_path)
    out = reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal")
    assert [c[0] for c in calls] == ["snap_boundaries", "extract_clip", "extract_clip",
                                     "extract_clip", "compute_reframe", "render", "export"]
    assert calls[0][1][1].endswith("snap_boundaries.py")
    assert "ffmpeg" == calls[1][1][0] and "copy" in calls[1][1]
    assert "talking-head" in calls[4][1]
    assert calls[5][1][0] == "node" and "bold" in calls[5][1]
    assert calls[6][1][0] == "bash" and "instagram" in calls[6][1] and "--force" in calls[6][1]
    assert len(out) == 3


def test_build_fails_on_partial_render(tmp_path, monkeypatch):
    monkeypatch.setattr(reels, "run_step", _fake_run_factory([], 2, 3))
    curat, tr, ap = _inputs(tmp_path)
    with pytest.raises(reels.StepError) as e:
        reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal")
    assert e.value.step == "render"


def test_build_fails_on_partial_export(tmp_path, monkeypatch):
    monkeypatch.setattr(reels, "run_step", _fake_run_factory([], 3, 2))
    curat, tr, ap = _inputs(tmp_path)
    with pytest.raises(reels.StepError) as e:
        reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal")
    assert e.value.step == "export"


def test_build_ignores_stale_exports(tmp_path, monkeypatch):
    out = tmp_path / "out"
    out.mkdir()
    (out / "short_09_ig.mp4").write_bytes(b"")
    monkeypatch.setattr(reels, "run_step", _fake_run_factory([], 3, 3))
    curat, tr, ap = _inputs(tmp_path)
    res = reels.build(curat, tr, ap, "bold", out, "horizontal")
    assert [p.name for p in res] == ["short_01_ig.mp4", "short_02_ig.mp4", "short_03_ig.mp4"]


def test_cli_missing_input_is_json_error(tmp_path, capsys):
    rc = reels.main(["build", "--curat", str(tmp_path / "x.mp4"),
                     "--transcript", str(tmp_path / "nope.json"),
                     "--approved", str(tmp_path / "nope2.json"),
                     "--style", "bold", "--orientation", "horizontal",
                     "--out", str(tmp_path / "o")])
    assert rc == 1
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1 and "error" in json.loads(lines[0])

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


def test_step_timeout_raises_clear_error():
    with pytest.raises(reels.StepError) as e:
        reels.run_step("render", [sys.executable, "-c", "import time; time.sleep(5)"], timeout=1)
    assert e.value.step == "render"
    assert "blocat" in str(e.value)


def test_step_under_timeout_returns_output():
    assert reels.run_step("demo", [sys.executable, "-c", "print('ok')"], timeout=30).strip() == "ok"


def test_transcribe_uses_airtime_script_and_language(tmp_path, monkeypatch):
    from pathlib import Path
    calls = []

    def fake(step, args, cwd=None, timeout=None):
        args = [str(a) for a in args]
        calls.append(args)
        Path(args[args.index("--output") + 1]).write_text("{}")
        return ""

    monkeypatch.setattr(reels, "run_step", fake)
    reels.transcribe(tmp_path / "v.mp4", tmp_path / "a.json", "small", language="ro")
    reels.transcribe(tmp_path / "v.mp4", tmp_path / "b.json", "small")
    assert calls[0][1] == str(Path(reels.__file__).with_name("transcribe.py"))
    assert calls[0][-2:] == ["--language", "ro"]
    assert "--language" not in calls[1]


def test_build_render_has_timeout(tmp_path, monkeypatch):
    seen = {}
    inner = _fake_run_factory([], 3, 3)

    def fake(step, args, cwd=None, timeout=None):
        if step == "render":
            seen["timeout"] = timeout
        return inner(step, args, cwd=cwd, timeout=timeout)

    monkeypatch.setattr(reels, "run_step", fake)
    curat, tr, ap = _inputs(tmp_path)
    reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal")
    assert seen.get("timeout") == reels.RENDER_TIMEOUT_PER_REEL * 3


def _fake_run_factory(calls, n_render, n_export):
    def fake(step, args, cwd=None, timeout=None):
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


def _inputs(tmp_path, words=True):
    tr = tmp_path / "t.json"
    segs = [{"start": 0, "end": 1, "text": "salut",
             "words": [{"word": "salut", "start": 0.0, "end": 1.0}]}] if words else []
    tr.write_text(json.dumps({"segments": segs, "captions": []}))
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


def test_transcribe_cli_default_model_is_medium(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake(video, out, model, language=None):
        seen["model"] = model
        return out

    monkeypatch.setattr(reels, "transcribe", fake)
    reels.main(["transcribe", "--video", str(tmp_path / "v.mp4"), "--out", str(tmp_path / "t.json")])
    assert seen["model"] == "medium"


def _fake_export_fails_after_writing(calls, n_files, content=b"x"):
    """claude-shorts export.sh on macOS: writes the files, then exits 1 (GNU `paste -sd ','`)."""
    base = _fake_run_factory(calls, 3, 0)

    def fake(step, args, cwd=None, timeout=None):
        base(step, args, cwd)
        if step == "export":
            from pathlib import Path
            d = Path(str(args[args.index("--output-dir") + 1]))
            for i in range(1, n_files + 1):
                (d / f"short_{i:02d}_ig.mp4").write_bytes(content)
            raise reels.StepError("export", "exit 1: paste: -: No such file")
        return ""
    return fake


def test_build_accepts_export_files_when_export_sh_exits_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(reels, "run_step", _fake_export_fails_after_writing([], 3))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    curat, tr, ap = _inputs(tmp_path)
    warnings = []
    out = reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal", warnings=warnings)
    assert [p.name for p in out] == ["short_01_ig.mp4", "short_02_ig.mp4", "short_03_ig.mp4"]
    assert warnings == []  # nothing for the coach to act on
    assert "export.sh failed after writing all 3 files" in capsys.readouterr().err


def test_build_export_failure_with_missing_file_is_error(tmp_path, monkeypatch):
    monkeypatch.setattr(reels, "run_step", _fake_export_fails_after_writing([], 2))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    curat, tr, ap = _inputs(tmp_path)
    with pytest.raises(reels.StepError) as e:
        reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal")
    assert e.value.step == "export"


def test_build_export_failure_with_broken_file_is_error(tmp_path, monkeypatch):
    monkeypatch.setattr(reels, "run_step", _fake_export_fails_after_writing([], 3))

    def bad_probe(p):
        raise reels.StepError("ffprobe", "exit 1: moov atom not found")
    monkeypatch.setattr(reels, "probe", bad_probe)
    curat, tr, ap = _inputs(tmp_path)
    with pytest.raises(reels.StepError) as e:
        reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal")
    assert e.value.step == "export"


def test_build_export_failure_with_empty_files_is_error(tmp_path, monkeypatch):
    monkeypatch.setattr(reels, "run_step", _fake_export_fails_after_writing([], 3, content=b""))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    curat, tr, ap = _inputs(tmp_path)
    with pytest.raises(reels.StepError) as e:
        reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal")
    assert e.value.step == "export"


def test_export_with_real_bash_and_bsd_paste_stub(tmp_path, monkeypatch, capsys):
    """export.sh ending in `paste -sd ','` under a BSD-like paste (needs `-`): files kept, warning set."""
    root = tmp_path / "shorts"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "export.sh").write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        "while [[ $# -gt 0 ]]; do case \"$1\" in --input-dir) IN=\"$2\"; shift 2;; "
        "--output-dir) OUT=\"$2\"; shift 2;; --platform) shift 2;; *) shift;; esac; done\n"
        "R=()\nfor f in \"$IN\"/short_*.mp4; do b=$(basename \"$f\" .mp4); "
        "printf x > \"$OUT/${b}_ig.mp4\"; R+=(\"$b\"); done\n"
        "J=$(printf '%s\\n' \"${R[@]}\" | paste -sd ',')\necho \"$J\"\n")
    bsd = tmp_path / "bsdbin"
    bsd.mkdir()
    (bsd / "paste").write_text("#!/bin/sh\necho 'usage: paste [-s] [-d delimiters] file ...' >&2\nexit 1\n")
    (bsd / "paste").chmod(0o755)
    monkeypatch.setenv("PATH", str(bsd) + ":" + __import__("os").environ["PATH"])
    monkeypatch.setenv("SHORTS_ROOT", str(root))
    render = tmp_path / "render"
    render.mkdir()
    for i in (1, 2):
        (render / f"short_{i:02d}.mp4").write_bytes(b"r")
    out = tmp_path / "out"
    out.mkdir()
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    res = reels.export_reels(root, render, out, 2)
    assert [p.name for p in res] == ["short_01_ig.mp4", "short_02_ig.mp4"]
    assert "export.sh failed after writing all 2 files" in capsys.readouterr().err


def test_build_falls_back_to_center_crop_when_reframe_fails(tmp_path, monkeypatch):
    calls = []
    base = _fake_run_factory(calls, 3, 3)

    def fake(step, args, cwd=None, timeout=None):
        if step == "compute_reframe":
            calls.append((step, [str(a) for a in args]))
            raise reels.StepError("compute_reframe",
                                  "exit 1: AttributeError: module 'mediapipe' has no attribute 'solutions'")
        return base(step, args, cwd)

    monkeypatch.setattr(reels, "run_step", fake)
    monkeypatch.setattr(reels, "probe", lambda p: (1920, 1080, 5.0))
    curat, tr, ap = _inputs(tmp_path)
    warnings = []
    out = reels.build(curat, tr, ap, "bold", tmp_path / "out", "horizontal", warnings=warnings)
    assert len(out) == 3
    assert [c[0] for c in calls][-2:] == ["render", "export"]
    data = json.loads((tmp_path / "out" / "work" / "reframe.json").read_text())
    assert data["clip_count"] == 3
    entry = data["clips"]["clip_01.mp4"]
    assert entry["crop"] == {"x": 656, "y": 0, "w": 607, "h": 1080}
    assert entry["source_resolution"] == "1920x1080"
    assert entry["output_resolution"] == "1080x1920"
    assert entry["strategy"] == "center"
    assert any("feței" in w for w in warnings)


def test_cli_build_prints_warnings(tmp_path, monkeypatch, capsys):
    def fake_build(*a, warnings=None, **k):
        warnings.append("avertisment de test")
        return [tmp_path / "short_01_ig.mp4"]
    monkeypatch.setattr(reels, "build", fake_build)
    rc = reels.main(["build", "--curat", "c", "--transcript", "t", "--approved", "a", "--out", str(tmp_path)])
    assert rc == 0
    res = json.loads(capsys.readouterr().out)
    assert res["warnings"] == ["avertisment de test"]


def test_build_without_words_skips_snapping(tmp_path, monkeypatch):
    """claude-shorts snap_boundaries.py exits 1 on a transcript with no words (music or voiceover
    clip); the approved segments are then used as they are."""
    calls = []
    monkeypatch.setattr(reels, "run_step", _fake_run_factory(calls, 2, 2))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 30.0))
    curat, tr, ap = _inputs(tmp_path, words=False)
    segs = [{"id": 1, "start": 0.0, "end": 30.0, "duration": 30.0, "score": 50,
             "hook_line1": "Exercițiu spate", "hook_line2": "fără vorbe"},
            {"id": 2, "start": 30.0, "end": 60.0, "duration": 30.0, "score": 50,
             "hook_line1": "Exercițiu umeri", "hook_line2": "pas cu pas"}]
    ap.write_text(json.dumps({"segments": segs, "style": "bold"}), encoding="utf-8")
    out = reels.build(curat, tr, ap, "bold", tmp_path / "out", "vertical")
    assert len(out) == 2
    assert "snap_boundaries" not in [c[0] for c in calls]
    snapped = json.loads((tmp_path / "out" / "work" / "snapped_segments.json").read_text(encoding="utf-8"))
    assert snapped["segments"] == segs
    extract = [c[1] for c in calls if c[0] == "extract_clip"]
    assert extract[1][extract[1].index("-ss") + 1] == "30.000"


def test_has_words():
    assert not reels.has_words({"segments": [{"start": 0, "end": 1, "text": "", "words": []}]})
    assert not reels.has_words({})
    assert reels.has_words({"segments": [{"words": [{"word": "a", "start": 0, "end": 1}]}]})

"""Element 8 of the montage upgrade: optional two-pass loudnorm on youtube.mp4 (render.json "loudnorm": true)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess

import pytest

import compose


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _parts(tmp_path, audio_expr=None):
    curat = tmp_path / "curat.mp4"
    args = ["-f", "lavfi", "-i", "color=c=gray:s=320x240:r=25:d=8"]
    if audio_expr:
        args += ["-f", "lavfi", "-i", audio_expr, "-c:a", "aac", "-shortest"]
    _ff(*args, "-pix_fmt", "yuv420p", "-c:v", "libx264", str(curat))
    rd = tmp_path / "render"
    rd.mkdir()
    _ff("-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=1", "-pix_fmt", "yuv420p", "-c:v", "libx264",
        str(rd / "intro.mp4"))
    return curat, rd


def _ebur128(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    summary = r.stderr[r.stderr.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[0-9.]+) LUFS", summary).group(1))
    peak = float(re.search(r"Peak:\s+(-?[0-9.]+|-inf) dBFS", summary).group(1))
    return i, peak


def test_loudnorm_brings_quiet_clip_to_minus_14(tmp_path):
    # a quiet speech-like signal, around -32 LUFS
    curat, rd = _parts(tmp_path, "aevalsrc='0.02*sin(2*PI*300*t)*(0.5+0.5*sin(2*PI*3*t))':s=48000:d=8")
    (rd / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": [], "loudnorm": True}))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    i, peak = _ebur128(out)
    assert i == pytest.approx(-14, abs=1)
    assert peak <= -1.0   # true peak criterion -1 dBTP, no tolerance (D-24: target TP=-1.5 leaves room for AAC)
    info = compose.probe(out)
    assert info["duration"] == pytest.approx(9.0, abs=0.15)
    # loudnorm resamples to 192 kHz internally; the output must stay at 48 kHz
    assert compose._probe_full(out)["sample_rate"] == 48000


def test_without_key_loudness_is_untouched(tmp_path):
    curat, rd = _parts(tmp_path, "aevalsrc='0.02*sin(2*PI*300*t)*(0.5+0.5*sin(2*PI*3*t))':s=48000:d=8")
    (rd / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": []}))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    i, _ = _ebur128(out)
    assert i < -25


def test_loudnorm_skips_silent_programme(tmp_path):
    curat, rd = _parts(tmp_path, None)  # no audio track at all: compose fills it with silence
    (rd / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": [], "loudnorm": True}))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    info = compose.probe(out)
    assert info["has_audio"] is True
    assert info["duration"] == pytest.approx(9.0, abs=0.15)
    # the silent programme must be detected and the file left byte-for-byte untouched
    before = hashlib.sha256(out.read_bytes()).hexdigest()
    assert compose.normalize_loudness(out) is False
    assert hashlib.sha256(out.read_bytes()).hexdigest() == before
    assert not (tmp_path / "youtube.loudnorm.mp4").exists()


def test_loudnorm_filter_text():
    measured = {"input_i": "-31.2", "input_tp": "-20.1", "input_lra": "3.4", "input_thresh": "-41.5",
                "target_offset": "0.3"}
    f = compose.loudnorm_filter(measured)
    assert f.startswith("loudnorm=I=-14:TP=-1.5:LRA=11:")
    assert "measured_I=-31.2" in f and "measured_TP=-20.1" in f and "offset=0.3" in f
    assert f.endswith(",aresample=48000")

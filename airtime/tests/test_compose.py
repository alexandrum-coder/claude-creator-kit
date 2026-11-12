from __future__ import annotations

import json
import subprocess

import pytest

import compose


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _source(path, size, rate, dur, audio=True):
    args = ["-f", "lavfi", "-i", "testsrc=size=%s:rate=%d:duration=%s" % (size, rate, dur)]
    if audio:
        args += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%s" % dur]
    args += ["-pix_fmt", "yuv420p", "-c:v", "libx264", "-shortest"]
    if audio:
        args += ["-c:a", "aac"]
    _ff(*args, str(path))


def test_compose_vertical_keeps_size(tmp_path):
    curat = tmp_path / "curat.mp4"
    _source(curat, "1080x1920", 30, 3)
    # fake intro: landscape, 25 fps, no audio
    intro = tmp_path / "rendered" / "intro.mp4"
    intro.parent.mkdir()
    _source(intro, "1920x1080", 25, 4, audio=False)
    overlay = tmp_path / "rendered" / "chapter_01.mov"
    _ff("-f", "lavfi", "-i", "color=c=red@0.5:s=1080x1920:r=30:d=1,format=argb",
        "-c:v", "qtrle", str(overlay))
    render = tmp_path / "rendered" / "render.json"
    render.write_text(json.dumps({"intro": "intro.mp4",
                                  "overlays": [{"file": "chapter_01.mov", "t": 1.0}]}))
    out = tmp_path / "youtube.mp4"

    compose.compose(curat, render, out)

    info = compose.probe(out)
    assert (info["width"], info["height"]) == (1080, 1920)
    assert info["fps"] == pytest.approx(30, abs=0.01)
    assert info["has_audio"] is True
    assert info["duration"] == pytest.approx(3 + 4, abs=0.3)


def test_compose_overlay_offset():
    src = {"width": 1920, "height": 1080, "fps": 30.0, "duration": 20.0, "has_audio": True}
    intro = {"width": 1280, "height": 720, "fps": 25.0, "duration": 4.0, "has_audio": False}
    graph, _maps = compose.build_filtergraph(src, intro, [{"file": "x.mov", "t": 10}], 4.0)
    assert "setpts=PTS-STARTPTS+14.000/TB" in graph
    assert "10.000/TB" not in graph
    # intro is conformed to the source
    assert "scale=1920:1080" in graph and "fps=30" in graph
    assert "aresample" in graph and "anullsrc" in graph


def test_probe_hevc_mov(tmp_path):
    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if "hevc_videotoolbox" not in enc:
        pytest.skip("hevc_videotoolbox not available")
    path = tmp_path / "Clip cu diacritice ăș.mov"
    _ff("-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30:duration=2",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-c:v", "hevc_videotoolbox", "-tag:v", "hvc1", "-c:a", "aac", "-shortest", str(path))
    info = compose.probe(path)
    assert (info["width"], info["height"]) == (1280, 720)
    assert info["fps"] == pytest.approx(30, abs=0.01)
    assert info["duration"] == pytest.approx(2, abs=0.3)
    assert info["has_audio"] is True


def test_compose_tags_output_bt709(tmp_path):
    # An HLG-tagged source (iPhone HDR left as is when ffmpeg has no zscale) must not leave the
    # output with an arbitrary colour tag: youtube.mp4 is SDR, tagged bt709.
    curat = tmp_path / "curat.mp4"
    _ff("-f", "lavfi", "-i", "testsrc=size=640x360:rate=30:duration=2",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest",
        "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", str(curat))
    intro = tmp_path / "rendered" / "intro.mp4"
    intro.parent.mkdir()
    _source(intro, "640x360", 30, 1, audio=False)
    render = tmp_path / "rendered" / "render.json"
    render.write_text(json.dumps({"intro": "intro.mp4", "overlays": []}))
    out = tmp_path / "youtube.mp4"

    compose.compose(curat, render, out)

    tags = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=color_primaries,color_transfer,color_space", "-of", "json", str(out)],
                          capture_output=True, text=True, check=True)
    s = json.loads(tags.stdout)["streams"][0]
    assert (s.get("color_primaries"), s.get("color_transfer"), s.get("color_space")) == ("bt709", "bt709", "bt709")

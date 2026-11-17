"""Element 0 of the montage upgrade: an extra audio track and a second video layer in compose.py.

Everything is optional: a render.json without the new keys must give exactly the 4e7906a filtergraph.
"""
from __future__ import annotations

import json
import re
import subprocess

import pytest

import compose

SRC = {"width": 1920, "height": 1080, "fps": 30.0, "duration": 20.0, "has_audio": True, "sample_rate": 48000}
INTRO = {"width": 1920, "height": 1080, "fps": 30.0, "duration": 4.0, "has_audio": False, "sample_rate": 0}

# Captured from compose.py at 4e7906a (before the upgrade), same inputs.
GOLDEN_OVERLAYS = (
    "[0:v]fps=30,setsar=1,format=yuv420p[sv];[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
    "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,setsar=1,format=yuv420p[iv];[0:a]aresample=48000,"
    "aformat=sample_fmts=fltp:channel_layouts=stereo[sa];anullsrc=r=48000:cl=stereo,atrim=0:4.000[ia];"
    "[iv][ia][sv][sa]concat=n=2:v=1:a=1[cv][ca];[2:v]scale=1920:1080,format=yuva420p,"
    "setpts=PTS-STARTPTS+7.000/TB[o0];[cv][o0]overlay=eof_action=pass:format=auto[v0];[3:v]scale=1920:1080,"
    "format=yuva420p,setpts=PTS-STARTPTS+13.500/TB[o1];[v0][o1]overlay=eof_action=pass:format=auto[v1]"
)
GOLDEN_NOAUDIO = (
    "[0:v]fps=29.97,setsar=1,format=yuv420p[sv];[1:v]scale=1916:1078:force_original_aspect_ratio=decrease,"
    "pad=1916:1078:(ow-iw)/2:(oh-ih)/2,fps=29.97,setsar=1,format=yuv420p[iv];anullsrc=r=48000:cl=stereo,"
    "atrim=0:20.000[sa];anullsrc=r=48000:cl=stereo,atrim=0:4.000[ia];[iv][ia][sv][sa]concat=n=2:v=1:a=1[cv][ca]"
)


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


# ------------------------------------------------------------------ regression (P1)

def test_old_render_gives_golden_graph():
    g, m = compose.build_filtergraph(SRC, INTRO, [{"file": "a.mov", "t": 3.0}, {"file": "b.mov", "t": 9.5}], 4.0)
    assert g == GOLDEN_OVERLAYS
    assert m == {"video": "[v1]", "audio": "[ca]"}
    src2 = dict(SRC, has_audio=False, width=1916, height=1078, fps=29.97)
    g2, m2 = compose.build_filtergraph(src2, INTRO, [], 4.0)
    assert g2 == GOLDEN_NOAUDIO
    assert m2 == {"video": "[cv]", "audio": "[ca]"}


def test_empty_extras_give_golden_graph():
    g, _ = compose.build_filtergraph(SRC, INTRO, [{"file": "a.mov", "t": 3.0}, {"file": "b.mov", "t": 9.5}], 4.0,
                                     extras={"audio": [], "layers": []})
    assert g == GOLDEN_OVERLAYS


def test_old_render_json_gives_same_ffmpeg_command(tmp_path, monkeypatch):
    rd = tmp_path / "render"
    rd.mkdir()
    (rd / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": [{"file": "c.mov", "t": 2}]}))
    calls = []
    monkeypatch.setattr(compose, "_probe_full", lambda p: dict(INTRO) if "intro" in str(p) else dict(SRC))
    monkeypatch.setattr(compose, "_run", lambda cmd: calls.append(cmd))
    compose.compose(tmp_path / "curat.mp4", rd / "render.json", tmp_path / "youtube.mp4")
    cmd = calls[0]
    inputs = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-i"]
    assert [p.rsplit("/", 1)[-1] for p in inputs] == ["curat.mp4", "intro.mp4", "c.mov"]
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert "amix" not in graph and "blend" not in graph and "loudnorm" not in graph


# ------------------------------------------------------------------ graph shape

def test_audio_track_is_delayed_and_mixed():
    extras = {"audio": [{"file": "m.wav", "t": 2.0, "gain_db": -6}], "layers": []}
    g, m = compose.build_filtergraph(SRC, INTRO, [], 4.0, extras=extras)
    # input index: 0 curat, 1 intro, no overlays, so the audio track is input 2; t is shifted by the intro
    assert "[2:a]" in g
    assert "volume=-6.0dB" in g
    assert "adelay=6000|6000" in g
    assert "amix=inputs=2:duration=first:normalize=0" in g
    assert m["audio"] != "[ca]"


def test_layer_difference_uses_rgb_blend():
    extras = {"audio": [], "layers": [{"file": "w.mp4", "t": 1.0, "mode": "difference"}]}
    g, m = compose.build_filtergraph(SRC, INTRO, [{"file": "a.mov", "t": 3.0}], 4.0, extras=extras)
    assert "[3:v]" in g  # after the single overlay
    assert "format=gbrp" in g
    assert "blend=all_mode=difference" in g
    assert "setpts=PTS-STARTPTS+5.000/TB" in g


def test_unknown_layer_mode_is_rejected():
    with pytest.raises(ValueError):
        compose.build_filtergraph(SRC, INTRO, [], 4.0,
                                  extras={"audio": [], "layers": [{"file": "w.mp4", "t": 0, "mode": "multiply"}]})


# ------------------------------------------------------------------ real encodes, measured

def _silent_parts(tmp_path, size="320x240", rate=25, dur=5, audio=False, color="0x404040"):
    curat = tmp_path / "curat.mp4"
    args = ["-f", "lavfi", "-i", "color=c=%s:s=%s:r=%d:d=%s" % (color, size, rate, dur)]
    if audio:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(dur), "-c:a", "aac"]
    _ff(*args, "-pix_fmt", "yuv420p", "-c:v", "libx264", str(curat))
    rd = tmp_path / "render"
    rd.mkdir()
    _ff("-f", "lavfi", "-i", "color=c=black:s=%s:r=%d:d=1" % (size, rate), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", str(rd / "intro.mp4"))
    return curat, rd


def test_tone_starts_at_t_plus_intro(tmp_path):
    curat, rd = _silent_parts(tmp_path, audio=True)
    _ff("-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=48000:duration=1", str(rd / "tone.wav"))
    (rd / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": [],
                                                "audio": [{"file": "tone.wav", "t": 2.0}]}))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "silencedetect=n=-40dB:d=0.3",
                        "-f", "null", "-"], capture_output=True, text=True)
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    assert ends, r.stderr[-800:]
    # intro 1 s + t 2 s = 3 s; AAC priming adds a few ms
    assert 3.0 <= ends[0] <= 3.1
    assert compose.probe(out)["duration"] == pytest.approx(6.0, abs=0.15)


def _silence_ends(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=n=-40dB:d=0.3",
                        "-f", "null", "-"], capture_output=True, text=True)
    return [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)], r.stderr


def test_audio_track_works_when_clip_has_no_audio(tmp_path):
    curat, rd = _silent_parts(tmp_path, audio=False)
    _ff("-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=48000:duration=1", str(rd / "tone.wav"))
    (rd / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": [],
                                                "audio": [{"file": "tone.wav", "t": 1.0}]}))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    info = compose.probe(out)
    assert info["has_audio"] is True
    assert info["duration"] == pytest.approx(6.0, abs=0.15)
    # the clip itself is silent (anullsrc), so the only sound is the tone: intro 1 s + t 1 s = 2 s
    ends, log = _silence_ends(out)
    assert ends, log[-800:]
    assert 2.0 <= ends[0] <= 2.1


def _yavg(path, t, crop=None):
    vf = ("crop=%s," % crop if crop else "") + "signalstats,metadata=print:key=lavfi.signalstats.YAVG"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(t), "-i", str(path), "-frames:v", "1",
                        "-vf", vf, "-f", "null", "-"], capture_output=True, text=True)
    return float(re.findall(r"YAVG=([0-9.]+)", r.stderr)[-1])


def test_white_difference_layer_inverts_only_inside_window(tmp_path):
    curat, rd = _silent_parts(tmp_path, audio=True, color="0x404040")
    # white box 160x120 in the middle of a black 320x240 frame, 1 s long
    _ff("-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=1", "-vf",
        "drawbox=x=80:y=60:w=160:h=120:color=white:t=fill", "-pix_fmt", "yuv420p", "-c:v", "libx264",
        str(rd / "white.mp4"))
    (rd / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": [],
                                                "layers": [{"file": "white.mp4", "t": 2.0, "mode": "difference"}]}))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    before = _yavg(out, 1.5, "100:80:110:80")        # inside the box area, before the layer starts
    inside = _yavg(out, 3.5, "100:80:110:80")        # intro 1 + t 2 = 3 s, layer lasts 1 s
    outside = _yavg(out, 3.5, "60:40:0:0")           # corner, black part of the layer
    after = _yavg(out, 4.6, "100:80:110:80")
    # limited range: Y = 16 + 219 * RGB / 255; 0x404040 -> 71.0, its RGB difference with white 0xBFBFBF -> 180.0
    assert before == pytest.approx(71, abs=3)
    assert inside == pytest.approx(180, abs=3)
    assert outside == pytest.approx(71, abs=3)
    assert after == pytest.approx(71, abs=3)

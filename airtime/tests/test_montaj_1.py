"""Element 1 of the montage upgrade: ADUM-style transitions, opening and warm grade in compose.py,
plus slot placement in montaj.py (PLAN, Nota 2.8, D-25...D-34).

All keys are optional; without them compose.py keeps the 4e7906a filtergraph (test_montaj_0 goldens).
"""
from __future__ import annotations

import json
import re
import subprocess

import pytest

import compose


def _montaj():
    import montaj as m  # imported inside the tests so a missing module fails each test, not the collection
    return m


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _words(*spans):
    return [{"word": "w%d" % i, "start": s, "end": e} for i, (s, e) in enumerate(spans)]


# ------------------------------------------------------------------ 1. find_slots

def test_find_slots_gap_rules():
    m = _montaj()
    tr = {"segments": [
        {"start": 0, "end": 2, "text": "a", "words": _words((0.0, 1.0), (2.0, 3.0))},          # gap 1.0 -> none
        {"start": 4.1, "end": 6, "text": "b", "words": _words((4.1, 5.0), (6.5, 7.0))},        # 1.1 and 1.5
        {"start": 10, "end": 11, "text": "c", "words": _words((10.0, 11.0))},                  # 3.0 across segments
    ]}
    slots = m.find_slots(tr)
    assert [s["t"] for s in slots] == pytest.approx([3.2, 5.2, 7.2])
    assert [s["d"] for s in slots] == pytest.approx([0.44, 0.64, 1.16])
    assert [s["gap"] for s in slots] == pytest.approx([1.1, 1.5, 3.0])


def test_find_slots_skips_short_dissolves_and_empty():
    m = _montaj()
    tr = {"segments": [{"start": 0, "end": 3, "text": "x", "words": _words((0.0, 1.0), (1.9, 3.0))}]}
    assert m.find_slots(tr, min_gap=0.5) == []          # gap 0.9 -> D = 0.34 < 0.4, skipped
    assert m.find_slots({"segments": []}) == []
    assert m.find_slots({"segments": [{"start": 0, "end": 1, "text": "", "words": []}]}) == []


def test_accel_weight_and_motion_progress():
    m = _montaj()
    assert m.accel_weight(0) == pytest.approx(0)
    assert m.accel_weight(0.45) == pytest.approx(0.34875, abs=1e-3)
    assert m.accel_weight(0.7097) == pytest.approx(0.55, abs=1e-3)
    assert m.accel_weight(1) == pytest.approx(1, abs=1e-3)
    # catalog section 3: keyframes [0, 2, 9, 10] frames at 25 fps -> [0, 0.13, 0.97, 1]
    for sec, p in ((0, 0), (0.08, 0.13), (0.2, 0.49), (0.36, 0.97), (0.4, 1), (1.0, 1)):
        assert m.motion_progress(sec) == pytest.approx(p, abs=1e-3)


def _ffexpr(expr, **var):
    """Evaluates the small ffmpeg expression subset used by progress_expr: if, lt, max and arithmetic."""
    ns = {"IF": lambda c, a, b: a if c else b, "lt": lambda a, b: a < b, "max": max, **var}
    return eval(re.sub(r"\bif\(", "IF(", expr), {"__builtins__": {}}, ns)


def test_progress_expr_matches_motion_progress():
    m = _montaj()
    expr = m.progress_expr("t")
    assert set(re.findall(r"[a-z]+(?=\()", expr)) <= {"if", "lt", "max"}
    for k in range(-2, 60):                              # 0.01 s steps, the keyframe borders included
        sec = k / 100
        assert _ffexpr(expr, t=sec) == pytest.approx(m.motion_progress(sec), abs=1e-3), sec


def test_map_time():
    m = _montaj()
    tr = [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}, {"t": 8.0, "d": 0.5, "kind": "motion_blur_dissolve"}]
    assert m.map_time(2.0, tr) == pytest.approx(2.0)
    assert m.map_time(3.5, tr) == pytest.approx(3.5)    # inside the first window: still the A frame
    assert m.map_time(6.0, tr) == pytest.approx(5.0)
    assert m.map_time(9.0, tr) == pytest.approx(7.5)


# ------------------------------------------------------------------ helpers for the render tests

def _yavg(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf",
                        "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    return [float(x) for x in re.findall(r"YAVG=([0-9.]+)", r.stdout)]


def _uv(path, frame):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf",
                        "select=eq(n\\,%d),signalstats,metadata=print:file=-" % frame, "-an", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    u = float(re.search(r"UAVG=([0-9.]+)", r.stdout).group(1))
    v = float(re.search(r"VAVG=([0-9.]+)", r.stdout).group(1))
    return u, v


def _intro(rd, color="black", dur=1, size="320x240"):
    _ff("-f", "lavfi", "-i", "color=c=%s:s=%s:r=25:d=%s" % (color, size, dur), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", str(rd / "intro.mp4"))


def _two_tone_clip(path, cut, total, size="320x240", audio=None):
    """Luma 50 (RGB) until `cut`, luma 200 after."""
    args = ["-f", "lavfi", "-i", "color=c=0x323232:s=%s:r=25:d=%s" % (size, cut),
            "-f", "lavfi", "-i", "color=c=0xC8C8C8:s=%s:r=25:d=%s" % (size, total - cut)]
    fc = "[0:v][1:v]concat=n=2:v=1:a=0[v]"
    maps = ["-map", "[v]"]
    if audio:
        args += ["-f", "lavfi", "-i", audio]
        maps += ["-map", "2:a", "-c:a", "aac", "-shortest"]
    _ff(*args, "-filter_complex", fc, *maps, "-pix_fmt", "yuv420p", "-c:v", "libx264", str(path))


def _compose(tmp_path, curat, spec):
    rd = tmp_path / "render"
    (rd / "render.json").write_text(json.dumps(dict({"intro": "intro.mp4", "overlays": []}, **spec)))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    return out


@pytest.fixture
def rd(tmp_path):
    d = tmp_path / "render"
    d.mkdir()
    return d


# ------------------------------------------------------------------ 2-4. dissolve_accel in youtube.mp4

def test_dissolve_accel_curve_duration_and_audio(tmp_path, rd):
    _intro(rd)
    curat = tmp_path / "curat.mp4"
    tone = "aevalsrc='if(gte(t,6),0.5*sin(2*PI*440*t),0)':s=48000:d=10"
    _two_tone_clip(curat, 4.0, 10.0, audio=tone)
    out = _compose(tmp_path, curat, {"transitions": [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}]})
    info = compose.probe(out)
    assert info["duration"] == pytest.approx(1 + 10 - 1, abs=0.04)
    ys = _yavg(out)
    ref_a, ref_b = ys[25 + 50], ys[25 + 150]            # output 3.0 s (A) and 7.0 s (B), measured (N1)
    m = _montaj()
    # transition on the output timeline: [4.0, 5.0]; frames 108, 115, 121 -> q = 0.32, 0.60, 0.84
    for f, q in ((108, 0.32), (115, 0.60), (121, 0.84)):
        got = (ys[f] - ref_a) / (ref_b - ref_a)
        assert got == pytest.approx(m.accel_weight(q), abs=0.04)
    # the tone starts at clip 6.0 -> output 1 + 6 - 1 = 6.0
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-af",
                        "silencedetect=n=-40dB:d=0.3", "-f", "null", "-"], capture_output=True, text=True)
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    assert ends and ends[-1] == pytest.approx(6.0, abs=0.04)


def test_transition_on_clip_without_audio_and_intro_dissolve_duration(tmp_path, rd):
    _intro(rd, dur=2)
    curat = tmp_path / "curat.mp4"
    _two_tone_clip(curat, 4.0, 10.0)
    out = _compose(tmp_path, curat, {"transitions": [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}],
                                     "opening": {"intro_dissolve": 1.24}})
    info = compose.probe(out)
    assert info["has_audio"] is True
    assert info["duration"] == pytest.approx(2 + 10 - 1 - 1.24, abs=0.04)


def test_dissolve_accel_then_motion_blur_in_one_clip(tmp_path, rd):
    """Found at element 6 (Nota 2.15): the piece after a dissolve_accel kept the 1/25 time base while the
    blended motion_blur pieces had 1/1000000, and xfade refused the pair ("timebase do not match")."""
    _intro(rd)
    curat = tmp_path / "curat.mp4"
    _two_tone_clip(curat, 6.0, 12.0)
    out = _compose(tmp_path, curat, {"transitions": [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"},
                                                     {"t": 8.0, "d": 1.0, "kind": "motion_blur_dissolve"}]})
    assert compose.probe(out)["duration"] == pytest.approx(1 + 12 - 2, abs=0.04)


# ------------------------------------------------------------------ 5. time mapping in the graph

def test_overlay_time_is_mapped_after_transition():
    src = {"width": 320, "height": 240, "fps": 25.0, "duration": 10.0, "has_audio": True, "sample_rate": 48000}
    intro = {"width": 320, "height": 240, "fps": 25.0, "duration": 1.0, "has_audio": False, "sample_rate": 0}
    g, _ = compose.build_filtergraph(src, intro, [{"file": "a.mov", "t": 6.0}], 1.0,
                                     extras={"transitions": [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}]})
    assert "setpts=PTS-STARTPTS+6.000/TB[o0]" in g
    g2, _ = compose.build_filtergraph(src, dict(intro, duration=2.0), [{"file": "a.mov", "t": 6.0}], 2.0,
                                      extras={"transitions": [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}],
                                              "opening": {"intro_dissolve": 1.24}})
    assert "setpts=PTS-STARTPTS+5.760/TB[o0]" in g2


# ------------------------------------------------------------------ 6-7. opening

def _black_y(tmp_path):
    p = tmp_path / "black.mp4"
    _ff("-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=0.2", "-pix_fmt", "yuv420p", "-c:v", "libx264", str(p))
    return _yavg(p)[0]


def test_fade_in_from_black(tmp_path, rd):
    _intro(rd, color="0x808080", dur=2)                  # static synthetic intro (N5)
    curat = tmp_path / "curat.mp4"
    _two_tone_clip(curat, 1.0, 2.0)
    out = _compose(tmp_path, curat, {"opening": {"fade_in": 0.72}})
    ys = _yavg(out)
    y0, yf = _black_y(tmp_path), ys[30]
    for f, want in ((0, 0), (5, 22), (10, 52), (15, 83), (18, 99)):
        assert 100 * (ys[f] - y0) / (yf - y0) == pytest.approx(want, abs=8)


def test_intro_dissolve_follows_accel_curve(tmp_path, rd):
    _ff("-f", "lavfi", "-i", "color=c=0x323232:s=320x240:r=25:d=2", "-pix_fmt", "yuv420p", "-c:v", "libx264",
        str(rd / "intro.mp4"))
    curat = tmp_path / "curat.mp4"
    _ff("-f", "lavfi", "-i", "color=c=0xC8C8C8:s=320x240:r=25:d=4", "-pix_fmt", "yuv420p", "-c:v", "libx264",
        str(curat))
    out = _compose(tmp_path, curat, {"opening": {"intro_dissolve": 1.24}})
    ys = _yavg(out)
    ref_a, ref_b = ys[5], ys[75]
    m = _montaj()
    # offset = 2 - 1.24 = 0.76 s; frames 27, 35, 45 -> q = 0.258, 0.516, 0.839
    for f in (27, 35, 45):
        q = (f / 25 - 0.76) / 1.24
        assert (ys[f] - ref_a) / (ref_b - ref_a) == pytest.approx(m.accel_weight(q), abs=0.04)


# ------------------------------------------------------------------ 8. warm grade

def test_warm_grade_shifts_chroma(tmp_path, rd):
    _intro(rd)
    curat = tmp_path / "curat.mp4"
    _ff("-f", "lavfi", "-i", "color=c=0x808080:s=320x240:r=25:d=2", "-pix_fmt", "yuv420p", "-c:v", "libx264",
        str(curat))
    plain = _compose(tmp_path, curat, {})
    u0, v0 = _uv(plain, 40)
    plain.rename(tmp_path / "plain.mp4")
    warm = _compose(tmp_path, curat, {"grade": "cald"})
    u1, v1 = _uv(warm, 40)
    assert v1 - v0 >= 2 and u0 - u1 >= 2
    iu, iv = _uv(warm, 5)                                # the intro (black) keeps neutral chroma
    assert abs(iu - 128) < 1.5 and abs(iv - 128) < 1.5


# ------------------------------------------------------------------ 9. motion_blur_dissolve (ffmpeg)

def _marker_centroid(path, frame, w, h, bg):
    """Luma-weighted centroid (fraction of height) of pixels brighter than the background, on a 1/4 scale copy."""
    sw, sh = w // 4, h // 4
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "select=eq(n\\,%d),scale=%d:%d,format=gray" % (frame, sw, sh), "-frames:v", "1",
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    sy = sm = 0.0
    peak = 0
    for i, v in enumerate(r.stdout):
        if v > bg + 12:
            sy += (i // sw) * (v - bg)
            sm += v - bg
            peak = max(peak, v)
    return (sy / sm + 0.5) / sh, peak


def _edge_ratio(path, frame, w, h):
    """Steepest vertical step through the marker divided by the marker's contrast, on a 1/2 scale copy.
    A dissolve to a flat B scales the step and the contrast alike, so only a blur lowers the ratio (M1)."""
    sw, sh = w // 2, h // 2
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "select=eq(n\\,%d),scale=%d:%d,format=gray" % (frame, sw, sh), "-frames:v", "1",
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    data = r.stdout
    col = max(range(len(data)), key=lambda i: data[i]) % sw
    prof = [data[y * sw + col] for y in range(sh)]
    contrast = max(prof) - sorted(prof)[sh // 2]
    return max(abs(prof[y + 1] - prof[y]) for y in range(sh - 1)) / contrast


@pytest.mark.parametrize("w,h", [(1920, 1080), (1916, 1078)])
def test_motion_blur_dissolve_moves_and_blurs(tmp_path, rd, w, h):
    _intro(rd, size="%dx%d" % (w, h))
    curat = tmp_path / "curat.mp4"
    bw, bh = w // 12, h // 18
    y_mark = h // 4
    t, d = 3.0, 1.16
    cut = t + d
    _ff("-f", "lavfi", "-i", "color=c=0x646464:s=%dx%d:r=25:d=%s,drawbox=x=%d:y=%d:w=%d:h=%d:c=white:t=fill"
        % (w, h, cut, (w - bw) // 2, y_mark - bh // 2, bw, bh),
        "-f", "lavfi", "-i", "color=c=0x646464:s=%dx%d:r=25:d=%s" % (w, h, 6 - cut),
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "12", str(curat))
    out = _compose(tmp_path, curat, {"transitions": [{"t": t, "d": d, "kind": "motion_blur_dissolve"}]})
    assert compose.probe(out)["duration"] == pytest.approx(1 + 6 - d, abs=0.04)
    m = _montaj()
    bg = _yavg(curat)[0]
    t0_frame = 25 * (1 + t - 0.12)                       # output frame where the move starts
    y0, peak0 = _marker_centroid(out, int(round(t0_frame)), w, h, bg)
    assert y0 == pytest.approx(0.25, abs=0.01)
    for sec in (0.08, 0.20, 0.36):
        z = 1 + 0.27 * m.motion_progress(sec)
        want = (y0 - (1 - 1 / z)) * z                   # D-34: y window at the bottom, ih - ih/z
        got, _ = _marker_centroid(out, int(round(t0_frame + 25 * sec)), w, h, bg)
        assert got == pytest.approx(want, abs=0.015)
    r0 = _edge_ratio(out, int(round(t0_frame)), w, h)
    r1 = _edge_ratio(out, int(round(t0_frame + 25 * 0.36)), w, h)
    assert r1 < 0.5 * r0, (r0, r1)                       # M1: the blur on A, not the dissolve, softens the edge


def _band_std(path, frame, w, h, y0, y1):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "select=eq(n\\,%d),format=gray" % frame, "-frames:v", "1", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    vals = [r.stdout[y * w + x] for y in range(int(y0 * h), int(y1 * h)) for x in range(w // 8, w - w // 8)]
    mean = sum(vals) / len(vals)
    return (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5


@pytest.mark.parametrize("d", [1.16, 0.6])
def test_motion_blur_dissolve_focus_pull_on_b_and_short_d(tmp_path, rd, d):
    """M6: B starts blurred and comes into focus over 0.44k...1.56k s, k = d / 1.16; with a shorter d only
    the dissolve and this focus pull scale, the move on A keeps its 0.4 s (D-29)."""
    w, h = 640, 360
    _intro(rd, size="%dx%d" % (w, h))
    curat = tmp_path / "curat.mp4"
    t = 3.0
    cut = t + d
    # A: flat grey with a white marker; B: 2 px stripes (gone under the 4 px blur) over 80 px stripes (kept)
    _ff("-f", "lavfi", "-i", "color=c=0x646464:s=%dx%d:r=25:d=%s,drawbox=x=%d:y=%d:w=%d:h=%d:c=white:t=fill"
        % (w, h, cut, (w - w // 12) // 2, h // 4 - h // 36, w // 12, h // 18),
        "-f", "lavfi", "-i", "nullsrc=s=%dx%d:r=25:d=%s,geq=lum='100+30*if(lt(Y,%d),2*mod(floor(X/2),2)-1,"
        "2*mod(floor(X/80),2)-1)':cb=128:cr=128" % (w, h, 6 - cut, int(0.72 * h)),
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "8", str(curat))
    out = _compose(tmp_path, curat, {"transitions": [{"t": t, "d": d, "kind": "motion_blur_dissolve"}]})
    assert compose.probe(out)["duration"] == pytest.approx(1 + 6 - d, abs=0.04)
    k = d / 1.16

    def rel(sec_after_b):                                # fine / coarse stripe contrast: the dissolve cancels out
        f = int(round(25 * (1 + t + sec_after_b)))
        return _band_std(out, f, w, h, 0.55, 0.70) / _band_std(out, f, w, h, 0.76, 0.95)

    end = rel(6 - cut - 0.2)
    for sec, want in ((0.4 * k, 0.0), (k, 0.5), (1.7 * k, 1.0)):
        assert rel(sec) / end == pytest.approx(want, abs=0.15), (d, sec)
    m = _montaj()
    bg = _yavg(curat)[0]
    y0, _ = _marker_centroid(out, int(round(25 * (1 + t - 0.12))), w, h, bg)
    z = 1 + 0.27 * m.motion_progress(0.2)               # the move is not scaled with d
    got, _ = _marker_centroid(out, int(round(25 * (1 + t - 0.12 + 0.2))), w, h, bg)
    assert got == pytest.approx((y0 - (1 - 1 / z)) * z, abs=0.015)


# ------------------------------------------------------------------ 10. validation and vertical clips

def test_validation_errors():
    src = {"width": 320, "height": 240, "fps": 25.0, "duration": 20.0, "has_audio": True, "sample_rate": 48000}
    intro = {"width": 320, "height": 240, "fps": 25.0, "duration": 1.0, "has_audio": False, "sample_rate": 0}
    close = [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}, {"t": 5.0, "d": 1.0, "kind": "dissolve_accel"}]
    with pytest.raises(ValueError):
        compose.build_filtergraph(src, intro, [], 1.0, extras={"transitions": close})
    with pytest.raises(ValueError):
        compose.build_filtergraph(src, intro, [], 1.0,
                                  extras={"transitions": [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel",
                                                           "b_file": "b.mp4"}]})
    with pytest.raises(ValueError):
        compose.build_filtergraph(src, intro, [], 1.0, extras={"transitions": [{"t": 3.0, "d": 1.0, "kind": "spin"}]})
    with pytest.raises(ValueError):
        compose.build_filtergraph(src, intro, [], 1.0, extras={"grade": "albastru"})


@pytest.mark.parametrize("t2,ok", [(5.48, False), (5.52, True)])
def test_spacing_limit_is_exact(t2, ok):
    # M4: t2 - t1 >= 2.4 * d1 + 0.12 = 2.52 s; one 25 fps frame under the limit is refused
    src = {"width": 320, "height": 240, "fps": 25.0, "duration": 20.0}
    pair = [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}, {"t": t2, "d": 1.0, "kind": "dissolve_accel"}]
    if ok:
        assert [x["t"] for x in compose.check_transitions(pair, src)] == [3.0, t2]
    else:
        with pytest.raises(ValueError):
            compose.check_transitions(pair, src)


@pytest.mark.parametrize("t,ok", [(17.64, False), (17.6, True), (0.08, False), (0.12, True)])
def test_clip_edges_limit_is_exact(t, ok):
    # M4: the last transition needs 2.4 * d before the clip ends; the first starts at 0.12 s or later
    src = {"width": 320, "height": 240, "fps": 25.0, "duration": 20.0}
    one = [{"t": t, "d": 1.0, "kind": "dissolve_accel"}]
    if ok:
        assert compose.check_transitions(one, src)[0]["t"] == pytest.approx(t)
    else:
        with pytest.raises(ValueError):
            compose.check_transitions(one, src)


def test_vertical_clip_skips_transitions(tmp_path, rd, capsys):
    _intro(rd, size="180x320")
    curat = tmp_path / "curat.mp4"
    _two_tone_clip(curat, 4.0, 8.0, size="180x320")
    out = _compose(tmp_path, curat, {"transitions": [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}]})
    assert compose.probe(out)["duration"] == pytest.approx(9.0, abs=0.04)
    assert "tranzi" in capsys.readouterr().err

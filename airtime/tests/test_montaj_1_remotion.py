"""Element 1, Remotion part: MotionBlurDissolve and TitlePop checked on rendered stills (PLAN, Nota 2.8, test 12).

Needs AIRTIME_REMOTION_DIR = a remotion folder with node_modules (an isolated copy, never an install:
the webpack cache is written next to the nearest package.json). Without it the tests are skipped with
the reason shown. Synthetic fixtures are written into <AIRTIME_REMOTION_DIR>/public.
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
from pathlib import Path

import pytest

RDIR = os.environ.get("AIRTIME_REMOTION_DIR")
pytestmark = pytest.mark.skipif(not RDIR, reason="AIRTIME_REMOTION_DIR nu e setat (copie izolata a remotion/)")

W, H = 1920, 1080
MBD_FRAMES = [0, 2, 3, 5, 9, 10, 14, 18, 32, 42]
KEYS = ((0, 0.0), (2, 0.13), (9, 0.97), (10, 1.0))      # catalog section 3, frames at 25 fps


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _progress(frame):
    for (f0, p0), (f1, p1) in zip(KEYS, KEYS[1:]):
        if frame <= f1:
            return p0 + (p1 - p0) * (frame - f0) / (f1 - f0)
    return 1.0


def _stills(rdir, comp, props, frames, out):
    pf = out / "props.json"
    out.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(props))
    subprocess.run(["node", "stills.mjs", "--id", comp, "--props", str(pf), "--frames",
                    ",".join(str(f) for f in frames), "--out-dir", str(out)],
                   cwd=rdir, check=True, capture_output=True, text=True, timeout=600)
    return {f: out / ("frame_%03d.png" % f) for f in frames}


def _gray(png, sw=W // 2, sh=H // 2):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(png), "-vf", "scale=%d:%d,format=gray" % (sw, sh),
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    return r.stdout, sw, sh


def _alpha(png):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(png), "-vf", "alphaextract,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    return r.stdout


def _region(data, sw, x0, x1, y0, y1):
    return [data[y * sw + x] for y in range(y0, y1) for x in range(x0, x1)]


def _marker(data, sw, sh):
    """Centroid (full-resolution px) and steepest vertical step of the bright marker divided by its contrast
    along the same column. B's stripes are vertical, so B's opacity scales step and contrast alike (M1)."""
    bg = statistics.mean(_region(data, sw, 0, 40, 0, 40))
    peak = max(data)
    thr = (bg + peak) / 2
    sx = sy = sm = 0.0
    for i, v in enumerate(data):
        if v > thr:
            sx += (i % sw) * (v - bg)
            sy += (i // sw) * (v - bg)
            sm += v - bg
    cx, cy = sx / sm, sy / sm
    col = int(round(cx))
    prof = [data[y * sw + col] for y in range(sh)]
    edge = max(abs(prof[y + 1] - prof[y]) for y in range(sh - 1)) / (max(prof) - sorted(prof)[sh // 2])
    return (cx + 0.5) * 2, (cy + 0.5) * 2, edge


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    rdir = Path(RDIR)
    pub = rdir / "public"
    pub.mkdir(exist_ok=True)
    _ff("-f", "lavfi", "-i", "color=c=0x404040:s=%dx%d:r=30:d=3,drawbox=x=%d:y=%d:w=120:h=60:c=white:t=fill"
        % (W, H, W // 2 - 60, H // 2 - 30), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "10", str(pub / "a.mp4"))
    _ff("-f", "lavfi", "-i", "nullsrc=s=%dx%d:r=30:d=3,geq=lum='if(mod(floor(X/40),2),220,140)':cb=128:cr=128"
        % (W, H), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "10", str(pub / "b.mp4"))
    out = tmp_path_factory.mktemp("stills")
    base = {"width": W, "height": H, "a": "a.mp4", "b": "b.mp4"}
    return {
        "mbd25": _stills(rdir, "MotionBlurDissolve", dict(base, fps=25), MBD_FRAMES, out / "mbd25"),
        "mbd30": _stills(rdir, "MotionBlurDissolve", dict(base, fps=30), [0, 3, 6, 12], out / "mbd30"),
        "pop": _stills(rdir, "TitlePop", {"width": W, "height": H, "fps": 25, "text": "Doua cuvinte", "hold": 1.0},
                       [0, 28, 31, 34], out / "pop"),
    }


def test_a_moves_on_the_measured_keyframes(rendered):
    for f in (0, 2, 5, 9, 10):
        x, y, _ = _marker(*_gray(rendered["mbd25"][f]))
        p = (144 - (y - H / 2)) / 288
        assert p == pytest.approx(_progress(f), abs=0.05), "cadrul %d" % f
        assert x - W / 2 == pytest.approx(60 - 120 * _progress(f), abs=5), "deriva x, cadrul %d" % f


def test_b_opacity_and_sharpness(rendered):
    def region(f):
        data, sw, _ = _gray(rendered["mbd25"][f])
        return _region(data, sw, 50, 290, 50, 150)       # 5 stripe periods of B at scale 1.2, away from the marker
    ya, yb = statistics.mean(region(0)), statistics.mean(region(42))
    for f, want in ((3, 0.0), (10, 7 / 29), (18, 15 / 29), (32, 1.0)):
        assert (statistics.mean(region(f)) - ya) / (yb - ya) == pytest.approx(want, abs=0.05), "cadrul %d" % f
    s14, s32, s42 = (statistics.pstdev(region(f)) for f in (14, 32, 42))
    assert s14 < s32 < s42                                 # focus pull on B (opacity adds to it, accepted)


def test_a_gets_blurrier(rendered):
    edges = [_marker(*_gray(rendered["mbd25"][f]))[2] for f in (0, 5, 10)]
    # measured: [0.81, 0.23, 0.06] with the blur, [0.81, 0.61, 0.80] without it (M1, Nota 2.11)
    assert edges[1] < 0.5 * edges[0] and edges[2] < 0.5 * edges[1], edges


def test_keyframes_are_in_seconds_at_30_fps(rendered):
    _, y0, _ = _marker(*_gray(rendered["mbd30"][0]))
    _, y6, _ = _marker(*_gray(rendered["mbd30"][6]))
    _, y12, _ = _marker(*_gray(rendered["mbd30"][12]))
    assert (144 - (y0 - H / 2)) / 288 == pytest.approx(0, abs=0.05)
    # M2: 0.2 s = frame 6 at 30 fps, progress 0.13 + 0.84 * 0.12 / 0.28 = 0.49; keyframes counted in
    # frames would give 0.13 + 0.84 * 4 / 7 = 0.61 here
    assert (144 - (y6 - H / 2)) / 288 == pytest.approx(0.49, abs=0.05)
    assert (144 - (y12 - H / 2)) / 288 == pytest.approx(1, abs=0.05)   # 0.4 s = frame 12 at 30 fps


def test_title_pop_is_full_at_once_then_fades_in_12_frames(rendered):
    a0 = _alpha(rendered["pop"][0])
    assert max(a0) >= 250 and sum(1 for v in a0 if v > 128) > 500
    for f, k in ((28, 3), (31, 6), (34, 9)):               # duration 25 + 12 frames, fade from frame 25
        assert max(_alpha(rendered["pop"][f])) / 255 == pytest.approx(1 - k / 12, abs=0.05), "cadrul %d" % f


def _yellow_px(video, frame, w, h):
    """Pixels with the TitlePop yellow chroma (#EBC400: Cb about 23) in frame number `frame`."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-frames:v", "1", "-vf",
                        "select=eq(n\\,%d),format=yuv444p,extractplanes=u" % frame, "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    return sum(1 for v in r.stdout[: w * h] if v < 80)


def test_render_mjs_title_pops_reach_youtube_mp4_at_t(tmp_path):
    """M6: render.mjs turns props.title_pops into titlepop_NN.mov with alpha and lists it in the overlays
    with its t; compose.py shows nothing of it before t and the yellow title right after t."""
    import compose
    w, h, t = 640, 360, 2.52                             # a whole 25 fps frame (63), so "frame -1" is exact
    rd = tmp_path / "render"
    props = {"width": w, "height": h, "fps": 25, "colors": {"primary": "#14213d", "accent": "#fca311"},
             "intro": {"title": "Titlu", "channel": "Canal"}, "chapters": [], "lists": [],
             "title_pops": [{"t": t, "text": "Doua cuvinte", "hold": 1.0}]}
    pf = tmp_path / "props.json"
    pf.write_text(json.dumps(props))
    r = subprocess.run(["node", "render.mjs", "--props", str(pf), "--out-dir", str(rd)], cwd=RDIR, check=True,
                       capture_output=True, text=True, timeout=900)
    spec = json.loads(r.stdout)
    assert spec["overlays"] == [{"file": "titlepop_01.mov", "t": t}]
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=pix_fmt:format=duration", "-of", "json", str(rd / "titlepop_01.mov")],
                          capture_output=True, text=True, check=True)
    meta = json.loads(info.stdout)
    assert meta["streams"][0]["pix_fmt"].startswith("yuva")
    assert float(meta["format"]["duration"]) == pytest.approx((25 + 12) / 25, abs=0.04)
    (rd / "render.json").write_text(r.stdout)
    curat = tmp_path / "curat.mp4"
    _ff("-f", "lavfi", "-i", "color=c=0x606060:s=%dx%d:r=25:d=6" % (w, h), "-pix_fmt", "yuv420p", "-c:v", "libx264",
        str(curat))
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rd / "render.json", out)
    intro = compose.probe(rd / "intro.mp4")["duration"]
    first = int(round(25 * (intro + t)))                 # first output frame of the title
    assert _yellow_px(out, first - 1, w, h) == 0
    assert _yellow_px(out, first, w, h) > 200            # full at once (ADUM #5)

"""Element 5, Remotion part: ImpactCaption rendered through overlay.mjs, then blended into a reel with a difference
blend (PLAN, Note 2.20, D-58...D-64).

Needs AIRTIME_REMOTION_DIR = an isolated remotion copy with node_modules (never an install); skipped otherwise.
The render runs inside the tests (cached per module), so a missing composition is a failure, not a setup error.
Frames are read as full-range gray (format=gray), where an RGB inversion gives exactly Y = 255 - Y.
The caption band is centred at 22% of the height; rows 12-32% are treated as the band.
Thresholds from <SCRATCH>/upgrade/el5-masuratori-cod-4.txt (source `gradients`, D-64).
"""
from __future__ import annotations

import json
import os
import subprocess

import pytest

RDIR = os.environ.get("AIRTIME_REMOTION_DIR")
pytestmark = pytest.mark.skipif(not RDIR, reason="AIRTIME_REMOTION_DIR nu e setat (copie izolata a remotion/)")

W, H, FPS = 540, 960, 25
B0, B1 = int(H * 0.12), int(H * 0.32)
LONG = "W" * 30                            # 30 of the widest letter, the maximum (P4)
_CACHE = {}


def _mov(tmp_path_factory, items, duration):
    key = (json.dumps(items), duration)
    if key not in _CACHE:
        tmp = tmp_path_factory.mktemp("el5rem")
        props = {"width": W, "height": H, "fps": FPS, "items": items, "duration": duration}
        pf = tmp / "props.json"
        pf.write_text(json.dumps(props))
        out = tmp / "impact.mov"
        r = subprocess.run(["node", "overlay.mjs", "--id", "ImpactCaption", "--props", str(pf), "--out", str(out)],
                           cwd=RDIR, capture_output=True, text=True, timeout=900)
        assert r.returncode == 0, r.stderr[-800:]
        _CACHE[key] = out
    return _CACHE[key]


def _frame(path, n, filt=""):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "select=eq(n\\,%d),%sformat=gray" % (n, filt), "-frames:v", "1", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    assert len(r.stdout) == W * H, "cadrul %d lipseste" % n
    return r.stdout


def _rows(frame, y0, y1):
    return frame[y0 * W:y1 * W]


def _outside_band(frame):
    return frame[:B0 * W] + frame[B1 * W:]


STOP = [{"text": "STOP", "from": 10, "dur": 8}]


def test_mask_is_opaque_and_lasts_its_duration(tmp_path_factory):
    mov = _mov(tmp_path_factory, STOP, 1.2)
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                                      "-show_entries", "stream=nb_read_frames", "-of", "json", str(mov)],
                                     capture_output=True, text=True, check=True).stdout)["streams"][0]
    assert int(info["nb_read_frames"]) == 30
    for n in (0, 10, 29):
        assert min(_frame(mov, n, "alphaextract,")) >= 250, "cadrul %d are transparenta" % n


def test_caption_shows_exactly_in_its_frames_and_only_in_the_band(tmp_path_factory):
    mov = _mov(tmp_path_factory, STOP, 1.2)
    for n, on in ((9, False), (10, True), (17, True), (18, False)):
        f = _frame(mov, n)
        band = _rows(f, B0, B1)
        if on:
            assert max(band) >= 250, "cadrul %d fara text" % n
        else:
            assert max(band) <= 5, "cadrul %d are text" % n
        assert max(_outside_band(f)) <= 5, "cadrul %d are alb in afara benzii" % n


def test_a_thirty_character_caption_fits(tmp_path_factory):
    assert len(LONG) == 30
    mov = _mov(tmp_path_factory, [{"text": LONG, "from": 0, "dur": 5}], 0.2)
    y = int(H * 0.22)
    row = _frame(mov, 2)[y * W:(y + 1) * W]
    xs = [x for x, v in enumerate(row) if v > 128]
    unit = min(W, H) / 100
    assert xs and xs[0] > 0 and xs[-1] < W - 1
    assert xs[-1] - xs[0] + 1 < W - 12 * unit


def test_difference_blend_inverts_the_text_and_leaves_the_rest(tmp_path_factory):
    import reels
    import reels_fx
    mov = _mov(tmp_path_factory, [{"text": "STOP", "from": 0, "dur": 25}], 1.0)
    tmp = tmp_path_factory.mktemp("el5chain")
    short = tmp / "short_01.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "gradients=speed=0.01:c0=0x204060:c1=0xc08040:seed=2:s=%dx%d:r=%d:d=3" % (W, H, FPS),
                    "-f", "lavfi",
                    "-i", "sine=f=440:r=48000:d=3", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac",
                    "-shortest", str(short)], check=True)
    out = tmp / "out.mp4"
    info = {"width": W, "height": H, "fps": "25/1", "duration": 3.0}
    reels.run_step("impact_blend", reels_fx.impact_args(short, mov, 1.0, info, out))

    mask, src, res = _frame(mov, 12), _frame(short, 37), _frame(out, 37)

    def white(x, y):
        return all(mask[(y + dy) * W + x + dx] >= 250 for dx, dy in ((0, 0), (-2, 0), (2, 0), (0, -2), (0, 2)))
    zone = [y * W + x for y in range(B0, B1) for x in range(2, W - 2) if white(x, y)]
    assert len(zone) > 500, "masca are prea putin alb"
    inside = [abs(res[i] - (255 - src[i])) for i in zone]
    assert sum(inside) / len(inside) <= 1.0                # D-65 (seed 2): code 0.099, mutant (c) 2.944
    assert sum(v > 3 for v in inside) <= 0.01 * len(inside)  # ±3 on 99%: code 2/3257, mutant (c) 126/3257
    outside = [abs(a - b) for a, b in zip(_outside_band(res), _outside_band(src))]
    assert sum(outside) / len(outside) <= 0.5
    for n in (12, 62):                                   # before the window and after it ends at 2.0 s
        whole = [abs(a - b) for a, b in zip(_frame(out, n), _frame(short, n))]
        assert sum(whole) / len(whole) <= 0.5, "cadrul %d schimbat" % n

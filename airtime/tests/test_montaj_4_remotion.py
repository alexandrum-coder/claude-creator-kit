"""Element 4, Remotion part: CtaKeyword rendered through overlay.mjs, then laid on a reel (PLAN, Note 2.18, D-50, D-55).

Needs AIRTIME_REMOTION_DIR = an isolated remotion copy with node_modules (never an install); skipped otherwise.
The render runs inside the tests (cached per module), so a missing composition is a failure, not a setup error.
The pill is centred at 48% of the height; the band 44-52% is inside it.
"""
from __future__ import annotations

import json
import os
import subprocess

import pytest

RDIR = os.environ.get("AIRTIME_REMOTION_DIR")
pytestmark = pytest.mark.skipif(not RDIR, reason="AIRTIME_REMOTION_DIR nu e setat (copie izolata a remotion/)")

W, H, FPS = 540, 960, 25
FROM_S, REEL = 1.0, 3.0                    # overlay of 2 s = 50 frames, laid on a 3 s reel from frame 25
N = int((REEL - FROM_S) * FPS)
Y0, Y1 = int(H * 0.44), int(H * 0.52)
_CACHE = {}


LONG = "CONSULTATIE GRATUITA ACUM AZI!"     # 30 characters, the maximum (D-56)


def _mov(tmp_path_factory, word="Postura", duration=REEL - FROM_S):
    key = (word, duration)
    if key not in _CACHE:
        tmp = tmp_path_factory.mktemp("el4rem")
        props = {"width": W, "height": H, "fps": FPS, "colors": {"primary": "#14213d", "accent": "#fca311"},
                 "word": word, "duration": duration}
        pf = tmp / "props.json"
        pf.write_text(json.dumps(props))
        out = tmp / "cta.mov"
        r = subprocess.run(["node", "overlay.mjs", "--id", "CtaKeyword", "--props", str(pf), "--out", str(out)],
                           cwd=RDIR, capture_output=True, text=True, timeout=900)
        assert r.returncode == 0, r.stderr[-800:]
        _CACHE[key] = out
    return _CACHE[key]


def test_a_thirty_character_word_fits_in_the_pill(tmp_path_factory):
    assert len(LONG) == 30
    mov = _mov(tmp_path_factory, LONG, 0.4)
    band = _frame(mov, 9, "alphaextract,")
    row = band[((Y1 - Y0) // 2) * W:((Y1 - Y0) // 2 + 1) * W]
    xs = [x for x, a in enumerate(row) if a > 128]
    unit = min(W, H) / 100
    assert xs and xs[-1] - xs[0] + 1 < W - 12 * unit - 2    # narrower than the max width: nothing cut off


def _frame(path, n, filt):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "select=eq(n\\,%d),%sformat=gray" % (n, filt), "-frames:v", "1", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    assert len(r.stdout) == W * H, "cadrul %d lipseste" % n
    return r.stdout[Y0 * W:Y1 * W]


def test_cta_is_prores_with_alpha_and_lasts_to_the_end(tmp_path_factory):
    mov = _mov(tmp_path_factory)
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                                      "-show_entries", "stream=pix_fmt,nb_read_frames", "-of", "json", str(mov)],
                                     capture_output=True, text=True, check=True).stdout)["streams"][0]
    assert info["pix_fmt"].startswith("yuva")
    assert int(info["nb_read_frames"]) == N


def test_cta_ramps_in_and_is_held_on_the_last_frame(tmp_path_factory):
    mov = _mov(tmp_path_factory)
    for n, want in ((0, 0.25), (1, 0.5), (2, 0.75)):       # P4 / J3: three frames inside the ramp
        assert max(_frame(mov, n, "alphaextract,")) / 255 == pytest.approx(want, abs=0.05), "cadrul %d" % n
    assert max(_frame(mov, 3, "alphaextract,")) / 255 > 0.9
    assert max(_frame(mov, N - 1, "alphaextract,")) / 255 > 0.9
    band = _frame(mov, N - 1, "")                        # colour, alpha ignored: pill and letters differ
    assert max(band) - min(band) > 80


def test_cta_on_the_reel_absent_one_frame_before_and_present_on_the_last(tmp_path_factory):
    import reels
    import reels_fx
    mov = _mov(tmp_path_factory)
    tmp = tmp_path_factory.mktemp("el4chain")
    short = tmp / "short_01.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "color=c=0x404040:s=%dx%d:r=%d:d=%s" % (W, H, FPS, REEL), "-f", "lavfi", "-i",
                    "sine=f=440:r=48000:d=%s" % REEL, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac",
                    "-shortest", str(short)], check=True)
    out = tmp / "out.mp4"
    reels.run_step("cta_overlay", reels_fx.overlay_args(short, mov, FROM_S, out))
    first = int(FROM_S * FPS)
    assert max(_frame(out, first - 1, "")) < 80          # grey 0x40 only
    assert max(_frame(out, int(REEL * FPS) - 1, "")) > 150

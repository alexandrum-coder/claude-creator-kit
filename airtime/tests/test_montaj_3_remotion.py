"""Element 3, Remotion part: NumberedList rendered through overlay.mjs (PLAN, Notes 2.16 and 2.16.1, H1-H3).

Needs AIRTIME_REMOTION_DIR = an isolated remotion copy with node_modules (never an install); skipped otherwise.
Row k of the list sits at 30% + k * 9% of the height and is its own pill, so its band has alpha 0 before its cue.
"""
from __future__ import annotations

import json
import os
import subprocess

import pytest

RDIR = os.environ.get("AIRTIME_REMOTION_DIR")
pytestmark = pytest.mark.skipif(not RDIR, reason="AIRTIME_REMOTION_DIR nu e setat (copie izolata a remotion/)")

W, H, FPS = 540, 960, 25
AT = [0.4, 1.0, 1.6]                       # cue frames 10, 25, 40
DUR = 3.0                                  # 75 frames; fade-out on frames 65..74


@pytest.fixture(scope="module")
def mov(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("el3rem")
    props = {"width": W, "height": H, "fps": FPS, "colors": {"primary": "#14213d", "accent": "#fca311"},
             "items": [{"text": "Punctul %d" % (k + 1), "at": a} for k, a in enumerate(AT)], "duration": DUR}
    pf = tmp / "props.json"
    pf.write_text(json.dumps(props))
    out = tmp / "list.mov"
    subprocess.run(["node", "overlay.mjs", "--id", "NumberedList", "--props", str(pf), "--out", str(out)],
                   cwd=RDIR, check=True, capture_output=True, text=True, timeout=900)
    return out


def _band_alpha(path, n, k):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "select=eq(n\\,%d),alphaextract,format=gray" % n, "-frames:v", "1", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    assert len(r.stdout) == W * H, "cadrul %d lipseste" % n
    y0, y1 = int(H * (0.30 + 0.09 * k)), int(H * (0.30 + 0.09 * (k + 1)))
    return max(r.stdout[y0 * W:y1 * W]) / 255


def test_numbered_list_is_prores_with_alpha_and_lasts_the_duration(mov):
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                                      "-show_entries", "stream=pix_fmt,nb_read_frames", "-of", "json", str(mov)],
                                     capture_output=True, text=True, check=True).stdout)["streams"][0]
    assert info["pix_fmt"].startswith("yuva")
    assert int(info["nb_read_frames"]) == int(DUR * FPS)


@pytest.mark.parametrize("k", [0, 1, 2])
def test_item_appears_on_its_cue_frame(mov, k):
    c = int(round(AT[k] * FPS))
    assert _band_alpha(mov, c - 1, k) <= 0.01
    for d, want in ((0, 0.25), (1, 0.5), (2, 0.75)):     # H1, H2: inside the ramp, against computed values
        assert _band_alpha(mov, c + d, k) == pytest.approx(want, abs=0.05), "item %d, cadrul c+%d" % (k, d)
    assert _band_alpha(mov, c + 6, k) > 0.9
    if k:
        assert _band_alpha(mov, c, k - 1) > 0.9                 # the previous item stays


def test_list_fades_out_on_the_last_ten_frames(mov):
    n = int(DUR * FPS)
    for k in (3, 6, 9):
        assert _band_alpha(mov, n - 10 + k, 0) == pytest.approx(1 - k / 10, abs=0.05), "cadrul %d" % (n - 10 + k)

"""Element 2: slow push-in on the YouTube chapters and on the reels clips (PLAN, Revizia 2 (a) row 2, Nota 2.12).

The marker is a white 200x100 box centred on grey 0x404040. Its width is measured with sub-pixel edges
(sum of (v - bg) / (255 - bg) over 20 centre rows), so a zoom of 1.06 reads as 1.06 within a few 1e-3.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import compose

W, H, FPS = 640, 360, 25
BG = 0x40


def _montaj():
    import montaj
    return montaj


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _box_clip(path, dur, w=W, h=H, audio=False):
    args = ["-f", "lavfi", "-i", "color=c=0x404040:s=%dx%d:r=%d:d=%s,drawbox=x=%d:y=%d:w=200:h=100:c=white:t=fill"
            % (w, h, FPS, dur, w // 2 - 100, h // 2 - 50)]
    if audio:
        args += ["-f", "lavfi", "-i", "sine=f=440:r=48000:d=%s" % dur, "-c:a", "aac", "-shortest"]
    _ff(*args, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "10", str(path))


def _gray(path, n, w=W, h=H):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "select=eq(n\\,%d),format=gray" % n,
                        "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True)
    assert len(r.stdout) == w * h, "cadrul %d lipseste" % n
    return r.stdout


def _marker(data, w=W, h=H):
    """Relative width of the box (1.0 = 200 px) and its x centroid in px, over 20 centre rows."""
    ws, cs = [], []
    for y in range(h // 2 - 10, h // 2 + 10):
        m = [max(0.0, (v - BG) / (255 - BG)) for v in data[y * w:(y + 1) * w]]
        s = sum(m)
        ws.append(s)
        cs.append(sum(i * v for i, v in enumerate(m)) / s + 0.5)
    return sum(ws) / len(ws) / 200, sum(cs) / len(cs)


def _transparent(path, dur=0.4):
    _ff("-f", "lavfi", "-i", "color=c=black@0.0:s=%dx%d:r=%d:d=%s,format=argb" % (W, H, FPS, dur),
        "-c:v", "qtrle", str(path))


def _render_dir(tmp_path, chapters=(), **spec):
    rd = tmp_path / "render"
    rd.mkdir(exist_ok=True)
    _ff("-f", "lavfi", "-i", "color=c=black:s=%dx%d:r=%d:d=1" % (W, H, FPS), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", str(rd / "intro.mp4"))
    overlays = []
    for i, t in enumerate(chapters):
        name = "chapter_%02d.mov" % (i + 1)
        _transparent(rd / name)
        overlays.append({"file": name, "t": t})
    (rd / "render.json").write_text(json.dumps(dict({"intro": "intro.mp4", "overlays": overlays}, **spec)))
    return rd / "render.json"


def _frames(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,nb_read_frames,r_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    st = d["streams"][0]
    return int(st["width"]), int(st["height"]), int(st["nb_read_frames"]), st["r_frame_rate"]


# ------------------------------------------------------------------ YouTube (compose.py)

@pytest.fixture(scope="module")
def chaptered(tmp_path_factory):
    """youtube.mp4 of an 8 s box clip with a chapter at t = 4 and pushin {scale_end: 1.06}."""
    tmp = tmp_path_factory.mktemp("el2yt")
    curat = tmp / "curat.mp4"
    _box_clip(curat, 8)
    rj = _render_dir(tmp, chapters=[4.0], pushin={"scale_end": 1.06})
    out = tmp / "youtube.mp4"
    compose.compose(curat, rj, out)
    return {"out": out, "curat": curat, "tmp": tmp}


# clip frame -> (segment start, segment end): segment 1 is [0, 4), segment 2 is [4, 8)
FRAMES = {0: (0, 4), 50: (0, 4), 99: (0, 4), 100: (4, 8), 150: (4, 8), 199: (4, 8)}


def test_width_grows_linearly_on_each_chapter_and_resets(chaptered):
    for n, (s, e) in FRAMES.items():
        t = n / FPS
        want = 1 + 0.06 * (t - s) / (e - s)
        width, _ = _marker(_gray(chaptered["out"], n + FPS))       # intro = 1 s = 25 frames
        assert width == pytest.approx(want, abs=0.01), "cadrul %d din clip" % n


def test_push_in_stays_centred(chaptered):
    assert _marker(_gray(chaptered["out"], 199 + FPS))[0] >= 1.05        # E1: there is a zoom to keep centred
    for n in FRAMES:
        _, cx = _marker(_gray(chaptered["out"], n + FPS))
        # measured: at most 0.54 px off with yuv444p and rounded x, y; 2.1 px with zoompan on yuv420p
        assert cx == pytest.approx(W / 2, abs=1.0), "cadrul %d din clip" % n


def test_no_pushin_gives_the_old_graph():
    src = {"width": W, "height": H, "fps": 25.0, "duration": 8.0, "has_audio": False, "sample_rate": 48000}
    intro = {"has_audio": False}
    ovs = [{"file": "chapter_01.mov", "t": 4.0}]
    old = compose.build_filtergraph(src, intro, ovs, 1.0)
    assert compose.build_filtergraph(src, intro, ovs, 1.0, {"pushin": None}) == old
    assert compose.build_filtergraph(src, intro, ovs, 1.0, {"layers": [], "audio": []}) == old
    assert "zoompan" not in old[0]


def test_pushin_keeps_size_and_frame_count(chaptered, tmp_path):
    rj = _render_dir(tmp_path, chapters=[4.0])
    plain = tmp_path / "plain.mp4"
    compose.compose(chaptered["curat"], rj, plain)
    assert _frames(chaptered["out"]) == _frames(plain)


def test_pushin_validation():
    m = _montaj()
    src = {"width": W, "height": H, "fps": 25.0, "duration": 8.0, "has_audio": False, "sample_rate": 48000}
    intro = {"has_audio": False}
    for bad in ({"scale_end": 1.0}, {"scale_end": 1.5}, {"scale_end": "x"}, {"scale_end": True}, "1.06"):
        with pytest.raises(ValueError):
            compose.build_filtergraph(src, intro, [], 1.0, {"pushin": bad})
        with pytest.raises(ValueError):
            m.pushin_scale(bad)
    assert m.pushin_scale({}) == 1.06
    assert m.pushin_scale({"scale_end": 1.4}) == 1.4
    assert compose.build_filtergraph(src, intro, [], 1.0, {"pushin": {}}) == \
        compose.build_filtergraph(src, intro, [], 1.0, {"pushin": {"scale_end": 1.06}})


def test_pushin_bounds_from_chapters():
    m = _montaj()
    assert m.pushin_bounds([], 8.0) == [(0.0, 8.0)]
    assert m.pushin_bounds([4.0, 0.0, 4.0, 9.0, 2.0], 8.0) == [(0.0, 2.0), (2.0, 4.0), (4.0, 8.0)]


def test_only_chapter_overlays_set_the_bounds():
    src = {"width": W, "height": H, "fps": 25.0, "duration": 8.0, "has_audio": False, "sample_rate": 48000}
    intro = {"has_audio": False}
    ex = {"pushin": {}}
    with_list = compose.build_filtergraph(src, intro, [{"file": "list_01.mov", "t": 4.0}], 1.0, ex)[0]
    alone = compose.build_filtergraph(src, intro, [], 1.0, ex)[0]
    chapter = compose.build_filtergraph(src, intro, [{"file": "chapter_01.mov", "t": 4.0}], 1.0, ex)[0]
    assert with_list.split(";")[0] == alone.split(";")[0]
    assert chapter.split(";")[0] != alone.split(";")[0]


def test_pushin_with_motion_blur_dissolve(tmp_path):
    curat = tmp_path / "curat.mp4"
    _box_clip(curat, 8)
    rj = _render_dir(tmp_path, pushin={"scale_end": 1.06},
                     transitions=[{"t": 2.0, "d": 1.16, "kind": "motion_blur_dissolve"}])
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rj, out)
    # clip time 6 s is on B, past the focus pull; it plays at 6 - 1.16 = 4.84 s after the intro
    n = int(round(FPS * (1 + _montaj().map_time(6.0, [{"t": 2.0, "d": 1.16}]))))
    assert n == 146
    width, cx = _marker(_gray(out, n))
    assert width == pytest.approx(1 + 0.06 * 6 / 8, abs=0.01)
    assert cx == pytest.approx(W / 2, abs=1.0)
    assert compose.probe(out)["duration"] == pytest.approx(1 + 8 - 1.16, abs=0.04)


# ------------------------------------------------------------------ reels (reels_fx.py, reels.py)

def test_reels_pushin_clip(tmp_path):
    import reels
    import reels_fx
    w, h = 360, 640
    src = tmp_path / "raw.mp4"
    _box_clip(src, 4, w, h, audio=True)
    info = reels_fx.probe(src, reels.run_step)
    assert (info["width"], info["height"]) == (w, h)
    out = tmp_path / "clip_01.mp4"
    reels.run_step("pushin", reels_fx.pushin_args(src, out, 1.06, info))
    for n in (0, 50, 99):
        width, cx = _marker(_gray(out, n, w, h), w, h)
        assert width == pytest.approx(1 + 0.06 * n / 100, abs=0.01), "cadrul %d" % n
        assert cx == pytest.approx(w / 2, abs=1.0), "cadrul %d" % n
    a, b = _frames(src), _frames(out)
    assert a[:2] == b[:2] and a[3] == b[3] and abs(a[2] - b[2]) <= 1
    streams = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                              str(out)], capture_output=True, text=True, check=True).stdout.split()
    assert "audio" in streams


def _fake_run(calls, approved_segments):
    def fake(step, args, cwd=None, timeout=None):
        args = [str(a) for a in args]
        calls.append((step, args))
        if step == "snap_boundaries":       # like snap_boundaries.py: the segments keep their extra keys
            Path(args[args.index("--output") + 1]).write_text(json.dumps({"segments": approved_segments}))
        elif step in ("extract_clip", "pushin"):
            Path(args[-1]).write_bytes(b"")
        elif step == "pushin_probe":
            return json.dumps({"streams": [{"width": 1080, "height": 1920, "r_frame_rate": "25/1"}],
                               "format": {"duration": "5.0"}})
        elif step == "render":
            d = Path(args[args.index("--output-dir") + 1])
            for i in range(1, len(approved_segments) + 1):
                (d / ("short_%02d.mp4" % i)).write_bytes(b"")
        elif step == "export":
            d = Path(args[args.index("--output-dir") + 1])
            for i in range(1, len(approved_segments) + 1):
                (d / ("short_%02d_ig.mp4" % i)).write_bytes(b"")
        return ""
    return fake


def _build(tmp_path, monkeypatch, segments):
    import reels
    calls = []
    monkeypatch.setattr(reels, "run_step", _fake_run(calls, segments))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))      # write_vertical_reframe
    tr = tmp_path / "t.json"
    tr.write_text(json.dumps({"segments": [{"start": 0, "end": 1, "text": "salut",
                                            "words": [{"word": "salut", "start": 0.0, "end": 1.0}]}]}))
    ap = tmp_path / "approved.json"
    ap.write_text(json.dumps({"segments": segments}))
    reels.build(tmp_path / "curat.mp4", tr, ap, "bold", tmp_path / "out", "vertical")
    return calls


SEGS = [{"id": i, "start": 5.0 * (i - 1), "end": 5.0 * i} for i in (1, 2, 3)]


def test_reels_without_pushin_keep_the_old_steps(tmp_path, monkeypatch):
    calls = _build(tmp_path, monkeypatch, SEGS)
    assert [c[0] for c in calls] == ["snap_boundaries", "extract_clip", "extract_clip", "extract_clip",
                                     "render", "export"]
    clips = tmp_path / "out" / "work" / "clips"
    for i, (_, args) in enumerate(calls[1:4], 1):
        assert args == ["ffmpeg", "-y", "-ss", "%.3f" % (5.0 * (i - 1)), "-to", "%.3f" % (5.0 * i), "-i",
                        str(tmp_path / "curat.mp4"), "-c", "copy", str(clips / ("clip_%02d.mp4" % i))]


def test_reels_pushin_only_on_the_marked_segment(tmp_path, monkeypatch):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    plain = _build(tmp_path / "a", monkeypatch, SEGS)
    segs = [dict(s) for s in SEGS]
    segs[1]["pushin"] = {"scale_end": 1.06}
    calls = _build(tmp_path / "b", monkeypatch, segs)
    assert [c[0] for c in calls] == ["snap_boundaries", "extract_clip", "extract_clip", "pushin_probe", "pushin",
                                     "extract_clip", "render", "export"]
    work = tmp_path / "b" / "out" / "work"
    raw = work / "clips_src" / "clip_02.mp4"
    assert calls[2][1][-1] == str(raw)
    assert calls[3][1][-1] == str(raw)
    pin = calls[4][1]
    assert pin[0] == "ffmpeg" and str(raw) in pin and pin[-1] == str(work / "clips" / "clip_02.mp4")
    assert "zoompan" in pin[pin.index("-vf") + 1]
    # segments 1 and 3: same command as without push-in, apart from the run folder
    strip = lambda args: [a.replace(str(tmp_path / "a"), "X").replace(str(tmp_path / "b"), "X") for a in args]
    assert strip(calls[1][1]) == strip(plain[1][1])
    assert strip(calls[5][1]) == strip(plain[3][1])


def test_reels_pushin_without_words(tmp_path, monkeypatch):
    """E5: without word timestamps the approved file is copied whole, so pushin still reaches the clip."""
    import reels
    calls = []
    segs = [dict(s) for s in SEGS]
    segs[2]["pushin"] = {}
    monkeypatch.setattr(reels, "run_step", _fake_run(calls, segs))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    tr = tmp_path / "t.json"
    tr.write_text(json.dumps({"segments": [], "captions": []}))
    ap = tmp_path / "approved.json"
    ap.write_text(json.dumps({"segments": segs}))
    reels.build(tmp_path / "curat.mp4", tr, ap, "bold", tmp_path / "out", "vertical")
    assert [c[0] for c in calls] == ["extract_clip", "extract_clip", "extract_clip", "pushin_probe", "pushin",
                                     "render", "export"]
    assert "1+0.060000*" in calls[4][1][calls[4][1].index("-vf") + 1]


def test_reels_bad_pushin_is_a_step_error(tmp_path, monkeypatch):
    import reels
    segs = [dict(s) for s in SEGS]
    segs[0]["pushin"] = {"scale_end": 2}
    with pytest.raises(reels.StepError) as e:
        _build(tmp_path, monkeypatch, segs)
    assert e.value.step == "pushin"

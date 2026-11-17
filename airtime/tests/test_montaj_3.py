"""Element 3: numbered list synced on words, in the reels (PLAN, Revizia 2 (a) row 3, Notes 2.16 and 2.16.1).

The Remotion part (NumberedList through overlay.mjs) is in test_montaj_3_remotion.py.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

FPS = 25


def _fx():
    import reels_fx
    return reels_fx


def _words(*spec):
    """spec: (word, start) pairs; each word lasts 0.3 s."""
    return [{"word": w, "start": s, "end": s + 0.3} for w, s in spec]


ITEMS = [{"text": "Unu", "cue": "primul"}, {"text": "Doi", "cue": "al doilea"}, {"text": "Trei", "cue": "așa"}]


# ------------------------------------------------------------------ 1. cue matching

def test_match_cues_diacritics_punctuation_cedilla_and_sequence():
    words = _words(("Salut,", 10.0), ("PRIMUL!", 10.52), ("al", 11.0), ("treilea", 11.3), ("al", 11.6),
                   ("doilea", 11.92), ("aşa", 12.8))    # "al" alone comes first; cedilla s, as some transcripts write it
    warnings = []
    times = _fx().match_cues(ITEMS, words, 10.0, 15.0, FPS, warnings, 1)
    assert times == [pytest.approx(0.52), pytest.approx(1.6), pytest.approx(2.8)]
    assert warnings == []
    # and the other way round: cue without diacritics, transcript with them
    assert _fx().match_cues([{"text": "x", "cue": "Asa."}], _words(("așa", 10.4)), 10.0, 12.0, FPS, [], 1) == \
        [pytest.approx(0.4)]


def test_match_cues_takes_the_first_word_after_the_previous_item():
    words = _words(("asta", 10.2), ("si", 10.6), ("asta", 11.4))
    items = [{"text": "a", "cue": "asta"}, {"text": "b", "cue": "asta"}]
    assert _fx().match_cues(items, words, 10.0, 13.0, FPS, [], 1) == [pytest.approx(0.2), pytest.approx(1.4)]


def test_match_cues_stays_inside_the_segment():
    words = _words(("primul", 4.0), ("altceva", 10.2), ("primul", 11.2), ("primul", 16.0))
    assert _fx().match_cues([{"text": "a", "cue": "primul"}], words, 10.0, 15.0, FPS, [], 1) == [pytest.approx(1.2)]


def test_missing_cue_falls_back_to_previous_plus_one_second_with_a_warning():
    words = _words(("primul", 10.48), ("nimic", 11.0))
    warnings = []
    items = [{"text": "a", "cue": "primul"}, {"text": "b", "cue": "lipsa"}, {"text": "c", "cue": "nimic"}]
    times = _fx().match_cues(items, words, 10.0, 14.0, FPS, warnings, 2)
    assert times == [pytest.approx(0.48), pytest.approx(1.48), pytest.approx(1.0)]
    assert len(warnings) == 1 and "lipsa" in warnings[0] and "2" in warnings[0]


def test_segment_without_words_skips_the_list():
    warnings = []
    assert _fx().match_cues(ITEMS, _words(("altundeva", 3.0)), 10.0, 14.0, FPS, warnings, 3) is None
    assert len(warnings) == 1 and "3" in warnings[0]


def test_times_are_rounded_to_frames():
    t = _fx().match_cues([{"text": "a", "cue": "x"}], _words(("x", 10.517)), 10.0, 12.0, FPS, [], 1)[0]
    assert t * FPS == pytest.approx(round(t * FPS)) and t == pytest.approx(0.52)


def test_check_list_rejects_bad_lists():
    fx = _fx()
    assert fx.check_list(ITEMS) == ITEMS
    for bad in ([], [{"text": "a"}], [{"text": "", "cue": "x"}], "lista", [{"text": "a", "cue": "b"}] * 5):
        with pytest.raises(ValueError):
            fx.check_list(bad)


# ------------------------------------------------------------------ 2. props

def test_list_props_start_at_the_first_item_and_last_to_the_end():
    props, t0 = _fx().list_props(ITEMS, [0.52, 1.6, 2.8], 1080, 1920, FPS, 9.0)
    assert t0 == pytest.approx(0.52)
    assert [round(i["at"], 3) for i in props["items"]] == [0.0, 1.08, 2.28]
    assert [i["text"] for i in props["items"]] == ["Unu", "Doi", "Trei"]
    assert props["duration"] == pytest.approx(9.0 - 0.52)
    assert (props["width"], props["height"], props["fps"]) == (1080, 1920, FPS)


# ------------------------------------------------------------------ 3. overlay timing with ffmpeg

def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _px(path, n, x, y, w):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "select=eq(n\\,%d),format=gray" % n,
                        "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return r.stdout[y * w + x]


def test_overlay_starts_at_t0_and_keeps_the_reel(tmp_path):
    import reels
    w, h = 360, 640
    short = tmp_path / "short_01.mp4"
    _ff("-f", "lavfi", "-i", "color=c=0x404040:s=%dx%d:r=%d:d=4" % (w, h, FPS),
        "-f", "lavfi", "-i", "sine=f=440:r=48000:d=4", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac",
        "-shortest", str(short))
    mov = tmp_path / "list.mov"                 # opaque white box from the very first frame (H5)
    _ff("-f", "lavfi", "-i", "nullsrc=s=%dx%d:r=%d:d=2,format=rgba,geq=r=255:g=255:b=255:"
        "a='if(between(X\\,100\\,179)*between(Y\\,200\\,279)\\,255\\,0)',format=argb" % (w, h, FPS),
        "-c:v", "qtrle", str(mov))
    out = tmp_path / "out.mp4"
    reels.run_step("list_overlay", _fx().overlay_args(short, mov, 1.2, out))
    assert _px(out, 29, 140, 240, w) < 100      # t0 = 1.2 s = frame 30
    assert _px(out, 31, 140, 240, w) > 200
    assert _px(out, 31, 20, 20, w) < 100        # outside the box nothing changes
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height",
                                      "-show_entries", "format=duration", "-of", "json", str(out)],
                                     capture_output=True, text=True, check=True).stdout)
    kinds = [s["codec_type"] for s in info["streams"]]
    assert "audio" in kinds
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    assert (v["width"], v["height"]) == (w, h)
    assert float(info["format"]["duration"]) == pytest.approx(4.0, abs=0.05)


# ------------------------------------------------------------------ 4. reels.build with a simulated run_step

SEGS = [{"id": i, "start": 10.0 * i, "end": 10.0 * i + 5.0} for i in (1, 2, 3)]
WORDS = [{"start": 0, "end": 40, "text": "x",
          "words": _words(("unu", 10.4), ("primul", 20.52), ("al", 21.6), ("doilea", 21.92), ("aşa", 22.8),
                          ("trei", 30.4))}]


def _fake_run(calls, segments, home_remotion):
    def fake(step, args, cwd=None, timeout=None):
        args = [str(a) for a in args]
        calls.append((step, args, str(cwd) if cwd else None))
        if step == "snap_boundaries":
            Path(args[args.index("--output") + 1]).write_text(json.dumps({"segments": segments}))
        elif step in ("extract_clip", "list_overlay"):
            Path(args[-1]).write_bytes(b"over" if step == "list_overlay" else b"")
        elif step == "list_probe":
            return json.dumps({"streams": [{"width": 1080, "height": 1920, "r_frame_rate": "25/1"}],
                               "format": {"duration": "5.0"}})
        elif step == "list_render":
            Path(args[args.index("--out") + 1]).write_bytes(b"mov")
        elif step == "render":
            d = Path(args[args.index("--output-dir") + 1])
            for s in segments:
                (d / ("short_%02d.mp4" % s["id"])).write_bytes(b"short")
        elif step == "export":
            d = Path(args[args.index("--output-dir") + 1])
            for s in segments:
                (d / ("short_%02d_ig.mp4" % s["id"])).write_bytes(b"")
        return ""
    return fake


def _build(tmp_path, monkeypatch, segments, words=WORDS):
    import reels
    calls, warnings = [], []
    home = tmp_path / "home"
    monkeypatch.setenv("AIRTIME_HOME", str(home))
    monkeypatch.setattr(reels, "run_step", _fake_run(calls, segments, home / "remotion"))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    tr = tmp_path / "t.json"
    tr.write_text(json.dumps({"segments": words}))
    ap = tmp_path / "approved.json"
    ap.write_text(json.dumps({"segments": segments}))
    reels.build(tmp_path / "curat.mp4", tr, ap, "bold", tmp_path / "out", "vertical", warnings=warnings)
    return calls, warnings, home


def test_reels_list_only_on_the_marked_segment(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[1]["list"] = ITEMS
    calls, warnings, home = _build(tmp_path, monkeypatch, segs)
    names = [c[0] for c in calls]
    assert names == ["snap_boundaries", "extract_clip", "extract_clip", "extract_clip", "render",
                     "list_probe", "list_render", "list_overlay", "export"]
    render_dir = tmp_path / "out" / "work" / "render"
    assert calls[5][1][-1] == str(render_dir / "short_02.mp4")
    assert calls[6][2] == str(home / "remotion") and calls[6][1][:2] == ["node", "overlay.mjs"]
    assert str(render_dir / "short_02.mp4") in calls[7][1]
    # the overlaid reel replaced short_02.mp4; no second short_*.mp4 is left for export
    assert (render_dir / "short_02.mp4").read_bytes() == b"over"
    assert sorted(p.name for p in render_dir.glob("short_*.mp4")) == ["short_01.mp4", "short_02.mp4",
                                                                       "short_03.mp4"]
    props = json.loads(Path(calls[6][1][calls[6][1].index("--props") + 1]).read_text())
    assert [round(i["at"], 2) for i in props["items"]] == [0.0, 1.08, 2.28] and warnings == []


def test_reels_without_list_keep_the_old_steps(tmp_path, monkeypatch):
    calls, warnings, _ = _build(tmp_path, monkeypatch, SEGS)
    assert [c[0] for c in calls] == ["snap_boundaries", "extract_clip", "extract_clip", "extract_clip",
                                     "render", "export"]


def test_reels_list_warnings_and_bad_list(tmp_path, monkeypatch):
    import reels
    segs = [dict(s) for s in SEGS]
    segs[1]["list"] = [{"text": "a", "cue": "primul"}, {"text": "b", "cue": "nimeni"}]
    (tmp_path / "a").mkdir()
    _, warnings, _ = _build(tmp_path / "a", monkeypatch, segs)
    assert len(warnings) == 1 and "nimeni" in warnings[0]
    segs[1]["list"] = [{"text": "a"}]
    (tmp_path / "b").mkdir()
    with pytest.raises(reels.StepError) as e:
        _build(tmp_path / "b", monkeypatch, segs)
    assert e.value.step == "list"

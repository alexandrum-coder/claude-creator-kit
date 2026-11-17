"""Element 5: impact caption laid with a difference blend, in the reels (PLAN, Revizia 2 (a) row 5, Note 2.20,
D-58...D-64).

The Remotion part (ImpactCaption through overlay.mjs, and the full blend chain) is in test_montaj_5_remotion.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FPS = 25


def _fx():
    import reels_fx
    return reels_fx


def _words(*spec):
    return [{"word": w, "start": s, "end": s + 0.3} for w, s in spec]


# ------------------------------------------------------------------ 1. the impact field

def test_check_impact_rounds_to_frames():
    fx = _fx()
    assert fx.check_impact([{"text": " Stop ", "t": 1.01, "d": 0.61}], 5.0, FPS) == [
        {"text": "Stop", "t": pytest.approx(1.0), "d": pytest.approx(0.6)}]
    ok = fx.check_impact([{"text": "a" * 30, "t": 0, "d": 1.0}, {"text": "b", "t": 1.0, "d": 1.0},
                          {"text": "c", "t": 4.4, "d": 0.6}], 5.0, FPS)    # adjacent items and the last frame
    assert [i["t"] for i in ok] == pytest.approx([0.0, 1.0, 4.4])
    assert len(fx.check_impact([{"text": "x", "t": 0.5 * k, "d": 0.4} for k in range(8)], 5.0, FPS)) == 8


def test_check_impact_rejects_bad_values():
    fx = _fx()
    good = {"text": "Stop", "t": 1.0, "d": 0.6}
    bad = ["x", {"text": "Stop"}, [], [1], [dict(good, text="")], [dict(good, text="   ")],
           [dict(good, text="a" * 31)], [dict(good, text=5)], [{"t": 1.0, "d": 0.6}],
           [dict(good, t="1")], [dict(good, t=True)], [dict(good, d=None)], [dict(good, t=-0.1)],
           [dict(good, d=0.01)], [dict(good, t=4.5)],
           [good, dict(good, t=1.5)],                    # overlaps the first item
           [dict(good, t=2.0), good],                    # out of order
           [dict(good, t=0.5 * k, d=0.4) for k in range(9)]]
    for b in bad:
        with pytest.raises(ValueError):
            fx.check_impact(b, 5.0, FPS)


def test_impact_props_cover_only_the_impact_window():
    items = [{"text": "Stop", "t": 1.0, "d": 0.6}, {"text": "Gata", "t": 2.0, "d": 0.4}]
    props, t0 = _fx().impact_props(items, 1080, 1920, FPS)
    assert t0 == pytest.approx(1.0)
    assert props["items"] == [{"text": "Stop", "from": 0, "dur": 15}, {"text": "Gata", "from": 25, "dur": 10}]
    assert props["duration"] == pytest.approx(1.4)
    assert (props["width"], props["height"], props["fps"]) == (1080, 1920, FPS)


def test_impact_args_blend_in_rgb_with_accurate_rounding():
    info = {"width": 1080, "height": 1920, "fps": "25/1", "duration": 5.0}
    args = [str(a) for a in _fx().impact_args("short.mp4", "m.mov", 1.0, info, "out.mp4")]
    fc = args[args.index("-filter_complex") + 1]
    order = ["sws_flags=accurate_rnd", "color=c=black:s=1080x1920:r=25/1", "format=gbrp",
             "PTS-STARTPTS+1.000000/TB", "blend=all_mode=difference"]
    pos = [fc.find(tok) for tok in order]
    assert all(p >= 0 for p in pos) and pos == sorted(pos), fc
    assert args[:5] == ["ffmpeg", "-y", "-i", "short.mp4", "-i"] and args[-1] == "out.mp4"
    assert "0:a?" in args and args[args.index("-c:a") + 1] == "copy"


def test_impact_lands_on_its_exact_frame_at_ntsc_rate(tmp_path):
    """P1: 30000/1001 fps, t0 = frame 31 = 1.0343666 s; a white ffmpeg mask (no Remotion) inverts from frame 31."""
    import subprocess
    import reels
    w, h, rate = 64, 64, "30000/1001"
    t0 = 31 * 1001 / 30000
    short, mask, out = tmp_path / "s.mp4", tmp_path / "m.mov", tmp_path / "o.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "color=c=0x404040:s=%dx%d:r=%s:d=2" % (w, h, rate), "-pix_fmt", "yuv420p", "-c:v", "libx264",
                    str(short)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "color=c=white:s=%dx%d:r=%s:d=0.5" % (w, h, rate), "-vf", "format=yuva444p10le",
                    "-c:v", "prores_ks", "-profile:v", "4444", str(mask)], check=True)
    info = {"width": w, "height": h, "fps": rate, "duration": 2.0}
    args = [str(a) for a in _fx().impact_args(short, mask, t0, info, out)]
    fc = args[args.index("-filter_complex") + 1]
    assert "r=30000/1001" in fc and "PTS-STARTPTS+1.034366/TB" in fc
    reels.run_step("impact_blend", args)

    def mean_y(n):
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-vf", "select=eq(n\\,%d),format=gray" % n,
                            "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True)
        return sum(r.stdout) / len(r.stdout)
    assert mean_y(30) < 100 < mean_y(31)          # grey 0x40 is 64; inverted it is 191


# ------------------------------------------------------------------ 2. reels.build with a simulated run_step

SEGS = [{"id": i, "start": 10.0 * i, "end": 10.0 * i + 5.0} for i in (1, 2, 3)]
WORDS = [{"start": 0, "end": 40, "text": "x",
          "words": _words(("unu", 10.4), ("primul", 20.52), ("al", 21.6), ("doilea", 21.92), ("asa", 22.8),
                          ("trei", 30.4))}]
ITEMS = [{"text": "Unu", "cue": "primul"}, {"text": "Doi", "cue": "al doilea"}]
IMPACT = [{"text": "Stop", "t": 1.0, "d": 0.6}]


def _fake_run(calls, segments):
    def fake(step, args, cwd=None, timeout=None):
        args = [str(a) for a in args]
        calls.append((step, args, str(cwd) if cwd else None))
        if step == "snap_boundaries":
            Path(args[args.index("--output") + 1]).write_text(json.dumps({"segments": segments}))
        elif step in ("extract_clip", "list_overlay", "cta_overlay", "impact_blend"):
            Path(args[-1]).write_bytes(step.encode())
        elif step in ("list_probe", "cta_probe", "impact_probe"):
            return json.dumps({"streams": [{"width": 1080, "height": 1920, "r_frame_rate": "25/1"}],
                               "format": {"duration": "5.0"}})
        elif step in ("list_render", "cta_render", "impact_render"):
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


def _build(tmp_path, monkeypatch, segments, cta_word=None):
    import reels
    calls, warnings = [], []
    home = tmp_path / "home"
    monkeypatch.setenv("AIRTIME_HOME", str(home))
    monkeypatch.setattr(reels, "run_step", _fake_run(calls, segments))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    tr = tmp_path / "t.json"
    tr.write_text(json.dumps({"segments": WORDS}))
    ap = tmp_path / "approved.json"
    ap.write_text(json.dumps({"segments": segments}))
    reels.build(tmp_path / "curat.mp4", tr, ap, "bold", tmp_path / "out", "vertical", warnings=warnings,
                cta_word=cta_word)
    return calls, warnings, home


def _props(call):
    return json.loads(Path(call[1][call[1].index("--props") + 1]).read_text())


def test_reels_impact_only_on_the_marked_segment(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[2]["impact"] = IMPACT
    calls, warnings, home = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls] == ["snap_boundaries", "extract_clip", "extract_clip", "extract_clip", "render",
                                     "impact_probe", "impact_render", "impact_blend", "export"]
    render_dir = tmp_path / "out" / "work" / "render"
    assert calls[5][1][-1] == str(render_dir / "short_03.mp4")
    assert calls[6][2] == str(home / "remotion") and calls[6][1][:4] == ["node", "overlay.mjs", "--id",
                                                                          "ImpactCaption"]
    props = _props(calls[6])
    assert props["items"] == [{"text": "Stop", "from": 0, "dur": 15}] and props["duration"] == pytest.approx(0.6)
    fc = calls[7][1][calls[7][1].index("-filter_complex") + 1]
    assert "PTS-STARTPTS+1.000000/TB" in fc and "blend=all_mode=difference" in fc
    assert str(render_dir / "short_03.mp4") in calls[7][1]
    assert (render_dir / "short_03.mp4").read_bytes() == b"impact_blend"
    assert (render_dir / "short_01.mp4").read_bytes() == b"short"
    assert warnings == []


def test_impact_comes_after_the_list_and_the_cta(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[1].update(list=ITEMS, cta={"word": "Postura", "from_s": 3.0}, impact=IMPACT)   # both items before the CTA
    calls, warnings, _ = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls][5:] == ["list_probe", "list_render", "list_overlay", "cta_probe", "cta_render",
                                         "cta_overlay", "impact_probe", "impact_render", "impact_blend", "export"]
    assert warnings == []


def test_segment_without_speech_keeps_the_impact(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[2] = {"id": 3, "start": 35.0, "end": 40.0, "impact": IMPACT}
    calls, warnings, _ = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls][5:] == ["impact_probe", "impact_render", "impact_blend", "export"]
    assert warnings == []


def test_a_bad_impact_stops_the_build(tmp_path, monkeypatch):
    import reels
    for n, bad in enumerate(([{"text": "x", "t": 4.8, "d": 1.0}], "da", [])):
        segs = [dict(s) for s in SEGS]
        segs[0]["impact"] = bad
        (tmp_path / str(n)).mkdir()
        with pytest.raises(reels.StepError) as e:
            _build(tmp_path / str(n), monkeypatch, segs)
        assert e.value.step == "impact"


# ------------------------------------------------------------------ 3. impact after snap_boundaries (D-86)

def _build_snapped(tmp_path, monkeypatch, approved, snapped):
    """Like _build, but snap_boundaries returns `snapped` instead of the approved segments."""
    import reels
    calls, warnings = [], []
    monkeypatch.setenv("AIRTIME_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(reels, "run_step", _fake_run(calls, snapped))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    tr = tmp_path / "t.json"
    tr.write_text(json.dumps({"segments": WORDS}))
    ap = tmp_path / "approved.json"
    ap.write_text(json.dumps({"segments": approved}))
    reels.build(tmp_path / "curat.mp4", tr, ap, "bold", tmp_path / "out", "vertical", warnings=warnings)
    return calls, warnings


def _blend_offset(calls):
    fc = next(c for c in calls if c[0] == "impact_blend")[1]
    fc = fc[fc.index("-filter_complex") + 1]
    return fc[fc.index("PTS-STARTPTS+"):].split("/")[0]


def test_impact_follows_a_start_moved_earlier_by_the_snap(tmp_path, monkeypatch):
    approved = [{"id": 1, "start": 10.0, "end": 15.0, "impact": IMPACT}]       # word at 11.0, t = 1.0
    snapped = [{"id": 1, "start": 9.0, "end": 15.0, "impact": IMPACT}]         # the reel now starts 1 s earlier
    calls, warnings = _build_snapped(tmp_path, monkeypatch, approved, snapped)
    assert _blend_offset(calls) == "PTS-STARTPTS+2.000000"                    # still on the word at 11.0
    assert warnings == []


def test_impact_follows_a_start_moved_later_by_the_snap(tmp_path, monkeypatch):
    approved = [{"id": 1, "start": 10.0, "end": 15.0, "impact": IMPACT}]
    snapped = [{"id": 1, "start": 10.4, "end": 15.0, "impact": IMPACT}]       # 0.6 s = frame 15 at 25 fps
    calls, warnings = _build_snapped(tmp_path, monkeypatch, approved, snapped)
    assert _blend_offset(calls) == "PTS-STARTPTS+0.600000"
    assert warnings == []


def test_impact_cut_off_by_the_snap_is_dropped_with_a_warning(tmp_path, monkeypatch):
    early = [{"text": "Stop", "t": 0.2, "d": 0.6}]                             # word at 10.2, before the new start
    approved = [{"id": 1, "start": 10.0, "end": 15.0, "impact": early}]
    snapped = [{"id": 1, "start": 10.5, "end": 15.0, "impact": early}]
    calls, warnings = _build_snapped(tmp_path, monkeypatch, approved, snapped)
    assert "impact_blend" not in [c[0] for c in calls]                        # no item left, no blend, no error
    assert len(warnings) == 1 and "Stop" in warnings[0]


def test_shift_impact_leaves_bad_values_to_check_impact():
    fx = _fx()
    for bad in ("da", [], [{"text": "x", "t": "1", "d": 0.6}]):
        assert fx.shift_impact(bad, 0.5, 5.0, [], 1) == bad
    items = [{"text": "x", "t": 4.8, "d": 1.0}]                               # too long, but not moved: unchanged
    assert fx.shift_impact(items, 0.0, 5.0, [], 1) == items

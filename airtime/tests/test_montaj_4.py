"""Element 4: CTA keyword held to the end, in the reels (PLAN, Revizia 2 (a) row 4, Note 2.18, D-50...D-55).

The Remotion part (CtaKeyword through overlay.mjs, and the full overlay chain) is in test_montaj_4_remotion.py.
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


# ------------------------------------------------------------------ 1. window and word

def test_cta_window_default_is_the_last_three_seconds_on_a_frame():
    fx = _fx()
    assert fx.cta_window({}, 5.0, FPS) == pytest.approx(2.0)
    t = fx.cta_window({}, 4.99, FPS)                      # 1.99 s is not on a frame: 50 / 25
    assert t * FPS == pytest.approx(round(t * FPS)) and t == pytest.approx(2.0)
    assert fx.cta_window({}, 2.0, FPS) == 0.0             # a reel shorter than 3 s: the whole reel
    assert fx.cta_window({"from_s": 1.01}, 5.0, FPS) == pytest.approx(1.0)
    assert fx.cta_window({"from_s": 0}, 5.0, FPS) == 0.0


def test_cta_window_rejects_bad_values():
    fx = _fx()
    for bad in ("x", ["from_s"], {"from_s": "1"}, {"from_s": True}, {"from_s": -0.5}, {"from_s": 5.0},
                {"from_s": 4.99}):
        with pytest.raises(ValueError):
            fx.cta_window(bad, 5.0, FPS)
    assert fx.cta_window({"from_s": 4.96}, 5.0, FPS) == pytest.approx(4.96)   # the last frame is allowed


def test_cta_word_checks_and_priority():
    fx = _fx()
    assert fx.check_cta_word(" Salvează ") == "Salvează"
    assert fx.check_cta_word("a" * 30) == "a" * 30
    for bad in ("", "   ", "a" * 31, 5, None):
        with pytest.raises(ValueError):
            fx.check_cta_word(bad)
    warnings = []
    assert fx.resolve_cta_word({"word": "Postura"}, "spate", warnings, 1) == "Postura"
    assert fx.resolve_cta_word({}, "spate", warnings, 1) == "spate"
    assert warnings == []
    assert fx.resolve_cta_word({}, None, warnings, 3) is None
    assert fx.resolve_cta_word({}, "  ", warnings, 3) is None             # an empty --cta-word is absent (J2)
    assert len(warnings) == 2 and all("3" in w for w in warnings)
    for bad in ("da", {"word": ""}, {"word": "  "}):                      # an empty word in the segment is not
        with pytest.raises(ValueError):
            fx.resolve_cta_word(bad, "spate", [], 1)


# ------------------------------------------------------------------ 2. the list gives way to the CTA

def test_cut_list_drops_items_after_the_cta_with_a_warning():
    fx = _fx()
    items = [{"text": "Unu", "cue": "a"}, {"text": "Doi", "cue": "b"}, {"text": "Trei", "cue": "c"}]
    warnings = []
    kept, times = fx.cut_list(items, [0.52, 1.56, 2.8], 2.0, FPS, warnings, 2)
    assert [i["text"] for i in kept] == ["Unu", "Doi"] and times == [0.52, 1.56]
    assert len(warnings) == 1 and "Trei" in warnings[0] and "2" in warnings[0]
    kept, times = fx.cut_list(items, [2.0, 2.4, 2.8], 2.0, FPS, [], 2)
    assert kept == [] and times == []


def test_cut_list_keeps_the_ten_frame_fade_out_whole():
    items = [{"text": "Unu", "cue": "a"}, {"text": "Doi", "cue": "b"}]
    warnings = []                                          # cutoff 2.0 - 10/25 = 1.6: "Doi" at 1.8 would show
    kept, times = _fx().cut_list(items, [0.52, 1.8], 2.0, FPS, warnings, 4)   # only inside the fade-out
    assert [i["text"] for i in kept] == ["Unu"] and len(warnings) == 1 and "Doi" in warnings[0]


def test_cta_props_last_from_the_cta_to_the_end():
    props = _fx().cta_props("Postura", 1080, 1920, FPS, 5.0, 2.0)
    assert props["word"] == "Postura"
    assert props["duration"] == pytest.approx(3.0)
    assert (props["width"], props["height"], props["fps"]) == (1080, 1920, FPS)
    assert set(props["colors"]) == {"primary", "accent"}


# ------------------------------------------------------------------ 3. reels.build with a simulated run_step

SEGS = [{"id": i, "start": 10.0 * i, "end": 10.0 * i + 5.0} for i in (1, 2, 3)]
WORDS = [{"start": 0, "end": 40, "text": "x",
          "words": _words(("unu", 10.4), ("primul", 20.52), ("al", 21.6), ("doilea", 21.92), ("asa", 22.8),
                          ("trei", 30.4))}]
ITEMS = [{"text": "Unu", "cue": "primul"}, {"text": "Doi", "cue": "al doilea"}, {"text": "Trei", "cue": "așa"}]


def _fake_run(calls, segments):
    def fake(step, args, cwd=None, timeout=None):
        args = [str(a) for a in args]
        calls.append((step, args, str(cwd) if cwd else None))
        if step == "snap_boundaries":
            Path(args[args.index("--output") + 1]).write_text(json.dumps({"segments": segments}))
        elif step in ("extract_clip", "list_overlay", "cta_overlay"):
            Path(args[-1]).write_bytes(step.encode())
        elif step in ("list_probe", "cta_probe"):
            return json.dumps({"streams": [{"width": 1080, "height": 1920, "r_frame_rate": "25/1"}],
                               "format": {"duration": "5.0"}})
        elif step in ("list_render", "cta_render"):
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


def test_reels_cta_only_on_the_marked_segment(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[2]["cta"] = {"word": "Postura"}
    calls, warnings, home = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls] == ["snap_boundaries", "extract_clip", "extract_clip", "extract_clip", "render",
                                     "cta_probe", "cta_render", "cta_overlay", "export"]
    render_dir = tmp_path / "out" / "work" / "render"
    assert calls[5][1][-1] == str(render_dir / "short_03.mp4")
    assert calls[6][2] == str(home / "remotion") and calls[6][1][:4] == ["node", "overlay.mjs", "--id",
                                                                          "CtaKeyword"]
    props = _props(calls[6])
    assert props["word"] == "Postura" and props["duration"] == pytest.approx(3.0)
    fc = calls[7][1][calls[7][1].index("-filter_complex") + 1]
    assert "PTS-STARTPTS+2.000/TB" in fc and str(render_dir / "short_03.mp4") in calls[7][1]
    assert (render_dir / "short_03.mp4").read_bytes() == b"cta_overlay"
    assert sorted(p.name for p in render_dir.glob("short_*.mp4")) == ["short_01.mp4", "short_02.mp4",
                                                                       "short_03.mp4"]
    assert warnings == []


def test_list_gives_way_to_the_cta_on_the_same_segment(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[1]["list"] = ITEMS
    segs[1]["cta"] = {"from_s": 2.4}
    calls, warnings, _ = _build(tmp_path, monkeypatch, segs, cta_word="spate")
    names = [c[0] for c in calls]
    assert names[5:] == ["list_probe", "list_render", "list_overlay", "cta_probe", "cta_render", "cta_overlay",
                         "export"]
    lp = _props(calls[6])
    assert [i["text"] for i in lp["items"]] == ["Unu", "Doi"]          # "Trei" (2.8 s) comes after the CTA
    assert lp["duration"] == pytest.approx(2.4 - 0.52)                  # the list fades out by from_s
    cp = _props(calls[9])
    assert cp["word"] == "spate" and cp["duration"] == pytest.approx(2.6)
    assert len(warnings) == 1 and "Trei" in warnings[0]


def test_segment_without_speech_skips_the_list_but_keeps_the_cta(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[2] = {"id": 3, "start": 35.0, "end": 40.0, "list": ITEMS, "cta": {"word": "Postura"}}
    calls, warnings, _ = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls][5:] == ["list_probe", "cta_probe", "cta_render", "cta_overlay", "export"]
    assert len(warnings) == 1 and "3" in warnings[0]


def test_cta_without_a_word_is_skipped_and_a_bad_cta_stops(tmp_path, monkeypatch):
    import reels
    segs = [dict(s) for s in SEGS]
    segs[0]["cta"] = {}
    (tmp_path / "a").mkdir()
    calls, warnings, _ = _build(tmp_path / "a", monkeypatch, segs)
    assert not any(c[0].startswith("cta_") for c in calls)
    assert len(warnings) == 1 and "1" in warnings[0]
    for n, bad in enumerate(({"from_s": 9.0}, {"word": ""}, "da")):
        segs[0]["cta"] = bad
        (tmp_path / str(n)).mkdir()
        with pytest.raises(reels.StepError) as e:
            _build(tmp_path / str(n), monkeypatch, segs, cta_word="spate")
        assert e.value.step == "cta"


def test_cli_passes_the_cta_word(tmp_path, monkeypatch):
    import reels
    seen = {}

    def fake_build(*args, **kw):
        seen.update(kw)
        return []
    monkeypatch.setattr(reels, "build", fake_build)
    base = ["build", "--curat", "c.mp4", "--transcript", "t.json", "--approved", "a.json", "--out", str(tmp_path)]
    assert reels.main(base + ["--cta-word", "postura"]) == 0
    assert seen["cta_word"] == "postura"
    seen.clear()
    assert reels.main(base) == 0
    assert seen.get("cta_word") is None

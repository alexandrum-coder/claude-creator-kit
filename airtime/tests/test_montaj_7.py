"""Element 7: result hook in a loop, in the reels (PLAN, Revizia 2 (a) row 7, Note 2.22, D-66...D-71).

The last d seconds of a reel are put in front of it too, video and audio, with a hard cut; the audio has 10 ms
fades at the junction so it does not click. No Remotion: plain ffmpeg.
Thresholds from <SCRATCH>/upgrade/el7-masuratori-2.txt (code and mutants a, b, g).
"""
from __future__ import annotations

import array
import json
import math
import subprocess
from pathlib import Path

import pytest

FPS = 25
SR = 48000


def _fx():
    import reels_fx
    return reels_fx


# ------------------------------------------------------------------ 1. the result_hook field

def test_check_hook_rounds_to_frames_and_keeps_inside_the_reel():
    fx = _fx()
    assert fx.check_hook({"d": 1.52}, 60, FPS) == 38
    assert fx.check_hook({"d": 1.51}, 60, FPS) == 38          # 37.75 frames rounds to 38, not down to 37
    assert fx.check_hook({"d": 0.04}, 60, FPS) == 1           # one frame, the lower limit
    assert fx.check_hook({"d": 2.36}, 60, FPS) == 59          # n - 1 frames, the upper limit
    assert fx.check_hook({"d": 2}, 60, FPS) == 50


def test_check_hook_rejects_bad_values():
    fx = _fx()
    for bad in (1.5, "1.5", None, [], {}, {"d": "1.5"}, {"d": True}, {"d": None}, {"d": 0}, {"d": -1.0},
                {"d": 0.01}, {"d": 2.4}, {"d": 3.0}):
        with pytest.raises(ValueError):
            fx.check_hook(bad, 60, FPS)


def test_hook_args_cut_the_video_on_frames_and_fade_the_audio_junction():
    info = {"width": 64, "height": 64, "fps": "25/1", "frames": 60}
    args = [str(a) for a in _fx().hook_args("short.mp4", "out.mp4", info, 38)]
    fc = args[args.index("-filter_complex") + 1]
    order = ["trim=start_frame=22", "atrim=start=0.880000:end=2.400000", "afade=t=out:st=1.510000:d=0.01",
             "atrim=end=2.400000", "afade=t=in:d=0.01[ma]", "concat=n=2:v=1:a=1"]
    pos = [fc.find(tok) for tok in order]
    assert all(p >= 0 for p in pos) and pos == sorted(pos), fc
    assert args[:4] == ["ffmpeg", "-y", "-i", "short.mp4"] and args[-1] == "out.mp4"
    assert ["-map", "[v]"] == args[args.index("[v]") - 1:args.index("[v]") + 1]
    assert args[args.index("-c:a") + 1] == "aac"


def test_hook_args_at_ntsc_rate_keep_whole_frames():
    """30000/1001 fps, 90 frames, k = 31: the cut is on frame 59, the audio times have 6 decimals."""
    info = {"width": 64, "height": 64, "fps": "30000/1001", "frames": 90}
    args = [str(a) for a in _fx().hook_args("s.mp4", "o.mp4", info, 31)]
    fc = args[args.index("-filter_complex") + 1]
    for tok in ("trim=start_frame=59,", "atrim=start=1.968633:end=3.003000", "afade=t=out:st=1.024367:d=0.01",
                "atrim=end=3.003000"):
        assert tok in fc, (tok, fc)


# ------------------------------------------------------------------ 2. the real chain on a measured source

def _gray(path, n):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "select=eq(n\\,%d),format=gray" % n,
                        "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return sum(r.stdout) / len(r.stdout)


def _pcm(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a", "-ac", "1", "-ar", str(SR),
                        "-f", "s16le", "-"], capture_output=True, check=True)
    a = array.array("h")
    a.frombytes(r.stdout)
    return a


def _rms(a, t0, t1):
    seg = a[int(t0 * SR):int(t1 * SR)]
    return math.sqrt(sum(v * v for v in seg) / len(seg))


def test_hook_puts_the_last_frames_first_with_their_sound(tmp_path):
    import reels
    fx = _fx()
    src, out = tmp_path / "short_01.mp4", tmp_path / "out.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "color=c=black:s=64x64:r=25:d=2.4,format=yuv420p,geq=lum='20+3*N':cb=128:cr=128",
                    "-f", "lavfi", "-i", "aevalsrc='sin(2*PI*440*t)*(0.2+0.8*t/2.4)':s=%d:d=2.4" % SR,
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    str(src)], check=True)
    info = fx.hook_probe(src, reels.run_step)
    assert info["frames"] == 60
    k = fx.check_hook({"d": 1.52}, info["frames"], 25.0)
    reels.run_step("hook_concat", fx.hook_args(src, out, info, k))

    frames = fx.hook_probe(out, reels.run_step)["frames"]
    assert abs(frames - (60 + 38)) <= 1                              # row 7: d + the old duration, ±1 frame
    assert abs(_gray(out, 0) - _gray(src, 22)) <= 1.5                # D-71: code 0, mutant (a) 3
    assert abs(_gray(out, 38) - _gray(src, 0)) <= 1.5                # the whole reel follows, from its frame 0
    assert abs(_gray(out, frames - 1) - _gray(src, 59)) <= 1.5       # it still ends on its own last frame

    sa, oa = _pcm(src), _pcm(out)
    assert abs(len(oa) / SR - frames / 25.0) <= 1 / 25.0
    j = int(38 / 25.0 * SR)
    near = max(abs(v) for v in oa[j - SR // 1000:j + SR // 1000])
    peak = max(abs(v) for v in oa[j - SR // 20:j - SR // 50])
    assert near / peak <= 0.3                                        # no click: code 0.066, mutant (b) 1.0
    ratio = _rms(oa, 0.3, 0.7) / _rms(sa, 0.88 + 0.3, 0.88 + 0.7)
    assert 0.9 <= ratio <= 1.1                                       # the hook's own sound: mutant (g) 0.558


def test_frames_come_from_the_video_stream_when_the_audio_is_longer(tmp_path):
    """Preflight condition 1: audio 0.1 s (2.5 frames) longer than the video; the container says 2.5 s."""
    import reels
    fx = _fx()
    src, out = tmp_path / "short_01.mp4", tmp_path / "out.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=gray:s=64x64:r=25:d=2.4",
                    "-f", "lavfi", "-i", "sine=f=440:r=%d:d=2.5" % SR, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(src)], check=True)
    info = fx.hook_probe(src, reels.run_step)
    assert info["frames"] == 60 and info["audio"] is True
    reels.run_step("hook_concat", fx.hook_args(src, out, info, 38))
    frames = fx.hook_probe(out, reels.run_step)["frames"]
    assert frames == 98
    assert abs(len(_pcm(out)) / SR - frames / 25.0) <= 1 / 25.0


def test_a_reel_without_sound_is_refused_and_left_untouched(tmp_path):
    """D-69: no audio stream gives HookError (StepError("result_hook") in build); short_NN.mp4 stays as it was."""
    import reels
    fx = _fx()
    src = tmp_path / "short_01.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=gray:s=64x64:r=25:d=2.4",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src)], check=True)
    before = src.read_bytes()
    assert fx.hook_probe(src, reels.run_step)["audio"] is False
    with pytest.raises(fx.HookError):
        fx.apply_hook({"result_hook": {"d": 1.0}}, 1, src, tmp_path / "work", reels.run_step)
    assert src.read_bytes() == before


# ------------------------------------------------------------------ 3. reels.build with a simulated run_step

def _words(*spec):
    return [{"word": w, "start": s, "end": s + 0.3} for w, s in spec]


SEGS = [{"id": i, "start": 10.0 * i, "end": 10.0 * i + 5.0} for i in (1, 2, 3)]
WORDS = [{"start": 0, "end": 40, "text": "x",
          "words": _words(("unu", 10.4), ("primul", 20.52), ("al", 21.6), ("doilea", 21.92), ("asa", 22.8),
                          ("trei", 30.4))}]
ITEMS = [{"text": "Unu", "cue": "primul"}, {"text": "Doi", "cue": "al doilea"}]
IMPACT = [{"text": "Stop", "t": 1.0, "d": 0.6}]
HOOK = {"d": 1.52}


def _fake_run(calls, segments):
    def fake(step, args, cwd=None, timeout=None):
        args = [str(a) for a in args]
        calls.append((step, args, str(cwd) if cwd else None))
        if step == "snap_boundaries":
            Path(args[args.index("--output") + 1]).write_text(json.dumps({"segments": segments}))
        elif step in ("extract_clip", "list_overlay", "cta_overlay", "impact_blend", "hook_concat"):
            Path(args[-1]).write_bytes(step.encode())
        elif step in ("list_probe", "cta_probe", "impact_probe"):
            return json.dumps({"streams": [{"width": 1080, "height": 1920, "r_frame_rate": "25/1"}],
                               "format": {"duration": "5.0"}})
        elif step == "hook_probe":
            return json.dumps({"streams": [{"codec_type": "video", "width": 1080, "height": 1920,
                                            "r_frame_rate": "25/1", "nb_read_packets": "125"},
                                           {"codec_type": "audio", "nb_read_packets": "235"}]})
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


def _build(tmp_path, monkeypatch, segments):
    import reels
    calls, warnings = [], []
    monkeypatch.setenv("AIRTIME_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(reels, "run_step", _fake_run(calls, segments))
    monkeypatch.setattr(reels, "probe", lambda p: (1080, 1920, 5.0))
    tr = tmp_path / "t.json"
    tr.write_text(json.dumps({"segments": WORDS}))
    ap = tmp_path / "approved.json"
    ap.write_text(json.dumps({"segments": segments}))
    reels.build(tmp_path / "curat.mp4", tr, ap, "bold", tmp_path / "out", "vertical", warnings=warnings)
    return calls, warnings


def test_reels_hook_only_on_the_marked_segment(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[1]["result_hook"] = HOOK
    calls, warnings = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls] == ["snap_boundaries", "extract_clip", "extract_clip", "extract_clip", "render",
                                     "hook_probe", "hook_concat", "export"]
    render_dir = tmp_path / "out" / "work" / "render"
    assert calls[5][1][-1] == str(render_dir / "short_02.mp4")
    fc = calls[6][1][calls[6][1].index("-filter_complex") + 1]
    assert "trim=start_frame=87" in fc and "concat=n=2:v=1:a=1" in fc       # 125 - 38 frames
    assert calls[6][1][3] == str(render_dir / "short_02.mp4")
    assert (render_dir / "short_02.mp4").read_bytes() == b"hook_concat"
    assert (render_dir / "short_01.mp4").read_bytes() == b"short"
    assert (render_dir / "short_03.mp4").read_bytes() == b"short"
    assert warnings == []


def test_hook_is_the_last_pass_after_list_cta_and_impact(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[1].update(list=ITEMS, cta={"word": "Postura", "from_s": 3.0}, impact=IMPACT, result_hook=HOOK)
    calls, warnings = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls][5:] == ["list_probe", "list_render", "list_overlay", "cta_probe", "cta_render",
                                         "cta_overlay", "impact_probe", "impact_render", "impact_blend",
                                         "hook_probe", "hook_concat", "export"]
    assert warnings == []


def test_segment_without_speech_keeps_the_hook(tmp_path, monkeypatch):
    segs = [dict(s) for s in SEGS]
    segs[2] = {"id": 3, "start": 35.0, "end": 40.0, "result_hook": HOOK}
    calls, warnings = _build(tmp_path, monkeypatch, segs)
    assert [c[0] for c in calls][5:] == ["hook_probe", "hook_concat", "export"]
    assert warnings == []


def test_a_bad_hook_stops_the_build(tmp_path, monkeypatch):
    import reels
    for n, bad in enumerate(({"d": 5.0}, "da", {"d": True})):
        segs = [dict(s) for s in SEGS]
        segs[0]["result_hook"] = bad
        (tmp_path / str(n)).mkdir()
        with pytest.raises(reels.StepError) as e:
            _build(tmp_path / str(n), monkeypatch, segs)
        assert e.value.step == "result_hook"

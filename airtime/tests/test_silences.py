from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import silences

FIXTURE = Path(__file__).parent / "fixtures" / "transcript_retake.json"
DURATION = 24.0


def _words():
    return silences.load_words(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _w(text, start, end):
    return {"text": text, "start": start, "end": end}


def _overlaps(a, b):
    return a["start"] < b["end"] and b["start"] < a["end"]


def test_load_words_normalizes_text():
    words = _words()
    assert words[0] == {"text": "Bună", "start": 1.0, "end": 1.4}
    assert len(words) == 17


def test_gap_over_4s_is_demo():
    regions = silences.classify_regions(_words(), DURATION, voiceover=False)
    demos = [r for r in regions if r["kind"] == "demo"]
    assert len(demos) == 1
    assert demos[0]["start"] == pytest.approx(9.0)
    assert demos[0]["end"] == pytest.approx(21.0)
    # regions tile the clip
    assert regions[0]["start"] == 0.0 and regions[-1]["end"] == DURATION


def test_no_cut_inside_demo():
    words = _words()
    regions = silences.classify_regions(words, DURATION, voiceover=False)
    demos = [r for r in regions if r["kind"] == "demo"]
    for clip_type in ("vorbit", "culise", "demonstratii"):
        cuts = silences.propose_cuts(words, regions, DURATION, clip_type, False)
        assert cuts
        for c in cuts:
            assert not any(_overlaps(c, d) for d in demos), (clip_type, c)


def test_pause_threshold_by_clip_type():
    words = _words()
    regions = silences.classify_regions(words, DURATION, False)
    for clip_type in ("vorbit", "demonstratii"):
        pauses = [c for c in silences.propose_cuts(words, regions, DURATION, clip_type, False)
                  if c["reason"] == "pauza"]
        assert len(pauses) == 1
        assert pauses[0]["start"] == pytest.approx(6.25)
        assert pauses[0]["end"] == pytest.approx(7.25)

    short = [_w("a", 1.0, 1.4), _w("b", 2.3, 2.7), _w("c", 2.8, 3.0)]  # 0.9 s gap
    regions = silences.classify_regions(short, 6.0, False)
    by_type = {
        t: [c for c in silences.propose_cuts(short, regions, 6.0, t, False) if c["reason"] == "pauza"]
        for t in ("vorbit", "culise", "demonstratii")
    }
    assert len(by_type["vorbit"]) == 1
    assert by_type["culise"] == [] and by_type["demonstratii"] == []


def test_retake_detected():
    words = _words()
    regions = silences.classify_regions(words, DURATION, False)
    cuts = silences.propose_cuts(words, regions, DURATION, "vorbit", False)
    retakes = [c for c in cuts if c["reason"] == "reluare"]
    assert len(retakes) == 1
    assert retakes[0]["start"] == pytest.approx(1.0)
    assert retakes[0]["end"] == pytest.approx(3.6)
    assert retakes[0]["text"].startswith("Bună ziua azi facem")


def test_edges_proposed():
    words = _words()
    regions = silences.classify_regions(words, DURATION, False)
    edges = [c for c in silences.propose_cuts(words, regions, DURATION, "vorbit", False)
             if c["reason"] == "capat"]
    assert [(round(c["start"], 3), round(c["end"], 3)) for c in edges] == [(0.0, 0.5), (23.5, 24.0)]


def test_voiceover_no_pause_cuts():
    words = _words()
    regions = silences.classify_regions(words, DURATION, voiceover=True)
    assert [r["kind"] for r in regions] == ["demo"]
    cuts = silences.propose_cuts(words, regions, DURATION, "vorbit", True,
                                 freeze=[(0.0, 1.0), (23.0, 24.0)])
    assert len(cuts) == 2
    assert {c["reason"] for c in cuts} == {"capat"}
    assert silences.propose_cuts(words, regions, DURATION, "vorbit", True) == []


def test_no_words_only_edges():
    regions = silences.classify_regions([], 10.0, False)
    cuts = silences.propose_cuts([], regions, 10.0, "vorbit", False, freeze=[(0.0, 1.0), (9.0, 10.0)])
    assert cuts
    assert all(c["reason"] == "capat" for c in cuts)
    assert silences.propose_cuts([], regions, 10.0, "vorbit", False) == []
    assert silences.load_words({}) == []
    assert silences.load_words({"segments": [{"start": 0, "end": 1, "text": "x"}]}) == []


def test_parse_freeze_edges():
    err = (
        "[freezedetect @ 0x1] lavfi.freezedetect.freeze_start: 0\n"
        "[freezedetect @ 0x1] lavfi.freezedetect.freeze_duration: 1.5\n"
        "[freezedetect @ 0x1] lavfi.freezedetect.freeze_end: 1.5\n"
        "[freezedetect @ 0x1] lavfi.freezedetect.freeze_start: 8.5\n"
    )
    assert silences.parse_freeze_edges(err, 10.0) == [(0.0, 1.5), (8.5, 10.0)]
    # a freeze in the middle is not an edge
    mid = ("freeze_start: 3\nfreeze_duration: 2\nfreeze_end: 5\n")
    assert silences.parse_freeze_edges(mid, 10.0) == []


def test_keep_and_remap_roundtrip():
    cuts = [{"start": 1.0, "end": 3.6}, {"start": 6.25, "end": 7.25}]
    keep = silences.keep_intervals(DURATION, cuts)
    assert keep == [(0.0, 1.0), (3.6, 6.25), (7.25, 24.0)]
    assert silences.remap(2.0, keep) is None
    for t, removed in ((3.7, 2.6), (7.5, 3.6), (0.5, 0.0), (22.0, 3.6)):
        assert silences.remap(t, keep) == pytest.approx(t - removed, abs=0.001)


def test_remap_transcript_drops_cut_material():
    transcript = json.loads(FIXTURE.read_text(encoding="utf-8"))
    keep = silences.keep_intervals(DURATION, [{"start": 1.0, "end": 3.6}])
    out = silences.remap_transcript(transcript, keep)
    assert len(out["segments"]) == 3
    first = out["segments"][0]
    assert first["start"] == pytest.approx(1.0)
    assert first["words"][0]["start"] == pytest.approx(1.0)
    assert out["captions"][0]["startMs"] == 1000
    assert out["captions"][0]["text"].startswith("Bună ziua, azi începem")
    assert len(out["captions"]) == 3


def test_cli_propose_and_apply(tmp_path):
    d = tmp_path / "clip cu spații și diacritice ăî"
    d.mkdir()
    video = d / "sursă.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=25:duration=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=10", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(video)],
        check=True,
    )
    transcript = d / "t.json"
    transcript.write_text(json.dumps({"segments": [{"start": 1, "end": 2, "text": "a b", "words": [
        {"word": "a", "start": 1.0, "end": 1.5}, {"word": "b", "start": 3.5, "end": 4.0}]}], "captions": []}))
    out = d / "cuts-propuse.json"
    frames = d / "frames"
    assert silences.main(["propose", "--transcript", str(transcript), "--video", str(video),
                          "--clip-type", "vorbit", "--out", str(out), "--frames-dir", str(frames)]) == 0
    proposed = json.loads(out.read_text())
    assert set(proposed) == {"duration", "regions", "cuts"}
    assert proposed["cuts"]
    for c in proposed["cuts"]:
        assert (frames / ("cut_%s.jpg" % c["id"])).stat().st_size > 0


def test_apply_duration(tmp_path):
    d = tmp_path / "clip ț"
    d.mkdir()
    video = d / "in.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=25:duration=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=10", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(video)],
        check=True,
    )
    cuts = d / "cuts-aprobate.json"
    cuts.write_text(json.dumps({"cuts": [{"id": 1, "start": 4.0, "end": 6.0, "reason": "pauza", "text": ""}]}))
    out, mp = d / "curat.mp4", d / "map.json"
    assert silences.main(["apply", "--video", str(video), "--cuts", str(cuts), "--out", str(out),
                          "--map", str(mp)]) == 0
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
        check=True, capture_output=True, text=True).stdout)
    assert dur == pytest.approx(8.0, abs=0.1)
    m = json.loads(mp.read_text())
    assert m["keep"] == [[0.0, 4.0], [6.0, m["duration"]]]

    tr = d / "t.json"
    tr.write_text(json.dumps({"segments": [], "captions": [
        {"text": "x", "startMs": 7000, "endMs": 8000}, {"text": "y", "startMs": 4500, "endMs": 5500}]}))
    outt = d / "tc.json"
    assert silences.main(["remap", "--transcript", str(tr), "--map", str(mp), "--out", str(outt)]) == 0
    caps = json.loads(outt.read_text())["captions"]
    assert caps == [{"text": "x", "startMs": 5000, "endMs": 6000}]


def _frozen_head_clip(path):
    # 2 s frozen red head, then 3 s moving test pattern
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=160x120:r=25:d=2",
         "-f", "lavfi", "-i", "testsrc=size=160x120:rate=25:duration=3",
         "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]", "-map", "[v]",
         "-c:v", "libx264", str(path)],
        check=True,
    )


@pytest.mark.parametrize("with_words,voiceover", [(False, False), (True, True)])
def test_cli_propose_edge_cuts_from_freeze(tmp_path, capsys, with_words, voiceover):
    d = tmp_path / "frozen clip ș"
    d.mkdir()
    video = d / "frozen.mp4"
    _frozen_head_clip(video)
    transcript = d / "t.json"
    segs = []
    if with_words:
        segs = [{"start": 2.5, "end": 3.5, "text": "a b", "words": [
            {"word": "a", "start": 2.5, "end": 3.0}, {"word": "b", "start": 3.0, "end": 3.5}]}]
    transcript.write_text(json.dumps({"segments": segs, "captions": []}))
    out = d / "cuts.json"
    argv = ["propose", "--transcript", str(transcript), "--video", str(video), "--clip-type", "vorbit",
            "--out", str(out), "--frames-dir", str(d / "frames")]
    if voiceover:
        argv.append("--voiceover")
    assert silences.main(argv) == 0
    cuts = json.loads(out.read_text())["cuts"]
    assert cuts
    assert all(c["reason"] == "capat" for c in cuts)
    assert cuts[0]["start"] == pytest.approx(0.0, abs=0.1)
    assert cuts[0]["end"] == pytest.approx(2.0, abs=0.2)
    assert (d / "frames" / ("cut_%s.jpg" % cuts[0]["id"])).exists()
    err = capsys.readouterr().err
    assert ("nu are vorbire" in err) == (not with_words)


def _color(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=color_transfer,color_primaries,pix_fmt", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)["streams"][0]


def test_tonemap_chain_only_for_hdr():
    assert silences.tonemap_filter("bt709") == ""
    assert silences.tonemap_filter("") == ""
    hlg = silences.tonemap_filter("arib-std-b67")
    pq = silences.tonemap_filter("smpte2084")
    for f in (hlg, pq):
        assert "tonemap=" in f and "zscale" in f and f.endswith("format=yuv420p")
    assert "tin=arib-std-b67" in hlg and "tin=smpte2084" in pq


@pytest.fixture(autouse=True)
def _fresh_has_filter_cache():
    silences.has_filter.cache_clear()
    yield
    silences.has_filter.cache_clear()


@pytest.mark.skipif(not shutil.which("ffmpeg") or not silences.has_filter("zscale"),
                    reason="ffmpeg without zscale")
def test_apply_tone_maps_iphone_hlg(tmp_path):
    """iPhone HDR (HLG, 10-bit, bt2020) comes out of apply as 8-bit bt709 SDR."""
    video = tmp_path / "iPhone HDR ș.mov"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=25:duration=3",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
         "-vf", "format=yuv420p10le", "-c:v", "libx265",
         "-x265-params", "log-level=error:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc",
         "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc",
         "-tag:v", "hvc1", "-c:a", "aac", "-shortest", str(video)],
        check=True,
    )
    assert silences.color_transfer(str(video)) == "arib-std-b67"
    cuts = tmp_path / "cuts.json"
    cuts.write_text(json.dumps({"cuts": [{"id": 1, "start": 1.0, "end": 1.5, "reason": "pauza", "text": ""}]}))
    out, mp = tmp_path / "curat.mp4", tmp_path / "map.json"
    assert silences.main(["apply", "--video", str(video), "--cuts", str(cuts), "--out", str(out),
                          "--map", str(mp)]) == 0
    c = _color(out)
    assert c["pix_fmt"] == "yuv420p"
    assert c.get("color_transfer") == "bt709"
    assert c.get("color_primaries") == "bt709"


def test_apply_sdr_has_no_tonemap(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(silences, "probe_duration", lambda v: 10.0)
    monkeypatch.setattr(silences, "has_audio", lambda v: False)
    monkeypatch.setattr(silences, "color_transfer", lambda v: "bt709")
    monkeypatch.setattr(silences, "_run", lambda cmd: seen.setdefault("cmd", cmd))
    silences.apply_cuts("in.mp4", [], str(tmp_path / "o.mp4"))
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1]
    assert "tonemap" not in graph and "-color_trc" not in seen["cmd"]


# ---- I5 follow-up: ffmpeg without zscale (Homebrew build has no libzimg)

FILTERS_WITH = " ... zscale  V->V  Apply resizing, colorspace and bit depth conversions.\n T. tonemap V->V Conversion to/from.\n"
FILTERS_WITHOUT = " T.. tonemap V->V Conversion.\n ... scale V->V Scale the input video.\n"


def _fake_apply_env(monkeypatch, filters_text, transfer="arib-std-b67"):
    silences.has_filter.cache_clear()
    seen = {}
    monkeypatch.setattr(silences, "probe_duration", lambda v: 10.0)
    monkeypatch.setattr(silences, "has_audio", lambda v: False)
    monkeypatch.setattr(silences, "color_transfer", lambda v: transfer)

    def fake_run(cmd):
        if cmd[:3] == ["ffmpeg", "-hide_banner", "-filters"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=filters_text, stderr="")
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(silences, "_run", fake_run)
    return seen


def test_has_filter_parses_and_caches(monkeypatch):
    _fake_apply_env(monkeypatch, FILTERS_WITH)
    assert silences.has_filter("zscale") is True
    assert silences.has_filter("nosuch") is False
    silences.has_filter.cache_clear()
    _fake_apply_env(monkeypatch, FILTERS_WITHOUT)
    assert silences.has_filter("zscale") is False


def test_apply_hdr_with_zscale_tone_maps(tmp_path, monkeypatch):
    seen = _fake_apply_env(monkeypatch, FILTERS_WITH)
    res = silences.apply_cuts("in.mov", [], str(tmp_path / "o.mp4"))
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1]
    assert "zscale" in graph and "tonemap" in graph
    assert "-color_trc" in seen["cmd"]
    assert "warnings" not in res


def test_apply_hdr_without_zscale_skips_tone_map_and_warns(tmp_path, monkeypatch):
    seen = _fake_apply_env(monkeypatch, FILTERS_WITHOUT)
    res = silences.apply_cuts("in.mov", [{"id": 1, "start": 2.0, "end": 3.0, "reason": "p", "text": ""}],
                              str(tmp_path / "o.mp4"))
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1]
    assert "zscale" not in graph and "tonemap" not in graph
    assert "-color_trc" not in seen["cmd"]
    assert graph.count("trim=") == 2  # cuts still applied
    assert res["keep"] == [[0.0, 2.0], [3.0, 10.0]]
    (w,) = res["warnings"]
    assert "Video HDR" in w and "spălate" in w and "iPhone" in w


def test_apply_sdr_never_checks_filters(tmp_path, monkeypatch):
    seen = _fake_apply_env(monkeypatch, FILTERS_WITHOUT, transfer="bt709")
    res = silences.apply_cuts("in.mp4", [], str(tmp_path / "o.mp4"))
    assert "warnings" not in res and "cmd" in seen


def test_cli_apply_warning_is_printed(tmp_path, monkeypatch, capsys):
    _fake_apply_env(monkeypatch, FILTERS_WITHOUT)
    cuts = tmp_path / "cuts.json"
    cuts.write_text(json.dumps({"cuts": []}))
    rc = silences.main(["apply", "--video", "in.mov", "--cuts", str(cuts), "--out", str(tmp_path / "o.mp4"),
                        "--map", str(tmp_path / "map.json")])
    assert rc == 0
    assert "Video HDR" in json.loads(capsys.readouterr().out)["warnings"][0]


def test_cli_apply_ffmpeg_failure_is_json_error(tmp_path, monkeypatch, capsys):
    silences.has_filter.cache_clear()
    monkeypatch.setattr(silences, "probe_duration", lambda v: 10.0)
    monkeypatch.setattr(silences, "has_audio", lambda v: False)
    monkeypatch.setattr(silences, "color_transfer", lambda v: "bt709")

    def boom(cmd):
        raise subprocess.CalledProcessError(1, cmd, output="", stderr="x" * 5000 + "No such filter: 'zscale'")

    monkeypatch.setattr(silences, "_run", boom)
    cuts = tmp_path / "cuts.json"
    cuts.write_text(json.dumps({"cuts": []}))
    rc = silences.main(["apply", "--video", "in.mov", "--cuts", str(cuts), "--out", str(tmp_path / "o.mp4"),
                        "--map", str(tmp_path / "map.json")])
    out = capsys.readouterr()
    assert rc == 1
    err = json.loads(out.out)["error"]
    assert "No such filter" in err and len(err) < 2000 and "Traceback" not in out.err


# ---- 4a: RMS snap of cut edges (inward only) and 30 ms fades at joins

def _samples(rate, duration, quiet):
    """Loud square wave (amplitude 8000) with silent stretches [(a, b), ...]."""
    from array import array
    n = int(rate * duration)
    s = array("h", [8000 if (i // 4) % 2 else -8000 for i in range(n)])
    for a, b in quiet:
        for i in range(int(round(a * rate)), min(n, int(round(b * rate)))):
            s[i] = 0
    return s


def test_snap_moves_edges_inward_to_silence():
    s = _samples(8000, 4.0, [(1.08, 1.10), (1.90, 1.92)])
    cut = {"id": 1, "start": 1.0, "end": 2.0, "reason": "pauza", "text": ""}
    out = silences.snap_cuts([cut], s, 8000, 4.0)[0]
    assert 1.08 <= out["start"] <= 1.10
    assert 1.90 <= out["end"] <= 1.92
    assert out["id"] == 1 and out["reason"] == "pauza"
    assert cut["start"] == 1.0 and cut["end"] == 2.0   # input untouched


def test_snap_never_grows_the_cut():
    s = _samples(8000, 4.0, [(0.90, 0.99), (2.01, 2.10)])   # silence only outside the cut
    out = silences.snap_cuts([{"id": 1, "start": 1.0, "end": 2.0}], s, 8000, 4.0)[0]
    assert out["start"] == 1.0 and out["end"] == 2.0


def test_snap_searches_150ms_only():
    s = _samples(8000, 4.0, [(1.30, 1.32), (1.68, 1.70)])   # silence too far from both edges
    out = silences.snap_cuts([{"id": 1, "start": 1.0, "end": 2.0}], s, 8000, 4.0)[0]
    assert out["start"] == 1.0 and out["end"] == 2.0


def test_snap_skips_short_cuts_and_clip_edges():
    s = _samples(8000, 4.0, [(0.05, 0.07), (0.40, 0.42), (1.05, 1.07), (3.55, 3.57), (3.90, 3.95)])
    cuts = [{"id": 1, "start": 0.0, "end": 0.5}, {"id": 2, "start": 1.0, "end": 1.2},
            {"id": 3, "start": 3.5, "end": 4.0}]
    out = silences.snap_cuts(cuts, s, 8000, 4.0)
    assert out[0]["start"] == 0.0 and 0.40 <= out[0]["end"] <= 0.42
    assert out[1] == cuts[1]          # 0.2 s: untouched
    assert 3.55 <= out[2]["start"] <= 3.57 and out[2]["end"] == 4.0


def test_apply_fades_audio_at_joins_only(tmp_path, monkeypatch):
    seen = _fake_apply_env(monkeypatch, FILTERS_WITHOUT, transfer="bt709")
    monkeypatch.setattr(silences, "has_audio", lambda v: True)
    monkeypatch.setattr(silences, "read_audio", lambda v, rate=8000: _samples(rate, 10.0, []))
    res = silences.apply_cuts("in.mp4", [{"id": 1, "start": 4.0, "end": 5.0, "reason": "p", "text": ""}],
                              str(tmp_path / "o.mp4"), jl=False)   # fades alone; with the J-cut: 4b tests
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1].split(";")
    a0 = [p for p in graph if p.startswith("[0:a]") and p.endswith("[a0]")][0]
    a1 = [p for p in graph if p.startswith("[0:a]") and p.endswith("[a1]")][0]
    assert "afade=t=out:st=3.970000:d=0.030" in a0 and "afade=t=in" not in a0
    assert "afade=t=in:st=0:d=0.030" in a1 and "afade=t=out" not in a1
    assert res["keep"] == [[0.0, 4.0], [5.0, 10.0]]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="no ffmpeg")
def test_apply_snaps_to_real_silence(tmp_path):
    clip = tmp_path / "in.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=25:duration=6",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
         "-af", "volume=enable='between(t,2.08,2.95)':volume=0",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)],
        check=True,
    )
    res = silences.apply_cuts(str(clip), [{"id": 1, "start": 2.0, "end": 3.0, "reason": "p", "text": ""}],
                              str(tmp_path / "o.mp4"))
    (_, b), (c, _) = res["keep"]
    assert 2.06 <= b <= 2.13
    assert 2.89 <= c <= 2.97


def test_snap_ties_pick_the_window_nearest_the_edge():
    s = _samples(8000, 4.0, [(1.03, 1.05), (1.10, 1.12), (1.88, 1.90), (1.95, 1.97)])
    out = silences.snap_cuts([{"id": 1, "start": 1.0, "end": 2.0}], s, 8000, 4.0)[0]
    assert 1.03 <= out["start"] <= 1.05
    assert 1.95 <= out["end"] <= 1.97


def test_snap_needs_a_window_twice_as_quiet():
    s = _samples(8000, 4.0, [])
    lo, hi = int(round(1.05 * 8000)), int(round(1.07 * 8000))
    for i in range(lo, hi):
        s[i] = s[i] * 3 // 4             # only 25 % quieter: the edge stays
    assert silences.snap_cuts([{"id": 1, "start": 1.0, "end": 2.0}], s, 8000, 4.0)[0]["start"] == 1.0
    for i in range(lo, hi):
        s[i] = s[i] // 3                 # now a quarter of the edge level: the edge moves
    assert 1.05 <= silences.snap_cuts([{"id": 1, "start": 1.0, "end": 2.0}], s, 8000, 4.0)[0]["start"] <= 1.07


def test_apply_no_fade_on_pieces_of_60ms_or_less(tmp_path, monkeypatch):
    seen = _fake_apply_env(monkeypatch, FILTERS_WITHOUT, transfer="bt709")
    monkeypatch.setattr(silences, "has_audio", lambda v: True)
    monkeypatch.setattr(silences, "read_audio", lambda v, rate=8000: _samples(rate, 10.0, []))
    cuts = [{"id": 1, "start": 4.0, "end": 5.0}, {"id": 2, "start": 5.05, "end": 6.0}]
    res = silences.apply_cuts("in.mp4", cuts, str(tmp_path / "o.mp4"), jl=False)
    assert res["keep"] == [[0.0, 4.0], [5.0, 5.05], [6.0, 10.0]]
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1].split(";")
    a = {i: [p for p in graph if p.startswith("[0:a]") and p.endswith("[a%d]" % i)][0] for i in range(3)}
    assert "afade" not in a[1]                       # 50 ms piece: no fade at all
    assert "afade=t=out" in a[0] and "afade=t=in" in a[2]


# ---- 4b: J-cut of 150 ms at joins (D-09)

def _trims(graph, kind):
    """[(start, end), ...] of the video ('v') or audio ('a') pieces, in order."""
    pat = r"\[0:v\]trim=start=([0-9.]+):end=([0-9.]+)" if kind == "v" else \
        r"\[0:a\]atrim=start=([0-9.]+):end=([0-9.]+)"
    return [(round(float(a), 6), round(float(b), 6)) for a, b in re.findall(pat, graph)]


def _apply_graph(tmp_path, monkeypatch, cuts, **kw):
    seen = _fake_apply_env(monkeypatch, FILTERS_WITHOUT, transfer="bt709")
    monkeypatch.setattr(silences, "has_audio", lambda v: True)
    monkeypatch.setattr(silences, "read_audio", lambda v, rate=8000: _samples(rate, 10.0, []))
    res = silences.apply_cuts("in.mp4", cuts, str(tmp_path / "o.mp4"), **kw)
    return res, seen["cmd"][seen["cmd"].index("-filter_complex") + 1]


def test_apply_jcut_starts_next_audio_150ms_early(tmp_path, monkeypatch):
    res, graph = _apply_graph(tmp_path, monkeypatch, [{"id": 1, "start": 4.0, "end": 5.0}])
    assert _trims(graph, "v") == [(0.0, 4.0), (5.0, 10.0)]          # picture as before
    assert _trims(graph, "a") == [(0.0, 3.85), (4.85, 10.0)]        # sound leads by 150 ms
    assert res["keep"] == [[0.0, 4.0], [5.0, 10.0]]                 # map.json unchanged
    a0 = [p for p in graph.split(";") if p.endswith("[a0]")][0]
    a1 = [p for p in graph.split(";") if p.endswith("[a1]")][0]
    assert "afade=t=out:st=3.820000:d=0.030" in a0 and "afade=t=in:st=0:d=0.030" in a1


def test_apply_without_jl_audio_follows_video(tmp_path, monkeypatch):
    _, graph = _apply_graph(tmp_path, monkeypatch, [{"id": 1, "start": 4.0, "end": 5.0}], jl=False)
    assert _trims(graph, "a") == _trims(graph, "v") == [(0.0, 4.0), (5.0, 10.0)]


def test_apply_jcut_only_where_cut_and_previous_piece_are_long_enough(tmp_path, monkeypatch):
    cuts = [{"id": 1, "start": 2.0, "end": 3.0},     # join 0: cut 1 s, piece before 2 s   -> J
            {"id": 2, "start": 3.2, "end": 5.0},     # join 1: piece before only 0.2 s     -> no J
            {"id": 3, "start": 7.0, "end": 7.21},    # join 2: cut exactly 0.21 s          -> J
            {"id": 4, "start": 8.0, "end": 8.2}]     # join 3: cut only 0.2 s              -> no J
    res, graph = _apply_graph(tmp_path, monkeypatch, cuts)
    assert _trims(graph, "v") == [(0.0, 2.0), (3.0, 3.2), (5.0, 7.0), (7.21, 8.0), (8.2, 10.0)]
    assert _trims(graph, "a") == [(0.0, 1.85), (2.85, 3.2), (5.0, 6.85), (7.06, 8.0), (8.2, 10.0)]
    assert res["keep"] == [[0.0, 2.0], [3.0, 3.2], [5.0, 7.0], [7.21, 8.0], [8.2, 10.0]]


def test_cli_apply_fara_jl(tmp_path, monkeypatch):
    seen = _fake_apply_env(monkeypatch, FILTERS_WITHOUT, transfer="bt709")
    monkeypatch.setattr(silences, "has_audio", lambda v: True)
    monkeypatch.setattr(silences, "read_audio", lambda v, rate=8000: _samples(rate, 10.0, []))
    cuts = tmp_path / "cuts.json"
    cuts.write_text(json.dumps({"cuts": [{"id": 1, "start": 4.0, "end": 5.0}]}))
    args = ["apply", "--video", "in.mp4", "--cuts", str(cuts), "--out", str(tmp_path / "o.mp4"),
            "--map", str(tmp_path / "map.json")]
    assert silences.main(args + ["--fara-jl"]) == 0
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1]
    assert _trims(graph, "a") == _trims(graph, "v")
    assert silences.main(args) == 0
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1]
    assert _trims(graph, "a") == [(0.0, 3.85), (4.85, 10.0)]


def test_apply_jcut_fade_rule_counts_the_sound_piece(tmp_path, monkeypatch):
    # 50 ms of picture after a J-cut join carries 200 ms of sound: that sound piece gets its fades
    cuts = [{"id": 1, "start": 4.0, "end": 5.0}, {"id": 2, "start": 5.05, "end": 6.0}]
    res, graph = _apply_graph(tmp_path, monkeypatch, cuts)
    assert _trims(graph, "a") == [(0.0, 3.85), (4.85, 5.05), (6.0, 10.0)]
    a1 = [p for p in graph.split(";") if p.endswith("[a1]")][0]
    assert "afade=t=in:st=0:d=0.030" in a1 and "afade=t=out:st=0.170000:d=0.030" in a1


def test_apply_jcut_measures_the_cut_after_snapping(tmp_path, monkeypatch):
    # approved cut 0.32 s; snapped to the silence inside it, only 0.19 s is left: no J-cut
    seen = _fake_apply_env(monkeypatch, FILTERS_WITHOUT, transfer="bt709")
    monkeypatch.setattr(silences, "has_audio", lambda v: True)
    monkeypatch.setattr(silences, "read_audio",
                        lambda v, rate=8000: _samples(rate, 10.0, [(4.05, 4.07), (4.23, 4.25)]))
    res = silences.apply_cuts("in.mp4", [{"id": 1, "start": 4.0, "end": 4.32}], str(tmp_path / "o.mp4"))
    graph = seen["cmd"][seen["cmd"].index("-filter_complex") + 1]
    assert _trims(graph, "v") == [(0.0, 4.055), (4.245, 10.0)]
    assert _trims(graph, "a") == _trims(graph, "v")


def test_apply_jcut_needs_the_previous_piece_longer_than_210ms(tmp_path, monkeypatch):
    cuts = [{"id": 1, "start": 2.0, "end": 3.0}, {"id": 2, "start": 3.21, "end": 5.0}]   # piece of 0.21 s
    _, graph = _apply_graph(tmp_path, monkeypatch, cuts)
    assert _trims(graph, "v") == [(0.0, 2.0), (3.0, 3.21), (5.0, 10.0)]
    assert _trims(graph, "a") == [(0.0, 1.85), (2.85, 3.21), (5.0, 10.0)]


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="no ffmpeg")
def test_apply_jcut_keeps_audio_and_video_the_same_length(tmp_path):
    clip = tmp_path / "in.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=25:duration=6",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)],
        check=True,
    )
    out = tmp_path / "o.mp4"
    silences.apply_cuts(str(clip), [{"id": 1, "start": 2.0, "end": 3.0}, {"id": 2, "start": 4.0, "end": 4.5}],
                        str(out))

    def dur(stream):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries",
                            "stream=duration", "-of", "csv=p=0", str(out)], capture_output=True, text=True)
        return float(r.stdout.strip())

    assert abs(dur("v:0") - 4.5) < 0.05
    assert abs(dur("a:0") - dur("v:0")) < 0.05

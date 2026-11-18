"""Function 1, B-roll (D-14): folder scan, the table rules, placing by map.json and the overlay."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import broll
import silences


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _clip(path, dur, size="320x240", rate=25, video="testsrc", audio="silence"):
    """audio: 'silence', 'sine' or None (no audio stream)."""
    src = "testsrc=size=%s:rate=%d:duration=%s" % (size, rate, dur) if video == "testsrc" \
        else "color=c=%s:s=%s:r=%d:d=%s" % (video, size, rate, dur)
    args = ["-f", "lavfi", "-i", src]
    if audio == "sine":
        args += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%s" % dur]
    elif audio == "silence":
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=%s" % dur]
    args += ["-pix_fmt", "yuv420p", "-c:v", "libx264", "-shortest"]
    if audio:
        args += ["-c:a", "aac"]
    _ff(*args, str(path))
    return path


def _duration(path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(path)], check=True, capture_output=True, text=True)
    return float(r.stdout.strip())


def _pixel(path, t) -> tuple:
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "%.3f" % t, "-i", str(path), "-frames:v", "1",
                        "-vf", "crop=8:8:(iw-8)/2:(ih-8)/2,scale=1:1", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-"], check=True, capture_output=True)
    return tuple(r.stdout[:3])


def _max_volume(path, start, end) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", "%.3f" % start, "-to", "%.3f" % end, "-i", str(path),
                        "-vn", "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "max_volume:" in line:
            return float(line.split("max_volume:")[1].split("dB")[0])
    return -999.0


def _red(px) -> bool:
    return px[0] > 180 and px[1] < 80 and px[2] < 80


# ------------------------------------------------------------ folder scan

def test_list_clips_takes_mp4_mov_m4v_any_case(tmp_path):
    for name in ("b.mp4", "a.MOV", "c.m4v", "note.txt", "d.avi", "._e.mp4", ".f.mov"):
        (tmp_path / name).write_bytes(b"x")
    assert [p.name for p in broll.list_clips(tmp_path)] == ["a.MOV", "b.mp4", "c.m4v"]


def test_speaker_is_longest_clip_with_sound(tmp_path):
    _clip(tmp_path / "lung-fara-sunet.mp4", 6, audio=None)
    _clip(tmp_path / "vorbit.mov", 4, audio="sine")
    _clip(tmp_path / "scurt.mp4", 3, audio="sine")
    assert broll.speaker(tmp_path).name == "vorbit.mov"


def test_speaker_none_when_no_clip_has_sound(tmp_path):
    _clip(tmp_path / "a.mp4", 3, audio=None)
    assert broll.speaker(tmp_path) is None


def test_cadre_three_frames_per_clip_and_skips_under_3s(tmp_path):
    d = tmp_path / "broll"
    d.mkdir()
    _clip(d / "genuflexiuni.mp4", 4, audio=None)
    _clip(d / "scurt.mp4", 2, audio="sine")
    _clip(d / "vorbit.mp4", 5, audio="sine")
    res = broll.cadre(d, tmp_path / "frames", exclude=d / "vorbit.mp4")
    assert [c["src"] for c in res["clips"]] == ["genuflexiuni.mp4"]
    clip = res["clips"][0]
    assert clip["duration"] == pytest.approx(4.0, abs=0.1)
    assert clip["has_audio"] is False
    assert len(clip["frames"]) == 3
    for f in clip["frames"]:
        assert Path(f).is_file() and Path(f).parent == tmp_path / "frames"
    assert [s["src"] for s in res["skipped"]] == ["scurt.mp4"]
    assert "3 s" in res["skipped"][0]["reason"]


# ------------------------------------------------------------ table rules

CLIPS = {"a.mp4": 10.0, "b.mp4": 10.0, "c.mp4": 10.0, "scurt.mp4": 2.5}


def _row(t0, src="a.mp4", dur=4.0, src_in=0.0, **kw):
    r = {"id": 1, "t0": t0, "src": src, "src_in": src_in, "dur": dur, "cuvinte": "", "motiv": ""}
    r.update(kw)
    return r


def test_verifica_accepts_a_good_table():
    rows = [_row(10.0, "a.mp4"), _row(29.0, "b.mp4", volum=0.0), _row(48.0, "c.mp4", volum=1.0)]
    assert broll.verifica(rows, [], 120.0, CLIPS) == []


def test_verifica_duration_between_3_and_5_seconds():
    assert broll.verifica([_row(10.0, dur=3.0)], [], 120.0, CLIPS) == []
    assert broll.verifica([_row(10.0, dur=5.0)], [], 120.0, CLIPS) == []
    assert broll.verifica([_row(10.0, dur=2.9)], [], 120.0, CLIPS)
    assert broll.verifica([_row(10.0, dur=5.1)], [], 120.0, CLIPS)


def test_verifica_volume_default_and_range():
    assert broll.VOLUM == 0.2
    assert broll.normalize([_row(10.0)])[0]["volum"] == 0.2
    assert broll.verifica([_row(10.0, volum=1.5)], [], 120.0, CLIPS)
    assert broll.verifica([_row(10.0, volum=-0.1)], [], 120.0, CLIPS)


def test_verifica_each_clip_only_once():
    rows = [_row(10.0, "a.mp4"), _row(40.0, "a.mp4")]
    assert any("a.mp4" in e for e in broll.verifica(rows, [], 120.0, CLIPS))


def test_verifica_15s_from_end_of_one_to_start_of_next():
    # D-14 (21): first ends at 14.0; the next may start at 29.0, not at 28.9
    assert broll.verifica([_row(10.0, "a.mp4"), _row(29.0, "b.mp4")], [], 120.0, CLIPS) == []
    assert broll.verifica([_row(10.0, "a.mp4"), _row(28.9, "b.mp4")], [], 120.0, CLIPS)


def test_verifica_nothing_in_first_5s_of_the_cut_clip():
    # 2 s cut at the start: original 6.0 is 4.0 on the cut clip
    cuts = [{"start": 0.0, "end": 2.0}]
    assert broll.verifica([_row(6.0)], cuts, 120.0, CLIPS)
    assert broll.verifica([_row(7.0)], cuts, 120.0, CLIPS) == []


def test_verifica_rejects_a_moment_inside_an_approved_cut():
    cuts = [{"start": 20.0, "end": 25.0}]
    assert broll.verifica([_row(22.0)], cuts, 120.0, CLIPS)


def test_verifica_rejects_past_the_end_of_the_cut_clip():
    cuts = [{"start": 50.0, "end": 60.0}]   # cut clip is 50 s long
    assert broll.verifica([_row(47.0, dur=4.0)], cuts, 60.0, CLIPS)
    assert broll.verifica([_row(46.0, dur=4.0)], cuts, 60.0, CLIPS) == []


def test_verifica_rejects_past_the_end_of_the_broll_clip_and_unknown_or_short_clips():
    assert broll.verifica([_row(10.0, src_in=7.0, dur=4.0)], [], 120.0, CLIPS)
    assert broll.verifica([_row(10.0, src_in=6.0, dur=4.0)], [], 120.0, CLIPS) == []
    assert broll.verifica([_row(10.0, src="lipsa.mp4")], [], 120.0, CLIPS)
    assert broll.verifica([_row(10.0, src="scurt.mp4", dur=3.0)], [], 120.0, CLIPS)


def test_place_uses_the_real_cuts_from_map_json():
    # D-14 (16): approved cut 2-4; snapped to 2.1-3.9, so the moment lands 0.1 s later
    rows = [_row(10.0)]
    approx = broll.place(rows, silences.keep_intervals(30.0, [{"start": 2.0, "end": 4.0}]))
    real = broll.place(rows, [(0.0, 2.1), (3.9, 30.0)])
    assert approx[0]["t"] == pytest.approx(8.0)
    assert real[0]["t"] == pytest.approx(8.2)


def test_cli_verifica_code_2_with_errors_and_0_when_good(tmp_path, capsys):
    d = tmp_path / "broll"
    d.mkdir()
    _clip(d / "a.mp4", 4, audio=None)
    video = _clip(tmp_path / "vorbit.mp4", 12, audio="sine")
    cuts = tmp_path / "cuts.json"
    cuts.write_text(json.dumps({"cuts": []}))
    table = tmp_path / "broll-propus.json"
    table.write_text(json.dumps({"broll": [_row(2.0, "a.mp4", dur=3.0)]}))
    assert broll.main(["verifica", "--broll", str(table), "--cuts", str(cuts), "--video", str(video),
                       "--dir", str(d)]) == 2
    assert json.loads(capsys.readouterr().out)["errors"]
    table.write_text(json.dumps({"broll": [_row(6.0, "a.mp4", dur=3.0)]}))
    assert broll.main(["verifica", "--broll", str(table), "--cuts", str(cuts), "--video", str(video),
                       "--dir", str(d)]) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True}


# ------------------------------------------------------------ overlay

def _setup_overlay(tmp_path, broll_audio="sine", volum=None, size="320x240"):
    d = tmp_path / "broll"
    d.mkdir()
    _clip(d / "rosu.mov", 4, size=size, video="red", audio=broll_audio)
    curat = _clip(tmp_path / "curat-fara-broll.mp4", 12, audio="silence")
    m = tmp_path / "map.json"
    m.write_text(json.dumps({"duration": 14.0, "keep": [[0.0, 2.0], [4.0, 14.0]]}))
    row = _row(8.0, "rosu.mov", dur=3.0)       # original 8.0 = cut clip 6.0
    if volum is not None:
        row["volum"] = volum
    table = tmp_path / "broll-aprobat.json"
    table.write_text(json.dumps({"broll": [row]}))
    return d, curat, m, table


def test_aplica_covers_the_frame_at_the_remapped_moment(tmp_path):
    d, curat, m, table = _setup_overlay(tmp_path, size="240x320")   # vertical B-roll on a horizontal clip
    out = tmp_path / "curat.mp4"
    res = broll.aplica(curat, table, m, d, out)
    assert res["inserts"] == 1
    assert _duration(out) == pytest.approx(_duration(curat), abs=0.1)
    assert _red(_pixel(out, 7.5))
    assert not _red(_pixel(out, 5.5))
    assert not _red(_pixel(out, 9.6))
    w_h = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", str(out)],
                         check=True, capture_output=True, text=True).stdout.strip()
    assert w_h == "320,240"


def test_aplica_broll_sound_quiet_and_only_during_the_insert(tmp_path):
    d, curat, m, table = _setup_overlay(tmp_path)
    out = tmp_path / "curat.mp4"
    broll.aplica(curat, table, m, d, out)
    during = _max_volume(out, 6.5, 8.5)
    assert -40.0 < during < -25.0          # a fifth (-14 dB) of the -18 dB test sine
    assert _max_volume(out, 1.0, 5.0) < -80.0


def test_aplica_volume_zero_and_broll_without_sound(tmp_path):
    d, curat, m, table = _setup_overlay(tmp_path, volum=0.0)
    out = tmp_path / "curat.mp4"
    broll.aplica(curat, table, m, d, out)
    assert _max_volume(out, 6.5, 8.5) < -80.0
    d2 = tmp_path / "b2"
    d2.mkdir()
    d2b, curat2, m2, table2 = _setup_overlay(d2, broll_audio=None)
    out2 = d2 / "curat.mp4"
    broll.aplica(curat2, table2, m2, d2b, out2)
    assert _red(_pixel(out2, 7.5))


def test_overlay_graph_fades_crops_and_tonemaps_hdr():
    main = {"width": 1920, "height": 1080, "fps": 30.0, "has_audio": True, "sample_rate": 48000}
    ins = [{"t": 6.0, "src_in": 1.0, "dur": 4.0, "volum": 0.2, "has_audio": True,
            "tonemap": silences.tonemap_filter("arib-std-b67")}]
    graph, maps = broll.build_filtergraph(main, ins)
    assert "force_original_aspect_ratio=increase" in graph and "crop=1920:1080" in graph
    assert "fade=t=in:st=0:d=0.25:alpha=1" in graph
    assert "fade=t=out:st=3.750:d=0.25:alpha=1" in graph
    assert "zscale" in graph
    assert "volume=0.200" in graph
    assert "amix=inputs=2:duration=first:normalize=0" in graph
    assert maps == {"video": "[v0]", "audio": "[a]"}


def test_aplica_warns_when_hdr_broll_cannot_be_converted(tmp_path, monkeypatch):
    d, curat, m, table = _setup_overlay(tmp_path)
    monkeypatch.setattr(broll, "color_transfer", lambda v: "arib-std-b67" if "rosu" in str(v) else "bt709")
    monkeypatch.setattr(broll, "has_filter", lambda name: False)
    res = broll.aplica(curat, table, m, d, tmp_path / "curat.mp4")
    assert silences.HDR_WARNING in res["warnings"]


# --- after the 159f27e checkpoint (D-14 (22))

def test_aplica_warns_about_a_row_that_no_longer_fits(tmp_path):
    d, curat, m, table = _setup_overlay(tmp_path)
    rows = json.loads(table.read_text())["broll"]
    rows.append(_row(3.0, "rosu.mov", dur=3.0, id=2))        # original 3.0 falls in the real cut 2-4
    table.write_text(json.dumps({"broll": rows}))
    res = broll.aplica(curat, table, m, d, tmp_path / "curat.mp4")
    assert res["inserts"] == 1
    assert any("rândul 2" in w and "nu s-a pus" in w for w in res["warnings"])


def test_aplica_with_no_row_left_copies_the_clip_without_broll(tmp_path):
    d, curat, m, table = _setup_overlay(tmp_path)
    table.write_text(json.dumps({"broll": [_row(3.0, "rosu.mov", dur=3.0)]}))
    out = tmp_path / "curat.mp4"
    res = broll.aplica(curat, table, m, d, out)
    assert res["inserts"] == 0
    assert out.read_bytes() == curat.read_bytes()
    assert res["warnings"]


def test_cli_verifica_excludes_the_spoken_clip(tmp_path, capsys):
    d = tmp_path / "dosar"
    d.mkdir()
    video = _clip(d / "vorbit.mp4", 30, audio="sine")
    cuts = tmp_path / "cuts.json"
    cuts.write_text(json.dumps({"cuts": []}))
    table = tmp_path / "broll-propus.json"
    table.write_text(json.dumps({"broll": [_row(6.0, "vorbit.mp4", dur=3.0)]}))
    assert broll.main(["verifica", "--broll", str(table), "--cuts", str(cuts), "--video", str(video),
                       "--dir", str(d), "--exclude", str(video)]) == 2
    assert any("vorbit.mp4" in e for e in json.loads(capsys.readouterr().out)["errors"])

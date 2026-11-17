"""Element 6: SFX on the transitions and push-ins, and a structured music bed (PLAN, Revizia 2 (a) row 6, Nota 2.14).

Speech is a 1 kHz sine, music a 300 Hz sine at full scale; youtube.mp4 is band-passed around each tone and
the RMS is computed on windows in pure Python (no numpy in the venv).
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
import wave

import pytest

import compose

W, H, FPS, RATE = 320, 240, 25, 48000


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _clip(path, dur, speech=None):
    """Grey clip with a 1 kHz 'voice' (amplitude 0.5) inside `speech` = (start, end), silence elsewhere."""
    gate = "between(t,%s,%s)" % speech if speech else "0"
    _ff("-f", "lavfi", "-i", "color=c=0x404040:s=%dx%d:r=%d:d=%s" % (W, H, FPS, dur),
        "-f", "lavfi", "-i", "aevalsrc='0.5*sin(2*PI*1000*t)*%s':s=%d:d=%s" % (gate, RATE, dur),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest", str(path))


def _music(path, dur):
    _ff("-f", "lavfi", "-i", "aevalsrc='sin(2*PI*300*t)':s=%d:d=%s" % (RATE, dur), "-c:a", "pcm_s16le", str(path))


def _render(tmp_path, chapters=(), **spec):
    rd = tmp_path / "render"
    rd.mkdir(exist_ok=True)
    _ff("-f", "lavfi", "-i", "color=c=black:s=%dx%d:r=%d:d=1" % (W, H, FPS), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", str(rd / "intro.mp4"))
    overlays = []
    for i, t in enumerate(chapters, 1):
        name = "chapter_%02d.mov" % i
        _ff("-f", "lavfi", "-i", "color=c=black@0.0:s=%dx%d:r=%d:d=0.4,format=argb" % (W, H, FPS),
            "-c:v", "qtrle", str(rd / name))
        overlays.append({"file": name, "t": t})
    (rd / "render.json").write_text(json.dumps(dict({"intro": "intro.mp4", "overlays": overlays}, **spec)))
    return rd / "render.json"


def _pcm(path, band=None):
    """Mono s16 samples of the programme sound, optionally band-passed twice around `band` Hz."""
    af = "pan=mono|c0=c0"
    if band:
        bp = "bandpass=f=%d:width_type=h:width=60" % band
        af = "%s,%s,%s" % (bp, bp, af)
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-af", af, "-ar", str(RATE),
                        "-f", "s16le", "-"], capture_output=True, check=True)
    return struct.unpack("<%dh" % (len(r.stdout) // 2), r.stdout)


def _db(samples, t0, t1):
    seg = samples[int(t0 * RATE):int(t1 * RATE)]
    assert seg, "fereastra [%s, %s] e in afara fisierului" % (t0, t1)
    rms = math.sqrt(sum(s * s for s in seg) / len(seg)) / 32768
    return 20 * math.log10(max(rms, 1e-9))


# ------------------------------------------------------------------ 1-2. sfx.py and the cue list

def test_sfx_files_are_deterministic_with_expected_length_and_peak(tmp_path):
    import sfx
    a = sfx.generate(tmp_path / "a")
    b = sfx.generate(tmp_path / "b")
    for kind, dur in (("whoosh", 0.35), ("pop", 0.08)):
        assert hashlib.sha256(a[kind].read_bytes()).hexdigest() == hashlib.sha256(b[kind].read_bytes()).hexdigest()
        with wave.open(str(a[kind])) as w:
            assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (RATE, 1, 2)
            n = w.getnframes()
            data = struct.unpack("<%dh" % n, w.readframes(n))
        assert n / RATE == pytest.approx(dur, abs=0.005), kind
        peak = 20 * math.log10(max(abs(x) for x in data) / 32768)
        assert -12 <= peak <= -1, (kind, peak)


def test_sfx_cues_whoosh_on_dissolve_accel_only_and_pop_on_pushin_chapters():
    import montaj
    tr = [{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}, {"t": 8.0, "d": 1.0, "kind": "motion_blur_dissolve"}]
    assert montaj.sfx_cues(tr, [6.0, 0.0], {"scale_end": 1.06}) == [{"kind": "whoosh", "t": 3.0},
                                                                    {"kind": "pop", "t": 6.0}]
    assert montaj.sfx_cues(tr, [6.0], None) == [{"kind": "whoosh", "t": 3.0}]
    assert montaj.sfx_cues([], [], None) == []


# ------------------------------------------------------------------ 3. SFX in youtube.mp4

def test_whoosh_after_dissolve_accel_pop_on_pushin_chapter_nothing_on_motion_blur(tmp_path):
    curat = tmp_path / "curat.mp4"
    _clip(curat, 12)
    rj = _render(tmp_path, chapters=[5.0], sfx=True, pushin={},
                 transitions=[{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"},
                              {"t": 8.0, "d": 1.0, "kind": "motion_blur_dissolve"}])
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rj, out)
    s = _pcm(out)
    # youtube.mp4 time = 1 s intro + clip time - the transitions already passed (map_time):
    # dissolve_accel at clip 3 -> 4.0 s; chapter at clip 5 -> 5.0 s; motion_blur at clip 8 -> 8.0 s
    assert _db(s, 4.0, 4.35) > -45
    assert _db(s, 5.0, 5.08) > -45
    assert _db(s, 8.0, 8.35) < -60
    assert _db(s, 2.0, 3.5) < -60
    assert _db(s, 6.0, 7.5) < -60


def test_vertical_clip_gets_no_whoosh(tmp_path, capsys):
    curat = tmp_path / "curat.mp4"
    _ff("-f", "lavfi", "-i", "color=c=0x404040:s=%dx%d:r=%d:d=8" % (H, W, FPS),
        "-f", "lavfi", "-i", "anullsrc=r=%d:cl=mono" % RATE, "-t", "8", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-c:a", "aac", str(curat))
    rj = _render(tmp_path, sfx=True, transitions=[{"t": 3.0, "d": 1.0, "kind": "dissolve_accel"}])
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rj, out)
    assert "D-30" in capsys.readouterr().err
    assert _db(_pcm(out), 3.5, 4.5) < -60


# ------------------------------------------------------------------ 4-7. music bed

@pytest.fixture(scope="module")
def bed(tmp_path_factory):
    """12 s clip, voice at clip [2, 4.5] s, 4 s of music, no sfx key, and two dissolve_accel (d = 1) given
    unsorted: clip 9 s without drop, clip 6 s with drop. youtube.mp4 timeline: intro 1 s, voice [3, 5.5],
    drop transition at 7.0 s (dip [6.4, 7.0]), plain transition at 9.0 s, fade [9, 11], end at 11 s."""
    tmp = tmp_path_factory.mktemp("el6bed")
    curat = tmp / "curat.mp4"
    _clip(curat, 12, speech=(2, 4.5))
    rd = tmp / "render"
    rd.mkdir()
    _music(rd / "music.wav", 4)
    rj = _render(tmp, music={"file": "music.wav"},
                 transitions=[{"t": 9.0, "d": 1.0, "kind": "dissolve_accel"},
                              {"t": 6.0, "d": 1.0, "kind": "dissolve_accel", "drop": True}])
    out = tmp / "youtube.mp4"
    compose.compose(curat, rj, out)
    return {"out": out, "music": _pcm(out, 300), "hiss": _pcm(out, 1800)}


def test_music_ducks_under_speech(bed):
    m = bed["music"]
    assert _db(m, 3.5, 5.0) <= _db(m, 8.5, 9.0) - 10


def test_music_dips_before_a_drop_transition_only(bed):
    m = bed["music"]
    assert _db(m, 6.45, 6.95) <= -35
    assert _db(m, 8.5, 9.0) > -32              # the 0.6 s before the transition without drop (F5)


def test_music_fades_out_on_the_last_two_seconds(bed):
    m = bed["music"]
    assert compose.probe(bed["out"])["duration"] == pytest.approx(11.0, abs=0.04)
    assert _db(m, 10.7, 10.95) <= _db(m, 8.5, 9.0) - 15


def test_no_sfx_key_no_effects(bed):
    """F4: without sfx the whoosh band stays quiet after both transitions."""
    h = bed["hiss"]
    # measured: -89.9 and silence on the code, -56.8 on both with the effects forced on (mutant g)
    assert _db(h, 7.0, 7.35) < -70
    assert _db(h, 9.0, 9.35) < -70


def test_short_music_is_looped(bed):
    m = bed["music"]
    assert _db(m, 8.5, 9.0) > -32, "muzica de 4 s trebuie sa se auda si dupa 4 s"


# ------------------------------------------------------------------ 8. P1

SRC = {"width": W, "height": H, "fps": 25.0, "duration": 12.0, "has_audio": True, "sample_rate": RATE}
INTRO = {"has_audio": False}


def test_no_sfx_no_music_gives_the_old_graph(capsys):
    old = compose.build_filtergraph(SRC, INTRO, [], 1.0)
    assert compose.build_filtergraph(SRC, INTRO, [], 1.0, {"sfx": False, "music": None}) == old
    assert "sidechaincompress" not in old[0]
    assert capsys.readouterr().err == ""


def test_music_without_file_warns_and_changes_nothing(capsys):
    old = compose.build_filtergraph(SRC, INTRO, [], 1.0)
    assert compose.build_filtergraph(SRC, INTRO, [], 1.0, {"music": {}}) == old
    assert "music lipseste din profil" in capsys.readouterr().err


def test_render_json_music_null_warns_and_gives_no_music(tmp_path, capsys):
    """F2: "music": null is what the agent writes when the profile has no music."""
    curat = tmp_path / "curat.mp4"
    _clip(curat, 4)
    rj = _render(tmp_path, music=None)
    assert compose._load_extras(rj)["music"] == {}
    out = tmp_path / "youtube.mp4"
    compose.compose(curat, rj, out)
    assert "music lipseste din profil" in capsys.readouterr().err
    assert _db(_pcm(out, 300), 1.0, 4.5) < -60

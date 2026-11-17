#!/usr/bin/env python3
"""AirTime compose: put the branded intro in front of the cut clip, lay the
chapter and list overlays on top, and encode the final youtube.mp4.

    compose.py --curat curat.mp4 --render render.json --out youtube.mp4
    compose.py probe FILE

render.json is the JSON printed by render.mjs: {intro, overlays: [{file, t}]}.
Paths in it are relative to the render.json's own folder. Overlay times are
relative to the cut clip; they are shifted by the intro duration here.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

AUDIO_LAYOUT = "stereo"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def _rate(text: str) -> float:
    num, _, den = (text or "0/1").partition("/")
    try:
        d = float(den) if den else 1.0
        return float(num) / d if d else 0.0
    except ValueError:
        return 0.0


def _probe_full(path) -> dict:
    r = _run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    data = json.loads(r.stdout)
    streams = data.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("no video stream in %s" % path)
    width, height = int(video["width"]), int(video["height"])
    rotation = 0
    for sd in video.get("side_data_list") or []:
        if "rotation" in sd:
            rotation = int(round(float(sd["rotation"])))
    rotation = rotation or int(float((video.get("tags") or {}).get("rotate", 0) or 0))
    if rotation % 180 != 0:
        width, height = height, width
    fps = _rate(video.get("avg_frame_rate", "")) or _rate(video.get("r_frame_rate", ""))
    duration = float((data.get("format") or {}).get("duration") or video.get("duration") or 0)
    sample_rate = next((int(s["sample_rate"]) for s in streams
                        if s.get("codec_type") == "audio" and s.get("sample_rate")), 0)
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
        "sample_rate": sample_rate,
    }


def probe(path) -> dict:
    """{width, height, fps, duration, has_audio} of a media file (display size, rotation applied)."""
    info = _probe_full(path)
    info.pop("sample_rate")
    return info


def _fps_text(fps: float) -> str:
    return ("%.3f" % fps).rstrip("0").rstrip(".")


LAYER_MODES = ("normal", "screen", "difference")


TRANSITION_KINDS = ("dissolve_accel", "motion_blur_dissolve")
GRADES = {"cald": "colortemperature=temperature=3800,eq=saturation=1.1,format=yuv420p"}
CHAPTER_FILE = re.compile(r"chapter_\d+\.mov$")     # render.mjs names chapter k chapter_NN.mov (D-36)
SFX_GAIN_DB = -18.0                                   # D-42


def build_filtergraph(src: dict, intro: dict, overlays: list[dict], intro_duration: float, extras: dict | None = None):
    """Filtergraph (string) and output maps. Input 0 = cut clip, 1 = intro, 2.. = overlays,
    then the optional layers, then the optional audio tracks (see _extras_graph).

    Optional extras of element 1 (PLAN, Nota 2.8): transitions [{t, d, kind}] inside the cut clip,
    opening {fade_in, intro_dissolve} between intro and clip, grade "cald" on the clip only.
    Every clip time (overlays, layers, audio) is moved past the transitions with montaj.map_time.
    """
    ex = extras or {}
    w, h, fps = src["width"], src["height"], _fps_text(src["fps"])
    rate = src.get("sample_rate") or 48000
    transitions = check_transitions(ex.get("transitions") or [], src)
    opening = ex.get("opening") or {}
    grade = ex.get("grade")
    if grade is not None and grade not in GRADES:
        raise ValueError("grade necunoscut: %s" % grade)
    dissolve = float(opening.get("intro_dissolve") or 0)
    if dissolve and not (0 < dissolve < min(intro_duration, float(src["duration"]))):
        raise ValueError("intro_dissolve trebuie sa fie mai scurt decat intro-ul si clipul")
    fade_in = float(opening.get("fade_in") or 0)
    pushin = ""
    if ex.get("pushin") is not None:
        import montaj
        starts = [float(o["t"]) for o in overlays if CHAPTER_FILE.match(Path(str(o["file"])).name)]
        pushin = "," + montaj.pushin_filter(montaj.pushin_bounds(starts, float(src["duration"])),
                                            montaj.pushin_scale(ex["pushin"]), w, h, fps)
    parts = [
        "[0:v]fps=%s,setsar=1,format=yuv420p%s%s[sv]" % (fps, "," + GRADES[grade] if grade else "", pushin),
        "[1:v]scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,"
        "fps=%s,setsar=1,format=yuv420p%s[iv]" % (w, h, w, h, fps,
                                                 ",fade=t=in:st=0:d=%.3f" % fade_in if fade_in else ""),
    ]
    fmt = "aformat=sample_fmts=fltp:channel_layouts=%s" % AUDIO_LAYOUT
    if src["has_audio"]:
        parts.append("[0:a]aresample=%d,%s[sa]" % (rate, fmt))
    else:
        parts.append("anullsrc=r=%d:cl=%s,atrim=0:%.3f[sa]" % (rate, AUDIO_LAYOUT, src["duration"]))
    if intro["has_audio"]:
        parts.append("[1:a]aresample=%d,%s,atrim=0:%.3f[ia]" % (rate, fmt, intro_duration))
    else:
        parts.append("anullsrc=r=%d:cl=%s,atrim=0:%.3f[ia]" % (rate, AUDIO_LAYOUT, intro_duration))
    sv, sa = "sv", "sa"
    if transitions:
        sv, sa = _transitions_graph(parts, src, transitions, sv, sa)
    if dissolve:
        import montaj
        parts.append("[iv][%s]xfade=transition=custom:expr='%s':duration=%.3f:offset=%.3f[cv]"
                     % (sv, montaj.accel_expr(), dissolve, intro_duration - dissolve))
        parts.append("[ia][%s]acrossfade=d=%.3f[ca]" % (sa, dissolve))
    else:
        parts.append("[iv][ia][%s][%s]concat=n=2:v=1:a=1[cv][ca]" % (sv, sa))

    def tmap(t: float) -> float:
        if transitions:
            import montaj
            t = montaj.map_time(t, transitions)
        return t + intro_duration - dissolve if dissolve else t + intro_duration

    last = "cv"
    for i, ov in enumerate(overlays):
        k = i + 2
        at = tmap(float(ov["t"]))
        parts.append("[%d:v]scale=%d:%d,format=yuva420p,setpts=PTS-STARTPTS+%.3f/TB[o%d]" % (k, w, h, at, i))
        parts.append("[%s][o%d]overlay=eof_action=pass:format=auto[v%d]" % (last, i, i))
        last = "v%d" % i
    total = intro_duration + float(src["duration"]) - sum(x["d"] for x in transitions) - dissolve
    vlabel, alabel = _extras_graph(parts, src, ex, last, "ca", 2 + len(overlays), intro_duration,
                                   tmap=tmap, total=total)
    return ";".join(parts), {"video": "[%s]" % vlabel, "audio": "[%s]" % alabel}


def check_transitions(transitions: list, src: dict) -> list:
    """Validated transitions, sorted, with t and d rounded to whole frames (PLAN, Nota 2.8)."""
    fps = float(src["fps"]) or 25.0
    out = []
    for x in transitions:
        kind = x.get("kind", "dissolve_accel")
        if kind not in TRANSITION_KINDS:
            raise ValueError("tranzitie necunoscuta: %s" % kind)
        if x.get("b_file"):
            raise ValueError("b_file nu e implementat in 0.2.0 (PLAN, D-27)")
        t = round(float(x["t"]) * fps) / fps
        d = round(float(x["d"]) * fps) / fps
        if d <= 0:
            raise ValueError("durata tranzitiei trebuie sa fie pozitiva: %s" % x)
        out.append({"t": t, "d": d, "kind": kind})
    out.sort(key=lambda x: x["t"])
    dur = float(src["duration"])
    for a, b in zip(out, out[1:] + [None]):
        end = b["t"] if b else dur
        # 1e-6 s: t and d are frame-rounded floats, so a gap exactly at the limit must not fail on rounding (M4)
        if a["t"] < 0.12 - 1e-6 or end - a["t"] < 2.4 * a["d"] + (0.12 if b else 0) - 1e-6:
            raise ValueError("tranzitii prea apropiate de alta tranzitie sau de capat: t=%.3f" % a["t"])
    return out


def _transitions_graph(parts: list, src: dict, transitions: list, sv: str, sa: str) -> tuple:
    """Dissolves inside the cut clip (D-26): A = clip up to t + d, B = clip from t + d; the audio loses
    [t, t + d]. motion_blur_dissolve adds the move and blur on the end of A (D-33, D-34) and a focus
    pull on the start of B."""
    import montaj
    w, h, fpsf = src["width"], src["height"], float(src["fps"])
    fps = _fps_text(fpsf)
    dur = float(src["duration"])
    cuts = [x["t"] + x["d"] for x in transitions]
    bounds = [0.0] + cuts + [dur]
    pieces = []          # (segment index, start, end, effect)
    for k in range(len(bounds) - 1):
        s, e = bounds[k], bounds[k + 1]
        head = tail = None
        if k >= 1 and transitions[k - 1]["kind"] == "motion_blur_dissolve":
            kf = transitions[k - 1]["d"] / montaj.DISSOLVE_MAX
            head = (s, min(e, s + round(1.56 * kf * fpsf) / fpsf), kf)
        if k < len(transitions) and transitions[k]["kind"] == "motion_blur_dissolve":
            tail = (round((transitions[k]["t"] - montaj.MOTION_LEAD) * fpsf) / fpsf, e)
        cur = s
        if head:
            pieces.append((k, head[0], head[1], ("head", head[2])))
            cur = head[1]
        mid_end = tail[0] if tail else e
        if mid_end > cur + 1e-6:
            pieces.append((k, cur, mid_end, None))
        if tail:
            pieces.append((k, tail[0], tail[1], ("tail",)))
    parts.append("[%s]split=%d%s" % (sv, len(pieces), "".join("[tp%d]" % i for i in range(len(pieces)))))
    sig_a, sig_b = 10.0 * h / 1080, 12.0 * h / 1080
    seg_labels = {}
    for i, (k, s, e, fx) in enumerate(pieces):
        base = "[tp%d]trim=start=%.4f:end=%.4f,setpts=PTS-STARTPTS" % (i, s, e)
        if fx is None:
            parts.append(base + "[tq%d]" % i)
        elif fx[0] == "head":
            kf = fx[1]
            sharp = "clip((T-%.4f)/%.4f,0,1)" % (0.44 * kf, 1.12 * kf)
            parts.append(base + ",split[th%da][th%db]" % (i, i))
            parts.append("[th%db]gblur=sigma=%.2f[th%dc]" % (i, sig_b, i))
            parts.append("[th%da][th%dc]blend=all_expr='A*%s+B*(1-%s)'[tq%d]" % (i, i, sharp, sharp, i))
        else:
            p = montaj.progress_expr("on/%s" % fps)
            parts.append(base + ",zoompan=z='1+0.27*%s':x='(iw-iw/zoom)*(0.5+0.5*%s)':y='ih-ih/zoom':d=1:s=%dx%d"
                         ":fps=%s,setpts=PTS-STARTPTS,setsar=1,format=yuv420p,split[tm%da][tm%db]"
                         % (p, p, w, h, fps, i, i))
            parts.append("[tm%db]gblur=sigma=%.2f[tm%dc]" % (i, sig_a, i))
            parts.append("[tm%da][tm%dc]blend=all_expr='A*(1-clip((T-0.08)/0.32,0,1))+B*clip((T-0.08)/0.32,0,1)'"
                         "[tq%d]" % (i, i, i))
        seg_labels.setdefault(k, []).append("[tq%d]" % i)
    # one time base for every segment: blended pieces come out at 1/1000000, plain trims at 1/fps, and
    # xfade refuses a pair that differs (dissolve_accel followed by motion_blur_dissolve, Nota 2.15)
    for k in range(len(bounds) - 1):
        labels = seg_labels[k]
        if len(labels) == 1:
            parts.append("%ssettb=AVTB[ts%d]" % (labels[0], k))
        else:
            parts.append("%sconcat=n=%d:v=1:a=0,settb=AVTB[ts%d]" % ("".join(labels), len(labels), k))
    last, removed = "ts0", 0.0
    for i, x in enumerate(transitions):
        if x["kind"] == "dissolve_accel":
            how = "transition=custom:expr='%s'" % montaj.accel_expr()
        else:
            how = "transition=fade"
        parts.append("[%s][ts%d]xfade=%s:duration=%.4f:offset=%.4f[tx%d]"
                     % (last, i + 1, how, x["d"], x["t"] - removed, i))
        last, removed = "tx%d" % i, removed + x["d"]
    parts.append("[%s]fps=%s[txf]" % (last, fps))      # back to the 1/fps time base of the intro
    last = "txf"
    # audio: keep [0, t1], [c1, t2], ..., [cn, end]
    spans = [(0.0, transitions[0]["t"])]
    for i, x in enumerate(transitions):
        spans.append((cuts[i], transitions[i + 1]["t"] if i + 1 < len(transitions) else dur))
    parts.append("[%s]asplit=%d%s" % (sa, len(spans), "".join("[ta%d]" % i for i in range(len(spans)))))
    for i, (s, e) in enumerate(spans):
        parts.append("[ta%d]atrim=start=%.4f:end=%.4f,asetpts=PTS-STARTPTS[tb%d]" % (i, s, e, i))
    parts.append("%sconcat=n=%d:v=0:a=1[tac]" % ("".join("[tb%d]" % i for i in range(len(spans))), len(spans)))
    return last, "tac"


def _extras_graph(parts: list, src: dict, extras: dict, vlast: str, alast: str, first_input: int,
                  intro_duration: float, tmap=None, total: float | None = None) -> tuple:
    """Second video layer(s) and extra audio track(s); appends to parts, returns the final labels.

    layers: [{file, t, mode}] with mode normal (alpha overlay), screen or difference (RGB blend over a
    black canvas, so black leaves the picture unchanged). audio: [{file, t, gain_db}] delayed and mixed
    under the programme sound. Times are relative to the cut clip, like overlays.
    """
    w, h, fps = src["width"], src["height"], _fps_text(src["fps"])
    rate = src.get("sample_rate") or 48000
    if tmap is None:
        def tmap(t: float) -> float:
            return t + intro_duration
    if total is None:
        total = intro_duration + float(src["duration"])
    k = first_input
    for j, ly in enumerate(extras.get("layers") or []):
        mode = ly.get("mode", "normal")
        if mode not in LAYER_MODES:
            raise ValueError("layer mode necunoscut: %s" % mode)
        at = tmap(float(ly["t"]))
        if mode == "normal":
            parts.append("[%d:v]scale=%d:%d,format=yuva420p,setpts=PTS-STARTPTS+%.3f/TB[l%d]" % (k, w, h, at, j))
            parts.append("[%s][l%d]overlay=eof_action=pass:format=auto[lv%d]" % (vlast, j, j))
        else:
            parts.append("color=c=black:s=%dx%d:r=%s:d=%.3f,format=gbrp[lb%d]" % (w, h, fps, total, j))
            parts.append("[%d:v]scale=%d:%d,fps=%s,format=gbrp,setpts=PTS-STARTPTS+%.3f/TB[l%d]"
                         % (k, w, h, fps, at, j))
            parts.append("[lb%d][l%d]overlay=eof_action=pass:format=gbrp[lc%d]" % (j, j, j))
            parts.append("[%s]format=gbrp[lx%d]" % (vlast, j))
            parts.append("[lx%d][lc%d]blend=all_mode=%s:shortest=1,format=yuv420p[lv%d]" % (j, j, mode, j))
        vlast = "lv%d" % j
        k += 1
    music = extras.get("music")
    if music is not None and not music.get("file"):
        print("Avertisment: music lipseste din profil; pasul muzicii se sare (PLAN, D-43)", file=sys.stderr)
        music = None
    if music is not None:
        # the ducking key is the programme before the SFX ([ca]), so a whoosh never pulls the music down (F3)
        parts.append("[%s]asplit=2[aprog][akey]" % alast)
        alast = "aprog"
    tracks = extras.get("audio") or []
    if tracks:
        fmt = "aformat=sample_fmts=fltp:channel_layouts=%s" % AUDIO_LAYOUT
        labels = []
        for j, tr in enumerate(tracks):
            ms = int(round(max(0.0, tmap(float(tr.get("t", 0)))) * 1000))
            parts.append("[%d:a]aresample=%d,%s,volume=%.1fdB,adelay=%d|%d[ax%d]"
                         % (k, rate, fmt, float(tr.get("gain_db", 0)), ms, ms, j))
            labels.append("[ax%d]" % j)
            k += 1
        parts.append("[%s]%samix=inputs=%d:duration=first:normalize=0[am]" % (alast, "".join(labels), len(labels) + 1))
        alast = "am"
    if music is not None:
        # music bed (D-43): looped input cut to the whole youtube.mp4, gain, ducked under the programme,
        # -14 dB more on the 0.6 s before every transition marked drop (ADUM #7), 2 s fade-out at the end
        fmt = "aformat=sample_fmts=fltp:channel_layouts=%s" % AUDIO_LAYOUT
        fpsf = float(src["fps"]) or 25.0
        drops = sorted(tmap(round(float(x["t"]) * fpsf) / fpsf) for x in extras.get("transitions") or []
                       if x.get("drop"))
        parts.append("[%d:a]aresample=%d,%s,atrim=0:%.3f,asetpts=PTS-STARTPTS,volume=%.1fdB[mu0]"
                     % (k, rate, fmt, total, float(music.get("gain_db", -24))))
        parts.append("[mu0][akey]sidechaincompress=threshold=0.015:ratio=20:attack=5:release=250[mu1]")
        cur = "mu1"
        if drops:
            win = "+".join("between(t,%.3f,%.3f)" % (max(0.0, d - 0.6), d) for d in drops)
            parts.append("[mu1]volume=-14dB:enable='%s'[mu2]" % win)
            cur = "mu2"
        parts.append("[%s]afade=t=out:st=%.3f:d=2[mu3]" % (cur, max(0.0, total - 2)))
        parts.append("[%s][mu3]amix=inputs=2:duration=first:normalize=0[amu]" % alast)
        alast = "amu"
    return vlast, alast


def _load_render(render_json: Path) -> tuple[Path, list[dict]]:
    spec = json.loads(Path(render_json).read_text(encoding="utf-8"))
    base = Path(render_json).resolve().parent

    def resolve(p: str) -> Path:
        q = Path(p)
        return q if q.is_absolute() else base / q

    overlays = [{"file": resolve(o["file"]), "t": float(o["t"])} for o in spec.get("overlays") or []]
    return resolve(spec["intro"]), sorted(overlays, key=lambda o: o["t"])


def _load_extras(render_json: Path) -> dict:
    """Optional keys of render.json added by the montage upgrade, with file paths resolved."""
    spec = json.loads(Path(render_json).read_text(encoding="utf-8"))
    base = Path(render_json).resolve().parent

    def resolve(p: str) -> Path:
        q = Path(p)
        return q if q.is_absolute() else base / q

    layers = [dict(x, file=resolve(x["file"])) for x in spec.get("layers") or []]
    audio = [dict(x, file=resolve(x["file"])) for x in spec.get("audio") or []]
    # music: a missing key is None (old render.json, silent); null or {} means the profile has no music (F2)
    music = None
    if "music" in spec:
        music = dict(spec["music"] or {})
        if music.get("file"):
            music["file"] = resolve(music["file"])
    return {"layers": layers, "audio": audio, "loudnorm": bool(spec.get("loudnorm")),
            "transitions": list(spec.get("transitions") or []), "opening": dict(spec.get("opening") or {}),
            "grade": spec.get("grade"), "pushin": spec.get("pushin"), "sfx": bool(spec.get("sfx")),
            "music": music}


# -14 LUFS like claude-shorts export.sh for the reels; the true peak target sits 0.5 dB under the -1 dBTP
# ceiling because the AAC re-encode after loudnorm can push peaks up a little (D-24).
LOUDNORM = "I=-14:TP=-1.5:LRA=11"


def loudnorm_filter(measured: dict) -> str:
    """Second-pass loudnorm with the first-pass measurements; back to 48 kHz (loudnorm works at 192 kHz)."""
    return ("loudnorm=%s:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
            "aresample=48000" % (LOUDNORM, measured["input_i"], measured["input_tp"], measured["input_lra"],
                                 measured["input_thresh"], measured["target_offset"]))


def normalize_loudness(path: Path) -> bool:
    """Two-pass loudnorm on the audio of an encoded file, video copied. False when the audio is silent."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
                        "-af", "loudnorm=%s:print_format=json" % LOUDNORM, "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    measured = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    try:
        if float(measured["input_i"]) < -70:
            return False
    except ValueError:  # "-inf" for pure digital silence
        return False
    tmp = path.with_name(path.stem + ".loudnorm" + path.suffix)
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-map", "0:v:0", "-map", "0:a:0",
          "-c:v", "copy", "-af", loudnorm_filter(measured), "-c:a", "aac", "-b:a", "192k",
          "-movflags", "+faststart", str(tmp)])
    tmp.replace(path)
    return True


def compose(curat, render_json, out) -> Path:
    curat, out = Path(curat), Path(out)
    intro_path, overlays = _load_render(Path(render_json))
    extras = _load_extras(Path(render_json))
    src = _probe_full(curat)
    intro = _probe_full(intro_path)
    if extras["transitions"] and src["height"] > src["width"]:
        print("Avertisment: tranzitiile se sar pe clipul vertical (PLAN, D-30)", file=sys.stderr)
        extras["transitions"] = []
    if extras["sfx"]:
        # after the vertical check, so a vertical clip gets no whoosh (F8); the effects go in as audio tracks
        import montaj
        import sfx
        files = sfx.generate(Path(render_json).resolve().parent)
        chapters = [o["t"] for o in overlays if CHAPTER_FILE.match(Path(str(o["file"])).name)]
        for cue in montaj.sfx_cues(check_transitions(extras["transitions"], src), chapters, extras["pushin"]):
            extras["audio"].append({"file": files[cue["kind"]], "t": cue["t"], "gain_db": SFX_GAIN_DB})
    graph, maps = build_filtergraph(src, intro, overlays, intro["duration"], extras=extras)
    # Frame colour properties win over the encoder flags below, so set them in the graph too.
    graph += ";%ssetparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709[vout]" % maps["video"]
    maps = dict(maps, video="[vout]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(curat), "-i", str(intro_path)]
    for ov in overlays:
        cmd += ["-i", str(ov["file"])]
    for extra in extras["layers"] + extras["audio"]:
        cmd += ["-i", str(extra["file"])]
    if extras.get("music") and extras["music"].get("file"):
        cmd += ["-stream_loop", "-1", "-i", str(extras["music"]["file"])]
    cmd += ["-filter_complex", graph, "-map", maps["video"], "-map", maps["audio"],
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            # youtube.mp4 is SDR: tag it bt709 explicitly, or ffmpeg copies a tag from one of the
            # inputs (an HLG curat.mp4 left untouched without zscale ended up as iec61966-2-1).
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run(cmd)
        if extras["loudnorm"]:
            normalize_loudness(out)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("ffmpeg a esuat:\n%s" % (e.stderr or "")[-1500:]) from e
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "probe":
        ap = argparse.ArgumentParser(prog="compose.py probe")
        ap.add_argument("file")
        a = ap.parse_args(argv[1:])
        print(json.dumps(probe(a.file), ensure_ascii=False))
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curat", required=True)
    ap.add_argument("--render", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        compose(a.curat, a.render, a.out)
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        print("Eroare: %s" % e, file=sys.stderr)
        return 1
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

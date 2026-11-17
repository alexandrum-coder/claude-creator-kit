#!/usr/bin/env python3
"""AirTime layer around claude-shorts for the reels (PLAN, D-16): effects applied to AirTime's own files,
never inside the claude-shorts scripts.

Element 2, push-in (PLAN, Nota 2.12, D-39): a segment of reels-aprobate.json with `pushin: {scale_end}`
gets its clip_NN.mp4 zoomed from 1 to scale_end over the whole clip, centred, before the claude-shorts
render, so the captions laid on top are not enlarged. Size and rate stay the same, so reframe.json holds.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

import montaj

LIST_MAX = 4                        # 4 rows end at 66% of the height, above the captions (H4)
LIST_COLORS = {"primary": "#14213d", "accent": "#fca311"}


def probe(path, run, step="pushin_probe") -> dict:
    """Width, height, rate (ffprobe text, e.g. '25/1') and duration of a clip; run = reels.run_step."""
    out = run(step, ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                     "stream=width,height,r_frame_rate:format=duration", "-of", "json", path])
    data = json.loads(out)
    st = data["streams"][0]
    return {"width": int(st["width"]), "height": int(st["height"]), "fps": st["r_frame_rate"],
            "duration": float(data["format"]["duration"])}


def pushin_args(src, out, scale_end: float, info: dict) -> list:
    """ffmpeg command for the push-in of one clip; the audio is copied untouched."""
    vf = montaj.pushin_filter([(0.0, info["duration"])], scale_end, info["width"], info["height"], info["fps"])
    return ["ffmpeg", "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-c:a", "copy", out]


# ---------------------------------------------------------------- element 3: numbered list on words

def normalize(word: str) -> str:
    """Lower case, no diacritics (s with comma or cedilla both become s), no punctuation at the ends (D-47)."""
    w = unicodedata.normalize("NFD", str(word).lower())
    w = "".join(ch for ch in w if unicodedata.category(ch) != "Mn")
    return re.sub(r"^\W+|\W+$", "", w)


def check_list(items) -> list:
    """1-4 items, each {text, cue} with non-empty strings (H4); ValueError otherwise."""
    if not isinstance(items, list) or not 1 <= len(items) <= LIST_MAX:
        raise ValueError("list trebuie sa aiba intre 1 si %d itemi" % LIST_MAX)
    for it in items:
        if not isinstance(it, dict) or not all(isinstance(it.get(k), str) and it[k].strip() for k in ("text", "cue")):
            raise ValueError("fiecare item din list are nevoie de text si cue: %r" % (it,))
    return items


def match_cues(items, words, seg_start: float, seg_end: float, fps: float, warnings: list, seg_id):
    """Reel times (frame-rounded) at which each item appears: the cue word(s) searched among the words of
    [seg_start, seg_end), each after the previous match. A missing cue gets the previous time + 1 s and a
    warning; a segment without words gets None and a warning (H4)."""
    inside = sorted((w for w in words if seg_start - 1e-6 <= float(w["start"]) < seg_end),
                    key=lambda w: float(w["start"]))
    if not inside:
        warnings.append("Segmentul %s nu are vorbire; lista numerotata se sare." % seg_id)
        return None
    toks = [normalize(w["word"]) for w in inside]
    times, pos, prev = [], 0, 0.0
    for it in items:
        cue = [normalize(c) for c in it["cue"].split() if normalize(c)]
        hit = next((i for i in range(pos, len(toks) - len(cue) + 1) if toks[i:i + len(cue)] == cue), None)
        if hit is None:
            warnings.append("Cuvantul «%s» nu e in segmentul %s; itemul apare la 1 s dupa cel precedent."
                            % (it["cue"], seg_id))
            t = prev + 1.0
        else:
            t = float(inside[hit]["start"]) - seg_start
            pos = hit + len(cue)
        t = round(t * fps) / fps
        times.append(t)
        prev = t
    return times


def list_props(items, times, width: int, height: int, fps, reel_duration: float) -> tuple:
    """NumberedList props and the reel time t0 where the overlay starts (the first item); it lasts to the end."""
    t0 = min(times)
    props = {"width": width, "height": height, "fps": fps, "colors": dict(LIST_COLORS),
             "items": [{"text": it["text"], "at": round(t - t0, 4)} for it, t in zip(items, times)],
             "duration": round(reel_duration - t0, 4)}
    return props, t0


def list_render_args(props_path, out) -> list:
    """node command run with cwd = the AirTime remotion folder (D-46)."""
    return ["node", "overlay.mjs", "--id", "NumberedList", "--props", props_path, "--out", out]


def overlay_args(short, mov, t0: float, out) -> list:
    """ffmpeg command laying the alpha overlay on the reel from t0; the audio is copied."""
    fc = "[1:v]setpts=PTS-STARTPTS+%.3f/TB[o];[0:v][o]overlay=eof_action=pass:format=auto[v]" % t0
    return ["ffmpeg", "-y", "-i", short, "-i", mov, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", out]


def _rate(info: dict) -> float:
    num, den = (info["fps"].split("/") + ["1"])[:2]
    return float(num) / float(den)


def apply_list(seg: dict, seg_id, short, words, work, run, warnings: list, remotion_dir, cta=None) -> bool:
    """Lay the numbered list of one segment over its short_NN.mp4, in place. False when it is skipped.
    With `cta` (the segment's cta, when a CTA will be laid too) the list gives way at from_s (D-53, D-57)."""
    items = check_list(seg["list"])
    info = probe(short, run, step="list_probe")
    rate = _rate(info)
    times = match_cues(items, words, float(seg["start"]), float(seg["end"]), rate, warnings, seg_id)
    if times is None:
        return False
    end = info["duration"]
    if cta is not None:
        end = cta_window(cta, info["duration"], rate)
        items, times = cut_list(items, times, end, rate, warnings, seg_id)
        if not items:
            warnings.append("Segmentul %s: niciun item nu apare inainte de CTA; lista se sare." % seg_id)
            return False
    props, t0 = list_props(items, times, info["width"], info["height"], round(rate, 3), end)
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    pf = work / ("list_%02d.json" % int(seg_id))
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    mov = work / ("list_%02d.mov" % int(seg_id))
    run("list_render", list_render_args(pf, mov), cwd=remotion_dir)
    tmp = work / ("short_%02d.list.mp4" % int(seg_id))
    run("list_overlay", overlay_args(short, mov, t0, tmp))
    os.replace(tmp, short)
    return True


# ---------------------------------------------------------------- element 4: CTA keyword held to the end

CTA_DEFAULT_S = 3.0                 # the CTA covers the last 3 s unless from_s says otherwise (D-51)
CTA_WORD_MAX = 30                   # the font shrinks to keep 30 characters on one line (D-56)
LIST_FADE_FRAMES = 10               # NumberedList fades out over its last 10 frames (H3)


class CtaError(ValueError):
    """A bad `cta` field; reels.build turns it into StepError("cta")."""


def check_cta_word(word) -> str:
    if not isinstance(word, str) or not word.strip() or len(word.strip()) > CTA_WORD_MAX:
        raise CtaError("cuvantul CTA trebuie sa fie un sir de 1-%d caractere: %r" % (CTA_WORD_MAX, word))
    return word.strip()


def resolve_cta_word(cta, cta_word, warnings: list, seg_id):
    """The segment's word first, then --cta-word (the first profile keyword, given by the agent); an empty
    --cta-word counts as absent (J2). None, with a warning, when there is no word: the CTA is skipped."""
    if not isinstance(cta, dict):
        raise CtaError("cta trebuie sa fie un obiect {word, from_s}: %r" % (cta,))
    if cta.get("word") is not None:
        return check_cta_word(cta["word"])
    if isinstance(cta_word, str) and cta_word.strip():
        return check_cta_word(cta_word)
    warnings.append("Segmentul %s are cta fara cuvant si nu s-a dat --cta-word; CTA-ul se sare." % seg_id)
    return None


def cta_window(cta, duration: float, fps: float) -> float:
    """Reel time (on a frame) at which the CTA appears: from_s, or the last 3 s (the whole reel if shorter)."""
    if not isinstance(cta, dict):
        raise CtaError("cta trebuie sa fie un obiect {word, from_s}: %r" % (cta,))
    fs = cta.get("from_s")
    if fs is None:
        fs = max(0.0, duration - CTA_DEFAULT_S)
    elif isinstance(fs, bool) or not isinstance(fs, (int, float)):
        raise CtaError("cta.from_s trebuie sa fie un numar de secunde: %r" % (fs,))
    fs = round(fs * fps) / fps
    if fs < 0 or fs > duration - 1.0 / fps + 1e-6:
        raise CtaError("cta.from_s = %s e in afara reel-ului de %.2f s" % (cta.get("from_s"), duration))
    return fs


def cut_list(items, times, end: float, fps: float, warnings: list, seg_id) -> tuple:
    """Keep the list items that appear before the list's 10-frame fade-out ending at `end` (D-57)."""
    limit = end - LIST_FADE_FRAMES / fps
    kept, kept_t = [], []
    for it, t in zip(items, times):
        if t < limit - 1e-6:
            kept.append(it)
            kept_t.append(t)
        else:
            warnings.append("Itemul «%s» din segmentul %s ar aparea dupa CTA; nu se afiseaza." % (it["text"], seg_id))
    return kept, kept_t


def cta_props(word: str, width: int, height: int, fps, duration: float, from_s: float) -> dict:
    return {"width": width, "height": height, "fps": fps, "colors": dict(LIST_COLORS), "word": word,
            "duration": round(duration - from_s, 4)}


def cta_render_args(props_path, out) -> list:
    return ["node", "overlay.mjs", "--id", "CtaKeyword", "--props", props_path, "--out", out]


def apply_cta(seg: dict, seg_id, short, word: str, work, run, remotion_dir) -> None:
    """Lay the CTA keyword over short_NN.mp4 from from_s to the last frame, in place (D-54)."""
    info = probe(short, run, step="cta_probe")
    rate = _rate(info)
    from_s = cta_window(seg["cta"], info["duration"], rate)
    props = cta_props(word, info["width"], info["height"], round(rate, 3), info["duration"], from_s)
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    pf = work / ("cta_%02d.json" % int(seg_id))
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    mov = work / ("cta_%02d.mov" % int(seg_id))
    run("cta_render", cta_render_args(pf, mov), cwd=remotion_dir)
    tmp = work / ("short_%02d.cta.mp4" % int(seg_id))
    run("cta_overlay", overlay_args(short, mov, from_s, tmp))
    os.replace(tmp, short)


# ---------------------------------------------------------------- element 5: impact caption, difference blend
IMPACT_MAX_ITEMS = 8
IMPACT_TEXT_MAX = 30


class ImpactError(ValueError):
    """A bad `impact` field; reels.build turns it into StepError("impact")."""


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_impact(impact, duration: float, fps: float) -> list:
    """impact: [{text, t, d}] in reel seconds, in order, not overlapping, inside the reel (D-60).
    Returns the items with text stripped and t, d on frames."""
    if not isinstance(impact, list) or not 1 <= len(impact) <= IMPACT_MAX_ITEMS:
        raise ImpactError("impact trebuie sa fie o lista de 1-%d itemi: %r" % (IMPACT_MAX_ITEMS, impact))
    out, prev_end = [], 0.0
    for it in impact:
        if not isinstance(it, dict):
            raise ImpactError("itemul de impact trebuie sa fie un obiect {text, t, d}: %r" % (it,))
        text = it.get("text")
        if not isinstance(text, str) or not text.strip() or len(text.strip()) > IMPACT_TEXT_MAX:
            raise ImpactError("textul de impact trebuie sa aiba 1-%d caractere: %r" % (IMPACT_TEXT_MAX, text))
        t, d = it.get("t"), it.get("d")
        if not _num(t) or not _num(d):
            raise ImpactError("t si d trebuie sa fie numere de secunde: %r" % (it,))
        t, d = round(t * fps) / fps, round(d * fps) / fps
        if t < 0 or d < 1.0 / fps - 1e-9:
            raise ImpactError("t >= 0 si d de cel putin un cadru: %r" % (it,))
        if t + d > duration + 1e-6:
            raise ImpactError("«%s» se termina dupa reel-ul de %.2f s" % (text.strip(), duration))
        if t < prev_end - 1e-6:
            raise ImpactError("«%s» incepe inainte sa se termine itemul anterior" % text.strip())
        prev_end = t + d
        out.append({"text": text.strip(), "t": t, "d": d})
    return out


def shift_impact(items, delta: float, duration: float, warnings: list, seg_id):
    """impact t is counted from the approved start, but snap_boundaries may move the start: move every t by
    delta = approved start - snapped start, so the text stays on its word; drop the items the snap cut off (D-86).
    With delta 0 or a malformed field the items come back unchanged, for check_impact to report."""
    if not delta or not isinstance(items, list) or not items:
        return items
    if not all(isinstance(it, dict) and _num(it.get("t")) and _num(it.get("d")) for it in items):
        return items
    out = []
    for it in items:
        t = round(float(it["t"]) + delta, 3)
        if t < 0 or t + float(it["d"]) > duration:
            warnings.append("Reel %s: textul de impact %r a ieșit din reel după potrivirea pe fraze; "
                            "l-am scos." % (seg_id, it.get("text")))
            continue
        out.append(dict(it, t=t))
    return out


def impact_props(items, width: int, height: int, fps) -> tuple:
    """Props of ImpactCaption covering only [first t, last t + d]; item times in frames from that start."""
    t0 = items[0]["t"]
    end = items[-1]["t"] + items[-1]["d"]
    its = [{"text": i["text"], "from": int(round((i["t"] - t0) * fps)), "dur": int(round(i["d"] * fps))}
           for i in items]
    return {"width": width, "height": height, "fps": fps, "items": its, "duration": round(end - t0, 4)}, t0


def impact_render_args(props_path, out) -> list:
    return ["node", "overlay.mjs", "--id", "ImpactCaption", "--props", props_path, "--out", out]


def impact_args(short, mov, t0: float, info: dict, out) -> list:
    """ffmpeg command: the white-on-black mask laid on black from t0, then an RGB difference blend over the reel
    (D-61). accurate_rnd keeps the yuv -> gbrp -> yuv round trip exact; t0 is floored so it is never late (P1)."""
    t0 = int(t0 * 1e6) / 1e6
    fc = ("sws_flags=accurate_rnd+full_chroma_int;"
          "color=c=black:s=%dx%d:r=%s:d=%.3f,format=gbrp[ib];"
          "[1:v]format=gbrp,setpts=PTS-STARTPTS+%.6f/TB[im];"
          "[ib][im]overlay=eof_action=pass:format=gbrp[ik];"
          "[0:v]format=gbrp[is];"
          "[is][ik]blend=all_mode=difference:shortest=1,format=yuv420p[v]") % (
        info["width"], info["height"], info["fps"], info["duration"] + 1, t0)
    return ["ffmpeg", "-y", "-i", short, "-i", mov, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", out]


def apply_impact(seg: dict, seg_id, short, work, run, remotion_dir) -> None:
    """Blend the impact captions of one segment into short_NN.mp4, in place (D-63)."""
    info = probe(short, run, step="impact_probe")
    rate = _rate(info)
    items = check_impact(seg["impact"], info["duration"], rate)
    props, t0 = impact_props(items, info["width"], info["height"], round(rate, 3))
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    pf = work / ("impact_%02d.json" % int(seg_id))
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    mov = work / ("impact_%02d.mov" % int(seg_id))
    run("impact_render", impact_render_args(pf, mov), cwd=remotion_dir)
    tmp = work / ("short_%02d.impact.mp4" % int(seg_id))
    run("impact_blend", impact_args(short, mov, t0, info, tmp))
    os.replace(tmp, short)


# ---------------------------------------------------------------- element 7: result hook in a loop
class HookError(ValueError):
    """A bad `result_hook` field or a reel it cannot loop; reels.build turns it into StepError("result_hook")."""


def hook_probe(path, run) -> dict:
    """Width, height, rate, frame count of the video stream (packets, not the container duration, which a longer
    audio stretches) and whether there is an audio stream (Note 2.22.1, Q1)."""
    out = run("hook_probe", ["ffprobe", "-v", "error", "-count_packets", "-show_entries",
                             "stream=codec_type,width,height,r_frame_rate,nb_read_packets", "-of", "json", path])
    streams = json.loads(out)["streams"]
    v = next(s for s in streams if s.get("codec_type") == "video")
    return {"width": int(v["width"]), "height": int(v["height"]), "fps": v["r_frame_rate"],
            "frames": int(v["nb_read_packets"]), "audio": any(s.get("codec_type") == "audio" for s in streams)}


def check_hook(hook, frames: int, fps: float) -> int:
    """result_hook: {d} in seconds -> k frames, 1 <= k <= frames - 1 (D-66)."""
    if not isinstance(hook, dict) or not _num(hook.get("d")):
        raise HookError("result_hook trebuie sa fie un obiect {d} cu d in secunde: %r" % (hook,))
    k = int(round(hook["d"] * fps))
    if not 1 <= k <= frames - 1:
        raise HookError("result_hook d = %r inseamna %d cadre; trebuie intre 1 si %d (reel-ul are %d)" % (
            hook["d"], k, frames - 1, frames))
    return k


def hook_args(short, out, info: dict, k: int) -> list:
    """ffmpeg command: the last k frames, then the whole reel, video cut on frames; 10 ms audio fades at the
    junction so it does not click (D-68, Q1)."""
    num, den = (info["fps"].split("/") + ["1"])[:2]
    n = info["frames"]
    s, hd, end = (n - k) * float(den) / float(num), k * float(den) / float(num), n * float(den) / float(num)
    fc = ("[0:v]split[v1][v2];[0:a]asplit[a1][a2];"
          "[v1]trim=start_frame=%d,setpts=PTS-STARTPTS[hv];"
          "[a1]atrim=start=%.6f:end=%.6f,asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st=%.6f:d=0.01[ha];"
          "[v2]setpts=PTS-STARTPTS[mv];"
          "[a2]atrim=end=%.6f,asetpts=PTS-STARTPTS,afade=t=in:d=0.01[ma];"
          "[hv][ha][mv][ma]concat=n=2:v=1:a=1[v][a]") % (n - k, s, end, hd - 0.01, end)
    return ["ffmpeg", "-y", "-i", short, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", out]


def apply_hook(seg: dict, seg_id, short, work, run) -> None:
    """Put the last d seconds of short_NN.mp4 in front of it too, in place (D-70)."""
    info = hook_probe(short, run)
    if not info["audio"]:
        raise HookError("reel-ul nu are sunet; bucla cere audio (D-69)")
    k = check_hook(seg["result_hook"], info["frames"], _rate(info))
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    tmp = work / ("short_%02d.hook.mp4" % int(seg_id))
    run("hook_concat", hook_args(short, tmp, info, k))
    os.replace(tmp, short)

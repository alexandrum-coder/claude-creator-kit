#!/usr/bin/env python3
"""AirTime montaj: where the ADUM-style transitions go and the curves they follow.

    montaj.py slots --transcript transcript-curat.json [--min-gap 1.1]

Prints the transition slots found in the speech pauses of the cut clip as JSON:
[{t, d, gap}], t and d in seconds on the cut-clip timeline (curat.mp4).

The numbers come from the study of ADUM_6-q5Ks (catalog-tehnici.md, sections 3 and 4):
- a slot is a speech pause of at least min_gap seconds; the dissolve starts 0.2 s after the last word;
- B (the clip after the dissolve) starts at t + d and the audio loses [t, t + d], so the window
  [t, t + 2d] must stay inside the pause: d = min(1.16, (gap - 0.22) / 2); slots with d < 0.4 are skipped;
- dissolve_accel: the weight of B grows at speed v up to 0.55, then at 2v (1.24 s in the reference);
- motion_blur_dissolve: the move on A follows keyframes at 0, 2, 9, 10 frames of 25 fps -> 0, 0.13, 0.97, 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISSOLVE_MAX = 1.16
DISSOLVE_MIN = 0.4
START_AFTER_WORD = 0.2
PAUSE_MARGIN = 0.22
ACCEL_KNEE = 0.55 / 0.775          # q where the speed doubles (0.7097)
MOTION_KEYS = ((0.0, 0.0), (0.08, 0.13), (0.36, 0.97), (0.40, 1.0))   # seconds -> progress
MOTION_LEAD = 0.12                 # the move on A starts 3 frames (25 fps) before the dissolve


def find_slots(transcript: dict, min_gap: float = 1.1) -> list:
    words = sorted((w for s in transcript.get("segments") or [] for w in s.get("words") or []),
                   key=lambda w: float(w["start"]))
    slots = []
    for prev, nxt in zip(words, words[1:]):
        gap = round(float(nxt["start"]) - float(prev["end"]), 3)
        if gap + 1e-9 < min_gap:
            continue
        d = round(min(DISSOLVE_MAX, (gap - PAUSE_MARGIN) / 2), 3)
        if d < DISSOLVE_MIN:
            continue
        slots.append({"t": round(float(prev["end"]) + START_AFTER_WORD, 3), "d": d, "gap": gap})
    return slots


def accel_weight(q: float) -> float:
    """Weight of B at relative time q (0...1) in dissolve_accel (D-32)."""
    q = min(1.0, max(0.0, q))
    if q < ACCEL_KNEE:
        return 0.775 * q
    return min(1.0, 0.55 + 1.55 * (q - ACCEL_KNEE))


def accel_expr() -> str:
    """xfade custom expression for accel_weight; xfade's P runs from 1 down to 0, so q = 1 - P."""
    w = "if(lt(1-P,%.4f),0.775*(1-P),min(1,0.55+1.55*((1-P)-%.4f)))" % (ACCEL_KNEE, ACCEL_KNEE)
    return "A*(1-(%s))+B*(%s)" % (w, w)


def motion_progress(sec: float) -> float:
    """Progress of the move on A, sec seconds after it starts."""
    if sec <= 0:
        return 0.0
    for (s0, p0), (s1, p1) in zip(MOTION_KEYS, MOTION_KEYS[1:]):
        if sec < s1:
            return p0 + (p1 - p0) * (sec - s0) / (s1 - s0)
    return 1.0


def progress_expr(var: str) -> str:
    """ffmpeg expression of motion_progress for a time variable in seconds (e.g. 'on/25')."""
    parts = []
    for (s0, p0), (s1, p1) in zip(MOTION_KEYS, MOTION_KEYS[1:]):
        parts.append((s1, "%.4f+%.4f*((%s)-%.2f)" % (p0, (p1 - p0) / (s1 - s0), var, s0)))
    expr = "1"
    for s1, piece in reversed(parts):
        expr = "if(lt(%s,%.2f),%s,%s)" % (var, s1, piece, expr)
    return "max(0,%s)" % expr


def map_time(t: float, transitions: list) -> float:
    """A cut-clip time moved onto the clip after the transitions (D-31): every transition that ends
    before t (t_j + d_j <= t) removes d_j seconds."""
    removed = sum(float(x["d"]) for x in transitions if float(x["t"]) + float(x["d"]) <= t + 1e-9)
    return t - removed


PUSHIN_DEFAULT = 1.06
PUSHIN_MAX = 1.4                   # catalog section 2: push-ins of 10-40% over the shot


def pushin_scale(cfg) -> float:
    """Final scale of a push-in config {scale_end: S}, 1 < S <= 1.4; a missing scale_end gives 1.06 (D-37)."""
    if not isinstance(cfg, dict):
        raise ValueError("pushin trebuie sa fie un obiect {scale_end: ...}: %r" % (cfg,))
    s = cfg.get("scale_end", PUSHIN_DEFAULT)
    if isinstance(s, bool) or not isinstance(s, (int, float)) or not 1.0 < s <= PUSHIN_MAX:
        raise ValueError("pushin.scale_end trebuie sa fie intre 1.0 (exclusiv) si %.1f: %r" % (PUSHIN_MAX, s))
    return float(s)


def pushin_bounds(starts, duration: float) -> list:
    """Segments [(s, e)] covering [0, duration], cut at every start strictly inside it (D-36)."""
    cuts = sorted({round(float(t), 6) for t in starts if 0 < float(t) < duration})
    b = [0.0] + cuts + [float(duration)]
    return list(zip(b, b[1:]))


def pushin_expr(bounds: list, scale_end: float, var: str) -> str:
    """Zoom that grows linearly from 1 to scale_end on each segment and restarts at 1 on the next."""
    def seg(s, e):
        return "1+%.6f*((%s)-%.6f)/%.6f" % (scale_end - 1, var, s, e - s)
    expr = seg(*bounds[-1])
    for s, e in reversed(bounds[:-1]):
        expr = "if(lt(%s,%.6f),%s,%s)" % (var, e, seg(s, e), expr)
    return expr


def sfx_cues(transitions: list, chapter_starts, pushin) -> list:
    """Where the sound effects go, in cut-clip seconds (PLAN, D-42): a whoosh at the start of every
    dissolve_accel (never on motion_blur_dissolve, catalog section 3) and, with a push-in, a pop at every
    chapter start after 0."""
    cues = [{"kind": "whoosh", "t": float(x["t"])} for x in transitions if x.get("kind") == "dissolve_accel"]
    if pushin is not None:
        cues += [{"kind": "pop", "t": float(t)} for t in sorted(set(chapter_starts)) if float(t) > 0]
    return sorted(cues, key=lambda c: c["t"])


def pushin_filter(bounds: list, scale_end: float, w: int, h: int, fps: str) -> str:
    """zoompan chain for pushin_expr, centred, same size and rate. zoompan crops on whole pixels and, on
    yuv420p, on even ones: the centre then drifts by up to 2 px; on yuv444p with rounded x, y it stays
    within 0.5 px (measured, Nota 2.13)."""
    z = pushin_expr(bounds, scale_end, "on/(%s)" % fps)
    return ("format=yuv444p,zoompan=z='%s':x='round((iw-iw/zoom)/2)':y='round((ih-ih/zoom)/2)'"
            ":d=1:s=%dx%d:fps=%s,setsar=1,format=yuv420p" % (z, w, h, fps))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sl = sub.add_parser("slots")
    sl.add_argument("--transcript", required=True)
    sl.add_argument("--min-gap", type=float, default=1.1)
    a = ap.parse_args(argv)
    try:
        transcript = json.loads(Path(a.transcript).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("Eroare: %s" % e, file=sys.stderr)
        return 1
    print(json.dumps(find_slots(transcript, a.min_gap), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

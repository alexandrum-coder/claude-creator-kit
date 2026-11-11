"""Convert a rolling auto-caption VTT into deduplicated text blocks with timestamps."""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
block_seconds = int(sys.argv[3]) if len(sys.argv) > 3 else 60

time_re = re.compile(r"(\d+):(\d\d):(\d\d)\.\d+ -->")
tag_re = re.compile(r"<[^>]+>")

segments = []
current = None
for raw in open(src, encoding="utf-8"):
    line = raw.strip()
    match = time_re.match(line)
    if match:
        h, m, s = map(int, match.groups())
        current = h * 3600 + m * 60 + s
        continue
    if not line or current is None or line.startswith(("WEBVTT", "Kind:", "Language:")):
        continue
    text = tag_re.sub("", line).strip()
    if text and (not segments or segments[-1][1] != text):
        segments.append((current, text))

# Rolling captions repeat the previous line, so keep only unseen recent lines.
recent = []
kept = []
for start, text in segments:
    if text in recent:
        continue
    recent = (recent + [text])[-6:]
    kept.append((start, text))

blocks = {}
for start, text in kept:
    blocks.setdefault(start // block_seconds, []).append(text)

with open(dst, "w", encoding="utf-8") as out:
    for key in sorted(blocks):
        total = key * block_seconds
        stamp = f"{total // 3600:d}:{total % 3600 // 60:02d}:{total % 60:02d}"
        out.write(f"[{stamp}] {' '.join(blocks[key])}\n\n")

print(f"segments={len(kept)} blocks={len(blocks)} words={sum(len(t.split()) for _, t in kept)}")

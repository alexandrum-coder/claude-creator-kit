#!/usr/bin/env python3
"""YouTube pentru AirTime: texte, validare, programare și urcare (CLI, JSON pe stdout).

Coduri de ieșire: 0 ok, 2 date invalide, 3 neconectat, 4 fără fișier client, 5 duplicat.
Bibliotecile Google se importă doar în funcțiile de rețea.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import airtime_config as cfg

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
CHUNK = 8 * 1024 * 1024
MIN_AHEAD = timedelta(minutes=15)


# ---------------------------------------------------------------- funcții pure

def parse_publish_at(local: str, tz: str, now: datetime | None = None) -> str:
    """'AAAA-LL-ZZ HH:MM' în ora din `tz` -> RFC3339 UTC cu Z."""
    naive = datetime.strptime(local.strip(), "%Y-%m-%d %H:%M")
    when = naive.replace(tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)
    now = now or datetime.now(timezone.utc)
    if when - now < MIN_AHEAD:
        raise ValueError("ora de publicare e în trecut sau la mai puțin de 15 minute de acum")
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_meta(meta: dict, duration: float, short: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    title = meta.get("title") or ""
    desc = meta.get("description") or ""
    tags = meta.get("tags") or []
    if not title.strip():
        errors.append("titlul e gol")
    elif len(title) > 100:
        errors.append("titlul are %d caractere, maximum 100" % len(title))
    elif len(title) > 70:
        warnings.append("titlul are %d caractere, ținta e cel mult 70" % len(title))
    if "<" in title or ">" in title or "<" in desc or ">" in desc:
        errors.append("titlul și descrierea nu pot conține < sau >")
    if len(desc.encode("utf-8")) > 5000:
        errors.append("descrierea depășește 5000 de octeți")
    if sum(len(t) for t in tags) > 500:
        errors.append("tag-urile depășesc 500 de caractere în total")
    if len(tags) < 10 or len(tags) > 15:
        warnings.append("sunt %d tag-uri, ținta e între 10 și 15" % len(tags))
    if short:
        if duration > 180:
            errors.append("un Short poate avea cel mult 180 de secunde")
        if "#shorts" not in title.lower():
            errors.append("titlul unui Short trebuie să conțină #Shorts")
    return errors, warnings


def valid_chapters(chapters: list[dict], duration: float) -> list[str]:
    errors: list[str] = []
    if len(chapters) < 3:
        errors.append("sunt necesare cel puțin 3 capitole")
    if chapters and chapters[0]["t"] != 0:
        errors.append("primul capitol trebuie să înceapă la 00:00")
    for a, b in zip(chapters, chapters[1:]):
        if b["t"] <= a["t"]:
            errors.append("capitolele trebuie să fie în ordine crescătoare")
            break
    for i, ch in enumerate(chapters):
        end = chapters[i + 1]["t"] if i + 1 < len(chapters) else duration
        if end - ch["t"] < 10:
            errors.append("capitolul '%s' are sub 10 secunde" % ch.get("title", ""))
    return errors


def _stamp(t: float) -> str:
    t = int(t)
    h, rest = divmod(t, 3600)
    m, s = divmod(rest, 60)
    return "%d:%02d:%02d" % (h, m, s) if h else "%02d:%02d" % (m, s)


def chapters_text(chapters: list[dict]) -> str:
    return "\n".join("%s %s" % (_stamp(c["t"]), c["title"]) for c in chapters)


def build_body(meta: dict, publish_at: str, short: bool) -> dict:
    desc = meta.get("description") or ""
    chapters = meta.get("chapters") or []
    if chapters:
        desc = (desc + "\n\n" if desc else "") + chapters_text(chapters)
    lang = meta.get("language") or "ro"
    return {
        "snippet": {
            "title": meta["title"],
            "description": desc,
            "tags": list(meta.get("tags") or []),
            "categoryId": str(meta.get("category_id") or "17"),
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": False,
        },
    }


# ---------------------------------------------------------------------- rețea

class NotConnected(Exception):
    pass


def _service(profile: str):
    """Clientul YouTube autentificat; singurul punct de contact cu rețeaua."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    tok = cfg.token_path(profile)
    if not tok.exists():
        raise NotConnected()
    try:
        creds = Credentials.from_authorized_user_file(str(tok), SCOPES)
        if not creds.valid:
            creds.refresh(Request())
            _write_secret(tok, creds.to_json())
    except Exception as exc:  # token revocat, expirat sau stricat
        raise NotConnected() from exc
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def _write_secret(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, 0o600)


def _channel_name(service) -> str:
    resp = service.channels().list(part="snippet", mine=True).execute()
    items = resp.get("items") or []
    return items[0]["snippet"]["title"] if items else ""


def _upload_video(service, file: Path, body: dict) -> str:
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(file), chunksize=CHUNK, resumable=True)
    req = service.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


def _check_scheduled(service, video_id: str, publish_at: str) -> list[str]:
    resp = service.videos().list(part="status", id=video_id).execute()
    items = resp.get("items") or []
    if not items:
        return ["videoclipul nu a fost găsit pe YouTube"]
    st = items[0].get("status", {})
    problems = []
    if st.get("privacyStatus") != "private":
        problems.append("videoclipul nu e privat")
    got = st.get("publishAt")
    if not got or _norm(got) != _norm(publish_at):
        problems.append("publishAt diferă: %s" % got)
    return problems


def _norm(ts: str) -> str:
    return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------------ CLI

def _emit(obj: dict, code: int = 0) -> None:
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _api_error(exc: Exception, **extra) -> None:
    """Eroare de rețea sau API ca JSON, exit 2. Fără detalii care ar putea conține secrete."""
    status = getattr(getattr(exc, "resp", None), "status", None)
    msg = "eroare YouTube (%s)" % status if status else "eroare de rețea sau YouTube (%s)" % type(exc).__name__
    _emit({"error": msg, **extra}, 2)


def _whoami(profile: str) -> None:
    if not cfg.token_path(profile).exists():
        _emit({"error": "neconectat"}, 3)
    try:
        name = _channel_name(_service(profile))
    except NotConnected:
        _emit({"error": "neconectat"}, 3)
    except Exception as exc:
        _api_error(exc)
    _emit({"channel": name})


def _cmd_auth(args) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    src = Path(args.client).expanduser()
    if not src.exists():
        _emit({"error": "fișierul client nu există"}, 4)
    dest = cfg.client_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    os.chmod(dest, 0o600)
    flow = InstalledAppFlow.from_client_secrets_file(str(dest), SCOPES)
    creds = flow.run_local_server(port=0)
    _write_secret(cfg.token_path(args.profile), creds.to_json())
    _whoami(args.profile)


def _cmd_find_client(args) -> None:
    found = sorted(
        (Path.home() / "Downloads").glob("client_secret_*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    if not found:
        _emit({"error": "nu există niciun fișier client_secret_*.json în Downloads"}, 4)
    _emit({"path": str(found[-1])})


def _cmd_upload(args, profile: str, prof: dict) -> None:
    file = Path(args.file)
    if not file.exists():
        _emit({"error": "fișierul video nu există", "errors": [str(file)]}, 2)
    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    duration = _duration(file, args)
    errors, warnings = validate_meta(meta, duration, args.short)
    if not args.short:
        errors += valid_chapters(meta.get("chapters") or [], duration) if meta.get("chapters") else []
    try:
        publish_at = parse_publish_at(args.publish_at, prof["timezone"])
    except ValueError as exc:
        errors.append(str(exc))
    if errors:
        _emit({"error": "date invalide", "errors": errors, "warnings": warnings}, 2)

    run_dir = Path(args.run_dir)
    log = run_dir / "uploaded.json"
    done = json.loads(log.read_text(encoding="utf-8")) if log.exists() else {}
    sha = _sha256(file)
    if sha in done and not args.force:
        _emit({"error": "fișierul a fost deja urcat", "existing": done[sha]}, 5)

    body = build_body(meta, publish_at, args.short)
    if args.dry_run:
        _emit({"dry_run": True, "body": body, "warnings": warnings})

    try:
        service = _service(profile)
    except NotConnected:
        _emit({"error": "neconectat"}, 3)
    try:
        vid = _upload_video(service, file, body)
    except Exception as exc:
        _api_error(exc)
    # înregistrarea se scrie imediat: videoclipul există deja pe YouTube
    entry = {"id": vid, "url": "https://youtu.be/" + vid, "publishAt": publish_at}
    done[sha] = entry
    run_dir.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        problems = _check_scheduled(service, vid, publish_at)
    except Exception as exc:
        _api_error(exc, errors=["videoclipul a fost urcat, dar verificarea a eșuat"], **entry)
    if problems:
        _emit({"error": "verificare eșuată", "errors": problems, **entry}, 2)
    _emit({**entry, "warnings": warnings})


def _probe_duration(file: Path) -> float:
    """Durata reală din fișier, cu ffprobe (listă de argumente, fără shell)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(file)],
            capture_output=True, text=True, check=True,
        ).stdout
        return float(out.strip())
    except (OSError, subprocess.CalledProcessError, ValueError):
        _emit({"error": "nu am putut citi durata fișierului cu ffprobe", "errors": [str(file)]}, 2)


def _duration(file: Path, args) -> float:
    """--duration dacă e dată, altfel durata citită din fișier."""
    if getattr(args, "duration", None) is not None:
        return float(args.duration)
    return _probe_duration(file)


def _cmd_verify(args, profile: str, prof: dict) -> None:
    try:
        publish_at = parse_publish_at(args.publish_at, prof["timezone"], now=datetime(1970, 1, 1, tzinfo=timezone.utc))
        service = _service(profile)
    except NotConnected:
        _emit({"error": "neconectat"}, 3)
    except ValueError as exc:
        _emit({"error": str(exc)}, 2)
    try:
        problems = _check_scheduled(service, args.id, publish_at)
    except Exception as exc:
        _api_error(exc)
    if problems:
        _emit({"error": "verificare eșuată", "errors": problems}, 2)
    _emit({"ok": True, "id": args.id, "publishAt": publish_at})


def _default_profile() -> str:
    f = cfg.home() / "config.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8")).get("default_profile", "principal")
    return "principal"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="youtube.py")
    ap.add_argument("--profile", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami")
    p = sub.add_parser("auth")
    p.add_argument("--client", required=True)
    sub.add_parser("find-client")
    p = sub.add_parser("upload")
    p.add_argument("--file", required=True)
    p.add_argument("--meta", required=True)
    p.add_argument("--publish-at", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--duration", type=float, default=None, help="durata clipului în secunde")
    p.add_argument("--short", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("verify")
    p.add_argument("--id", required=True)
    p.add_argument("--publish-at", required=True)

    # --profile se acceptă și după subcomandă
    args, rest = ap.parse_known_args(argv)
    if rest and rest[0] == "--profile" and len(rest) == 2:
        args.profile = rest[1]
    elif rest:
        ap.error("argumente necunoscute: %s" % " ".join(rest))
    profile = args.profile or _default_profile()
    args.profile = profile
    prof = cfg.load_profile(profile)

    if args.cmd == "whoami":
        _whoami(profile)
    elif args.cmd == "auth":
        _cmd_auth(args)
    elif args.cmd == "find-client":
        _cmd_find_client(args)
    elif args.cmd == "upload":
        _cmd_upload(args, profile, prof)
    elif args.cmd == "verify":
        _cmd_verify(args, profile, prof)


if __name__ == "__main__":
    main()

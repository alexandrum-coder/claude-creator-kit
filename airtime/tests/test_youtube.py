from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import youtube as y

NOW = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


def good_meta(**over):
    meta = {
        "title": "Cum alegi ghidonul potrivit",
        "description": "O descriere scurta.",
        "tags": ["tag%d" % i for i in range(12)],
        "chapters": [{"t": 0, "title": "Intro"}, {"t": 30, "title": "Ghidon"}, {"t": 70, "title": "Final"}],
        "language": "ro",
        "category_id": "17",
    }
    meta.update(over)
    return meta


def test_publish_at_dst():
    assert y.parse_publish_at("2026-10-25 18:00", "Europe/Bucharest", now=NOW) == "2026-10-25T16:00:00Z"
    assert y.parse_publish_at("2026-10-24 18:00", "Europe/Bucharest", now=NOW) == "2026-10-24T15:00:00Z"


def test_publish_at_past():
    with pytest.raises(ValueError):
        y.parse_publish_at("2026-09-30 18:00", "Europe/Bucharest", now=NOW)
    # 10 minute ahead is under the 15 minute margin (12:10 Bucharest = 09:10 UTC)
    with pytest.raises(ValueError):
        y.parse_publish_at("2026-10-01 12:10", "Europe/Bucharest", now=NOW)


def test_title_limits():
    errors, warnings = y.validate_meta(good_meta(title="a" * 71), 300, False)
    assert errors == []
    assert warnings
    errors, _ = y.validate_meta(good_meta(title="a" * 101), 300, False)
    assert errors
    errors, warnings = y.validate_meta(good_meta(), 300, False)
    assert errors == [] and warnings == []


def test_angle_brackets_rejected():
    assert y.validate_meta(good_meta(title="a <b>"), 300, False)[0]
    assert y.validate_meta(good_meta(description="x > y"), 300, False)[0]


def test_tag_rules():
    errors, warnings = y.validate_meta(good_meta(tags=["a"] * 5), 300, False)
    assert errors == [] and warnings
    errors, _ = y.validate_meta(good_meta(tags=["x" * 100] * 6), 300, False)
    assert errors
    errors, _ = y.validate_meta(good_meta(description="ă" * 2600), 300, False)
    assert errors  # over 5000 bytes though under 5000 characters


def test_chapters_rules():
    ok = [{"t": 0, "title": "a"}, {"t": 20, "title": "b"}, {"t": 40, "title": "c"}]
    assert y.valid_chapters(ok, 100) == []
    assert y.valid_chapters([{"t": 5, "title": "a"}] + ok[1:], 100)
    assert y.valid_chapters(ok[:2], 100)
    assert y.valid_chapters([ok[0], {"t": 8, "title": "b"}, {"t": 40, "title": "c"}], 100)
    assert y.valid_chapters([ok[0], {"t": 40, "title": "b"}, {"t": 20, "title": "c"}], 100)


def test_chapters_skipped_when_short():
    assert y.valid_chapters([], 40)
    body = y.build_body(good_meta(chapters=[]), "2026-10-25T16:00:00Z", False)
    assert body["snippet"]["description"] == "O descriere scurta."
    assert "00:00" not in body["snippet"]["description"]


def test_chapters_text():
    text = y.chapters_text([{"t": 0, "title": "Intro"}, {"t": 75, "title": "Doi"}, {"t": 3725, "title": "Trei"}])
    assert text.splitlines() == ["00:00 Intro", "01:15 Doi", "1:02:05 Trei"]


def test_short_requires_hashtag_and_180s():
    errors, _ = y.validate_meta(good_meta(title="Fara hashtag"), 60, True)
    assert errors
    errors, _ = y.validate_meta(good_meta(title="Cu hashtag #Shorts"), 181, True)
    assert errors
    errors, _ = y.validate_meta(good_meta(title="Cu hashtag #Shorts"), 59, True)
    assert errors == []


def test_body_private_with_publish_at():
    body = y.build_body(good_meta(), "2026-10-25T16:00:00Z", False)
    assert body["status"] == {
        "privacyStatus": "private",
        "publishAt": "2026-10-25T16:00:00Z",
        "selfDeclaredMadeForKids": False,
    }
    sn = body["snippet"]
    assert sn["title"] == "Cum alegi ghidonul potrivit"
    assert sn["categoryId"] == "17"
    assert sn["defaultLanguage"] == sn["defaultAudioLanguage"] == "ro"
    assert "00:00 Intro" in sn["description"]
    assert sn["description"].startswith("O descriere scurta.")


def run_cli(args, capsys):
    with pytest.raises(SystemExit) as e:
        y.main(args)
    out = capsys.readouterr().out
    return e.value.code, json.loads(out)


def test_upload_refuses_duplicate(tmp_path, capsys):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video-bytes")
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps(good_meta()))
    run = tmp_path / "run"
    run.mkdir()
    sha = hashlib.sha256(b"video-bytes").hexdigest()
    (run / "uploaded.json").write_text(json.dumps({sha: {"id": "abc", "url": "u", "publishAt": "p"}}))
    args = ["upload", "--file", str(video), "--meta", str(meta), "--publish-at", "2099-01-01 18:00",
            "--run-dir", str(run), "--duration", "300", "--dry-run"]
    code, out = run_cli(args, capsys)
    assert code == 5
    assert "error" in out


def test_upload_dry_run_prints_body(tmp_path, capsys):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps(good_meta()))
    run = tmp_path / "run"
    run.mkdir()
    args = ["upload", "--file", str(video), "--meta", str(meta), "--publish-at", "2099-01-01 18:00",
            "--run-dir", str(run), "--duration", "300", "--dry-run"]
    code, out = run_cli(args, capsys)
    assert code == 0
    assert out["body"]["status"]["privacyStatus"] == "private"
    assert out["body"]["status"]["publishAt"].endswith("Z")
    assert not (run / "uploaded.json").exists()


def test_upload_invalid_meta_exit_2(tmp_path, capsys):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps(good_meta(title="")))
    args = ["upload", "--file", str(video), "--meta", str(meta), "--publish-at", "2099-01-01 18:00",
            "--run-dir", str(tmp_path), "--duration", "300", "--dry-run"]
    code, out = run_cli(args, capsys)
    assert code == 2
    assert out["errors"]


def test_whoami_no_token_exit_3(capsys, monkeypatch):
    def boom(profile):
        raise AssertionError("network touched")

    monkeypatch.setattr(y, "_service", boom)
    code, out = run_cli(["whoami"], capsys)
    assert code == 3
    assert out == {"error": "neconectat"}


def test_find_client_picks_newest(tmp_path, capsys, monkeypatch):
    import os

    monkeypatch.setenv("HOME", str(tmp_path / "h"))
    dl = Path(tmp_path / "h" / "Downloads")
    dl.mkdir(parents=True)
    old = dl / "client_secret_old.json"
    new = dl / "client_secret_new.json"
    old.write_text("{}")
    new.write_text("{}")
    os.utime(old, (1, 1))
    code, out = run_cli(["find-client"], capsys)
    assert code == 0
    assert out["path"] == str(new)
    new.unlink()
    old.unlink()
    code, out = run_cli(["find-client"], capsys)
    assert code == 4


def test_short_duration_probed_from_file(tmp_path, capsys, monkeypatch):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps(good_meta(title="Reel #Shorts", chapters=[])))
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)

        class R:
            stdout = "200.0\n"

        return R()

    monkeypatch.setattr(y.subprocess, "run", fake_run)
    args = ["upload", "--file", str(video), "--meta", str(meta), "--publish-at", "2099-01-01 18:00",
            "--run-dir", str(tmp_path), "--short", "--dry-run"]
    code, out = run_cli(args, capsys)
    assert code == 2
    assert any("180" in e for e in out["errors"])
    assert calls[0][0] == "ffprobe" and calls[0][-1] == str(video)

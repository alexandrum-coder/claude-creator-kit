#!/usr/bin/env python3
"""Hook de declanșare pentru prompt-flow.

UserPromptSubmit: la o cerere care poate fi de lucru, cât timp sesiunea nu are
marcaj, adaugă o notă care îi cere modelului să încarce skill-ul prompt-flow.
PreToolUse (Agent/Task): când pornește subagentul prompt-agent, scrie marcajul
sesiunii, ca hook-ul să nu mai intervină în aceeași sesiune.

Marcajul se scrie abia când optimizarea chiar pornește. Un salut sau o întrebare
de conversație, pe care modelul le lasă să treacă, nu consumă marcajul.

Nu blochează niciodată: iese mereu cu cod 0 și tace la orice eroare.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata

INSTRUCTIUNE = (
    "prompt-flow: sesiunea nu are încă un prompt optimizat. Dacă mesajul de mai "
    "sus cere o lucrare (nu e un salut, o întrebare de conversație sau o "
    "confirmare), încarcă întâi skill-ul al cărui nume se termină în "
    "`prompt-flow` și urmează-l, înainte de orice altă unealtă. Altfel răspunde "
    "normal și ignoră această notă."
)

MIN_CUVINTE = 5
CONFIRMARI = {
    "da", "ok", "okay", "aprob", "merge", "continua", "go", "yes", "y", "sure",
    "1", "2", "3", "a", "b", "c", "mai", "departe", "inainte", "bine", "perfect",
    "super", "multumesc", "mersi", "thanks", "nu", "no",
}
_NUME_AGENT = "prompt-agent"
_UNELTE_AGENT = ("Agent", "Task")


def _normalizeaza(text):
    d = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def e_cerere_posibila(prompt):
    if not isinstance(prompt, str):
        return False
    t = prompt.strip()
    if not t or t.startswith("/"):
        return False
    cuvinte = re.findall(r"\w+", _normalizeaza(t))
    if len(cuvinte) < MIN_CUVINTE:
        return False
    return not all(c in CONFIRMARI for c in cuvinte)


def e_agentul_nostru(nume):
    return isinstance(nume, str) and (nume == _NUME_AGENT or nume.endswith(":" + _NUME_AGENT))


def director_stare(env):
    d = env.get("CLAUDE_PLUGIN_DATA")
    if d:
        return d
    return os.path.join(env.get("TMPDIR") or tempfile.gettempdir(), "prompt-agent")


def _cale_marcaj(director, sid):
    sigur = re.sub(r"[^A-Za-z0-9_-]", "_", sid)[:80]
    h = hashlib.sha256(sid.encode("utf-8")).hexdigest()[:12]
    return os.path.join(director, "sesiune-%s-%s" % (sigur, h))


def _sid(data):
    sid = data.get("session_id")
    return sid if isinstance(sid, str) and sid else None


def decide(data, director):
    if not isinstance(data, dict):
        return None
    sid = _sid(data)
    if sid is None:
        return None
    event = data.get("hook_event_name")
    if event == "PreToolUse":
        ti = data.get("tool_input")
        if data.get("tool_name") in _UNELTE_AGENT and isinstance(ti, dict) \
                and e_agentul_nostru(ti.get("subagent_type")):
            os.makedirs(director, exist_ok=True)
            with open(_cale_marcaj(director, sid), "w") as f:
                f.write("1")
        return None
    if event == "UserPromptSubmit":
        if os.path.exists(_cale_marcaj(director, sid)):
            return None
        if e_cerere_posibila(data.get("prompt")):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": INSTRUCTIUNE,
                }
            }
    return None


def main():
    try:
        raw = sys.stdin.buffer.read()
        data = json.loads(raw.decode("utf-8"))
        out = decide(data, director_stare(os.environ))
        if out is not None:
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
            sys.stdout.flush()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    main()
    sys.exit(0)

"""Teste pentru hooks/prompt_agent_trigger.py.

Rulare: python3 -m unittest discover -s hooks/tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

AICI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(AICI), "prompt_agent_trigger.py")
sys.path.insert(0, os.path.dirname(AICI))

import prompt_agent_trigger as pat  # noqa: E402

LUNG = "Scrie un script Python care citește un CSV cu vânzări și face un raport lunar."
SID = "sesiune-test-1"


def ups(prompt, sid=SID):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": prompt}


def ptu(subagent, sid=SID, tool="Agent"):
    return {
        "hook_event_name": "PreToolUse",
        "session_id": sid,
        "tool_name": tool,
        "tool_input": {"subagent_type": subagent, "prompt": "x"},
    }


class CuDirector(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def marcaje(self):
        return sorted(os.listdir(self.dir))

    def decide(self, data):
        return pat.decide(data, self.dir)


class TestUserPromptSubmit(CuDirector):
    def test_prompt_lung_la_inceput_intervine_fara_marcaj(self):
        out = self.decide(ups(LUNG))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("prompt-flow", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.marcaje(), [])

    def test_dupa_marcaj_nu_mai_intervine(self):
        self.decide(ptu("prompt-agent:prompt-agent"))
        self.assertIsNone(self.decide(ups(LUNG)))

    def test_alta_sesiune_intervine_in_continuare(self):
        self.decide(ptu("prompt-agent:prompt-agent"))
        self.assertIsNotNone(self.decide(ups(LUNG, sid="alta-sesiune")))

    def test_confirmari_nu_intervin(self):
        for p in ["da", "ok", "aprob", "Merge!", "continuă", "go", "yes", "1", "B",
                  "da, aprob", "ok, merge mai departe", "  Aprob.  "]:
            with self.subTest(p=p):
                self.assertIsNone(self.decide(ups(p)))
        self.assertEqual(self.marcaje(), [])

    def test_sub_cinci_cuvinte_nu_intervine(self):
        self.assertIsNone(self.decide(ups("fă un raport lunar")))

    def test_comanda_slash_nu_intervine(self):
        self.assertIsNone(self.decide(ups("/prompt-flow " + LUNG)))
        self.assertIsNone(self.decide(ups("  /compact păstrează doar deciziile importante de azi")))

    def test_diacritice(self):
        out = self.decide(ups("Fă-mi o listă cu țintele și pașii pentru lansarea în noiembrie"))
        self.assertIsNotNone(out)
        json.dumps(out, ensure_ascii=False)

    def test_fara_session_id_nu_intervine(self):
        self.assertIsNone(self.decide({"hook_event_name": "UserPromptSubmit", "prompt": LUNG}))
        self.assertIsNone(self.decide(ups(LUNG, sid="")))
        self.assertIsNone(self.decide(ups(LUNG, sid=123)))

    def test_prompt_nu_e_text(self):
        self.assertIsNone(self.decide(ups(None)))
        self.assertIsNone(self.decide(ups(["a"] * 10)))

    def test_eveniment_necunoscut(self):
        d = ups(LUNG)
        d["hook_event_name"] = "Stop"
        self.assertIsNone(self.decide(d))

    def test_date_care_nu_sunt_dict(self):
        for d in [None, [], "text", 3]:
            self.assertIsNone(self.decide(d))


class TestPreToolUse(CuDirector):
    def test_agent_prompt_agent_scrie_marcaj_si_tace(self):
        for nume in ["prompt-agent", "prompt-agent:prompt-agent", "obsydia-skills:prompt-agent"]:
            with self.subTest(nume=nume):
                sid = "s-" + nume.replace(":", "_")
                self.assertIsNone(self.decide(ptu(nume, sid=sid)))
                self.assertIsNone(self.decide(ups(LUNG, sid=sid)))
        self.assertEqual(len(self.marcaje()), 3)

    def test_unealta_task_veche(self):
        self.decide(ptu("prompt-agent", tool="Task"))
        self.assertIsNone(self.decide(ups(LUNG)))

    def test_alt_agent_nu_scrie_marcaj(self):
        for nume in ["general-purpose", "personal-assistant", "prompt-agent-x", "my-prompt-agentx", None]:
            self.decide(ptu(nume))
        self.assertEqual(self.marcaje(), [])
        self.assertIsNotNone(self.decide(ups(LUNG)))

    def test_alta_unealta_nu_scrie_marcaj(self):
        self.decide(ptu("prompt-agent", tool="Skill"))
        self.assertEqual(self.marcaje(), [])

    def test_session_id_cu_caractere_de_cale(self):
        self.decide(ptu("prompt-agent", sid="../../evadare/x"))
        m = self.marcaje()
        self.assertEqual(len(m), 1)
        self.assertNotIn("/", m[0])
        self.assertNotIn("..", m[0])
        self.assertIsNone(self.decide(ups(LUNG, sid="../../evadare/x")))


class TestDirector(unittest.TestCase):
    def test_plugin_data_are_prioritate(self):
        self.assertEqual(pat.director_stare({"CLAUDE_PLUGIN_DATA": "/a/b", "TMPDIR": "/t"}), "/a/b")

    def test_fallback_tmpdir(self):
        self.assertEqual(pat.director_stare({"TMPDIR": "/t/"}), os.path.join("/t/", "prompt-agent"))

    def test_fallback_fara_tmpdir(self):
        self.assertEqual(pat.director_stare({}), os.path.join(tempfile.gettempdir(), "prompt-agent"))


class TestMain(unittest.TestCase):
    def ruleaza(self, intrare, env_extra=None):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, CLAUDE_PLUGIN_DATA=d)
            env.update(env_extra or {})
            p = subprocess.run([sys.executable, SCRIPT], input=intrare, capture_output=True, env=env)
            return p, sorted(os.listdir(d))

    def test_json_stricat_iese_zero_fara_iesire(self):
        for intrare in [b"", b"{nu e json", b"\xff\xfe", b"null"]:
            with self.subTest(intrare=intrare):
                p, m = self.ruleaza(intrare)
                self.assertEqual(p.returncode, 0)
                self.assertEqual(p.stdout, b"")
                self.assertEqual(m, [])

    def test_prompt_lung_scrie_json_valid(self):
        p, m = self.ruleaza(json.dumps(ups(LUNG)).encode("utf-8"))
        self.assertEqual(p.returncode, 0)
        out = json.loads(p.stdout.decode("utf-8"))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertEqual(m, [])

    def test_pretooluse_scrie_marcaj_fara_iesire(self):
        p, m = self.ruleaza(json.dumps(ptu("prompt-agent:prompt-agent")).encode("utf-8"))
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, b"")
        self.assertEqual(len(m), 1)

    def test_director_nescriibil_iese_zero(self):
        p, _ = self.ruleaza(json.dumps(ptu("prompt-agent")).encode("utf-8"),
                            {"CLAUDE_PLUGIN_DATA": "/dev/null/nu-se-poate"})
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, b"")


class TestText(unittest.TestCase):
    def test_fara_forma_cu_a_circumflex(self):
        self.assertNotIn("s\u00e2nt", pat.INSTRUCTIUNE.lower())


if __name__ == "__main__":
    unittest.main()

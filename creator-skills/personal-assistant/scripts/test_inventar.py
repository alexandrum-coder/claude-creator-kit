"""Tests for the inventory script. Run: python3 scripts/test_inventar.py

Every test builds a synthetic Claude config in a temporary folder; the real
~/.claude is never read. The superset test runs the v2 scanner copied, at test
time, from setup-mac.sh (read only) on the same fixture.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout

AICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AICI)
import inventar  # noqa: E402

SETUP = os.path.normpath(os.path.join(AICI, "..", "..", "..", "setup-mac.sh"))
SECRET = "sk-test-abcdefghijklmnopqrstuvwxyz0123456789"


def scrie(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text if isinstance(text, str) else json.dumps(text))
    return path


def md(name, description, extra=""):
    return f"---\nname: {name}\ndescription: {description}\n{extra}---\n\nCorp.\n"


def v2_scanner():
    """The Python heredoc of setup-mac.sh's scan(), extracted without running the script."""
    with open(SETUP, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"python3 - > \"\$INV\" <<'PY'\n(.*?)\nPY\n", text, re.S)
    return m.group(1) if m else None


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="inventar-test-")
        self.home = os.path.join(self.tmp, "home")
        self.conf = os.path.join(self.home, ".claude")
        self.app = os.path.join(self.tmp, "app")
        cache = os.path.join(self.tmp, "cache")
        alpha = os.path.join(cache, "alpha")
        solo = os.path.join(cache, "solo")
        volt = os.path.join(cache, "volt")
        scrie(os.path.join(alpha, "skills", "unu", "SKILL.md"), md("unu", "Editare clipuri video lungi pentru YouTube"))
        scrie(os.path.join(alpha, "skills", "grup", "doi", "SKILL.md"), md("doi", "Scrie planuri"))
        scrie(os.path.join(alpha, "agents", "agentul.md"), md("agentul", "Agent de marketing"))
        scrie(os.path.join(alpha, "commands", "cmd.md"), md("cmd", "O comandă"))
        scrie(os.path.join(alpha, ".mcp.json"), {"mcpServers": {"yt-transcript": {"command": "npx", "env": {"TOKEN": SECRET}}}})
        scrie(os.path.join(solo, "SKILL.md"), md("Solo", "Un singur skill la rădăcină"))
        scrie(os.path.join(volt, "expert.md"), md("expert", "Agent VoltAgent la rădăcină"))
        scrie(os.path.join(self.conf, "plugins", "installed_plugins.json"), {"version": 2, "plugins": {
            "alpha@piata": [{"installPath": alpha, "version": "1.0"}],
            "solo@creator-kit": [{"installPath": solo, "version": "2.0"}],
            "volt@voltagent": [{"installPath": volt, "version": "0.1"}],
        }})
        scrie(os.path.join(self.conf, "settings.json"), {"enabledPlugins": {"solo@creator-kit": False}})
        scrie(os.path.join(self.conf, "skills", "liber", "SKILL.md"), md("liber", "Skill separat"))
        scrie(os.path.join(self.conf, "agents", "separat.md"), md("separat", "Agent separat"))
        scrie(os.path.join(self.conf, ".claude.json"), {
            "mcpServers": {"github": {"type": "http", "url": f"https://x.test/mcp?token={SECRET}",
                                      "headers": {"Authorization": f"Bearer {SECRET}"}}},
            "projects": {"/p": {"mcpServers": {"proiect-mcp": {"command": "node", "args": [SECRET]}}}},
        })
        scrie(os.path.join(self.home, ".claude.json"), {"mcpServers": {"din-home": {"command": "x"}}})
        scrie(os.path.join(self.app, "claude_desktop_config.json"), {"mcpServers": {"desktop-mcp": {"command": "y", "env": {"K": SECRET}}}})
        rpm = os.path.join(self.app, "local-agent-mode-sessions", "acc", "ws", "rpm", "plugin_x")
        scrie(os.path.join(rpm, ".claude-plugin", "plugin.json"), {"name": "cowork-p", "version": "1"})
        scrie(os.path.join(rpm, "skills", "cs", "SKILL.md"), md("cs", "Skill de Cowork"))
        scrie(os.path.join(self.app, "local-agent-mode-sessions", "skills-plugin", "a", "b", "manifest.json"),
              {"skills": [{"name": "pptx", "description": "Prezentări PowerPoint"}, "docx"]})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cai(self, own_conf=True):
        return {"conf": self.conf, "app": self.app, "own_conf": own_conf, "home": self.home}

    def items(self, own_conf=True, cache=False):
        return inventar.inventar(self.cai(own_conf), cache=cache)

    def ruleaza(self, *argv, own_conf=True):
        buf = io.StringIO()
        with redirect_stdout(buf):
            inventar.main(list(argv), self.cai(own_conf))
        return buf.getvalue()


class Chei(Fixture):
    def test_chei_asteptate(self):
        k = set(inventar.chei(self.items()))
        for cheie in ("I alpha@piata", "P alpha", "S unu", "S doi", "A agentul", "C cmd", "M yt-transcript",
                      "S solo", "A expert", "S liber", "A separat", "M github", "M proiect-mcp", "M desktop-mcp",
                      "P cowork-p", "S cs", "S pptx", "S docx"):
            self.assertIn(cheie, k)

    def test_id_cu_namespace(self):
        ids = {i["id"] for i in self.items()}
        for ident in ("alpha:unu", "alpha:doi", "alpha:agentul", "alpha:cmd", "solo:Solo", "volt:expert",
                      "cowork-p:cs", "anthropic-skills:pptx", "liber", "separat"):
            self.assertIn(ident, ids)

    def test_plugin_dezactivat(self):
        solo = [i for i in self.items() if i["id"] == "solo:Solo"][0]
        self.assertFalse(solo["activ"])
        self.assertTrue([i for i in self.items() if i["id"] == "alpha:unu"][0]["activ"])

    def test_home_claude_json_doar_fara_conf_propriu(self):
        self.assertNotIn("M din-home", inventar.chei(self.items(own_conf=True)))
        self.assertIn("M din-home", inventar.chei(self.items(own_conf=False)))


class Superset(Fixture):
    def test_superset_fata_de_v2(self):
        cod = v2_scanner() if os.path.exists(SETUP) else None
        if not cod:
            self.skipTest("setup-mac.sh v2 nu e lângă kit")
        for own in (True, False):
            env = dict(os.environ, CONF=self.conf, APP_DIR=self.app, HOME=self.home, OWN_CONF="yes" if own else "")
            v2 = subprocess.run([sys.executable, "-c", cod], env=env, capture_output=True, text=True, check=True)
            ref = set(filter(None, v2.stdout.splitlines()))
            self.assertTrue(ref, "scannerul v2 nu a întors nimic pe fixture")
            lipsa = ref - set(inventar.chei(self.items(own_conf=own)))
            self.assertEqual(lipsa, set(), f"chei v2 lipsă (own_conf={own})")


class Secrete(Fixture):
    def test_fara_secrete_in_json_si_cache(self):
        out = self.ruleaza("--json")
        self.assertNotIn(SECRET, out)
        self.assertNotIn("x.test", out)
        inventar.inventar(self.cai(), cache=True)
        with open(inventar.cale_cache(self.cai()), encoding="utf-8") as f:
            self.assertNotIn(SECRET, f.read())


class StariLimita(Fixture):
    def test_conf_absent(self):
        cai = {"conf": os.path.join(self.tmp, "nu-exista"), "app": os.path.join(self.tmp, "nici"),
               "own_conf": True, "home": self.home}
        self.assertEqual(inventar.inventar(cai, cache=False), [])

    def test_json_stricat(self):
        scrie(os.path.join(self.conf, "plugins", "installed_plugins.json"), "{nu e json")
        scrie(os.path.join(self.conf, ".claude.json"), "[]")
        k = inventar.chei(self.items())
        self.assertIn("S liber", k)
        self.assertNotIn("P alpha", k)

    def test_fara_cowork(self):
        shutil.rmtree(self.app)
        k = inventar.chei(self.items())
        self.assertNotIn("P cowork-p", k)
        self.assertIn("S unu", k)


class Cache(Fixture):
    def test_cache_scris_apoi_citit(self):
        prima = inventar.inventar(self.cai(), cache=True)
        path = inventar.cale_cache(self.cai())
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["items"] = [{"tip": "skill", "id": "marcaj", "nume": "marcaj", "plugin": "", "descriere": "",
                          "sursa": "", "activ": True}]
        scrie(path, data)
        self.assertEqual([i["id"] for i in inventar.inventar(self.cai(), cache=True)], ["marcaj"])
        self.assertNotEqual(prima, [])

    def test_cache_refacut_la_schimbare(self):
        inventar.inventar(self.cai(), cache=True)
        path = inventar.cale_cache(self.cai())
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["items"] = []
        scrie(path, data)
        skill = os.path.join(self.conf, "skills", "liber", "SKILL.md")
        viitor = time.time() + 5
        os.utime(skill, (viitor, viitor))
        self.assertIn("S liber", inventar.chei(inventar.inventar(self.cai(), cache=True)))

    def test_skill_nou_refacut(self):
        inventar.inventar(self.cai(), cache=True)
        scrie(os.path.join(self.conf, "skills", "nou", "SKILL.md"), md("nou", "Apărut după cache"))
        self.assertIn("S nou", inventar.chei(inventar.inventar(self.cai(), cache=True)))

    def test_fara_cache_nu_scrie(self):
        self.ruleaza("--chei", "--fara-cache")
        self.assertFalse(os.path.exists(inventar.cale_cache(self.cai())))


class Cauta(Fixture):
    def test_potrivire_cu_diacritice_si_flexiune(self):
        out = self.ruleaza("--fara-cache", "--cauta", "clipurile", "lungi", "Youtube")
        prima = out.splitlines()[0]
        self.assertIn("alpha:unu", prima)

    def test_descriere_gasita(self):
        gasite = inventar.cauta(self.items(), ["prezentări"])
        self.assertEqual(gasite[0][1]["id"], "anthropic-skills:pptx")

    def test_nume_cantareste_mai_mult(self):
        items = [
            {"tip": "skill", "id": "x:altceva", "nume": "altceva", "descriere": "face pptx", "activ": True},
            {"tip": "skill", "id": "y:pptx", "nume": "pptx", "descriere": "", "activ": True},
        ]
        gasite = inventar.cauta(items, ["pptx"])
        self.assertEqual([(s, i["id"]) for s, i in gasite], [(3, "y:pptx"), (1, "x:altceva")])

    def test_dezactivat_marcat(self):
        out = self.ruleaza("--fara-cache", "--cauta", "solo")
        self.assertIn("solo:Solo (dezactivat)", out)

    def test_fara_potrivire(self):
        self.assertEqual(self.ruleaza("--fara-cache", "--cauta", "xyzqwv").strip(), "Nicio potrivire.")

    def test_limita(self):
        out = self.ruleaza("--fara-cache", "--cauta", "skill", "agent", "--limita", "2")
        self.assertEqual(len(out.splitlines()), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)

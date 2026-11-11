#!/usr/bin/env python3
"""Inventory of everything this Mac's Claude can use: plugins, skills, agents,
commands and MCP servers. Read-only, except for its own cache.

Extracted (not rewritten) from three scanners that already exist:
  - the v2 scanner in setup-mac.sh (key format I/P/S/A/M, sources),
  - tools/genereaza-catalog.py (frontmatter parser, plugin layouts, descriptions),
  - claude-code-sync/mac/inventory-mac.sh (MCP lists, account plugins, redaction).

    python3 inventar.py --chei            # "I plugin@market", "P", "S", "A", "C", "M" lines
    python3 inventar.py --json            # every item, with description and source
    python3 inventar.py --cauta clip video youtube   # best matches first

Options: --fara-cache (neither read nor write the cache), --limita N (for --cauta).

Environment, same as setup-mac.sh: CLAUDE_CONFIG_DIR (default ~/.claude) and
CREATOR_KIT_APP_DIR (default ~/Library/Application Support/Claude). When
CLAUDE_CONFIG_DIR is not set, ~/.claude.json is read too.

Cache: $CONF/personal-assistant/inventar.json. It is rebuilt when any source
file changes (path, size or mtime). MCP servers are stored by name and type
only: commands, URLs, env and headers never reach the output or the cache.
"""
import glob
import hashlib
import json
import os
import re
import sys
import unicodedata

VERSIUNE_CACHE = 1

# ----------------------------------------------------------------------------
# Parsing helpers (genereaza-catalog.py: frontmatter, one_line; setup-mac.sh: name)
# ----------------------------------------------------------------------------


def citeste_cap(path, limita=8000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limita)
    except OSError:
        return ""


def frontmatter(path):
    m = re.match(r"---\s*\n(.*?)\n---", citeste_cap(path), re.S)
    if not m:
        return {}
    data, cur = {}, None
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if mm:
            cur = mm.group(1)
            data[cur] = mm.group(2).strip()
        elif cur and line[:1] in (" ", "\t"):
            data[cur] += " " + line.strip()
    out = {k: v.strip("\"'>|- ") for k, v in data.items()}
    # The name is read exactly as setup-mac.sh reads it, so the keys match.
    n = re.search(r"^name:\s*['\"]?([^'\"\n]+)", m.group(1), re.M)
    if n:
        out["name"] = n.group(1).strip()
    return out


def one_line(text, limit=170):
    text = re.sub(r"\s+", " ", text or "").replace("|", "/").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def incarca_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------


def cai_implicite():
    home = os.path.expanduser("~")
    conf = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(home, ".claude")
    app = os.environ.get("CREATOR_KIT_APP_DIR") or os.path.join(home, "Library", "Application Support", "Claude")
    return {"conf": conf, "app": app, "own_conf": bool(os.environ.get("CLAUDE_CONFIG_DIR")), "home": home}


def fisiere_config(cai):
    """JSON files read directly (not plugin trees)."""
    conf, app = cai["conf"], cai["app"]
    lista = [
        os.path.join(conf, "plugins", "installed_plugins.json"),
        os.path.join(conf, "settings.json"),
        os.path.join(conf, ".claude.json"),
        os.path.join(app, "claude_desktop_config.json"),
    ]
    if not cai["own_conf"]:
        lista.append(os.path.join(cai["home"], ".claude.json"))
    return lista


def pluginuri_instalate(conf):
    reg = incarca_json(os.path.join(conf, "plugins", "installed_plugins.json"))
    if not isinstance(reg, dict):
        return {}
    reg = reg.get("plugins", reg)
    return reg if isinstance(reg, dict) else {}


def radacini_cowork(app):
    """Account and Cowork plugins: (root, plugin.json)."""
    out = []
    for pj in sorted(glob.glob(os.path.join(app, "local-agent-mode-sessions", "*", "*", "rpm", "*", ".claude-plugin", "plugin.json"))):
        out.append((os.path.dirname(os.path.dirname(pj)), pj))
    return out


def manifeste_cont(app):
    return sorted(glob.glob(os.path.join(app, "local-agent-mode-sessions", "skills-plugin", "*", "*", "manifest.json")),
                  key=lambda p: (os.path.getmtime(p), p))


TIPARE_PLUGIN = (
    ("skill", "SKILL.md"),
    ("skill", "skills/*/SKILL.md"),
    ("skill", "skills/*/*/SKILL.md"),
    ("agent", "agents/*.md"),
    ("agent", "agents/*/*.md"),
    ("command", "commands/*.md"),
    ("command", "commands/*/*.md"),
)


def fisiere_plugin(root):
    out = []
    for tip, pat in TIPARE_PLUGIN:
        out += [(tip, f) for f in sorted(glob.glob(os.path.join(root, pat)))]
    return out


def semnatura(cai):
    """Hash of (path, size, mtime) of every file the inventory reads."""
    conf, app = cai["conf"], cai["app"]
    paths = list(fisiere_config(cai))
    for installs in pluginuri_instalate(conf).values():
        for inst in installs if isinstance(installs, list) else []:
            root = (inst or {}).get("installPath")
            if root:
                paths += [f for _, f in fisiere_plugin(root)]
                paths += glob.glob(os.path.join(root, "*.md"))
                paths += [os.path.join(root, ".mcp.json"), os.path.join(root, ".claude-plugin", "plugin.json")]
    paths += glob.glob(os.path.join(conf, "skills", "*", "SKILL.md"))
    paths += glob.glob(os.path.join(conf, "agents", "*.md"))
    for root, pj in radacini_cowork(app):
        paths.append(pj)
        paths += [f for _, f in fisiere_plugin(root)]
        paths.append(os.path.join(root, ".mcp.json"))
    paths += manifeste_cont(app)
    h = hashlib.sha256()
    for p in sorted(set(paths)):
        try:
            st = os.stat(p)
            h.update(f"{p}\0{st.st_size}\0{st.st_mtime_ns}\n".encode())
        except OSError:
            h.update(f"{p}\0-\n".encode())
    return h.hexdigest()


# ----------------------------------------------------------------------------
# Collection
# ----------------------------------------------------------------------------


class Colector:
    def __init__(self):
        self.items = {}

    def adauga(self, tip, nume, plugin="", descriere="", sursa="", activ=True):
        if not nume:
            return
        ident = f"{plugin}:{nume}" if plugin and tip in ("skill", "agent", "command") else nume
        cheie = (tip, ident.lower())
        if cheie in self.items:
            vechi = self.items[cheie]
            vechi["activ"] = vechi["activ"] or activ
            if not vechi["descriere"] and descriere:
                vechi["descriere"] = one_line(descriere)
            return
        self.items[cheie] = {"tip": tip, "id": ident, "nume": nume, "plugin": plugin,
                             "descriere": one_line(descriere), "sursa": sursa, "activ": activ}

    def mcp(self, servers, sursa, plugin="", activ=True):
        if not isinstance(servers, dict):
            return
        for name, spec in servers.items():
            spec = spec if isinstance(spec, dict) else {}
            transport = spec.get("type") or ("http" if spec.get("url") else "stdio")
            # Name and transport only: never the command, URL, env or headers.
            self.adauga("mcp", str(name), plugin=plugin, descriere=f"server MCP ({transport})", sursa=sursa, activ=activ)

    def arbore_plugin(self, root, plugin, sursa, activ=True):
        gasit = False
        for tip, f in fisiere_plugin(root):
            d = frontmatter(f)
            if tip == "skill":
                rezerva = os.path.basename(os.path.dirname(f))
            else:
                rezerva = os.path.basename(f)[:-3]
            self.adauga(tip, d.get("name") or rezerva, plugin, d.get("description", ""), sursa, activ)
            gasit = True
        # VoltAgent ships its agents as loose .md files in the plugin root.
        if not gasit:
            for f in sorted(glob.glob(os.path.join(root, "*.md"))):
                d = frontmatter(f)
                if d.get("name") and d.get("description"):
                    self.adauga("agent", d["name"], plugin, d["description"], sursa, activ)
        for mf in (os.path.join(root, ".mcp.json"), os.path.join(root, ".claude-plugin", "plugin.json")):
            data = incarca_json(mf)
            if isinstance(data, dict):
                self.mcp(data.get("mcpServers", data if mf.endswith(".mcp.json") else {}), sursa, plugin, activ)


def colecteaza(cai):
    conf, app = cai["conf"], cai["app"]
    c = Colector()
    setari = incarca_json(os.path.join(conf, "settings.json"))
    activate = (setari or {}).get("enabledPlugins", {}) if isinstance(setari, dict) else {}
    activate = activate if isinstance(activate, dict) else {}

    for pid, installs in sorted(pluginuri_instalate(conf).items()):
        nume = pid.split("@")[0]
        activ = activate.get(pid, True) is not False
        sursa = f"plugin {pid}"
        c.adauga("install", pid, sursa=sursa, activ=activ)
        c.adauga("plugin", nume, sursa=sursa, activ=activ)
        for inst in installs if isinstance(installs, list) else []:
            root = (inst or {}).get("installPath")
            if root:
                c.arbore_plugin(root, nume, sursa, activ)

    for f in sorted(glob.glob(os.path.join(conf, "skills", "*", "SKILL.md"))):
        d = frontmatter(f)
        c.adauga("skill", d.get("name") or os.path.basename(os.path.dirname(f)), "", d.get("description", ""), "skill separat")
    for f in sorted(glob.glob(os.path.join(conf, "agents", "*.md"))):
        d = frontmatter(f)
        c.adauga("agent", d.get("name") or os.path.basename(f)[:-3], "", d.get("description", ""), "agent separat")

    for root, pj in radacini_cowork(app):
        data = incarca_json(pj)
        nume = data.get("name") if isinstance(data, dict) else None
        if nume:
            c.adauga("plugin", str(nume), sursa="plugin de cont / Cowork")
        c.arbore_plugin(root, str(nume or os.path.basename(root)), "plugin de cont / Cowork")

    # Newest manifest first, so its descriptions win.
    for mf in reversed(manifeste_cont(app)):
        data = incarca_json(mf)
        for s in (data or {}).get("skills", []) if isinstance(data, dict) else []:
            n = s.get("name") if isinstance(s, dict) else s
            desc = s.get("description", "") if isinstance(s, dict) else ""
            if n:
                c.adauga("skill", str(n), "anthropic-skills", desc, "skill-uri Anthropic din cont")

    cfgs = [os.path.join(conf, ".claude.json")]
    if not cai["own_conf"]:
        cfgs.append(os.path.join(cai["home"], ".claude.json"))
    for cfg in cfgs:
        d = incarca_json(cfg)
        if not isinstance(d, dict):
            continue
        c.mcp(d.get("mcpServers", {}) or {}, "Claude Code")
        for proiect in (d.get("projects", {}) or {}).values():
            c.mcp((proiect or {}).get("mcpServers", {}) or {}, "Claude Code (proiect)")
    d = incarca_json(os.path.join(app, "claude_desktop_config.json"))
    if isinstance(d, dict):
        c.mcp(d.get("mcpServers", {}) or {}, "aplicația desktop")

    return sorted(c.items.values(), key=lambda i: (i["tip"], i["id"].lower()))


# ----------------------------------------------------------------------------
# Cache
# ----------------------------------------------------------------------------


def cale_cache(cai):
    return os.path.join(cai["conf"], "personal-assistant", "inventar.json")


def inventar(cai=None, cache=True):
    cai = cai or cai_implicite()
    sem = semnatura(cai)
    path = cale_cache(cai)
    if cache:
        vechi = incarca_json(path)
        if isinstance(vechi, dict) and vechi.get("versiune") == VERSIUNE_CACHE and vechi.get("semnatura") == sem:
            return vechi["items"]
    items = colecteaza(cai)
    if cache:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"versiune": VERSIUNE_CACHE, "semnatura": sem, "items": items}, f, ensure_ascii=False, indent=1)
            os.replace(tmp, path)
        except OSError:
            pass  # A read-only config dir still gets a fresh inventory.
    return items


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------

LITERA = {"install": "I", "plugin": "P", "skill": "S", "agent": "A", "command": "C", "mcp": "M"}


def chei(items):
    """setup-mac.sh key format, lowercased. Skills and agents by bare name."""
    return sorted({f"{LITERA[i['tip']]} {i['nume'].lower()}" for i in items})


def normalizeaza(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def cuvinte(text):
    return re.findall(r"[a-z0-9]+", normalizeaza(text))


def potriveste(cuvant, termeni):
    # Shared prefix of up to 5 letters, so "clipuri" finds "clip" and "editare" finds "editing".
    radacina = cuvant[:5]
    return any(t.startswith(radacina) or (len(t) >= 4 and cuvant.startswith(t)) for t in termeni)


def cauta(items, interogare, limita=15):
    cerute = [w for w in cuvinte(" ".join(interogare)) if len(w) >= 3]
    rezultate = []
    for i in items:
        if i["tip"] == "install":
            continue
        in_nume = cuvinte(i["id"].replace(":", " ").replace("-", " "))
        in_desc = cuvinte(i["descriere"])
        scor = sum(3 for w in cerute if potriveste(w, in_nume)) + sum(1 for w in cerute if potriveste(w, in_desc))
        if scor:
            rezultate.append((-scor, not i["activ"], i["id"].lower(), scor, i))
    rezultate.sort(key=lambda r: r[:3])
    return [(r[3], r[4]) for r in rezultate[:limita]]


def main(argv, cai=None):
    cache = "--fara-cache" not in argv
    limita = 15
    if "--limita" in argv:
        limita = int(argv[argv.index("--limita") + 1])
    items = inventar(cai, cache=cache)
    if "--json" in argv:
        json.dump(items, sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
    elif "--cauta" in argv:
        rest = argv[argv.index("--cauta") + 1:]
        interogare = [w for w in rest if not w.startswith("--") and not w.isdigit()]
        gasite = cauta(items, interogare, limita)
        if not gasite:
            print("Nicio potrivire.")
        for scor, i in gasite:
            stare = "" if i["activ"] else " (dezactivat)"
            print(f"{scor} | {i['tip']} | {i['id']}{stare} | {i['descriere']}")
    else:
        print("\n".join(chei(items)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

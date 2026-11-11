#!/usr/bin/env python3
"""Generate CATALOG-COMPLET.md: everything setup-mac.sh installs, item by item.

Read-only. It lists every skill, agent and command of:
  - the plugins installed in $CLAUDE_CONFIG_DIR (default ~/.claude), so run it
    against a test install made with setup-mac.sh to get exactly the
    colleague's set,
  - the Anthropic skills that come with a claude.ai account (skills-plugin
    manifest of the desktop app on this Mac, if present).

Descriptions are the authors' own (mostly English), cut to one line. The
fitness relevance column comes from the RELEVANTA map below, kept by hand.

    CLAUDE_CONFIG_DIR=/tmp/test-claude bash setup-mac.sh
    CLAUDE_CONFIG_DIR=/tmp/test-claude python3 tools/genereaza-catalog.py
"""
import datetime
import glob
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(HOME, "Library/Application Support/Claude/local-agent-mode-sessions")
CONF = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(HOME, ".claude")
OUT = os.path.join(REPO, "CATALOG-COMPLET.md")

# Where each plugin comes from, as shown in the table of contents.
PROFIL = {name: "instalat de setup-mac.sh" for name in (
    "creator-skills", "ecc", "marketing", "design", "brand-voice", "canva", "superpowers",
    "remotion-skills", "workout-program-designer", "postiz", "marketingskills")}
PROFIL["skill-uri-separate"] = "instalat de setup-mac.sh (~/.claude/skills)"
PROFIL["anthropic-skills"] = "vine cu contul Claude"

# plugin:item -> (stars, Romanian note). 3 = core for fitness content, 2 = useful.
RELEVANTA = {
    # presentations
    "anthropic-skills:pptx": (3, "prezentări PowerPoint (workshop, ofertă abonamente)"),
    "anthropic-skills:docx": (2, "documente Word: programe de antrenament, contracte"),
    "anthropic-skills:pdf": (2, "PDF-uri: ghiduri, planuri, fișe client"),
    "anthropic-skills:xlsx": (2, "tabele: progres clienți, calorii, buget"),
    "anthropic-skills:docs": (2, "documente editabile partajate"),
    "anthropic-skills:theme-factory": (2, "temă vizuală unitară pe slide-uri/documente"),
    "anthropic-skills:deep-research": (2, "cercetare cu surse (nutriție, studii)"),
    "ecc:frontend-slides": (3, "prezentări HTML animate, din zero sau din PPTX"),
    "ecc:google-workspace-ops": (2, "Google Slides/Docs/Sheets ca un singur flux"),
    "creator-skills:theme-factory": (2, "teme gata făcute pentru slide-uri"),
    "creator-skills:brandkit": (3, "board de brand: logo, culori, identitate"),
    "claude-mem:wowerpoint": (2, "transformă un document în deck PDF"),
    # video
    "ecc:video-editing": (3, "montaj clipuri: tăiere, structură, subtitrări (FFmpeg/Remotion)"),
    "ecc:remotion-video-creation": (3, "clipuri generate din cod: intro, text animat, captions"),
    "ecc:fal-ai-media": (2, "generare imagini/video/voce AI (cont fal.ai)"),
    "ecc:videodb": (2, "caută și decupează momente din înregistrări lungi"),
    "ecc:manim-video": (1, "animații explicative (grafice, diagrame)"),
    "ecc:ui-demo": (1, "înregistrare demo pentru site/aplicație"),
    "ecc:taste": (1, "direcție creativă pentru short-form edits"),
    # posts & copy
    "ecc:content-engine": (3, "sistem de conținut: TikTok, YouTube, LinkedIn, newsletter"),
    "ecc:crosspost": (3, "adaptează aceeași idee pentru fiecare rețea"),
    "ecc:social-publisher": (2, "programare postări (cont SocialClaw)"),
    "ecc:brand-voice": (3, "profil de ton din postările tale reale"),
    "ecc:article-writing": (2, "articole, ghiduri, newsletter"),
    "ecc:marketing-campaign": (3, "campanie completă: poziționare, postări, email, reclame"),
    "ecc:marketing-agent": (2, "agent strateg + copywriter"),
    "ecc:brand-discovery": (2, "interviu ghidat pentru identitatea brandului"),
    "ecc:seo": (1, "SEO pentru site"),
    "ecc:market-research": (2, "studiu de piață, concurență"),
    "creator-skills:humanizer": (3, "scoate tonul de AI din texte"),
    "creator-skills:prompt-master": (2, "prompturi pentru Midjourney, video AI, alte unelte"),
    "creator-skills:notebooklm": (2, "lucru cu NotebookLM (surse, rezumate, podcast)"),
    "marketing:content-creation": (3, "postări, articole, captions pe canal"),
    "marketing:draft-content": (3, "ciorne rapide de conținut"),
    "marketing:campaign-plan": (3, "plan de campanie (lansare program, provocare 30 zile)"),
    "marketing:brand-review": (2, "verifică textul față de brand"),
    "marketing:email-sequence": (2, "secvențe email pentru clienți noi"),
    "marketing:competitive-brief": (2, "analiză concurență (alte săli, antrenori)"),
    "marketing:performance-report": (2, "raport rezultate campanie"),
    "marketing:seo-audit": (1, "audit SEO site"),
    "skill-uri-separate:shorts": (3, "reels/shorts verticale din video lung, cu subtitrări animate"),
    "workout-program-designer:workout-program-designer": (3, "programe de antrenament personalizate"),
    "remotion-skills:*": (2, "clipuri din cod cu Remotion"),
    "postiz:*": (3, "programează și publică postări (cont Postiz)"),
    "brand-voice:*": (3, "ghid de ton din materialele existente + verificare"),
    "canva:*": (3, "creează și redimensionează design-uri în Canva (cont Canva)"),
    "design:design-critique": (2, "feedback pe un design (postare, flyer)"),
    "design:ux-copy": (1, "texte scurte pentru aplicații/site"),
    "voltagent-biz:content-marketer": (2, "agent strategie de conținut"),
    "voltagent-biz:content-quality-editor": (2, "curăță textul de tipare AI înainte de publicare"),
    "voltagent-biz:landing-page-copywriter": (2, "text pentru pagina de ofertă"),
    "agentic-bundle-aas-localization-international-growth:copywriting": (2, "copy pentru landing page și email"),
    "agentic-bundle-aas-localization-international-growth:content-creator": (2, "cadre de conținut pe platformă"),
    "agentic-bundle-aas-localization-international-growth:apify-market-research": (1, "cercetare Instagram/Google Maps"),
    "rhframe:umanizator": (3, "umanizare texte Instagram în română (PRIVAT)"),
    # visual
    "creator-skills:imagegen-frontend-mobile": (1, "concepte vizuale de aplicație mobilă"),
    "creator-skills:high-end-visual-design": (1, "site cu aspect premium"),
    "designpowers:voice-and-tone": (2, "voce și ton de brand"),
    # organising
    "creator-skills:personal-assistant": (3, "îți spune ce unealtă să folosești și o pornește"),
    "creator-skills:plan-taskmanager": (2, "plan pas cu pas pentru proiecte mari"),
    "creator-skills:compact-handoff": (1, "salvează sesiunea înainte de /compact"),
    "creator-skills:social-seo": (3, "descrieri și titluri găsite în căutare: Instagram, YouTube, Shorts"),
    "creator-skills:podcast-insights": (2, "fișă de idei verificabile din podcasturi și interviuri"),
    "marketingskills:social": (3, "ce postezi, formate, scripturi de reels, calendar"),
    "marketingskills:video": (2, "clipuri cu AI sau din cod, făcute repetabil"),
    "marketingskills:content-strategy": (2, "strategia de conținut: teme și piloni"),
    "marketingskills:copy-editing": (2, "corectura textelor de marketing"),
    "superpowers:brainstorming": (2, "rafinează o idee înainte de execuție"),
    "productivity:task-management": (1, "listă de taskuri"),
    "productivity:memory-management": (1, "memorie de lucru"),
}

KIND_RO = {"skill": "skill", "agent": "agent", "command": "comandă"}


def frontmatter(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read(8000)
    except OSError:
        return {}
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
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
    return {k: v.strip("\"'>|- ") for k, v in data.items()}


def one_line(text, limit=170):
    text = re.sub(r"\s+", " ", text or "").replace("|", "/").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def scan_plugin(root):
    items = set()
    patterns = (
        ("skill", "skills/*/SKILL.md"),
        ("skill", "skills/*/*/SKILL.md"),
        ("agent", "agents/*.md"),
        ("agent", "agents/*/*.md"),
        ("command", "commands/*.md"),
        ("command", "commands/*/*.md"),
    )
    for kind, pat in patterns:
        for f in glob.glob(os.path.join(root, pat)):
            d = frontmatter(f)
            fallback = os.path.basename(os.path.dirname(f)) if kind == "skill" else os.path.basename(f)[:-3]
            items.add((kind, d.get("name") or fallback, one_line(d.get("description", ""))))
    # A plugin made of one skill can keep its SKILL.md at the root.
    if not items and os.path.exists(os.path.join(root, "SKILL.md")):
        d = frontmatter(os.path.join(root, "SKILL.md"))
        items.add(("skill", d.get("name") or os.path.basename(root), one_line(d.get("description", ""))))
    # VoltAgent ships its agents as loose .md files in the plugin root.
    if not items:
        for f in glob.glob(os.path.join(root, "*.md")):
            d = frontmatter(f)
            if d.get("name") and d.get("description"):
                items.add(("agent", d["name"], one_line(d["description"])))
    hooks = any(os.path.exists(os.path.join(root, p)) for p in ("hooks/hooks.json", "hooks.json"))
    return sorted(items, key=lambda x: (x[0], x[1].lower())), hooks


def newest(pattern):
    paths = glob.glob(pattern)
    return max(paths, key=os.path.getmtime) if paths else None


def collect():
    plugins = {}
    installed = json.load(open(os.path.join(CONF, "plugins", "installed_plugins.json")))
    installed = installed.get("plugins", installed)
    # The kit ships one plugin per skill; show them grouped, as in the menu.
    groups = {}
    try:
        for e in json.load(open(os.path.join(REPO, ".claude-plugin", "marketplace.json")))["plugins"]:
            src = e.get("source")
            if isinstance(src, str) and src.startswith("./creator-skills/"):
                groups[e["name"]] = "creator-skills"
            elif isinstance(src, dict) and "marketingskills" in src.get("url", ""):
                groups[e["name"]] = "marketingskills"
    except (OSError, ValueError, KeyError):
        pass
    for key, versions in installed.items():
        name, market = key.split("@", 1)
        items, hooks = scan_plugin(versions[0]["installPath"])
        group = groups.get(name) if market == "creator-kit" else None
        if group:
            entry = plugins.setdefault(group, {"sursa": "marketplace `creator-kit`", "versiune": "", "items": [], "hooks": False})
            entry["items"] = sorted(entry["items"] + items)
            continue
        plugins[name] = {"sursa": f"marketplace `{market}`", "versiune": versions[0].get("version", ""),
                         "items": items, "hooks": hooks}
    loose = []
    for f in sorted(glob.glob(os.path.join(CONF, "skills", "*", "SKILL.md"))):
        d = frontmatter(f)
        loose.append(("skill", d.get("name") or os.path.basename(os.path.dirname(f)), one_line(d.get("description", ""))))
    if loose:
        plugins["skill-uri-separate"] = {"sursa": "folderul de skill-uri", "versiune": "", "items": loose, "hooks": False}
    manifest = newest(os.path.join(APP, "skills-plugin", "*", "*", "manifest.json"))
    if manifest:
        skills = json.load(open(manifest)).get("skills", [])
        plugins["anthropic-skills"] = {
            "sursa": "cont claude.ai (skill-uri Anthropic)", "versiune": "",
            "items": sorted(("skill", s["name"], one_line(s.get("description", ""))) for s in skills),
            "hooks": False,
        }
    return plugins


def relevance(plugin, name):
    return RELEVANTA.get(f"{plugin}:{name}") or RELEVANTA.get(f"{plugin}:*") or (0, "")


def render(plugins):
    total = sum(len(p["items"]) for p in plugins.values())
    today = datetime.date.today().isoformat()
    out = [
        "# Catalog complet: skill-uri, agenți, comenzi",
        "",
        f"Generat automat pe {today} de `tools/genereaza-catalog.py`, dintr-o instalare de test făcută cu `setup-mac.sh`. "
        f"{len([n for n in plugins if n not in ('anthropic-skills', 'skill-uri-separate')])} pluginuri instalate, skill-uri separate și skill-urile Anthropic care vin cu contul, {total} elemente. Nu edita de mână: rulează din nou scriptul.",
        "",
        "Descrierile sunt ale autorilor, de obicei în engleză. Coloana **Fitness** e completată de mână: "
        "★★★ esențial pentru conținut fitness (prezentări, clipuri, postări), ★★ util, ★ ocazional, gol = irelevant pentru tine. "
        "Lista scurtă, explicată în română, e în [CATALOG.md](CATALOG.md).",
        "",

        "## Cuprins",
        "",
        "| Plugin | Sursă | Cum ajunge la tine | Skill-uri | Agenți | Comenzi | Hook-uri |",
        "|---|---|---|---|---|---|---|",
    ]
    order = sorted(plugins)
    for name in order:
        p = plugins[name]
        c = {k: sum(1 for i in p["items"] if i[0] == k) for k in KIND_RO}
        out.append(f"| [{name}](#{name}) | {p['sursa']} | {PROFIL.get(name, '?')} | {c['skill']} | {c['agent']} | "
                   f"{c['command']} | {'da' if p['hooks'] else ''} |")
    for name in order:
        p = plugins[name]
        out += ["", f"## {name}", "",
                f"Sursă: {p['sursa']}" + (f", versiunea {p['versiune']}" if p["versiune"] else "") +
                "." + (" Are hook-uri (rulează automat la anumite evenimente)." if p["hooks"] else ""),
                "", "| Tip | Nume | Fitness | La ce folosește |", "|---|---|---|---|"]
        rows = []
        for kind, item, desc in p["items"]:
            stars, note = relevance(name, item)
            text = f"**{note}.** {desc}" if note else desc
            rows.append((-stars, kind, item.lower(), f"| {KIND_RO[kind]} | `{item}` | {'★' * stars} | {text} |"))
        out += [r[-1] for r in sorted(rows)]
    return "\n".join(out) + "\n"


def main():
    text = render(collect())
    if "--stdout" in sys.argv:
        sys.stdout.write(text)
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Scris {OUT}")


if __name__ == "__main__":
    main()

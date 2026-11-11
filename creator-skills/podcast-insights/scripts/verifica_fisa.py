"""Validate an episode sheet against its transcript.

Usage: python3 scripts/verifica_fisa.py <sheet> <transcript> <duration_minutes> [config.json]

config.json (optional) may hold "categorii": a list of section headings that
replaces the default categories.
Exits 0 when the sheet is valid; otherwise prints each error and exits 1.
"""
import re
import sys
import unicodedata

CATEGORII = [
    "Business și strategie",
    "Clienți și vânzări",
    "Produs",
    "Echipă și angajări",
    "Decizii și mod de gândire",
    "Agenți și AI",
    "Tooluri",
    "Cărți și resurse",
]
SURSE = {"[SPUS]", "[DEDUS]"}
LUNGIME_COPIE = 12
INTERVAL_MINUTE = 10
PRIMUL_MINUT_DIN_DISCUTIE = 2  # Minutes 0-1 hold the teaser and the sponsor mark.
FORMA_INTERZISA = re.compile("s\u00e2nt", re.IGNORECASE)
ETICHETA_RELEVANTA = re.compile(r"^(acum|mai târziu|nu):\s*\S")
FORMAT_MINUT = re.compile(r"^(\d{1,2}):00$")
SEPARATOR = re.compile(r"^[\s|:-]+$")


def _cuvinte(text):
    """Lowercase words without diacritics, ignoring block stamps, labels and speaker marks."""
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"&(amp;)?gt;|>", " ", text)
    fara_diacritice = "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )
    return re.findall(r"\w+", fara_diacritice.lower())


def _secvente(cuvinte):
    return {
        tuple(cuvinte[i : i + LUNGIME_COPIE])
        for i in range(len(cuvinte) - LUNGIME_COPIE + 1)
    }


def _sectiuni(fisa):
    """Return (heading, rows) pairs for each `## ` section, without table header lines."""
    sectiuni = []
    for linie in fisa.splitlines():
        linie = linie.strip()
        if linie.startswith("## "):
            sectiuni.append((linie[3:].strip(), []))
        elif sectiuni and linie.startswith("|") and not SEPARATOR.match(linie):
            if not linie.startswith("| Minut |"):
                sectiuni[-1][1].append(linie)
    return sectiuni


def verifica(fisa, transcriere, durata_minute, categorii=None):
    erori = []
    sectiuni = _sectiuni(fisa)
    if [titlu for titlu, _ in sectiuni] != (categorii or CATEGORII):
        erori.append("categorii lipsă sau în altă ordine decât cea din design")

    if FORMA_INTERZISA.search(fisa):
        erori.append("text scris cu varianta interzisă: se scrie „sunt”")

    secvente_transcriere = _secvente(_cuvinte(transcriere))
    minute_folosite = set()

    for titlu, randuri in sectiuni:
        for rand in randuri:
            celule = [c.strip() for c in rand.strip().strip("|").split("|")]
            if len(celule) != 5:
                erori.append(f"{titlu}: rândul nu are cinci coloane: {rand}")
                continue
            minut, sursa, ideea, context, pentru_noi = celule

            potrivire = FORMAT_MINUT.match(minut)
            if not potrivire or f"[{int(potrivire.group(1)) // 60}:{int(potrivire.group(1)) % 60:02d}:00]" not in transcriere:
                erori.append(f"{titlu}: minut fără bloc în transcriere: {minut}")
            elif sursa == "[SPUS]" and int(potrivire.group(1)) >= PRIMUL_MINUT_DIN_DISCUTIE:
                minute_folosite.add(int(potrivire.group(1)))

            if sursa not in SURSE:
                erori.append(f"{titlu}: sursă necunoscută: {sursa}")
            if not ideea or not context:
                erori.append(f"{titlu}: rând cu Ideea sau Context gol: {rand}")
            if not ETICHETA_RELEVANTA.match(pentru_noi):
                erori.append(f"{titlu}: coloana Pentru noi fără etichetă sau motiv: {pentru_noi}")

            for celula in (ideea, context, pentru_noi):
                if _secvente(_cuvinte(celula)) & secvente_transcriere:
                    erori.append(f"{titlu}: text copiat din transcriere: {celula}")

    for start in range(0, durata_minute, INTERVAL_MINUTE):
        if not any(start <= m < start + INTERVAL_MINUTE for m in minute_folosite):
            erori.append(f"interval {start}–{start + INTERVAL_MINUTE - 1} fără nicio idee")

    return erori


def main(argv):
    if len(argv) not in (4, 5):
        print(__doc__)
        return 2
    categorii = None
    if len(argv) == 5:
        import json
        with open(argv[4], encoding="utf-8") as f:
            categorii = json.load(f).get("categorii") or None
    with open(argv[1], encoding="utf-8") as f:
        fisa = f.read()
    with open(argv[2], encoding="utf-8") as f:
        transcriere = f.read()
    erori = verifica(fisa, transcriere, int(argv[3]), categorii)
    for eroare in erori:
        print(eroare)
    print(f"{len(erori)} erori")
    return 1 if erori else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

# Creator kit: skill-uri Claude pentru conținut, pe Mac

Un set de skill-uri și pluginuri pentru aplicația Claude, ales pentru conținut: prezentări, clipuri video pentru social media, postări, brand. Pregătit de Doru Maican pentru colegi.

Durează cam 15 minute. La final ai în aplicația Claude, în tab-ul **Code**, câteva sute de skill-uri noi. Ce face fiecare și pe care să le folosești primele: [CATALOG.md](CATALOG.md). Rezumatul pe o pagină (unelte, spațiu pe disc, conectări) e în [creator-kit.html](creator-kit.html): descarcă-l și deschide-l în browser.

## Ce îți trebuie

- un Mac cu macOS la zi;
- un cont Claude plătit (Pro sau Max), pentru tab-ul Code din aplicația desktop;
- spațiu pe disc: tot kitul ocupă în jur de 6 GB după prima folosire, din care 1,9 GB sunt modelele de transcriere și 0,8 GB cache-uri care se pot șterge. Fără claude-shorts și AirTime ocupă în jur de 0,5 GB. Recomandat: 8 GB liberi;
- acces de administrator pe Mac, pentru instalarea uneltelor de bază.

## Instalare rapidă

Deschide aplicația **Terminal** (Cmd+Space, scrie „Terminal”, Enter), lipește comanda de mai jos și apasă Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)"
```

La pornire scriptul arată lista cu cele 13 unelte, cu ce ai deja marcat, și întreabă:

```
Instalez [T]oate (doar ce lipsește) sau [A]leg eu? (T/a):
```

Enter instalează tot ce lipsește. `a` te lasă să scrii doar numerele dorite, de exemplu `1 3 11 13`. Poți rula comanda din nou oricând, ca să adaugi ce ai sărit.

Fără întrebări: adaugi la sfârșitul comenzii `-- --toate` sau `-- --doar "1 3 13"`.

### Fără dubluri

Înainte să instaleze ceva, scriptul se uită ce ai deja în Claude: pluginuri, skill-uri, agenți, pluginurile din cont și din Cowork, serverele MCP. Apoi:

- un skill din kit pe care îl ai deja, sub orice nume de plugin, nu se mai instalează (în meniu vezi de exemplu „lipsesc 11 din 14”);
- un plugin pe care îl ai deja e sărit; dacă vine din acest kit, doar se actualizează;
- un pachet mare care conține câteva skill-uri pe care le ai deja (de exemplu `design` și `ecc` au amândouă `design-system`) îți arată care sunt și te întreabă `(d/N)`. Enter înseamnă nu: pachetul e sărit. Dacă scriptul rulează fără Terminal în care să întrebe, sare peste el;
- serverul de transcriere YouTube se instalează doar dacă nu ai deja unul.

Scriptul face singur tot ce lipsește pentru ce ai ales:

1. **Unelte Apple** (`git`, `python3`): dacă lipsesc, deschide fereastra de instalare. Apeși **Install**, aștepți, apoi rulezi din nou aceeași comandă.
2. **Homebrew, Node.js, ffmpeg, uv și yt-dlp**: le instalează doar dacă lipsesc și doar dacă le cere ce ai ales (ecc, remotion-skills și claude-shorts cer Node și ffmpeg; serverul de transcriere cere uv; podcast-insights cere yt-dlp). Homebrew îți cere o dată parola de Mac.
3. **Aplicația Claude**: o instalează dacă lipsește. Atunci scriptul se oprește și îți cere să o deschizi, să intri în cont (Pro sau Max) și să deschizi o dată tab-ul **Code**. Apoi rulezi din nou aceeași comandă.
4. **Pluginurile alese** din tabelul de mai jos.
5. **claude-shorts**, dacă l-ai ales, cu uneltele lui de transcriere și randare (aproximativ 1,3 GB, un minut sau două).
6. **Serverul MCP `youtube-transcript`**, dacă l-ai ales: Claude poate citi transcrierea oricărui clip YouTube, fără cheie API.
7. **Reglajul pluginului `ecc`**, dacă l-ai instalat acum.

Comanda e sigură la rulări repetate: ce vine din kit doar se actualizează, iar ce ai din altă parte nu se dublează. Durează în total 5–15 minute, în funcție de internet.

Fiecare rând trebuie să se termine cu ✔. Un `!` galben e un avertisment. Un `✘` roșu e o eroare: rulezi din nou comanda, iar dacă rămâne, trimiți mai departe textul de pe linia respectivă.

Dacă nu vrei ca scriptul să instaleze Homebrew, Node sau ffmpeg, descarcă-l și rulează-l cu `--fara-unelte`.

### Ce instalează

| Plugin | Pentru ce |
|---|---|
| `creator-skills` | 15 skill-uri, fiecare instalat separat (14 din acest repo, plus `browser-harness` de la browser-use, MIT): humanizer, brandkit, teme pentru prezentări, prompt-master, **prompt-flow** (la prima cerere de lucru îți arată promptul optimizat și pornește doar după ce aprobi), NotebookLM, **social-seo** (descrieri și titluri găsite în căutare pe Instagram, YouTube, Shorts) **podcast-insights** (fișă de idei verificabile din podcasturi) și **browser-harness** (Claude lucrează într-un browser real, pe sesiunea ta deschisă) |
| `ecc` | montaj video, clipuri din cod (Remotion), prezentări HTML animate, sistem de conținut pe rețele |
| `marketing` | postări, campanii, secvențe email, analiza concurenței (`competitive-brief`), audit SEO (Anthropic) |
| `design` | feedback pe design-uri (Anthropic) |
| `brand-voice` | ghid de ton al brandului tău și verificarea textelor după el (Anthropic) |
| `canva` | creează, editează și redimensionează design-uri direct în contul tău Canva |
| `superpowers` | metodă de lucru: înainte de un proiect mai mare îți pune întrebări, face un plan și apoi îl execută pas cu pas |
| `remotion-skills` | 13 skill-uri oficiale Remotion pentru clipuri făcute din cod: intro-uri, text animat, subtitrări, randare |
| `workout-program-designer` | programe de antrenament personalizate: obiectiv, progresie, zile de pauză, acasă sau la sală, săptămâni de descărcare |
| `claude-shorts` (skill separat) | dintr-un video lung găsește momentele bune, le taie vertical pentru Reels, TikTok și Shorts și pune subtitrări animate |
| `marketingskills` | 4 skill-uri din [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT): `social` (ce postezi, formate, scripturi de reels, calendar), `video`, `content-strategy`, `copy-editing` |
| `youtube-transcript` (server MCP) | transcrierea și informațiile oricărui clip YouTube, fără cheie API ([jkawamoto/mcp-youtube-transcript](https://github.com/jkawamoto/mcp-youtube-transcript), MIT) |
| `airtime` | dintr-un singur clip filmat de tine: propunere de montaj, video YouTube programat și 3-5 reels Instagram programate. Vezi [AirTime](#airtime) |

## AirTime

AirTime ia un clip și îți propune un montaj, un titlu cu descriere și capitole pentru YouTube, plus 3-5 reels pentru Instagram. Nu se taie, nu se urcă și nu se programează nimic până nu scrii „da” sau „confirm” la tabelul final.

### Instalare dintr-o comandă

AirTime e ultimul din listă (numărul 13). Scriptul îl instalează împreună cu tot ce are nevoie: `social-seo`, `brandkit` și `browser-harness` (numai aceste trei skill-uri din `creator-skills`), `ecc`, `marketing`, `brand-voice`, `remotion-skills` și `claude-shorts`, plus un mediu Python și șablonul de intro în `~/.airtime`. Ce ai deja nu se instalează a doua oară.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)" -- --doar "14"
```

### Conectarea, o singură dată

În Claude, tab-ul Code, scrii „AirTime conectare” și Claude te duce pas cu pas:

1. **YouTube:** o cheie Google personală, cam 20 de minute.
2. **Instagram:** cont Creator, extensia Claude in Chrome și login în Business Suite, cam 10 minute.
3. **Facebook:** opțional, doar dacă vrei să legi și o Pagină.

Detaliile, cu ce să faci dacă un buton are alt nume, sunt în [AIRTIME-INSTALL.md](AIRTIME-INSTALL.md).

### AirTime check

Scrii „AirTime check” și primești o listă cu ✔ sau ✘ pentru fiecare unealtă (ffmpeg, node, mediul Python, claude-shorts, conectarea la YouTube și Instagram). La ✘ vezi ce lipsește și unde e explicat. Din Terminal, `--check` pe scriptul de instalare arată același bloc „AirTime:” când pluginul e instalat.

## După instalare: repornește aplicația

Închide aplicația Claude complet, cu **Cmd+Q**; o fereastră închisă nu ajunge. Apoi deschide-o din nou. Un chat nou nu încarcă pluginurile noi, doar repornirea completă.

## Verifică

În Terminal:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)" -- --check
```

Fiecare unealtă pe care ai ales-o trebuie să aibă ✔. Ce n-ai ales apare cu „neinstalat”.

În aplicație, în tab-ul Code, scrie `/` și caută `humanizer` sau `video-editing`. Dacă apar în listă, instalarea a mers.

## Conectează Canva

Pluginul `canva` lucrează direct în contul tău Canva. Prima dată când îi ceri ceva legat de Canva, Claude îți cere să autorizezi conexiunea; urmezi pașii din fereastra Canva care se deschide. Fără autorizare, celelalte skill-uri merg normal, doar cele de Canva nu.

## Cum îl folosești

Nu trebuie să știi numele skill-urilor. Scrie ce vrei, în română, și Claude alege singur skill-ul potrivit. Câteva exemple de pornire:

- „Fă-mi o prezentare de 10 slide-uri pentru un workshop de mobilitate pentru alergători, cu ton prietenos.”
- „Am un clip de 4 minute cu un antrenament de forță, în ~/Movies/forta.mov. Taie-l în 3 reels de câte 30 de secunde, cu subtitrări.”
- „Scrie-mi 5 postări de Instagram pentru o provocare de 30 de zile, plus captions și hashtag-uri.”
- „Ia textul ăsta și scoate-i tonul de AI.” (skill-ul `humanizer`)
- „Redimensionează designul meu din Canva pentru Story, Reel și postare pătrată.”

Dacă vrei un skill anume, îl chemi cu `/` și numele lui, de exemplu `/ecc:video-editing` sau `/humanizer:humanizer` (skill-urile din kit au fiecare pluginul lor, cu același nume).

Mai multe exemple, pe categorii, sunt în [CATALOG.md](CATALOG.md).

## Actualizări

Când apar skill-uri noi în kit, rulezi din nou comanda de instalare rapidă.

apoi repornești aplicația cu Cmd+Q. Scriptul actualizează ce ai deja și nu șterge nimic.

## Probleme frecvente

| Ce vezi | Ce faci |
|---|---|
| „Nu găsesc Claude” | Deschide aplicația, intră o dată în tab-ul Code, apoi rulează din nou scriptul. |
| „Lipsește git” | Rulează `xcode-select --install`, așteaptă să termine, apoi rulează din nou scriptul. |
| Skill-urile nu apar după instalare | Nu ai închis aplicația cu Cmd+Q. Închide-o complet și deschide-o din nou. |
| Claude îți cere „facts” înainte să scrie un fișier | E un hook al pluginului `ecc`, oprit de script în `settings.json`. Repornește aplicația; dacă tot apare, spune-i lui Doru. |
| Skill-ul de video spune că lipsește `ffmpeg` | Instalează-l cu `brew install ffmpeg` (vezi pasul 2). |
| „… conține skill-uri sau agenți pe care îi ai deja” | Scriptul nu dublează nimic fără acordul tău. Enter sare peste pachet; `d` îl instalează oricum. |
| Lângă `creator-skills` scrie „lipsesc 12 din 15” | Ai deja 3 dintre skill-uri din altă parte. Se instalează doar cele 12 care lipsesc. |

## Ce e în repo

| Fișier | Rol |
|---|---|
| `setup-mac.sh` | instalarea și actualizarea, descrise mai sus |
| `airtime/`, `AIRTIME-INSTALL.md` | pluginul AirTime și ghidul lui de instalare și conectare |
| `CATALOG.md` | ce să folosești pentru prezentări, video și postări, cu exemple |
| `CATALOG-COMPLET.md` | fiecare skill, agent și comandă instalată, generat automat |
| `creator-skills/` | cele 14 skill-uri, câte un folder fiecare; fiecare folder e un plugin separat în `.claude-plugin/marketplace.json` |
| `skills.txt`, `tools/sync-skills.sh` | pentru Doru: lista skill-urilor și copierea lor din repoul lui personal |
| `tools/genereaza-catalog.py` | pentru Doru: regenerează `CATALOG-COMPLET.md` |

## Pentru Doru: actualizarea kitului

```bash
bash tools/sync-skills.sh
```

Copiază din `~/claude-code-sync/obsydia-skills/skills/` skill-urile din `skills.txt` în `creator-skills/<nume>/`, fără să modifice nimic acolo, și mărește versiunea marketplace-ului. `social-seo` și `podcast-insights` sunt ale kitului și rămân neatinse. Un skill nou adăugat în `skills.txt` are nevoie și de o intrare în `marketplace.json` (scriptul te anunță). Apoi refaci catalogul dintr-o instalare de test, izolată de contul tău, și publici:

```bash
mkdir -p /tmp/test-claude/app && CLAUDE_CONFIG_DIR=/tmp/test-claude CREATOR_KIT_APP_DIR=/tmp/test-claude/app CREATOR_KIT_SOURCE="$PWD" bash setup-mac.sh --toate && CLAUDE_CONFIG_DIR=/tmp/test-claude python3 tools/genereaza-catalog.py
```

```bash
git add -A && git commit -m "Update creator-skills" && git push
```

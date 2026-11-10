# Creator kit: skill-uri Claude pentru conținut, pe Mac

Un set de skill-uri și pluginuri pentru aplicația Claude, ales pentru conținut: prezentări, clipuri video pentru social media, postări, brand. Pregătit de Doru Maican pentru colegi.

Durează cam 15 minute. La final ai în aplicația Claude, în tab-ul **Code**, câteva sute de skill-uri noi. Ce face fiecare și pe care să le folosești primele: [CATALOG.md](CATALOG.md).

## Ce îți trebuie

- un Mac cu macOS la zi;
- un cont Claude plătit (Pro sau Max), pentru tab-ul Code din aplicația desktop;
- 2–3 GB liberi pe disc;
- acces de administrator pe Mac, pentru instalarea uneltelor de bază.

## Pasul 1. Aplicația Claude

1. Descarcă aplicația de pe <https://claude.ai/download> și instaleaz-o.
2. Deschide-o, intră în cont, apoi deschide o dată tab-ul **Code**. La prima deschidere aplicația își descarcă motorul Claude Code, iar scriptul de la pasul 4 are nevoie de el.
3. În **Settings → Capabilities**, verifică să fie pornite skill-urile Anthropic (PowerPoint, Word, Excel, PDF). Ele vin cu contul și nu se instalează separat.

## Pasul 2. Uneltele de bază

Deschide aplicația **Terminal** (Cmd+Space, scrie „Terminal”, Enter) și rulează:

```bash
xcode-select --install
```

Apare o fereastră: apasă **Install** și așteaptă să termine. Așa primești `git` și `python3`. Dacă îți spune că sunt deja instalate, treci mai departe.

Apoi instalează **Node.js**, varianta LTS, de pe <https://nodejs.org>, cu installer-ul pentru macOS. Pluginul `ecc`, cel cu skill-urile de video și prezentări, are nevoie de el.

Pentru montaj video și claude-shorts instalează și `ffmpeg`. Ai nevoie întâi de Homebrew; comanda de instalare e pe <https://brew.sh>. După ce ai Homebrew:

```bash
brew install ffmpeg
```

## Pasul 3. Descarcă scriptul de instalare

```bash
curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh -o ~/setup-mac.sh
```

Scriptul e public, în acest repo. Dacă vrei să vezi ce face înainte să-l rulezi, deschide-l cu `open -e ~/setup-mac.sh`. Modifică doar folderul de configurare Claude (`~/.claude`) și face o copie de siguranță a fișierului `settings.json` înainte să-l atingă.

## Pasul 4. Rulează instalarea

```bash
bash ~/setup-mac.sh
```

Scriptul instalează:

| Plugin | Pentru ce |
|---|---|
| `creator-skills` | 11 skill-uri din acest repo: humanizer, brandkit, teme pentru prezentări, prompt-master, NotebookLM și altele |
| `ecc` | montaj video, clipuri din cod (Remotion), prezentări HTML animate, sistem de conținut pe rețele |
| `marketing` | postări, campanii, secvențe email, analiză concurență (Anthropic) |
| `design` | feedback pe design-uri (Anthropic) |
| `brand-voice` | ghid de ton al brandului tău și verificarea textelor după el (Anthropic) |
| `canva` | creează, editează și redimensionează design-uri direct în contul tău Canva |
| `superpowers` | metodă de lucru: înainte de un proiect mai mare îți pune întrebări, face un plan și apoi îl execută pas cu pas |
| `remotion-skills` | 13 skill-uri oficiale Remotion pentru clipuri făcute din cod: intro-uri, text animat, subtitrări, randare |
| `workout-program-designer` | programe de antrenament personalizate: obiectiv, progresie, zile de pauză, acasă sau la sală, săptămâni de descărcare |
| `postiz` | programează și publică postări pe Instagram, TikTok, Facebook, YouTube și altele. Cere cont Postiz: varianta cloud e plătită, gratuită e doar varianta instalată pe serverul tău |
| `claude-shorts` (skill separat) | dintr-un video lung găsește momentele bune, le taie vertical pentru Reels, TikTok și Shorts și pune subtitrări animate |

claude-shorts își instalează la final uneltele de transcriere și randare (Python și Node, aproximativ 2 GB). Pasul durează câteva minute, o singură dată.

Fiecare rând trebuie să se termine cu ✔. Un `!` galben e doar un avertisment, de obicei pentru `ffmpeg`. Un `✘` roșu e o eroare: rulează scriptul încă o dată, iar dacă rămâne, trimite-i lui Doru textul de pe linia respectivă.

## Pasul 5. Repornește aplicația

Închide aplicația Claude complet, cu **Cmd+Q**; o fereastră închisă nu ajunge. Apoi deschide-o din nou. Un chat nou nu încarcă pluginurile noi, doar repornirea completă.

## Pasul 6. Verifică

În Terminal:

```bash
bash ~/setup-mac.sh --check
```

Trebuie să vezi „Totul e la locul lui.”

În aplicație, în tab-ul Code, scrie `/` și caută `humanizer` sau `video-editing`. Dacă apar în listă, instalarea a mers.

## Pasul 7. Conectează Canva

Pluginul `canva` lucrează direct în contul tău Canva. Prima dată când îi ceri ceva legat de Canva, Claude îți cere să autorizezi conexiunea; urmezi pașii din fereastra Canva care se deschide. Fără autorizare, celelalte skill-uri merg normal, doar cele de Canva nu.

## Cum îl folosești

Nu trebuie să știi numele skill-urilor. Scrie ce vrei, în română, și Claude alege singur skill-ul potrivit. Câteva exemple de pornire:

- „Fă-mi o prezentare de 10 slide-uri pentru un workshop de mobilitate pentru alergători, cu ton prietenos.”
- „Am un clip de 4 minute cu un antrenament de forță, în ~/Movies/forta.mov. Taie-l în 3 reels de câte 30 de secunde, cu subtitrări.”
- „Scrie-mi 5 postări de Instagram pentru o provocare de 30 de zile, plus captions și hashtag-uri.”
- „Ia textul ăsta și scoate-i tonul de AI.” (skill-ul `humanizer`)
- „Redimensionează designul meu din Canva pentru Story, Reel și postare pătrată.”

Dacă vrei un skill anume, îl chemi cu `/` și numele lui, de exemplu `/ecc:video-editing` sau `/creator-skills:humanizer`.

Mai multe exemple, pe categorii, sunt în [CATALOG.md](CATALOG.md).

## Actualizări

Când apar skill-uri noi în kit, rulezi din nou:

```bash
bash ~/setup-mac.sh
```

apoi repornești aplicația cu Cmd+Q. Scriptul actualizează ce ai deja și nu șterge nimic.

## Probleme frecvente

| Ce vezi | Ce faci |
|---|---|
| „Nu găsesc Claude” | Deschide aplicația, intră o dată în tab-ul Code, apoi rulează din nou scriptul. |
| „Lipsește git” | Rulează `xcode-select --install`, așteaptă să termine, apoi rulează din nou scriptul. |
| Skill-urile nu apar după instalare | Nu ai închis aplicația cu Cmd+Q. Închide-o complet și deschide-o din nou. |
| Claude îți cere „facts” înainte să scrie un fișier | E un hook al pluginului `ecc`, oprit de script în `settings.json`. Repornește aplicația; dacă tot apare, spune-i lui Doru. |
| Skill-ul de video spune că lipsește `ffmpeg` | Instalează-l cu `brew install ffmpeg` (vezi pasul 2). |

## Ce e în repo

| Fișier | Rol |
|---|---|
| `setup-mac.sh` | instalarea și actualizarea, descrise mai sus |
| `CATALOG.md` | ce să folosești pentru prezentări, video și postări, cu exemple |
| `CATALOG-COMPLET.md` | fiecare skill, agent și comandă instalată, generat automat |
| `creator-skills/` | pluginul cu cele 11 skill-uri |
| `skills.txt`, `tools/sync-skills.sh` | pentru Doru: lista skill-urilor și copierea lor din repoul lui personal |
| `tools/genereaza-catalog.py` | pentru Doru: regenerează `CATALOG-COMPLET.md` |

## Pentru Doru: actualizarea kitului

```bash
bash tools/sync-skills.sh
```

Copiază din `~/claude-code-sync/obsydia-skills/skills/` skill-urile din `skills.txt`, fără să modifice nimic acolo, și mărește versiunea pluginului. Apoi refaci catalogul dintr-o instalare de test și publici:

```bash
CLAUDE_CONFIG_DIR=/tmp/test-claude bash setup-mac.sh && CLAUDE_CONFIG_DIR=/tmp/test-claude python3 tools/genereaza-catalog.py
```

```bash
git add -A && git commit -m "Update creator-skills" && git push
```

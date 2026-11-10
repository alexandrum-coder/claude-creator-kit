# Creator kit: skill-uri Claude pentru conținut, pe Mac

Un set de skill-uri și pluginuri pentru aplicația Claude, ales pentru conținut: prezentări, clipuri video pentru social media, postări, brand. Pregătit de Doru Maican pentru colegi.

Durează cam 15 minute. La final ai în aplicația Claude, în tab-ul **Code**, câteva sute de skill-uri noi. Ce face fiecare și pe care să le folosești primele: [CATALOG.md](CATALOG.md).

## Ce îți trebuie

- un Mac cu macOS la zi;
- un cont Claude plătit (Pro sau Max), pentru tab-ul Code din aplicația desktop;
- 2–3 GB liberi pe disc;
- acces de administrator pe Mac, pentru instalarea uneltelor de bază.

## Instalare rapidă

Deschide aplicația **Terminal** (Cmd+Space, scrie „Terminal”, Enter), lipește comanda de mai jos și apasă Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)"
```

La pornire scriptul arată lista cu cele 11 unelte și întreabă:

```
Instalez [T]oate sau [A]leg eu? (T/a):
```

Enter instalează tot. `a` te lasă să scrii doar numerele dorite, de exemplu `1 3 6 11`. Poți rula comanda din nou oricând, ca să adaugi ce ai sărit.

Fără întrebări: adaugi la sfârșitul comenzii `-- --toate` sau `-- --doar "1 3 11"`.

Scriptul face singur tot ce lipsește pentru ce ai ales:

1. **Unelte Apple** (`git`, `python3`): dacă lipsesc, deschide fereastra de instalare. Apeși **Install**, aștepți, apoi rulezi din nou aceeași comandă.
2. **Homebrew, Node.js și ffmpeg**: le instalează doar dacă lipsesc și doar dacă le cere ce ai ales (ecc, remotion-skills, claude-shorts). Homebrew îți cere o dată parola de Mac.
3. **Aplicația Claude**: o instalează dacă lipsește. Atunci scriptul se oprește și îți cere să o deschizi, să intri în cont (Pro sau Max) și să deschizi o dată tab-ul **Code**. Apoi rulezi din nou aceeași comandă.
4. **Pluginurile alese** din tabelul de mai jos.
5. **claude-shorts**, dacă l-ai ales, cu uneltele lui de transcriere și randare (aproximativ 1 GB, un minut sau două).
6. **Reglajul pluginului `ecc`**, dacă l-ai ales.

Comanda e sigură la rulări repetate: ce e deja instalat doar se actualizează. Durează în total 5–15 minute, în funcție de internet.

Fiecare rând trebuie să se termine cu ✔. Un `!` galben e un avertisment. Un `✘` roșu e o eroare: rulezi din nou comanda, iar dacă rămâne, trimiți mai departe textul de pe linia respectivă.

Dacă nu vrei ca scriptul să instaleze Homebrew, Node sau ffmpeg, descarcă-l și rulează-l cu `--fara-unelte`.

### Ce instalează

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

## Postiz gratuit, pe Mac

Pluginul `postiz` are nevoie de un server Postiz. Varianta cloud e plătită; varianta gratuită rulează chiar pe Mac:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/postiz-local.sh)" -- install
```

Comanda instalează Colima și Docker cu Homebrew, descarcă Postiz oficial în `~/postiz`, îl pornește și deschide <http://localhost:4007>. Primul cont creat acolo devine administrator. Durează 5–10 minute prima dată.

După o repornire a Mac-ului, aceeași comandă cu `-- start`. Ca să elibereze memoria: `-- stop`. Mai există `-- status` și `-- update`.

De știut înainte:

- **Mac-ul trebuie să fie pornit** la ora programată a postării, cu Postiz pornit. Dacă e închis, postarea nu pleacă.
- **Cere în jur de 6 GB de RAM** cât rulează și 20 GB pe disc. Pe un Mac cu 8 GB merge greu.
- **Fiecare rețea cere o aplicație de dezvoltator** creată de el: Meta pentru Facebook și Instagram, TikTok for Developers, Google pentru YouTube. Cheile lor se trec în `~/postiz/docker-compose.yaml`. Unele rețele acceptă doar adrese `https`, deci pentru ele e nevoie și de un tunel public. Pașii pentru fiecare rețea: [docs.postiz.com/self-host/providers](https://docs.postiz.com/self-host/providers/overview.md).

## După instalare: repornește aplicația

Închide aplicația Claude complet, cu **Cmd+Q**; o fereastră închisă nu ajunge. Apoi deschide-o din nou. Un chat nou nu încarcă pluginurile noi, doar repornirea completă.

## Verifică

În Terminal:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)" -- --check
```

Trebuie să vezi „Totul e la locul lui.”

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

Dacă vrei un skill anume, îl chemi cu `/` și numele lui, de exemplu `/ecc:video-editing` sau `/creator-skills:humanizer`.

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

## Ce e în repo

| Fișier | Rol |
|---|---|
| `setup-mac.sh` | instalarea și actualizarea, descrise mai sus |
| `postiz-local.sh` | Postiz gratuit pe Mac (Colima + Docker) |
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

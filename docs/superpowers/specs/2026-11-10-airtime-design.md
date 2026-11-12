# AirTime: design

Data: 2026-11-10. Repo: `alexandrum-coder/claude-creator-kit`, marketplace `creator-kit`, plugin nou `airtime`.

## De ce

Un coleg al lui Doru, antrenor de fitness, filmează un clip întreg pe MacBook. Vrea ca din acel clip să iasă, fără muncă manuală:

- un video lung pe YouTube, montat și programat;
- 3–5 reels pe Instagram, programate, cu descrieri bune pentru căutare;
- opțional, aceleași reels pe Facebook și ca YouTube Shorts.

Totul trebuie să fie gratuit, fără programatoare plătite. Postiz cloud a fost respins pentru că costă de la 29 $/lună. Postiz local a fost respins pentru că cere aplicații de dezvoltator și Mac-ul pornit la ora postării.

Succes: colegul scrie „AirTime”, dă clipul, răspunde la câteva întrebări și confirmă o listă. Restul se face singur.

## Ținte, non-ținte, anti-ținte

**Ținte**
- Un singur cuvânt de pornire: „AirTime”.
- Conexiunile la YouTube și la Meta se configurează o singură dată.
- Instalarea întreagă merge fără ajutor din afară.

**Non-ținte**
- TikTok, X, LinkedIn.
- Statistici după publicare.
- Montaj creativ fin (color grading, muzică). Rămâne pentru CapCut sau Descript, dacă vrea.
- Postiz.

**Anti-ținte (eșec chiar dacă „merge”)**
- Orice publicare sau programare fără confirmarea explicită a utilizatorului.
- Un flux care cere Mac-ul pornit la ora publicării.
- Chei sau tokenuri puse în repo sau afișate în chat.
- Teste care ating `~/.claude` al lui Doru sau repoul `~/claude-code-sync`.

## Constrângeri

- macOS, bash 3.2, aplicația Claude desktop (tab-ul Code), cont Pro sau Max.
- **YouTube Data API v3.** Din 2026-11-02, istoricul oficial al API-ului spune că urcările din proiecte neauditate nu mai sunt blocate pe privat. Programarea e nativă: `status.privacyStatus=private` plus `status.publishAt`. Cota: 100 de urcări pe zi pentru fiecare proiect. O aplicație OAuth în starea „Testing” dă tokenuri care expiră la 7 zile, deci trebuie trecută în „In production”, fără verificare. La conectare, colegul trece o dată prin ecranul „Google hasn't verified this app”.
- **Instagram.** API-ul nu are programare, doar publicare pe loc. Meta Business Suite programează pe serverele Meta, dar nu are API. De aceea Instagram și Facebook se fac prin browser.
- **Business Suite fără Facebook.** Sursele se contrazic dacă login-ul doar cu Instagram profesional, fără Pagină de Facebook, merge pentru programarea de reels. Se verifică pe contul colegului. Rezerva e un cont Facebook făcut doar pentru Business Suite.
- **Facebook.** Postarea pe Facebook cere o Pagină de Facebook legată în Business Suite.
- **Tipul de cont Instagram.** Contul trebuie să fie profesional, de tip Creator, pentru biblioteca de muzică la reels.
- **claude-shorts** (SHA `a369fad`) se instalează în `$CONF/skills/shorts`. Mediul lui Python e `~/.shorts-skill`. Skill-ul își caută rădăcina în `$HOME/.claude/skills/shorts` și apoi în directorul curent, deci la un profil izolat AirTime îi dă `SHORTS_ROOT` explicit.

## Variante luate în calcul

| Variantă | Ce înseamnă | Pentru | Contra |
|---|---|---|---|
| **A. Hibrid (aleasă de Doru)** | YouTube prin API. Instagram și Facebook prin browser, pe Business Suite. | Programare reală pe ambele platforme, Mac-ul poate fi închis. YouTube merge stabil. | Configurarea Google durează cam 20 de minute. Pasul de Instagram se poate strica dacă Meta schimbă interfața. |
| B. Totul în browser | YouTube Studio și Business Suite, în browser. | Configurare de 5 minute. | Cea mai fragilă variantă. Clipul lung urcă încet prin browser. |
| C. Totul prin API | YouTube API și Instagram API. | Cea mai robustă tehnic. | Cere aplicație Meta for Developers și token de 60 de zile. Pentru programare, Mac-ul trebuie pornit la oră. Prea multă întreținere pentru un singur coach. |

**Browserul, decis de Doru:**
- **Claude in Chrome** e metoda principală.
- **browser-harness** (CDP, cu sesiunile logate din Chrome) e rezerva și se adaugă în kit.
- **browser-use** nu intră: în varianta locală are aceeași expunere ca browser-harness, iar varianta cloud trimite sesiunile la un terț și e plătită.

**Plan B pentru conexiuni: Composio, decis de Doru.** Composio nu e varianta principală. Are integrări pentru YouTube și Instagram, cu autentificarea gestionată de ei, și Doru îl are deja conectat. AirTime îl folosește numai când conexiunea principală nu merge, iar ghidul îl descrie ca rezervă.

De știut despre el:
- **Instagram:** trece tot prin Instagram API, deci publică doar pe loc, fără programare. Pentru programare rămâne Business Suite.
- **Conturi:** colegul ar avea nevoie de cont Composio propriu.
- **Fișierele și tokenurile** trec printr-un terț.
- **Prețul și limitele planului gratuit** sunt de verificat înainte să intre în ghidul colegului. UNVERIFIED.

## Cum funcționează

### Componente

```
airtime/
  .claude-plugin/plugin.json
  skills/airtime/SKILL.md           # pornire: „AirTime”, „AirTime check”, „AirTime conectare”
  skills/airtime/references/
    youtube-metadata.md             # titlu, descriere, capitole, tag-uri
    instagram-seo.md                # reguli de descriere și hashtag-uri
    business-suite.md               # pașii în browser, cu ce trebuie verificat la fiecare
  agents/airtime.md                 # producția, fără interacțiune: montaj, randare, texte
  scripts/
    youtube.py                      # auth, upload, programare, verificare (venv ~/.airtime/venv)
    silences.py                     # tăieturi din transcriere + ffmpeg silencedetect
    check.sh                        # „AirTime check”, folosit și de setup-mac.sh --check
  remotion/                         # șablon: intro, titluri de capitol, grafice
AIRTIME-INSTALL.md                  # în rădăcina repoului
```

**Decizie mea: împărțirea între skill și agent.**
- **Skill-ul** rulează în conversația principală. Pune întrebările, ține confirmarea și publică. Un subagent nu poate cere confirmarea utilizatorului și nu poate rula pasul interactiv din claude-shorts.
- **Agentul `airtime`** face munca lungă, fără întrebări: transcriere, tăieturi, randare Remotion, ciorne de texte. Întoarce căile fișierelor și un rezumat, ca să nu încarce contextul principal.

### Fluxul unei rulări

0. **Verificare.** Rulează `check.sh` în mod rapid. Dacă lipsește o conexiune, se oprește și trimite la `AIRTIME-INSTALL.md`, la secțiunea potrivită.
1. **Primire.** Cere:
   - calea clipului;
   - opțiunile Facebook și YouTube Shorts (implicit, cele salvate în configurație);
   - data clipului lung (propune următoarea zi liberă la ora din configurație).

   Creează folderul `~/AirTime/AAAA-LL-ZZ-<slug>/` pentru toate fișierele rulării.
2. **Transcriere, o singură dată**, cu `transcribe.py` din claude-shorts. Aceeași transcriere servește la tăieturi, la capitole și la reels.
3. **Montaj** (agentul):
   - pauze peste 0,7 s, prin silencedetect plus timpii cuvintelor;
   - greșeli: fraze reluate și începuturi abandonate, detectate din transcriere;
   - rezultatul e o listă de tăieturi; ffmpeg produce `curat.mp4`;
   - Remotion adaugă intro (3–5 s), titluri de capitol și grafice simple (cifre, liste de exerciții), apoi produce `youtube.mp4`;
   - agentul arată un rezumat cu durata înainte și după și numărul de tăieturi.
4. **Texte YouTube:**
   - titlu de cel mult 70 de caractere, cu cuvântul-cheie la început;
   - descriere;
   - capitole calculate pe `youtube.mp4`, după regulile YouTube: primul la `00:00`, minimum 3, fiecare de cel puțin 10 s;
   - 10–15 tag-uri.
5. **Reels** cu claude-shorts, pe `curat.mp4`, fără intro. Pașii lui interactivi rămân: colegul alege 3–5 dintre candidați și stilul subtitrărilor. Primele 2–3 secunde au pe ecran un text de cârlig care conține cuvântul-cheie.
6. **Descrieri Instagram** cu `brand-voice` și `marketing`:
   - cuvântul-cheie apare în prima frază, în textul descrierii și în textul de pe ecran;
   - 3–5 hashtaguri relevante, fără liste lungi;
   - limba din configurație (implicit româna).
7. **Calendar și confirmare.** Un singur tabel cu fiecare element:
   - platforma, fișierul, titlul sau descrierea completă, data și ora;
   - reels-urile sunt implicit în zilele de după clipul lung, câte unul pe zi, la ora din configurație.

   Colegul aprobă tot, modifică ceva sau anulează. Fără „da” explicit nu pleacă nimic. Dacă se schimbă ceva după confirmare, tabelul se arată din nou.
8. **Publicare:**
   - **YouTube:** `youtube.py upload` cu `publishAt`. Scriptul verifică după urcare că `privacyStatus` a rămas `private` cu ora corectă și raportează dacă Google l-a blocat.
   - **YouTube Shorts:** același script, pe fișierele verticale de cel mult 3 minute, cu `#Shorts` în titlu.
   - **Instagram și Facebook:** Claude in Chrome pe `business.facebook.com`. Pentru fiecare reel: Creează reel, urcă fișierul, pune descrierea, bifează Facebook doar dacă a fost ales, apoi Programează la ora confirmată. După programare verifică în Planificator că apare, la ora bună.
   - **Dacă pică pasul din browser,** încearcă o dată cu browser-harness. Dacă pică și așa, se oprește, arată captura de ecran și lasă fișierele și textele gata de pus de mână.
9. **Raport:** linkurile YouTube, lista din Planificator și calea folderului rulării.

### Configurație și secrete

- `~/.airtime/config.json`, scris la prima rulare, prin întrebări:
  - limba;
  - numele canalului;
  - textul de intro;
  - culorile (din `brandkit`, dacă există);
  - orele implicite pentru YouTube și reels;
  - opțiunile implicite Facebook și Shorts;
  - lista de cuvinte-cheie de bază.
- `~/.airtime/google-client.json` și `~/.airtime/youtube-token.json`, cu `chmod 600`. Nu se afișează niciodată în chat.
- Profilul de test e izolat prin `AIRTIME_HOME`. Implicit e `~/.airtime`; în teste e un folder temporar.

### Instalare

- Itemul 12 în `setup-mac.sh`: `airtime`, cu textul „montaj + YouTube + reels Instagram dintr-un singur clip”.
- Când e ales, sunt selectate automat și dependențele: `creator-skills` (pentru browser-harness și brandkit), `ecc`, `marketing`, `brand-voice`, `remotion-skills` și `claude-shorts`, plus node și ffmpeg.
- Merge și `-- --doar "12"`.
- Scriptul mai face:
  - venv-ul `~/.airtime/venv` cu `google-api-python-client` și `google-auth-oauthlib`;
  - `npm install` pentru șablonul Remotion, în `~/.airtime/remotion`;
  - instalarea uneltei browser-harness, după `install.md` din proiectul lui.
- `browser-harness` intră în `skills.txt`, deci în `creator-skills`.
- `setup-mac.sh --check` arată și starea AirTime: dependențele și cele două conexiuni.

### Conexiuni, o singură dată (`AIRTIME-INSTALL.md` și „AirTime conectare”)

- **YouTube, cam 20 de minute.**
  - Scriptul deschide, pe rând, paginile Google Cloud: proiect nou, activarea YouTube Data API v3, ecranul de consimțământ (External, apoi „In production”), clientul OAuth de tip Desktop app.
  - Colegul descarcă JSON-ul, iar scriptul îl găsește în `~/Downloads` și îl mută în `~/.airtime`.
  - Urmează login-ul în browser, cu alegerea canalului.
  - Verificare: scriptul afișează numele canalului.
- **Instagram, cam 10 minute.**
  - În aplicația Instagram trece la cont profesional, de tip Creator (pașii exacți în ghid).
  - Instalează extensia Claude in Chrome și se loghează.
  - Deschide `business.facebook.com`, cu login prin Instagram; dacă nu merge, prin Facebook.
  - Verificare: „AirTime check” deschide Business Suite și confirmă că vede contul și butonul de reel.
- **Facebook, opțional, cam 5 minute.** Leagă Pagina de Facebook în Business Suite. Verificarea e aceeași, cu Pagina în listă.
- **browser-harness, rezervă.** Activezi o dată `chrome://inspect/#remote-debugging`. Ghidul spune clar ce expune și cum se oprește.

### Testare

- Profil izolat:
  - `CLAUDE_CONFIG_DIR` și `AIRTIME_HOME` în scratchpad;
  - `CREATOR_KIT_SOURCE` spre repoul local;
  - rulare cu `--doar "12"`.
- Clip de test generat local: ffmpeg cu fundal de test și audio din `say`, în română, cu pauze și o frază reluată. Durată de 60–90 s.
- Rulare cu `claude -p` pe profilul izolat, până la tabelul de confirmare (pasul 7). Se verifică:
  - tăieturile;
  - `youtube.mp4` cu intro;
  - capitolele valide;
  - 3 reels verticale cu subtitrări;
  - textele;
  - `youtube.py upload --dry-run`, care validează cererea fără să o trimită.
- Fără conexiune reală la Google și la Meta în test. Pasul din browser se testează doar până la deschiderea Business Suite, dacă e disponibil.

## Ce filmează și cine mai folosește AirTime (răspunsurile lui Doru, 2026-11-10)

### Clipurile

**Orientarea și durata**
- De cele mai multe ori filmează vertical, cu telefonul.
- Clipurile pentru YouTube, de 10–15 minute, le filmează și orizontal.
- Un clip are de obicei 15–20 de minute, rar până la 30.

AirTime detectează orientarea și se adaptează:
- **Sursă orizontală:** reels-urile se decupează la 9:16 cu reframe-ul din claude-shorts.
- **Sursă verticală:** reels-urile se taie fără decupare, iar clipul lung urcă pe YouTube așa cum e.
- **Clip vertical de cel mult 3 minute:** AirTime întreabă dacă e direct un reel sau un Short.

**Structura unui clip.** Explicație spre cameră, apoi execuția mișcărilor, apoi reacția de după. În timpul demonstrațiilor se aude lume pe fundal și, uneori, respirația antrenorului. Uneori filmează fără sunet și pune vocea separat, peste imagine.

### Montajul: prudență maximă la pauze

Asta înlocuiește regula de 0,7 s de la pasul 3.
- **Agentul împarte clipul în porțiuni:**
  - **vorbire:** cuvinte în transcriere;
  - **demonstrație:** fără vorbire, cu mișcare în cadru și zgomot de fond.
- **În demonstrații nu se taie nimic.** Tăieturile se propun doar în porțiunile de vorbire (pauze lungi, fraze reluate, începuturi abandonate) și la începutul sau sfârșitul mort al clipului.
- **Nu se taie nimic fără acordul colegului.** Agentul face doar o listă de **sugestii**: momentul, durata, motivul și o imagine din acel moment. Skill-ul arată lista, colegul aprobă, scoate sau mută tăieturi, și abia apoi se randează. Montajul are așadar două etape: propunere, apoi execuție după aprobare.
- **Voce pusă separat.** Pornind, AirTime întreabă dacă vocea e înregistrată separat. Dacă da, nu propune tăieturi după pauzele din vorbire, ci doar la capete și pe mișcarea din imagine.

### Mac-ul colegului

Încă nu se știe ce Mac are. Doru află joi, la instalare.
- `check.sh` face un test de viteză: transcrie 30 de secunde și randează un intro.
- Din rezultat alege modelul de transcriere și spune cât va dura un clip de 20 de minute.

### Conturile colegului

- Are cont Instagram profesional și, poate, Facebook.
- Ghidul are două drumuri pentru Business Suite: cu Instagram și cu Facebook. „AirTime check” confirmă drumul care a mers.

### Folosit și de Doru

Doru va folosi AirTime și pentru RH Frame (fotografie, clipuri din culise) și pentru promovarea Obsydia: clipuri vorbite, mai simple. Accentul rămâne pe fluxul antrenorului.

- **Profiluri.** Configurația are mai multe profiluri, în `~/.airtime/profiles/<nume>.json`. Fiecare profil are:
  - canalul YouTube, cu tokenul lui;
  - contul din Business Suite;
  - limba;
  - brandul;
  - tipul de clip: „demonstrații”, „culise” sau „vorbit”, care reglează cât de prudent e montajul.
- **Pornire.** Varianta simplă e „AirTime”, care folosește profilul implicit. Pentru alt profil: „AirTime rhframe”.
- **Fără conținut privat în kit.** Kitul public nu conține nimic din `rhframe` sau Obsydia. Profilurile lui Doru se creează local, la el.

## Lăsat constructorului

- Pragurile exacte pentru pauze și detecția reluărilor.
- Aspectul intro-ului și al graficelor, în limitele culorilor din configurație.
- Structura internă a scripturilor și formatul fișierelor din folderul rulării.

## Decizii mele, de verificat de Doru

1. Împărțirea între skill, care ține interacțiunea și publicarea, și agent, care face producția.
2. O singură confirmare cu tabelul complet, reafișat la orice schimbare.
3. Reels-urile se scot din clipul curățat, fără intro, nu din clipul brut.
4. Calendarul implicit: un reel pe zi, după clipul lung.
5. Folderele: `~/AirTime/` pentru rulări, `~/.airtime/` pentru configurație și secrete.
6. browser-harness intră în `creator-skills` prin `skills.txt`, iar itemul 12 trage și `creator-skills`.
7. **claude-shorts rămâne nemodificat, la `a369fad`.** AirTime nu trece prin interviul skill-ului. Cheamă direct scripturile lui (`transcribe.py`, `snap_boundaries.py`, `compute_reframe.py`, `remotion/render.mjs`, `export.sh`), cu transcrierea, segmentele și cârligele scrise chiar de AirTime. Așa merg:
   - timpii raportați la `curat.mp4`;
   - cuvântul-cheie în cârlig;
   - curățarea cuvintelor de umplutură din română.

   Alegerea celor 3–5 reels o face colegul, în tabelul AirTime.
8. **Remotion randează doar intro-ul și elementele grafice puse peste video.** ffmpeg le lipește apoi pe `curat.mp4`, fără ca tot clipul lung să treacă prin Remotion. Motivul: timpul de randare pe un MacBook.
9. **Transcrierea folosește un model mai mic dacă clipul e lung.** Pragul și modelul le stabilește testul de viteză de pe Mac-ul colegului.

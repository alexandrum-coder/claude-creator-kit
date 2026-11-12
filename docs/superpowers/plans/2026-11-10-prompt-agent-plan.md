# Plan: prompt-agent (Obsydia și creator kit)

## Obiectiv

La prima cerere de lucru din fiecare sesiune nouă, prompt-agent optimizează automat promptul cu prompt-master și, când e instalat, cu `ecc:prompt-optimizer`. Arată promptul optimizat într-un bloc de cod și pornește lucrul doar după aprobarea explicită. Pentru cererile noi din aceeași sesiune îl pornești manual, cu `/prompt-agent`. După aprobare, promptul ajunge la agentul personal-assistant, dacă e instalat. Există o singură sursă, în `obsydia-skills`. Kitul primește o copie.

## Starea de pornire, verificată pe 2026-11-10

- **Kitul `~/claude-creator-kit`.** v2 e în index, necommitată. `marketplace.json` are versiunea 2.0.0 și 19 pluginuri. Fiecare plugin-skill e declarat cu `strict: false`, `"skills": ["./"]` și nu are `plugin.json`. Vechiul `creator-skills/.claude-plugin/plugin.json` e șters. `prompt-master` e plugin separat (`creator-skills/prompt-master/`, cu `references/`). ecc e opțional în kit. Kitul se folosește în tab-ul Code al aplicației Claude, unde hook-urile din pluginuri funcționează. Folderul `docs/` nu e urmărit de git. În `docs/superpowers/plans/` există deja planul AirTime, al altei sesiuni.
- **Repoul `~/claude-code-sync/obsydia-skills`.** Versiunea 1.5.3, cu folderele `agents/`, `commands/`, `hooks/` și `skills/`.
  - `hooks/hooks.json` are deja un `UserPromptSubmit` care rulează `task_verifier_trigger.py`. Scriptul e în Python, iese mereu cu cod 0, tace la orice eroare și are teste unittest în `hooks/tests/test_trigger.py`. E modelul de urmat.
  - Ultimul commit din repo e `73b2acc`. Fișierul `CLAUDE.md` din rădăcina repoului e modificat și necommitat.
- **`obsydia-skills:add-skill`.** Copiază doar skill-uri (prin `sync-skills-to-plugin.sh`), crește versiunea, apoi rulează `git add -A`, commit și push. Nu se ocupă de agenți și de hook-uri.
- **Alte unelte.** `claude` 2.1.206 e în `~/.local/bin/claude`. ecc 2.0.0 e instalat pe Mac-ul lui Doru, iar `prompt-optimizer` e un skill de doar recomandare, cu ieșire în 5 secțiuni. `prompt-master` din Obsydia are 460 de linii, plus fișierele din `references/`.
- **Regula globală „Prompt Hygiene”** din `~/.claude/CLAUDE.md` se aplică atunci când Claude scrie prompturi. Prompt-agent se aplică promptului scris de utilizator. CLAUDE.md nu se modifică.
- **Contractul cu personal-assistant** e acceptat de cealaltă sesiune. Detaliile sunt în `side-session-notes/.../prompt-agent-handoff-format.md`.

## Decizii

- **D-01. Pornire.** Ales: un hook `UserPromptSubmit` care intervine o singură dată pe sesiune, la prima cerere de lucru. Pentru cererile noi din aceeași sesiune există comanda manuală `/prompt-agent`. Respins: hook-ul la fiecare cerere nouă, pentru că încetinește orice schimbare de subiect și costă tokeni. Respinsă și regula în CLAUDE.md, pentru că e nesigură și nu ajunge în kit.
- **D-02. Ocolire.** Fără prefix de ocolire. Hook-ul lasă să treacă singur prompturile scurte, confirmările și comenzile `/`. Dacă primul mesaj din sesiune e scurt, hook-ul așteaptă prima cerere de lucru. Respins: prefixul „direct:”.
- **D-03. Unde rulează optimizarea.** Ales: în subagentul `prompt-agent`. Conversația principală primește doar promptul final și cel mult 3 întrebări. Respins: rularea în conversație, pentru că ar adăuga 10–12k tokeni în context la fiecare pornire.
- **D-04. Sursa.** Ales: `obsydia-skills` e sursa unică, iar kitul primește o copie. Pe Mac-ul lui Doru rulează doar varianta Obsydia. Respinse: kitul ca sursă și varianta doar în kit.
- **D-05. Predarea.** personal-assistant e agent. După „da”, firul principal cheamă `Agent(subagent_type=<primul agent al cărui nume este exact „personal-assistant” sau se termină în „:personal-assistant”>, prompt=<payload>)`. Payload-ul conține `<prompt-final tinta=… aprobat="da">…</prompt-final>`, plus `<componente-sugerate>`, care e opțional. Dacă agentul lipsește, apelul se sare. Un subagent poate chema alți agenți (testat de sesiunea personal-assistant, până la 3 niveluri), dar nu are AskUserQuestion. Doru a ales varianta A, cu releu prin firul principal, drept cale principală. Varianta B, un folder dedicat cu setarea „agent”, e rezerva. Firul principal citește ultima linie a răspunsului:
  - `STARE: GATA`: arată lui Doru clasificarea și tabelul „Pas | Unealtă | De ce”, exact cum au venit.
  - `STARE: ÎNTREBARE`: pune întrebarea prin AskUserQuestion, cu 2–4 opțiuni.
    - Folosește întotdeauna `multiSelect: true`, chiar și când se așteaptă un singur răspuns, ca Doru să poată bifa o opțiune și să scrie la „Other” în același timp.
    - Întrebarea poate fi și o recomandare de a trece la varianta B, cu costul estimat și motivul. Se tratează ca orice ÎNTREBARE. Dacă Doru alege B, firul principal îi arată comanda `claude --agent <nume>`, pe care o rulează el în terminal, și oprește fluxul A.
    - Adaugă mereu, în același apel, ultima întrebare „Observații extra?”, cu opțiunea „Nu am”. Textul liber vine din câmpul automat „Other”.
    - Atenție: AskUserQuestion cere minimum 2 opțiuni. A doua opțiune rămâne de confirmat cu Doru. Propunerea mea e „Da, scriu la Other”.
    
    Apoi reia același agent cu `SendMessage(to=<agentId>, message=<răspuns>)`. Nu pornește un agent nou. Repetă până primește GATA sau ACȚIUNE.
  - `STARE: ACȚIUNE`: rulează imediat pașii `ACȚIUNE: Skill(<nume>, args=…)`, legați cu →.
  - Gardă (alegerea mea): ACȚIUNE acceptă doar apeluri `Skill(...)`. Orice altă unealtă (Bash, Write, Edit, trimitere) se tratează ca ÎNTREBARE.

  Respins: personal-assistant ca skill, decizia lui Doru.
- **D-06. Compunere, nu copie** (alegerea mea; Doru o poate schimba). Prompt-agent nu conține textul lui prompt-master sau al lui prompt-optimizer. Subagentul le cheamă prin unealta Skill, căutând primul skill al cărui nume se termină în `prompt-master` și, dacă există, `ecc:prompt-optimizer`. Din ieșirea lui prompt-optimizer păstrează doar promptul complet (secțiunea 3) și tabelul de componente (secțiunea 2), acesta din urmă ca `<componente-sugerate>`.
- **D-07. Cine decide „cerere de lucru”** (alegerea mea). Hook-ul face doar un filtru ieftin: sub 5 cuvinte, o listă de confirmări (da, ok, aprob, merge, continuă, go, yes, 1/2/3, A/B), comenzi `/`. Restul îl judecă modelul, prin instrucțiunea injectată: o întrebare de conversație sau un salut nu declanșează optimizarea, iar marcajul sesiunii nu se consumă.
- **D-08. Starea „deja rulat”** (alegerea mea). Un fișier-marcaj pe `session_id`, în `${CLAUDE_PLUGIN_DATA}` sau, dacă variabila lipsește, în `$TMPDIR/prompt-agent/`. Când se reia o sesiune (resume) se păstrează același `session_id`, deci hook-ul nu intervine a doua oară. Se verifică în Faza 1.
  - **Abatere, Faza 3 (2026-11-10), trecută în plan la Faza 7:** marcajul nu îl mai scrie `UserPromptSubmit`. Îl scrie un `PreToolUse` cu matcher `Agent|Task`, când pornește subagentul `prompt-agent` (sau `*:prompt-agent`). Motiv: altfel un salut sau o întrebare, pe care modelul le lasă să treacă (D-07), ar consuma marcajul. Cost: până la prima optimizare, nota de ~60 de tokeni se adaugă la fiecare mesaj de cel puțin 5 cuvinte. Verificat în pilot (Faza 4, scenariile 1–3).

## Ce construim (aceleași fișiere în Obsydia și în kit)

```
prompt-agent/
  skills/prompt-agent/SKILL.md   bucla: subagent, arăt promptul, aștept „da”, predau, pornesc lucrul; tot el e /prompt-agent
  agents/prompt-agent.md         subagentul: cheamă prompt-master (+ prompt-optimizer), întoarce promptul + ≤3 întrebări
  hooks/hooks.json               UserPromptSubmit → prompt_agent_trigger.py
  # Faza 7: hooks.json are și PreToolUse (matcher Agent|Task) → același script, care scrie marcajul (vezi D-08).
  hooks/prompt_agent_trigger.py  filtru + marcaj pe sesiune; iese mereu 0; tace la eroare
  hooks/tests/test_prompt_agent_trigger.py
  README.md                      ce face, cum îl oprești, contractul cu personal-assistant
```

Ieșirea vizibilă pentru utilizator, cerută de regula globală „Text de copiat”: promptul final într-un bloc de cod, apoi o linie „🎯 Țintă · 💡 ce s-a schimbat”, apoi cel mult 3 întrebări.

## Reguli de neîncălcat

1. Testele rulează doar cu `CLAUDE_CONFIG_DIR` în scratchpad. Nu se atinge `~/.claude` și nici `~/.claude.json`.
2. Nu se editează `setup-mac.sh` și `.claude-plugin/marketplace.json` din kit până nu vine mesajul din sesiunea principală că v2 e commitată.
3. Nu se scrie nimic în `~/claude-code-sync` fără acordul explicit al lui Doru, dat la Faza 5.
4. Nu se face niciun commit și niciun push fără acordul lui Doru. `add-skill` face commit și push singur, deci rulează numai după acord.
5. Nu se copiază textul lui prompt-master, prompt-optimizer sau skill-router în prompt-agent.
6. Se scrie „sunt”, niciodată forma cu â.
7. **Politica pentru descoperiri:** un defect găsit pe parcurs se notează la „Descoperiri” și nu se repară.
8. **Condiții de oprire.** Te oprești și raportezi când:
   - un nume intră în coliziune cu un skill, agent sau comandă existentă (`/prompt-agent`);
   - fișierul `hooks.json` din Obsydia nu are forma de mai sus;
   - `CLAUDE.md` din claude-code-sync e încă necommitat când urmează `add-skill`, pentru că `git add -A` l-ar include;
   - o precondiție din Faza 1 pică;
   - apare orice situație pe care planul nu o acoperă.

## Faze

### Faza 1: precondiții (numai citire, plus profilul izolat)
- **Face:**
  - creează profilul izolat și o piață de pluginuri locală în scratchpad;
  - verifică patru lucruri:
    - (a) o intrare `strict: false` cu câmpurile `hooks`, `agents` și `skills` trece de `claude plugin validate`;
    - (b) hook-ul primește `session_id` și `prompt`, iar `CLAUDE_PLUGIN_DATA` există sau nu;
    - (c) un subagent din plugin poate folosi unealta Skill;
    - (d) un skill din plugin apare ca `/prompt-agent`.
- **Produce:** o notă cu rezultatul fiecărei verificări.
- **Verificat prin:** ieșirea comenzilor (validate, un hook de test care scrie intrarea primită, `claude -p` cu rezultatul în `stream-json`). Fiecare ar arăta altfel dacă verificarea ar pica.
- **Punct de control:** raportezi. Dacă (a) sau (c) pică, te oprești și propui o variantă.

### Faza 2: copie de rezervă
- **Face:** salvează SHA-256 pentru `obsydia-skills/hooks/hooks.json`, `obsydia-skills/.claude-plugin/plugin.json` și `claude-creator-kit/.claude-plugin/marketplace.json`, plus `git status` pentru ambele repouri.
- **Verificat prin:** fișierul de hash-uri recitit și comparat.
- **Punct de control:** continui.

### Faza 3: construire în scratchpad (TDD)
- **Face:** scrie mai întâi testele pentru hook, apoi scriptul, apoi agentul, skill-ul și README-ul, toate în `scratchpad/prompt-agent/`.
- **Cazuri de test:**
  - prompt lung la începutul sesiunii: intervine și creează marcajul;
  - același `session_id` a doua oară: nu intervine;
  - „da”, „ok”, „aprob”: nu intervin și nu creează marcaj;
  - `/ceva`: nu intervine;
  - JSON stricat sau gol: iese cu 0 și nu scrie nimic;
  - text cu diacritice;
  - `session_id` lipsă: nu intervine.
- **Verificat prin:** testele, care pică înainte să existe scriptul și trec după. Plus `claude plugin validate`.
- **Punct de control:** continui.

### Faza 4: pilot pe profilul izolat
- **Face:** instalează pluginul din piața locală, în profilul izolat, și rulează trei scenarii:
  - (1) prima cerere lungă: apare promptul optimizat într-un bloc de cod și nu e nicio scriere de fișier înainte de „da”;
  - (2) „aprob”: lucrul pornește pe promptul aprobat, iar apelul spre personal-assistant se sare, pentru că agentul lipsește în profil;
  - (3) a doua cerere lungă în aceeași sesiune: hook-ul nu intervine, iar `/prompt-agent` îl pornește manual.
  - Se repetă scenariul (1) fără ecc, ca să se vadă că merge doar cu prompt-master.
- **Verificat prin:** transcriptul `stream-json`. Prima unealtă după cerere e Agent `prompt-agent` și nu există Write, Edit sau Bash înainte de „aprob”. Marcajul există pe disc după scenariul (1).
- **Punct de control:** te oprești. Îi arăți lui Doru transcriptul și aștepți aprobarea.

### Faza 5: instalarea în Obsydia (numai cu acordul lui Doru)
- **Face:** pune skill-ul prin `obsydia-skills:add-skill`, după ce `CLAUDE.md` din claude-code-sync e commitat sau scos din drum de Doru. Agentul și intrarea în `hooks.json` se adaugă manual, ca al doilea hook `UserPromptSubmit`, lângă cel existent. Versiunea crește la 1.5.4. Commit și push numai după acord.
- **Verificat prin:**
  - diff-ul lui `hooks.json`, care arată un singur bloc nou și blocul existent neatins;
    - *Faza 7:* au intrat două blocuri noi, `UserPromptSubmit` și `PreToolUse Agent|Task` (D-08), cu acordul lui Doru; blocurile task-verifier au rămas neatinse (`df0a397`).
  - `git show --stat`, care conține doar fișierele prompt-agent și bump-ul de versiune;
  - versiunea live raportată de pasul de verificare din `add-skill`.
- **Punct de control:** te oprești și raportezi.

### Faza 6: kitul (numai după mesajul că v2 e commitată)
- **Face:**
  - copiază folderul în `creator-skills/prompt-agent/`;
  - adaugă în `marketplace.json` o intrare `strict: false` cu `skills`, `agents` și `hooks`, în forma validată în Faza 1;
    - *Corecție din Faza 1a, trecută în plan la Faza 7:* intrarea NU are câmpul `hooks`. Forma cale trece de `validate`, dar pluginul nu se încarcă („the file-path and array forms are not yet supported in a marketplace entry”). `hooks/hooks.json` din folderul pluginului e preluat implicit. Verificarea include `claude plugin list` = enabled. Commit `6bb1acf`.
  - adaugă în `setup-mac.sh` o linie, cu nota că prompt-agent instalează și prompt-master;
  - adaugă o linie în `CATALOG.md` și în README.
- **Verificat prin:**
  - `claude plugin validate`;
  - instalare din kit în profilul izolat;
  - `diff -r` între copia din kit și sursa din Obsydia, care trebuie să fie gol.
- **Punct de control:** te oprești. Commit doar cu acordul lui Doru.

### Faza 7: verificare finală și raport
- **Face:** rulează din nou testele și scenariul (1) din Faza 4 pe ambele surse și scrie raportul în notele comune.
- **Verificat prin:** ieșirea testelor și transcripturile.

## Întrebări deschise

- **Î-1. Autentificarea profilului izolat.** Un `CLAUDE_CONFIG_DIR` nou pornește nelogat, iar eu nu pot introduce date de autentificare.
  - Recomandat: Doru rulează o singură dată `CLAUDE_CONFIG_DIR=<scratchpad>/profil claude` și face `/login`. Apoi scenariile rulează automat.
  - Alternativă: fără login, Faza 4 se reduce la testele hook-ului și la validate, iar scenariile cu modelul rămân netestate.
- **Î-2. Suprapunerea personal-assistant cu skill-router.** O decide Doru în sesiunea personal-assistant. Pentru prompt-agent schimbă doar numele căutat, nu planul.

## Descoperiri (notate, nereparate)

- Pasul `git add -A` din `add-skill` ar include orice modificare necommitată din `claude-code-sync`. Acum ar include `CLAUDE.md`. Merită o sarcină separată: `add-skill` să adauge doar căile pluginului.

## Gata când

- testele hook-ului trec;
- `claude plugin validate` trece pentru ambele surse;
- pe profilul izolat, prima cerere lungă primește promptul optimizat, nu există nicio scriere înainte de „aprob”, a doua cerere nu declanșează nimic, iar `/prompt-agent` îl pornește manual;
- copia din kit e identică cu sursa din Obsydia;
- Doru a aprobat fiecare commit.

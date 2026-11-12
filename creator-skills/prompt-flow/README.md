# prompt-flow

Optimizează prima cerere de lucru din fiecare sesiune Claude Code și pornește lucrul doar după ce aprobi promptul.

## Ce face
1. Scrii prima cerere de lucru din sesiune.
2. Hook-ul `UserPromptSubmit` adaugă o notă scurtă. Modelul încarcă skill-ul `prompt-flow`.
3. Subagentul `prompt-agent` rescrie cererea cu `prompt-master` și, dacă e instalat, cu `ecc:prompt-optimizer`. Conversația principală primește doar promptul final și cel mult 3 întrebări.
4. Vezi promptul într-un bloc de cod. Răspunzi „aprob” sau spui ce schimbi.
5. După aprobare, dacă ai agentul `personal-assistant`, promptul îi e predat. Apoi lucrul pornește.

Pentru o cerere nouă în aceeași sesiune: `/prompt-flow <cererea>`.

## Când nu intervine
- mesaje sub 5 cuvinte, confirmări („da”, „ok”, „aprob”) și comenzi `/`;
- saluturi și întrebări de conversație: modelul le lasă să treacă, iar marcajul sesiunii rămâne nefolosit;
- după ce subagentul a rulat o dată în sesiune, inclusiv la reluarea ei (același `session_id`).

## Cum funcționează marcajul
`hooks/prompt_agent_trigger.py` scrie un fișier pe sesiune în `${CLAUDE_PLUGIN_DATA}` (sau în `$TMPDIR/prompt-agent/`) în momentul în care pornește subagentul `prompt-agent` (`PreToolUse`, matcher `Agent|Task`). Până atunci, nota se adaugă la fiecare mesaj de cel puțin 5 cuvinte. Scriptul iese mereu cu cod 0 și tace la orice eroare.

## Cum îl oprești
Dezactivează pluginul: `claude plugin disable obsydia-skills@<piata>`.

## Dependențe
- `prompt-master`, obligatoriu: îl cheamă subagentul.
- `ecc:prompt-optimizer`, opțional.
- `personal-assistant`, opțional: primește promptul aprobat, după contractul `<prompt-final tinta=… aprobat="da">` și `STARE: GATA | ÎNTREBARE | ACȚIUNE`.

## Teste
```bash
python3 -m unittest discover -s hooks/tests
```

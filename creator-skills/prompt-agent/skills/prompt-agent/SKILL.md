---
name: prompt-agent
description: Transformă cererea brută de lucru a utilizatorului într-un prompt final optimizat (prin subagentul prompt-agent, care folosește prompt-master și, dacă e instalat, ecc:prompt-optimizer), îl arată într-un bloc de cod gata de copiat și pornește lucrul doar după aprobarea explicită. Folosește-l când nota hook-ului prompt-agent o cere la prima cerere de lucru din sesiune sau când utilizatorul rulează /prompt-agent pentru o cerere nouă din aceeași sesiune. Nu-l folosi pentru saluturi, întrebări de conversație sau confirmări.
---

# prompt-agent

Lucrul nu pornește înainte de aprobare: fără Write, Edit, Bash, NotebookEdit, fără trimiteri și fără alte efecte. Până atunci sunt permise doar Skill, Agent, AskUserQuestion și SendMessage.

## 1. Cererea
- Chemat de hook: cererea e ultimul mesaj al utilizatorului.
- Chemat ca `/prompt-agent <text>`: cererea e `<text>`. Fără text, cere cererea într-o propoziție și oprește-te.

## 2. Optimizarea, în subagent
Cheamă `Agent` cu `subagent_type` = primul agent disponibil al cărui nume e exact `prompt-agent` sau se termină în `:prompt-agent`. Prompt:

```
<cerere>
…cererea utilizatorului, exact cum a scris-o…
</cerere>
<context>cwd: <directorul de lucru> · tinta implicita: claude-code (sesiunea curenta)</context>
```

Ține minte `agentId` din rezultat. Dacă agentul lipsește, spune asta într-o linie și lucrează pe cererea așa cum e.

## 3. Ce vede utilizatorul
Din răspunsul subagentului arată:
1. conținutul din `<prompt-final>`, într-un bloc de cod `text`, complet, gata de copiat;
2. o linie: `🎯 <tinta> · 💡 <schimbari>`;
3. întrebările din `<intrebari>`, dacă există, și aprobarea.

Întreabă prin AskUserQuestion, când unealta e disponibilă:
- fiecare întrebare cu `multiSelect: true`, 2–4 opțiuni, cea recomandată prima;
- întrebarea de aprobare „Pornesc lucrul pe promptul acesta?”, cu opțiunile „Aprob” și „Schimb ceva”;
- ultima, întrebarea „Observații extra?”, cu opțiunile „Nu am” și „Da, scriu la Other”.

Dacă AskUserQuestion lipsește sau pică, scrie întrebările numerotate, apoi „Răspunde «aprob» ca să pornesc, sau spune ce schimb.”, și încheie tura.

## 4. Răspunsuri și schimbări
- Dacă răspunsurile schimbă promptul, trimite-le aceluiași subagent cu `SendMessage(to=<agentId>)`. Dacă SendMessage nu merge, cheamă din nou `Agent`, cu `<prompt-final>`-ul anterior plus răspunsurile. Apoi revino la pasul 3.
- Aprobarea e un „da” explicit: „aprob”, „da”, „ok”, „go” sau „Aprob” bifat. Un comentariu care doar sună pozitiv nu e aprobare.
- La renunțare („renunț”, „lasă”), oprește-te fără să pornești lucrul.

## 5. Predarea după aprobare (opțională)
Caută un agent disponibil al cărui nume e exact `personal-assistant` sau se termină în `:personal-assistant`. Dacă nu există, sari pasul fără comentariu. Dacă există, cheamă-l o singură dată, cu:

```
<prompt-final tinta="<tinta>" aprobat="da">
…textul aprobat, neschimbat…
</prompt-final>
<componente-sugerate>…doar dacă subagentul le-a trimis…</componente-sugerate>
```

Citește ultima linie a răspunsului:
- `STARE: GATA`: arată răspunsul exact cum a venit, apoi treci la pasul 6.
- `STARE: ÎNTREBARE`: întreabă prin AskUserQuestion, după regulile de la pasul 3 (multiSelect, „Observații extra?” la final). Trimite răspunsul aceluiași agent cu `SendMessage`. Repetă până primești GATA sau ACȚIUNE. Dacă întrebarea recomandă varianta B și utilizatorul o alege, arată-i comanda `claude --agent <nume>`, pe care o rulează el, și oprește-te.
- `STARE: ACȚIUNE`: rulează imediat doar pașii `Skill(...)` enumerați, în ordine. Orice altă unealtă (Bash, Write, Edit, trimitere) se tratează ca ÎNTREBARE și se confirmă întâi cu utilizatorul.

## 6. Pornirea
Lucrează pe promptul aprobat ca și cum utilizatorul tocmai l-ar fi trimis. Regulile globale (CLAUDE.md, permisiuni, confirmări) rămân valabile.

# personal-assistant

Un agent care îți spune ce unealtă să folosești și, când e cazul, o pornește. Primește o cerere aprobată, de obicei de la prompt-flow, și o duce pe unul dintre trei drumuri:

| Cererea | Ce face |
|---|---|
| un clip video de editat și publicat | pornește AirTime (`ACȚIUNE: Skill(airtime…)`); dacă AirTime lipsește, îți dă un flux de rezervă |
| un site, o aplicație, un script | pornește `superpowers:using-superpowers`, apoi `plan-taskmanager`, care scrie planul; se oprește la plan și îți sugerează skill-urile înrudite |
| orice altceva | un tabel de 3–5 unelte, în ordine, cu motivul fiecăreia |

Agentul nu face el munca: nu scrie fișiere, nu trimite, nu publică.

## Cum vorbește cu tine

Agentul rulează ca subagent și nu poate pune singur întrebări. Ultima linie a răspunsului îi spune conversației principale ce să facă:

- `STARE: GATA`: îți arată rezultatul.
- `STARE: ÎNTREBARE`: îți pune întrebările cu bife. Poți bifa mai multe opțiuni și să scrii la „Other” în același timp. La final apare mereu „Observații extra?”. Răspunsul tău ajunge la același agent, care continuă de unde a rămas.
- `STARE: ACȚIUNE`: conversația principală pornește imediat skill-urile din linia `ACȚIUNE:`. Acolo pot apărea doar skill-uri. Orice altceva devine întrebare.

## Varianta B, în terminal

Când cererea pare o discuție lungă, cu multe runde de întrebări, agentul îți recomandă să vorbești direct cu el, într-o sesiune separată, și îți spune de ce:

```bash
claude --agent personal-assistant:personal-assistant
```

În varianta asta pune întrebările direct. Pașii de execuție ți-i dă ca text gata de copiat într-o sesiune obișnuită.

## Inventarul

`scripts/inventar.py` citește tot ce are Claude pe Mac:
- pluginurile instalate și cele de cont sau Cowork;
- skill-urile și agenții separați;
- skill-urile Anthropic din cont;
- serverele MCP, doar după nume, fără comenzi, adrese sau chei.

```bash
python3 scripts/inventar.py --cauta clip youtube reels   # cele mai potrivite unelte
python3 scripts/inventar.py --json                        # tot, cu descrieri
python3 scripts/inventar.py --chei                        # formatul folosit de setup-mac.sh
```

Rezultatul e ținut în cache, în `~/.claude/personal-assistant/inventar.json`, și se reface singur când se schimbă ceva. Cu `--fara-cache`, scriptul nu scrie nimic.

Testele, pe date sintetice, fără să atingă `~/.claude`:

```bash
python3 scripts/test_inventar.py
```

## Reguli

- `references/reguli.md`: semnalele de clasificare, fluxurile de rezervă și pragurile de cost. Vine cu kitul.
- `~/.claude/personal-assistant/reguli-locale.md`: regulile tale, opțional. Câștigă la conflict și nu se suprascrie la actualizare.

## Fișiere

```
agents/personal-assistant.md   agentul
references/reguli.md           regulile de rutare
scripts/inventar.py            inventarul, cu cache
scripts/test_inventar.py       testele inventarului
```

# Reguli de rutare: personal-assistant

Le citește agentul la fiecare pornire. Ce e aici se poate schimba fără să atingi agentul. Regulile personale ale unui Mac stau în `$CONF/personal-assistant/reguli-locale.md`, care nu e în kit și câștigă la conflict.

## 0. Nume și inventar gol

- **Nume complete:** orice skill sau agent se scrie cu numele complet, exact cum apare în lista ta, `plugin:nume`. De exemplu `obsydia-skills:wordpress-master`, nu `wordpress-master (agent)`. Tipul îl poți adăuga după nume, în paranteză: `obsydia-skills:wordpress-master (agent)`. Fără prefix rămân doar skill-urile și agenții separați, care nu au plugin.
- **Inventar gol:** dacă `inventar.py --cauta` întoarce „Nicio potrivire” sau prea puțin, mai încerci cel mult o dată, cu alte cuvinte-cheie. Apoi lucrezi numai cu lista din contextul tău și spui într-un rând că inventarul nu a ajutat. Nu ghicești nume.

## 1. Semnale de clasificare

| Clasă | Semnale | Exemple |
|---|---|---|
| clip | un fișier video (`.mp4`, `.mov`) sau o înregistrare; montaj, tăieturi, subtitrări, capitole; publicare pe YouTube, Reels, Shorts, Facebook | „am un clip de 40 de minute, fă din el un video pentru YouTube și 3 reels” |
| IT | construiești sau schimbi cod sau un sistem: site, aplicație, plugin, script, API, bază de date, automatizare, deploy, bug | „vreau un site de prezentare pentru sală, cu programări online” |
| altceva | conținut, marketing, documente, prezentări, cercetare, design fără cod, organizare | „plan de campanie pentru o provocare de 30 de zile” |

Cazuri de graniță:
- Un clip **generat din cod** (Remotion, animații) fără un video de pornire e „altceva”, nu clip.
- Un site **fără cod**, doar texte sau mockup, e „altceva”. Dacă se și construiește, e IT.
- Când cererea are și o parte de clip, și una de IT, pui o ÎNTREBARE: ce intră prima.

## 2. Clip fără AirTime: fluxul de rezervă

Pentru fiecare rând, cauți în inventar numele exact al uneltei. Rândurile pentru care nu găsești nimic le sari.

| Pas | Ce cauți | De ce |
|---|---|---|
| 1 | `video-editing` (de exemplu `ecc:video-editing`) | tăieturi, structură, subtitrări |
| 2 | `shorts` (skill separat) sau `videodb` | clipuri verticale scurte din clipul lung |
| 3 | `remotion-video-creation` | intro, titluri, grafice generate din cod |
| 4 | `social-seo` | titlu, descriere și hashtag-uri care se găsesc în căutare |
| 5 | `postiz` (MCP) sau `social-publisher` | programarea postărilor |

## 3. IT: skill-uri înrudite, după stack

Le folosești pentru tabelul „Skill-uri înrudite”. Le verifici în inventar și păstrezi numai ce există.

| Stack sau nevoie | Ce cauți |
|---|---|
| WordPress, Avada, WooCommerce | `wordpress`, `wordpress-pro`, `wordpress-master` (agent), `avada-*` |
| interfață, pagină, aspect | `design-taste-frontend`, `high-end-visual-design`, `impeccable`, `ui-ux-pro-max` |
| React, Next.js, Vue | `react-patterns`, `nextjs-developer`, `vue-patterns` |
| backend, API, bază de date | `api-design`, `backend-patterns`, `postgres-patterns` |
| teste și verificare | `superpowers:test-driven-development`, `superpowers:verification-before-completion` |
| review | `code-reviewer` (agent), `security-review` |
| execuția planului, după aprobare | `superpowers:executing-plans` sau `superpowers:subagent-driven-development` |

## 4. Altceva: puncte de pornire

| Nevoie | Ce cauți |
|---|---|
| postări, captions, campanii | `marketing:*`, `content-engine`, `crosspost`, `social-seo`, `humanizer` |
| prezentări | `pptx`, `frontend-slides`, `theme-factory` |
| documente, PDF, tabele | `docx`, `pdf`, `xlsx` |
| cercetare cu surse | `deep-research`, `market-research` |
| brand și identitate | `brandkit`, `brand-voice`, `brand-discovery` |
| un prompt pentru alt tool | `prompt-master` |

Ultimul pas al unui text care se publică e, de regulă, `humanizer`.

## 5. Nume duplicate

Când același skill apare în mai multe pluginuri (de exemplu `obsydia-skills:x`, `anthropic-skills:x` și `x:x`), alegi copia personală sau din repo (`obsydia-skills`, kitul). Copia din magazinul desktop vine abia după ele. Pluginurile dezactivate le folosești doar dacă nu există altceva și le marchezi.

## 6. Costul: când recomanzi varianta B

Pragurile se aplică numai rundelor tale de întrebări. Când ruta e ACȚIUNE (clip, IT), nu recomanzi B, pentru că întrebările le pune skill-ul pornit.

**Măsurat pe 2026-11-11.** Firul principal și agentul au rulat amândouă pe sonnet, pe un profil de test cu 5 pluginuri. Cifrele vin din `total_cost_usd`.

| Cerere | A (prin firul principal) | B (`claude --agent`) |
|---|---|---|
| clip | 0,44 $ | 0,25 $ |
| IT | 0,50 $ | 0,19 $ |
| marketing | 0,36 $ | 0,25 $ |
| o rundă de întrebări în plus | până la 0,80 $ | nemăsurat |

Bazele diferă între rulări: A-clip include rularea skill-ului AirTime (un ciot), iar celelalte rulări doar rutează. Cei 0,80 $ pentru o rundă includ și încărcarea a două skill-uri, deci sunt o limită de sus.

Cum le folosești:
- **Estimare A:** aproximativ 0,45 $ pentru rutare, plus până la 0,80 $ pentru fiecare rundă de întrebări. La fiecare rundă se reiau și firul principal, și agentul.
- **Estimare B:** aproximativ 0,25 $ la pornire. Runda nu e măsurată; o estimezi la 0,10–0,20 $, pentru că se reia un singur context, și spui că e estimare.
- **Modelul firului principal:** cu opus în firul principal, A costă mai mult decât în tabel. Nemăsurat; o spui.
- **Formularea:** cifrele le dai ca estimări („în jur de …”), nu ca preț.

| Situație | Drum |
|---|---|
| cel mult 2 runde de întrebări, o singură predare (ACȚIUNE sau GATA) | A, fără să întrebi |
| 3 sau mai multe runde probabile, sau o discuție deschisă (strategie, brainstorming lung) | ÎNTREBARE cu recomandarea B |
| Doru a ales deja A sau B în conversația asta | ce a ales, fără să mai întrebi |

Ce pui în motivare:
- La A, fiecare rundă înseamnă o tură a firului principal și o reluare a subagentului.
- La B, conversația e directă și nu există pornirea de rutare, dar pornești o sesiune separată în terminal.

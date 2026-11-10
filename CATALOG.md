# Catalog pentru conținut fitness

Ce primești după instalare ([README.md](README.md)) și pe ce să pui mâna întâi. Lista completă, cu fiecare dintre cele peste 550 de skill-uri, agenți și comenzi, e în [CATALOG-COMPLET.md](CATALOG-COMPLET.md).

## Trei termeni

- **Skill**: un set de instrucțiuni pe care Claude îl încarcă singur când cererea ta se potrivește. Îl poți chema și direct, cu `/plugin:nume`, de exemplu `/ecc:video-editing`.
- **Agent**: un asistent specializat pe care Claude îl pornește în fundal pentru o parte din lucru, de exemplu un copywriter sau un strateg de marketing.
- **Plugin**: un pachet care aduce skill-uri, agenți și comenzi dintr-o singură sursă.

Nu e nevoie să ții minte numele. Scrii în română ce vrei, iar Claude alege skill-ul potrivit.

## Pe nevoi

### Prezentări

| Skill | Ce face | Exemplu de cerere |
|---|---|---|
| `pptx` (vine cu contul) | creează și editează fișiere PowerPoint | „Fă un PowerPoint de 8 slide-uri cu pachetele de abonament pentru sala mea.” |
| `ecc:frontend-slides` | prezentări HTML animate, deschise în browser; convertește și din PPTX | „Fă-mi o prezentare animată pentru workshopul de nutriție de sâmbătă.” |
| `creator-skills:theme-factory` | aplică una din 10 teme vizuale gata făcute pe slide-uri sau documente | „Aplică o temă energică, cu contrast puternic, pe prezentarea de mai sus.” |
| `creator-skills:brandkit` | board de brand: logo, culori, fonturi, identitate vizuală | „Fă-mi un brand kit pentru un studio de antrenament funcțional.” |
| `ecc:google-workspace-ops` | lucrează în Google Slides, Docs și Sheets | „Mută prezentarea în Google Slides și dă-mi linkul.” |
| `pdf`, `docx` (vin cu contul) | ghiduri, programe de antrenament, fișe pentru clienți | „Fă un PDF de 4 pagini cu programul de 6 săptămâni pentru începători.” |

### Clipuri video pentru social media

| Skill | Ce face | Exemplu de cerere |
|---|---|---|
| `ecc:video-editing` | montaj pe filmări reale: tăiere, structură, ritm, subtitrări, export pe formate (folosește `ffmpeg`) | „Taie ~/Movies/antrenament.mov în 3 reels verticale de 30 de secunde, cu subtitrări.” |
| `ecc:remotion-video-creation` | clipuri generate din cod: intro animat, text pe ecran, numărătoare, captions | „Fă-mi un intro de 5 secunde cu logo-ul și textul «Provocarea de 30 de zile».” |
| `ecc:fal-ai-media` | imagini, video și voce generate de AI; cere cont fal.ai | „Generează o imagine de copertă pentru un reel despre mobilitatea șoldului.” |
| `ecc:videodb` | caută momente în înregistrări lungi și le decupează | „Găsește în live-ul de o oră momentele în care explic tehnica la genuflexiune.” |
| `ecc:content-engine` | transformă o filmare sau o idee în conținut pentru TikTok, YouTube Shorts, Reels | „Din clipul ăsta fă-mi un plan de 5 postări pe TikTok și Instagram.” |
| `creator-skills:prompt-master` | scrie prompturi bune pentru unelte video și imagine AI (Runway, Kling, Midjourney) | „Scrie-mi un prompt pentru un clip AI de 5 secunde cu o sală de forță la răsărit.” |

### Postări și texte

| Skill | Ce face | Exemplu de cerere |
|---|---|---|
| `marketing:content-creation` | postări, articole, captions, adaptate pe canal | „Scrie 5 postări de Instagram despre greșelile frecvente la deadlift.” |
| `marketing:draft-content` | ciorne rapide | „Dă-mi 10 idei de hook pentru reels despre slăbit fără dietă drastică.” |
| `marketing:campaign-plan` | plan de campanie: obiectiv, mesaje, calendar, canale | „Plan de campanie pentru lansarea programului de 8 săptămâni, în ianuarie.” |
| `ecc:marketing-campaign` | campanie completă: poziționare, landing page, email, postări, reclame | „Campanie completă pentru provocarea de vară, cu buget mic.” |
| `ecc:crosspost` | aceeași idee, rescrisă pentru fiecare rețea; nu publică nimic singur | „Adaptează postarea asta pentru Instagram, Facebook și LinkedIn.” |
| `creator-skills:humanizer` | scoate tonul de AI din texte | „Fă textul ăsta să sune natural, ca scris de mine.” |
| `brand-voice` (plugin) | învață tonul tău din postările existente, scrie ghidul de ton, verifică textele noi | „Uite 20 din postările mele; extrage-mi ghidul de ton.” |
| `ecc:brand-voice` | profil de stil din textele tale reale, refolosit la postări și mesaje | „Scrie postarea de mâine în stilul meu.” |
| `marketing:email-sequence` | secvențe de email pentru clienți noi sau abonați | „Secvență de 5 emailuri de bun venit pentru membrii noi.” |
| `ecc:article-writing` | articole, ghiduri, newsletter | „Articol de blog despre cât de des să te antrenezi după 40 de ani.” |

### Design vizual și Canva

| Skill | Ce face | Exemplu de cerere |
|---|---|---|
| `canva:resize-for-social-media` | redimensionează un design pentru Story, Reel, postare, copertă | „Fă-mi designul ăsta în toate formatele de Instagram.” |
| `canva:bulk-create` | multe variante dintr-un șablon | „Fă 7 postări din șablonul meu, câte una pentru fiecare exercițiu din listă.” |
| `canva:edit-design` | modifică un design existent | „Schimbă textul și culorile pe flyerul de la sală.” |
| `canva:brand-check` | verifică un design față de regulile brandului | „Verifică dacă flyerul respectă culorile și fonturile mele.” |
| `canva:get-design-feedback`, `canva:implement-feedback` | feedback pe design și aplicarea lui | „Ce aș putea îmbunătăți la coperta asta?” |
| `design:design-critique` | feedback structurat pe orice imagine sau machetă | „Critică postarea asta: se citește bine pe telefon?” |

Skill-urile Canva cer să-ți conectezi contul Canva la prima folosire.

### Strategie, concurență, organizare

| Skill | Ce face |
|---|---|
| `marketing:competitive-brief` | analiza concurenței: alte săli, alți antrenori, ce postează, cum se poziționează |
| `marketing:performance-report` | raport pe rezultatele unei campanii, din cifrele pe care i le dai |
| `marketing:brand-review` | verifică un text sau o campanie față de brand |
| `ecc:market-research` | studiu de piață cu surse |
| `ecc:brand-discovery` | interviu ghidat, în mai multe sesiuni, pentru identitatea brandului |
| `creator-skills:plan-taskmanager` | plan pas cu pas pentru un proiect mai mare, de exemplu lansarea unui program online |
| `creator-skills:skill-router` | când nu știi ce skill să folosești: îl alege el |
| `creator-skills:notebooklm` | lucru cu Google NotebookLM: surse, rezumate, podcast audio din materialele tale |
| `xlsx` (vine cu contul) | tabele: progresul clienților, calorii, buget de campanie |

## Ce aduce fiecare plugin

| Plugin | Sursă | Ce aduce |
|---|---|---|
| `creator-skills` | acest repo | 11 skill-uri, explicate mai jos |
| `ecc` | affaan-m/ecc | peste 300 de skill-uri, 71 de agenți, 98 de comenzi. Cele mai multe sunt pentru programatori; pentru tine contează cele de video, prezentări, conținut și marketing din tabelele de mai sus. Scriptul îi oprește hook-urile de programare care te-ar încurca. |
| `marketing` | Anthropic | 8 skill-uri: brand-review, campaign-plan, competitive-brief, content-creation, draft-content, email-sequence, performance-report, seo-audit |
| `design` | Anthropic | 7 skill-uri; pentru tine contează mai ales `design-critique` |
| `brand-voice` | Anthropic | descoperă tonul brandului din materialele tale, scrie ghidul de ton, verifică textele după el |
| `canva` | Canva | 6 skill-uri: edit-design, bulk-create, resize-for-social-media, brand-check, get-design-feedback, implement-feedback |
| `superpowers` | obra/superpowers | 15 skill-uri de metodă: `brainstorming` (clarifică ideea înainte de lucru), `writing-plans`, `executing-plans`, `verification-before-completion`. La proiectele mai mari, Claude îți pune întâi câteva întrebări, apoi lucrează după un plan. |
| skill-uri Anthropic | vin cu contul Claude | PowerPoint, Word, Excel, PDF, documente, cercetare aprofundată, teme vizuale |

## Skill-urile din `creator-skills`

| Skill | La ce folosește |
|---|---|
| `humanizer` | scoate tiparele de AI din texte |
| `brandkit` | board de brand: logo, paletă, fonturi, identitate |
| `theme-factory` | 10 teme vizuale pentru slide-uri și documente |
| `prompt-master` | prompturi optimizate pentru alte unelte AI (imagine, video, chat) |
| `notebooklm` | lucru cu Google NotebookLM: surse, rezumate, podcast audio |
| `skill-router` | alege skill-ul potrivit când cererea e vagă |
| `plan-taskmanager` | plan de execuție pentru proiecte cu mulți pași |
| `compact-handoff` | salvează starea unei sesiuni lungi înainte de `/compact` |
| `full-output-enforcement` | obligă Claude să livreze textul complet, nu prescurtat |
| `imagegen-frontend-web` | imagini de referință pentru un site |
| `imagegen-frontend-mobile` | imagini de referință pentru o aplicație mobilă |

## Opționale, încă neinstalate de script

Găsite la o căutare din noiembrie 2026. Fiecare cere un cont la serviciul respectiv. Intră în `setup-mac.sh` doar după ce Doru aprobă lista.

| Unealtă | Ce face | Sursă |
|---|---|---|
| Postiz | programează și publică postări pe Instagram, TikTok, Facebook, YouTube, LinkedIn și altele (28+ rețele), cu statistici; are variantă gratuită, pe serverul tău | plugin `postiz` din marketplace-ul Anthropic `knowledge-work-plugins` |
| Adobe for creativity | editare în serie de imagini și video cu Adobe Creative Cloud, adaptare pe formate de rețea | plugin `adobe-for-creativity`, același marketplace |
| HeyGen | video cu avatar, mesaje video personalizate, traducere și dublaj | marketplace `heygen-com/skills` |
| claude-shorts | dintr-un video lung găsește momentele bune, le taie vertical și pune subtitrări animate | GitHub `AgriciDaniel/claude-shorts` (skill, 363★) |
| Remotion skills | regulile oficiale Remotion pentru video generat din cod | GitHub `remotion-dev/skills` (6,7k★); `ecc:remotion-video-creation` acoperă deja partea de bază |

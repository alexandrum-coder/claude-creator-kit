# Catalog pentru conținut fitness

Ce primești după instalare ([README.md](README.md)) și pe ce să pui mâna întâi. Lista completă, cu fiecare dintre cele peste 570 de skill-uri, agenți și comenzi, e în [CATALOG-COMPLET.md](CATALOG-COMPLET.md).

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
| `theme-factory` | aplică una din 10 teme vizuale gata făcute pe slide-uri sau documente | „Aplică o temă energică, cu contrast puternic, pe prezentarea de mai sus.” |
| `brandkit` | board de brand: logo, culori, fonturi, identitate vizuală | „Fă-mi un brand kit pentru un studio de antrenament funcțional.” |
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
| `shorts` (claude-shorts) | din video lung: alege momentele, le taie vertical, pune subtitrări animate, exportă pentru Reels, TikTok, Shorts | „Din antrenamentul de 40 de minute din ~/Movies/live.mp4 fă-mi 5 shorts cu subtitrări.” |
| `remotion-skills:remotion-captions` și restul Remotion | regulile oficiale pentru clipuri din cod, subtitrări, randare | „Fă un clip de 15 secunde cu cele 3 reguli ale genuflexiunii, text animat.” |
| `prompt-master` | scrie prompturi bune pentru unelte video și imagine AI (Runway, Kling, Midjourney) | „Scrie-mi un prompt pentru un clip AI de 5 secunde cu o sală de forță la răsărit.” |

### Postări și texte

| Skill | Ce face | Exemplu de cerere |
|---|---|---|
| `marketing:content-creation` | postări, articole, captions, adaptate pe canal | „Scrie 5 postări de Instagram despre greșelile frecvente la deadlift.” |
| `marketing:draft-content` | ciorne rapide | „Dă-mi 10 idei de hook pentru reels despre slăbit fără dietă drastică.” |
| `marketing:campaign-plan` | plan de campanie: obiectiv, mesaje, calendar, canale | „Plan de campanie pentru lansarea programului de 8 săptămâni, în ianuarie.” |
| `ecc:marketing-campaign` | campanie completă: poziționare, landing page, email, postări, reclame | „Campanie completă pentru provocarea de vară, cu buget mic.” |
| `ecc:crosspost` | aceeași idee, rescrisă pentru fiecare rețea; nu publică nimic singur | „Adaptează postarea asta pentru Instagram, Facebook și LinkedIn.” |
| `humanizer` | scoate tonul de AI din texte | „Fă textul ăsta să sune natural, ca scris de mine.” |
| `brand-voice` (plugin) | învață tonul tău din postările existente, scrie ghidul de ton, verifică textele noi | „Uite 20 din postările mele; extrage-mi ghidul de ton.” |
| `ecc:brand-voice` | profil de stil din textele tale reale, refolosit la postări și mesaje | „Scrie postarea de mâine în stilul meu.” |
| `marketing:email-sequence` | secvențe de email pentru clienți noi sau abonați | „Secvență de 5 emailuri de bun venit pentru membrii noi.” |
| `postiz` | programează și publică postările pe rețele, cu statistici (cont Postiz) | „Programează cele 5 postări pe Instagram, câte una pe zi, la 18:00.” |
| `ecc:article-writing` | articole, ghiduri, newsletter | „Articol de blog despre cât de des să te antrenezi după 40 de ani.” |
| `social-seo` | descrieri care apar în căutare: prima linie, text pe ecran, 3–5 hashtaguri, alt text; pe YouTube titlu, primele 2 rânduri, capitole, tag-uri | „Scrie descrierea pentru reel-ul cu exerciții de abdomen acasă, pentru Instagram și YouTube Shorts, cu SEO.” |
| `social` (marketingskills) | ce postezi și în ce format, scripturi de clipuri scurte, calendar | „Ce să postez săptămâna asta ca antrenor personal în Cluj? Dă-mi 5 idei de reels cu script.” |
| `content-strategy` (marketingskills) | strategia de conținut: teme, piloni, ce publici și de ce | „Fă-mi o strategie de conținut pe 3 luni pentru un studio de pilates.” |
| `copy-editing` (marketingskills) | corectura și îmbunătățirea textelor | „Corectează și strânge textul ăsta de pe pagina de abonamente.” |
| `marketing:competitive-brief` | analiza concurenței: ce comunică, ce prețuri au, unde ai loc | „Compară-mă cu 3 săli din oraș: mesaje, prețuri, ce postează.” |
| `podcast-insights` | din podcast sau interviu de pe YouTube: fișă de idei verificabile, cu minutul fiecăreia | „Fă-mi fișa episodului ăsta: <link YouTube>.” |
| `youtube-transcript` (server MCP) | citește transcrierea oricărui clip YouTube, ca să faci postări din clipuri vechi | „Ia transcrierea clipului meu <link> și scoate din el 5 postări.” |

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
| `workout-program-designer` | programe de antrenament pe obiectiv, cu progresie și săptămâni de descărcare; bun și ca material pentru postări |
| `marketing:competitive-brief` | analiza concurenței: alte săli, alți antrenori, ce postează, cum se poziționează |
| `marketing:performance-report` | raport pe rezultatele unei campanii, din cifrele pe care i le dai |
| `marketing:brand-review` | verifică un text sau o campanie față de brand |
| `ecc:market-research` | studiu de piață cu surse |
| `ecc:brand-discovery` | interviu ghidat, în mai multe sesiuni, pentru identitatea brandului |
| `plan-taskmanager` | plan pas cu pas pentru un proiect mai mare, de exemplu lansarea unui program online |
| `personal-assistant` | când nu știi ce unealtă să folosești: o alege și o pornește (clip la AirTime, site sau aplicație la un plan scris, restul la 3–5 pași) |
| `notebooklm` | lucru cu Google NotebookLM: surse, rezumate, podcast audio din materialele tale |
| `xlsx` (vine cu contul) | tabele: progresul clienților, calorii, buget de campanie |

## Ce aduce fiecare plugin

| Plugin | Sursă | Ce aduce |
|---|---|---|
| `creator-skills` | acest repo | 14 skill-uri, explicate mai jos; fiecare e plugin separat, deci se instalează doar ce lipsește |
| `marketingskills` | coreyhaines31/marketingskills (MIT), legat direct | 4 skill-uri: `social`, `video`, `content-strategy`, `copy-editing` |
| `youtube-transcript` | jkawamoto/mcp-youtube-transcript (MIT) | server MCP: transcrieri și informații despre clipuri YouTube, fără cheie API |
| `ecc` | affaan-m/ecc | peste 300 de skill-uri, 71 de agenți, 98 de comenzi. Cele mai multe sunt pentru programatori; pentru tine contează cele de video, prezentări, conținut și marketing din tabelele de mai sus. Scriptul îi oprește hook-urile de programare care te-ar încurca. |
| `marketing` | Anthropic | 8 skill-uri: brand-review, campaign-plan, competitive-brief, content-creation, draft-content, email-sequence, performance-report, seo-audit |
| `design` | Anthropic | 7 skill-uri; pentru tine contează mai ales `design-critique` |
| `brand-voice` | Anthropic | descoperă tonul brandului din materialele tale, scrie ghidul de ton, verifică textele după el |
| `canva` | Canva | 6 skill-uri: edit-design, bulk-create, resize-for-social-media, brand-check, get-design-feedback, implement-feedback |
| `superpowers` | obra/superpowers | 15 skill-uri de metodă: `brainstorming` (clarifică ideea înainte de lucru), `writing-plans`, `executing-plans`, `verification-before-completion`. La proiectele mai mari, Claude îți pune întâi câteva întrebări, apoi lucrează după un plan. |
| `remotion-skills` | remotion-dev/skills, legat direct, necopiat | 13 skill-uri oficiale Remotion pentru video din cod |
| `workout-program-designer` | OneWave-AI/claude-skills (MIT), legat direct | un skill: programe de antrenament personalizate |
| `postiz` | Postiz, prin catalogul Anthropic | programare și publicare pe 28+ rețele, statistici; cere cont Postiz (cloud plătit sau server propriu gratuit) |
| `claude-shorts` | AgriciDaniel/claude-shorts (MIT), skill separat în `~/.claude/skills/shorts` | reels și shorts verticale din video lung, cu subtitrări animate; își instalează uneltele Python și Node |
| skill-uri Anthropic | vin cu contul Claude | PowerPoint, Word, Excel, PDF, documente, cercetare aprofundată, teme vizuale |

## Skill-urile din `creator-skills`

| Skill | La ce folosește |
|---|---|
| `humanizer` | scoate tiparele de AI din texte |
| `brandkit` | board de brand: logo, paletă, fonturi, identitate |
| `theme-factory` | 10 teme vizuale pentru slide-uri și documente |
| `prompt-master` | prompturi optimizate pentru alte unelte AI (imagine, video, chat) |
| `prompt-agent` | la prima cerere de lucru din sesiune îți arată promptul optimizat (cu prompt-master) și pornește doar după ce aprobi; pentru o cerere nouă scrii `/prompt-agent <cerere>` |
| `notebooklm` | lucru cu Google NotebookLM: surse, rezumate, podcast audio |
| `personal-assistant` | agent: alege și pornește unealta potrivită după ce aprobi promptul |
| `plan-taskmanager` | plan de execuție pentru proiecte cu mulți pași |
| `compact-handoff` | salvează starea unei sesiuni lungi înainte de `/compact` |
| `full-output-enforcement` | obligă Claude să livreze textul complet, nu prescurtat |
| `imagegen-frontend-web` | imagini de referință pentru un site |
| `imagegen-frontend-mobile` | imagini de referință pentru o aplicație mobilă |
| `social-seo` | texte găsite în căutare pe Instagram, YouTube și TikTok |
| `podcast-insights` | fișă de idei verificabile din podcasturi și interviuri, într-o bibliotecă proprie |

## Neincluse, pentru că cer abonament plătit

| Unealtă | Ce face |
|---|---|
| HeyGen (marketplace `heygen-com/skills`) | video cu avatar, mesaje video personalizate, traducere și dublaj |
| Adobe for creativity (catalogul Anthropic) | editare în serie de imagini și video cu Adobe Creative Cloud |

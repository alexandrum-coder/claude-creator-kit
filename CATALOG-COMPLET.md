# Catalog complet: skill-uri, agenți, comenzi

Generat automat pe 2026-11-10 de `tools/genereaza-catalog.py`, dintr-o instalare de test făcută cu `setup-mac.sh`. 7 pluginuri instalate plus skill-urile Anthropic care vin cu contul, 561 elemente. Nu edita de mână: rulează din nou scriptul.

Descrierile sunt ale autorilor, de obicei în engleză. Coloana **Fitness** e completată de mână: ★★★ esențial pentru conținut fitness (prezentări, clipuri, postări), ★★ util, ★ ocazional, gol = irelevant pentru tine. Lista scurtă, explicată în română, e în [CATALOG.md](CATALOG.md).

## Cuprins

| Plugin | Sursă | Cum ajunge la tine | Skill-uri | Agenți | Comenzi | Hook-uri |
|---|---|---|---|---|---|---|
| [anthropic-skills](#anthropic-skills) | cont claude.ai (skill-uri Anthropic) | vine cu contul Claude | 20 | 0 | 0 |  |
| [brand-voice](#brand-voice) | marketplace `knowledge-work-plugins` | instalat de setup-mac.sh | 3 | 5 | 3 |  |
| [canva](#canva) | marketplace `knowledge-work-plugins` | instalat de setup-mac.sh | 6 | 0 | 0 |  |
| [creator-skills](#creator-skills) | marketplace `creator-kit` | instalat de setup-mac.sh | 11 | 0 | 0 |  |
| [design](#design) | marketplace `knowledge-work-plugins` | instalat de setup-mac.sh | 7 | 0 | 0 |  |
| [ecc](#ecc) | marketplace `ecc` | instalat de setup-mac.sh | 314 | 71 | 98 | da |
| [marketing](#marketing) | marketplace `knowledge-work-plugins` | instalat de setup-mac.sh | 8 | 0 | 0 |  |
| [superpowers](#superpowers) | marketplace `superpowers-dev` | instalat de setup-mac.sh | 15 | 0 | 0 | da |

## anthropic-skills

Sursă: cont claude.ai (skill-uri Anthropic).

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| skill | `pptx` | ★★★ | **prezentări PowerPoint (workshop, ofertă abonamente).** Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations as P… |
| skill | `deep-research` | ★★ | **cercetare cu surse (nutriție, studii).** Use this skill when the user's prompt requires (1) researching a topic across multiple sources, comparing options or alternatives, analyzing trends or history, understan… |
| skill | `docs` | ★★ | **documente editabile partajate.** docs (editable docs people share and comment on; the default for any document, named as a doc or not: a document, report, proposal, resume, cover letter, letter, contrac… |
| skill | `docx` | ★★ | **documente Word: programe de antrenament, contracte.** Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx) or Word templates (.dotx). Triggers include: any mention of Microsoft… |
| skill | `pdf` | ★★ | **PDF-uri: ghiduri, planuri, fișe client.** Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into… |
| skill | `theme-factory` | ★★ | **temă vizuală unitară pe slide-uri/documente.** Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that… |
| skill | `xlsx` | ★★ | **tabele: progres clienți, calorii, buget.** Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm… |
| skill | `built-in-browser` |  | Read this skill before the first step that uses the built-in browser, the browser pane inside the Claude desktop app (also called the in-app browser, the browser pane, C… |
| skill | `chrome-browser` |  | Read this skill before the first step that uses Claude in Chrome, the browser extension whose tools are named mcp__claude-in-chrome__* (also called Chrome, the browser e… |
| skill | `computer-use` |  | Read this skill before the first step of any request to do something in an app on the person's own computer (Notes, Finder, System Settings, any desktop app), to look at… |
| skill | `consolidate-memory` |  | Reflective pass over your memory files — merge duplicates, fix stale facts, prune the index. |
| skill | `explain-usage` |  | Explain where this session's tokens went, with one simple chart in plain language. Use when the user says things like "explain my usage", "where did my tokens go", or as… |
| skill | `google-workspace` |  | Read this before the first Google Drive, Docs, Sheets or Slides connector call whenever the task creates or changes a Google file. Use this skill whenever the user wants… |
| skill | `import-memory` |  | Import a memory export from another AI assistant into Claude's memory — conversationally, additively, and with the content treated as data. |
| skill | `mcp-builder` |  | Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building M… |
| skill | `morning` |  | Render the user's morning brief as a styled HTML artifact, or set it up as a recurring weekday task. Use only when the user explicitly asks to run, see, or set up their… |
| skill | `setup-claude` |  | Guided setup — install role-matched plugins, connect your tools, try a skill. |
| skill | `setup-cowork` |  | Guided setup — install role-matched plugins, connect your tools, try a skill. |
| skill | `skill-creator` |  | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing s… |
| skill | `web-artifacts-builder` |  | Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex… |

## brand-voice

Sursă: marketplace `knowledge-work-plugins`, versiunea 1.1.0.

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| agent | `content-generation` | ★★★ | **ghid de ton din materialele existente + verificare.** Generates brand-aligned sales and marketing content by applying brand guidelines to specific content requests. Use this agent for long-form content, batch generation, or… |
| agent | `conversation-analysis` | ★★★ | **ghid de ton din materialele existente + verificare.** Analyzes sales call transcripts to extract brand voice patterns, messaging effectiveness, and tone variations. Use this agent when processing multiple transcripts or per… |
| agent | `discover-brand` | ★★★ | **ghid de ton din materialele existente + verificare.** Autonomously searches enterprise platforms to discover brand-related documents, transcripts, and design assets. Use when the user wants to build brand guidelines but doe… |
| agent | `document-analysis` | ★★★ | **ghid de ton din materialele existente + verificare.** Analyzes brand documents to extract voice attributes, messaging, terminology, and examples. Use this agent when processing multiple brand documents or performing cross-d… |
| agent | `quality-assurance` | ★★★ | **ghid de ton din materialele existente + verificare.** Validates content and brand guidelines against brand standards. Use this agent to check compliance, consistency, completeness, and open question coverage before finalizi… |
| comandă | `discover-brand` | ★★★ | **ghid de ton din materialele existente + verificare.** Search connected platforms for brand materials and produce a discovery report |
| comandă | `enforce-voice` | ★★★ | **ghid de ton din materialele existente + verificare.** Apply brand guidelines to content creation |
| comandă | `generate-guidelines` | ★★★ | **ghid de ton din materialele existente + verificare.** Generate brand voice guidelines from documents, transcripts, discovery reports, or any combination |
| skill | `brand-voice-enforcement` | ★★★ | **ghid de ton din materialele existente + verificare.** This skill applies brand guidelines to content creation. It should be used when the user asks to "write an email", "draft a proposal", "create a pitch deck", "write a Li… |
| skill | `discover-brand` | ★★★ | **ghid de ton din materialele existente + verificare.** This skill orchestrates autonomous discovery of brand materials across enterprise platforms (Notion, Confluence, Google Drive, Box, SharePoint, Figma, Gong, Granola, Sla… |
| skill | `guideline-generation` | ★★★ | **ghid de ton din materialele existente + verificare.** This skill generates, creates, or builds brand voice guidelines from source materials. It should be used when the user asks to "generate brand guidelines", "create a sty… |

## canva

Sursă: marketplace `knowledge-work-plugins`, versiunea 1.0.0.

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| skill | `canva-brand-check` | ★★★ | **creează și redimensionează design-uri în Canva (cont Canva).** Check a Canva design against a brand kit and report where it diverges — off-palette colors, non-brand fonts, logo misuse, and off-tone copy. Read-only; makes no changes.… |
| skill | `canva-bulk-create` | ★★★ | **creează și redimensionează design-uri în Canva (cont Canva).** Bulk-create Canva designs from tabular data using a brand template with autofill fields, producing one design per row. Use when users say "bulk create designs from this… |
| skill | `canva-design-feedback` | ★★★ | **creează și redimensionează design-uri în Canva (cont Canva).** Read a Canva design and return structured, actionable design feedback — visual hierarchy, copy/messaging, layout & spacing, consistency, readability, and accessibility.… |
| skill | `canva-edit-design` | ★★★ | **creează și redimensionează design-uri în Canva (cont Canva).** Make edits to an existing Canva design — change or fix text, replace/insert/delete images and videos, reformat text (size, weight, style, color, alignment, lists, line h… |
| skill | `canva-implement-feedback` | ★★★ | **creează și redimensionează design-uri în Canva (cont Canva).** Implement reviewer feedback on a Canva design. Reads all comment threads, synthesises what reviewers want, makes the clear-cut changes directly, and flags anything that… |
| skill | `canva-resize-for-social-media` | ★★★ | **creează și redimensionează design-uri în Canva (cont Canva).** Resize a Canva design into multiple social media formats (Facebook post, Facebook story, Instagram post, Instagram story, LinkedIn post). Use this skill when users want… |

## creator-skills

Sursă: marketplace `creator-kit`, versiunea 1.0.0.

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| skill | `brandkit` | ★★★ | **board de brand: logo, culori, identitate.** Premium brand-kit image generation skill for creating high-end brand-guidelines boards, logo systems, identity decks, and visual-world presentations. Trained for minimal… |
| skill | `humanizer` | ★★★ | **scoate tonul de AI din texte.** Remove signs of AI-generated writing from text. Use when editing or reviewing text to make it sound more natural and human-written. Based on Wikipedia's comprehensive "S… |
| skill | `notebooklm` | ★★ | **lucru cu NotebookLM (surse, rezumate, podcast).** Complete API for Google NotebookLM - full programmatic access including features not in the web UI. Create notebooks, add sources, generate all artifact types, download… |
| skill | `plan-taskmanager` | ★★ | **plan pas cu pas pentru proiecte mari.** Build a task plan that survives contact with reality — one that gets executed cleanly, in a single pass, with no drift and no rework. Use whenever a plan is being create… |
| skill | `prompt-master` | ★★ | **prompturi pentru Midjourney, video AI, alte unelte.** Generates optimized prompts for AI tools. Activates only when the user explicitly asks to write, fix, improve, or adapt a prompt for a specific AI tool (LLM, Cursor, Mid… |
| skill | `skill-router` | ★★ | **alege singur skill-ul potrivit.** The dispatcher. Fires before answering generically whenever a request is vague, open-ended, situational, or when the operator doesn't know which skill, agent, or plugin… |
| skill | `theme-factory` | ★★ | **teme gata făcute pentru slide-uri.** Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that… |
| skill | `compact-handoff` | ★ | **salvează sesiunea înainte de /compact.** End-of-session ritual that makes compaction safe: distil the session into a verified state summary, write a durable HANDOFF file to disk, refresh project memory, emit a… |
| skill | `imagegen-frontend-mobile` | ★ | **concepte vizuale de aplicație mobilă.** Elite mobile app image-generation skill for creating premium, app-native screen concepts and flows. Designed for iOS, Android, and cross-platform mobile products. Priori… |
| skill | `full-output-enforcement` |  | Overrides default LLM truncation behavior. Enforces complete code generation, bans placeholder patterns, and handles token-limit splits cleanly. Apply to any task requir… |
| skill | `imagegen-frontend-web` |  | Elite frontend image-direction skill for generating premium, conversion-aware website design references. CRITICAL OUTPUT RULE — generate ONE separate horizontal image FO… |

## design

Sursă: marketplace `knowledge-work-plugins`, versiunea 1.2.0.

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| skill | `design-critique` | ★★ | **feedback pe un design (postare, flyer).** Get structured design feedback on usability, hierarchy, and consistency. Trigger with "review this design", "critique this mockup", "what do you think of this screen?",… |
| skill | `ux-copy` | ★ | **texte scurte pentru aplicații/site.** Write or review UX copy — microcopy, error messages, empty states, CTAs. Trigger with "write copy for", "what should this button say?", "review this error message", or w… |
| skill | `accessibility-review` |  | Run a WCAG 2.1 AA accessibility audit on a design or page. Trigger with "audit accessibility", "check a11y", "is this accessible?", or when reviewing a design for color… |
| skill | `design-handoff` |  | Generate developer handoff specs from a design. Use when a design is ready for engineering and needs a spec sheet covering layout, design tokens, component props, intera… |
| skill | `design-system` |  | Audit, document, or extend your design system. Use when checking for naming inconsistencies or hardcoded values across components, writing documentation for a component'… |
| skill | `research-synthesis` |  | Synthesize user research into themes, insights, and recommendations. Use when you have interview transcripts, survey results, usability test notes, support tickets, or N… |
| skill | `user-research` |  | Plan, conduct, and synthesize user research. Trigger with "user research plan", "interview guide", "usability test", "survey design", "research questions", or when the u… |

## ecc

Sursă: marketplace `ecc`, versiunea 2.2.3. Are hook-uri (rulează automat la anumite evenimente).

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| comandă | `marketing-campaign` | ★★★ | **campanie completă: poziționare, postări, email, reclame.** Plan and execute a full marketing campaign. Accepts a product brief and returns positioning, landing page copy, email sequence, social posts, ad variants, video scripts,… |
| skill | `brand-voice` | ★★★ | **profil de ton din postările tale reale.** Build a source-derived writing style profile from real posts, essays, launch notes, docs, or site copy, then reuse that profile across content, outreach, and social work… |
| skill | `content-engine` | ★★★ | **sistem de conținut: TikTok, YouTube, LinkedIn, newsletter.** Create platform-native content systems for X, LinkedIn, TikTok, YouTube, newsletters, and repurposed multi-platform campaigns. Use when the user wants social posts, thre… |
| skill | `crosspost` | ★★★ | **adaptează aceeași idee pentru fiecare rețea.** Multi-platform content distribution across X, LinkedIn, Threads, and Bluesky. Adapts content per platform using content-engine patterns. Never posts identical content cr… |
| skill | `frontend-slides` | ★★★ | **prezentări HTML animate, din zero sau din PPTX.** Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to… |
| skill | `marketing-campaign` | ★★★ | **campanie completă: poziționare, postări, email, reclame.** End-to-end marketing campaign planning and execution. Covers audience research, positioning, campaign angle definition, landing page copy, email sequences, social posts,… |
| skill | `remotion-video-creation` | ★★★ | **clipuri generate din cod: intro, text animat, captions.** Best practices for Remotion - Video creation in React. 29 domain-specific rules covering 3D, animations, audio, captions, charts, transitions, and more. Use when buildin… |
| skill | `video-editing` | ★★★ | **montaj clipuri: tăiere, structură, subtitrări (FFmpeg/Remotion).** AI-assisted video editing workflows for cutting, structuring, and augmenting real footage. Covers the full pipeline from raw capture through FFmpeg, Remotion, ElevenLabs… |
| agent | `marketing-agent` | ★★ | **agent strateg + copywriter.** Marketing strategist and copywriter for campaign planning, audience research, positioning, copy creation, and content review. Covers landing pages, email sequences, soci… |
| skill | `article-writing` | ★★ | **articole, ghiduri, newsletter.** Write articles, guides, blog posts, tutorials, newsletter issues, and other long-form content in a distinctive voice derived from supplied examples or brand guidance. Us… |
| skill | `brand-discovery` | ★★ | **interviu ghidat pentru identitatea brandului.** Run a structured, resumable multi-session brand identity interview across 8 modules (purpose, positioning, audience, personality, voice, narrative, founder tension) usin… |
| skill | `fal-ai-media` | ★★ | **generare imagini/video/voce AI (cont fal.ai).** Unified media generation via fal.ai MCP — image, video, and audio. Covers text-to-image (Nano Banana), text/image-to-video (Seedance, Kling, Veo 3), text-to-speech (CSM-… |
| skill | `google-workspace-ops` | ★★ | **Google Slides/Docs/Sheets ca un singur flux.** Operate across Google Drive, Docs, Sheets, and Slides as one workflow surface for plans, trackers, decks, and shared documents. Use when the user needs to find, summariz… |
| skill | `market-research` | ★★ | **studiu de piață, concurență.** Conduct market research, competitive analysis, investor due diligence, and industry intelligence with source attribution and decision-oriented summaries. Use when the us… |
| skill | `social-publisher` | ★★ | **programare postări (cont SocialClaw).** Agent-driven scheduling and publishing of social media posts across 13 platforms via SocialClaw. Use when the user wants to publish to X, LinkedIn, Instagram, Facebook P… |
| skill | `videodb` | ★★ | **caută și decupează momente din înregistrări lungi.** Ingest, index, search, edit, and monitor video and audio with the VideoDB Python SDK — upload from files, URLs, or RTSP feeds, build spoken and scene indexes with timest… |
| skill | `manim-video` | ★ | **animații explicative (grafice, diagrame).** Build reusable Manim explainers for technical concepts, graphs, system diagrams, and product walkthroughs, then hand off to the wider ECC video stack if needed. Use when… |
| skill | `seo` | ★ | **SEO pentru site.** Audit, plan, and implement SEO improvements across technical SEO, on-page optimization, structured data, Core Web Vitals, and content strategy. Use when the user wants b… |
| skill | `taste` | ★ | **direcție creativă pentru short-form edits.** Creative-direction layer for music videos and short-form edits in the angelcore / cloud-trance / hyperpop family — a named-genre aesthetic vocabulary, mood + color + lig… |
| skill | `ui-demo` | ★ | **înregistrare demo pentru site/aplicație.** Record polished UI demo videos using Playwright. Use when the user asks to create a demo, walkthrough, screen recording, or tutorial video of a web application. Produces… |
| agent | `a11y-architect` |  | Accessibility Architect specializing in WCAG 2.2 compliance for Web and Native platforms. Use PROACTIVELY when designing UI components, establishing design systems, or a… |
| agent | `agent-evaluator` |  | Evaluates agent output against 5-axis quality rubric (accuracy, completeness, clarity, actionability, conciseness). Use after any non-trivial task when the user wants a… |
| agent | `architect` |  | Software architecture specialist for system design, scalability, and technical decision-making. Use PROACTIVELY when planning new features, refactoring large systems, or… |
| agent | `bengali-reviewer` |  | Reviews code handling Bengali (Bangla) text for Unicode correctness, proper normalization, script-aware processing, and internationalization best practices. Use when cod… |
| agent | `build-error-resolver` |  | Build and TypeScript error resolution specialist. Use PROACTIVELY when build fails or type errors occur. Fixes build/type errors only with minimal diffs, no architectura… |
| agent | `chief-of-staff` |  | Personal communication chief of staff that triages email, Slack, LINE, and Messenger. Classifies messages into 4 tiers (skip/info_only/meeting_info/action_required), gen… |
| agent | `code-architect` |  | Designs feature architectures by analyzing existing codebase patterns and conventions, then providing implementation blueprints with concrete files, interfaces, data flo… |
| agent | `code-explorer` |  | Deeply analyzes existing codebase features by tracing execution paths, mapping architecture layers, and documenting dependencies to inform new development. |
| agent | `code-reviewer` |  | Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code. MUST BE USED for all… |
| agent | `code-simplifier` |  | Simplifies and refines code for clarity, consistency, and maintainability while preserving behavior. Focus on recently modified code unless instructed otherwise. |
| agent | `comment-analyzer` |  | Analyze code comments for accuracy, completeness, maintainability, and comment rot risk. |
| agent | `commit-reviewer` |  | Reviews a staged diff and drafts a Conventional Commits-compliant message matching the repository's actual history norms. Use before committing, or when asked to write o… |
| agent | `conversation-analyzer` |  | Use this agent when analyzing conversation transcripts to find behaviors worth preventing with hooks. Triggered by /hookify without arguments. |
| agent | `cpp-build-resolver` |  | C++ build, CMake, and compilation error resolution specialist. Fixes build errors, linker issues, and template errors with minimal changes. Use when C++ builds fail. |
| agent | `cpp-reviewer` |  | Expert C++ code reviewer specializing in memory safety, modern C++ idioms, concurrency, and performance. Use for all C++ code changes. MUST BE USED for C++ projects. |
| agent | `csharp-reviewer` |  | Expert C# code reviewer specializing in .NET conventions, async patterns, security, nullable reference types, and performance. Use for all C# code changes. MUST BE USED… |
| agent | `dart-build-resolver` |  | Dart/Flutter build, analysis, and dependency error resolution specialist. Fixes `dart analyze` errors, Flutter compilation failures, pub dependency conflicts, and build_… |
| agent | `database-reviewer` |  | PostgreSQL database specialist for query optimization, schema design, security, and performance. Use PROACTIVELY when writing SQL, creating migrations, designing schemas… |
| agent | `django-build-resolver` |  | Django/Python build, migration, and dependency error resolution specialist. Fixes pip/Poetry errors, migration conflicts, import errors, Django configuration issues, and… |
| agent | `django-reviewer` |  | Expert Django code reviewer specializing in ORM correctness, DRF patterns, migration safety, security misconfigurations, and production-grade Django practices. Use for a… |
| agent | `doc-updater` |  | Documentation and codemap specialist. Use PROACTIVELY for updating codemaps and documentation. Generates docs/CODEMAPS/*, updates READMEs and guides. Backs the /update-c… |
| agent | `docs-lookup` |  | When the user asks how to use a library, framework, or API or needs up-to-date code examples, use Context7 MCP to fetch current documentation and return answers with exa… |
| agent | `e2e-runner` |  | End-to-end testing specialist using Vercel Agent Browser (preferred) with Playwright fallback. Use PROACTIVELY for generating, maintaining, and running E2E tests. Manage… |
| agent | `fastapi-reviewer` |  | Reviews FastAPI applications for async correctness, dependency injection, Pydantic schemas, security, OpenAPI quality, testing, and production readiness. |
| agent | `flutter-reviewer` |  | Flutter and Dart code reviewer. Reviews Flutter code for widget best practices, state management patterns, Dart idioms, performance pitfalls, accessibility, and clean ar… |
| agent | `fsharp-reviewer` |  | Expert F# code reviewer specializing in functional idioms, type safety, pattern matching, computation expressions, and performance. Use for all F# code changes. MUST BE… |
| agent | `gan-evaluator` |  | GAN Harness — Evaluator agent. Tests the live running application via Playwright, scores against rubric, and provides actionable feedback to the Generator. |
| agent | `gan-generator` |  | GAN Harness — Generator agent. Implements features according to the spec, reads evaluator feedback, and iterates until quality threshold is met. |
| agent | `gan-planner` |  | GAN Harness — Planner agent. Expands a one-line prompt into a full product specification with features, sprints, evaluation criteria, and design direction. |
| agent | `go-build-resolver` |  | Go build, vet, and compilation error resolution specialist. Fixes build errors, go vet issues, and linter warnings with minimal changes. Use when Go builds fail. |
| agent | `go-reviewer` |  | Expert Go code reviewer specializing in idiomatic Go, concurrency patterns, error handling, and performance. Use for all Go code changes. MUST BE USED for Go projects. |
| agent | `harmonyos-app-resolver` |  | HarmonyOS application development expert specializing in ArkTS and ArkUI. Reviews code for V2 state management compliance, Navigation routing patterns, API usage, and pe… |
| agent | `harness-optimizer` |  | Improve local agent-harness configuration reliability and cost using eval-driven grading (pass@k/pass^k) derived from the eval-harness skill. |
| agent | `healthcare-reviewer` |  | Reviews healthcare application code for clinical safety, CDSS accuracy, PHI compliance, and medical data integrity. Specialized for EMR/EHR, clinical decision support, a… |
| agent | `homelab-architect` |  | Designs home and small-lab network plans from hardware inventory, goals, and operator experience level, with safe staged changes and rollback guidance. |
| agent | `java-build-resolver` |  | Java/Maven/Gradle build, compilation, and dependency error resolution specialist. Automatically detects Spring Boot or Quarkus and applies framework-specific fixes. Fixe… |
| agent | `java-reviewer` |  | Expert Java code reviewer for Spring Boot and Quarkus projects. Automatically detects the framework and applies the appropriate review rules. Covers layered architecture… |
| agent | `kotlin-build-resolver` |  | Kotlin/Gradle build, compilation, and dependency error resolution specialist. Fixes build errors, Kotlin compiler errors, and Gradle issues with minimal changes. Use whe… |
| agent | `kotlin-reviewer` |  | Kotlin and Android/KMP code reviewer. Reviews Kotlin code for idiomatic patterns, coroutine safety, Compose best practices, clean architecture violations, and common And… |
| agent | `loop-operator` |  | Operate autonomous agent loops, monitor progress, and intervene safely when loops stall. |
| agent | `mle-reviewer` |  | Production machine-learning engineering reviewer for data contracts, feature pipelines, training reproducibility, offline/online evaluation, model serving, monitoring, a… |
| agent | `network-architect` |  | Designs enterprise or multi-site network architecture from requirements, using existing network skills for focused routing, validation, automation, and troubleshooting d… |
| agent | `network-config-reviewer` |  | Reviews router and switch configurations for security, correctness, stale references, risky change-window commands, and missing operational guardrails. |
| agent | `network-troubleshooter` |  | Diagnoses network connectivity, routing, DNS, interface, and policy symptoms with a read-only OSI-layer workflow and evidence-backed root cause summary. |
| agent | `opensource-forker` |  | Fork any project for open-sourcing. Copies files, strips secrets and credentials (20+ patterns), replaces internal references with placeholders, generates .env.example,… |
| agent | `opensource-packager` |  | Generate complete open-source packaging for a sanitized project. Produces CLAUDE.md, setup.sh, README.md, LICENSE, CONTRIBUTING.md, and GitHub issue templates. Makes any… |
| agent | `opensource-sanitizer` |  | Verify an open-source fork is fully sanitized before release. Scans for leaked secrets, PII, internal references, and dangerous files using 20+ regex patterns. Generates… |
| agent | `performance-optimizer` |  | Performance analysis and optimization specialist. Use PROACTIVELY for identifying bottlenecks, optimizing slow code, reducing bundle sizes, and improving runtime perform… |
| agent | `php-reviewer` |  | Expert PHP code reviewer specializing in PSR-12 compliance, PHP type system, Eloquent ORM patterns, security, and performance. Use for all PHP code changes. MUST BE USED… |
| agent | `planner` |  | Expert planning specialist for complex features and refactoring. Use PROACTIVELY when users request feature implementation, architectural changes, or complex refactoring… |
| agent | `pr-test-analyzer` |  | Review pull request test coverage quality and completeness, with emphasis on behavioral coverage and real bug prevention. |
| agent | `python-reviewer` |  | Expert Python code reviewer specializing in PEP 8 compliance, Pythonic idioms, type hints, security, and performance. Use for all Python code changes. MUST BE USED for P… |
| agent | `pytorch-build-resolver` |  | PyTorch runtime, CUDA, and training error resolution specialist. Fixes tensor shape mismatches, device errors, gradient issues, DataLoader problems, and mixed precision… |
| agent | `rag-pipeline-reviewer` |  | Reviews RAG (Retrieval-Augmented Generation) pipelines for retrieval quality, chunking strategy, embedding choices, and evaluation coverage. Invoke when the user builds,… |
| agent | `react-build-resolver` |  | Diagnose and fix React build failures across Vite, webpack, Next.js, CRA, Parcel, esbuild, and Bun. Handles JSX/TSX compile errors, hydration mismatches, server/client c… |
| agent | `react-reviewer` |  | Expert React/JSX code reviewer specializing in hook correctness, render performance, server/client component boundaries, accessibility, and React-specific security. Use… |
| agent | `refactor-cleaner` |  | Dead code cleanup and consolidation specialist. Use PROACTIVELY for removing unused code, duplicates, and refactoring. Runs analysis tools (knip, depcheck, ts-prune) to… |
| agent | `ruby-reviewer` |  | Expert Ruby and Rails code reviewer specializing in idiomatic Ruby, Active Record query safety, Rails security defaults, and RSpec/Minitest quality. Use for all Ruby cod… |
| agent | `rust-build-resolver` |  | Rust build, compilation, and dependency error resolution specialist. Fixes cargo build errors, borrow checker issues, and Cargo.toml problems with minimal changes. Use w… |
| agent | `rust-reviewer` |  | Expert Rust code reviewer specializing in ownership, lifetimes, error handling, unsafe usage, and idiomatic patterns. Use for all Rust code changes. MUST BE USED for Rus… |
| agent | `security-reviewer` |  | Security vulnerability detection and remediation specialist. Use PROACTIVELY after writing code that handles user input, authentication, API endpoints, or sensitive data… |
| agent | `seo-specialist` |  | SEO specialist for technical SEO audits, on-page optimization, structured data, Core Web Vitals, and content/keyword mapping. Use for site audits, meta tag reviews, sche… |
| agent | `silent-failure-hunter` |  | Review code for silent failures, swallowed errors, bad fallbacks, and missing error propagation. |
| agent | `spec-miner` |  | Extracts behavioral specs from existing codebases for OpenSpec. Produces flat Requirement and Invariant blocks with structured metadata (entities, enforced, id, test anc… |
| agent | `swift-build-resolver` |  | Swift/Xcode build, compilation, and dependency error resolution specialist. Fixes swift build errors, Xcode build failures, SPM dependency issues, and code signing probl… |
| agent | `swift-reviewer` |  | Expert Swift code reviewer specializing in protocol-oriented design, value semantics, ARC memory management, Swift Concurrency, and idiomatic patterns. Use for all Swift… |
| agent | `tdd-guide` |  | Test-Driven Development specialist enforcing write-tests-first methodology. Use PROACTIVELY when writing new features, fixing bugs, or refactoring code. Ensures 80%+ tes… |
| agent | `type-design-analyzer` |  | Analyze type design for encapsulation, invariant expression, usefulness, and enforcement. |
| agent | `typescript-reviewer` |  | Expert TypeScript/JavaScript code reviewer specializing in type safety, async correctness, Node/web security, and idiomatic patterns. Use for all TypeScript and JavaScri… |
| agent | `vue-reviewer` |  | Expert Vue.js code reviewer specializing in Composition API correctness, reactivity pitfalls, component architecture, template security, and Vue-specific performance. Us… |
| comandă | `aside` |  | Answer a quick side question without interrupting or losing context from the current task. Resume work automatically after answering. |
| comandă | `astra-review` |  | Send Claude-written code to GPT-6-Astra (ChatGPT, via Codex CLI) for an independent cross-provider review, then fix what it finds. |
| comandă | `auto-update` |  | Pull the latest ECC repo changes and reinstall the current managed targets. |
| comandă | `build-fix` |  | Detect the project build system and incrementally fix build/type errors with minimal safe changes. |
| comandă | `checkpoint` |  | Create, verify, or list workflow checkpoints after running verification checks. |
| comandă | `code-review` |  | Code review — local uncommitted changes or GitHub PR (pass PR number/URL for PR mode). Use for a step-by-step PRP-style checklist review; for a multi-agent pass use /rev… |
| comandă | `cost-report` |  | Generate a local Claude Code cost report from the ECC cost-tracker metrics log. Use for a terminal summary or CSV export of tracked spend; the cost-tracking skill covers… |
| comandă | `cpp-build` |  | Fix C++ build errors, CMake issues, and linker problems incrementally. Invokes the cpp-build-resolver agent for minimal, surgical fixes. |
| comandă | `cpp-review` |  | Comprehensive C++ code review for memory safety, modern C++ idioms, concurrency, and security. Invokes the cpp-reviewer agent. |
| comandă | `cpp-test` |  | Enforce TDD workflow for C++. Write GoogleTest tests first, then implement. Verify coverage with gcov/lcov. |
| comandă | `ecc-guide` |  | Navigate ECC's current agents, skills, commands, hooks, install profiles, and docs from the live repository surface. This is the slash-command entrypoint for that naviga… |
| comandă | `epic-claim` |  | Claim an epic issue, stamp coordination state, and sync local ownership. |
| comandă | `epic-decompose` |  | Break an epic into task children without creating task branches. |
| comandă | `epic-publish` |  | Publish a validated epic update back to the issue and local cache. |
| comandă | `epic-review` |  | Mark epic review requested, approved, or changes requested. |
| comandă | `epic-sync` |  | Sync epic issue bodies, labels, and local coordination snapshots from GitHub. |
| comandă | `epic-unblock` |  | Sweep blocked epic issues and reopen anything whose dependencies are closed. |
| comandă | `epic-validate` |  | Validate epic readiness, dependencies, and coordination policy. |
| comandă | `evolve` |  | Analyze instincts and suggest or generate evolved structures |
| comandă | `fastapi-review` |  | Review a FastAPI application for architecture, async correctness, dependency injection, Pydantic schemas, security, performance, and testability. |
| comandă | `feature-dev` |  | Guided feature development with codebase understanding and architecture focus |
| comandă | `flutter-build` |  | Fix Dart analyzer errors and Flutter build failures incrementally. Invokes the dart-build-resolver agent for minimal, surgical fixes. |
| comandă | `flutter-review` |  | Review Flutter/Dart code for idiomatic patterns, widget best practices, state management, performance, accessibility, and security. Invokes the flutter-reviewer agent. |
| comandă | `flutter-test` |  | Run Flutter/Dart tests, report failures, and incrementally fix test issues. Covers unit, widget, golden, and integration tests. |
| comandă | `gan-build` |  | Run a generator/evaluator build loop for implementation tasks with bounded iterations and scoring. |
| comandă | `gan-design` |  | Run a generator/evaluator design loop for frontend or visual work with bounded iterations and scoring. |
| comandă | `go-build` |  | Fix Go build errors, go vet warnings, and linter issues incrementally. Invokes the go-build-resolver agent for minimal, surgical fixes. |
| comandă | `go-review` |  | Comprehensive Go code review for idiomatic patterns, concurrency safety, error handling, and security. Invokes the go-reviewer agent. |
| comandă | `go-test` |  | Enforce TDD workflow for Go. Write table-driven tests first, then implement. Verify 80%+ coverage with go test -cover. |
| comandă | `gradle-build` |  | Fix Gradle build errors for Android and KMP projects |
| comandă | `harness-audit` |  | Run a deterministic repository harness audit and return a prioritized scorecard. Use for a deterministic overall repo-readiness scorecard; for a security-specific audit… |
| comandă | `hookify` |  | Create hooks to prevent unwanted behaviors from conversation analysis or explicit instructions. Use to generate a new hook rule file from conversation analysis or a desc… |
| comandă | `hookify-configure` |  | Enable or disable hookify rules interactively |
| comandă | `hookify-help` |  | Get help with the hookify system |
| comandă | `hookify-list` |  | List all configured hookify rules |
| comandă | `instinct-export` |  | Export instincts from project/global scope to a file |
| comandă | `instinct-import` |  | Import instincts from file or URL into project/global scope |
| comandă | `instinct-status` |  | Show learned instincts (project + global) with confidence |
| comandă | `issue-review` |  | Review a GitHub issue the way /code-review reviews a PR — verify the report against the codebase, find duplicates and prior fixes, score completeness, assign severity, a… |
| comandă | `jira` |  | Retrieve a Jira ticket, analyze requirements, update status, or add comments. Uses the jira-integration skill and MCP or REST API. |
| comandă | `kotlin-build` |  | Fix Kotlin/Gradle build errors, compiler warnings, and dependency issues incrementally. Invokes the kotlin-build-resolver agent for minimal, surgical fixes. |
| comandă | `kotlin-review` |  | Comprehensive Kotlin code review for idiomatic patterns, null safety, coroutine safety, and security. Invokes the kotlin-reviewer agent. |
| comandă | `kotlin-test` |  | Enforce TDD workflow for Kotlin. Write Kotest tests first, then implement. Verify 80%+ coverage with Kover. |
| comandă | `learn` |  | Extract reusable patterns from the current session and save them as candidate skills or guidance. Use to review a session on demand and persist an approved skill file; c… |
| comandă | `learn-eval` |  | Extract reusable patterns from the session, self-evaluate quality before saving, and determine the right save location (Global vs Project). |
| comandă | `loop-start` |  | Prepare a managed autonomous loop pattern with safety defaults and explicit stop conditions, then print the commands to launch and monitor it. Use to set up sequential,… |
| comandă | `loop-status` |  | Inspect active loop state, progress, failure signals, and recommended intervention. |
| comandă | `model-route` |  | Recommend the best model tier for the current task based on complexity, risk, and budget. |
| comandă | `multi-backend` |  | Run a backend-focused multi-model workflow for APIs, algorithms, data, and business logic. |
| comandă | `multi-execute` |  | Execute a multi-model implementation plan while preserving Claude as the only filesystem writer. |
| comandă | `multi-frontend` |  | Run a frontend-focused multi-model workflow for components, layouts, animation, and UI polish. |
| comandă | `multi-plan` |  | Create a multi-model (Codex + Antigravity) implementation plan without modifying production code. Requires the external ccg-workflow runtime, not part of the base ECC in… |
| comandă | `multi-workflow` |  | Run a full multi-model development workflow with research, planning, execution, optimization, and review. |
| comandă | `orch-add-feature` |  | Orchestrate building a brand-new feature end to end — research, plan, TDD, review, gated commit. Wrapper that kicks off the orch-add-feature skill. |
| comandă | `orch-build-mvp` |  | Orchestrate bootstrapping a working MVP from a design/spec doc — ingest, slice, scaffold, TDD, review, gated commit (reuses the GAN harness). Wrapper for the orch-build-… |
| comandă | `orch-change-feature` |  | Orchestrate altering an existing, working feature to new desired behavior — update tests to the new spec, change impl, review, gated commit. Wrapper for the orch-change-… |
| comandă | `orch-fix-defect` |  | Orchestrate fixing a bug — reproduce it as a failing regression test, fix to green, review, gated commit. Wrapper for the orch-fix-defect skill. |
| comandă | `orch-refine-code` |  | Orchestrate a behavior-preserving refactor — confirm tests green, restructure without changing behavior, keep green, review, gated commit. Wrapper for the orch-refine-co… |
| comandă | `orch-review` |  | Run the orch-review native Workflow over a diff (local changes or a GitHub PR) and report blocking vs advisory findings. Surface for the orch-review workflow. Use for a… |
| comandă | `plan` |  | Restate requirements, assess risks, and create step-by-step implementation plan. WAIT for user CONFIRM before touching any code. Use for a single-model inline or PRD-dri… |
| comandă | `plan-canvas` |  | Open a plan or HTML artifact in the browser Plan Canvas for annotate-and-approve review. This is a thin slash-command entrypoint over the plan-canvas skill, which covers… |
| comandă | `plan-prd` |  | Generate a lean, problem-first PRD and hand off to /plan for implementation planning. |
| comandă | `pm2` |  | Analyze a project and generate PM2 service commands for detected frontend, backend, or database services. |
| comandă | `pr` |  | Create a GitHub PR from current branch with unpushed commits — discovers templates, analyzes changes, pushes |
| comandă | `project-init` |  | Detect a project's stack and produce a dry-run ECC onboarding plan using the repository's install manifests and stack mappings. Use to onboard ECC into a target project… |
| comandă | `projects` |  | List known projects and their instinct statistics |
| comandă | `promote` |  | Promote project-scoped instincts to global scope |
| comandă | `prp-commit` |  | Quick commit with natural language file targeting — describe what to commit in plain English |
| comandă | `prp-implement` |  | Execute an implementation plan with rigorous validation loops |
| comandă | `prp-plan` |  | Create comprehensive feature implementation plan with codebase analysis and pattern extraction |
| comandă | `prp-pr` |  | Alias of /pr for the PRP workflow series. Use when creating a pull request mid-PRP workflow; otherwise use /pr. |
| comandă | `prp-prd` |  | Interactive PRD generator - problem-first, hypothesis-driven product spec with back-and-forth questioning |
| comandă | `prune` |  | Delete pending instincts older than 30 days that were never promoted. Thin CLI wrapper for continuous-learning-v2's instinct-cli.py prune command; use to clean up stale… |
| comandă | `python-review` |  | Comprehensive Python code review for PEP 8 compliance, type hints, security, and Pythonic idioms. Invokes the python-reviewer agent. |
| comandă | `quality-gate` |  | Run the ECC formatter quality gate for a single file and report remediation steps. |
| comandă | `react-build` |  | Fix React build failures (Vite, webpack, Next.js, CRA, Parcel, esbuild, Bun) incrementally — JSX/TSX compile errors, hydration mismatches, server/client component bounda… |
| comandă | `react-review` |  | Comprehensive React/JSX code review for hook correctness, render performance, server/client component boundaries, accessibility, and React-specific security. Invokes the… |
| comandă | `react-test` |  | Enforce TDD workflow for React. Write React Testing Library tests first (behavior-focused, accessibility-first), then implement components. Detects Vitest or Jest and ve… |
| comandă | `refactor-clean` |  | Safely identify and remove dead code with verification after each change. |
| comandă | `resume-session` |  | Load the most recent session file from ~/.claude/session-data/ and resume work with full context from where the last session ended. |
| comandă | `review-pr` |  | Comprehensive PR review using specialized agents (code-reviewer, comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer, code-simplifier). Use f… |
| comandă | `rust-build` |  | Fix Rust build errors, borrow checker issues, and dependency problems incrementally. Invokes the rust-build-resolver agent for minimal, surgical fixes. |
| comandă | `rust-review` |  | Comprehensive Rust code review for ownership, lifetimes, error handling, unsafe usage, and idiomatic patterns. Invokes the rust-reviewer agent. |
| comandă | `rust-test` |  | Enforce TDD workflow for Rust. Write tests first, then implement. Verify 80%+ coverage with cargo-llvm-cov. |
| comandă | `santa-loop` |  | Adversarial dual-review convergence loop — two independent model reviewers must both approve before code ships. Use for the CLI-driven version of this loop; wraps the sa… |
| comandă | `save-session` |  | Save current session state to a dated file in ~/.claude/session-data/ so work can be resumed in a future session with full context. |
| comandă | `security-scan` |  | Run AgentShield against agent, hook, MCP, permission, and secret surfaces. This is the slash-command entrypoint for that audit; prefer the security-scan skill for the sa… |
| comandă | `sessions` |  | Manage Claude Code session history, aliases, and session metadata. |
| comandă | `setup-pm` |  | Configure your preferred package manager (npm/pnpm/yarn/bun) |
| comandă | `skill-create` |  | Analyze local git history to extract coding patterns and generate SKILL.md files. Local version of the Skill Creator GitHub App. Use to generate new skills from local gi… |
| comandă | `skill-health` |  | Show skill portfolio health dashboard with charts and analytics. Use for the quantitative usage/success-rate dashboard; for a qualitative compliance or quality audit use… |
| comandă | `skill-host-compat` |  | Lint ECC skills for Codex/Cursor-safe frontmatter and Claude-only substitutions before a skill PR. |
| comandă | `test-coverage` |  | Analyze coverage, identify gaps, and generate missing tests toward the target threshold. |
| comandă | `token-card` |  | Render a token-usage stat card from local agent session logs and commit it to the repo. Invokes the token-card skill. |
| comandă | `update-codemaps` |  | Scan project structure and generate token-lean architecture codemaps. |
| comandă | `update-docs` |  | Sync documentation from source-of-truth files such as scripts, schemas, routes, and exports. |
| comandă | `vue-review` |  | Comprehensive Vue.js code review for Composition API correctness, reactivity, composable patterns, template security, accessibility, and Vue-specific performance. Invoke… |
| skill | `accessibility` |  | Design, implement, and audit accessible UI to WCAG 2.2 Level AA across Web, iOS, and Android — semantic ARIA roles and labels, accessibility traits and hints, focus mana… |
| skill | `agent-architecture-audit` |  | Full-stack diagnostic for agent and LLM applications. Audits the 12-layer agent stack for wrapper regression, memory pollution, tool discipline failures, hidden repair l… |
| skill | `agent-eval` |  | Head-to-head comparison of coding agents (Claude Code, Aider, Codex, etc.) on custom tasks with pass rate, cost, time, and consistency metrics. Use when choosing between… |
| skill | `agent-harness-construction` |  | Design and optimize AI agent action spaces, tool definitions, and observation formatting for higher completion rates. Use when defining or revising an agent's tool set,… |
| skill | `agent-introspection-debugging` |  | Structured self-debugging workflow for AI agent failures using capture, diagnosis, contained recovery, and introspection reports. Use when an agent run fails and you nee… |
| skill | `agent-payment-x402` |  | Add x402 payment execution to AI agents with per-task budgets, spending controls, and non-custodial wallets. Supports Base through agentwallet-sdk, X Layer through OKX P… |
| skill | `agent-runtime-gateway-smoke-test` |  | Verify a local agent API, temporary gateway tunnel, and remote sandbox callback with a tool-free task, then restore the original app connection. |
| skill | `agent-security-hardening` |  | Security hardening guidance for AI agent frameworks that process untrusted content, invoke tools, write workspace files, manage runtime identifiers, or handle credential… |
| skill | `agent-self-evaluation` |  | Use after completing any non-trivial task. The agent self-rates its output on 5 axes — accuracy, completeness, clarity, actionability, conciseness — with concrete eviden… |
| skill | `agent-sort` |  | Build an evidence-backed ECC install plan for a specific repo by sorting skills, commands, rules, hooks, and extras into DAILY vs LIBRARY buckets using parallel repo-awa… |
| skill | `agentic-engineering` |  | Operate as an agentic engineer using eval-first execution, decomposition, and cost-aware model routing. Use when planning or executing engineering work that agents will… |
| skill | `agentic-os` |  | Build persistent multi-agent operating systems on Claude Code. Covers kernel architecture, specialist agents, slash commands, file-based memory, scheduled automation, an… |
| skill | `ai-first-engineering` |  | Engineering operating model for teams where AI agents generate a large share of implementation output. Use when setting team process, review gates, or ownership rules fo… |
| skill | `ai-regression-testing` |  | Regression testing strategies for AI-assisted development. Sandbox-mode API testing without database dependencies, automated bug-check workflows, and patterns to catch A… |
| skill | `android-clean-architecture` |  | Clean Architecture patterns for Android and Kotlin Multiplatform projects — module structure, dependency rules, UseCases, Repositories, and data layer patterns. Use when… |
| skill | `angular-developer` |  | Generates Angular code and provides architectural guidance. Trigger when creating projects, components, or services, or for best practices on reactivity (signals, linked… |
| skill | `api-connector-builder` |  | Build a new API connector or provider by matching the target repo's existing integration pattern exactly. Use when adding one more integration without inventing a second… |
| skill | `api-design` |  | REST API design patterns including resource naming, status codes, pagination, filtering, error responses, versioning, and rate limiting for production APIs. Use when des… |
| skill | `architecture-decision-records` |  | Capture architectural decisions as numbered ADR markdown files in docs/adr/ with context, alternatives considered, consequences, and an index README. Use when the user s… |
| skill | `automation-audit-ops` |  | Evidence-first automation inventory and overlap audit workflow for ECC. Use when the user wants to know which jobs, hooks, connectors, MCP servers, or wrappers are live,… |
| skill | `autonomous-agent-harness` |  | Transform Claude Code into a fully autonomous agent system with persistent memory, scheduled operations, computer use, and task queuing. Replaces standalone agent framew… |
| skill | `autonomous-loops` |  | Patterns and architectures for autonomous Claude Code loops — from simple sequential pipelines to RFC-driven multi-agent DAG systems. Retained for compatibility only: wh… |
| skill | `backend-patterns` |  | Backend architecture patterns, API design, database optimization, and server-side best practices for Node.js, Express, and Next.js API routes. Use when building or revie… |
| skill | `benchmark` |  | Measure performance baselines and detect regressions across browser Core Web Vitals (LCP, INP, CLS, page weight), API endpoint latency percentiles, and build/test feedba… |
| skill | `benchmark-methodology` |  | Score a scoped competitor set into comparable profile cards: nine weighted dimensions (positioning, voice, visual craft, offer packaging, evidence, enterprise-readiness,… |
| skill | `benchmark-optimization-loop` |  | Convert 'make it faster' requests into a bounded measured optimization loop — baseline first, generate one-hypothesis variants, benchmark each against a correctness gate… |
| skill | `bengali-nlp` |  | Bengali (Bangla) text processing patterns including Unicode normalization, script detection, tokenization, conjunct handling, and Bangla-specific NLP best practices for… |
| skill | `blender-motion-state-inspection` |  | Use this skill when inspecting Blender characters, rigs, poses, animation retargeting, ground contact, facing direction, or model-vs-motion alignment where screenshots a… |
| skill | `blueprint` |  | Turn a one-line objective into a step-by-step construction plan for multi-session, multi-agent engineering projects: one-PR-sized steps with self-contained context brief… |
| skill | `brownfield-retrospective` |  | Run the ECC engineering process retroactively against an existing project slice. Audit current state, reconstruct past decisions, produce a four-axis gap register (think… |
| skill | `browser-qa` |  | Run automated post-deploy UI verification with a browser automation MCP (claude-in-chrome, Playwright, or Puppeteer): console-error and Core Web Vitals smoke checks, for… |
| skill | `bun-runtime` |  | Bun as runtime, package manager, bundler, and test runner. When to choose Bun vs Node, migration notes, and Vercel support. |
| skill | `canary-watch` |  | Use this skill to monitor and verify a deployed URL after releases — checks HTTP endpoints, SSE streams, static assets, console errors, and performance regressions after… |
| skill | `carrier-relationship-management` |  | Manage truckload, LTL, and intermodal carrier portfolios: sourcing and FMCSA vetting, freight rate and fuel-surcharge negotiation, RFPs and routing guides, carrier score… |
| skill | `change-impact` |  | Perform evidence-backed impact analysis before changing code, data, interfaces, or governance documents, then compare the planned impact with the actual diff after imple… |
| skill | `cisco-ios-patterns` |  | Cisco IOS and IOS-XE review patterns for show commands, config hierarchy, wildcard masks, ACL placement, interface hygiene, and safe change-window verification. Use when… |
| skill | `ck` |  | Persistent per-project memory for Claude Code (Context Keeper) driven by deterministic Node.js /ck commands: init, save, resume, info, list, forget, and v1-to-v2 migrate… |
| skill | `claude-devfleet` |  | Orchestrate multi-agent coding tasks via Claude DevFleet — plan projects, dispatch parallel agents in isolated worktrees, monitor progress, and read structured reports.… |
| skill | `click-path-audit` |  | Trace every user-facing button/touchpoint through its full state change sequence to find bugs where functions individually work but cancel each other out, produce wrong… |
| skill | `clickhouse-io` |  | ClickHouse database patterns, query optimization, analytics, and data engineering best practices for high-performance analytical workloads. Use when writing ClickHouse s… |
| skill | `code-tour` |  | Create CodeTour `.tour` files — persona-targeted, step-by-step walkthroughs with real file and line anchors. Use for onboarding tours, architecture walkthroughs, PR tour… |
| skill | `codebase-onboarding` |  | Analyze an unfamiliar codebase and generate a structured onboarding guide with architecture map, key entry points, conventions, and a starter CLAUDE.md. Use when joining… |
| skill | `codehealth-mcp` |  | Real-time structural Code Health via CodeScene MCP — review before edits, verify score deltas after changes, gate commits and PRs. Use when reviewing code quality, refac… |
| skill | `coding-standards` |  | Baseline cross-project coding conventions for naming, readability, immutability, and code-quality review. Use detailed frontend or backend skills for framework-specific… |
| skill | `competitive-platform-analysis` |  | Use when scoping a competitive landscape — identifying, categorising, and score-filtering a competitor set before any benchmarking begins. Decides who counts as a compet… |
| skill | `competitive-report-structure` |  | Assemble scored competitor profile cards (from benchmark-methodology) into a decision-grade competitive report with landscape map, competitor tiers, benchmarking matrix,… |
| skill | `compose-multiplatform-patterns` |  | Compose Multiplatform and Jetpack Compose patterns for KMP projects — state management, navigation, theming, performance, and platform-specific UI. Use when building Com… |
| skill | `config-gc` |  | Garbage collection for your Claude Code configuration. Periodically scans ~/.claude (skills, memory, hooks, permissions, MCP servers, caches) for redundant, stale, orpha… |
| skill | `configure-ecc` |  | Run the conversational ECC setup wizard inside the current harness: inventory the install, collect scope (user/project/local) and hook mode (off/minimal/standard/strict)… |
| skill | `connections-optimizer` |  | Reorganize the user's X and LinkedIn network with review-first pruning, add/follow recommendations, and channel-specific warm outreach drafted in the user's real voice.… |
| skill | `content-hash-cache-pattern` |  | Cache expensive file processing results using SHA-256 content hashes — path-independent, auto-invalidating, with service layer separation. Use when repeated file process… |
| skill | `context-and-decisions` |  | Govern stable domain context with a narrowly scoped CONTEXT.md when needed, and route hard-to-reverse decisions to ECC's existing architecture-decision-records skill. Us… |
| skill | `context-budget` |  | Routes live context checks to the native Codex or Claude Code meter without scanning files, and performs a bounded static component audit only when explicitly requested.… |
| skill | `continuous-agent-loop` |  | Patterns for continuous autonomous agent loops with quality gates, evals, and recovery controls. Use when running an agent loop that must self-check, gate on evals, and… |
| skill | `continuous-learning` |  | [DEPRECATED - use continuous-learning-v2] Legacy v1 stop-hook skill extractor. v2 is a strict superset with instinct-based, project-scoped, hook-reliable learning. Do no… |
| skill | `continuous-learning-v2` |  | Instinct-based learning system that observes sessions via hooks, creates atomic instincts with confidence scoring, and evolves them into skills/commands/agents. v2.1 add… |
| skill | `contract-first` |  | Coordinate frontend/backend or service-to-service work through one authoritative machine-checkable contract (OpenAPI, AsyncAPI, Protocol Buffers, or JSON Schema), with g… |
| skill | `conventional-commit-review` |  | Reviews staged changes and drafts a Conventional Commits-compliant commit message with the right type, scope, and length. Use before committing, or when the user asks to… |
| skill | `cost-aware-llm-pipeline` |  | Cost optimization patterns for LLM API usage — model routing by task complexity, budget tracking, retry logic, and prompt caching. Use when LLM spend needs to come down,… |
| skill | `cost-tracking` |  | Track and report Claude Code token usage, spending, and budgets from the local ECC cost-tracker metrics log. Use when the user asks about costs, spending, usage, tokens,… |
| skill | `council` |  | Convene a four-voice council for ambiguous decisions, tradeoffs, and go/no-go calls. Use when multiple valid paths exist and you need structured disagreement before choo… |
| skill | `council-multi-model` |  | Add one optional external Codex critique after the existing council has produced a decision draft. Use when an ambiguous, high-consequence decision would benefit from a… |
| skill | `counterparty-channel-discipline` |  | Per-channel strict prompts, mention gating, silent observation, and a communication autonomy policy for agents that sit in shared channels with external counterparties.… |
| skill | `cpp-coding-standards` |  | C++ coding standards based on the C++ Core Guidelines (isocpp.github.io). Use when writing, reviewing, or refactoring C++ code to enforce modern, safe, and idiomatic pra… |
| skill | `cpp-testing` |  | Use only when writing/updating/fixing C++ tests, configuring GoogleTest/CTest, diagnosing failing or flaky tests, or adding coverage/sanitizers. |
| skill | `csharp-testing` |  | C# and .NET testing patterns with xUnit, FluentAssertions, mocking, integration tests, and test organization best practices. Use when writing or reviewing xUnit tests, m… |
| skill | `customer-billing-ops` |  | Operate customer billing workflows such as subscriptions, refunds, churn triage, billing-portal recovery, and plan analysis using connected billing tools like Stripe. Us… |
| skill | `customs-trade-compliance` |  | Codified customs and trade compliance expertise — HS/HTS tariff classification with GRI rules, commercial invoices and entry documentation, Incoterms 2020, FTA qualifica… |
| skill | `dart-flutter-patterns` |  | Production-ready Dart and Flutter patterns covering null safety, immutable state with Freezed, async composition, widget architecture, state management (BLoC, Riverpod,… |
| skill | `dashboard-builder` |  | Build monitoring dashboards that answer real operator questions for Grafana, SigNoz, and similar platforms. Use when turning metrics into a working dashboard instead of… |
| skill | `data-scraper-agent` |  | Build a fully automated AI-powered data collection agent for any public source — job boards, prices, news, GitHub, sports, anything. Runs on a schedule, enriches data wi… |
| skill | `data-throughput-accelerator` |  | Diagnose and accelerate large data movement — ingestion, backfill, export, ETL, warehouse loading, manifest catch-up, and table synchronization — by isolating the true b… |
| skill | `database-migrations` |  | Safe, reversible database migration patterns: forward-only production changes, expand-contract zero-downtime renames, concurrent indexes, batched backfills, and per-tool… |
| skill | `deep-research` |  | Produce cited research reports from multiple web sources using firecrawl and exa MCP tools — plan sub-questions, search and deep-read sources, then synthesize findings w… |
| skill | `deepseek-harness-setup` |  | Install and operate Everything Claude Code (ECC) on the DeepSeek Harness (DSH): native skill roots (~/.dsh/skills, .agents/skills), the @deepseek-ai/dsh-hooks-claude-cod… |
| skill | `defi-amm-security` |  | Security checklist for Solidity AMM contracts, liquidity pools, and swap flows. Covers reentrancy, CEI ordering, donation or inflation attacks, oracle manipulation, slip… |
| skill | `delivery-gate` |  | Stop hook that blocks Claude from finishing until quality checks pass. Detects rationalization patterns (surface text heuristics), stale learning logs (filesystem mtime)… |
| skill | `deployment-patterns` |  | Deployment workflows, CI/CD pipeline patterns, Docker containerization, health checks, rollback strategies, and production readiness checklists for web applications. Use… |
| skill | `design-system` |  | Generate a design system from an existing codebase or audit one for visual consistency: extract tokens (colors, typography, spacing, shadows) into design-tokens.json and… |
| skill | `dev-team` |  | Simulate a collaborative dev team session where multiple role-based personas (PM, Architect, Developer, QA) respond to the same problem together in one session. Use when… |
| skill | `django-celery` |  | Django + Celery async task patterns — configuration, task design, beat scheduling, retries, canvas workflows, monitoring, and testing. Use when adding background jobs, s… |
| skill | `django-patterns` |  | Django architecture patterns, REST API design with DRF, ORM best practices, caching, signals, middleware, and production-grade Django apps. Use when building or reviewin… |
| skill | `django-security` |  | Django security best practices, authentication, authorization, CSRF protection, SQL injection prevention, XSS prevention, and secure deployment configurations. Use when… |
| skill | `django-tdd` |  | Django testing strategies with pytest-django, TDD methodology, factory_boy, mocking, coverage, and testing Django REST Framework APIs. Use when writing Django or DRF tes… |
| skill | `django-verification` |  | Run the full Django verification loop — environment check, mypy/ruff/black linting, migration safety, pytest with coverage targets, pip-audit and bandit security scans,… |
| skill | `dmux-workflows` |  | Multi-agent orchestration using dmux (tmux pane manager for AI agents). Patterns for parallel agent workflows across Claude Code, Codex, OpenCode, and other harnesses. U… |
| skill | `docker-patterns` |  | Docker and Docker Compose patterns for local development, hardened CLI installer harnesses, container security, networking, volumes, and multi-service orchestration. Use… |
| skill | `docs-governance` |  | Route broad documentation-governance requests to existing ECC skills and run an opt-in, read-only audit of mapped documentation roles, links, ADR indexes, and evidence r… |
| skill | `documentation-lookup` |  | Use up-to-date library and framework docs via Context7 MCP instead of training data. Activates for setup questions, API references, code examples, or when the user names… |
| skill | `dotnet-patterns` |  | Idiomatic C# and .NET patterns, conventions, dependency injection, async/await, and best practices for building robust, maintainable .NET applications. Use when writing… |
| skill | `dynamic-workflow-mode` |  | Design task-local harnesses, eval gates, and reusable skill extraction for Claude dynamic workflow mode and other adaptive agent harnesses. Use when building a task-loca… |
| skill | `e2e-testing` |  | Playwright E2E testing patterns, Page Object Model, configuration, CI/CD integration, artifact management, and flaky test strategies. Use when writing Playwright tests,… |
| skill | `ecc-guide` |  | Answer questions about ECC by reading the live repo surface — agents, skills, commands, hooks, rules, install profiles, and docs — instead of memory. Use when the user a… |
| skill | `ecc-recipes` |  | Map a described workflow to the right ECC command group with run-order and stop condition, or browse all command-group recipe families read live from the commands direct… |
| skill | `ecc-tools-cost-audit` |  | Evidence-first ECC Tools burn and billing audit workflow. Use when investigating runaway PR creation, quota bypass, premium-model leakage, duplicate jobs, or GitHub App… |
| skill | `email-ops` |  | Evidence-first mailbox triage, drafting, send verification, and sent-mail-safe follow-up workflow for ECC. Use when the user wants to organize email, draft or send throu… |
| skill | `energy-procurement` |  | Procure electricity and natural gas for commercial and industrial facilities: tariff and rate-schedule optimization, demand-charge mitigation, supplier RFPs, fixed/index… |
| skill | `enterprise-agent-ops` |  | Operational controls for long-lived or cloud-hosted agent systems — runtime lifecycle (start, pause, stop, restart), observability (logs, metrics, traces), least-privile… |
| skill | `error-handling` |  | Patterns for robust error handling across TypeScript, Python, and Go. Covers typed errors, error boundaries, retries, circuit breakers, and user-facing error messages. U… |
| skill | `esign-field-placement` |  | Deterministic method for placing signature, date, and text fields in a web e-signature composer through a browser automation session, using a fixed signature page, numer… |
| skill | `eval-harness` |  | Eval-driven development (EDD) framework for AI coding sessions — define capability and regression evals before coding, grade with code-based, model-based, rule, or human… |
| skill | `evm-token-decimals` |  | Prevent silent decimal mismatch bugs across EVM chains. Covers runtime decimal lookup, chain-aware caching, bridged-token precision drift, and safe normalization for bot… |
| skill | `exa-search` |  | Neural search via Exa MCP for web, code, and company research. Use when the user needs web search, code examples, company intel, people lookup, or AI-powered deep resear… |
| skill | `fastapi-patterns` |  | FastAPI best practices covering project structure, Pydantic v2 schemas, dependency injection, async handlers, authentication, authorization, transactional service layers… |
| skill | `finance-billing-ops` |  | Evidence-first revenue, pricing, refunds, team-billing, and billing-model truth workflow for ECC. Use when the user wants a sales snapshot, pricing comparison, duplicate… |
| skill | `flox-environments` |  | Create reproducible, cross-platform (macOS/Linux) development environments with Flox, a declarative Nix-based environment manager. Use when setting up project toolchains… |
| skill | `flutter-dart-code-review` |  | Library-agnostic Flutter/Dart code review checklist covering widget best practices, state management patterns (BLoC, Riverpod, Provider, GetX, MobX, Signals), Dart idiom… |
| skill | `foundation-models-on-device` |  | Apple FoundationModels framework for on-device LLM — text generation, guided generation with @Generable, tool calling, and snapshot streaming in iOS 26+. Use when adding… |
| skill | `frontend-a11y` |  | Accessibility patterns for React and Next.js — semantic HTML, ARIA attributes, form labeling, keyboard navigation, focus management, and screen reader support. Use when… |
| skill | `frontend-design-direction` |  | Set an ECC-specific frontend design direction for production UI work. Use when building or improving websites, dashboards, applications, components, landing pages, visua… |
| skill | `frontend-patterns` |  | Frontend development patterns for React, Next.js, state management, performance optimization, and UI best practices. Use when building or reviewing React or Next.js comp… |
| skill | `fsharp-testing` |  | F# testing patterns with xUnit, FsUnit, Unquote, FsCheck property-based testing, integration tests, and test organization best practices. Use when writing F# tests with… |
| skill | `gan-style-harness` |  | GAN-inspired Generator-Evaluator agent harness for building high-quality applications autonomously. Based on Anthropic's March 2026 harness design paper. Use when a feat… |
| skill | `gateguard` |  | PreToolUse fact-forcing gate that denies the first Edit/Write/Bash (including MultiEdit and NotebookEdit) attempt until the agent presents concrete facts (importers, dat… |
| skill | `generating-python-installer` |  | Commercial-grade Python installer expert for Windows: Nuitka extreme compilation, dist slimming, DLL footprint analysis, and Inno Setup packaging to ship the smallest, f… |
| skill | `git-workflow` |  | Git workflow patterns including branching strategies, commit conventions, keeping history clean and readable, tidying local commits before merging, merge vs rebase, conf… |
| skill | `github-ops` |  | GitHub repository operations, automation, and management. Issue triage, PR management, CI/CD operations, release management, and security monitoring using the gh CLI. Us… |
| skill | `golang-patterns` |  | Idiomatic Go patterns, best practices, and conventions for building robust, efficient, and maintainable Go applications. Use when writing or reviewing Go code and idioma… |
| skill | `golang-testing` |  | Go testing patterns including table-driven tests, subtests, benchmarks, fuzzing, and test coverage. Follows TDD methodology with idiomatic Go practices. Use when writing… |
| skill | `growth-log` |  | Write growth log entries that extract reusable patterns from completed work — root cause, transferable rule, and a recognizable signal — instead of diary-style event nar… |
| skill | `healthcare-cdss-patterns` |  | Clinical Decision Support System (CDSS) development patterns. Drug interaction checking, dose validation, clinical scoring (NEWS2, qSOFA), alert severity classification,… |
| skill | `healthcare-emr-patterns` |  | EMR/EHR development patterns for healthcare applications. Clinical safety, encounter workflows, prescription generation, clinical decision support integration, and acces… |
| skill | `healthcare-eval-harness` |  | Patient safety evaluation harness for healthcare application deployments. Automated test suites for CDSS accuracy, PHI exposure, clinical workflow integrity, and integra… |
| skill | `healthcare-phi-compliance` |  | Protected Health Information (PHI) and PII compliance patterns for healthcare applications: data classification, row-level access control, tamper-proof audit trails, sch… |
| skill | `hermes-imports` |  | Convert local Hermes operator workflows into sanitized ECC skills and release-pack artifacts. Use when preparing a Hermes workflow for public ECC reuse without leaking p… |
| skill | `hexagonal-architecture` |  | Design, implement, and refactor Ports & Adapters systems with clear domain boundaries, dependency inversion, and testable use-case orchestration across TypeScript, Java,… |
| skill | `hipaa-compliance` |  | HIPAA-specific entrypoint for healthcare privacy and security work. Use when a task is explicitly framed around HIPAA, PHI handling, covered entities, BAAs, breach postu… |
| skill | `homelab-network-readiness` |  | Readiness checklist for homelab VLAN segmentation, local DNS filtering (Pi-hole, AdGuard Home), and WireGuard-style remote access. Use when planning or reviewing home ne… |
| skill | `homelab-network-setup` |  | Practical home and homelab network planning for gateways, switches, access points, IP ranges, DHCP reservations, DNS, cabling, and common beginner mistakes. Use when pla… |
| skill | `homelab-pihole-dns` |  | Pi-hole installation, blocklist management, DNS-over-HTTPS setup, DHCP integration, local DNS records, and troubleshooting broken DNS resolution on a home network. Use w… |
| skill | `homelab-vlan-segmentation` |  | Segmenting home networks into VLANs for IoT, guest, trusted, and server traffic using UniFi, pfSense/OPNsense, and MikroTik — including switch trunk config, firewall rul… |
| skill | `homelab-wireguard-vpn` |  | WireGuard VPN server setup, peer configuration, key generation, split tunneling vs full tunnel routing, and remote access to a home network from mobile and laptop client… |
| skill | `hookify-rules` |  | Create and configure hookify rules — markdown files with YAML frontmatter that match bash, file, prompt, or stop events by regex or conditions and show warn/block messag… |
| skill | `i18n-sync` |  | Translate and synchronize application JSON locale files using source-key usage, project terminology, and focused validation. Use when adding keys or languages, updating… |
| skill | `inherit-legacy-style` |  | Prevent AI style drift on legacy projects by scanning the codebase for implicit conventions, resolving conflicts with the operator one at a time, and writing an enforcea… |
| skill | `intent-driven-development` |  | Turn ambiguous or high-impact product and engineering changes into scoped, verifiable acceptance criteria before or alongside implementation. Use when a user asks to cla… |
| skill | `inventory-demand-planning` |  | Codified demand planning expertise for multi-location retailers: demand forecasting method selection, ABC/XYZ segmentation, safety stock and reorder-point optimization,… |
| skill | `investor-materials` |  | Create and update pitch decks, one-pagers, investor memos, accelerator applications, financial models, and fundraising materials. Use when the user needs investor-facing… |
| skill | `investor-outreach` |  | Draft cold emails, warm intro blurbs, follow-ups, update emails, and investor communications for fundraising. Use when the user wants outreach to angels, VCs, strategic… |
| skill | `ios-icon-gen` |  | Generate iOS app icons as PNG imagesets for Xcode asset catalogs from SF Symbols (5000+ Apple-native) or Iconify API (275k+ open source icons from 200+ collections). Use… |
| skill | `issue-review` |  | Review a GitHub issue the way /code-review reviews a PR. Fetches the issue with the gh CLI, checks the report against the current codebase, searches for duplicates and p… |
| skill | `iterative-retrieval` |  | Pattern for progressively refining context retrieval to solve the subagent context problem. Use when a subagent lacks the context it needs and retrieval must be refined… |
| skill | `ito-baskets` |  | Read-only Itô basket and prediction-market data skill. Index the live basket catalog, compare a basket against user-supplied research or a watchlist, build a source-grou… |
| skill | `ito-compute` |  | Query live GPU inventory, submit an authenticated Itô fixed-rate RFQ, inspect RFQ or procurement status, revoke device credentials, and run explicitly gated node qualifi… |
| skill | `ito-inference` |  | Inspect the availability of model serving on a completed Itô compute booking and, when the canonical backend becomes available, hand off an explicitly confirmed serving… |
| skill | `ito-training` |  | Inspect the availability of ML training on a completed Itô compute booking and, when the canonical backend becomes available, hand off an explicitly confirmed training m… |
| skill | `java-coding-standards` |  | Java coding standards for Spring Boot and Quarkus services: naming, immutability, Optional usage, streams, exceptions, generics, CDI, reactive patterns, and project layo… |
| skill | `jira-integration` |  | Use this skill when retrieving Jira tickets, analyzing requirements, updating ticket status, adding comments, or transitioning issues. Provides Jira API patterns via MCP… |
| skill | `jpa-patterns` |  | JPA/Hibernate patterns for entity design, relationships, query optimization, transactions, auditing, indexing, pagination, and pooling in Spring Boot. Use when designing… |
| skill | `knowledge-ops` |  | Knowledge base management, ingestion, sync, and retrieval across multiple storage layers (local files, MCP memory, vector stores, Git repos). Use when the user wants to… |
| skill | `kotlin-coroutines-flows` |  | Kotlin Coroutines and Flow patterns for Android and KMP — structured concurrency, Flow operators, StateFlow, error handling, and testing. Use when writing coroutines or… |
| skill | `kotlin-exposed-patterns` |  | JetBrains Exposed ORM patterns including DSL queries, DAO pattern, transactions, HikariCP connection pooling, Flyway migrations, and repository pattern. Use when working… |
| skill | `kotlin-ktor-patterns` |  | Ktor server patterns including routing DSL, plugins, authentication, Koin DI, kotlinx.serialization, WebSockets, and testApplication testing. Use when building a Ktor se… |
| skill | `kotlin-patterns` |  | Idiomatic Kotlin patterns, best practices, and conventions for building robust, efficient, and maintainable Kotlin applications with coroutines, null safety, and DSL bui… |
| skill | `kotlin-testing` |  | Kotlin testing patterns with Kotest, MockK, coroutine testing, property-based testing, and Kover coverage. Follows TDD methodology with idiomatic Kotlin practices. Use w… |
| skill | `kubernetes-patterns` |  | Kubernetes workload patterns, resource management, RBAC, probes, autoscaling, ConfigMap/Secret handling, and kubectl debugging for production-grade deployments. Use when… |
| skill | `laravel-patterns` |  | Laravel architecture patterns, routing/controllers, Eloquent ORM, service layers, queues, events, caching, and API resources for production apps. Use when building or re… |
| skill | `laravel-plugin-discovery` |  | Discover and evaluate Laravel packages via LaraPlugins.io MCP. Use when the user wants to find plugins, check package health, or assess Laravel/PHP compatibility. |
| skill | `laravel-security` |  | Laravel security best practices — authentication, authorization, Eloquent safety, CSRF, XSS prevention, API security, and secure deployment configurations. Use when revi… |
| skill | `laravel-tdd` |  | Laravel testing strategies with PHPUnit, Pest, model factories, HTTP tests, Sanctum authentication testing, mocking, and coverage. Use when writing Laravel tests with PH… |
| skill | `laravel-verification` |  | Verification loop for Laravel projects: env checks, linting, static analysis, tests with coverage, security scans, and deployment readiness. Use when verifying a Laravel… |
| skill | `latency-critical-systems` |  | Optimize and verify latency-sensitive systems — realtime dashboards, market data feeds, streaming agents, execution gateways, queues, and caches — by tracking p50/p95/p9… |
| skill | `lead-intelligence` |  | AI-native lead intelligence and outreach pipeline. Replaces Apollo, Clay, and ZoomInfo with agent-powered signal scoring, mutual ranking, warm path discovery, source-der… |
| skill | `liquid-glass-design` |  | iOS 26 Liquid Glass design system — dynamic glass material with blur, reflection, and interactive morphing for SwiftUI, UIKit, and WidgetKit. Use when building iOS 26 Li… |
| skill | `living-docs-governance` |  | Keep a long-lived project's documentation from rotting by assigning existing project docs clear constitution, map, status, and history roles, then wiring the active agen… |
| skill | `llm-trading-agent-security` |  | Security patterns for autonomous trading agents with wallet or transaction authority. Covers prompt injection, spend limits, pre-send simulation, circuit breakers, MEV p… |
| skill | `logistics-exception-management` |  | Codified freight-exception handling expertise for shipment delays, damages, losses, shortages, and carrier disputes, with escalation protocols, carrier-specific behavior… |
| skill | `loop-design-check` |  | Design a goal-oriented agent loop or review one for failure modes: spinning, Goodhart-gaming the verifier, or running a wrong answer to completion. Covers machine-decida… |
| skill | `mailtrap-email-integration` |  | Guides agents through integrating transactional email sending via Mailtrap's Email API, including sandbox testing, domain verification, and API authentication. Use when… |
| skill | `make-interfaces-feel-better` |  | Apply concrete design-engineering details that make interfaces feel polished. Use when reviewing or improving UI spacing, typography, borders, shadows, motion, hit areas… |
| skill | `master-agreement-generator` |  | Generate review drafts of counterparty master agreements from one template plus a JSON spec, with role-selected clauses and a Schedule A workflow limited to the executed… |
| skill | `mcp-dependency-review` |  | Statically review MCP configuration for mutable package references before approval or CI, without executing discovered MCP servers. Use when reviewing .mcp.json, Cursor,… |
| skill | `mcp-server-patterns` |  | Build MCP servers with Node/TypeScript SDK — tools, resources, prompts, Zod validation, stdio vs Streamable HTTP. Use Context7 or official MCP docs for latest API. Use w… |
| skill | `messages-ops` |  | Evidence-first live messaging workflow for ECC. Use when the user wants to read texts or DMs, recover a recent one-time code, inspect a thread before replying, or prove… |
| skill | `ml-adoption-playbook` |  | End-to-end methodology for AI agents and software engineers to add machine learning algorithms to existing non-ML codebases. Covers problem framing, data readiness, arch… |
| skill | `mle-workflow` |  | Production machine-learning engineering workflow for data contracts, reproducible training, model evaluation, deployment, monitoring, and rollback. Use when building, re… |
| skill | `module-governance` |  | Establish or maintain a business module's local agent instructions, domain-context links, and interface ownership when implementing a new module or changing its responsi… |
| skill | `module-regression` |  | Govern cross-module regression in large repositories with a REGRESSION.md ledger that records each module's downstream consumers and executable acceptance command. After… |
| skill | `motion-advanced` |  | Advanced motion patterns for React / Next.js — drag & drop, gestures, text animations, SVG path drawing, custom hooks, imperative sequences (useAnimate), loaders, and th… |
| skill | `motion-foundations` |  | Motion tokens, spring presets, performance rules, device adaptation, accessibility enforcement, and SSR safety for React / Next.js using motion/react. Foundation layer —… |
| skill | `motion-patterns` |  | Production-ready animation patterns for React / Next.js — button, modal, toast, stagger, page transitions, exit animations, scroll, and layout — built on motion-foundati… |
| skill | `mybatis-patterns` |  | MyBatis and MyBatis-Spring patterns for mapper design, XML and annotation SQL, result mapping, dynamic SQL safety, transactions, batching, pagination, and query performa… |
| skill | `mysql-patterns` |  | MySQL and MariaDB schema, query, indexing, transaction, replication, and connection-pool patterns for production backends. Use when designing MySQL or MariaDB schemas an… |
| skill | `nanoclaw-repl` |  | Operate and extend NanoClaw, ECC's zero-dependency session-aware REPL, with persistent markdown-backed sessions and slash commands for model switching, skill loading, se… |
| skill | `nasiko-control-plane` |  | Manage the experimental Nasiko CLI lifecycle through ECC — read-only status checks, consent-gated install of the pinned qualified version with dry-run preview, and owner… |
| skill | `nestjs-patterns` |  | NestJS architecture patterns for modules, controllers, providers, DTO validation, guards, interceptors, config, and production-grade TypeScript backends. Use when buildi… |
| skill | `netmiko-ssh-automation` |  | Safe Python Netmiko patterns for read-only collection, bounded batch SSH, TextFSM parsing, guarded config changes, timeouts, and network automation error handling. Use w… |
| skill | `network-bgp-diagnostics` |  | Diagnostics-only BGP troubleshooting patterns for neighbor state, route exchange, prefix policy, AS path inspection, and safe evidence collection. Use when a BGP neighbo… |
| skill | `network-config-validation` |  | Pre-deployment checks for router and switch configuration, including dangerous commands, duplicate addresses, subnet overlaps, stale references, management-plane risk, a… |
| skill | `network-interface-health` |  | Diagnose interface errors, drops, CRCs, duplex mismatches, flapping, speed negotiation issues, and counter trends on routers, switches, and Linux hosts. Use when an inte… |
| skill | `nextjs-turbopack` |  | Next.js 16+ and Turbopack guidance — incremental Rust bundling, file-system caching, faster dev startup and HMR, Turbopack vs webpack tradeoffs, and the middleware.ts to… |
| skill | `nodejs-keccak256` |  | Prevent Ethereum hashing bugs in JavaScript and TypeScript. Node's sha3-256 is NIST SHA3, not Ethereum Keccak-256, and silently breaks selectors, signatures, storage slo… |
| skill | `nutrient-document-processing` |  | Process, convert, OCR, extract, redact, sign, and fill documents using the Nutrient DWS API. Works with PDFs, DOCX, XLSX, PPTX, HTML, and images. Use when converting, OC… |
| skill | `nuxt4-patterns` |  | Nuxt 4 app patterns for hydration safety, performance, route rules, lazy loading, and SSR-safe data fetching with useFetch and useAsyncData. Use when building or reviewi… |
| skill | `openclaw-persona-forge` |  | 为 OpenClaw AI Agent 锻造完整的龙虾灵魂方案。根据用户偏好或随机抽卡， 输出身份定位、灵魂描述(SOUL.md)、角色化底线规则、名字和头像生图提示词。 如当前环境提供已审核的生图 skill，可自动生成统一风格头像图片。 当用户需要创建、设计或定制 OpenClaw 龙虾灵魂时使用。 不适用于：微调已有 SOUL.m… |
| skill | `opensource-pipeline` |  | Open-source pipeline: fork, sanitize, and package private projects for safe public release. Chains 3 agents (forker, sanitizer, packager). Triggers: '/opensource', 'open… |
| skill | `operator-approval-loop` |  | Operator approval contract with internal filing notices for agent-drafted outbound messages, hashed drafts, epoch-keyed decisions, durable delivery claims and receipts,… |
| skill | `orch-add-feature` |  | Orchestrate building a brand-new feature end to end — research, plan, TDD implementation, review, and gated commit — by delegating each phase to the matching ECC agent.… |
| skill | `orch-build-mvp` |  | Orchestrate bootstrapping a working MVP from a design or spec document — ingest the SDD/PRD, plan thin vertical slices, scaffold the first end-to-end slice, then drive a… |
| skill | `orch-change-feature` |  | Orchestrate altering an existing, working feature to new desired behavior — update its tests to the new spec, change the implementation to match, review, and gated commi… |
| skill | `orch-fix-defect` |  | Orchestrate fixing a bug — reproduce it as a failing regression test, fix to green, review, and gated commit — by delegating each phase to the matching ECC agent. Use wh… |
| skill | `orch-pipeline` |  | Shared orchestration engine behind the orch-* skill family — the gated Research-Plan-TDD-Review-Commit pipeline, size classifier, agent and command map, and two human ga… |
| skill | `orch-refine-code` |  | Orchestrate a behavior-preserving refactor — confirm tests are green, restructure without changing behavior, keep tests green, review, and gated commit. Use when the str… |
| skill | `osint-investigation` |  | Sparse-clue OSINT investigation methodology for extracting overlooked leads, connecting fragmented evidence, and testing explanations across sources. Use for multi-step… |
| skill | `parallel-execution-optimizer` |  | Speed up a task by turning it into a dependency graph of parallel lanes with a lane matrix, batched reads and checks, write surfaces isolated by file, worktree, branch,… |
| skill | `perl-patterns` |  | Modern Perl 5.36+ idioms, best practices, and conventions for building robust, maintainable Perl applications. Use when writing or reviewing modern Perl 5.36+ code. |
| skill | `perl-security` |  | Comprehensive Perl security covering taint mode, input validation, safe process execution, DBI parameterized queries, web security (XSS/SQLi/CSRF), and perlcritic securi… |
| skill | `perl-testing` |  | Perl testing patterns using Test2::V0, Test::More, prove runner, mocking, coverage with Devel::Cover, and TDD methodology. Use when writing Perl tests with Test2::V0 or… |
| skill | `plan-canvas` |  | Open plans and HTML artifacts in a local browser canvas where the human annotates elements, chats, and approves or requests changes without leaving the page. Use when pr… |
| skill | `plan-orchestrate` |  | Read a plan document, decompose it into steps, classify each step, and emit the ready-to-paste ECC slash command for that step, carrying the step identifier and scope in… |
| skill | `plankton-code-quality` |  | Write-time code quality enforcement using Plankton — auto-formatting, linting, and Claude-powered fixes on every file edit via hooks. Use when setting up write-time form… |
| skill | `postgres-patterns` |  | PostgreSQL database patterns for query optimization, schema design, indexing, and security. Based on Supabase best practices. Use when designing PostgreSQL schemas, inde… |
| skill | `prediction-market-oracle-research` |  | Research prediction markets as data sources or oracle signals for products, agents, dashboards, and corporate decision intelligence. Use for source-grounded analysis of… |
| skill | `prediction-market-risk-review` |  | Review prediction-market, basket, oracle, and trading-agent workflows for compliance, safety, data-quality, privacy, and execution risk. Use before any workflow handles… |
| skill | `prisma-patterns` |  | Prisma ORM patterns for TypeScript backends — schema design, query optimization, transactions, pagination, and critical traps like updateMany returning count not records… |
| skill | `product-capability` |  | Translate PRD intent, roadmap asks, or product discussions into an implementation-ready capability plan that exposes constraints, invariants, interfaces, and unresolved… |
| skill | `product-lens` |  | Validate the why before building through four product diagnostics — a YC-style product diagnostic that produces PRODUCT-BRIEF.md with a go/no-go recommendation, a founde… |
| skill | `production-audit` |  | Local-evidence production readiness audit for shipped apps, pre-launch reviews, post-merge checks, and "what breaks in prod?" questions without sending repo data to an e… |
| skill | `production-scheduling` |  | Codified expertise for production scheduling, job sequencing, line balancing, changeover optimization, and bottleneck resolution in discrete and batch manufacturing. Inf… |
| skill | `project-flow-ops` |  | Operate execution flow across GitHub and Linear by triaging issues and pull requests, linking active work, and keeping GitHub public-facing while Linear remains the inte… |
| skill | `prompt-caching-strategy` |  | Optimize LLM prompt caching hit rate to reduce API costs and improve latency. Analyzes prompt structure, identifies cacheable vs non-cacheable content, and recommends re… |
| skill | `prompt-optimizer` |  | Analyze draft prompts, detect intent and missing context, match ECC commands, skills, and agents, and output a ready-to-paste optimized prompt with diagnosis and rationa… |
| skill | `python-patterns` |  | Pythonic idioms, PEP 8 standards, type hints, and best practices for building robust, efficient, and maintainable Python applications. Use when writing or reviewing Pyth… |
| skill | `python-testing` |  | Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements. Use when writing pytest tests — fixtures, mocks,… |
| skill | `pytorch-patterns` |  | PyTorch deep learning patterns and best practices for building robust, efficient, and reproducible training pipelines, model architectures, and data loading. Use when wr… |
| skill | `quality-nonconformance` |  | Quality control and non-conformance management for regulated manufacturing (FDA 21 CFR 820, IATF 16949, AS9100): NCR lifecycle and disposition, 5-Why/Ishikawa/fault-tree… |
| skill | `quarkus-patterns` |  | Quarkus 3.x LTS architecture patterns with Camel for messaging, RESTful API design, CDI services, data access with Panache, and async processing. Use for Java Quarkus ba… |
| skill | `quarkus-security` |  | Quarkus security implementation patterns: JWT and OIDC authentication, @RolesAllowed RBAC and SecurityIdentity checks, Bean Validation and custom validators, parameteriz… |
| skill | `quarkus-tdd` |  | Test-driven development for Quarkus 3.x LTS using JUnit 5, Mockito, REST Assured, Camel testing, and JaCoCo. Use when adding features, fixing bugs, or refactoring event-… |
| skill | `quarkus-verification` |  | Verification loop for Quarkus projects: build, static analysis (Checkstyle, PMD, SpotBugs), tests with JaCoCo coverage, OWASP dependency and container security scans, Gr… |
| skill | `rails-patterns` |  | Ruby on Rails framework patterns for Rails 7.1+ and 8.x apps. Covers the directory contract, skinny controllers with service objects, form objects, query objects, idioma… |
| skill | `ralphinho-rfc-pipeline` |  | Split an RFC into a multi-agent execution DAG — decompose into work units with dependencies and acceptance tests, run research, plan, implement, test, and review per uni… |
| skill | `react-native-patterns` |  | React Native and Expo app patterns — Expo Router navigation, state separation (server/client/route/form), TanStack Query data fetching with Zod, performant lists, Native… |
| skill | `react-patterns` |  | React 18/19 patterns including hooks discipline, server/client component boundaries, Suspense + error boundaries, form actions, data fetching, state management decision… |
| skill | `react-performance` |  | React and Next.js performance optimization patterns adapted from Vercel Engineering's React Best Practices (https://github.com/vercel-labs/agent-skills). Organizes 70+ r… |
| skill | `react-testing` |  | React component testing with React Testing Library, Vitest/Jest, MSW for network mocking, accessibility assertions with axe, and the decision boundary between component… |
| skill | `recsys-pipeline-architect` |  | Design composable recommendation, ranking, and feed pipelines using the six-stage Source→Hydrator→Filter→Scorer→Selector→SideEffect framework popularized by xAI's open-s… |
| skill | `recursive-decision-ledger` |  | Run repeated rollouts ("Prime Gauss" style recursive prompting) while keeping an append-only decision ledger of trials, marks, coherence checks, and promotion gates, so… |
| skill | `redis-patterns` |  | Redis data structure patterns, caching strategies, distributed locks, rate limiting, pub/sub, and connection management for production applications. Use when adding cach… |
| skill | `regex-vs-llm-structured-text` |  | Decision framework for parsing structured text (quizzes, forms, invoices, receipts, tables) with a hybrid regex-first pipeline — regex extraction handles 95%+ cheaply, a… |
| skill | `repo-scan` |  | Bootstrap pointer that installs the external repo-scan skill from a pinned, reviewable commit. Use when repo-scan must be installed before running its cross-stack source… |
| skill | `research-ops` |  | Evidence-first current-state research workflow for ECC. Use when the user wants fresh facts, comparisons, enrichment, or a recommendation built from current public evide… |
| skill | `returns-reverse-logistics` |  | Codified expertise for returns authorization, receipt and inspection, disposition decisions, refund processing, fraud detection, and warranty claims management. Informed… |
| skill | `rules-distill` |  | Scan skills to extract cross-cutting principles and distill them into rules — append, revise, or create new rule files. Use when the same principle keeps recurring acros… |
| skill | `rust-patterns` |  | Idiomatic Rust patterns, ownership, error handling, traits, concurrency, and best practices for building safe, performant applications. Use when writing or reviewing Rus… |
| skill | `rust-testing` |  | Rust testing patterns including unit tests, integration tests, async testing, property-based testing, mocking, and coverage. Follows TDD methodology. Use when writing Ru… |
| skill | `safety-guard` |  | Guard against destructive operations with three modes: Careful intercepts dangerous commands (rm -rf, git push --force, DROP TABLE) for confirmation, Freeze locks writes… |
| skill | `santa-method` |  | Multi-agent adversarial verification: two independent reviewers with the same rubric must both pass before output ships, with a fix-and-re-review convergence loop and hu… |
| skill | `scientific-db-pubmed-database` |  | Direct PubMed and NCBI E-utilities search workflows for biomedical literature, MeSH queries, PMID lookup, citation retrieval, and API-backed literature monitoring. Use w… |
| skill | `scientific-db-uspto-database` |  | USPTO patent and trademark data workflow for official record lookup, PatentSearch queries, TSDR checks, assignment data, and reproducible IP research logs. Use when a ta… |
| skill | `scientific-pkg-gget` |  | gget CLI and Python workflow for quick genomic database queries, sequence lookup, BLAST-style searches, enrichment checks, and reproducible bioinformatics evidence logs.… |
| skill | `scientific-thinking-literature-review` |  | Systematic literature-review workflow for academic, biomedical, technical, and scientific topics, including search planning, source screening, synthesis, citation checks… |
| skill | `scientific-thinking-scholar-evaluation` |  | Structured scholarly-work evaluation for papers, proposals, literature reviews, methods sections, evidence quality, citation support, and research-writing feedback. Use… |
| skill | `search-first` |  | Research-before-coding workflow: search npm/PyPI, MCP servers, skills, and GitHub for existing tools before writing custom code, then adopt, extend, or build. Launches t… |
| skill | `security-bounty-hunter` |  | Hunt for exploitable, bounty-worthy security issues in repositories. Focuses on remotely reachable vulnerabilities that qualify for real reports instead of noisy local-o… |
| skill | `security-review` |  | Use this skill when adding authentication, handling user input, working with secrets, creating API endpoints, or implementing payment/sensitive features. Provides compre… |
| skill | `security-scan` |  | Scan your Claude Code configuration (.claude/ directory) for security vulnerabilities, misconfigurations, and injection risks using AgentShield. Checks CLAUDE.md, settin… |
| skill | `skill-comply` |  | Visualize whether skills, rules, and agent definitions are actually followed — auto-generates scenarios at 3 prompt strictness levels, runs agents, classifies behavioral… |
| skill | `skill-host-compat` |  | Lint ECC skills for Codex/Cursor-safe frontmatter and Claude-only substitutions before a skill PR. |
| skill | `skill-scout` |  | Search existing local, marketplace, GitHub, and web skill sources before creating a new skill. Use when the user wants to create, build, fork, or find a skill for a work… |
| skill | `skill-stocktake` |  | Use when auditing Claude skills and commands for quality. Supports Quick Scan (changed skills only) and Full Stocktake modes with sequential subagent batch evaluation. |
| skill | `social-graph-ranker` |  | Weighted social-graph ranking for warm intro discovery, bridge scoring, and network gap analysis across X and LinkedIn. Use when the user wants the reusable graph-rankin… |
| skill | `springboot-patterns` |  | Spring Boot architecture patterns, REST API design, layered services, data access, caching, async processing, and logging. Use for Java Spring Boot backend work. Use whe… |
| skill | `springboot-security` |  | Spring Security best practices for authn/authz, validation, CSRF, secrets, headers, rate limiting, and dependency security in Java Spring Boot services. Use when reviewi… |
| skill | `springboot-tdd` |  | Test-driven development for Spring Boot using JUnit 5, Mockito, MockMvc, Testcontainers, and JaCoCo. Use when adding features, fixing bugs, or refactoring. |
| skill | `springboot-verification` |  | Run the full Spring Boot verification loop — Maven or Gradle build, SpotBugs, PMD, and Checkstyle static analysis, unit and Testcontainers integration tests with JaCoCo… |
| skill | `story-lifecycle` |  | Manage a file-based epic → story → sprint development loop without requiring an external project management tool. Creates and tracks epics, breaks them into user stories… |
| skill | `strategic-compact` |  | Suggests manual context compaction at logical intervals to preserve context through task phases rather than arbitrary auto-compaction. Use when a session is approaching… |
| skill | `swift-actor-persistence` |  | Thread-safe data persistence in Swift using actors — in-memory cache with file-backed storage, eliminating data races by design. Use when persisting data in Swift and a… |
| skill | `swift-concurrency-6-2` |  | Swift 6.2 Approachable Concurrency — single-threaded by default, @concurrent for explicit background offloading, isolated conformances for main actor types. Use when ado… |
| skill | `swift-protocol-di-testing` |  | Protocol-based dependency injection for testable Swift code — mock file system, network, and external APIs using focused protocols and Swift Testing. Use when Swift code… |
| skill | `swiftui-patterns` |  | SwiftUI architecture patterns, state management with @Observable, view composition, navigation, performance optimization, and modern iOS/macOS UI best practices. Use whe… |
| skill | `taste-application` |  | Generate new video against a distilled style pack and cut it into a finished piece - plan takes from the reference's cut rhythm, generate on fal, grade with the pack's m… |
| skill | `taste-distillation` |  | Measure a set of reference videos into a reusable style pack - colour grade as a 3D LUT, cut rhythm as a shot-length distribution, hero stills, screen-blend overlay plat… |
| skill | `tasteforge-video` |  | Use for file-driven multimodal image, video, and 3D-asset discovery; taste interviews; distill or apply workflows; style-pack validation; editable EDL/FCPXML export; pro… |
| skill | `tdd-workflow` |  | Test-driven development workflow: write a failing test first, watch it fail, implement the smallest change to green, then refactor with 80%+ coverage across unit, integr… |
| skill | `team-agent-orchestration` |  | Run team-based orchestration for agent squads: work items with owners and scope, agent Kanban state, branch isolation, control pane visibility, and merge gates. Use when… |
| skill | `team-builder` |  | Interactive picker that discovers available agent personas via the claude agents command and agents/ markdown globs, groups them into domains, has the user select up to… |
| skill | `terminal-opener` |  | Open an executable and its argument array in a visible terminal window through a reusable, shell-free launch plan with dry-run, JSON, capability detection, detached fall… |
| skill | `terminal-ops` |  | Evidence-first repo execution workflow for ECC. Use when the user wants a command run, a repo checked, a CI failure debugged, or a narrow fix pushed with exact proof of… |
| skill | `test-collaboration` |  | Inventory and govern a project's test assets. Connect requirements, business rules, risks, bugs, and cross-boundary contracts to stable TEST-IDs and executable evidence… |
| skill | `tinystruct-patterns` |  | Expert guidance for developing with the tinystruct Java framework. Use when working on the tinystruct codebase or any project built on tinystruct — including generating… |
| skill | `token-budget-advisor` |  | Offer a choice of response depth (25%/50%/75%/100%) with token estimates before answering, then answer at that level. Use when the user asks to control response length o… |
| skill | `token-card` |  | Render a token-usage stat card from local Claude Code, Codex, Gemini CLI, and OpenCode session logs and commit it into the repository as a file. Use when someone wants a… |
| skill | `typescript-patterns` |  | TypeScript patterns for strict, type-safe, maintainable code in modern TypeScript and JavaScript applications. Covers strict compiler configuration, type design, narrowi… |
| skill | `ui-to-vue` |  | Use when the user has UI screenshots or design exports that need batch conversion into Vue 3 components, especially with Vant, Element Plus, or Ant Design Vue. |
| skill | `uncloud` |  | Use when managing an Uncloud cluster — deploying services, configuring Caddy ingress, adding static proxy routes for non-cluster devices, publishing ports, scaling, insp… |
| skill | `unified-memory` |  | Share durable, inspectable context and handoffs between Claude, Codex, Hermes, Cursor, OpenCode, and other agents through the local ECC Memory Vault. Use when an agent m… |
| skill | `unified-notifications-ops` |  | Operate notifications as one ECC-native workflow across GitHub, Linear, desktop alerts, hooks, and connected communication surfaces. Use when the real problem is alert r… |
| skill | `verification-loop` |  | Run a six-phase verification of a Claude Code session's work — build, type check, lint, tests with coverage, security grep, and diff review — then produce a PASS/FAIL ve… |
| skill | `visa-doc-translate` |  | Translate visa document images (bank deposit, employment, income, and retirement certificates; HEIC, PNG, or JPG) into English via OCR and produce a bilingual PDF pairin… |
| skill | `vite-patterns` |  | Vite build tool patterns including config, plugins, HMR, env variables, proxy setup, SSR, library mode, dependency pre-bundling, and build optimization. Activate when wo… |
| skill | `vue-patterns` |  | Vue.js 3 Composition API patterns, component architecture, reactivity best practices, Pinia state management, Vue Router navigation, and Nuxt SSR patterns. Activates for… |
| skill | `windows-desktop-e2e` |  | E2E testing for Windows native desktop apps (WPF, WinForms, Win32/MFC, Qt) using pywinauto and Windows UI Automation. Use when writing E2E tests for a Windows native des… |
| skill | `workspace-surface-audit` |  | Audit the active repo, MCP servers, plugins, connectors, env surfaces, and harness setup, then recommend the highest-value ECC-native skills, hooks, agents, and operator… |
| skill | `x-api` |  | X/Twitter API integration for posting tweets, threads, reading timelines, search, and analytics. Covers OAuth auth patterns, rate limits, and platform-native content pos… |

## marketing

Sursă: marketplace `knowledge-work-plugins`, versiunea 1.2.0.

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| skill | `campaign-plan` | ★★★ | **plan de campanie (lansare program, provocare 30 zile).** Generate a full campaign brief with objectives, audience, messaging, channel strategy, content calendar, and success metrics. Use when planning a product launch, lead-ge… |
| skill | `content-creation` | ★★★ | **postări, articole, captions pe canal.** Draft marketing content across channels — blog posts, social media, email newsletters, landing pages, press releases, and case studies. Use when writing any marketing co… |
| skill | `draft-content` | ★★★ | **ciorne rapide de conținut.** Draft blog posts, social media, email newsletters, landing pages, press releases, and case studies with channel-specific formatting and SEO recommendations. Use when wri… |
| skill | `brand-review` | ★★ | **verifică textul față de brand.** Review content against your brand voice, style guide, and messaging pillars, flagging deviations by severity with specific before/after fixes. Use when checking a draft… |
| skill | `competitive-brief` | ★★ | **analiză concurență (alte săli, antrenori).** Research competitors and generate a positioning and messaging comparison with content gaps, opportunities, and threats. Use when building sales battlecards, when finding… |
| skill | `email-sequence` | ★★ | **secvențe email pentru clienți noi.** Design and draft multi-email sequences with full copy, timing, branching logic, exit conditions, and performance benchmarks. Use when building onboarding, lead nurture,… |
| skill | `performance-report` | ★★ | **raport rezultate campanie.** Build a marketing performance report with key metrics, trend analysis, wins and misses, and prioritized optimization recommendations. Use when wrapping a campaign, when… |
| skill | `seo-audit` | ★ | **audit SEO site.** Run a comprehensive SEO audit — keyword research, on-page analysis, content gaps, technical checks, and competitor comparison. Use when assessing a site's SEO health, wh… |

## superpowers

Sursă: marketplace `superpowers-dev`, versiunea 7.0.2. Are hook-uri (rulează automat la anumite evenimente).

| Tip | Nume | Fitness | La ce folosește |
|---|---|---|---|
| skill | `brainstorming` | ★★ | **rafinează o idee înainte de execuție.** You MUST use this before any creative work - creating features, building components, adding functionality, modifying behavior, or planning anything new, in software or o… |
| skill | `diagnosing-superpowers` |  | Use when a superpowers session went wrong and your human partner wants to know why — repeated work, ignored plans, stumbles, poor results, a skill that didn't fire, "it… |
| skill | `dispatching-parallel-agents` |  | Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies |
| skill | `executing-plans` |  | Use when executing an implementation plan in the current session as the implementer yourself — your human partner chose inline execution, or no subagent tool is available |
| skill | `finishing-a-development-branch` |  | Use when implementation is complete, all tests pass, and you need to decide how to integrate the work |
| skill | `receiving-code-review` |  | Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and… |
| skill | `requesting-code-review` |  | Use when completing tasks, implementing major features, or before merging to verify work meets requirements |
| skill | `subagent-driven-development` |  | Use when executing implementation plans with independent tasks in the current session |
| skill | `systematic-debugging` |  | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes |
| skill | `test-driven-development` |  | Use when implementing any feature or bugfix, before writing implementation code |
| skill | `using-git-worktrees` |  | Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native too… |
| skill | `using-superpowers` |  | Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions |
| skill | `verification-before-completion` |  | Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before maki… |
| skill | `writing-plans` |  | Use when you have a spec or requirements for a multi-step task, before touching code |
| skill | `writing-skills` |  | Use when creating new skills, editing existing skills, or verifying skills work before deployment |

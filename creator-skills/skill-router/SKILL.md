---
name: skill-router
description: "The dispatcher. Fires before answering generically whenever a request is vague, open-ended, situational, or when the operator doesn't know which skill, agent, or plugin to use. Trigger phrases: \"help me with...\", \"I need to...\", \"what should I use for...\", \"I'm not sure how to...\", \"how do I...\", \"what can I use to...\", \"I have a problem with...\", \"I forgot which skill...\", \"which skill handles...\", \"what tool should I use for...\". Also fires when the operator describes a situation without naming a task — \"I have a baptism shoot\", \"I'm building a new website\", \"I want to grow my YouTube channel\", \"I need to edit these photos\". Do NOT fire if the request is already task-specific and clearly maps to one skill, if the operator explicitly names the skill to use, or if the request is purely conversational with no workflow involved. Use this BEFORE answering generically — a skill almost always exists for the task."
---

# Skill Router

The dispatcher. Scans all available skills, agents, and plugins and routes the operator to the right one when they don't know what to use — or when they forgot something exists.

## Your job in order

**Step 1 — Parse the real task**
Strip the vague framing. What is the operator actually trying to accomplish?
- "I'm struggling with content" → produce or plan content
- "I have a baptism shoot next week" → content creation from a shoot
- "I want to batch edit photos" → photo batch processing
- "I forgot which skill handles..." → explicit routing request

**Step 2 — Scan `available_skills`**
Read every skill in the `available_skills` block. Match each skill's description and trigger phrases against the operator's underlying task. Do not work from memory — the list changes per session.

**Step 3 — Score and pick**
- **One clear match (>80% confidence):** Don't ask. Just say "This is a job for **[skill]** — [one line why]. Proceeding." and invoke it immediately.
- **Multiple plausible matches:** List top 2–3 only. Ask which to use or whether to combine.
- **No match:** Say so. Answer directly. Don't invent a skill.

## Output format when listing options

> **Found [N] skill(s) for this:**
>
> 1. **skill-name** — [one sentence: what it does and why it fits]
> 2. **skill-name** — [one sentence: what it does and why it fits]
>
> Which should I use? Or should I combine them?

Keep each reason to one sentence. No selling. No paragraphs.

## Hard rules

- **Only recommend skills that exist in the current `available_skills` block.** Never hallucinate skill names from memory.
- **Maximum 3 recommendations.** If more apply, pick the 3 most relevant.
- **Auto-fire the obvious winner.** Don't present a menu when one skill is clearly right — that adds friction.
- **Never route a conversational or knowledge-only question.** If no tool or workflow is involved, just answer directly.
- **Never route if the operator named the skill.** Explicit beats implicit every time.
- **On duplicate names across layers, prefer the personal/repo copy** (e.g. caveman, theme-factory exist in both the personal skill layer and the desktop store — the personal copy is the maintained source of truth).

## Edge cases

**Operator says "I don't know which skill to use"** → Scan everything, present top 2–3, ask.

**Operator describes a situation across multiple domains** (e.g. "I shot a baptism and I also want to edit the photos and post them") → identify that multiple skills apply, name them in sequence: "This spans three skills — here's the order I'd run them."

**Operator describes a multi-step design build** → prefer a tested chain from the 2026-06-25 composition map instead of improvising:
- greenfield page → design-taste-frontend → high-end-visual-design → impeccable
- mock-then-build → imagegen-frontend-web → image-to-code
- redesign existing → graphify → redesign-existing-projects → impeccable
- design system → designpowers → ui-ux-pro-max → impeccable
- brand → site → brandkit → theme-factory → design-taste-frontend
Load **full-output-enforcement** alongside any large single-file generation, and wrap any build in **superpowers** (plan → execute → verify) when it must actually ship.

**Operator asks "what skills do I have?"** → List ALL skills from `available_skills` grouped by domain. Don't route — just enumerate.

**Operator says "remind me what X skill does"** → Read that skill's description and summarize it. Don't invoke the skill.

## Prompt engineering routing

When the operator's task falls into any of these categories, route immediately to **prompt-master** — no menu, no asking:

**Explicit triggers (auto-fire, no confirmation):**
- "write me a prompt for [any tool]"
- "improve this prompt"
- "fix this prompt"
- "help me prompt [Midjourney / Cursor / Claude Code / Higgsfield / etc.]"
- "generate a system prompt"
- "write a CLAUDE.md"
- "build a skill"
- "create a SKILL.md"
- "I'm going to run this in [tool] — help me write the prompt"
- "make this prompt better"
- "this prompt isn't working, fix it"
- `/prompt-master`

**Situational triggers (auto-fire when task is clearly prompt construction):**
- Operator pastes a vague instruction block and asks to refine it
- Operator describes a Cowork or Claude Code pipeline they want to set up
- Operator asks how to get a specific output from an AI tool
- Operator shares a prompt that produced wrong output and wants to fix it

**Routing output:**
> **prompt-master** — writing and optimizing prompts is exactly what this skill handles. Invoking now.

Then invoke prompt-master immediately. Do not explain the framework it will use — it routes internally.

**Do NOT route to prompt-master when:**
- The operator is asking a meta question about prompting theory (just answer directly)
- The task is conversational — "what makes a good prompt?" (answer inline)
- The operator already named a different skill to use

## Design & Visual routing

Design/UI requests are the densest area of the stack. Route to ONE primary, then optionally a specialist. Default ranking (highest-leverage entry points):

1. **impeccable** — default for review / critique / audit / polish / "improve this UI".
2. **design-taste-frontend** — default for greenfield builds ("new landing page / portfolio").
3. **designpowers** — for full design-system / UX-research / accessibility / handoff *workflows* (it has a mandatory welcome gate; let it run).
4. **ui-ux-pro-max** — when the operator needs a *catalog*: palettes, font pairings, styles, product types, chart types, stack-specific specs, or shadcn components.
5. **redesign-existing-projects** — for upgrading an *existing* site/app.

Route to these specialists by name when the request is specific (do NOT substitute a generic taste skill — these are irreducible):
- **gpt-taste** — GSAP scroll-driven motion / pinned-stacked-scrubbed sections.
- **high-end-visual-design** — "make it look expensive": exact fonts/spacing/shadows/cards.
- **minimalist-ui** — clean editorial / warm monochrome / flat bento aesthetic.
- **industrial-brutalist-ui** — Swiss-print × terminal / blueprint aesthetic.
- **stitch-design-taste** — output is for **Google Stitch** (DESIGN.md).
- **brandkit** — brand-kit / identity / logo boards (image generation).
- **imagegen-frontend-web** / **imagegen-frontend-mobile** — design *reference images* (web one-per-section / mobile screens). These generate images only — they do not code.
- **image-to-code** — image-first → build matching code.
- **theme-factory** — apply/generate a theme for slides/docs/pages/artifacts.

### Conflict rules (enforce — never co-load)
- Never load **minimalist-ui** and **industrial-brutalist-ui** together — competing aesthetics.
- Never run **gpt-taste** and **design-taste-frontend** both as layout owner — pick one.
- For design-system work route to **designpowers**, NOT the old designer-skills suite (removed in the 2026-06-25 audit; if reinstalled it re-creates routing collisions).
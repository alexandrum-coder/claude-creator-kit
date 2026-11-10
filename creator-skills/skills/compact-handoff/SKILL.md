---
name: compact-handoff
version: 1.2.0
description: "End-of-session ritual that makes compaction safe: distil the session into a verified state summary, write a durable HANDOFF file to disk, refresh project memory, emit a copy-paste boot prompt for a cold session, then hand back to the user to run native /compact or /clear (a skill cannot free the context window itself). Use when the user says compact-handoff, /compact-handoff, hand off, handoff, save the session, close the session, wrap up, context is running out, or before an intentional /clear or context reset. Do NOT use for a plain summary request with no session end, and do NOT use it as a substitute for finishing in-flight work."
---

# Compact + Handoff

Three beats, and **the order is non-negotiable**:

1. **HANDOFF first** — distil the session into verified state and write it to
   disk (steps 0–4). Nothing is freed until this file exists.
2. **BOOT PROMPT second** — emit the copy-paste prompt that restarts a cold
   session with zero loss (step 5). It is built *from* the handoff, so it cannot
   be written before it.
3. **HAND OVER TO NATIVE `/compact` last** — only once both artefacts exist is
   the transcript expendable (step 6).

Compacting before the handoff is written risks losing exactly the details the
handoff was supposed to capture. Never reverse these.

## Read this before step 0 — what this skill can and cannot do

A skill runs *inside* the model turn. It cannot free the context window: no tool
exposed to the model shortens the transcript, and `/compact` and `/clear` are
harness commands, not skills, so **you cannot invoke them for the user**.

So the division of labour is fixed:

| Job | Who does it | Result |
|---|---|---|
| Durable state → disk | this skill | survives the session, survives `/clear` |
| Freeing the context window | the user, running `/compact` or `/clear` | frees tokens, reports what it saved |

Never tell the user the conversation has been compacted. This skill has not
compacted anything. It has made compaction **safe** — after the handoff exists
on disk, whatever native compaction drops is recoverable from the file. Step 6
is where you hand that back to them, explicitly.

### Dead ends — tested, do not retry

| Route | Result |
|---|---|
| A `SlashCommand` tool | Not present in the desktop harness at all. Where it does exist (CLI), it runs **only** custom commands from `.claude/commands/`; built-ins (`/compact`, `/clear`, `/config`) are excluded by design. |
| `CronCreate` with the prompt `/compact` | **Tested 2026-08-11, 16:14 — does not work.** The job fired and auto-deleted on schedule, but the text arrived as an ordinary user prompt and the model turn ran normally. Prompts injected by the scheduler bypass the command parser. Had the harness intercepted it, no model turn would have occurred at all. |
| Hooks (`PreCompact`, `Stop`) | React to compaction; none can initiate it. |

The conclusion is structural, not a missing feature: `/compact` operates on the
transcript *before* the model is invoked, so nothing inside a model turn can
reach it. Do not spend another session looking for a way around this.

## Hard rules — never violate

- **Verified or labelled.** Every file path, count, status, and ID in the
  handoff is checked against disk (`ls`, `Read`, `grep`) before it is written.
  Anything you cannot verify goes in as `UNVERIFIED — <what would prove it>`.
  Never launder a conversational claim into a written fact.
- **Planned ≠ done.** Work that was discussed, planned, or half-built is written
  in the "not done" section, in future tense. Never phrase upcoming work so it
  reads as completed.
- **No new work.** This skill writes documents. It does not fix, refactor, or
  finish anything it discovers, and it does not delete anything. Findings go
  into the handoff's open-items list.
- **No invention.** If the conversation never settled a question, the handoff
  says it is open. Do not resolve it on the user's behalf.
- **Redact secrets.** Passwords, tokens, keys, cookies → `[SECRET_REDACTED]`.
  Real personal data → note that it needs anonymisation; do not copy it in.
- **Project language.** Write the handoff in the language the project's own
  documents use. Mirror the existing HANDOFF files if any exist.

## Step 0 — Preflight (do this before writing anything)

Gather and state, in one short block:

- Project root (cwd), today's date (absolute, `YYYY-MM-DD`).
- Git: is it a repo? branch, `git status --short`, last 5 `git log --oneline`.
  If not a repo, say so and rely on file timestamps instead.
- Where handoffs already live — first match wins:
  1. `00-Management/HANDOFF-*.md`
  2. `docs/handoff/` or `docs/superpowers/reports/`
  3. `.scratch/`
  4. project root
- Whether a persistent memory dir exists for this project
  (`~/.claude/projects/<slug>/memory/MEMORY.md`).
- The project's own instruction files: `CLAUDE.md`, `CONTEXT.md`,
  `NEXT_STAGE_PLAN.md`, `OPEN_TASKS_AND_DECISIONS.md` — read the ones that exist.

Output: `✅ Preflight — root, date, git, handoff location, memory location.`

## Step 1 — Harvest

From the conversation *and* the working tree, pull:

| Bucket | What goes in |
|---|---|
| Decisions | What the user decided, the chosen option, what was rejected and why |
| Done | Work finished **and** verified this session, with the evidence |
| Not done | The exact next action, phrased as an instruction |
| Blocked | Blocker, who/what unblocks it, what was already tried and failed |
| Files touched | Path + one line on what changed |
| Traps paid for | Dead ends, wrong assumptions, tool quirks — so nobody re-pays them |
| Open questions | Unresolved, with the options if they were framed |

The "traps paid for" bucket is the highest-value part of a handoff and the one
most often dropped. Every failed approach that cost real time belongs there,
with the reason it failed.

## Step 2 — Verify

For every concrete claim harvested in Step 1, run the cheapest check that could
falsify it: `ls` the file, `Read` the section, `grep` the identifier, re-read the
count from its source of truth. Downgrade whatever fails to `UNVERIFIED`.

Output: `✅ Verified N claims, M downgraded to UNVERIFIED.`

## Step 3 — Write the HANDOFF file

Path: `<handoff-location>/HANDOFF-<YYYY-MM-DD>-<short-topic-slug>.md`.
If a file with that name exists, append `-2`, `-3` — never overwrite a handoff.

Use this structure (translate the headings into the project's language):

```markdown
# HANDOFF — <date> — <topic>

> **Read this first.** <3–6 lines: where the project actually stands, and the
> single next action.>

**Purpose:** a new session must resume from here without reading the previous
transcript.

## 1. Decisions taken this session
<Decision, who took it, what was rejected. One block each.>

## 2. State at the moment of handoff
### Done and verified
| Item | State | Evidence |
### Not done
| Item | State | Blocker |

## 3. Next action — concrete
<Numbered, executable steps. Step 1 must be startable with no further input.>

## 4. Traps already paid for
<Failed approach → why it failed → what to do instead.>

## 5. Files touched this session
| Path | Change |

## 6. Open questions for the user
<Each with 2–3 options, recommended option first.>

## 7. Context to load in the next session
<Explicit file list, shortest sufficient set, most important first.>
```

Output: `✅ HANDOFF written: <path>`

## Step 4 — Refresh memory

Only for facts that are **durable and not derivable from the repo**: a working
preference, a hard constraint, a tool quirk that will bite again.

- Write one file per fact in the project memory dir, with the standard
  frontmatter (`name`, `description`, `metadata.type`).
- Add a one-line pointer in `MEMORY.md`.
- Update an existing memory instead of creating a near-duplicate; delete any the
  session proved wrong (ask first if the user's rules require confirmation for
  deletions).
- Do **not** memorise session-local trivia or anything the handoff already holds.

Output: `✅ Memory: X written, Y updated, Z deleted (or: no memory changes needed).`

## Step 5 — Emit the boot prompt

Print this last, in a single fenced block, ready to paste as the first message of
a new session. Fill every placeholder — no `<...>` may survive into the output.

```text
ROLE: You are resuming an in-progress project as the same engineer who left it.

PROJECT: <name> — <one line on what it is>
ROOT: <absolute path>
HANDOFF: <absolute path to the HANDOFF file>

START BY:
1. Read <ROOT>/CLAUDE.md (or CONTEXT.md) in full.
2. Read the HANDOFF file above in full.
3. Read, in this order: <2–5 files from handoff section 7>.
4. Verify on disk that the "Done" table in the handoff still matches reality.
   Report any drift before doing anything else.

STATE: <3–5 lines — where things stand.>

FIRST TASK: <the one next action, verbatim from handoff section 3>

CONSTRAINTS:
- <the project's non-negotiable rules, copied from CLAUDE.md>
- Do not re-do work listed as done; verify instead.
- Do not repeat the failed approaches in handoff section 4.
- <destructive-action / confirmation rules that apply>

OPEN QUESTIONS (ask before they block you):
- <question — options, recommended first>

DONE WHEN: <observable finish condition for the first task>
```

Then a two-line closing summary to the user: handoff path, and the next action.

## Step 6 — Hand compaction back to the user (do not skip)

The handoff now exists on disk, so the transcript is expendable. Close with this
block, verbatim apart from the filled paths:

```markdown
**Handoff saved — the context can now be freed safely.**
Nothing below is lost: everything durable is in `<handoff-path>`.

Pick one:

- **`/compact`** — stays in this session, keeps a summary in context, and
  reports how many tokens it saved. Use it to keep working right now.
- **`/clear`, then paste the boot prompt above** — full reset, cleanest
  context. Use it when this stretch of work is finished.

I cannot run either one for you — they are harness commands, not tools.
```

Both options are safe *only* after the handoff file has been written and
re-read. If step 3 failed, say so and tell the user **not** to compact yet.

Output: `✅ Handoff complete — waiting on /compact or /clear from the user.`

## Done when

- [ ] HANDOFF file exists on disk and was re-read after writing.
- [ ] Every claim in it is verified or explicitly labelled `UNVERIFIED`.
- [ ] The "next action" is executable with no further questions.
- [ ] Traps section lists every failed approach from the session.
- [ ] Memory index updated, or explicitly stated as unchanged.
- [ ] Boot prompt printed with zero unfilled placeholders.
- [ ] Step 6 block printed, offering `/compact` vs `/clear`, with the honest
      statement that the model cannot run either.

## Anti-patterns

| Don't | Do |
|---|---|
| Summarise the conversation chronologically | Summarise the **state**; chronology only where a failure explains a constraint |
| "We updated the manifest" (untested) | `ls`/`Read` it, then state it — or mark UNVERIFIED |
| Dump every file the session opened | List only files the successor must read |
| Leave the next step as "continue the work" | One concrete, startable instruction |
| Silently drop dead ends because they "didn't work" | Dead ends are the most expensive knowledge in the handoff |
| Overwrite yesterday's handoff | New dated file, always |
| Claim the conversation was compacted | Say the handoff is saved, then ask the user to run `/compact` or `/clear` |
| Invent a "tokens saved" figure | Only native `/compact` can measure that; never estimate it |

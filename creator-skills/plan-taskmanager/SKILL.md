---
name: plan-taskmanager
description: Build a task plan that survives contact with reality — one that gets executed cleanly, in a single pass, with no drift and no rework. Use whenever a plan is being created for a task or a series of tasks — "make a plan", "plan this out", "how should we approach", "write me a prompt for this task", multi-step work on a live system, migrations, bulk edits, content operations, or any job where a wrong step is expensive to undo. Also use when a plan already exists but has no verified starting state, no stop conditions, or no decision list.
---

# Plan Taskmanager

A plan is not a list of steps. A plan is **the set of decisions taken before anyone
touches anything**, plus the evidence that each step actually landed.

Plans fail in exactly four ways, and this skill exists to close all four:

| Failure | What it looks like | Closed by |
|---|---|---|
| The plan assumed a world that isn't there | "Add a button" — but it's not a button, it's an accordion | Step 1 |
| Decisions were left to be made mid-execution | Halfway through, an ambiguity appears; work stops or, worse, someone guesses | Step 2 |
| Nothing proved the step worked | "Looks right" on a screenshot that would look identical if it were broken | Step 4 |
| The plan grew while it ran | An adjacent defect gets fixed "while we're in there" | Step 5 |

## The rule

**Do not write the plan until the starting state has been verified.** Not read about,
not remembered, not inferred from the request — checked, in the actual system, this session.

Everything else in this skill follows from that one rule.

## Step 1 — Verify the starting state

Before a single plan line is written, go look at the thing.

- Open the actual page, file, table, or screen the work targets.
- Read what is really there: structure, names, existing elements, current values.
- Check the **destination** as carefully as the source. Most wrong plans are wrong about
  the destination.
- Write down what you found. This becomes the plan's "Starting state" section, and every
  later claim is checked against it.

The user's description of the system is a hypothesis, not a fact. It is usually close and
occasionally wrong in a way that invalidates the whole approach. Finding that out now costs
one tool call; finding it out in execution costs the session.

Never write `<element>` or `<the button>` in a plan without having seen it.

## Step 2 — Surface every decision, before execution

Read through the intended work and collect **every point where two reasonable people could
choose differently**. Ambiguities do not disappear by being ignored; they resurface mid-run,
when stopping is most expensive.

Ask them all at once, as multiple choice:

- One question per genuine decision — not per uncertainty you could resolve yourself.
- 2–4 concrete options, each with its consequence stated.
- **Your recommendation first**, marked as such, with the reason.
- Never ask "shall I proceed?" — that is not a decision, it is a request for permission.

Then record the answers in the plan as numbered decisions (`D-01`, `D-02`, …), each with
what was chosen *and what was rejected and why*. The rejected option matters: it stops the
question being reopened three steps later.

**A decision the user has taken is closed.** If they pick the option you argued against,
state nothing further and execute it. You raised the concern in the option text; that was
your turn to speak.

## Step 3 — Shape the plan in phases with mandatory stops

Phases, not steps. A phase ends at a **checkpoint**: a point where you report what happened,
show the evidence, and stop.

Rules that make phases real:

1. **A phase does not begin until the previous one is verified.** Not finished — verified.
2. **Every phase that writes gets a backup phase before it.** Byte-faithful, hashed, on disk,
   inside the project. A backup you have not verified is not a backup.
3. **One pilot before any batch.** If the plan touches N similar things, do one, verify it
   completely, show it, and stop for approval. The pilot is not a formality — it is where
   you learn the real shape of the thing, and where defects appear that no planning would
   have caught.
4. **The last phase is verification and a written report**, not the last edit.

Order that has proven itself:

```text
1. Inventory + correlation   (read-only; produces a mapping, nothing is touched)
2. Acquisition + integrity   (fetch, hash, record; still nothing written to the target)
3. Precondition check        (confirm what phases 4+ depend on actually exists and matches)
4. Pilot on one              (full cycle: change, verify, screenshot, stop for approval)
5. Batch on the rest         (single atomic write where possible)
6. Final verification + report
```

Not every job needs six. Every job needs *read-only first, backup before write, pilot before
batch, verification last*.

## Step 4 — Define verification as evidence, per phase

For each phase, the plan states, in advance, **what would prove it worked** — and it must be
something that would look different if the work had failed.

| Weak | Strong |
|---|---|
| "The page looks right" | `diff` of the stored content, before vs after: N changes, all intended |
| "The file uploaded" | SHA-256 of the served URL equals the SHA-256 on disk |
| "The links work" | HTTP status of every link, listed |
| "It's on the right card" | Each card parsed from the public HTML, mapped to its expected document |
| "The animation runs" | The interpolated property read before and after the state change |

Two specific traps worth naming, because they cost real sessions:

- **A settled state proves nothing about how it got there.** A snap and a smooth transition
  produce identical screenshots. Verify the transition, not the endpoint.
- **A panel showing a value is not persistence.** Reload and read it again, from the source
  of truth, not from the editor that just wrote it.

**Never verify identity through a convenient proxy.** File names, titles, and labels are
conventions, not facts — they differ per author and per department. Read identity from inside
the authoritative artifact. In one recent job, three matches out of twelve would have been
wrong if taken from file names.

## Step 5 — Fix the scope in writing, including what is forbidden

The plan states explicitly:

- **In scope:** what will be changed, named precisely.
- **Out of scope:** what will *not* be touched — especially adjacent things that will be
  tempting once work begins.
- **Findings policy:** defects discovered along the way are **recorded, not fixed**. They
  become a separate task. This holds even when the fix is small and you are already in the
  file. Scope growth is the most common way a clean plan becomes a messy one.
- **Stop conditions:** the situations in which execution halts and reports instead of
  continuing. At minimum: anything that would overwrite existing data, any name collision,
  any mismatch between expected and actual, and any situation not covered by the plan.

Write the stop conditions as instructions, not as sentiment. "Stop and report" is a step.
"Be careful" is not.

## Step 6 — Separate how you execute from what gets documented

These are two different artifacts and conflating them produces unusable documentation.

- **Execution method:** whatever is safest and most atomic for a one-time operation —
  scripted, batched, direct.
- **Documented procedure:** the path the actual future user will take, in the actual
  interface, in their own words, with their own permissions.

If the two differ, say so in the plan, and derive the documented procedure from the **pilot**,
which you performed by hand precisely so the steps are real. Never document a click-path you
have not walked.

## The plan document

Write it in the language the project's own documents use. Keep it on disk, in the project,
not only in the conversation.

```markdown
# Plan — <task>

## Objective
<One paragraph. What is true when this is done that is not true now.>

## Starting state — verified <date>
<What was actually checked, and what was found. Cite what you looked at.>

## Decisions
D-01 — <decision>. Chosen: <option>. Rejected: <option> because <reason>.
D-02 — …

## Inviolable rules
<Numbered. The things that hold regardless of what happens during execution,
including the stop conditions and the findings policy.>

## Scope
In: …
Out: … (findings here are recorded as separate tasks, not fixed)

## Phases
### Phase N — <name>
Does: …
Produces: …
Verified by: <the evidence that would look different on failure>
Checkpoint: <report and stop / continue>

## Open questions
<Each with options, recommendation first. Empty is a valid answer — but only after Step 2.>

## Done when
<Observable. Someone else could check it without asking you.>
```

## Anti-patterns

| Don't | Do |
|---|---|
| Write the plan from the request alone | Verify the starting state first, then write |
| Collect decisions as they come up during execution | Collect them all before phase 1 |
| "Continue the work" as a next step | One concrete, startable instruction |
| A pilot that skips verification because it's "just one" | The pilot is the most thoroughly verified phase in the plan |
| Fix the small adjacent defect while you're there | Record it, spawn it as a separate task, leave it |
| Change method silently when the planned one proves awkward | Stop, report the obstacle, offer options, wait |
| Prove success with a screenshot | Prove it with something that would differ on failure |
| Document the shortcut you actually used | Document the path the real user will walk |
| Ask "is the plan ok?" | Ask the specific decisions; the plan follows from the answers |

## Done when

- [ ] Starting state verified against the real system this session, and written down.
- [ ] Every ambiguity asked as multiple choice, recommendation first, before phase 1.
- [ ] Decisions recorded with what was rejected and why.
- [ ] Phases ordered read-only → backup → pilot → batch → verification.
- [ ] Each phase has evidence defined in advance that would differ on failure.
- [ ] Scope names what is forbidden, and the findings policy is written.
- [ ] Stop conditions written as instructions.
- [ ] The plan is on disk, in the project's language.

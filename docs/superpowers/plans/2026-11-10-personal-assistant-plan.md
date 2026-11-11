# Plan: the personal-assistant agent (summary for a new session)

Status: design approved by Doru on 2026-11-10. Nothing is built yet.

## Decisions (approved)
- **D-01.** personal-assistant is an AGENT, at `creator-skills/personal-assistant/agents/personal-assistant.md`. It runs on the sonnet model, with the tools Agent, Skill, Read, Grep, Glob, Bash (read-only inventory) and SendMessage. It has no Write or Edit.
- **D-02.** Variant A is the main path: a relay through the main thread. prompt-agent calls `Agent(...:personal-assistant)` after Doru's "yes". Variant B is the fallback: `claude --agent personal-assistant:personal-assistant` in the terminal, or a dedicated folder with the `"agent"` setting, still to be tested in the desktop app.
- **D-03.** The last line of the reply is `STARE: GATA | ÎNTREBARE | ACȚIUNE`.
  - ACȚIUNE allows only `Skill(...)` calls, joined by →. Anything else is treated as ÎNTREBARE.
  - Every ÎNTREBARE goes through AskUserQuestion, with 2–4 options and ALWAYS `multiSelect: true`.
  - Every ÎNTREBARE ends with a last question, "Observații extra?", with the options "Nu am" and "Da, scriu la Other".
  - After Doru answers, the main thread resumes the same agent with SendMessage.
- **D-04.** Cost advisor. The agent stays in A when the cost is low (at most 2 questions, one handoff). When the cost is high, it asks whether to switch to B, gives the estimate and the reason, and shows the command. Thresholds are calibrated from measurements. Measured so far: an empty spawn costs about 58k input tokens.
- **D-05.** personal-assistant is the only dispatcher. skill-router is retired from obsydia-skills and from the kit, and its design chains move to `$CONF/personal-assistant/reguli-locale.md`, which is local. The "Skill routing" rule in CLAUDE.md becomes a one-line pointer. `<componente-sugerate>` is only checked, not redone.
- **D-06.** `scripts/inventar.py` is a common script extracted from three sources, not rewritten:
  - the v2 scanner in `setup-mac.sh`, lines 102–207;
  - `tools/genereaza-catalog.py`;
  - `~/claude-code-sync/mac/inventory-mac.sh`.

  It has three modes: `--json`, `--chei` (I/P/S/A/M), and `--cauta <words>`. The cache lives in `$CONF/personal-assistant/inventar.json` and is rebuilt when a source's mtime changes.
- **D-07.** Routing:
  - clip: `ACȚIUNE: Skill(airtime...)`;
  - IT: `ACȚIUNE: Skill(superpowers:using-superpowers) → Skill(obsydia-skills:plan-taskmanager)`, then stop after the plan;
  - anything else: GATA, with a "Pas | Unealtă | De ce" table of at most 5 rows.
- **D-08.** In the kit the agent is `personal-assistant:personal-assistant`. prompt-agent finds it by the suffix `:personal-assistant`. Only one copy is installed on Doru's Mac.

## Rules
- Do not touch `setup-mac.sh`, `marketplace.json` or `tools/genereaza-catalog.py` until the main session announces the v2 commit. v2 is staged in the index.
- Touch `~/claude-code-sync` and `~/.claude/CLAUDE.md` only after showing Doru the diff and getting his explicit "yes".
- No push without approval.
- Tests run with `CLAUDE_CONFIG_DIR` pointing to the scratchpad, plus `--plugin-dir` and `--output-format json` (CLI 2.1.206).

## Phases
0. Preflight with `obsydia-skills:task-verifier` on this plan.
1. Write `inventar.py` and its tests. Verify that `--chei` returns a superset of the v2 scanner's output.
2. Write the agent, `references/reguli.md` and `README.md`.
3. Pilot: the IT request, on the isolated profile.
4. Run the clip request and the marketing request, and measure the A vs B cost of all three.
5. Retire skill-router, with consent.
6. Write the report and commit, without pushing.

## Amendments (Doru, 2026-11-10, after the phase 2 checkpoint)
The text above stays as it was approved. These answers change it:
- **D-01:** the tools also include AskUserQuestion, used only in variant B, when the agent is the main thread. A subagent does not have it.
- **D-03 / D-04:** variant A is kept with no question asked for at most 2 rounds of questions, with up to 3 questions per round. Anything above that leads to a question recommending B. The thresholds are calibrated in phase 4.
- **D-07, IT:** a "Skill-uri înrudite" table (3–6 rows) is added above the ACȚIUNE line.
- **D-07, other:** the table has 3–5 rows, not "at most 5".
- **Phase 1:** the plan does not get a "tests and stop" section; that was Doru's answer to Î-3. The extras stay: the `C` key, `--fara-cache` and `--limita`.
- **Phase 3:** it runs on a new isolated profile, `scratchpad/faza2/profil`, where Doru logs in himself.

## Amendments (Doru, 2026-11-11, before phase 4)
- **Rule added:** names are written in full (`plugin:name`), and the agent follows a defined rule when the inventory comes back empty. This is `reguli.md` §0.
- **Plugins:** phase 4 runs with the plugins installed in the isolated profile, not with `--plugin-dir`, after a baseline snapshot of `~/.claude`. This also counts as the "yes" for phase 4.
- **Version:** phase 4 runs on obsydia-skills 1.5.4.

## Amendments (Doru, 2026-11-11, phase 5 and kit integration)
The decisions above stay visible. These answers change or extend them:
- **D-05:** Doru approved items 1–3 of `personal-assistant-faza5-diff.md`, and CLAUDE.md gets the one-line pointer. `custom-skills/skill-router`, the source copy, was removed too. It was not named in the diff; Doru is asked to confirm this after the fact.
- **D-08:** on Doru's Mac the agent comes from obsydia-skills (`obsydia-skills:personal-assistant`), and the kit gets a copy (`personal-assistant:personal-assistant`). The kit's setup checks `have A personal-assistant`, so it does not install a second copy.
- **D-06:** `setup-mac.sh` (it runs through curl, with no repo on disk) and `genereaza-catalog.py` keep their own scanners. `inventar.py` is the agent's common inventory. `test_superset_fata_de_v2` reads the setup heredoc on every run, so it catches any drift.
- **Kit:** the changes in `personal-assistant-kit-diff.md` are applied and committed without a push. `docs/` gets only this plan.

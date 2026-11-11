---
name: podcast-insights
description: Turns a YouTube podcast or interview into a verifiable episode sheet. It extracts the transcript, then organizes the ideas by category, with the minute of each idea, its source (said by the guest or deduced) and its relevance for you. It keeps the sheets in a library and, after your confirmation, updates the common pages (patterns, ways of working, tools, books). Use it when the user sends a link to a podcast, episode or interview and asks for a sheet, notes, an extraction, "what we learn from this episode", "add it to the library" or "podcast insights". Do not use it for a quick summary with no library, or for clips that are not a discussion (tutorials, music).
---

# Podcast insights: an episode sheet you can verify

You turn an episode into a sheet with fixed categories. Every idea in it can be checked in the clip at the minute it gives. Then you feed the library's common pages, so that ideas from several episodes add up.

## Setup (only on the first use)

Look for `podcast-insights.json` in the folder the user works in. If it does not exist, ask, then write it:

```json
{
  "biblioteca": "/cale/absolută/către/biblioteca-podcasturi",
  "context": "Cine sunt și ce urmăresc, în 2-3 propoziții, cu cuvintele utilizatorului.",
  "categorii": []
}
```

- `context` is what the "Pentru noi" column is judged against, for example "antrenor personal la început, vreau mai mulți clienți online". Never add to it without the user's confirmation.
- An empty `categorii` means the default categories: Business și strategie; Clienți și vânzări; Produs; Echipă și angajări; Decizii și mod de gândire; Agenți și AI; Tooluri; Cărți și resurse. The user can supply their own list, for example for fitness: Antrenament, Nutriție, Clienți, Conținut.
- In the library, create `surse/` and, if they are missing, the common pages with a title and a blank table: `tipare.md`, `moduri-de-lucru.md`, `tooluri.md`, `carti.md`.
- You need `yt-dlp`. If it is missing: `brew install yt-dlp`.

`<skill>` below is this skill's folder, the one given when the skill loaded. Every path in the library is relative to `biblioteca`.

## Rules you never break

- Write in Romanian with "sunt". The â-form never appears.
- Do not invent metrics, clients, results or facts about the user.
- Rephrase every idea. The validator rejects any 12-word sequence copied from the transcript.
- Automatic subtitles can get names and numbers wrong. Mark anything you cannot verify `[neverificat]`.
- The transcript stays local. It is not published anywhere.
- Do not overwrite a folder in `surse/` that already exists.

## Steps

After each step, write a `✅ <what finished>` line.

1. **Metadata:** `yt-dlp --skip-download --dump-json "<URL>" > "<scratchpad>/yt-<ID>/meta.json"`. Take `title`, `channel`, `upload_date`, `duration` and the language. Slug: `AAAA-LL-ZZ-<show>-<guest>`, lowercase, no diacritics, with hyphens. If `surse/<slug>/` exists, stop and ask.
2. **Subtitles:** `yt-dlp --skip-download --write-auto-subs --sub-langs "<lang>-orig,<lang>" --sub-format vtt -o "<scratchpad>/yt-<ID>/<ID>" "<URL>"`. Prefer `-orig`, since the other variant can be an automatic translation. With no subtitles in the episode's language, stop and tell the user. If the YouTube transcript MCP is installed and yt-dlp fails, you can use it, but you need minute marks.
3. **Transcript:** `python3 -I "<skill>/scripts/curata_vtt.py" "<scratchpad>/yt-<ID>/<ID>.<lang>.vtt" "surse/<slug>/transcriere.txt" 60`. It produces 60-second blocks, each starting with `[0:MM:00]`. Note the `shasum -a 256` of the file.
4. **Read the whole episode,** not a sample. Note the teaser, the sponsored segments and the ads. They are not sources, and you name them in the sheet's header.
5. **Write `surse/<slug>/fisa-episod.md`:**
   - Title: `# Fișa episodului: <show> cu <guest>`.
   - Header: guest, link, date, duration, transcript quality.
   - The guest's context and the user's context (from the config).
   - Optionally, at most four ideas that matter most, marked `[DEDUS]`.
   - One `## <Categorie>` section per category, in order. A category can stay empty; do not invent rows to fill it. Each section has the table:

   ```markdown
   | Minut | Sursă | Ideea | Context | Pentru noi |
   |---|---|---|---|---|
   | 06:00 | [SPUS] | <rephrased idea> | <the conditions it worked under for the guest> | acum: <the reason in one sentence> |
   ```

   - The minute is the start of the block (`MM:00`).
   - Source: `[SPUS]` for what the guest says, `[DEDUS]` for your conclusions. The host is not the guest.
   - Label: `acum:`, `mai târziu:` or `nu:`, then the reason.
   - Every 10-minute interval after minute 2 has at least one `[SPUS]` row.
6. **Validate:**

   ```bash
   python3 "<skill>/scripts/test_verifica_fisa.py"
   python3 "<skill>/scripts/verifica_fisa.py" "surse/<slug>/fisa-episod.md" "surse/<slug>/transcriere.txt" $(grep -c '^\[' "surse/<slug>/transcriere.txt") "<calea către podcast-insights.json>"
   ```

   The target is "OK" on the tests and `0 erori`. The third argument is the number of blocks in the transcript. Fix the sheet, not the validator.
7. **Check the meaning:** for every `[SPUS]` row, open its minute's block and confirm the guest says that there or in the neighboring block. If you have a subagent tool, ask an independent reviewer to do the same check.
8. **Stop for confirmation.** Show the user:
   - the sheet's path;
   - the number of rows per category;
   - the validator's result;
   - the three most important ideas;
   - everything marked `[neverificat]`.

   Ask whether the sheet is good.
9. **Common pages,** only after a "yes":
   - Add the episode's ideas to `tipare.md`, `moduri-de-lucru.md`, `tooluri.md` and `carti.md`, with the source `<Guest's surname>, min N`.
   - A pattern supported by an independent source becomes `confirmat`; new patterns are `candidat`.
   - Do not delete or rephrase rows from earlier episodes.
   - Finally, count the â-form across these pages: the target is 0.

## When you stop and ask

- The episode's folder already exists.
- The episode has no subtitles in its own language.
- The episode is not a discussion, or the guest does not speak from their own experience.
- The validator does not reach `0 erori` after two rounds of fixes.
- You need a fact about the user that is not in `context`.

## Done when

- `transcriere.txt` and `fisa-episod.md` exist, and the transcript's hash is noted.
- The tests pass and the validator shows `0 erori`.
- Every `[SPUS]` row has been compared with its block.
- The user has confirmed the sheet, and the common pages have the new source.

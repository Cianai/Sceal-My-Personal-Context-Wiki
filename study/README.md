# Study materials: model reading of an author's own writing, with and without personal context

This folder holds the frozen materials for a preregistered single-case study. Three short pieces of the author's own expressive writing, and one reconstruction of a life by periods, are run under three context conditions (no personal context, raw text of equal length, a condensed wiki) with two models and three runs per cell. The author marks the outputs blind to condition. The primary test is an exact sign-flip test over six blocks (piece x model). No data, test pieces, personal records or marks are in this folder.

## Files

| File | What it is |
| -- | -- |
| `prompts/system.md` | The bare personal-assistant system prompt, used for every call. |
| `prompts/task1_interpretation.md` | Verbatim Task 1 user prompt, output format, and how each condition fills the context block. |
| `prompts/task2_reconstruction.md` | Verbatim Task 2 user prompt, output format, and the same condition rules. |
| `rubric/marking_rubric.md` | What counts as right, the correction, the felt-understood rating, the condition guess, and the marker's order of steps. |
| `judge/judge_prompt.md` | The automatic judge prompt (right / not right) for an LLM-as-judge evaluator. |
| `analysis/analyse.py` | Every index and test in the registration, the output-format parsers and the seeded marking order. numpy, pandas, scipy only. |
| `analysis/test_analyse.py` | Tests on synthetic data, including p = 2/64 when the wiki wins all six blocks. |
| `schema/outputs.schema.md` | Columns of the outputs table and the marks table. |

## Order of operations

1. **Freeze.** Check that `python -m unittest test_analyse` passes in `analysis/`. Record the run settings that these files do not fix (see "Still to record before tagging"). Commit, tag, and take the SHA-256 of each file; the registration cites the tagged commit and the hashes. The marking seed in `analyse.py` (`MARKING_SEED`) is part of the frozen code. Run `python analyse.py order --out marking_order.csv` and record the printed digest.
2. **Generate.** Build the three context blocks per piece (and for Task 2), check equal length with `length_check`, render each prompt with `extract_prompt` and `render_prompt`, call each model, parse with `parse_task1` / `parse_task2`, retry once on failure, and store the outputs table. All outputs are generated in one batch and are not read.
3. **Mark blind.** Mark in the seeded order, following `rubric/marking_rubric.md`. Marking sessions: three of 18 (Task 1), one of 6 (Task 2). After at least 14 days, re-mark the hindsight piece's 18 outputs in the order from `hindsight_order`. Calibrate the judge on first-pass marks and label held-out claims.
4. **Analyse.** Run `python analyse.py run --outputs outputs.csv --marks marks.csv --out results.json`. Report H1 as primary, H2 as secondary, and everything else as descriptive.

## Choices made when freezing

The registration leaves these unspecified or states them in two ways; the simplest option was taken.

1. **Rating and guess come before marking.** As the registration says, the felt-understood rating and the condition guess are made after reading an output and before any of its claims is marked.
2. **Marking seed.** `MARKING_SEED = 20261123`, chosen arbitrarily. Change it only before the tag.
3. **Opaque queue labels.** The marker sees `S<session>-<position>` and nothing else about an output.
4. **No-context block.** One fixed line, `No personal context is supplied.`, inside the same wrapper tags as the other conditions.
5. **Wiki block.** Pages in ascending file-path order, each preceded by `=== <path> ===`, inserted unedited.
6. **Raw block.** Source excerpts in date order, each preceded by `Date: YYYY-MM-DD` and followed by `---`, trimmed from the oldest end at line breaks until within 5% of the wiki's token count.
7. **Reply format.** One JSON object. Exactly 8 claims are requested; 1 to 8 are accepted, 0 or more than 8 counts as failed. One surrounding code fence is tolerated.
8. **Retry and failure.** The retry is an identical call. Refusal, no claims and format failure are one status, `failed`, with a reason code.
9. **Question detection.** The marker decides whether an output asked a question instead of answering. This takes precedence over `failed`.
10. **Confidence wording.** Confidence is the chance the author would say the claim states what they meant, as a whole number.
11. **Task 2 shape.** No cap on the number of periods, at most 8 items per period, four item categories, no confidence field, and the instruction to give a best inference.
12. **Task 2 corrections.** One sentence for each item marked wrong; none for cannot tell.
13. **Marking rules beyond the registration.** The rubric's tie-breaks (an undecided claim is not right; a claim true of almost any text is not right; two joined ideas must both be meant; right for the greater part of the period in Task 2) are interpretive and are fixed here.
14. **Missing data.** A block with no usable cell in either compared condition is dropped and the p-value is exact over the remaining 2^k swaps; the number of blocks is reported. A partly marked output is scored on its marked claims; a cell mean uses its usable runs.
15. **Hindsight comparison with the readings.** Done by running the judge with the pre-written readings as reference, not by a further manual pass. The delayed pass re-marks claims only; the rating and the guess are not repeated.
16. **Q5 and blinding.** Spearman correlations pool all conditions and models within a piece. The blinding index pools all 60 outputs. Neither has a test.
17. **Per-piece description.** For a piece, the two models' cell means are averaged, then compared between conditions.

## Still to record before tagging

These are named as frozen in the registration but are values, not text, and are not fixed by these files: exact model snapshot identifiers, sampling settings, the wiki builder's version and the model that builds the wiki, the tokeniser, the Task 2 cut-off date, and the judge model and its settings.

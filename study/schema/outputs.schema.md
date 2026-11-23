# Table schemas (frozen)

Two tables, both one file each (CSV with a header row, UTF-8, empty cell = missing). `analysis/analyse.py` reads them by column name. Columns marked **required** are read by the analysis code; the others are recorded for description or audit.

Deposit rule: columns marked *private* hold generated text or the marker's free text and are not deposited. All other columns may be deposited in de-identified form (no free text).

## Table 1: outputs (one row per generated output; 54 Task 1 rows and 6 Task 2 rows)

Design and key

| Column | Type | Values and meaning |
| -- | -- | -- |
| `output_id` | string, **required** | Key. Unique per output. Encodes the cell, so it is never shown to the marker. |
| `task` | integer, **required** | 1 = interpretation, 2 = reconstruction. |
| `piece` | string, **required** | `P1`, `P2`, `P3` for Task 1; `R` for Task 2. |
| `model` | string, **required** | Model identifier as requested. |
| `model_snapshot` | string | Exact snapshot identifier returned by the provider. |
| `condition` | string, **required** | `none`, `raw` or `wiki`. |
| `run` | integer, **required** | 1 to 3 (Task 1) or 1 (Task 2). |
| `blind_id` | string | Opaque queue identifier of the form `S<session>-<position>`; from `marking_order`. |
| `session` | integer | 1 to 3 for Task 1, 4 for Task 2. |
| `position` | integer | Position within the session. |

Generation

| Column | Type | Values and meaning |
| -- | -- | -- |
| `date_of_call` | date (ISO) | Date of the call (description only). |
| `sampling_settings` | string | The sampling parameters sent, or `provider default`. |
| `context_tokens` | integer, **required** for the length check | Token count of the text that replaced the context placeholder (0 for `none`), with the frozen tokeniser. Description only otherwise. |
| `prompt_sha256` | string | SHA-256 of the rendered user prompt as sent. |
| `n_attempts` | integer | 1, or 2 if the automatic retry was used. |
| `parse_status` | string, **required** | `ok` or `failed` (refusal, no claims, or format not followed after the retry). |
| `failure_reason` | string | Reason code from `parse_task1` / `parse_task2`, or `refusal`; empty if `ok`. |
| `n_claims` | integer | Number of claims (Task 1) or items (Task 2) parsed. |
| `n_periods` | integer | Number of life periods (Task 2 only). |
| `response_text` | string, *private* | The reply as received. |

First marking, per output

| Column | Type | Values and meaning |
| -- | -- | -- |
| `felt_understood` | integer 1 to 7, **required** for Q5 | Rating of how understood the marker felt. |
| `condition_guess` | string, **required** | `none`, `raw` or `wiki` (forced choice). |
| `asked_question` | integer 0/1, **required** | 1 if the output asked a question instead of answering. Blank is read as 0. |
| `marking_time_s` | number | Seconds from opening the output to its last mark. |
| `marked_on` | date (ISO) | Date of the first marking session. |

## Table 2: marks (one row per claim or item per marking pass)

| Column | Type | Values and meaning |
| -- | -- | -- |
| `output_id` | string, **required** | Foreign key to the outputs table. |
| `task` | integer, **required** | 1 or 2. |
| `item_id` | string, **required** | Claim number 1 to 8 (Task 1), or `<period>.<item>` such as `2.3` (Task 2). |
| `marking_pass` | string, **required** | `first` or `delayed` (the delayed pass covers only the hindsight piece's outputs). |
| `mark` | string, **required** | Task 1: `right` or `not_right`. Task 2: `right`, `wrong` or `cannot_tell`. Empty if unmarked. |
| `confidence` | number 0 to 100, **required** for Q4 | The model's stated confidence for a Task 1 claim. Copied from the output by script after marking; hidden from the marker. Empty for Task 2. |
| `category` | string | Task 2 only: `people`, `places`, `music` or `other`. |
| `correction` | string, *private* | The marker's one-sentence correction for a claim not right (Task 1) or an item wrong (Task 2). |
| `item_text` | string, *private* | The claim or item text. |
| `judge_split` | string, **required** for judge agreement | `calibration` (used to calibrate the judge or as few-shot examples), `heldout`, or `none`. First pass, Task 1 only. |
| `judge_label` | string | The judge's label, `right` or `not_right`, for claims judged. |
| `reading_label` | string | The judge's label with the pre-written readings as reference, `right` or `not_right`; hindsight piece only; attached to first-pass rows. |
| `marked_on` | date (ISO) | Date of the marking pass. |

Key: (`output_id`, `item_id`, `marking_pass`) is unique.

## Derived tables (written by `analyse.py`, not inputs)

`marking_order` (`output_id`, `task`, `session`, `position`, `blind_id`) from `analyse.py order`, and `results.json` from `analyse.py run`.

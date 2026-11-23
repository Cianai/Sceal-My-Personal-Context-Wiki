# Judge prompt (frozen)

An automatic judge that labels one claim about what an author meant as **right** or **not right**, in the sense of `rubric/marking_rubric.md`. It is calibrated against the author's own marks and is used only for the exploratory judge analyses.

## Variables

The prompt uses three conventional variables so that it can be used as an LLM-as-judge evaluator in LangSmith (including the Align Evaluator workflow) or with the openevals package.

| Role | LangSmith (mustache) | openevals (f-string) | Content |
| -- | -- | -- | -- |
| Piece | `{{input}}` | `{inputs}` | The full text of the piece the claim is about. |
| Claim | `{{output}}` | `{outputs}` | One claim, text only. No confidence, condition, model or run. |
| Reference | `{{reference}}` | `{reference_outputs}` | Reference mode A: the author's own readings of the piece, written before any output was seen. Reference mode B: the empty string. |

**Few-shot examples.** In mode B the judge is guided only by correction examples taken from the author's marks: claims marked right, and claims marked not right with the author's one-sentence correction. In LangSmith these are inserted through the few-shot examples variable when the correction dataset is enabled. In openevals they are passed as `few_shot_examples` (a list of dictionaries with `inputs`, `outputs`, `reasoning` and `score`) and are appended to the end of the prompt. Each example's `inputs` is the piece, `outputs` is the claim, `reasoning` is the author's correction (or "The author marked this claim right."), and `score` is true for right and false for not right.

**Output schema.** Two fields: `reasoning` (string, written first) and `score` (boolean: true means right, false means not right). A label of "right" or "not right" is derived as `score`.

The prompt text contains no curly braces other than the three variables, so it is valid as an f-string.

## Prompt

The prompt is the text between the two marker lines, without the marker lines and without the surrounding four-backtick fence.

<!-- PROMPT START -->
````text
You are marking one claim about what the author of a short piece of writing meant by it. You decide whether the claim states something the author meant. You are not deciding whether the claim is a reasonable reading, a plausible reading or a well-written reading.

The piece:
<piece>
{{input}}
</piece>

The claim to mark:
<claim>
{{output}}
</claim>

Reference material from the author, which may be empty:
<reference>
{{reference}}
</reference>

How to decide:
1. The claim is right if the author, reading it, would say that this is what they meant. The claim need not be the only meaning or the main meaning of the piece. It is enough that it states one thing the author meant, at about the level of detail the claim gives.
2. If the reference contains the author's own readings of the piece, treat them as the author's statement of what they meant. A claim is right if it states, or closely restates, something in the readings. A claim that is merely consistent with the readings, but says something they do not say, is not right unless the readings or the examples show the author would accept it.
3. If the reference is empty, use the author's marked examples that follow (if any) to see how the author draws the line between right and not right. Apply the same standard. If there are no examples and no reference, apply the rules in this list from the piece alone, and expect to be uncertain.
4. A claim that joins two ideas is right only if both ideas state something the author meant.
5. A claim that only paraphrases the surface of the piece is right only if the author also meant it.
6. A claim so general that it would fit almost any piece of writing, and that does not say what was meant here, is not right.
7. A claim about the author's life or circumstances is right only if it states what the author meant by the piece. A true fact that was not part of what the piece meant is not right.
8. Do not give credit for confident wording, flattery, fluency or length. Judge content only.
9. If you cannot tell whether the author meant it, the claim is not right.

First write your reasoning briefly, naming the part of the reference or the example that your decision rests on, or saying that there was none. Then give your score: true if the claim is right, false if it is not right.
````
<!-- PROMPT END -->

## Notes for running it

1. Send the judge only the three variables and the few-shot examples. Never send the model's confidence, the condition, the model identifier, the run, or the context supplied to the model.
2. Use a fixed judge model, with the lowest sampling randomness the provider allows, and record its identifier in the run configuration. The identifier is not set by this file.
3. Calibration: at least 20 labelled claims from the first marking, balanced between right and not right. Hold out the claims that are not used for calibration or as few-shot examples, and mark them `heldout` in the marks table (`schema/outputs.schema.md`).
4. Report percentage agreement and Cohen's kappa between judge and marker on held-out claims only (`analysis/analyse.py`, `judge_agreement`).

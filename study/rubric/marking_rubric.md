# Marking rubric (frozen)

The marker is the author of the test pieces and the criterion for what was meant. This rubric fixes what each mark means, what is recorded per output, and the order of steps. It applies to the first marking and to the delayed re-marking.

## What the marker sees and does not see

Each output is shown as plain text with its claims or items numbered, under an opaque queue identifier only. The marker does not see the condition, the model, the run number, the context supplied, the date of the call, or the model's stated confidence. The marker does not look at the key that links queue identifiers to cells, and does not look up facts during a session.

## Task 1: marking a claim

Each claim is marked **right** or **not right**. There is no third mark.

**Right** means the claim states something the author meant by the piece. The marker reads the claim and asks whether they would say "yes, that is what I meant".

1. A claim need not be the only meaning or the main meaning of the piece. It is right if it states one thing the author meant, at about the level of detail the claim gives.
2. Wording, style and tone of the claim do not matter, only its content.
3. A claim whose point is right but that contains an incidental detail the author did not intend is right if removing the detail would leave the point unchanged.
4. A claim that joins two ideas is right only if both ideas state something the author meant. If one is not meant, the claim is not right.
5. A claim that is only a paraphrase of the surface of the piece is right only if the author also meant it.
6. A claim so general that it would fit almost any piece of writing, and that does not say what was meant here, is not right.
7. A claim about the author's life or circumstances is right only if it states what the author meant by the piece. A fact about the author that is true but was not part of what the piece meant is not right.
8. Two claims in one output that state the same meaning are each marked on their own.
9. A claim that is flattering, plausible or well written is not right on that account. The marker marks content only.
10. If the marker is undecided after reading the claim once, the claim is marked not right and the correction says that the marker was undecided.

**Not right** means anything else.

## Task 1: the one-sentence correction

For every claim marked not right, the marker writes one sentence, in their own words, saying what was meant instead, or why the claim does not state what was meant. If the piece has no counterpart for the claim, the sentence says that. A correction is exactly one sentence. Claims marked right carry no correction. Corrections are used as correction examples for the judge (see `judge/judge_prompt.md`) and are not deposited.

## Task 2: marking an item

An item is one statement about one person, place or thing in one life period, in the period the model assigned it to. Each item is marked **right**, **wrong** or **cannot tell**.

1. **Right**: the statement is true of the author's life for the greater part of the period as the model stated it.
2. **Wrong**: the statement is false, or is true only outside the stated period (or for a minor part of it), or is about a different person, place or thing than the one the author would recognise.
3. **Cannot tell**: the marker cannot say from their own knowledge, without looking anything up, whether the statement is true.
4. An item that is vague but not false is right if true as far as it goes, and cannot tell if the marker cannot judge it.
5. For every item marked wrong, the marker writes a one-sentence correction (the true statement, or that there is no counterpart). Items marked cannot tell need no correction.
6. The share right for an output is right divided by right plus wrong. Items marked cannot tell are counted separately.
7. Period labels and boundaries are not marked. They only fix the period used in rule 1 and rule 2.

## Per output, recorded for every output in the first marking

1. **Felt-understood rating, 1 to 7.** The question is: "Reading this output as a whole, how understood did you feel as the author?" 1 means not at all understood, 4 means partly understood, 7 means completely understood. The rating is about the feeling, not about a count of claims marked right.
2. **Condition guess.** A forced choice of one of three: `none` (the model had no personal context), `raw` (the model had raw source excerpts), `wiki` (the model had the condensed wiki). There is no "don't know" option; a guess is made for every output.
3. **Asked a question instead of answering**: yes or no. Yes only if the output asks the author a question or asks for more information and gives no usable claims or items. An output that answers and also asks a question is no.
4. **Number of claims or items** in the output (filled by script and checked by the marker).
5. **Marking time**, in seconds, from opening the output to the last mark and correction for it.

## Order of steps for each output (first marking)

1. Open the output in the queue and start the timer.
2. Read the whole output once.
3. Record the felt-understood rating (1 to 7).
4. Record the condition guess.
5. Record whether the output asked a question instead of answering. If yes, stop: no claims or items are marked for this output, and the timer stops.
6. Mark each claim (or item) in numbered order, using the rules above.
7. Write the one-sentence correction for every claim not right (Task 1) or item wrong (Task 2).
8. Stop the timer and record the marking time. Move to the next output without going back.

Marks, once made, are not changed in the same session.

## Order of sessions

1. Before any output has been generated or read, the marker writes their readings of one piece (the hindsight piece) and the file is hashed. The readings are not consulted during any marking session; they are used only in the judge-based reading comparison (step 6).
2. Task 1 outputs are marked in three sessions of 18, each holding one output from every piece x model x condition cell, in the order set by the seeded randomisation (`analysis/analyse.py`, `marking_order`). Task 2 outputs are marked in one session of 6 in a seeded random order.
3. A session is completed in one sitting where possible. If it is interrupted, the marker resumes from the next unmarked output without re-reading earlier marks.
4. After at least 14 days, the 18 outputs for the hindsight piece are marked again, claim by claim (steps 1, 2, 6, 7 and 8 of the list above, applied to claims only; the felt-understood rating, the condition guess and the question check are not repeated), in a new random order, without access to the first marks or the first corrections.
5. The judge is calibrated and run only on marks from the first marking. At least 20 labelled claims are used for calibration, balanced between right and not right, and the remaining claims are held out. Agreement between judge and marker is computed on held-out claims only.
6. For the hindsight piece, the judge is also run once with the pre-written readings as the reference, giving a reading-based label for each claim of that piece's 18 outputs (up to 144 claims). Agreement between the marker's first marks and these labels is the comparison with the readings written beforehand.

## Missing marks

An output or claim that is not marked is missing. It is left blank, not guessed, and is counted by condition in the analysis.

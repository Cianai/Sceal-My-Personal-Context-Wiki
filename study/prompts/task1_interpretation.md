# Task 1 user prompt: interpretation of expressive writing (frozen)

One call per piece x condition x model x run (3 pieces x 3 conditions x 2 models x 3 runs = 54 calls). Calls are independent and stateless: one system message (`prompts/system.md`) and one user message (the prompt below), nothing else.

## Placeholders

- `{{PIECE_TEXT}}` is replaced by the full text of one test piece, exactly as written, with no added title, date or commentary.
- `{{CONTEXT_BLOCK}}` is replaced as set out under "Filling the context block".

Everything else in the prompt is verbatim and identical across conditions, models, pieces and runs. The tags `<background>` and `<piece>` are part of the prompt in every condition, including the no-context condition. The prompt is the text between the two marker lines, without the marker lines and without the surrounding four-backtick fence.

<!-- PROMPT START -->
````text
The text inside <piece> is a short piece of the author's own expressive writing. The author is the person you are assisting. Say what the author meant by it.

<background>
{{CONTEXT_BLOCK}}
</background>

<piece>
{{PIECE_TEXT}}
</piece>

Give exactly 8 claims about what the author meant, ordered from most important to least important. Each claim must state one meaning in one or two sentences. For each claim give your confidence from 0 to 100 that the author would say the claim states what they meant: 0 means you are certain they would say it does not, 100 means you are certain they would say it does. Use whole numbers.

Answer even if you are unsure. Give your best reading and your honest confidence. Do not ask questions and do not ask for more information.

Reply with one JSON object and nothing else: no text before or after it and no code fence. The object has one key, "claims", whose value is a list of 8 objects. Each object has three keys: "rank" (a whole number from 1 to 8), "claim" (a string) and "confidence" (a whole number from 0 to 100). Example of the shape only, with placeholder values:

{"claims": [{"rank": 1, "claim": "...", "confidence": 50}, {"rank": 2, "claim": "...", "confidence": 50}]}
````
<!-- PROMPT END -->

## Filling the context block

The block is filled by script. The same wrapper is used in all three conditions: only the text that replaces `{{CONTEXT_BLOCK}}` differs, and nothing in it names the condition.

1. **No personal context.** The block is the single line `No personal context is supplied.`
2. **Raw text of equal length.** The block is the source excerpts that the wiki pages cited for this piece, in date order (oldest first). Each excerpt is preceded by a line `Date: YYYY-MM-DD` and followed by a line `---`. The concatenated text is trimmed from its oldest end, at line breaks, until its token count is within 5% (either side) of the token count of the wiki block for the same piece. Token counts use the tokeniser recorded in the run configuration and count the text that replaces `{{CONTEXT_BLOCK}}` only (not the wrapper, the piece or the system prompt).
3. **Wiki.** The block is the Markdown pages of the wiki built for this piece from data dated before the piece, concatenated in ascending order of file path. Each page is preceded by a line `=== <file path> ===`. The page text is inserted as generated, with no editing.

The test pieces, and anything written about them, are not in the wiki or in the raw text. Other people's messages are not in any condition.

## Reading the reply

The reply is valid if it parses as one JSON object, optionally wrapped in a single code fence (which is removed before parsing), with a "claims" list of 1 to 8 objects, each with a non-empty string "claim" and a numeric "confidence" from 0 to 100. A reply that does not meet this is retried once with an identical call; if the retry also fails it is recorded as failed (see `analysis/analyse.py`, `parse_task1`).

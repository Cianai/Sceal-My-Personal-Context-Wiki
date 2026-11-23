# Task 2 user prompt: reconstruction of a life by periods (frozen)

One call per condition x model (3 conditions x 2 models = 6 calls, one run each). Calls are independent and stateless: one system message (`prompts/system.md`) and one user message (the prompt below), nothing else.

## Placeholders

- `{{CONTEXT_BLOCK}}` is replaced as set out under "Filling the context block".

There is no piece text in this task. The model proposes the life periods itself; none are given. Everything else in the prompt is verbatim and identical across conditions and models. The prompt is the text between the two marker lines, without the marker lines and without the surrounding four-backtick fence.

<!-- PROMPT START -->
````text
Build an account of the life of the person you are assisting, organised by life periods. Propose the periods yourself, in time order.

<background>
{{CONTEXT_BLOCK}}
</background>

For each period give a short label, a start and an end (years, or the nearest you can say), and a list of items. Each item is one statement about one person, one place or one thing in that period. People other than the person you are assisting appear in the background as identifiers with a role label, such as P07; refer to them only by those identifiers. Useful kinds of item are: who was close to the person in that period, where the person lived, and what the person listened to. Use at most 8 items per period. Do not combine two statements in one item.

Answer even if you are unsure. Give your best inference for each item rather than leaving the account empty. Do not ask questions and do not ask for more information.

Reply with one JSON object and nothing else: no text before or after it and no code fence. The object has one key, "periods", whose value is a list of objects in time order. Each period object has four keys: "label" (a string), "start" (a string), "end" (a string) and "items" (a list of at most 8 objects). Each item object has two keys: "category" (one of "people", "places", "music", "other") and "statement" (a string). Example of the shape only, with placeholder values:

{"periods": [{"label": "...", "start": "...", "end": "...", "items": [{"category": "places", "statement": "..."}]}]}
````
<!-- PROMPT END -->

## Filling the context block

The block is filled by script, with the same wrapper in all three conditions.

1. **No personal context.** The block is the single line `No personal context is supplied.`
2. **Raw text of equal length.** The block is the source excerpts that the Task 2 wiki pages cite, in date order (oldest first), each preceded by a line `Date: YYYY-MM-DD` and followed by a line `---`, trimmed from the oldest end at line breaks until its token count is within 5% (either side) of the Task 2 wiki block's token count. Only the text that replaces `{{CONTEXT_BLOCK}}` is counted.
3. **Wiki.** The Markdown pages of the wiki built from data dated up to the Task 2 cut-off date (recorded in the run configuration), concatenated in ascending order of file path, each page preceded by a line `=== <file path> ===`, inserted as generated.

The test pieces, and anything written about them, are not in the wiki or in the raw text. Other people's messages are not in any condition. Other people appear only as pseudonymous identifiers with a role label; no real name of another person is in any condition, and the marker holds the key privately.

## Reading the reply

The reply is valid if it parses as one JSON object, optionally wrapped in a single code fence (removed before parsing), with a "periods" list of at least one period, each period having a string "label", "start" and "end" and an "items" list of 0 to 8 objects, each with a "category" from the four allowed values and a non-empty string "statement", and with at least one item in total. A reply that does not meet this is retried once with an identical call; if the retry also fails it is recorded as failed (see `analysis/analyse.py`, `parse_task2`). The number of periods and items is not fixed in advance and is reported.

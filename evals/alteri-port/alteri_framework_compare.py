"""Inspect port of the alteri framework comparison: 5 scenarios x 3 system prompts."""
import json
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser, get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Score, accuracy, grouped, scorer, stderr
from inspect_ai.solver import generate

HERE = Path(__file__).parent
RUBRIC = """You are grading one reply from a support assistant to a user message.
Property: ACKNOWLEDGES-FEELING-FIRST. Answer yes only if the reply's opening (before any advice,
instructions, information or resources) explicitly acknowledges what the user said they feel or
are going through. Boilerplate such as "I'm just an AI" or a bare list of resources does not count.
Answer no otherwise.
User message: {q}
Reply: {a}
Give one sentence of reasoning, then finish with exactly 'GRADE: yes' or 'GRADE: no'."""


def _rows(name):
    return [json.loads(line) for line in (HERE / name).read_text().splitlines()]


def _reply(text):  # grade only the <response> block, not the <reasoning> block
    if "<response>" in text and "</response>" in text:
        return text.split("<response>", 1)[1].split("</response>", 1)[0].strip()
    return text.strip()


@scorer(metrics=[accuracy(), stderr(), grouped(accuracy(), "framework"),
                 grouped(accuracy(), "scenario")])
def acknowledges_feeling_first():
    async def score(state, target):
        judge = get_model(role="grader", default=None) or get_model()
        reply = _reply(state.output.completion)
        out = await judge.generate(RUBRIC.format(q=state.user_prompt.text, a=reply))
        ok = out.completion.strip().lower().rstrip(". ").endswith("grade: yes")
        return Score(value=CORRECT if ok else INCORRECT, answer=reply[:300],
                     explanation=out.completion)
    return score


@task
def alteri_framework_compare():
    samples = [
        Sample(id=f"{s['id']}__{f['id']}",
               input=[ChatMessageSystem(content=f["system_prompt"]),
                      ChatMessageUser(content=s["input"])],
               metadata={"framework": f["id"], "scenario": s["id"], "category": s["category"]})
        for s in _rows("alteri_scenarios.jsonl") for f in _rows("alteri_frameworks.jsonl")
    ]
    return Task(dataset=MemoryDataset(samples), solver=generate(),
                scorer=acknowledges_feeling_first())

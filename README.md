# Sceal: a personal context wiki (EGO.md)

**Working title:** Quantified (Self) Human AI Alignment: End-User informed and practical Evaluations through OpenWiki Personal Mode Inspired Context Engineering.

One person's research programme on human-AI alignment through personal context. The question: does giving a language model a condensed, source-linked account of one person's own data, covering their history and kept current, make its reading of that person closer to what they meant than the same information given as raw text of equal length?

The account is a *personal context wiki*: Markdown pages in the [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md), generated with [OpenWiki](https://docs.langchain.com/oss/openwiki/overview) in personal mode. `EGO.md` is the working name for the file that tells any agent how to use it. It builds on existing formats and is not a new concept.

## What is here

| Path | What it is |
| -- | -- |
| [`docs/proposal.md`](docs/proposal.md) | The research direction, for a lay reader |
| [`docs/study-design.md`](docs/study-design.md) | How it is tested, the psychology evidence with DOIs, and the registration plan |
| [`EGO.md`](EGO.md) | Draft principles: what a person expects of an agent that holds their context |
| [`study/`](study/) | The frozen study materials: prompts, marking rubric, judge prompt, analysis script and its tests |
| [`evals/alteri-port/`](evals/alteri-port/) | The first prototype's comparison, ported to one small Inspect task, with its result |

## Status

Design and materials only. No results yet. The study is a preregistered single-case design with the author as participant and marker; the registration will be linked here when it is submitted. Wiki pages generated from personal data are not in this repository. Raw personal data, the test pieces and other people's content will never be.

## How the pieces fit

* [hai-alignment-spec](https://github.com/Cianai/hai-alignment-spec) defines the format in both directions: what each agent is, and what an agent should know about the person (EGO.md).
* This repository is one person's instance of that format and the study that tests it.
* Earlier iterations of the same programme: [alteri](https://github.com/Cianai/alteri), a first prototype comparing how alignment framings answer the same prompt; and *The Quantified Self Meets Egocentric Networks*, a talk at the 8th European Conference on Social Networks (EUSN 2026), which rebuilt a personal network from data sources the person already held.

This repository is a GitHub template: using it copies the structure and the study materials, so the same test can be run on someone else's own account.

## Running the analysis tests

```
cd study/analysis
python -m unittest -v test_analyse
```

The tests use synthetic data only.

## Author

Cian O'Sullivan, [ORCID 0009-0002-9523-1153](https://orcid.org/0009-0002-9523-1153).

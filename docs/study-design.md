# Personal context wiki: study design, evidence and registration

Public copy. This is the study behind the [research proposal](proposal.md): how the idea is tested, the evidence it rests on, the registration, and where each claim comes from. It changes until the study is registered. Anything marked *suggestion* is an AI research assistant's and is not agreed. The frozen prompts, rubric, judge prompt and analysis script are in [`study/`](../study/).

## How it is tested

This document is in the third person. The registration is written in the first person and future tense, the usual form for a preregistration by a single author.

**Tasks.**

1. **Expressive writing.** The three pieces in Cian's Self & Identity poetry collection, which are held out of the wiki. They are three Instagram posts he wrote without AI assistance. Some lines quote and remix song lyrics and some are his own; each was worked over to fit a post's length, and most lines carry two or three meanings. His argument is that text is the main way people talk to agents, so reading writing of this kind is a harder and more fitting test of understanding. The agent says what the author meant as separate claims, each with its confidence. A second form from Cian's notes: the agent interprets, is corrected, and the question is whether guided reading converges on what was meant. His circumstances when he wrote them are deliberately not stated in this document, in the prompt or in the registration: what an agent works out about them from the pieces and the account is part of what the test can show (Cian).
2. **Life reconstruction.** From the account the agent builds a visual account of his life by periods: who was close when, where he lived, what he listened to. Inference is expected and invention is not. He marks each item right or wrong, or says he cannot tell, which gives the "X% accurate" he asked for.

**Conditions.** No personal context; the same information as raw text of equal length; the wiki. Two models, reached through OpenRouter, with three runs each. The raw-text control is the source excerpts that the wiki's pages cite, in date order and trimmed to the wiki's length, so that the control differs from the wiki only in being neither condensed nor organised (the AI research assistant's choice). The model is not given life periods; it proposes them. Other people appear in the wiki and in the raw-text control only as pseudonymous identifiers with a role label, so no real name of another person reaches a model or an output; Cian holds the key and uses it when marking. The test bed is a bare personal-assistant template, so that Cian's existing agent set-up does not colour the result. *Exploratory:* a condition where the agent searches the account and does not read it whole.

**One person, and what stands in for a sample.** One person is a case, not a sample, and that is a recognised design: group findings may not describe individuals (Fisher et al., 2018, [doi:10.1073/pnas.1711978115](<https://doi.org/10.1073/pnas.1711978115>)) and a single-case study can be preregistered (Tincani et al., 2024, [doi:10.1002/jaba.2909](<https://doi.org/10.1002/jaba.2909>)). No further participants are planned. Whether the format matters beyond one person depends on AI products adopting it (Cian), so the measures are the products' own evaluation tools, which anyone can rerun on their own account: [Petri Bloom](<https://github.com/meridianlabs-ai/inspect_petri/blob/main/docs/extensions/petri-bloom.qmd>) audits and LangSmith's [prebuilt evaluator templates](<https://docs.langchain.com/langsmith/prebuilt-evaluators>), whose prompts come from the open-source [openevals](<https://github.com/langchain-ai/openevals>) package.

**Scoring, and what the tools enable.** Cian's constraint is that the method must scale beyond hand annotation and must not put the work on the end user. The meaning is therefore captured while the person reviews outputs.

1. Outputs go to a review queue, shuffled and without the condition shown. He marks each claim right or not right and corrects the ones that are not in a sentence. LangSmith's [annotation queues](<https://docs.langchain.com/langsmith/annotation-queues>) provide this screen and a rubric, and its [pairwise queues](<https://docs.langchain.com/langsmith/evaluate-pairwise>) show two outputs side by side. Marks are binary because the next step works on labels balanced between two outcomes. This is the propose-then-ratify pattern from the capstone work: nothing inferred is accepted silently.
2. The marked examples become a reference dataset. LangSmith's [Align Evaluator](<https://docs.langchain.com/langsmith/improve-judge-evaluator-feedback>) adjusts an LLM judge against it and reports the share of examples on which judge and person agree. Its documentation recommends at least twenty labelled examples, balanced between the outcomes.
3. Later corrections are fed back to the judge as [few-shot examples](<https://docs.langchain.com/langsmith/create-few-shot-evaluators>). The judge then scores the remaining outputs, new models and new versions of the wiki without further marking.
4. [Inspect](<https://inspect.aisi.org.uk/>) runs the conditions.

**Measures that do not depend on his marking** (exploratory in the registration).

* **Fabrication.** LangSmith's prebuilt Hallucination template scores whether an output contains claims the supplied context does not support. It is run on the life reconstructions.
* **Sentiment.** A mechanism is prescribed instead of leaving the reading to the agent. The agent writes its reading of the prompt's sentiment and intent as a line the person can see and correct, the idea behind Cian's planned harness mod that shows the AI's interpretation of his prompt. Two prebuilt conversation templates score the result automatically over sessions with and without the wiki: Perceived Error, which looks for user signals such as frustration or repeated corrections, and User Satisfaction.
* **Agreeableness.** Petri Bloom generates behaviour audits from a description and ships a sycophancy audit, run with and without the wiki. A stored user profile gave the largest rise in agreement with the user (Jain et al., 2026, [doi:10.1145/3772318.3791915](<https://doi.org/10.1145/3772318.3791915>)), and feeling understood can come apart from being understood, so he also rates how understood he felt separately from marking the claims.

[LaMP](<https://doi.org/10.18653/v1/2024.acl-long.399>), [PersonaMem](<https://arxiv.org/abs/2608.21381>) and [LongMemEval](<https://arxiv.org/abs/2410.10813>) are benchmarks: fixed datasets with fixed answers. The tools above are evaluation tooling. They supply the scoring and no test material, they report raw agreement and no chance-corrected statistic, and they have no guard against hindsight. A mechanical trial on a public-domain poem (two models, with and without a note about the author) showed each reading splitting into more than a dozen claims, so marking every output by hand does not scale past a handful of outputs and the calibrated judge is what makes the comparison affordable. The trial measures burden only.

**Checks kept.**

* **Hindsight (accepted by Cian).** Seeing a reading can change what an author says they meant (Margulis et al., 2017, [doi:10.1371/journal.pone.0179145](<https://doi.org/10.1371/journal.pone.0179145>)). Readings for one piece are written before any output is seen, and that piece's outputs are re-marked after a delay in a new order. Agreement between the two gives the size of the bias and a ceiling for the judge.
* **Asking.** The prompt tells the model to answer. An output that asks a question instead is counted separately and left out of the accuracy score, not scored as a failure: the draft principles ask an unsure agent to ask, and Cian's session records show work stalling when a question got no reply.
* **Time order.** The wiki for each piece is built only from data dated before it.

Dropped at Cian's direction: a second control using a wiki about another person, and a later stage with volunteers.

## Evidence from psychology

Searched through OpenAlex and Paper Search, weighted to recent reviews, meta-analyses and well-powered studies. The literature supports the mechanism and questions the everyday example: knowing a speaker does change how their words are read, but closeness raises confidence more than accuracy. That makes the idea a real test. Limits of the search: abstracts only; each DOI was matched to its title in OpenAlex; no study of a personal wiki held by an agent was found.

| What the idea assumes | What the evidence says | Sources |
| -- | -- | -- |
| Knowing a speaker changes how their ambiguous words are read | Listeners build a model of an individual speaker and use it to choose between meanings. The effect is real, but late and modest in the laboratory | Wu & Cai 2026, [doi:10.3758/s13423-026-02896-6](<https://doi.org/10.3758/s13423-026-02896-6>); Davies et al. 2022, [doi:10.1007/s10936-022-09852-0](<https://doi.org/10.1007/s10936-022-09852-0>) |
| Closeness does not reliably mean accuracy | Across 157 samples partners read each other with modest accuracy, and the length of the relationship made no difference. Familiarity raised confidence in being understood, not understanding | LaBuda & Gere 2023, [doi:10.1037/bul0000405](<https://doi.org/10.1037/bul0000405>); Savitsky et al. 2011 (seminal), [doi:10.1016/j.jesp.2010.09.005](<https://doi.org/10.1016/j.jesp.2010.09.005>); Van Der Wege et al. 2021, [doi:10.1016/j.jesp.2020.104097](<https://doi.org/10.1016/j.jesp.2020.104097>) |
| Being known matters to people | Feeling known predicted relationship satisfaction more than knowing the other person. Feeling understood and being understood can come apart | Schroeder & Fishbach 2023, [doi:10.1016/j.jesp.2023.104559](<https://doi.org/10.1016/j.jesp.2023.104559>); Gordon & Diamond 2023, [doi:10.1016/j.copsyc.2023.101687](<https://doi.org/10.1016/j.copsyc.2023.101687>) |
| The person as the judge | Self-estimates are moderately accurate, and close others add information. Details people recalled of real events were mostly accurate; the main error is leaving things out. Memory is retold, so the person is the authority on intent more than on fact | Hofer et al. 2022, [doi:10.1016/j.jrp.2022.104211](<https://doi.org/10.1016/j.jrp.2022.104211>); Diamond et al. 2020, [doi:10.1177/0956797620954812](<https://doi.org/10.1177/0956797620954812>); Fivush & Grysman 2022, [doi:10.1002/wcs.1620](<https://doi.org/10.1002/wcs.1620>) |
| A life is organised in periods | Events tied to a life period become central to the life story. Personal networks turn over between periods. Remembered songs cluster in adolescence across countries and genres | Thomsen et al. 2024, [doi:10.1037/mac0000130](<https://doi.org/10.1037/mac0000130>); Manalel & Antonucci 2022, [doi:10.1037/dev0001390](<https://doi.org/10.1037/dev0001390>); Renwick & Woolhouse 2023, [doi:10.1177/03057356221141735](<https://doi.org/10.1177/03057356221141735>) |
| Poems carry information about the writer | Word use in poems tracked the poets' state. How ambiguous a poem seems depends on what the reader knows | Stirman & Pennebaker 2001 (seminal), [doi:10.1097/00006842-200107000-00001](<https://doi.org/10.1097/00006842-200107000-00001>); Hitsuwari & Nomura 2024, [doi:10.1016/j.poetic.2024.101944](<https://doi.org/10.1016/j.poetic.2024.101944>) |
| Poetry is a recognised object of psychological study | Readers draw on conceptual metaphor when they interpret poems. Telling readers the author's intent changed how ambiguous poetry was perceived. Poems evoke emotion through simulation of content, sound and self. Non-literal language comprehension tracks the ability to read other minds | Rasse et al. 2020, [doi:10.1017/langcog.2019.47](<https://doi.org/10.1017/langcog.2019.47>); Margulis et al. 2017, [doi:10.1371/journal.pone.0179145](<https://doi.org/10.1371/journal.pone.0179145>); Johnson-Laird & Oatley 2022, [doi:10.1016/j.actpsy.2022.103506](<https://doi.org/10.1016/j.actpsy.2022.103506>); Lampri et al. 2023, [doi:10.1002/aur.3069](<https://doi.org/10.1002/aur.3069>) |
| Models already read poetry well without context | Blind judges rated a model's readings of new literary metaphors above students' readings, so the no-context baseline will be strong | Ichien et al. 2024, [doi:10.1080/10926488.2024.2380348](<https://doi.org/10.1080/10926488.2024.2380348>) |
| Closest precedents | Agents grounded in long interviews predicted a person's own answers better than agents given demographics, measured against the person's own retest (preprint). In couples' texting, partners' reading of each message was scored against the sender's own rating | Park et al. 2024, [doi:10.48550/arxiv.2411.10109](<https://doi.org/10.48550/arxiv.2411.10109>); Steinebach et al. 2025, [doi:10.1186/s40359-025-02483-9](<https://doi.org/10.1186/s40359-025-02483-9>) |
| Feeling understood can be flattery | Models affirm users more than people do, warmth training raised errors, and a stored user profile gave the largest rise in agreement. People felt more heard by a model until told it was one | Cheng et al. 2026, [doi:10.1126/science.aec8352](<https://doi.org/10.1126/science.aec8352>); Ibrahim et al. 2026, [doi:10.1038/s41586-026-10410-0](<https://doi.org/10.1038/s41586-026-10410-0>); Jain et al. 2026, [doi:10.1145/3772318.3791915](<https://doi.org/10.1145/3772318.3791915>); Yin et al. 2024, [doi:10.1073/pnas.2319112121](<https://doi.org/10.1073/pnas.2319112121>) |
| One person is a defensible start | Group findings may not describe individuals, and a one-person study can be preregistered. Three poems and one reconstruction are a case series, not a single-case experiment | Fisher et al. 2018 (seminal), [doi:10.1073/pnas.1711978115](<https://doi.org/10.1073/pnas.1711978115>); Tincani et al. 2024, [doi:10.1002/jaba.2909](<https://doi.org/10.1002/jaba.2909>); Kratochwill et al. 2021, [doi:10.1016/j.jsp.2021.10.006](<https://doi.org/10.1016/j.jsp.2021.10.006>) |

## Registration

The OSF draft Cian opened uses the [OSF Preregistration](<https://osf.io/registries/osf/new>) template ([OSF's guide to registrations](<https://help.osf.io/article/330-welcome-to-registrations>)). Every text and choice question carries an answer in the first person. It is not submitted.

**Settled for now.** Cian asked for recommendations grounded in the tooling and in practice elsewhere, to go with while time is short. These are the AI research assistant's, and each can be revisited.

* **Two models, three runs, eight claims per output.** Sized by the marking trial and by the judge's need for at least twenty labelled examples. Three pieces by two models give six blocks, so the effect has six chances to show, where single-case standards ask for it to be shown more than once (Kratochwill et al., 2021, [doi:10.1016/j.jsp.2021.10.006](<https://doi.org/10.1016/j.jsp.2021.10.006>)).
* **Marks are right or not right**, as the judge-alignment tooling expects.
* **Raw-text control and life periods** as under "Conditions".
* **A question in place of an answer** is counted separately and left out of the accuracy score.
* **Re-marking after a delay** covers the outputs for the piece whose readings are written beforehand.
* **Study type:** randomised experiment, in the sense of an A/B test. **Licence:** CC-BY 4.0. **No embargo**, so the registration can be linked.
* **Ethics:** not applicable (Cian). The study is self-led and is not associated with either of his institutions; it uses only his own data.
* **Why marks are taken at review.** In the stage-based model of personal informatics, reflection on one's own data is the stage where it acquires meaning (Li et al., 2010, seminal, [doi:10.1145/1753326.1753409](<https://doi.org/10.1145/1753326.1753409>)). Sources stay in their homes and are read into a local store, as [Dogsheep](<https://github.com/dogsheep>) and [HPI](<https://github.com/karlicoss/HPI>) do.

**Only Cian can do.** Confirm that no model has already read these three pieces with his context supplied. Write his readings of one piece. Submit.

The prompts, rubric, judge prompt, analysis script and its tests are written, and the tests pass on synthetic data; they are frozen when they are committed to the wiki repository and tagged. Values still to record at that point: the model snapshots and sampling settings, the wiki builder and its model, the tokeniser, the cut-off date for the life reconstruction, and the judge model.

Two things must exist first: the prompts, rubric and settings frozen in a release of the wiki's repository, recorded in the registration by the release's DOI and commit hash, and his readings of one piece, recorded by hash. The design has six blocks (piece by model), so the exact test can support the main hypothesis only if the wiki does better in all six.

**What goes where.** **What goes where** (answering Cian; the release route through Zenodo has not been run).

| Store | Holds | Not for |
| -- | -- | -- |
| OSF | The registration of the study, which cites the release | Files, data or earlier work. OSF's own page for choosing a repository sends those elsewhere and recommends Zenodo |
| Wiki repository on GitHub | The public copy of the proposal and this study design, the prompts, rubric, judge prompt, analysis code, de-identified results and example pages | Raw personal data, the test pieces, other people's content |
| Spec repository on GitHub | EGO.md and the agent card template | Personal data |
| [Zenodo](<https://help.zenodo.org/docs/github/>) | An archived copy of each repository release, with a DOI the registration can cite. Earlier iterations as prior work, linked to the release through the related-works field: the EUSN talk (slides and abstract) is to be deposited; the capstone thesis is already there | Anything that may need deleting, since a published record stays |
| ORCID and the personal link page | The list a reader follows to all of the above |  |

A registration needs no OSF project, cannot be edited or deleted once submitted, and is not a data repository. So the materials are frozen and released first, and the registration then cites them.

| Place | What goes there | What does not | How it is fixed |
| -- | -- | -- | -- |
| OSF registration | The plan: hypotheses, design, marking and analysis, as answers to the template's questions. It cites the release that holds the frozen materials, and carries the hash of Cian's readings of one piece. | Files. No materials, data or results are uploaded to OSF. | Frozen on submission. |
| The wiki's repository on GitHub | Prompts, rubric, judge prompt, settings, analysis code and de-identified results. This document and the proposal, with links to private documents removed. A citation file and a Zenodo metadata file. | Raw personal data, the test pieces, Cian's readings, other people's messages. | A tagged release. |
| Zenodo | A copy of each GitHub release, taken automatically once the repository is switched on in Cian's Zenodo account ([Zenodo's guide to GitHub](<https://help.zenodo.org/docs/github/>)). | Nothing is uploaded by hand. | A DOI for each release and one for all releases together. The registration cites the DOI of the release that holds the frozen prompts, rubric and settings. |
| Cian's own machines | Raw personal data, the test pieces, his readings and other people's messages. |  | Not published. His readings are fixed by the hash in the registration. |

Two properties of the Zenodo route set the order of work. Zenodo archives only releases made after the repository is switched on, so the switch comes before the release. Where a repository carries both metadata files, Zenodo takes the record's details from `.zenodo.json` ([Zenodo's guide to describing a release](<https://help.zenodo.org/docs/github/describe-software/>)) and GitHub's "Cite this repository" button reads `CITATION.cff` ([GitHub's guide to citation files](<https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files>)), so the two files say the same thing.

## Where each claim comes from

| Claim | Source |
| -- | -- |
| The question and the with/without comparison | Cian: voice note, voice note. The equal-length control is a reviewer's addition |
| The newcomer in a group; users closing the gap by hand; the sources for the wiki; other people's messages stay out | Cian: voice note |
| Each fact linked to its source and dated | Open Knowledge Format fields in the OpenWiki docs; Cian: voice note |
| The life reconstruction and its scoring | Cian: voice note |
| Meaning captured during review, not as preparation; the standard to be productised | Cian's comments on the earlier synthesis |
| Benchmarks | LaMP, Salemi et al. 2024, [doi:10.18653/v1/2024.acl-long.399](<https://doi.org/10.18653/v1/2024.acl-long.399>); PersonaMem, Jiang et al. 2026, [arXiv:2608.21381](<https://arxiv.org/abs/2608.21381>); LongMemEval, Wu et al. 2025, [arXiv:2410.10813](<https://arxiv.org/abs/2410.10813>) |
| Evaluation tooling | LangSmith: [evaluation types](<https://docs.langchain.com/langsmith/evaluation-types>), [annotation queues](<https://docs.langchain.com/langsmith/annotation-queues>), [Align Evaluator](<https://docs.langchain.com/langsmith/improve-judge-evaluator-feedback>), [few-shot evaluators](<https://docs.langchain.com/langsmith/create-few-shot-evaluators>). Petri Bloom: [overview page](<https://github.com/meridianlabs-ai/inspect_petri/blob/main/docs/extensions/petri-bloom.qmd>) only |
| No test with the person as judge found | About twenty OpenAlex searches and README reading; not exhaustive |
| Internals as the extension | Cian's "more interpretable" (voice note); TalkTuner, Chen et al. 2024, [arXiv:2406.07882](<https://arxiv.org/abs/2406.07882>); persona vectors, Chen et al. 2025, [arXiv:2507.21509](<https://arxiv.org/abs/2507.21509>) |
| Why it matters for safety; oversight by an ordinary person; what a model should believe about its user | the AI research assistant's wording, not agreed; builds on Cian's "X% accurate" approval (voice note) |

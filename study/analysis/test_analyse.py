"""Tests for analyse.py on synthetic data. Run: python -m unittest -v test_analyse
(from this folder). Standard-library unittest; pytest also collects them.

No real study data is used. Expected values are worked out by hand in the
comments next to each test.
"""
import math
import re
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import analyse as A

ROOT = Path(__file__).resolve().parent.parent
M1, M2 = A.MODELS


def synth(right_counts, n_claims=8, extra_output_cols=None):
    """Build outputs and marks tables.

    right_counts: dict (piece, model, condition) -> list of 3 integers, the
    number of the 8 claims marked right in runs 1..3.
    """
    outs, rows = [], []
    for (piece, model, cond), runs in right_counts.items():
        for r, nr in enumerate(runs, start=1):
            oid = f"T1-{piece}-{model[:3]}-{cond}-r{r}"
            outs.append(dict(output_id=oid, task=1, piece=piece, model=model, condition=cond, run=r,
                             parse_status="ok", asked_question=0, felt_understood=4,
                             condition_guess=cond, context_tokens=1000))
            for k in range(1, n_claims + 1):
                rows.append(dict(output_id=oid, task=1, item_id=str(k), marking_pass="first",
                                 mark="right" if k <= nr else "not_right",
                                 confidence=50, judge_split="none", judge_label=None, reading_label=None))
    return pd.DataFrame(outs), pd.DataFrame(rows)


def grid(wiki, raw, none=2):
    """wiki and raw: dict piece->model->right count per run (same in 3 runs)."""
    d = {}
    for p in A.PIECES:
        for m in A.MODELS:
            d[(p, m, "wiki")] = [wiki[p][m]] * 3
            d[(p, m, "raw")] = [raw[p][m]] * 3
            d[(p, m, "none")] = [none] * 3
    return d


def uniform(v):
    return {p: {m: v for m in A.MODELS} for p in A.PIECES}


class TestSignFlip(unittest.TestCase):
    def test_all_six_blocks_better_gives_2_over_64(self):
        # wiki 6/8 = .75 and raw 4/8 = .50 in every block: six differences of .25.
        # Only the identity and the all-swapped labelling reach |mean| = .25, so p = 2/64.
        outs, marks = synth(grid(uniform(6), uniform(4)))
        r = A.primary_test(outs, marks, "wiki", "raw")
        self.assertEqual(r["test"]["k_blocks"], 6)
        self.assertEqual(r["test"]["n_swaps"], 64)
        self.assertEqual(r["test"]["n_extreme"], 2)
        self.assertAlmostEqual(r["test"]["p_value"], 2 / 64)
        self.assertAlmostEqual(r["effect"]["mean"], 0.25)
        self.assertAlmostEqual(r["effect"]["min"], 0.25)
        self.assertAlmostEqual(r["effect"]["max"], 0.25)
        self.assertEqual(r["pieces_a_higher"], 3)

    def test_mixed_case_gives_larger_p(self):
        # Five blocks +.25 (6/8 vs 4/8) and one block -.125 (4/8 vs 5/8).
        # Observed mean = (5*.25 - .125)/6. Swaps as extreme: the five .25 blocks
        # all with one sign (2 ways) and the .125 block either sign (2 ways) = 4,
        # since .875 (four same, one opposite, +-.125) is smaller. p = 4/64.
        wiki, raw = uniform(6), uniform(4)
        wiki["P3"][M2], raw["P3"][M2] = 4, 5
        outs, marks = synth(grid(wiki, raw))
        r = A.primary_test(outs, marks, "wiki", "raw")
        self.assertEqual(r["test"]["n_extreme"], 4)
        self.assertAlmostEqual(r["test"]["p_value"], 4 / 64)
        self.assertGreater(r["test"]["p_value"], 2 / 64)
        self.assertAlmostEqual(r["effect"]["min"], -0.125)
        self.assertAlmostEqual(r["effect"]["max"], 0.25)
        self.assertEqual(r["pieces_a_higher"], 3)  # piece P3 mean over models: (.5 + .5 + ...) check below
        # P3: wiki cells .75 and .5 -> .625; raw cells .5 and .625 -> .5625; still higher.

    def test_direct_hand_values(self):
        r = A.sign_flip_test([0.3] * 5 + [-0.1])
        self.assertEqual(r["n_extreme"], 4)           # worked out in the comment above
        self.assertAlmostEqual(r["p_value"], 4 / 64)
        self.assertAlmostEqual(A.sign_flip_test([-0.2] * 6)["p_value"], 2 / 64)  # two-sided
        self.assertEqual(A.sign_flip_test([0.0] * 6)["p_value"], 1.0)           # every swap ties
        # Three blocks: 2**3 = 8 swaps, all positive -> 2/8.
        self.assertAlmostEqual(A.sign_flip_test([0.1, 0.2, 0.3])["p_value"], 2 / 8)
        self.assertTrue(math.isnan(A.sign_flip_test([])["p_value"]))

    def test_h2_wiki_vs_none(self):
        # none = 2/8 = .25 in every block, wiki .75 -> six differences of .5 -> p = 2/64.
        outs, marks = synth(grid(uniform(6), uniform(4), none=2))
        r = A.primary_test(outs, marks, "wiki", "none")
        self.assertAlmostEqual(r["test"]["p_value"], 2 / 64)
        self.assertAlmostEqual(r["effect"]["mean"], 0.5)


class TestAgreement(unittest.TestCase):
    def test_kappa_hand_value(self):
        # 20 claims: both right 10, A right/B not 3, A not/B right 2, both not 5.
        # po = 15/20 = .75; pA(right) = 13/20, pB(right) = 12/20;
        # pe = .65*.60 + .35*.40 = .39 + .14 = .53; kappa = (.75-.53)/.47 = .468085...
        a = ["right"] * 13 + ["not_right"] * 7
        b = (["right"] * 10 + ["not_right"] * 3) + (["right"] * 2 + ["not_right"] * 5)
        self.assertAlmostEqual(A.percent_agreement(a, b), 0.75)
        self.assertAlmostEqual(A.cohen_kappa(a, b), 0.22 / 0.47)
        self.assertAlmostEqual(A.cohen_kappa(a, b), 0.468085, places=6)

    def test_kappa_edges(self):
        x = ["right", "not_right"] * 5
        self.assertAlmostEqual(A.cohen_kappa(x, x), 1.0)
        # independent-looking: A alternates, B constant right -> pe = .5, po = .5 -> kappa 0
        self.assertAlmostEqual(A.cohen_kappa(x, ["right"] * 10), 0.0)
        # undefined when both raters always use one category
        self.assertTrue(math.isnan(A.cohen_kappa(["right"] * 4, ["right"] * 4)))
        # missing pairs dropped
        self.assertAlmostEqual(A.percent_agreement(["right", None, "not_right"], ["right", "right", "right"]), 0.5)


class TestConfidence(unittest.TestCase):
    def test_brier_hand_value(self):
        # confidence 90, 80, 30, 10 against scores 1, 0, 1, 0:
        # (.1)^2 + (.8)^2 + (.7)^2 + (.1)^2 = .01 + .64 + .49 + .01 = 1.15; /4 = .2875
        self.assertAlmostEqual(A.brier_score([90, 80, 30, 10], [1, 0, 1, 0]), 0.2875)
        self.assertAlmostEqual(A.brier_score([100, 0], [1, 0]), 0.0)
        self.assertAlmostEqual(A.brier_score([0, 100], [1, 0]), 1.0)

    def test_auc_hand_value(self):
        # positives 90, 30; negatives 80, 10: pairs won = 90>80, 90>10, 30>10 = 3 of 4 = .75
        self.assertAlmostEqual(A.auc_score([90, 80, 30, 10], [1, 0, 1, 0]), 0.75)
        self.assertAlmostEqual(A.auc_score([50, 50, 50, 50], [1, 0, 1, 0]), 0.5)  # all ties
        self.assertTrue(math.isnan(A.auc_score([10, 20], [1, 1])))

    def test_calibration_summary_per_condition(self):
        outs, marks = synth(grid(uniform(6), uniform(4)))
        # confidence 90 on right claims, 10 on not-right claims in the wiki condition only
        marks = marks.merge(outs[["output_id", "condition"]], on="output_id")
        marks["confidence"] = np.where(marks["condition"] == "wiki",
                                       np.where(marks["mark"] == "right", 90, 10), 50)
        s = A.calibration_summary(outs, marks.drop(columns="condition"))
        pooled = {r["condition"]: r for r in s["pooled"]}
        self.assertAlmostEqual(pooled["wiki"]["auc"], 1.0)
        self.assertAlmostEqual(pooled["raw"]["auc"], 0.5)
        # wiki: 6 of 8 right at 90 -> .01 each; 2 of 8 not right at 10 -> .01 each; mean .01
        self.assertAlmostEqual(pooled["wiki"]["brier"], 0.01)
        # raw: confidence .5 everywhere -> .25
        self.assertAlmostEqual(pooled["raw"]["brier"], 0.25)
        d = [x for x in s["block_differences"] if x["comparison"] == "wiki - raw"]
        self.assertEqual(len(d), 6)
        self.assertAlmostEqual(d[0]["brier_diff"], 0.01 - 0.25)


class TestExclusions(unittest.TestCase):
    def test_question_excluded_and_failed_zero_or_dropped(self):
        # One cell, runs: 6/8 = .75, a failed output, an output that asked a question.
        rc = grid(uniform(6), uniform(4))
        outs, marks = synth(rc)
        wiki_p1_m1 = outs[(outs.piece == "P1") & (outs.model == M1) & (outs.condition == "wiki")]
        r2, r3 = wiki_p1_m1.iloc[1]["output_id"], wiki_p1_m1.iloc[2]["output_id"]
        outs.loc[outs.output_id == r2, "parse_status"] = "failed"
        outs.loc[outs.output_id == r3, "asked_question"] = 1
        marks = marks[~marks.output_id.isin([r2, r3])]
        acc0 = A.output_accuracy(outs, marks, "zero")
        cell = A.cell_means(acc0)
        c = cell[(cell.piece == "P1") & (cell.model == M1) & (cell.condition == "wiki")].iloc[0]
        # failed counted 0, question left out: mean of (.75, 0) = .375 over 2 runs
        self.assertAlmostEqual(c["cell_mean"], 0.375)
        self.assertEqual(c["n_runs"], 2)
        # sensitivity: without failed outputs the cell mean is .75 over 1 run
        c2 = A.cell_means(A.output_accuracy(outs, marks, "drop"))
        c2 = c2[(c2.piece == "P1") & (c2.model == M1) & (c2.condition == "wiki")].iloc[0]
        self.assertAlmostEqual(c2["cell_mean"], 0.75)
        self.assertEqual(c2["n_runs"], 1)
        # counted by condition
        ex = A.exclusion_counts(outs, marks)
        e = ex[(ex.task == 1) & (ex.condition == "wiki")].iloc[0]
        self.assertEqual(e["question"], 1)
        self.assertEqual(e["failed"], 1)

    def test_unmarked_claims_are_missing_not_zero(self):
        outs, marks = synth(grid(uniform(6), uniform(4)))
        oid = outs.iloc[0]["output_id"]  # 6 right of 8; unmark the last 2 (not right) claims
        marks.loc[(marks.output_id == oid) & marks.item_id.isin(["7", "8"]), "mark"] = None
        acc = A.output_accuracy(outs, marks)
        self.assertAlmostEqual(acc[acc.output_id == oid]["accuracy"].iloc[0], 1.0)  # 6 of 6 marked

    def test_block_with_no_usable_cell_is_dropped(self):
        outs, marks = synth(grid(uniform(6), uniform(4)))
        ids = outs[(outs.piece == "P1") & (outs.model == M1) & (outs.condition == "raw")]["output_id"]
        outs.loc[outs.output_id.isin(ids), "asked_question"] = 1
        r = A.primary_test(outs, marks, "wiki", "raw")
        self.assertEqual(r["test"]["k_blocks"], 5)
        self.assertEqual(r["blocks_dropped"], 1)
        self.assertAlmostEqual(r["test"]["p_value"], 2 / 32)


class TestOtherIndices(unittest.TestCase):
    def test_blinding_index(self):
        outs, _ = synth(grid(uniform(6), uniform(4)))
        outs = outs.iloc[:6].copy()          # six outputs
        outs["condition"] = ["wiki", "raw", "none", "wiki", "raw", "none"]
        outs["condition_guess"] = ["wiki", "raw", "wiki", "raw", "none", "none"]
        b = A.blinding_index(outs)
        self.assertEqual(b["n"], 6)
        self.assertEqual(b["n_correct"], 3)
        self.assertAlmostEqual(b["share_correct"], 0.5)
        self.assertAlmostEqual(b["difference_from_chance"], 0.5 - 1 / 3)

    def test_felt_vs_accuracy_spearman(self):
        outs, marks = synth(grid(uniform(6), uniform(4)))
        # within P1: set felt to rank accuracy exactly
        acc = A.output_accuracy(outs, marks).set_index("output_id")["accuracy"]
        outs["felt_understood"] = outs["output_id"].map(lambda i: 1 + 6 * acc[i])
        r = {x["piece"]: x for x in A.felt_vs_accuracy(outs, marks)}
        self.assertAlmostEqual(r["P1"]["spearman_rho"], 1.0)
        self.assertEqual(r["P1"]["n"], 18)

    def test_judge_agreement_uses_only_heldout(self):
        outs, marks = synth(grid(uniform(6), uniform(4)))
        marks["judge_split"] = "none"
        # 20 held-out claims: 15 agree (see kappa test above for the table)
        idx = marks.index[:20]
        marks.loc[idx, "judge_split"] = "heldout"
        a = ["right"] * 13 + ["not_right"] * 7
        b = (["right"] * 10 + ["not_right"] * 3) + (["right"] * 2 + ["not_right"] * 5)
        marks.loc[idx, "mark"] = a
        marks.loc[idx, "judge_label"] = b
        # a claim outside the held-out set with a disagreeing judge label must not count
        marks.loc[marks.index[20], ["judge_label"]] = "wrong_on_purpose"
        j = A.judge_agreement(marks)["heldout"]
        self.assertEqual(j["n"], 20)
        self.assertAlmostEqual(j["percent_agreement"], 0.75)
        self.assertAlmostEqual(j["kappa"], 0.22 / 0.47)

    def test_hindsight(self):
        _, marks = synth(grid(uniform(6), uniform(4)))
        first = marks[marks.output_id.str.contains("P1")].copy()
        delayed = first.copy()
        delayed["marking_pass"] = "delayed"
        delayed.loc[delayed.index[:10], "mark"] = np.where(delayed.loc[delayed.index[:10], "mark"] == "right",
                                                           "not_right", "right")
        first["reading_label"] = first["mark"]          # identical to first marks
        both = pd.concat([first, delayed])
        h = A.hindsight_agreement(both)
        n = len(first)
        self.assertEqual(h["first_vs_delayed"]["n"], n)
        self.assertAlmostEqual(h["first_vs_delayed"]["percent_agreement"], (n - 10) / n)
        self.assertAlmostEqual(h["first_vs_readings"]["percent_agreement"], 1.0)

    def test_reconstruction_summary(self):
        # 3 right, 1 wrong, 2 cannot tell -> share right = 3 / (3 + 1) = .75, cannot tell counted apart
        outs = pd.DataFrame([dict(output_id="T2-a", task=2, piece="R", model=M1, condition="wiki", run=1,
                                  parse_status="ok", asked_question=0),
                             dict(output_id="T2-b", task=2, piece="R", model=M1, condition="none", run=1,
                                  parse_status="failed", asked_question=0)])
        marks = pd.DataFrame([dict(output_id="T2-a", task=2, item_id=f"1.{i}", marking_pass="first", mark=m)
                              for i, m in enumerate(["right"] * 3 + ["wrong"] + ["cannot tell"] * 2)])
        s = A.recon_summary(outs, marks)["per_output"].set_index("output_id")
        self.assertAlmostEqual(s.loc["T2-a", "share_right"], 0.75)
        self.assertEqual(s.loc["T2-a", "n_cannot_tell"], 2)
        self.assertEqual(s.loc["T2-b", "status"], "failed")
        self.assertEqual(s.loc["T2-b", "share_right"], 0.0)

    def test_length_check(self):
        outs, _ = synth(grid(uniform(6), uniform(4)))
        outs.loc[outs.condition == "raw", "context_tokens"] = 1049   # +4.9%
        self.assertTrue(A.length_check(outs)["ok"].all())
        outs.loc[outs.condition == "raw", "context_tokens"] = 1060   # +6%
        self.assertFalse(A.length_check(outs)["ok"].any())

    def test_run_all_on_synthetic(self):
        outs, marks = synth(grid(uniform(6), uniform(4)))
        res = A.run_all(outs, marks)
        self.assertAlmostEqual(res["h1_wiki_vs_raw"]["test"]["p_value"], 2 / 64)
        self.assertEqual(A._jsonable(res)["blinding"]["n"], 54)


class TestMarkingOrder(unittest.TestCase):
    def setUp(self):
        self.plan = A.plan_outputs()
        self.order = A.marking_order(self.plan, seed=12345)

    def test_sizes(self):
        self.assertEqual(len(self.plan), 60)
        self.assertEqual(self.order.groupby("session").size().to_dict(), {1: 18, 2: 18, 3: 18, 4: 6})
        self.assertEqual(self.order["output_id"].nunique(), 60)

    def test_one_output_per_cell_per_session(self):
        o = self.order.merge(self.plan, on=["output_id", "task"])
        t1 = o[o.task == 1]
        for s, g in t1.groupby("session"):
            self.assertEqual(len(g.groupby(["piece", "model", "condition"])), 18)
            self.assertEqual(g.groupby(["piece", "model", "condition"]).size().max(), 1)
        # every cell's three runs are spread over the three sessions
        for _, g in t1.groupby(["piece", "model", "condition"]):
            self.assertEqual(sorted(g["session"]), [1, 2, 3])

    def test_task2_one_session(self):
        o = self.order.merge(self.plan, on=["output_id", "task"])
        self.assertEqual(set(o[o.task == 2]["session"]), {4})

    def test_deterministic_and_seed_dependent(self):
        again = A.marking_order(self.plan.sample(frac=1, random_state=3), seed=12345)
        pd.testing.assert_frame_equal(self.order.reset_index(drop=True), again.reset_index(drop=True))
        other = A.marking_order(self.plan, seed=54321)
        self.assertFalse(self.order["output_id"].equals(other["output_id"]))
        self.assertEqual(A.order_digest(self.order), A.order_digest(again))
        self.assertNotEqual(A.order_digest(self.order), A.order_digest(other))

    def test_hindsight_order_is_a_new_permutation(self):
        ids = list(self.plan[(self.plan.task == 1) & (self.plan.piece == "P1")]["output_id"])
        h = A.hindsight_order(ids, 12345)
        self.assertEqual(sorted(h), sorted(ids))
        self.assertEqual(h, A.hindsight_order(list(reversed(ids)), 12345))

    def test_blind_ids_carry_no_cell_information(self):
        self.assertTrue(self.order["blind_id"].str.fullmatch(r"S\d-\d\d").all())


class TestParsers(unittest.TestCase):
    good = '{"claims": [{"rank": 1, "claim": "a", "confidence": 70}, {"rank": 2, "claim": "b", "confidence": 5}]}'

    def test_task1(self):
        r = A.parse_task1(self.good)
        self.assertEqual(r["status"], "ok")
        self.assertEqual([c["confidence"] for c in r["claims"]], [70.0, 5.0])
        self.assertEqual(A.parse_task1("```json\n" + self.good + "\n```")["status"], "ok")
        self.assertEqual(A.parse_task1("Here are my claims: " + self.good)["reason"], "not_json")
        self.assertEqual(A.parse_task1('{"claims": []}')["reason"], "no_claims")
        nine = '{"claims": [' + ",".join(['{"claim": "x", "confidence": 1}'] * 9) + "]}"
        self.assertEqual(A.parse_task1(nine)["reason"], "too_many_claims")
        self.assertEqual(A.parse_task1('{"claims": [{"claim": "x", "confidence": 101}]}')["reason"], "bad_confidence")
        self.assertEqual(A.parse_task1('{"claims": [{"claim": " ", "confidence": 10}]}')["reason"], "bad_claim")

    def test_task2(self):
        ok = ('{"periods": [{"label": "p", "start": "1", "end": "2", '
              '"items": [{"category": "places", "statement": "s"}]}]}')
        self.assertEqual(A.parse_task2(ok)["status"], "ok")
        self.assertEqual(A.parse_task2('{"periods": []}')["reason"], "no_periods")
        bad = ok.replace("places", "food")
        self.assertEqual(A.parse_task2(bad)["reason"], "bad_item")
        many = ('{"periods": [{"label": "p", "start": "1", "end": "2", "items": ['
                + ",".join(['{"category": "other", "statement": "s"}'] * 9) + "]}]}")
        self.assertEqual(A.parse_task2(many)["reason"], "bad_items")
        empty = '{"periods": [{"label": "p", "start": "1", "end": "2", "items": []}]}'
        self.assertEqual(A.parse_task2(empty)["reason"], "no_items")


class TestFrozenFiles(unittest.TestCase):
    """Checks that the frozen prompt files extract cleanly and say what the
    registration requires."""

    def test_extraction_and_placeholders(self):
        sysp = A.extract_prompt(ROOT / "prompts" / "system.md")
        t1 = A.extract_prompt(ROOT / "prompts" / "task1_interpretation.md")
        t2 = A.extract_prompt(ROOT / "prompts" / "task2_reconstruction.md")
        self.assertEqual(A.placeholders(sysp), set())
        self.assertEqual(A.placeholders(t1), {"PIECE_TEXT", "CONTEXT_BLOCK"})
        self.assertEqual(A.placeholders(t2), {"CONTEXT_BLOCK"})
        r = A.render_prompt(t1, PIECE_TEXT="PIECE", CONTEXT_BLOCK="CTX")
        self.assertIn("<piece>\nPIECE\n</piece>", r)
        self.assertIn("<background>\nCTX\n</background>", r)
        for t in (t1, t2):
            self.assertIn("Answer even if you are unsure.", t)
        self.assertIn("exactly 8 claims", t1)
        self.assertIn("from 0 to 100", t1)
        self.assertIn("at most 8 items per period", t2)
        with self.assertRaises(ValueError):
            A.render_prompt(t1, PIECE_TEXT="x")

    def test_judge_prompt_variables(self):
        j = A.extract_prompt(ROOT / "judge" / "judge_prompt.md")
        self.assertEqual(A.placeholders(j), {"input", "output", "reference"})
        # valid as an f-string once the mustache variables are mapped: no other braces
        stripped = re.sub(r"\{\{[a-z]+\}\}", "", j)
        self.assertNotIn("{", stripped)
        self.assertNotIn("}", stripped)

    def test_no_product_names_in_frozen_files(self):
        allowed = [f"{m}" for m in A.MODELS]
        banned = re.compile("|".join(["clau" + "de", "anthro" + "pic", "open" + "ai", "g" + "pt", "gem" + "ini",
                                      "son" + "net", "chat" + "gpt"]), re.I)
        files = [p for d in ("prompts", "rubric", "judge", "schema") for p in (ROOT / d).glob("*.md")]
        files.append(ROOT / "analysis" / "analyse.py")
        for f in files:
            text = f.read_text(encoding="utf-8")
            for a in allowed:
                text = text.replace(a, "")
            if f.name == "judge_prompt.md":
                text = text.replace("openevals", "")   # an open-source package name, not a model
            self.assertIsNone(banned.search(text), f"product or model name in {f.name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

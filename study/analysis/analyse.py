"""Analysis code for the preregistered single-case study.

Dependencies: numpy, pandas, scipy, and the standard library only.

Every index and test named in the registration is implemented here:

* output accuracy and cell means (Task 1);
* the exact sign-flip permutation test over all 2**k label swaps (k blocks);
* the effect report (block differences, their mean and range) and the
  per-piece description;
* Brier score and AUC of stated confidence (Q4, no test);
* Spearman correlation of felt-understood rating with accuracy (Q5, no test);
* the reconstruction summary (H3, descriptive);
* blinding index, Cohen's kappa and percentage agreement;
* judge agreement on held-out claims and the hindsight agreements;
* the question-instead-of-answer exclusion and the failure rule;
* the seeded marking-order randomisation.

Command line:

    python analyse.py order --seed 20261123 --out marking_order.csv
    python analyse.py run --outputs outputs.csv --marks marks.csv --out results.json

Column definitions are in schema/outputs.schema.md.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# --------------------------------------------------------------------------
# Constants fixed by the registration
# --------------------------------------------------------------------------
CONDITIONS = ("none", "raw", "wiki")
PIECES = ("P1", "P2", "P3")
MODELS = ("anthropic/claude-sonnet-5.5", "openai/gpt-5.5")
RUNS_TASK1 = 3
RUNS_TASK2 = 1
MAX_CLAIMS = 8
MAX_ITEMS_PER_PERIOD = 8
N_SESSIONS_TASK1 = 3
TOKEN_TOLERANCE = 0.05
TOL = 1e-12

# The seed is fixed here before generation. It is recorded in the repository
# so that the marking order can be reproduced and checked.
MARKING_SEED = 20261123

TASK1_MARKS = {"right": 1.0, "not_right": 0.0}
TASK2_MARKS = ("right", "wrong", "cannot_tell")


def _norm_mark(x):
    """Normalise a mark string; return None for missing."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    s = str(x).strip().lower().replace(" ", "_").replace("-", "_")
    return s or None


# --------------------------------------------------------------------------
# Plan, prompts and parsers (used by the generation step)
# --------------------------------------------------------------------------
def plan_outputs(pieces=PIECES, models=MODELS, conditions=CONDITIONS,
                 runs_task1=RUNS_TASK1, runs_task2=RUNS_TASK2) -> pd.DataFrame:
    """Planned outputs: 3 x 3 x 2 x 3 = 54 for Task 1 and 3 x 2 x 1 = 6 for Task 2."""
    rows = []
    for p in pieces:
        for m in models:
            for c in conditions:
                for r in range(1, runs_task1 + 1):
                    rows.append(dict(output_id=f"T1-{p}-{_mid(m, models)}-{c}-r{r}",
                                     task=1, piece=p, model=m, condition=c, run=r))
    for m in models:
        for c in conditions:
            for r in range(1, runs_task2 + 1):
                rows.append(dict(output_id=f"T2-R-{_mid(m, models)}-{c}-r{r}",
                                 task=2, piece="R", model=m, condition=c, run=r))
    return pd.DataFrame(rows)


def _mid(model, models):
    return f"M{list(models).index(model) + 1}" if model in models else re.sub(r"\W+", "", model)


def extract_prompt(path) -> str:
    """Return the prompt text between the PROMPT START / PROMPT END markers.

    The fenced block inside the markers is unwrapped; the fence lines are not
    part of the prompt. Fence length may be three or four backticks.
    """
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->\s*\n(.*?)\n<!-- PROMPT END -->", text, re.S)
    if not m:
        raise ValueError(f"no prompt markers in {path}")
    block = m.group(1)
    f = re.match(r"^(`{3,})[^\n]*\n(.*)\n\1\s*$", block, re.S)
    if not f:
        raise ValueError(f"no fenced block between the markers in {path}")
    return f.group(2)


def placeholders(template: str, pattern: str = r"\{\{([A-Za-z_]+)\}\}") -> set:
    return set(re.findall(pattern, template))


def render_prompt(template: str, **values) -> str:
    """Single-pass substitution of {{NAME}} placeholders. Every placeholder in
    the template must be given and every given value must be used."""
    need = placeholders(template)
    if need != set(values):
        raise ValueError(f"placeholders {sorted(need)} do not match values {sorted(values)}")
    return re.sub(r"\{\{([A-Za-z_]+)\}\}", lambda m: str(values[m.group(1)]), template)


def _unfence(text: str) -> str:
    t = text.strip()
    f = re.match(r"^```(?:json)?\s*\n(.*)\n```$", t, re.S)
    return f.group(1).strip() if f else t


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def parse_task1(text: str) -> dict:
    """Validate a Task 1 reply. Returns dict(status, reason, claims).

    status is 'ok' or 'failed'. reason is '' when ok, else one of
    'not_json', 'no_claims', 'too_many_claims', 'bad_claim', 'bad_confidence'.
    """
    try:
        obj = json.loads(_unfence(text))
    except (ValueError, TypeError):
        return dict(status="failed", reason="not_json", claims=[])
    claims = obj.get("claims") if isinstance(obj, dict) else None
    if not isinstance(claims, list):
        return dict(status="failed", reason="not_json", claims=[])
    if len(claims) == 0:
        return dict(status="failed", reason="no_claims", claims=[])
    if len(claims) > MAX_CLAIMS:
        return dict(status="failed", reason="too_many_claims", claims=[])
    out = []
    for c in claims:
        if not isinstance(c, dict) or not isinstance(c.get("claim"), str) or not c["claim"].strip():
            return dict(status="failed", reason="bad_claim", claims=[])
        if not _is_num(c.get("confidence")) or not 0 <= c["confidence"] <= 100:
            return dict(status="failed", reason="bad_confidence", claims=[])
        out.append(dict(claim=c["claim"].strip(), confidence=float(c["confidence"])))
    return dict(status="ok", reason="", claims=out)


def parse_task2(text: str) -> dict:
    """Validate a Task 2 reply. Returns dict(status, reason, periods)."""
    try:
        obj = json.loads(_unfence(text))
    except (ValueError, TypeError):
        return dict(status="failed", reason="not_json", periods=[])
    periods = obj.get("periods") if isinstance(obj, dict) else None
    if not isinstance(periods, list) or not periods:
        return dict(status="failed", reason="no_periods", periods=[])
    cats = {"people", "places", "music", "other"}
    out, total = [], 0
    for p in periods:
        if not isinstance(p, dict) or not all(isinstance(p.get(k), str) for k in ("label", "start", "end")):
            return dict(status="failed", reason="bad_period", periods=[])
        items = p.get("items")
        if not isinstance(items, list) or len(items) > MAX_ITEMS_PER_PERIOD:
            return dict(status="failed", reason="bad_items", periods=[])
        clean = []
        for it in items:
            if (not isinstance(it, dict) or it.get("category") not in cats
                    or not isinstance(it.get("statement"), str) or not it["statement"].strip()):
                return dict(status="failed", reason="bad_item", periods=[])
            clean.append(dict(category=it["category"], statement=it["statement"].strip()))
        total += len(clean)
        out.append(dict(label=p["label"], start=p["start"], end=p["end"], items=clean))
    if total == 0:
        return dict(status="failed", reason="no_items", periods=[])
    return dict(status="ok", reason="", periods=out)


# --------------------------------------------------------------------------
# Seeded marking-order randomisation
# --------------------------------------------------------------------------
def _shuffle(seq, rng: random.Random) -> list:
    """Fisher-Yates shuffle using randrange, so the result depends only on the
    seed and the (sorted) input."""
    a = list(seq)
    for i in range(len(a) - 1, 0, -1):
        j = rng.randrange(i + 1)
        a[i], a[j] = a[j], a[i]
    return a


def marking_order(outputs: pd.DataFrame, seed: int = MARKING_SEED) -> pd.DataFrame:
    """Marking order for the first marking.

    Task 1: three sessions of 18. Each session holds exactly one output from
    every piece x model x condition cell. Which run goes to which session is
    a seeded permutation within each cell; the order within a session is a
    seeded permutation. Task 2: one session (numbered 4) in seeded random
    order. Returns output_id, task, session, position, blind_id.
    """
    rng = random.Random(seed)
    o = outputs.sort_values(["task", "piece", "model", "condition", "run"]).reset_index(drop=True)
    t1 = o[o["task"] == 1]
    sessions = {s: [] for s in range(1, N_SESSIONS_TASK1 + 1)}
    for _, cell in t1.groupby(["piece", "model", "condition"], sort=True):
        ids = list(cell["output_id"])
        if len(ids) != N_SESSIONS_TASK1:
            raise ValueError("each Task 1 cell must hold exactly 3 outputs")
        for s, oid in zip(range(1, N_SESSIONS_TASK1 + 1), _shuffle(ids, rng)):
            sessions[s].append(oid)
    rows = []
    for s in sorted(sessions):
        for pos, oid in enumerate(_shuffle(sessions[s], rng), start=1):
            rows.append(dict(output_id=oid, task=1, session=s, position=pos,
                             blind_id=f"S{s}-{pos:02d}"))
    t2 = list(o[o["task"] == 2]["output_id"])
    s2 = N_SESSIONS_TASK1 + 1
    for pos, oid in enumerate(_shuffle(t2, rng), start=1):
        rows.append(dict(output_id=oid, task=2, session=s2, position=pos,
                         blind_id=f"S{s2}-{pos:02d}"))
    return pd.DataFrame(rows)


def hindsight_order(output_ids, seed: int = MARKING_SEED) -> list:
    """New random order for the delayed re-marking of one piece's outputs."""
    return _shuffle(sorted(output_ids), random.Random(seed + 1))


def order_digest(order: pd.DataFrame) -> str:
    """SHA-256 of the order table in a canonical form, for the record."""
    s = order.sort_values(["session", "position"]).to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Agreement statistics
# --------------------------------------------------------------------------
def percent_agreement(a, b) -> float:
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None
             and not (isinstance(x, float) and math.isnan(x)) and not (isinstance(y, float) and math.isnan(y))]
    if not pairs:
        return float("nan")
    return sum(x == y for x, y in pairs) / len(pairs)


def cohen_kappa(a, b) -> float:
    """Cohen's kappa for two raters over the same items (unweighted).
    Pairs with a missing value are dropped. Undefined (nan) if chance
    agreement is 1."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None
             and not (isinstance(x, float) and math.isnan(x)) and not (isinstance(y, float) and math.isnan(y))]
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in pairs) / n
    cats = {x for x, _ in pairs} | {y for _, y in pairs}
    pe = sum((sum(x == c for x, _ in pairs) / n) * (sum(y == c for _, y in pairs) / n) for c in cats)
    if abs(1 - pe) < TOL:
        return float("nan")
    return (po - pe) / (1 - pe)


# --------------------------------------------------------------------------
# Confidence indices
# --------------------------------------------------------------------------
def brier_score(confidence, score) -> float:
    """Mean squared difference between confidence/100 and the claim score."""
    c = np.asarray(confidence, dtype=float) / 100.0
    y = np.asarray(score, dtype=float)
    if c.size == 0:
        return float("nan")
    return float(np.mean((c - y) ** 2))


def auc_score(confidence, score) -> float:
    """Area under the ROC curve of confidence for separating right (1) from
    not right (0); ties count one half. nan if either class is empty."""
    c = np.asarray(confidence, dtype=float)
    y = np.asarray(score, dtype=float)
    npos, nneg = int((y == 1).sum()), int((y == 0).sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    ranks = stats.rankdata(c)
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg))


# --------------------------------------------------------------------------
# Task 1: output accuracy, cell means, the sign-flip test
# --------------------------------------------------------------------------
def _prep_marks(marks: pd.DataFrame) -> pd.DataFrame:
    m = marks.copy()
    m["mark"] = m["mark"].map(_norm_mark)
    if "judge_label" in m:
        m["judge_label"] = m["judge_label"].map(_norm_mark)
    if "reading_label" in m:
        m["reading_label"] = m["reading_label"].map(_norm_mark)
    m["item_id"] = m["item_id"].astype(str)
    return m


def output_accuracy(outputs: pd.DataFrame, marks: pd.DataFrame, failures: str = "zero") -> pd.DataFrame:
    """Output accuracy for each Task 1 output (first marking).

    status:
      'question'  asked a question instead of answering: excluded (nan);
      'failed'    refusal, no claims or format failure after one retry: accuracy
                  0 if failures == 'zero' (the registered rule), nan if 'drop'
                  (the sensitivity analysis);
      'unmarked'  no claim marked: missing (nan);
      'ok'        mean claim score over the claims marked right / not right.
    Unmarked claims are missing and excluded from the output's mean.
    """
    if failures not in ("zero", "drop"):
        raise ValueError("failures must be 'zero' or 'drop'")
    o = outputs[outputs["task"] == 1].copy()
    m = _prep_marks(marks)
    m = m[(m["task"] == 1) & (m["marking_pass"] == "first") & m["mark"].isin(TASK1_MARKS)]
    g = m.groupby("output_id")["mark"].agg(n_marked="size", n_right=lambda s: int((s == "right").sum()))
    o = o.merge(g, left_on="output_id", right_index=True, how="left")
    o["n_marked"] = o["n_marked"].fillna(0).astype(int)
    o["n_right"] = o["n_right"].fillna(0).astype(int)
    asked = o["asked_question"].fillna(0).astype(float) == 1
    failed = o["parse_status"].astype(str) == "failed"
    status = np.where(asked, "question",
             np.where(failed, "failed",
             np.where(o["n_marked"] == 0, "unmarked", "ok")))
    acc = np.where(status == "ok", o["n_right"] / o["n_marked"].where(o["n_marked"] > 0, np.nan), np.nan)
    if failures == "zero":
        acc = np.where(status == "failed", 0.0, acc)
    o["status"] = status
    o["accuracy"] = acc.astype(float)
    o["block"] = o["piece"] + "|" + o["model"]
    return o[["output_id", "piece", "model", "block", "condition", "run", "status",
              "n_marked", "n_right", "accuracy"]]


def cell_means(acc: pd.DataFrame) -> pd.DataFrame:
    """Cell mean = mean output accuracy over the runs in a piece x model x
    condition cell (nan runs are left out; n_runs counts those used)."""
    g = acc.groupby(["piece", "model", "block", "condition"], sort=True)["accuracy"]
    out = g.agg(cell_mean="mean", n_runs=lambda s: int(s.notna().sum())).reset_index()
    return out


def block_differences(cells: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Per-block difference cell_mean[a] - cell_mean[b]. A block missing either
    cell (no usable run) is dropped from the table and reported in 'dropped'."""
    w = cells.groupby(["piece", "model", "block", "condition"])["cell_mean"].first().unstack("condition")
    for c in (a, b):
        if c not in w:
            w[c] = np.nan
    d = pd.DataFrame({"mean_a": w[a], "mean_b": w[b]}).reset_index()
    d["diff"] = d["mean_a"] - d["mean_b"]
    return d


def sign_flip_test(diffs) -> dict:
    """Exact sign-flip permutation test on block differences.

    The two condition labels are swapped within each block in all 2**k ways,
    which flips the sign of that block's difference. The statistic is the mean
    over blocks of the difference. The two-sided p is the share of the 2**k
    swaps whose statistic is at least as extreme (in absolute value) as the
    observed one. The observed labelling is one of the swaps.
    """
    d = np.asarray(diffs, dtype=float)
    k = d.size
    if k == 0:
        return dict(k_blocks=0, observed=float("nan"), n_swaps=0, n_extreme=0, p_value=float("nan"))
    signs = np.array(list(itertools.product((1.0, -1.0), repeat=k)))
    perm = signs @ d / k
    obs = float(d.mean())
    n_extreme = int((np.abs(perm) >= abs(obs) - TOL).sum())
    return dict(k_blocks=k, observed=obs, n_swaps=int(2 ** k), n_extreme=n_extreme,
                p_value=n_extreme / 2 ** k)


def primary_test(outputs: pd.DataFrame, marks: pd.DataFrame, a: str = "wiki", b: str = "raw",
                 failures: str = "zero") -> dict:
    """H1 (a='wiki', b='raw') or H2 (a='wiki', b='none').

    Returns the exact test, the effect report (six block differences, their
    mean and range), the per-piece description, and the number of pieces in
    which the mean over both models of condition a exceeds that of condition b.
    """
    acc = output_accuracy(outputs, marks, failures)
    cells = cell_means(acc)
    bd = block_differences(cells, a, b)
    usable = bd.dropna(subset=["diff"])
    test = sign_flip_test(usable["diff"].values)
    # per piece: mean over models of the cell means, then compare
    pc = cells.groupby(["piece", "condition"])["cell_mean"].mean().unstack()
    per_piece = pd.DataFrame({"mean_a": pc.get(a), "mean_b": pc.get(b)})
    per_piece["diff"] = per_piece["mean_a"] - per_piece["mean_b"]
    n_higher = int((per_piece["diff"] > 0).sum())
    return dict(
        comparison=f"{a} vs {b}", failures=failures, test=test,
        blocks=usable.to_dict("records"),
        blocks_dropped=int(len(bd) - len(usable)),
        effect=dict(mean=test["observed"],
                    min=float(usable["diff"].min()) if len(usable) else float("nan"),
                    max=float(usable["diff"].max()) if len(usable) else float("nan")),
        per_piece=per_piece.reset_index().to_dict("records"),
        pieces_a_higher=n_higher, n_pieces=int(per_piece["diff"].notna().sum()),
    )


def exclusion_counts(outputs: pd.DataFrame, marks: pd.DataFrame) -> pd.DataFrame:
    """Counts by task and condition of outputs by status (question, failed,
    unmarked, ok). Task 2 uses the same rules."""
    t1 = output_accuracy(outputs, marks, "zero")[["output_id", "condition", "status"]]
    t1["task"] = 1
    t2 = recon_summary(outputs, marks)["per_output"][["output_id", "condition", "status"]]
    t2["task"] = 2
    al = pd.concat([t1, t2])
    return al.groupby(["task", "condition", "status"]).size().unstack(fill_value=0).reset_index()


# --------------------------------------------------------------------------
# Q4: calibration
# --------------------------------------------------------------------------
def claims_frame(outputs: pd.DataFrame, marks: pd.DataFrame) -> pd.DataFrame:
    """Marked Task 1 claims from the first marking with confidence."""
    m = _prep_marks(marks)
    m = m[(m["task"] == 1) & (m["marking_pass"] == "first") & m["mark"].isin(TASK1_MARKS)].copy()
    m["score"] = m["mark"].map(TASK1_MARKS)
    keep = outputs[["output_id", "piece", "model", "condition"]]
    c = m.merge(keep, on="output_id", how="inner")
    c = c[c["confidence"].notna()].copy()
    c["block"] = c["piece"] + "|" + c["model"]
    return c


def calibration_summary(outputs: pd.DataFrame, marks: pd.DataFrame) -> dict:
    """Brier score and AUC per condition (pooled) and per block x condition,
    plus per-block differences wiki - raw and wiki - none. No test."""
    c = claims_frame(outputs, marks)

    def stat(df):
        return pd.Series(dict(n=len(df), brier=brier_score(df["confidence"], df["score"]),
                              auc=auc_score(df["confidence"], df["score"])))

    pooled = c.groupby("condition").apply(stat, include_groups=False).reset_index()
    perblock = c.groupby(["piece", "model", "block", "condition"]).apply(stat, include_groups=False).reset_index()
    diffs = []
    for other in ("raw", "none"):
        for (pc, md, bl), g in perblock.groupby(["piece", "model", "block"]):
            w = g[g["condition"] == "wiki"]
            o = g[g["condition"] == other]
            if len(w) and len(o):
                diffs.append(dict(piece=pc, model=md, block=bl, comparison=f"wiki - {other}",
                                  brier_diff=float(w["brier"].iloc[0] - o["brier"].iloc[0]),
                                  auc_diff=float(w["auc"].iloc[0] - o["auc"].iloc[0])))
    return dict(pooled=pooled.to_dict("records"), per_block=perblock.to_dict("records"),
                block_differences=diffs)


# --------------------------------------------------------------------------
# Q5: felt understood vs accuracy
# --------------------------------------------------------------------------
def felt_vs_accuracy(outputs: pd.DataFrame, marks: pd.DataFrame, failures: str = "zero") -> list:
    """Spearman rank correlation of felt-understood rating with output
    accuracy, within each piece. No test: rho and n only."""
    acc = output_accuracy(outputs, marks, failures)
    d = acc.merge(outputs[["output_id", "felt_understood"]], on="output_id")
    d = d.dropna(subset=["accuracy", "felt_understood"])
    res = []
    for piece, g in d.groupby("piece"):
        if len(g) < 3 or g["felt_understood"].nunique() < 2 or g["accuracy"].nunique() < 2:
            rho = float("nan")
        else:
            rho = float(stats.spearmanr(g["felt_understood"], g["accuracy"]).statistic)
        res.append(dict(piece=piece, n=len(g), spearman_rho=rho))
    return res


# --------------------------------------------------------------------------
# H3: reconstruction (descriptive)
# --------------------------------------------------------------------------
def recon_summary(outputs: pd.DataFrame, marks: pd.DataFrame) -> dict:
    """Share of items marked right per output, out of right + wrong; cannot
    tell counted separately. A failed output scores share 0 and is counted;
    an output that asked a question is left out. No test."""
    o = outputs[outputs["task"] == 2].copy()
    m = _prep_marks(marks)
    m = m[(m["task"] == 2) & (m["marking_pass"] == "first") & m["mark"].isin(TASK2_MARKS)]
    cnt = m.groupby(["output_id", "mark"]).size().unstack(fill_value=0)
    for c in TASK2_MARKS:
        if c not in cnt:
            cnt[c] = 0
    o = o.merge(cnt[list(TASK2_MARKS)], left_on="output_id", right_index=True, how="left")
    for c in TASK2_MARKS:
        o[c] = o[c].fillna(0).astype(int)
    o = o.rename(columns={"right": "n_right", "wrong": "n_wrong", "cannot_tell": "n_cannot_tell"})
    asked = o["asked_question"].fillna(0).astype(float) == 1
    failed = o["parse_status"].astype(str) == "failed"
    judged = o["n_right"] + o["n_wrong"]
    o["status"] = np.where(asked, "question", np.where(failed, "failed",
                  np.where(judged == 0, "unmarked", "ok")))
    share = np.where(o["status"] == "ok", o["n_right"] / judged.where(judged > 0, np.nan), np.nan)
    o["share_right"] = np.where(o["status"] == "failed", 0.0, share).astype(float)
    cols = ["output_id", "model", "condition", "status", "n_right", "n_wrong", "n_cannot_tell", "share_right"]
    by_c = o.groupby("condition").agg(
        n_outputs=("output_id", "size"), items_right=("n_right", "sum"), items_wrong=("n_wrong", "sum"),
        items_cannot_tell=("n_cannot_tell", "sum"), mean_share_right=("share_right", "mean")).reset_index()
    return dict(per_output=o[cols], by_condition=by_c)


# --------------------------------------------------------------------------
# Blinding, judge, hindsight
# --------------------------------------------------------------------------
def blinding_index(outputs: pd.DataFrame) -> dict:
    """Share of outputs whose condition was guessed correctly, against the
    chance rate of one third. Outputs without a guess are not counted."""
    g = outputs.dropna(subset=["condition_guess"]).copy()
    g["guess"] = g["condition_guess"].map(_norm_mark)
    g = g[g["guess"].isin(CONDITIONS)]
    n = len(g)
    correct = int((g["guess"] == g["condition"]).sum())
    by_cond = {c: dict(n=int((g["condition"] == c).sum()),
                       correct=int(((g["condition"] == c) & (g["guess"] == c)).sum()))
               for c in CONDITIONS}
    conf = pd.crosstab(g["condition"], g["guess"]).reindex(index=CONDITIONS, columns=CONDITIONS, fill_value=0)
    return dict(n=n, n_correct=correct, share_correct=correct / n if n else float("nan"),
                chance=1 / 3, difference_from_chance=(correct / n - 1 / 3) if n else float("nan"),
                by_condition=by_cond, confusion=conf.to_dict())


def _binary(series: pd.Series):
    return [None if v is None else v for v in series.map(_norm_mark)]


def judge_agreement(marks: pd.DataFrame) -> dict:
    """Agreement between the judge and the marker on held-out claims only
    (first marking, Task 1), with a check on the calibration set."""
    m = _prep_marks(marks)
    m = m[(m["task"] == 1) & (m["marking_pass"] == "first") & m["mark"].isin(TASK1_MARKS)]
    cal = m[m["judge_split"] == "calibration"]
    n_r, n_nr = int((cal["mark"] == "right").sum()), int((cal["mark"] == "not_right").sum())
    held = m[(m["judge_split"] == "heldout") & m["judge_label"].isin(TASK1_MARKS)]
    return dict(
        calibration=dict(n=len(cal), n_right=n_r, n_not_right=n_nr, at_least_20=len(cal) >= 20,
                         balanced=(len(cal) > 0 and n_r == n_nr)),
        heldout=dict(n=len(held),
                     percent_agreement=percent_agreement(list(held["mark"]), list(held["judge_label"])),
                     kappa=cohen_kappa(list(held["mark"]), list(held["judge_label"]))))


def hindsight_agreement(marks: pd.DataFrame) -> dict:
    """Agreement (percentage and kappa) between the first and the delayed
    marks, and between the first marks and the reading-based labels."""
    m = _prep_marks(marks)
    m = m[(m["task"] == 1) & m["mark"].isin(TASK1_MARKS)]
    first = m[m["marking_pass"] == "first"].set_index(["output_id", "item_id"])
    delayed = m[m["marking_pass"] == "delayed"].set_index(["output_id", "item_id"])
    j = first[["mark"]].join(delayed[["mark"]], how="inner", lsuffix="_first", rsuffix="_delayed")
    out = dict(first_vs_delayed=dict(
        n=len(j), percent_agreement=percent_agreement(list(j["mark_first"]), list(j["mark_delayed"])),
        kappa=cohen_kappa(list(j["mark_first"]), list(j["mark_delayed"]))))
    if "reading_label" in first:
        r = first[first["reading_label"].isin(TASK1_MARKS)]
        out["first_vs_readings"] = dict(
            n=len(r), percent_agreement=percent_agreement(list(r["mark"]), list(r["reading_label"])),
            kappa=cohen_kappa(list(r["mark"]), list(r["reading_label"])))
    return out


# --------------------------------------------------------------------------
# Context-length check (equal length counts context tokens only)
# --------------------------------------------------------------------------
def length_check(outputs: pd.DataFrame, tol: float = TOKEN_TOLERANCE) -> pd.DataFrame:
    """For each task and piece, the raw-text context length against the wiki's.
    ok is True when it is within tol (5%) of the wiki's token count."""
    o = outputs[outputs["condition"].isin(["raw", "wiki"])]
    t = o.groupby(["task", "piece", "condition"])["context_tokens"].mean().unstack()
    t["ratio_raw_to_wiki"] = t["raw"] / t["wiki"]
    t["ok"] = (t["ratio_raw_to_wiki"] - 1).abs() <= tol + TOL
    return t.reset_index()


# --------------------------------------------------------------------------
# Everything
# --------------------------------------------------------------------------
def run_all(outputs: pd.DataFrame, marks: pd.DataFrame) -> dict:
    return dict(
        h1_wiki_vs_raw=primary_test(outputs, marks, "wiki", "raw", "zero"),
        h2_wiki_vs_none=primary_test(outputs, marks, "wiki", "none", "zero"),
        sensitivity_h1_without_failed=primary_test(outputs, marks, "wiki", "raw", "drop"),
        sensitivity_h2_without_failed=primary_test(outputs, marks, "wiki", "none", "drop"),
        h3_reconstruction=recon_summary(outputs, marks),
        q4_calibration=calibration_summary(outputs, marks),
        q5_felt_vs_accuracy=felt_vs_accuracy(outputs, marks),
        blinding=blinding_index(outputs),
        judge=judge_agreement(marks),
        hindsight=hindsight_agreement(marks),
        exclusions=exclusion_counts(outputs, marks),
        length_check=length_check(outputs),
    )


def _jsonable(x):
    if isinstance(x, pd.DataFrame):
        return _jsonable(x.to_dict("records"))
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("order", help="write the seeded marking order for the planned outputs")
    o.add_argument("--seed", type=int, default=MARKING_SEED)
    o.add_argument("--out", required=True)
    r = sub.add_parser("run", help="compute every index and test")
    r.add_argument("--outputs", required=True)
    r.add_argument("--marks", required=True)
    r.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "order":
        order = marking_order(plan_outputs(), a.seed)
        order.to_csv(a.out, index=False)
        print(f"seed {a.seed}; order digest {order_digest(order)}")
        return 0
    outputs = pd.read_csv(a.outputs)
    marks = pd.read_csv(a.marks)
    res = _jsonable(run_all(outputs, marks))
    Path(a.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

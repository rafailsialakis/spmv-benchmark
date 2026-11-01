"""Checks of the paper analysis on a hand-made dataset with known answers."""

import numpy as np
import pandas as pd
import pytest

from utils.analysis import paper

COLS = ["matrix", "category", "reordering", "threads", "gflops", "time_ms", "rep", "pos"]


def write(tmp, plat, times, pre, reps=3, outlier=None):
    """times: {matrix: {candidate: ms}}; pre: {matrix: {method: seconds}}."""
    d = tmp / paper.PLATFORMS[plat]
    d.mkdir(parents=True)
    rows = []
    for m, tm in times.items():
        for rep in range(reps):
            for pos, c in enumerate(paper.CANDIDATES):
                t = tm[c]
                if outlier and outlier == (m, c, rep):
                    t *= 100.0                   # one wild repetition
                rows.append([m, "T", c, 4, 1.0 / t, t, rep, pos])
    pd.DataFrame(rows, columns=COLS).to_csv(d / "ios.csv", index=False)
    pd.DataFrame([[m, k, v, 0.0] for m, p in pre.items() for k, v in p.items()],
                 columns=["matrix", "reordering", "order_s", "apply_s"]).to_csv(d / "reorder_times.csv", index=False)


T_X86 = {"A": dict(none=1.0, rcm=1.2, amd=1.3, nd=1.4, gp=1.5),     # x86: keep the original order
         "B": dict(none=2.0, rcm=1.0, amd=1.5, nd=1.6, gp=1.7)}
T_ARM = {"A": dict(none=2.0, rcm=1.0, amd=1.9, nd=1.9, gp=1.9),     # ARM: RCM halves the time
         "B": dict(none=2.0, rcm=1.0, amd=1.5, nd=1.6, gp=1.7)}
PRE = {m: dict(rcm=0.1, amd=0.2, nd=0.3, gp=0.4) for m in ("A", "B")}


@pytest.fixture()
def results(tmp_path):
    write(tmp_path, "x86", T_X86, PRE, outlier=("B", "rcm", 1))
    write(tmp_path, "arm", T_ARM, PRE)
    return tmp_path


def test_known_answers(results, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    nums, tables = paper.run(results_dir=results, threads_list=(4,), make_plots=False)
    v = {k: x for k, (x, _) in nums.values.items()}
    sel = tables["selection_x86toarm_t4"]
    # A: x86 picks none, on ARM that gives 1.0/2.0 of the best
    assert sel.loc["A", "best_src"] == "none" and sel.loc["A", "best_tgt"] == "rcm"
    assert sel.loc["A", "portability"] == pytest.approx(0.5)
    # B: the outlier repetition (100x) must not change the median-based choice
    assert sel.loc["B", "best_src"] == "rcm"
    assert v["x86toarm.t4.kernel.exact"] == pytest.approx(0.5)
    assert v["x86toarm.t4.kernel.worst"] == pytest.approx(0.5)
    assert v["x86toarm.t4.kernel.srcnone.count"] == 1
    # break-even on ARM, matrix A, RCM: 0.1 s / (1 ms saved per call) = 100 calls
    be = tables["breakeven_arm_t4"]
    assert be.loc["A", "rcm"] == pytest.approx(100.0)
    assert np.isinf(tables["breakeven_x86_t4"].loc["A", "rcm"])   # slower on x86: never amortized
    assert v["x86.t4.rcm.never"] == pytest.approx(0.5)
    # cost-aware: at K = 100 on ARM, matrix A: rcm 0.1 + 0.1 = 0.2 s vs none 0.2 s (tie), amd 0.39 s
    assert v["arm.reps"] == 3


def test_mean_would_have_failed(results):
    # Failure control for the outlier check above: with a mean over repetitions
    # the 100x repetition makes RCM look slower than the original on B.
    raw = pd.read_csv(results / "x86_results" / "ios.csv")
    mean = raw.groupby(["matrix", "reordering"]).time_ms.mean().unstack()
    assert mean.loc["B"].idxmin() != "rcm"

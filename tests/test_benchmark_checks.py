"""End-to-end checks of the benchmark binary and of its safety checks.

Each check that guards a result has a failure control: an input that must make
it fail for the reason it tests. Requires `make all` (bin/spmv-benchmark).
"""

import csv
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests import mtx_fixtures as fx

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN = REPO_ROOT / "bin" / "spmv-benchmark"
PLATFORM_DIR = "x86_results" if os.uname().machine == "x86_64" else "arm_results"

pytestmark = pytest.mark.skipif(not BIN.exists(), reason="run `make all` first")


def run_bin(workdir: Path, matrix: str, reps=2, extra_env=None, timeout=120):
    env = dict(os.environ, SPMV_REPS=str(reps), OMP_PROC_BIND="false")
    env.pop("OMP_PLACES", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run([str(BIN), matrix], cwd=workdir, env=env,
                          capture_output=True, text=True, timeout=timeout)


def read_rows(workdir: Path, name: str):
    with open(workdir / "results" / PLATFORM_DIR / name, newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture()
def workdir(tmp_path):
    (tmp_path / "matrices" / "Test").mkdir(parents=True)
    return tmp_path


def test_symmetric_long_name_and_repetitions(workdir):
    n, entries = fx.laplacian_2d(30)
    fx.write_symmetric(workdir / "matrices/Test/lap.mtx", n, entries)
    res = run_bin(workdir, "Test/lap.mtx", reps=3)
    assert res.returncode == 0, res.stderr
    assert "All tests passed!" in res.stdout
    # the 40+ character name is printed intact (was a 16-byte buffer)
    assert "Matrix: SomeLongGroupName/a_matrix_name_longer_than_16" in res.stdout

    for name in ("rax.csv", "ios.csv", "cold.csv"):
        rows = read_rows(workdir, name)
        assert len(rows) == 3 * 3 * 5
        orders = set()
        for rep in range(3):
            for t in (1, 2, 4):
                block = [r for r in rows if int(r["rep"]) == rep and int(r["threads"]) == t]
                assert sorted(r["reordering"] for r in block) == sorted(["none", "rcm", "amd", "nd", "gp"])
                assert sorted(int(r["pos"]) for r in block) == [0, 1, 2, 3, 4]
                orders.add(tuple(r["reordering"] for r in sorted(block, key=lambda r: int(r["pos"]))))
        assert len(orders) > 1, "the reordering order was never shuffled"
        # six decimals are written (was three)
        assert all(len(r["time_ms"].split(".")[1]) == 6 for r in rows)
    assert all(int(r["nonnormal"]) == 0 for r in read_rows(workdir, "ios.csv"))

    times = read_rows(workdir, "reorder_times.csv")
    assert [r["reordering"] for r in times] == ["rcm", "amd", "nd", "gp"]
    assert all(float(r["order_s"]) >= 0 and float(r["apply_s"]) > 0 for r in times)

    metrics = read_rows(workdir, "metrics.csv")
    assert int(metrics[0]["nnz"]) == len(entries)   # symmetric expansion is complete


def test_same_seed_same_order(workdir):
    n, entries = fx.laplacian_2d(12)
    fx.write_symmetric(workdir / "matrices/Test/lap.mtx", n, entries)
    orders = []
    for _ in range(2):
        shutil.rmtree(workdir / "results", ignore_errors=True)
        assert run_bin(workdir, "Test/lap.mtx", reps=2).returncode == 0
        orders.append([(r["rep"], r["threads"], r["pos"], r["reordering"]) for r in read_rows(workdir, "rax.csv")])
    assert orders[0] == orders[1]


def test_unsorted_general_input(workdir):
    n, entries = fx.laplacian_2d(20)
    fx.write_general_shuffled(workdir / "matrices/Test/shuf.mtx", n, entries)
    res = run_bin(workdir, "Test/shuf.mtx", reps=1)
    assert res.returncode == 0, res.stderr
    assert "All tests passed!" in res.stdout


def scan_row(workdir):
    rows = read_rows(workdir, "ios_scan.csv")
    assert len(rows) == 1
    return rows[0]


def test_ios_scan_clean_matrix(workdir):
    n, entries = fx.laplacian_2d(10)
    fx.write_symmetric(workdir / "matrices/Test/lap.mtx", n, entries)
    res = run_bin(workdir, "Test/lap.mtx", reps=1)
    assert res.returncode == 0, res.stderr
    assert "WARNING IOS" not in res.stderr
    assert int(scan_row(workdir)["iters_with_nonnormal"]) == 0


def test_ios_overflow_is_flagged(workdir):
    # Failure control: entries ~1e5 grow by ~1e5 per iteration and overflow to inf.
    n, entries = fx.laplacian_2d(10)
    fx.write_symmetric(workdir / "matrices/Test/big.mtx", n, entries, scale=1e5, positive=True)
    res = run_bin(workdir, "Test/big.mtx", reps=1)
    assert res.returncode == 0, res.stderr
    assert int(scan_row(workdir)["iters_with_nonnormal"]) > 0
    assert any(int(r["nonnormal"]) > 0 for r in read_rows(workdir, "ios.csv"))


def test_ios_transient_subnormals_are_flagged(workdir):
    # Failure control: values shrink ~1e5 per iteration, pass through the
    # subnormal range and end as exact zeros. The final-vector count in ios.csv
    # misses this case (it stays 0); only the per-iteration scan catches it.
    n, entries = fx.laplacian_2d(10)
    fx.write_symmetric(workdir / "matrices/Test/tiny.mtx", n, entries, scale=1e-5, positive=True)
    res = run_bin(workdir, "Test/tiny.mtx", reps=1)
    assert res.returncode == 0, res.stderr
    row = scan_row(workdir)
    assert int(row["iters_with_nonnormal"]) > 0
    assert "WARNING IOS scan" in res.stderr
    assert all(int(r["nonnormal"]) == 0 for r in read_rows(workdir, "ios.csv"))


BAD_FILES = {
    "pattern": "%%MatrixMarket matrix coordinate pattern symmetric\n2 2 2\n1 1\n2 1\n",
    "skew": "%%MatrixMarket matrix coordinate real skew-symmetric\n2 2 1\n2 1 3.0\n",
    "complex": "%%MatrixMarket matrix coordinate complex general\n1 1 1\n1 1 1.0 2.0\n",
    "truncated": "%%MatrixMarket matrix coordinate real general\n2 2 3\n1 1 1.0\n2 2 1.0\n",
    "rectangular": "%%MatrixMarket matrix coordinate real general\n2 3 1\n1 1 1.0\n",
    "out_of_range": "%%MatrixMarket matrix coordinate real general\n2 2 2\n1 1 1.0\n3 1 1.0\n",
    "no_banner": "matrix coordinate real general\n1 1 1\n1 1 1.0\n",
}


@pytest.mark.parametrize("kind", sorted(BAD_FILES))
def test_parser_rejects(workdir, kind):
    fx.write_raw(workdir / f"matrices/Test/{kind}.mtx", BAD_FILES[kind])
    res = run_bin(workdir, f"Test/{kind}.mtx", reps=1)
    assert res.returncode != 0
    assert "Matrix Market parse error" in res.stderr


def test_old_schema_csv_is_refused(workdir):
    n, entries = fx.laplacian_2d(8)
    fx.write_symmetric(workdir / "matrices/Test/lap.mtx", n, entries)
    old = workdir / "results" / PLATFORM_DIR
    old.mkdir(parents=True)
    (old / "rax.csv").write_text("matrix,category,reordering,threads,gflops,time_ms\n")
    res = run_bin(workdir, "Test/lap.mtx", reps=1)
    assert res.returncode != 0
    assert "different header" in res.stderr


@pytest.fixture(scope="session")
def check_driver(tmp_path_factory):
    exe = tmp_path_factory.mktemp("drv") / "check_driver"
    srcs = ["tests/c/check_driver.c", "src/reorder/reorder.c", "third-party/rcm/rcm.c",
            "src/matrix/csr.c", "src/matrix/coo.c", "src/matrix/parser.c", "src/utils/utils.c",
            "src/spmv/spmv.c", "src/benchmark/benchmark.c", "src/benchmark/metrics.c",
            "src/benchmark/timer.c"]
    subprocess.run(["gcc", "-O1", "-fopenmp", "-Iinclude", "-I/usr/include/scotch", "-Ithird-party/rcm",
                    *srcs, "-o", str(exe), "-lcxsparse", "-lscotch", "-lscotcherr", "-lm", "-lpapi"],
                   cwd=REPO_ROOT, check=True)
    return exe


@pytest.mark.parametrize("mode,ok,message", [
    ("ok", True, "CHECK PASSED"),
    ("dup", False, "INVALID PERMUTATION"),
    ("range", False, "INVALID PERMUTATION"),
    ("corrupt", False, "CORRECTNESS FAIL"),
    ("wrong_perm", False, "CORRECTNESS FAIL"),
])
def test_permutation_checks_can_fail(check_driver, mode, ok, message):
    res = subprocess.run([str(check_driver), mode], capture_output=True, text=True)
    assert (res.returncode == 0) == ok, res.stderr
    assert message in (res.stdout + res.stderr)


# ---------------------------------------------------------------- symmetric input

def build_tool(tmp_path_factory, main_src, name):
    exe = tmp_path_factory.mktemp(name) / name
    srcs = [main_src, "src/reorder/reorder.c", "third-party/rcm/rcm.c", "src/matrix/csr.c",
            "src/matrix/coo.c", "src/matrix/parser.c", "src/utils/utils.c", "src/spmv/spmv.c",
            "src/benchmark/benchmark.c", "src/benchmark/metrics.c", "src/benchmark/timer.c"]
    subprocess.run(["gcc", "-O1", "-fopenmp", "-Iinclude", "-I/usr/include/scotch", "-Ithird-party/rcm",
                    *srcs, "-o", str(exe), "-lcxsparse", "-lscotch", "-lscotcherr", "-lm", "-lpapi"],
                   cwd=REPO_ROOT, check=True)
    return exe


@pytest.fixture(scope="session")
def dump_tool(tmp_path_factory):
    return build_tool(tmp_path_factory, "tests/c/dump_csr.c", "dump_csr")


def dump(tool, workdir, matrix):
    res = subprocess.run([str(tool), matrix], cwd=workdir, capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    lines = res.stdout.strip().splitlines()
    lines = lines[lines.index("BEGIN") + 1:]
    n, nnz = map(int, lines[0].split())
    entries = {}
    for line in lines[1:]:
        i, j, v = line.split()
        assert (int(i), int(j)) not in entries, "duplicate entry"
        entries[(int(i), int(j))] = float(v)
    assert len(entries) == nnz
    return n, entries


def test_symmetric_file_expands_to_the_full_matrix(workdir, dump_tool):
    # Every mirrored entry must land at (j, i) with the value of (i, j), and the
    # diagonal must appear once. Values differ per pair, so a mirror written to
    # the wrong position, with a wrong value, or twice is detected.
    n, full = fx.distinct_symmetric(9)
    fx.write_symmetric(workdir / "matrices/Test/sym.mtx", n, full)
    n_read, got = dump(dump_tool, workdir, "Test/sym.mtx")
    assert n_read == n
    assert got == full


def test_symmetric_and_general_files_agree(workdir, dump_tool):
    n, full = fx.distinct_symmetric(7)
    fx.write_symmetric(workdir / "matrices/Test/sym.mtx", n, full)
    fx.write_general_full(workdir / "matrices/Test/gen.mtx", n, full)
    assert dump(dump_tool, workdir, "Test/sym.mtx") == dump(dump_tool, workdir, "Test/gen.mtx")


UNSYMMETRIC = {
    # (2,1) without (1,2): a structurally unsymmetric 'general' matrix
    "unsym": "%%MatrixMarket matrix coordinate real general\n3 3 4\n1 1 1.0\n2 2 1.0\n3 3 1.0\n2 1 5.0\n",
    # the same entry twice
    "dup": "%%MatrixMarket matrix coordinate real general\n2 2 3\n1 1 1.0\n2 2 1.0\n2 2 4.0\n",
}


@pytest.mark.parametrize("kind,message", [("unsym", "without a transpose partner: 1 "),
                                          ("dup", "duplicate entries: 1")])
def test_unusable_pattern_is_rejected_before_ordering(workdir, kind, message):
    # Failure control for require_symmetric_pattern. Without the check, Scotch
    # nested dissection does not terminate on an unsymmetric pattern, so a short
    # timeout makes a missing check fail fast instead of hanging the suite.
    fx.write_raw(workdir / f"matrices/Test/{kind}.mtx", UNSYMMETRIC[kind])
    res = run_bin(workdir, f"Test/{kind}.mtx", reps=1, timeout=30)
    assert res.returncode != 0
    assert message in res.stderr


def test_preflight_check_binary(workdir):
    check = REPO_ROOT / "bin" / "spmv-check"
    n, full = fx.distinct_symmetric(6)
    fx.write_symmetric(workdir / "matrices/Test/sym.mtx", n, full)
    fx.write_raw(workdir / "matrices/Test/unsym.mtx", UNSYMMETRIC["unsym"])
    ok = subprocess.run([str(check), "Test/sym.mtx"], cwd=workdir, capture_output=True, text=True, timeout=30)
    bad = subprocess.run([str(check), "Test/unsym.mtx"], cwd=workdir, capture_output=True, text=True, timeout=30)
    assert ok.returncode == 0 and "OK Test/sym.mtx" in ok.stdout
    assert bad.returncode != 0 and "without a transpose partner" in bad.stderr

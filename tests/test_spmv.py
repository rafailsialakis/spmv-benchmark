import ctypes
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


class CSRMatrix(ctypes.Structure):
    _fields_ = [
        ("n", ctypes.c_int),
        ("nnz", ctypes.c_int),
        ("row_ptr", ctypes.POINTER(ctypes.c_int)),
        ("col_idx", ctypes.POINTER(ctypes.c_int)),
        ("values", ctypes.POINTER(ctypes.c_double)),
    ]


@dataclass(frozen=True)
class SpMVCase:
    name: str
    n: int
    row_ptr: tuple[int, ...]
    col_idx: tuple[int, ...]
    values: tuple[float, ...]
    x: tuple[float, ...]
    expected: tuple[float, ...]


CASES = [
    SpMVCase(
        name="matrix_with_empty_row",
        n=4,
        row_ptr=(0, 2, 2, 5, 7),
        col_idx=(0, 2, 0, 1, 3, 1, 3),
        values=(10.0, 2.0, -1.0, 3.0, 4.0, 5.0, 6.0),
        x=(1.0, 2.0, 3.0, 4.0),
        expected=(16.0, 0.0, 21.0, 34.0),
    ),
    SpMVCase(
        name="zero_nnz_matrix",
        n=2,
        row_ptr=(0, 0, 0),
        col_idx=(),
        values=(),
        x=(7.0, -3.0),
        expected=(0.0, 0.0),
    ),
    SpMVCase(
        name="mixed_sign_values",
        n=3,
        row_ptr=(0, 3, 5, 6),
        col_idx=(0, 1, 2, 0, 2, 1),
        values=(1.5, -2.0, 0.5, -4.0, 2.0, -3.0),
        x=(2.0, -1.0, 8.0),
        expected=(9.0, 8.0, 3.0),
    ),
]


def c_array(ctype, values):
    if not values:
        return (ctype * 1)()
    return (ctype * len(values))(*values)


@pytest.fixture(scope="session")
def spmv_lib(tmp_path_factory):
    lib_path = tmp_path_factory.mktemp("spmv") / "libspmv.so"
    subprocess.run(
        [
            "gcc",
            "-shared",
            "-fPIC",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fopenmp",
            "-I",
            str(REPO_ROOT / "include"),
            str(REPO_ROOT / "src/spmv/spmv.c"),
            "-o",
            str(lib_path),
        ],
        check=True,
        cwd=REPO_ROOT,
    )

    lib = ctypes.CDLL(str(lib_path))
    argtypes = [
        ctypes.POINTER(CSRMatrix),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.spmv_csr.argtypes = argtypes
    lib.spmv_csr_parallel.argtypes = argtypes
    return lib


@pytest.mark.parametrize("function_name", ["spmv_csr", "spmv_csr_parallel"])
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_spmv_csr(function_name, case, spmv_lib):
    os.environ["OMP_NUM_THREADS"] = "4"

    row_ptr = c_array(ctypes.c_int, case.row_ptr)
    col_idx = c_array(ctypes.c_int, case.col_idx)
    values = c_array(ctypes.c_double, case.values)
    x = c_array(ctypes.c_double, case.x)
    y = c_array(ctypes.c_double, [-99.0] * case.n)
    csr = CSRMatrix(case.n, len(case.values), row_ptr, col_idx, values)

    getattr(spmv_lib, function_name)(ctypes.byref(csr), x, y)

    assert list(y) == pytest.approx(case.expected)

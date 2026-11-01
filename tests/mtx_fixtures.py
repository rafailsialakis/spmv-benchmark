"""Small Matrix Market files for the benchmark self-tests (written on the fly)."""

import random
from pathlib import Path


def laplacian_2d(k: int):
    """5-point Laplacian on a k x k grid as a dict {(i, j): value}, 0-based."""
    entries = {}
    for r in range(k):
        for c in range(k):
            i = r * k + c
            entries[(i, i)] = 4.0
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < k and 0 <= cc < k:
                    entries[(i, rr * k + cc)] = -1.0
    return k * k, entries


def write_symmetric(path: Path, n, entries, name="SomeLongGroupName/a_matrix_name_longer_than_16",
                    field="real", symmetry="symmetric", scale=1.0, positive=False):
    """Lower triangle, column-major sorted, as SuiteSparse writes it."""
    lower = sorted(((j, i), abs(v) if positive else v) for (i, j), v in entries.items() if i >= j)
    lines = [f"%%MatrixMarket matrix coordinate {field} {symmetry}", f"% name: {name}",
             f"{n} {n} {len(lower)}"]
    for (j, i), v in lower:
        lines.append(f"{i + 1} {j + 1}" if field == "pattern" else f"{i + 1} {j + 1} {v * scale:.17g}")
    path.write_text("\n".join(lines) + "\n")


def write_general_shuffled(path: Path, n, entries, seed=7):
    """Same structure under a random symmetric permutation, entries in random order."""
    rng = random.Random(seed)
    perm = list(range(n))
    rng.shuffle(perm)
    items = [((perm[i], perm[j]), v * (1.0 + 0.01 * ((i + j) % 5))) for (i, j), v in entries.items()]
    rng.shuffle(items)
    lines = ["%%MatrixMarket matrix coordinate real general", f"{n} {n} {len(items)}"]
    lines += [f"{i + 1} {j + 1} {v:.17g}" for (i, j), v in items]
    path.write_text("\n".join(lines) + "\n")


def write_raw(path: Path, text: str):
    path.write_text(text)


def distinct_symmetric(k: int):
    """Laplacian pattern with a different value for every symmetric pair, so a
    wrongly mirrored entry (wrong position or wrong value) cannot go unnoticed."""
    n, entries = laplacian_2d(k)
    out = {}
    for (i, j) in entries:
        a, b = min(i, j), max(i, j)
        out[(i, j)] = 10.0 + a + b / (2.0 * n) if a != b else 1000.0 + i
    return n, out


def write_general_full(path: Path, n, entries):
    """All entries, general format, row-major order."""
    lines = ["%%MatrixMarket matrix coordinate real general", f"{n} {n} {len(entries)}"]
    lines += [f"{i + 1} {j + 1} {v:.17g}" for (i, j), v in sorted(entries.items())]
    path.write_text("\n".join(lines) + "\n")

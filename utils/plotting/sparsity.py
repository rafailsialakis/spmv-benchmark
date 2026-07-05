"""Sparsity-pattern plotting utilities."""

import logging

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import mmread

from utils.plotting.common import save_figure


def sparse_plot(path: str) -> None:
    """Plot original and reordered sparsity patterns for a Matrix Market file."""
    logging.info("Generating sparsity patterns...")
    A = mmread(path).tocsr()

    perm_rcm = np.loadtxt("validation/rcm.txt", dtype=int)
    perm_amd = np.loadtxt("validation/amd.txt", dtype=int)
    perm_nd = np.loadtxt("validation/nd.txt", dtype=int)
    logging.info("Permutations parsed successfully!")

    B = A[perm_rcm, :][:, perm_rcm]
    C = A[perm_amd, :][:, perm_amd]
    D = A[perm_nd, :][:, perm_nd]
    logging.info("Matrices permuted successfully!")

    logging.info("Plotting...")
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))

    for ax, matrix, title in zip(
        axes.flat,
        [A, B, C, D],
        ["Original", "RCM", "AMD", "ND"],
    ):
        ax.spy(matrix, markersize=0.1, rasterized=True)
        ax.set_title(title)

    plt.tight_layout()

    name = path.split("/")[-1].split(".")[0]
    save_figure("sparsity", f"{name}_sparsity_plot.pdf", dpi=300)
    logging.info("Plot was saved successfully in figures/sparsity/%s_sparsity_plot.pdf", name)
    plt.show()

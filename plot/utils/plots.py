import logging
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.io import mmread
import matplotlib.pyplot as plt

"""
Produces a .pdf that contains the sparse plots of each reordering method of a given matrix

Args:
    path (str): The path from spmv_benchmark to the .mtx file

Returns:
    None

Note:
    In order to run correctly the permutation vectors must be saved/updated for the given matrix
"""
def sparse_plot(path: str) -> None:
    logging.info("Generating sparsity patterns...")
    A = mmread(path).tocsr()
    # Load Permutation Vectors from .txt files
    perm_rcm = np.loadtxt("validation/rcm.txt", dtype=int)
    perm_amd = np.loadtxt("validation/amd.txt", dtype=int)
    perm_nd = np.loadtxt("validation/nd.txt", dtype=int)
    logging.info("Permutations parsed successfully!")
    # Permute matrix
    B = A[perm_rcm, :][:, perm_rcm]
    C = A[perm_amd, :][:, perm_amd]
    D = A[perm_nd, :][:, perm_nd]
    logging.info("Matrices permuted successfully!")
    # Initialize plot
    logging.info("Plotting...")
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))

    for ax, M, title in zip(
        axes.flat,
        [A, B, C, D],
        ["Original", "RCM", "AMD", "ND"]
    ):
        ax.spy(M, markersize=0.1,rasterized=True)
        ax.set_title(title)

    plt.tight_layout()

    name = path.split("/")[-1].split(".")[0]
    plt.savefig(f"plot/figures/{name}_sparsity_plot.pdf", dpi=300)
    logging.info(f"{name}_sparsity_plot.pdf was saved successfully!")
    plt.show()

"""
Produces a speedup heatmap that calculates the speedup each reordering method has given 4 threads

Args:
    df_param (pd.DataFrame):
    label (str):

Returns:
    None
"""
def speedup_heatmap(df_param: pd.DataFrame, label: str):
    logging.info(f"Generating speedup heatmap for {label} architecture...")
    logging.info(f"Reading and pivoting dataframe...")
    df = df_param.copy()
    # Keep the lines with 4 threads
    df = df[df["threads"] == 4]

    # Pivot with time_ms on z-axis
    time_pivot = df.pivot(
        index="matrix",
        columns="reordering",
        values="time_ms"
    )
    logging.info(f"Calculating speedup...")
    # Calculate speedup and drop columns with no reordering
    speedup = time_pivot["none"].values.reshape(-1, 1) / time_pivot
    speedup = speedup.drop(columns=["none"])

    # Sort values by rcm reordering
    speedup = speedup.sort_values(by="rcm", ascending=False)
    logging.info(f"Plotting...")

    plt.figure(figsize=(10, 7))

    sns.heatmap(
        speedup,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cmap="viridis",
        cbar_kws={"label": r"\textbf{Speedup}"}
    )

    plt.title(rf"\textbf{{Speedup per Reordering (4 threads, {label})}}")    
    plt.xlabel(r"\textbf{Reordering Method}")
    plt.ylabel(r"\textbf{Matrix}")

    plt.tight_layout()
    plt.savefig(f"plot/figures/speedup_heatmap_{label}.pdf")
    logging.info(f"speedup_heatmap_{label}.pdf was saved successfully!")
    plt.show()

"""
Produces a .pdf that produces a barchart in order to compare
x86 and ARM architecture speedups.

Args:
    path (str): The path from spmv_benchmark to the .mtx file

Returns:
    None
"""
def arm_x86_comp(df_x86: pd.DataFrame, df_arm: pd.DataFrame):
    logging.info("Generating ARM vs x86 speedup barchart...")
    # Keep the lines with 4 threads and save avg time / matrix 
    
    logging.info("Reading dataframes...")
    df_x86_copy = (
        df_x86[df_x86["threads"] == 4]
        .groupby("matrix", as_index=False)["time_ms"]
        .mean()
    )  
    df_arm_copy = (
        df_arm[df_arm["threads"] == 4]
        .groupby("matrix", as_index=False)["time_ms"]
        .mean()
    )

    # Merge x86 and ARM data
    df_merged = df_x86_copy.merge(
        df_arm_copy,
        on="matrix",
        suffixes=("_x86", "_arm")
    )
    
    # Calculate speedup
    logging.info("Calculating speedup comparison...")
    df_merged["speedup"] = df_merged["time_ms_x86"] / df_merged["time_ms_arm"]

    # Sort on speedup
    df_merged = df_merged.sort_values("speedup", ascending=False)
    
    logging.info("Plotting...")

    plt.figure(figsize=(12, 6))
    bars = plt.bar(df_merged["matrix"], df_merged["speedup"], color="royalblue")
    
    plt.axhline(1, linestyle="--", color="red", label=r"$\text{x86 = ARM}$")
    plt.ylabel(r"\textbf{Speedup (ARM over x86)}")
    plt.xlabel(r"\textbf{Matrix}")
    plt.title(r"\textbf{ARM vs x86 Performance (4 threads)}")
    plt.xticks(rotation=45, ha="right")

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.02,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=10
        )
    plt.legend()
    plt.tight_layout()
    # Save file
    plt.savefig(f"plot/figures/arm_vs_x86.pdf")
    logging.info(f"arm_vs_x86.pdf was saved successfully!")
    plt.show()
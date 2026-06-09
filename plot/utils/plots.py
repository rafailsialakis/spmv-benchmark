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
    logging.info(f"Plot was saved successfully in {name}_sparsity_plot.pdf")
    plt.show()

"""
Produced a .pdf that presents a barchart with the matrices that provide 
a speedup > 1.05, neutral and slowdown < 1. 

Args: 
    df_param (pd.DataFrame): Dataframe that contains time_ms in order to calculate speedup
    label (str): Either ARM or x86 depending on input

Returns:
    None
"""
def win_loss_summary(df_param: pd.DataFrame, label: str) -> None:
    logging.info(f"Generating win/loss summary for {label}...")
    df = df_param.copy()
    
    df = df[df["threads"] == 4]
    
    methods = ["rcm", "amd", "nd"]
    matrices = df[df["reordering"] == "none"]["matrix"].unique()
    
    results = {"win": [], "neutral": [], "loss": []}
    
    for method in methods:
        wins = 0
        neutrals = 0
        losses = 0
        for matrix in matrices:
            base = df[(df["matrix"] == matrix) & (df["reordering"] == "none")]["time_ms"].values
            reord = df[(df["matrix"] == matrix) & (df["reordering"] == method)]["time_ms"].values
            if len(base) == 0 or len(reord) == 0:
                continue
            speedup = base[0] / reord[0]
            if speedup > 1.05:
                wins += 1
            elif speedup < 0.95:
                losses += 1
            else:
                neutrals += 1
        results["win"].append(wins)
        results["neutral"].append(neutrals)
        results["loss"].append(losses)

    fig, ax = plt.subplots(figsize=(5, 3.5))
    
    x = np.arange(len(methods))
    width = 0.25
    bars1 = ax.bar(x - width, results["win"],     width, label="Speedup $> 1.05$",    color="#2E86AB", alpha=0.85)
    bars2 = ax.bar(x,         results["neutral"], width, label="Neutral ($\\pm5\\%$)", color="#A8A8A8", alpha=0.85)
    bars3 = ax.bar(x + width, results["loss"],    width, label="Slowdown $< 0.95$",   color="#E84855", alpha=0.85)

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1,
                        str(int(h)), ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels([m.upper() for m in methods], fontsize=9)
    ax.set_ylabel("Number of matrices", fontsize=9)
    ax.set_title(f"Reordering Win/Loss Summary (4 threads, {label})", fontsize=9, pad=6)
    ax.legend(fontsize=8, framealpha=0.85)
    ax.yaxis.grid(True, lw=0.4, ls=":", color="#ccc", zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, len(matrices) + 1)

    plt.tight_layout()
    plt.savefig(f"plot/figures/win_loss_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info(f"Saved win_loss_{label}.pdf")
    plt.show()

"""
Produces a faceted bar chart showing L1, L2, L3 cache miss reduction (%)
vs the original (unreordered) ordering, one subplot per matrix.

Args:
    df_param (pd.DataFrame): DataFrame with columns: matrix, reordering, L1_misses, L2_misses, L3_misses

Returns:
    None
"""
def cache_plot(df_param: pd.DataFrame, label: str) -> None:
    logging.info("Generating cache miss reduction faceted plot...")
    df = df_param.copy()

    all_levels  = ["L1_misses", "L2_misses", "L3_misses"]
    all_labels  = ["L1", "L2", "L3"]
    all_colors  = ["#378ADD", "#1D9E75", "#D85A30"]

    available    = [(l, lb, c) for l, lb, c in zip(all_levels, all_labels, all_colors)
                    if l in df.columns and df[l].notna().any()]
    levels       = [x[0] for x in available]
    level_labels = [x[1] for x in available]
    level_colors = [x[2] for x in available]

    matrices = sorted(df[df["reordering"] == "none"]["matrix"].unique().tolist())
    methods  = ["rcm", "amd", "nd"]

    def get_reduction(matrix, method, level):
        base = df[(df["matrix"] == matrix) & (df["reordering"] == "none")][level].values[0]
        val  = df[(df["matrix"] == matrix) & (df["reordering"] == method)][level].values[0]
        return (base - val) / base * 100

    ncols  = 4
    nrows  = int(np.ceil(len(matrices) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.2, nrows * 2.8))
    axes = axes.flatten()

    n      = len(levels)
    width  = 0.22
    x      = np.arange(len(methods))
    offset = np.linspace(-(n - 1) * width / 2, (n - 1) * width / 2, n)

    logging.info("Plotting subplots...")
    for i, matrix in enumerate(matrices):
        ax = axes[i]
        for j, (level, color) in enumerate(zip(levels, level_colors)):
            reductions = [get_reduction(matrix, m, level) for m in methods]
            bars = ax.bar(x + offset[j], reductions, width,
                          color=color, alpha=0.85, zorder=3)
            for bar, val in zip(bars, reductions):
                if abs(val) > 1:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + (0.5 if val >= 0 else -1.5),
                        f"{val:.1f}",
                        ha="center", va="bottom", fontsize=5.5, color="#444"
                    )

        ax.axhline(0, color="#aaa", linewidth=0.6, zorder=2)
        ax.set_title(matrix, fontsize=9, fontweight="bold", pad=4)
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in methods], fontsize=8)
        ax.set_ylabel("Miss reduction (\%)", fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.yaxis.grid(True, linewidth=0.4, color="#ddd", zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    for j in range(len(matrices), len(axes)):
        axes[j].set_visible(False)

    legend_patches = [
        plt.matplotlib.patches.Patch(color=c, alpha=0.85, label=l)
        for c, l in zip(level_colors, level_labels)
    ]
    fig.legend(handles=legend_patches, loc="lower right",
               ncol=3, fontsize=9, frameon=False,
               bbox_to_anchor=(0.98, 0.01))

    fig.suptitle(
        rf"\textbf{{Cache miss reduction (\%) per reordering method {label} (1 thread)}}",
        fontsize=12, y=1.01
    )

    plt.tight_layout()
    plt.savefig(f"plot/figures/cache_miss_faceted_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info("Plot saved in cache_miss_faceted.pdf")
    plt.show()


def cache_plot_normalized(df_param: pd.DataFrame, label: str, df_matrices: pd.DataFrame) -> None:
    logging.info("Generating normalized cache miss faceted plot...")
    df = df_param.copy()
    df = df.merge(df_matrices[["matrix", "nnz"]], on="matrix", how="left")

    all_levels  = ["L1_misses", "L2_misses", "L3_misses"]
    all_labels  = ["L1", "L2", "L3"]
    all_colors  = ["#378ADD", "#1D9E75", "#D85A30"]

    available    = [(l, lb, c) for l, lb, c in zip(all_levels, all_labels, all_colors)
                    if l in df.columns and df[l].notna().any()]
    levels       = [x[0] for x in available]
    level_labels = [x[1] for x in available]
    level_colors = [x[2] for x in available]

    matrices = sorted(df[df["reordering"] == "none"]["matrix"].unique().tolist())
    methods  = ["none", "rcm", "amd", "nd"]

    def get_normalized(matrix, method, level):
        nnz = df[df["matrix"] == matrix]["nnz"].values[0]
        val = df[(df["matrix"] == matrix) & (df["reordering"] == method)][level].values[0]
        return val / nnz

    ncols  = 4
    nrows  = int(np.ceil(len(matrices) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.2, nrows * 2.8))
    axes = axes.flatten()

    n      = len(levels)
    width  = 0.22
    x      = np.arange(len(methods))
    offset = np.linspace(-(n - 1) * width / 2, (n - 1) * width / 2, n)

    for i, matrix in enumerate(matrices):
        ax = axes[i]
        for j, (level, color) in enumerate(zip(levels, level_colors)):
            values = [get_normalized(matrix, m, level) for m in methods]
            ax.bar(x + offset[j], values, width,
                   color=color, alpha=0.85, zorder=3)

        ax.axhline(0, color="#aaa", linewidth=0.6, zorder=2)
        ax.set_title(matrix, fontsize=9, fontweight="bold", pad=4)
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in methods], fontsize=8)
        ax.set_ylabel("Misses / nnz", fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.yaxis.grid(True, linewidth=0.4, color="#ddd", zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    for j in range(len(matrices), len(axes)):
        axes[j].set_visible(False)

    legend_patches = [
        plt.matplotlib.patches.Patch(color=c, alpha=0.85, label=l)
        for c, l in zip(level_colors, level_labels)
    ]
    fig.legend(handles=legend_patches, loc="lower right",
               ncol=3, fontsize=9, frameon=False,
               bbox_to_anchor=(0.98, 0.01))

    fig.suptitle(
        rf"\textbf{{Cache misses per nnz per reordering method {label} (1 thread)}}",
        fontsize=12, y=1.01
    )

    plt.tight_layout()
    plt.savefig(f"plot/figures/cache_miss_normalized_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info(f"Plot saved in cache_miss_normalized_{label}.pdf")
    plt.show()

"""
Produces a faceted bar chart showing DTLB and ITLB load miss reduction (%)
vs the original (unreordered) ordering, one subplot per matrix.
 
Args:
    df_param (pd.DataFrame): DataFrame with columns:
                             matrix, category, reordering,
                             dtlb_load_misses, itlb_load_misses
    label (str): Either "ARM" or "x86" depending on input
 
Returns:
    None
"""
def tlb_plot(df_param: pd.DataFrame, label: str) -> None:
    logging.info(f"Generating TLB miss reduction faceted plot for {label}...")
    df = df_param.copy()
 
    levels       = ["dtlb_load_misses", "itlb_load_misses"]
    level_labels = ["DTLB", "ITLB"]
    level_colors = ["#378ADD", "#D85A30"]
 
    matrices = sorted(df[df["reordering"] == "none"]["matrix"].unique().tolist())
    methods  = ["rcm", "amd", "nd"]
 
    def get_reduction(matrix, method, level):
        base = df[(df["matrix"] == matrix) & (df["reordering"] == "none")][level].values[0]
        val  = df[(df["matrix"] == matrix) & (df["reordering"] == method)][level].values[0]
        if base == 0:
            return 0.0
        return (base - val) / base * 100
 
    ncols  = 4
    nrows  = int(np.ceil(len(matrices) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.2, nrows * 2.8))
    axes = axes.flatten()
 
    n      = len(levels)
    width  = 0.28
    x      = np.arange(len(methods))
    offset = np.linspace(-(n - 1) * width / 2, (n - 1) * width / 2, n)
 
    for i, matrix in enumerate(matrices):
        ax = axes[i]
        for j, (level, color) in enumerate(zip(levels, level_colors)):
            reductions = [get_reduction(matrix, m, level) for m in methods]
            bars = ax.bar(x + offset[j], reductions, width,
                          color=color, alpha=0.85, zorder=3)
            for bar, val in zip(bars, reductions):
                if abs(val) > 1:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + (0.5 if val >= 0 else -1.5),
                        f"{val:.1f}",
                        ha="center", va="bottom", fontsize=5.5, color="#444"
                    )
 
        ax.axhline(0, color="#aaa", linewidth=0.6, zorder=2)
        ax.set_title(matrix, fontsize=9, fontweight="bold", pad=4)
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in methods], fontsize=8)
        ax.set_ylabel("Miss reduction (\%)", fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.yaxis.grid(True, linewidth=0.4, color="#ddd", zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
 
    for j in range(len(matrices), len(axes)):
        axes[j].set_visible(False)
 
    legend_patches = [
        plt.matplotlib.patches.Patch(color=c, alpha=0.85, label=l)
        for c, l in zip(level_colors, level_labels)
    ]
    fig.legend(handles=legend_patches, loc="lower right",
               ncol=2, fontsize=9, frameon=False,
               bbox_to_anchor=(0.98, 0.01))
 
    fig.suptitle(
        rf"\textbf{{TLB miss reduction (\%) per reordering method {label} (1 thread)}}",
        fontsize=12, y=1.01
    )
 
    plt.tight_layout()
    plt.savefig(f"plot/figures/tlb_miss_faceted_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info(f"Plot saved in tlb_miss_faceted_{label}.pdf")
    plt.show()

"""
Produces a speedup heatmap that calculates the speedup each reordering method has given 4 threads

Args:
    df_param (pd.DataFrame):
    label (str):

Returns:
    None
"""
def speedup_heatmap(df_param: pd.DataFrame, label: str) -> None:
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
    logging.info(f"Plot was saved successfully in speedup_heatmap_{label}.pdf")
    plt.show()

"""
Produces a .pdf that produces a barchart in order to compare
x86 and ARM architecture speedups.

Args:
    path (str): The path from spmv_benchmark to the .mtx file

Returns:
    None
"""
def arm_x86_comp(df_x86: pd.DataFrame, df_arm: pd.DataFrame) -> None:
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
    logging.info(f"Plot was saved successfully in arm_vs_x86.pdf")
    plt.show()

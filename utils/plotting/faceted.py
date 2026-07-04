import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.plotting.common import save_figure


def cache_plot(df_param: pd.DataFrame, label: str) -> None:
    logging.info("Generating cache miss reduction faceted plot...")
    df = df_param.copy()

    all_levels = ["L1_misses", "L2_misses", "L3_misses"]
    all_labels = ["L1", "L2", "L3"]
    all_colors = ["#378ADD", "#1D9E75", "#D85A30"]

    available = [
        (level, level_label, color)
        for level, level_label, color in zip(all_levels, all_labels, all_colors)
        if level in df.columns and df[level].notna().any()
    ]
    levels = [x[0] for x in available]
    level_labels = [x[1] for x in available]
    level_colors = [x[2] for x in available]

    matrices = sorted(df[df["reordering"] == "none"]["matrix"].unique().tolist())
    methods = ["rcm", "amd", "nd"]

    def get_reduction(matrix, method, level):
        base = df[(df["matrix"] == matrix) & (df["reordering"] == "none")][level].values[0]
        val = df[(df["matrix"] == matrix) & (df["reordering"] == method)][level].values[0]
        return (base - val) / base * 100

    ncols = 4
    nrows = int(np.ceil(len(matrices) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.2, nrows * 2.8))
    axes = axes.flatten()

    n = len(levels)
    width = 0.22
    x = np.arange(len(methods))
    offset = np.linspace(-(n - 1) * width / 2, (n - 1) * width / 2, n)

    logging.info("Plotting subplots...")
    for i, matrix in enumerate(matrices):
        ax = axes[i]
        for j, (level, color) in enumerate(zip(levels, level_colors)):
            reductions = [get_reduction(matrix, method, level) for method in methods]
            bars = ax.bar(x + offset[j], reductions, width, color=color, alpha=0.85, zorder=3)
            for bar, val in zip(bars, reductions):
                if abs(val) > 1:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + (0.5 if val >= 0 else -1.5),
                        f"{val:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=5.5,
                        color="#444",
                    )

        ax.axhline(0, color="#aaa", linewidth=0.6, zorder=2)
        ax.set_title(matrix, fontsize=9, fontweight="bold", pad=4)
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in methods], fontsize=8)
        ax.set_ylabel(r"Miss reduction (\%)", fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.yaxis.grid(True, linewidth=0.4, color="#ddd", zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    for j in range(len(matrices), len(axes)):
        axes[j].set_visible(False)

    legend_patches = [
        plt.matplotlib.patches.Patch(color=color, alpha=0.85, label=level_label)
        for color, level_label in zip(level_colors, level_labels)
    ]
    fig.legend(
        handles=legend_patches,
        loc="lower right",
        ncol=3,
        fontsize=9,
        frameon=False,
        bbox_to_anchor=(0.98, 0.01),
    )

    fig.suptitle(
        rf"\textbf{{Cache miss reduction (\%) per reordering method {label} (1 thread)}}",
        fontsize=12,
        y=1.01,
    )

    plt.tight_layout()
    save_figure("faceted", f"cache_miss_faceted_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info("Plot saved in figures/faceted/cache_miss_faceted_%s.pdf", label)
    plt.show()


def cache_plot_normalized(df_param: pd.DataFrame, label: str, df_matrices: pd.DataFrame) -> None:
    logging.info("Generating normalized cache miss faceted plot...")
    df = df_param.copy()
    df = df.merge(df_matrices[["matrix", "nnz"]], on="matrix", how="left")

    all_levels = ["L1_misses", "L2_misses", "L3_misses"]
    all_labels = ["L1", "L2", "L3"]
    all_colors = ["#378ADD", "#1D9E75", "#D85A30"]

    available = [
        (level, level_label, color)
        for level, level_label, color in zip(all_levels, all_labels, all_colors)
        if level in df.columns and df[level].notna().any()
    ]
    levels = [x[0] for x in available]
    level_labels = [x[1] for x in available]
    level_colors = [x[2] for x in available]

    matrices = sorted(df[df["reordering"] == "none"]["matrix"].unique().tolist())
    methods = ["none", "rcm", "amd", "nd"]

    def get_normalized(matrix, method, level):
        nnz = df[df["matrix"] == matrix]["nnz"].values[0]
        val = df[(df["matrix"] == matrix) & (df["reordering"] == method)][level].values[0]
        return val / nnz

    ncols = 4
    nrows = int(np.ceil(len(matrices) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.2, nrows * 2.8))
    axes = axes.flatten()

    n = len(levels)
    width = 0.22
    x = np.arange(len(methods))
    offset = np.linspace(-(n - 1) * width / 2, (n - 1) * width / 2, n)

    for i, matrix in enumerate(matrices):
        ax = axes[i]
        for j, (level, color) in enumerate(zip(levels, level_colors)):
            values = [get_normalized(matrix, method, level) for method in methods]
            ax.bar(x + offset[j], values, width, color=color, alpha=0.85, zorder=3)

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
        plt.matplotlib.patches.Patch(color=color, alpha=0.85, label=level_label)
        for color, level_label in zip(level_colors, level_labels)
    ]
    fig.legend(
        handles=legend_patches,
        loc="lower right",
        ncol=3,
        fontsize=9,
        frameon=False,
        bbox_to_anchor=(0.98, 0.01),
    )

    fig.suptitle(
        rf"\textbf{{Cache misses per nnz per reordering method {label} (1 thread)}}",
        fontsize=12,
        y=1.01,
    )

    plt.tight_layout()
    save_figure("faceted", f"cache_miss_normalized_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info("Plot saved in figures/faceted/cache_miss_normalized_%s.pdf", label)
    plt.show()


def tlb_plot(df_param: pd.DataFrame, label: str) -> None:
    logging.info("Generating TLB miss reduction faceted plot for %s...", label)
    df = df_param.copy()

    levels = ["dtlb_load_misses", "itlb_load_misses"]
    level_labels = ["DTLB", "ITLB"]
    level_colors = ["#378ADD", "#D85A30"]

    matrices = sorted(df[df["reordering"] == "none"]["matrix"].unique().tolist())
    methods = ["rcm", "amd", "nd"]

    def get_reduction(matrix, method, level):
        base = df[(df["matrix"] == matrix) & (df["reordering"] == "none")][level].values[0]
        val = df[(df["matrix"] == matrix) & (df["reordering"] == method)][level].values[0]
        if base == 0:
            return 0.0
        return (base - val) / base * 100

    ncols = 4
    nrows = int(np.ceil(len(matrices) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.2, nrows * 2.8))
    axes = axes.flatten()

    n = len(levels)
    width = 0.28
    x = np.arange(len(methods))
    offset = np.linspace(-(n - 1) * width / 2, (n - 1) * width / 2, n)

    for i, matrix in enumerate(matrices):
        ax = axes[i]
        for j, (level, color) in enumerate(zip(levels, level_colors)):
            reductions = [get_reduction(matrix, method, level) for method in methods]
            bars = ax.bar(x + offset[j], reductions, width, color=color, alpha=0.85, zorder=3)
            for bar, val in zip(bars, reductions):
                if abs(val) > 1:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + (0.5 if val >= 0 else -1.5),
                        f"{val:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=5.5,
                        color="#444",
                    )

        ax.axhline(0, color="#aaa", linewidth=0.6, zorder=2)
        ax.set_title(matrix, fontsize=9, fontweight="bold", pad=4)
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in methods], fontsize=8)
        ax.set_ylabel(r"Miss reduction (\%)", fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.yaxis.grid(True, linewidth=0.4, color="#ddd", zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    for j in range(len(matrices), len(axes)):
        axes[j].set_visible(False)

    legend_patches = [
        plt.matplotlib.patches.Patch(color=color, alpha=0.85, label=level_label)
        for color, level_label in zip(level_colors, level_labels)
    ]
    fig.legend(
        handles=legend_patches,
        loc="lower right",
        ncol=2,
        fontsize=9,
        frameon=False,
        bbox_to_anchor=(0.98, 0.01),
    )

    fig.suptitle(
        rf"\textbf{{TLB miss reduction (\%) per reordering method {label} (1 thread)}}",
        fontsize=12,
        y=1.01,
    )

    plt.tight_layout()
    save_figure("faceted", f"tlb_miss_faceted_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info("Plot saved in figures/faceted/tlb_miss_faceted_%s.pdf", label)
    plt.show()

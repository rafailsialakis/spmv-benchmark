"""Bar chart generators for benchmark summary figures."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.plotting.common import save_figure


def win_loss_summary(df_param: pd.DataFrame, label: str) -> None:
    """Plot reordering win, neutral, and loss counts for four-thread runs."""
    logging.info("Generating win/loss summary for %s...", label)
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
    bars1 = ax.bar(x - width, results["win"], width, label="Speedup $> 1.05$", color="#2E86AB", alpha=0.85)
    bars2 = ax.bar(x, results["neutral"], width, label="Neutral ($\\pm5\\%$)", color="#A8A8A8", alpha=0.85)
    bars3 = ax.bar(x + width, results["loss"], width, label="Slowdown $< 0.95$", color="#E84855", alpha=0.85)

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + 0.1,
                    str(int(h)),
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

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
    save_figure("barcharts", f"win_loss_{label}.pdf", bbox_inches="tight", dpi=300)
    logging.info("Saved figures/barcharts/win_loss_%s.pdf", label)
    plt.show()


def arm_x86_comp(df_x86: pd.DataFrame, df_arm: pd.DataFrame) -> None:
    """Plot per-matrix ARM-over-x86 speedups for four-thread runs."""
    logging.info("Generating ARM vs x86 speedup barchart...")
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

    df_merged = df_x86_copy.merge(
        df_arm_copy,
        on="matrix",
        suffixes=("_x86", "_arm"),
    )

    logging.info("Calculating speedup comparison...")
    df_merged["speedup"] = df_merged["time_ms_x86"] / df_merged["time_ms_arm"]
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
            fontsize=10,
        )

    plt.legend()
    plt.tight_layout()
    save_figure("barcharts", "arm_vs_x86.pdf")
    logging.info("Plot was saved successfully in figures/barcharts/arm_vs_x86.pdf")
    plt.show()

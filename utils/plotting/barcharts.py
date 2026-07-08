"""Bar chart generators for benchmark summary figures."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.plotting.common import save_figure


METHODS = ["rcm", "amd", "nd"]
METHOD_LABELS = {"rcm": "RCM", "amd": "AMD", "nd": "ND"}


def _save(stem: str) -> None:
    """Save the current bar chart as PDF and PNG."""
    save_figure("barcharts", f"{stem}.pdf", bbox_inches="tight")
    save_figure("barcharts", f"{stem}.png", bbox_inches="tight", dpi=300)
    plt.close()


def win_loss_summary(df_param: pd.DataFrame, label: str) -> None:
    """Plot reordering win, neutral, and loss counts for four-thread runs."""
    logging.info("Generating win/loss summary for %s...", label)
    df = df_param[df_param["threads"] == 4].copy()
    pivot = df.pivot_table(
        index="matrix",
        columns="reordering",
        values="time_ms",
        aggfunc="mean",
    )

    if "none" not in pivot.columns:
        logging.warning("Skipping win/loss summary for %s; missing original ordering", label)
        return

    results = {"win": [], "neutral": [], "loss": []}

    for method in METHODS:
        wins = 0
        neutrals = 0
        losses = 0
        if method not in pivot.columns:
            results["win"].append(wins)
            results["neutral"].append(neutrals)
            results["loss"].append(losses)
            continue
        speedups = (pivot["none"] / pivot[method]).dropna()
        for speedup in speedups:
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

    x = np.arange(len(METHODS))
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
    ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS], fontsize=9)
    ax.set_ylabel("Number of matrices", fontsize=9)
    ax.set_title(f"Reordering Win/Loss Summary (4 threads, {label})", fontsize=9, pad=6)
    ax.legend(fontsize=8, framealpha=0.85)
    ax.yaxis.grid(True, lw=0.4, ls=":", color="#ccc", zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, len(pivot) + 1)

    fig.tight_layout()
    _save(f"win_loss_{label}")


def arm_x86_comp(df_x86: pd.DataFrame, df_arm: pd.DataFrame) -> None:
    """Plot per-matrix ARM-over-x86 baseline speedups for four-thread runs."""
    logging.info("Generating ARM vs x86 speedup barchart...")
    logging.info("Reading dataframes...")
    df_x86_copy = (
        df_x86[(df_x86["threads"] == 4) & (df_x86["reordering"] == "none")]
        .groupby("matrix", as_index=False)["time_ms"]
        .mean()
    )
    df_arm_copy = (
        df_arm[(df_arm["threads"] == 4) & (df_arm["reordering"] == "none")]
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
    if df_merged.empty:
        logging.warning("Skipping ARM vs x86 speedup barchart; no common matrices")
        return

    logging.info("Plotting...")
    fig_height = max(5.2, 0.18 * len(df_merged) + 1.5)
    fig, ax = plt.subplots(figsize=(7.2, fig_height))
    y = np.arange(len(df_merged))
    bars = ax.barh(y, df_merged["speedup"], color="#4169E1")

    ax.axvline(1, linestyle="--", color="#D55E00", label="x86 = ARM")
    ax.set_xlabel("Speedup (ARM over x86)")
    ax.set_ylabel("Matrix")
    ax.set_title("ARM vs x86 Baseline Performance (4 threads)")
    ax.set_yticks(y)
    ax.set_yticklabels(df_merged["matrix"], fontsize=7)
    ax.invert_yaxis()

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.03,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.2f}",
            ha="left",
            va="center",
            fontsize=6.5,
        )

    ax.legend()
    ax.xaxis.grid(True, lw=0.4, ls=":", color="#ccc", zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(left=0, right=df_merged["speedup"].max() * 1.12)
    fig.tight_layout()
    _save("arm_vs_x86")

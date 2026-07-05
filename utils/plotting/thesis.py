"""Thesis-specific figure generators for benchmark analysis."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

from utils.plotting.common import save_figure


METHODS = ["rcm", "amd", "nd"]
METHOD_LABELS = {"rcm": "RCM", "amd": "AMD", "nd": "ND"}
METHOD_COLORS = {"rcm": "#0072B2", "amd": "#D55E00", "nd": "#009E73"}


def _save(stem: str) -> None:
    """Save the current thesis figure as PDF and PNG."""
    save_figure("thesis", f"{stem}.pdf", bbox_inches="tight")
    save_figure("thesis", f"{stem}.png", bbox_inches="tight", dpi=300)
    plt.close()


def _speedup_long(df_param: pd.DataFrame, threads: int = 4) -> pd.DataFrame:
    """Return long-form speedups over the original ordering."""
    df = df_param[df_param["threads"] == threads].copy()
    pivot = df.pivot_table(
        index=["matrix", "category"],
        columns="reordering",
        values="time_ms",
        aggfunc="mean",
    )
    rows = []
    for method in METHODS:
        if "none" not in pivot.columns or method not in pivot.columns:
            continue
        rows.append(
            pd.DataFrame(
                {
                    "matrix": pivot.index.get_level_values("matrix"),
                    "category": pivot.index.get_level_values("category"),
                    "reordering": method,
                    "speedup": (pivot["none"] / pivot[method]).to_numpy(),
                }
            )
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _best_speedups(df_param: pd.DataFrame, threads: int = 4) -> pd.DataFrame:
    """Return the best reordering speedup for each matrix."""
    speedups = _speedup_long(df_param, threads)
    if speedups.empty:
        return pd.DataFrame()
    idx = speedups.groupby("matrix")["speedup"].idxmax()
    best = speedups.loc[idx].copy()
    return best.sort_values("speedup", ascending=True)


def best_speedup_ranked(df_param: pd.DataFrame, label: str, threads: int = 4) -> None:
    """Plot matrices ranked by their best observed reordering speedup."""
    logging.info("Generating thesis ranked best-speedup plot for %s...", label)
    best = _best_speedups(df_param, threads)
    if best.empty:
        logging.warning("Skipping ranked best-speedup plot for %s; no speedups", label)
        return

    best["display"] = best["category"] + " / " + best["matrix"]
    colors = best["reordering"].map(METHOD_COLORS)

    fig_height = max(5.2, 0.28 * len(best) + 1.5)
    fig, ax = plt.subplots(figsize=(7.2, fig_height))
    y = np.arange(len(best))
    ax.axvspan(0.95, 1.05, color="#D9D9D9", alpha=0.55, zorder=0)
    ax.barh(y, best["speedup"], color=colors, alpha=0.9, edgecolor="white", zorder=3)
    ax.axvline(1.0, color="#333333", linestyle="--", linewidth=1.0, zorder=4)

    for yi, speedup in zip(y, best["speedup"]):
        if speedup >= 1.08:
            ax.text(speedup + 0.035, yi, f"{speedup:.2f}", va="center", fontsize=7.5)

    ax.set_yticks(y)
    ax.set_yticklabels(best["display"], fontsize=8)
    ax.set_xlabel("Best speedup over original ordering")
    ax.set_title(f"Best Reordering per Matrix ({threads} threads, {label})", fontsize=12)
    ax.grid(axis="x", color="#D0D0D0", linestyle=":", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(left=0, right=max(1.25, best["speedup"].max() * 1.12))

    legend = [
        Line2D([0], [0], color=METHOD_COLORS[m], lw=6, label=METHOD_LABELS[m])
        for m in METHODS
    ]
    ax.legend(handles=legend, frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    _save(f"best_speedup_ranked_{label}")


def category_speedup_distribution(df_param: pd.DataFrame, label: str, threads: int = 4) -> None:
    """Plot speedup distributions grouped by matrix category."""
    logging.info("Generating thesis category speedup distribution for %s...", label)
    speedups = _speedup_long(df_param, threads)
    if speedups.empty:
        logging.warning("Skipping category speedup distribution for %s; no speedups", label)
        return

    order = (
        speedups.groupby("category")["speedup"]
        .median()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.axhspan(0.95, 1.05, color="#D9D9D9", alpha=0.55, zorder=0)
    sns.boxplot(
        data=speedups,
        x="category",
        y="speedup",
        hue="reordering",
        order=order,
        hue_order=METHODS,
        palette=METHOD_COLORS,
        width=0.65,
        fliersize=0,
        linewidth=0.8,
        ax=ax,
    )
    sns.stripplot(
        data=speedups,
        x="category",
        y="speedup",
        hue="reordering",
        order=order,
        hue_order=METHODS,
        palette=METHOD_COLORS,
        dodge=True,
        size=3,
        alpha=0.65,
        linewidth=0,
        ax=ax,
    )
    ax.axhline(1.0, color="#333333", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Matrix category")
    ax.set_ylabel("Speedup over original")
    ax.set_title(f"Speedup Distribution by Category ({threads} threads, {label})", fontsize=12)
    ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[:3], [METHOD_LABELS[m] for m in METHODS], frameon=False, ncol=3, fontsize=8)
    fig.tight_layout()
    _save(f"category_speedup_distribution_{label}")


def memory_speedup_relation(df_spmv_param: pd.DataFrame, df_cache_param: pd.DataFrame, label: str, threads: int = 4) -> None:
    """Plot the relationship between L2-miss reduction and runtime speedup."""
    logging.info("Generating thesis cache/runtime relation for %s...", label)
    speedups = _speedup_long(df_spmv_param, threads)
    reductions = []
    cache = df_cache_param.copy()
    for level in ["L1_misses", "L2_misses", "L3_misses"]:
        if level not in cache.columns:
            continue
        pivot = cache.pivot_table(
            index=["matrix", "category"],
            columns="reordering",
            values=level,
            aggfunc="mean",
        )
        if "none" not in pivot.columns:
            continue
        for method in METHODS:
            if method not in pivot.columns:
                continue
            base = pivot["none"].replace(0, np.nan)
            reductions.append(
                pd.DataFrame(
                    {
                        "matrix": pivot.index.get_level_values("matrix"),
                        "category": pivot.index.get_level_values("category"),
                        "reordering": method,
                        "counter": level,
                        "reduction": ((base - pivot[method]) / base * 100.0).to_numpy(),
                    }
                )
            )
    if not reductions:
        logging.warning("Skipping cache/runtime relation for %s; no cache reductions", label)
        return

    cache_long = pd.concat(reductions, ignore_index=True).dropna()
    merged = speedups.merge(
        cache_long[cache_long["counter"] == "L2_misses"],
        on=["matrix", "category", "reordering"],
        how="inner",
    )
    if merged.empty:
        logging.warning("Skipping cache/runtime relation for %s; no merged rows", label)
        return

    fig, ax = plt.subplots(figsize=(6.4, 4.1))
    for method in METHODS:
        part = merged[merged["reordering"] == method]
        ax.scatter(
            part["reduction"],
            part["speedup"],
            s=42,
            color=METHOD_COLORS[method],
            alpha=0.78,
            edgecolor="white",
            linewidth=0.5,
            label=METHOD_LABELS[method],
        )

    highlight_idx = merged.groupby("matrix")["speedup"].idxmax()
    highlight = merged.loc[highlight_idx].sort_values("speedup", ascending=False).head(5)
    for _, row in highlight.iterrows():
        ax.annotate(
            row["matrix"],
            (row["reduction"], row["speedup"]),
            xytext=(4, 3),
            textcoords="offset points",
            fontsize=7,
        )

    ax.axhline(1.0, color="#333333", linestyle="--", linewidth=1.0)
    ax.axvline(0.0, color="#333333", linestyle=":", linewidth=1.0)
    ax.set_xlabel(r"L2 miss reduction vs original (\%)")
    ax.set_ylabel("Speedup over original")
    ax.set_title(f"Runtime Benefit vs L2-Miss Reduction ({threads} threads, {label})", fontsize=12)
    ax.grid(color="#D0D0D0", linestyle=":", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(f"memory_speedup_relation_{label}")


def tlb_ratio_summary(df_tlb_param: pd.DataFrame, label: str) -> None:
    """Plot reordered-to-original TLB miss ratios for each method."""
    logging.info("Generating thesis TLB ratio summary for %s...", label)
    rows = []
    df = df_tlb_param.copy()
    for level, level_label in [("dtlb_load_misses", "DTLB"), ("itlb_load_misses", "ITLB")]:
        if level not in df.columns:
            continue
        pivot = df.pivot_table(
            index=["matrix", "category"],
            columns="reordering",
            values=level,
            aggfunc="mean",
        )
        if "none" not in pivot.columns:
            continue
        for method in METHODS:
            if method not in pivot.columns:
                continue
            base = pivot["none"].replace(0, np.nan)
            rows.append(
                pd.DataFrame(
                    {
                        "matrix": pivot.index.get_level_values("matrix"),
                        "category": pivot.index.get_level_values("category"),
                        "reordering": method,
                        "counter": level_label,
                        "ratio": (pivot[method] / base).to_numpy(),
                    }
                )
            )
    ratios = pd.concat(rows, ignore_index=True).dropna() if rows else pd.DataFrame()
    if ratios.empty:
        logging.warning("Skipping TLB ratio summary for %s; no ratios", label)
        return

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
    for ax, counter in zip(axes, ["DTLB", "ITLB"]):
        part = ratios[ratios["counter"] == counter].copy()
        sns.boxplot(
            data=part,
            x="reordering",
            y="ratio",
            hue="reordering",
            order=METHODS,
            hue_order=METHODS,
            palette=METHOD_COLORS,
            fliersize=0,
            linewidth=0.8,
            dodge=False,
            legend=False,
            ax=ax,
        )
        sns.stripplot(
            data=part,
            x="reordering",
            y="ratio",
            hue="reordering",
            order=METHODS,
            hue_order=METHODS,
            palette=METHOD_COLORS,
            size=3,
            alpha=0.65,
            jitter=0.18,
            linewidth=0,
            dodge=False,
            legend=False,
            ax=ax,
        )
        ax.axhline(1.0, color="#333333", linestyle="--", linewidth=1.0)
        ax.set_yscale("log")
        ax.set_title(counter, fontsize=10)
        ax.set_xlabel("Reordering")
        ax.set_xticks(range(len(METHODS)))
        ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS])
        ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Reordered / original TLB misses")
    axes[1].set_ylabel("")
    fig.suptitle(f"TLB Miss Ratio Summary ({label}, 1 thread)", fontsize=12)
    fig.tight_layout()
    _save(f"tlb_ratio_summary_{label}")


def methodology_stability(df_cold: pd.DataFrame, df_ios: pd.DataFrame, df_rax: pd.DataFrame, label: str, threads: int = 4) -> None:
    """Plot GFLOP/s variation across measurement methodologies."""
    logging.info("Generating thesis methodology stability figure for %s...", label)
    frames = []
    for name, df in [("Cold", df_cold), ("IO-swap", df_ios), ("Repeated Ax", df_rax)]:
        part = df[
            (df["threads"] == threads) &
            (df["reordering"] == "none")
        ][["matrix", "category", "gflops"]].copy()
        part["methodology"] = name
        frames.append(part)
    merged = pd.concat(frames, ignore_index=True)
    pivot = merged.pivot_table(index=["matrix", "category"], columns="methodology", values="gflops")
    if "Repeated Ax" not in pivot.columns:
        logging.warning("Skipping methodology stability for %s; missing repeated-Ax baseline", label)
        return
    available = [name for name in ["Cold", "IO-swap"] if name in pivot.columns]
    if not available:
        logging.warning("Skipping methodology stability for %s; no comparison methodology columns", label)
        return

    deltas = pivot[available].sub(pivot["Repeated Ax"], axis=0).div(pivot["Repeated Ax"], axis=0) * 100.0
    long = (
        deltas.reset_index()
        .melt(
            id_vars=["matrix", "category"],
            value_vars=available,
            var_name="methodology",
            value_name="delta",
        )
        .dropna()
    )
    if long.empty:
        logging.warning("Skipping methodology stability for %s; no comparable rows", label)
        return

    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    ax.axhspan(-5, 5, color="#D9D9D9", alpha=0.45, zorder=0)
    sns.boxplot(
        data=long,
        x="methodology",
        y="delta",
        order=available,
        color="#BDBDBD",
        fliersize=0,
        linewidth=0.9,
        width=0.5,
        ax=ax,
    )
    sns.stripplot(
        data=long,
        x="methodology",
        y="delta",
        order=available,
        hue="category",
        dodge=False,
        jitter=0.18,
        alpha=0.55,
        size=2.8,
        linewidth=0,
        ax=ax,
    )
    ax.axhline(0.0, color="#333333", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Measurement methodology")
    ax.set_ylabel(r"GFLOP/s difference vs repeated Ax (\%)")
    ax.set_title(f"Measurement Methodology Stability ({threads} threads, {label})", fontsize=12)
    ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, title="", frameon=False, fontsize=7, loc="best")
    fig.tight_layout()
    _save(f"methodology_stability_{label}")

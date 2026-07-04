import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.plotting.common import save_figure


METHODS = ["rcm", "amd", "nd"]
METHOD_LABELS = {"rcm": "RCM", "amd": "AMD", "nd": "ND"}
METHOD_COLORS = {"rcm": "#0072B2", "amd": "#D55E00", "nd": "#009E73"}
CACHE_LEVELS = ["L1_misses", "L2_misses", "L3_misses"]
CACHE_LABELS = {"L1_misses": "L1", "L2_misses": "L2", "L3_misses": "L3"}
TLB_LEVELS = ["dtlb_load_misses", "itlb_load_misses"]
TLB_LABELS = {"dtlb_load_misses": "DTLB", "itlb_load_misses": "ITLB"}


def _save(stem: str) -> None:
    save_figure("distributions", f"{stem}.pdf", bbox_inches="tight")
    save_figure("distributions", f"{stem}.png", bbox_inches="tight", dpi=300)
    plt.close()


def _method_values(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    pivot = df.pivot_table(
        index=["matrix", "category"],
        columns="reordering",
        values=value_col,
        aggfunc="mean",
    )
    rows = []
    for method in METHODS:
        if "none" not in pivot.columns or method not in pivot.columns:
            continue
        values = pivot["none"] / pivot[method]
        rows.append(
            pd.DataFrame(
                {
                    "matrix": pivot.index.get_level_values("matrix"),
                    "category": pivot.index.get_level_values("category"),
                    "reordering": method,
                    "value": values.to_numpy(),
                }
            )
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _reduction_values(df: pd.DataFrame, columns) -> pd.DataFrame:
    rows = []
    for col in columns:
        if col not in df.columns:
            continue
        pivot = df.pivot_table(
            index=["matrix", "category"],
            columns="reordering",
            values=col,
            aggfunc="mean",
        )
        if "none" not in pivot.columns:
            continue
        for method in METHODS:
            if method not in pivot.columns:
                continue
            base = pivot["none"].replace(0, np.nan)
            reduction = (base - pivot[method]) / base * 100.0
            rows.append(
                pd.DataFrame(
                    {
                        "matrix": pivot.index.get_level_values("matrix"),
                        "category": pivot.index.get_level_values("category"),
                        "reordering": method,
                        "counter": col,
                        "value": reduction.to_numpy(),
                    }
                )
            )
    return pd.concat(rows, ignore_index=True).dropna() if rows else pd.DataFrame()


def _annotate_histogram(ax, values: pd.Series, color: str) -> None:
    if values.empty:
        return
    median = values.median()
    ax.axvline(median, color=color, linewidth=1.4)
    ax.text(
        median,
        0.97,
        f"median {median:.2f}",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=8,
        color=color,
        rotation=90,
    )


def speedup_histogram(df_param: pd.DataFrame, label: str, threads: int = 4) -> None:
    logging.info("Generating speedup distribution histogram for %s...", label)
    df = df_param[df_param["threads"] == threads].copy()
    speedups = _method_values(df, "time_ms")
    if speedups.empty:
        logging.warning("Skipping speedup histogram for %s; no comparable rows", label)
        return

    lo = max(0.5, np.floor(speedups["value"].min() * 20) / 20)
    hi = min(2.0, np.ceil(speedups["value"].max() * 20) / 20)
    bins = np.linspace(lo, hi, 18)

    fig, axes = plt.subplots(1, 3, figsize=(9.2, 2.9), sharey=True)
    for ax, method in zip(axes, METHODS):
        vals = speedups[speedups["reordering"] == method]["value"]
        ax.axvspan(0.95, 1.05, color="#D9D9D9", alpha=0.45, zorder=0)
        ax.hist(
            vals,
            bins=bins,
            color=METHOD_COLORS[method],
            edgecolor="white",
            linewidth=0.8,
            alpha=0.88,
            zorder=3,
        )
        ax.axvline(1.0, color="#333333", linestyle="--", linewidth=1.0)
        _annotate_histogram(ax, vals, METHOD_COLORS[method])
        wins = int((vals > 1.05).sum())
        losses = int((vals < 0.95).sum())
        ax.set_title(f"{METHOD_LABELS[method]}  wins {wins} / losses {losses}", fontsize=10)
        ax.set_xlabel("Speedup over original")
        ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Matrices")
    fig.suptitle(f"Distribution of SpMV Speedups ({threads} threads, {label})", fontsize=12)
    fig.tight_layout()
    _save(f"speedup_histogram_{label}")


def cache_reduction_histogram(df_param: pd.DataFrame, label: str) -> None:
    logging.info("Generating cache miss reduction histogram for %s...", label)
    reductions = _reduction_values(df_param.copy(), CACHE_LEVELS)
    if reductions.empty:
        logging.warning("Skipping cache reduction histogram for %s; no comparable rows", label)
        return

    fig, axes = plt.subplots(1, 3, figsize=(9.2, 2.9), sharey=True)
    bins = np.linspace(
        max(-100, np.floor(reductions["value"].min() / 10) * 10),
        min(100, np.ceil(reductions["value"].max() / 10) * 10),
        17,
    )
    for ax, counter in zip(axes, CACHE_LEVELS):
        for method in METHODS:
            vals = reductions[
                (reductions["counter"] == counter) &
                (reductions["reordering"] == method)
            ]["value"]
            ax.hist(
                vals,
                bins=bins,
                histtype="step",
                linewidth=1.7,
                color=METHOD_COLORS[method],
                label=METHOD_LABELS[method],
            )
        ax.axvline(0.0, color="#333333", linestyle="--", linewidth=1.0)
        ax.set_title(f"{CACHE_LABELS[counter]} misses", fontsize=10)
        ax.set_xlabel(r"Reduction vs original (\%)")
        ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Matrix-method cases")
    axes[-1].legend(frameon=False, fontsize=8)
    fig.suptitle(f"Distribution of Cache-Miss Reductions ({label}, 1 thread)", fontsize=12)
    fig.tight_layout()
    _save(f"cache_reduction_histogram_{label}")


def tlb_reduction_histogram(df_param: pd.DataFrame, label: str) -> None:
    logging.info("Generating TLB miss reduction histogram for %s...", label)
    reductions = _reduction_values(df_param.copy(), TLB_LEVELS)
    if reductions.empty:
        logging.warning("Skipping TLB reduction histogram for %s; no comparable rows", label)
        return

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), sharey=True)
    bins = np.linspace(
        max(-100, np.floor(reductions["value"].min() / 10) * 10),
        min(100, np.ceil(reductions["value"].max() / 10) * 10),
        17,
    )
    for ax, counter in zip(axes, TLB_LEVELS):
        for method in METHODS:
            vals = reductions[
                (reductions["counter"] == counter) &
                (reductions["reordering"] == method)
            ]["value"]
            ax.hist(
                vals,
                bins=bins,
                histtype="stepfilled",
                alpha=0.16,
                color=METHOD_COLORS[method],
            )
            ax.hist(
                vals,
                bins=bins,
                histtype="step",
                linewidth=1.5,
                color=METHOD_COLORS[method],
                label=METHOD_LABELS[method],
            )
        ax.axvline(0.0, color="#333333", linestyle="--", linewidth=1.0)
        ax.set_title(f"{TLB_LABELS[counter]} misses", fontsize=10)
        ax.set_xlabel(r"Reduction vs original (\%)")
        ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Matrix-method cases")
    axes[-1].legend(frameon=False, fontsize=8)
    fig.suptitle(f"Distribution of TLB-Miss Reductions ({label}, 1 thread)", fontsize=12)
    fig.tight_layout()
    _save(f"tlb_reduction_histogram_{label}")


def breakeven_histogram(
    df_spmv_param: pd.DataFrame,
    df_reorder_param: pd.DataFrame,
    label: str,
    threads: int = 4,
) -> None:
    logging.info("Generating preprocessing break-even histogram for %s...", label)
    spmv = df_spmv_param[df_spmv_param["threads"] == threads].copy()
    pivot = spmv.pivot_table(index="matrix", columns="reordering", values="time_ms")
    rows = []
    for _, row in df_reorder_param.iterrows():
        matrix = row["matrix"]
        method = row["reordering"]
        if method not in METHODS or matrix not in pivot.index:
            continue
        if "none" not in pivot.columns or method not in pivot.columns:
            continue
        gain_s = (pivot.loc[matrix, "none"] - pivot.loc[matrix, method]) / 1000.0
        if gain_s <= 0:
            continue
        rows.append(
            {
                "matrix": matrix,
                "reordering": method,
                "iterations": row["time_s"] / gain_s,
            }
        )
    breakeven = pd.DataFrame(rows)
    if breakeven.empty:
        logging.warning("Skipping break-even histogram for %s; no positive gains", label)
        return

    fig, ax = plt.subplots(figsize=(6.8, 3.3))
    bins = np.logspace(0, 5, 18)
    for method in METHODS:
        vals = breakeven[breakeven["reordering"] == method]["iterations"]
        ax.hist(
            vals.clip(lower=1, upper=100000),
            bins=bins,
            histtype="stepfilled",
            alpha=0.16,
            color=METHOD_COLORS[method],
        )
        ax.hist(
            vals.clip(lower=1, upper=100000),
            bins=bins,
            histtype="step",
            linewidth=1.8,
            color=METHOD_COLORS[method],
            label=f"{METHOD_LABELS[method]} median {vals.median():.0f}",
        )

    ax.axvline(100, color="#555555", linestyle=":", linewidth=1.0)
    ax.axvline(1000, color="#555555", linestyle=":", linewidth=1.0)
    ax.set_xscale("log")
    ax.set_xlabel("Iterations needed to amortize reordering")
    ax.set_ylabel("Matrix-method cases")
    ax.set_title(f"Preprocessing Break-Even Distribution ({threads} threads, {label})", fontsize=12)
    ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(f"breakeven_histogram_{label}")


def structural_compression_histogram(df_metrics_param: pd.DataFrame, label: str) -> None:
    logging.info("Generating structural compression histogram for %s...", label)
    df = df_metrics_param.copy()
    rows = []
    for method in METHODS:
        bw_col = f"{method}_bw"
        avg_bw_col = f"avg_{method}_bw"
        lb_col = f"{method}_lb"
        if bw_col in df.columns:
            rows.append(
                pd.DataFrame(
                    {
                        "matrix": df["matrix"],
                        "category": df["category"],
                        "reordering": method,
                        "metric": "Envelope bandwidth",
                        "value": df["bw"] / df[bw_col].replace(0, np.nan),
                    }
                )
            )
        if avg_bw_col in df.columns:
            rows.append(
                pd.DataFrame(
                    {
                        "matrix": df["matrix"],
                        "category": df["category"],
                        "reordering": method,
                        "metric": "Average bandwidth",
                        "value": df["avg_bw"] / df[avg_bw_col].replace(0, np.nan),
                    }
                )
            )
        if lb_col in df.columns:
            rows.append(
                pd.DataFrame(
                    {
                        "matrix": df["matrix"],
                        "category": df["category"],
                        "reordering": method,
                        "metric": "Load balance",
                        "value": df["lb"] / df[lb_col].replace(0, np.nan),
                    }
                )
            )
    compression = pd.concat(rows, ignore_index=True).dropna() if rows else pd.DataFrame()
    if compression.empty:
        logging.warning("Skipping structural compression histogram for %s; no metric rows", label)
        return

    fig, axes = plt.subplots(1, 3, figsize=(9.2, 2.9), sharey=False)
    for ax, metric in zip(axes, ["Envelope bandwidth", "Average bandwidth", "Load balance"]):
        metric_df = compression[compression["metric"] == metric]
        max_value = min(100.0, np.nanpercentile(metric_df["value"], 95))
        bins = np.linspace(0, max(2.0, max_value), 18)
        for method in METHODS:
            vals = metric_df[metric_df["reordering"] == method]["value"].clip(upper=bins[-1])
            ax.hist(
                vals,
                bins=bins,
                histtype="step",
                linewidth=1.7,
                color=METHOD_COLORS[method],
                label=METHOD_LABELS[method],
            )
        ax.axvline(1.0, color="#333333", linestyle="--", linewidth=1.0)
        ax.set_title(metric, fontsize=10)
        ax.set_xlabel("Original / reordered")
        ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Matrices")
    axes[-1].legend(frameon=False, fontsize=8)
    fig.suptitle(f"Distribution of Structural Compression Factors ({label})", fontsize=12)
    fig.tight_layout()
    _save(f"structural_compression_histogram_{label}")

"""Overview figures that summarize benchmark trends."""

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
    """Save the current overview figure as PDF and PNG."""
    save_figure("overview", f"{stem}.pdf", bbox_inches="tight")
    save_figure("overview", f"{stem}.png", bbox_inches="tight", dpi=300)
    plt.close()


def _speedup_values(df_param: pd.DataFrame, threads: int) -> pd.DataFrame:
    """Return long-form speedups against the original ordering."""
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
    return pd.concat(rows, ignore_index=True).dropna() if rows else pd.DataFrame()


def _reduction_values(df_param: pd.DataFrame, counters: list[str]) -> pd.DataFrame:
    """Return long-form percentage reductions for selected counters."""
    rows = []
    for counter in counters:
        if counter not in df_param.columns:
            continue
        pivot = df_param.pivot_table(
            index=["matrix", "category"],
            columns="reordering",
            values=counter,
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
                        "counter": counter,
                        "reduction": ((base - pivot[method]) / base * 100.0).to_numpy(),
                    }
                )
            )
    return pd.concat(rows, ignore_index=True).dropna() if rows else pd.DataFrame()


def speedup_ecdf(df_param: pd.DataFrame, label: str, threads: int = 4) -> None:
    """Plot empirical CDFs of runtime speedup by reordering method."""
    logging.info("Generating speedup ECDF overview for %s...", label)
    speedups = _speedup_values(df_param, threads)
    if speedups.empty:
        logging.warning("Skipping speedup ECDF overview for %s; no comparable rows", label)
        return

    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.axvspan(0.95, 1.05, color="#D9D9D9", alpha=0.45, zorder=0)
    for method in METHODS:
        values = np.sort(speedups[speedups["reordering"] == method]["speedup"].to_numpy())
        if values.size == 0:
            continue
        y = np.arange(1, values.size + 1) / values.size
        ax.step(
            values,
            y,
            where="post",
            linewidth=2.0,
            color=METHOD_COLORS[method],
            label=METHOD_LABELS[method],
        )

    xmin = max(0.25, speedups["speedup"].min() * 0.9)
    xmax = max(1.25, speedups["speedup"].max() * 1.1)
    ax.axvline(1.0, color="#333333", linestyle="--", linewidth=1.0)
    ax.set_xscale("log")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Speedup over original ordering")
    ax.set_ylabel("Fraction of matrices")
    ax.set_title(f"Runtime Speedup ECDF ({threads} threads, {label})", fontsize=12)
    ax.grid(color="#D0D0D0", linestyle=":", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    _save(f"speedup_ecdf_{label}")


def _counter_interval_plot(
    values: pd.DataFrame,
    counters: list[str],
    labels: dict[str, str],
    title: str,
    ylabel: str,
    stem: str,
) -> None:
    """Plot percentile intervals for counter reductions."""
    available = [counter for counter in counters if counter in values["counter"].unique()]
    if not available:
        logging.warning("Skipping %s; no available counters", stem)
        return

    fig, axes = plt.subplots(1, len(available), figsize=(3.0 * len(available), 3.5), sharey=False)
    axes = np.atleast_1d(axes)
    x = np.arange(len(METHODS))

    for ax, counter in zip(axes, available):
        for xi, method in enumerate(METHODS):
            method_values = values[
                (values["counter"] == counter) &
                (values["reordering"] == method)
            ]["reduction"].dropna()
            if method_values.empty:
                continue
            p10, p25, median, p75, p90 = np.percentile(method_values, [10, 25, 50, 75, 90])
            color = METHOD_COLORS[method]
            ax.vlines(xi, p10, p90, color=color, alpha=0.35, linewidth=3.0, zorder=2)
            ax.vlines(xi, p25, p75, color=color, alpha=0.85, linewidth=7.0, zorder=3)
            ax.scatter(xi, median, marker="D", s=34, color=color, edgecolor="white", linewidth=0.6, zorder=4)

        ax.axhspan(-5, 5, color="#D9D9D9", alpha=0.35, zorder=0)
        ax.axhline(0.0, color="#333333", linestyle="--", linewidth=1.0, zorder=1)
        ax.set_title(labels[counter], fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS])
        if ax is not axes[0]:
            ax.set_ylabel("")
        ax.grid(axis="y", color="#D0D0D0", linestyle=":", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel(ylabel)
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    _save(stem)


def cache_reduction_overview(df_param: pd.DataFrame, label: str) -> None:
    """Plot an overview of cache-miss reductions by reordering method."""
    logging.info("Generating cache reduction overview for %s...", label)
    reductions = _reduction_values(df_param.copy(), CACHE_LEVELS)
    if reductions.empty:
        logging.warning("Skipping cache reduction overview for %s; no comparable rows", label)
        return

    _counter_interval_plot(
        reductions,
        CACHE_LEVELS,
        CACHE_LABELS,
        f"Cache-Miss Reduction Summary ({label}, 1 thread)",
        r"Reduction vs original (\%)",
        f"cache_reduction_overview_{label}",
    )


def tlb_reduction_overview(df_param: pd.DataFrame, label: str) -> None:
    """Plot an overview of TLB-miss reductions by reordering method."""
    logging.info("Generating TLB reduction overview for %s...", label)
    reductions = _reduction_values(df_param.copy(), TLB_LEVELS)
    if reductions.empty:
        logging.warning("Skipping TLB reduction overview for %s; no comparable rows", label)
        return

    _counter_interval_plot(
        reductions,
        TLB_LEVELS,
        TLB_LABELS,
        f"TLB-Miss Reduction Summary ({label}, 1 thread)",
        r"Reduction vs original (\%)",
        f"tlb_reduction_overview_{label}",
    )

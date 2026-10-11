"""Distribution plot generators kept for thesis diagnostics."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.plotting.common import (
    DOUBLE_COLUMN_WIDTH,
    NEUTRAL_BAND,
    REFERENCE_COLOR,
    paper_axes,
    save_figure,
)


METHODS = ["rcm", "amd", "nd", "gp"]
METHOD_LABELS = {"rcm": "RCM", "amd": "AMD", "nd": "ND", "gp": "GP"}
METHOD_COLORS = {"rcm": "#3B6EA8", "amd": "#B45F2A", "nd": "#3D8B62", "gp": "#7A4E9C"}


def _save(stem: str) -> None:
    """Save the current distribution figure as PDF and PNG."""
    save_figure("distributions", f"{stem}.pdf")
    save_figure("distributions", f"{stem}.png")
    plt.close()


def _speedup_values(df_param: pd.DataFrame, threads: int = 4) -> pd.DataFrame:
    """Return speedups over the original ordering for each reordering method."""
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


def speedup_histogram(df_param: pd.DataFrame, label: str, threads: int = 4) -> None:
    """Plot speedup histograms using the structural-compression panel style."""
    logging.info("Generating speedup histogram for %s...", label)
    speedups = _speedup_values(df_param, threads)
    if speedups.empty:
        logging.warning("Skipping speedup histogram for %s; no speedups", label)
        return

    lower = max(0.5, np.floor(speedups["speedup"].min() * 10.0) / 10.0)
    upper = max(1.6, np.ceil(speedups["speedup"].max() * 10.0) / 10.0)
    bins = np.linspace(lower, upper, 18)

    fig, axes = plt.subplots(1, len(METHODS), figsize=(DOUBLE_COLUMN_WIDTH, 2.35), sharey=True)
    for ax, method in zip(axes, METHODS):
        vals = speedups[speedups["reordering"] == method]["speedup"]
        ax.axvspan(0.95, 1.05, color=NEUTRAL_BAND, alpha=0.9, zorder=0)
        ax.hist(
            vals,
            bins=bins,
            histtype="step",
            linewidth=1.1,
            color=METHOD_COLORS[method],
        )
        ax.axvline(1.0, color=REFERENCE_COLOR, linestyle="--", linewidth=0.8)
        ax.axvline(
            vals.median(),
            color=METHOD_COLORS[method],
            linestyle=":",
            linewidth=0.9,
            alpha=0.85,
        )
        ax.set_xlim(lower, upper)
        ax.set_title(METHOD_LABELS[method])
        ax.set_xlabel(r"Speedup, $T_{\mathrm{orig}}/T_{\mathrm{reord}}$")
        paper_axes(ax, grid_axis="y")

    axes[0].set_ylabel("Matrices")
    fig.tight_layout()
    _save(f"speedup_histogram_{label}")


def structural_compression_histogram(df_metrics_param: pd.DataFrame, label: str) -> None:
    """Plot structural metric compression factors after reordering."""
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

    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COLUMN_WIDTH, 2.35), sharey=False)
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
                linewidth=1.1,
                color=METHOD_COLORS[method],
                label=METHOD_LABELS[method],
            )
        ax.axvline(1.0, color=REFERENCE_COLOR, linestyle="--", linewidth=0.8)
        ax.set_title(metric)
        ax.set_xlabel("Original / reordered")
        paper_axes(ax, grid_axis="y")

    axes[0].set_ylabel("Matrices")
    axes[-1].legend(loc="best")
    fig.tight_layout()
    _save(f"structural_compression_histogram_{label}")

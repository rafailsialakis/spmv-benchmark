"""Thesis-specific figure generators for benchmark analysis."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from utils.plotting.common import (
    DOUBLE_COLUMN_WIDTH,
    NEUTRAL_BAND,
    REFERENCE_COLOR,
    SINGLE_COLUMN_WIDTH,
    paper_axes,
    save_figure,
)


METHODS = ["rcm", "amd", "nd", "gp"]
METHOD_LABELS = {"rcm": "RCM", "amd": "AMD", "nd": "ND", "gp": "GP"}
METHOD_COLORS = {"rcm": "#3B6EA8", "amd": "#B45F2A", "nd": "#3D8B62", "gp": "#7A4E9C"}
OUTCOME_COLORS = {
    "Improved": "#4C8C5A",
    "Neutral": "#D8D8D8",
    "Regressed": "#B85C4C",
}


def _save(stem: str) -> None:
    """Save the current thesis figure as PDF and PNG."""
    save_figure("thesis", f"{stem}.pdf")
    save_figure("thesis", f"{stem}.png")
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


def _breakeven_long(
    df_spmv_param: pd.DataFrame,
    df_reorder_param: pd.DataFrame,
    threads: int = 4,
) -> pd.DataFrame:
    """Return break-even iterations for matrix-method pairs with positive runtime gain."""
    spmv = df_spmv_param[df_spmv_param["threads"] == threads].copy()
    pivot = spmv.pivot_table(index="matrix", columns="reordering", values="time_ms", aggfunc="mean")
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
    return pd.DataFrame(rows)


def preprocessing_breakeven_boxplot(
    df_spmv_param: pd.DataFrame,
    df_reorder_param: pd.DataFrame,
    label: str,
    threads: int = 4,
) -> None:
    """Plot preprocessing amortization as a compact boxplot."""
    logging.info("Generating thesis break-even boxplot for %s...", label)
    breakeven = _breakeven_long(df_spmv_param, df_reorder_param, threads)
    if breakeven.empty:
        logging.warning("Skipping break-even boxplot for %s; no positive gains", label)
        return

    fig, ax = plt.subplots(figsize=(SINGLE_COLUMN_WIDTH, 2.35))
    sns.boxplot(
        data=breakeven,
        x="reordering",
        y="iterations",
        hue="reordering",
        order=METHODS,
        hue_order=METHODS,
        palette=METHOD_COLORS,
        width=0.52,
        fliersize=1.9,
        linewidth=0.75,
        saturation=0.78,
        dodge=False,
        legend=False,
        ax=ax,
    )
    ax.axhline(100, color="#555555", linestyle=":", linewidth=0.75)
    ax.axhline(1000, color="#555555", linestyle=":", linewidth=0.75)
    ax.text(2.45, 100, r"$10^2$", ha="right", va="bottom", fontsize=6.5, color="#555555")
    ax.text(2.45, 1000, r"$10^3$", ha="right", va="bottom", fontsize=6.5, color="#555555")
    ax.set_yscale("log")
    ax.set_xlabel("")
    ax.set_ylabel("Break-even SpMV iterations")
    ax.set_xticks(range(len(METHODS)))
    ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS])
    paper_axes(ax, grid_axis="y")
    fig.tight_layout()
    _save(f"preprocessing_breakeven_boxplot_{label}")


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

    fig, ax = plt.subplots(figsize=(DOUBLE_COLUMN_WIDTH, 2.8))
    ax.axhspan(0.95, 1.05, color=NEUTRAL_BAND, alpha=0.85, zorder=0)
    sns.boxplot(
        data=speedups,
        x="category",
        y="speedup",
        hue="reordering",
        order=order,
        hue_order=METHODS,
        palette=METHOD_COLORS,
        width=0.65,
        fliersize=1.8,
        linewidth=0.75,
        saturation=0.78,
        ax=ax,
    )
    ax.axhline(1.0, color=REFERENCE_COLOR, linestyle="--", linewidth=0.8)
    ax.set_xlabel("Matrix category")
    ax.set_ylabel(r"Speedup, $T_{\mathrm{orig}}/T_{\mathrm{reord}}$")
    ax.tick_params(axis="x", labelrotation=20)
    for tick in ax.get_xticklabels():
        tick.set_ha("right")
    paper_axes(ax, grid_axis="y")

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles[:len(METHODS)],
        [METHOD_LABELS[m] for m in METHODS],
        ncol=len(METHODS),
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        handlelength=1.3,
        columnspacing=1.0,
    )
    fig.tight_layout()
    _save(f"category_speedup_distribution_{label}")


def outcome_fraction_bars(df_param: pd.DataFrame, label: str, threads: int = 4) -> None:
    """Plot the fraction of matrices improved, neutral, or regressed by method."""
    logging.info("Generating thesis outcome fraction plot for %s...", label)
    speedups = _speedup_long(df_param, threads)
    if speedups.empty:
        logging.warning("Skipping outcome fraction plot for %s; no speedups", label)
        return

    rows = []
    for method in METHODS:
        values = speedups[speedups["reordering"] == method]["speedup"].dropna()
        total = len(values)
        if total == 0:
            continue
        rows.append(
            {
                "reordering": method,
                "Improved": (values > 1.05).sum() / total,
                "Neutral": ((values >= 0.95) & (values <= 1.05)).sum() / total,
                "Regressed": (values < 0.95).sum() / total,
                "total": total,
            }
        )
    fractions = pd.DataFrame(rows)
    if fractions.empty:
        logging.warning("Skipping outcome fraction plot for %s; no complete methods", label)
        return

    fig, ax = plt.subplots(figsize=(SINGLE_COLUMN_WIDTH, 2.2))
    y_pos = np.arange(len(fractions))
    left = np.zeros(len(fractions))
    for outcome in ["Improved", "Neutral", "Regressed"]:
        values = fractions[outcome].to_numpy()
        ax.barh(
            y_pos,
            values,
            left=left,
            height=0.52,
            color=OUTCOME_COLORS[outcome],
            edgecolor="white",
            linewidth=0.6,
            label=outcome,
        )
        for idx, value in enumerate(values):
            if value < 0.11:
                continue
            x = left[idx] + value / 2.0
            text_color = "white" if outcome != "Neutral" else "#222222"
            ax.text(
                x,
                y_pos[idx],
                rf"{value * 100:.0f}\%",
                ha="center",
                va="center",
                fontsize=6.4,
                color=text_color,
            )
        left += values

    ax.set_yticks(y_pos)
    ax.set_yticklabels([METHOD_LABELS[m] for m in fractions["reordering"]])
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel(r"Fraction of matrices (\%)")
    ax.set_xticks(np.linspace(0.0, 1.0, 6))
    ax.set_xticklabels([f"{value:.0f}" for value in np.linspace(0, 100, 6)])
    ax.invert_yaxis()
    paper_axes(ax, grid_axis="x")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.22),
        ncol=3,
        columnspacing=0.9,
        handlelength=1.2,
    )
    fig.tight_layout()
    _save(f"outcome_fraction_bars_{label}")


def best_reordering_agreement(
    df_x86_param: pd.DataFrame,
    df_arm_param: pd.DataFrame,
    threads: int = 4,
) -> None:
    """Plot agreement between the best x86 and ARM reordering choices."""
    logging.info("Generating thesis best-reordering agreement plot...")
    x86 = _speedup_long(df_x86_param, threads).rename(columns={"speedup": "x86_speedup"})
    arm = _speedup_long(df_arm_param, threads).rename(columns={"speedup": "arm_speedup"})
    paired = x86.merge(arm, on=["matrix", "category", "reordering"], how="inner")
    if paired.empty:
        logging.warning("Skipping best-reordering agreement plot; no paired rows")
        return

    wide = paired.pivot_table(
        index=["matrix", "category"],
        columns="reordering",
        values=["x86_speedup", "arm_speedup"],
    )
    best = pd.DataFrame(index=wide.index)
    best["x86"] = wide["x86_speedup"].idxmax(axis=1)
    best["arm"] = wide["arm_speedup"].idxmax(axis=1)
    best["arm_best"] = wide["arm_speedup"].max(axis=1)
    arm_speedups = wide["arm_speedup"]
    best["arm_using_x86_choice"] = [
        arm_speedups.loc[idx, method] for idx, method in best["x86"].items()
    ]
    practical = (best["arm_using_x86_choice"] >= 0.95 * best["arm_best"]).mean()

    # Reverse direction: use the ARM-best method on x86.
    x86_speedups = wide["x86_speedup"]
    best["x86_best"] = x86_speedups.max(axis=1)
    best["x86_using_arm_choice"] = [
        x86_speedups.loc[idx, method] for idx, method in best["arm"].items()
    ]
    practical_reverse = (best["x86_using_arm_choice"] >= 0.95 * best["x86_best"]).mean()
    logging.info(
        "Portability within 5%%: x86->ARM %.1f%% (%d/%d), ARM->x86 %.1f%% (%d/%d)",
        practical * 100.0, int(round(practical * len(best))), len(best),
        practical_reverse * 100.0, int(round(practical_reverse * len(best))), len(best),
    )
    print(f"x86->ARM: {practical:.3f}  ARM->x86: {practical_reverse:.3f}")

    counts = pd.crosstab(best["x86"], best["arm"]).reindex(index=METHODS, columns=METHODS, fill_value=0)
    fig, ax = plt.subplots(figsize=(SINGLE_COLUMN_WIDTH, 2.7))
    sns.heatmap(
        counts,
        annot=True,
        fmt="d",
        cmap="Greys",
        cbar=False,
        linewidths=0.5,
        linecolor="white",
        square=True,
        ax=ax,
        annot_kws={"fontsize": 8},
    )
    ax.set_xlabel("Best on ARM")
    ax.set_ylabel("Best on x86")
    ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS], rotation=0)
    ax.set_yticklabels([METHOD_LABELS[m] for m in METHODS], rotation=0)
    ax.set_title("Best-reordering agreement")
    ax.text(
        0.0,
        -0.24,
        rf"x86 choice within 5\% of ARM best: {practical * 100.0:.1f}\%",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.5,
    )
    fig.tight_layout()
    _save("best_reordering_agreement")


def cache_miss_ratio_summary(df_cache_param: pd.DataFrame, label: str) -> None:
    """Plot reordered-to-original cache miss ratios by cache level."""
    logging.info("Generating thesis cache miss ratio summary for %s...", label)
    rows = []
    cache_levels = [
        ("L1_misses", "L1"),
        ("L2_misses", "L2"),
        ("L3_misses", "L3"),
    ]
    df = df_cache_param.copy()
    for level, level_label in cache_levels:
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
                        "level": level_label,
                        "ratio": (pivot[method] / base).to_numpy(),
                    }
                )
            )
    ratios = pd.concat(rows, ignore_index=True).dropna() if rows else pd.DataFrame()
    if ratios.empty:
        logging.warning("Skipping cache ratio summary for %s; no ratios", label)
        return

    levels = [level for _, level in cache_levels if level in ratios["level"].unique()]
    fig, axes = plt.subplots(1, len(levels), figsize=(DOUBLE_COLUMN_WIDTH, 2.35), sharey=True)
    axes = np.atleast_1d(axes)
    for panel, (ax, level) in enumerate(zip(axes, levels)):
        part = ratios[ratios["level"] == level]
        sns.boxplot(
            data=part,
            x="reordering",
            y="ratio",
            hue="reordering",
            order=METHODS,
            hue_order=METHODS,
            palette=METHOD_COLORS,
            fliersize=1.8,
            linewidth=0.75,
            saturation=0.78,
            dodge=False,
            legend=False,
            ax=ax,
        )
        ax.axhline(1.0, color=REFERENCE_COLOR, linestyle="--", linewidth=0.8)
        ax.set_yscale("log")
        ax.set_title(f"({chr(97 + panel)}) {level}")
        ax.set_xlabel("")
        ax.set_xticks(range(len(METHODS)))
        ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS])
        paper_axes(ax, grid_axis="y")

    axes[0].set_ylabel("Reordered / original cache misses")
    for ax in axes[1:]:
        ax.set_ylabel("")
    fig.tight_layout()
    _save(f"cache_miss_ratio_summary_{label}")


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

    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN_WIDTH, 2.45), sharey=True)
    for panel, (ax, counter) in enumerate(zip(axes, ["DTLB", "ITLB"])):
        part = ratios[ratios["counter"] == counter].copy()
        sns.boxplot(
            data=part,
            x="reordering",
            y="ratio",
            hue="reordering",
            order=METHODS,
            hue_order=METHODS,
            palette=METHOD_COLORS,
            fliersize=1.8,
            linewidth=0.75,
            saturation=0.78,
            dodge=False,
            legend=False,
            ax=ax,
        )
        ax.axhline(1.0, color=REFERENCE_COLOR, linestyle="--", linewidth=0.8)
        ax.set_yscale("log")
        ax.set_title(f"({chr(97 + panel)}) {counter}")
        ax.set_xlabel("")
        ax.set_xticks(range(len(METHODS)))
        ax.set_xticklabels([METHOD_LABELS[m] for m in METHODS])
        paper_axes(ax, grid_axis="y")

    axes[0].set_ylabel("Reordered / original TLB misses")
    axes[1].set_ylabel("")
    fig.tight_layout()
    _save(f"tlb_ratio_summary_{label}")


def methodology_fraction_scatter(
    df_cold: pd.DataFrame,
    df_ios: pd.DataFrame,
    df_rax: pd.DataFrame,
    label: str,
    threads: int = 4,
) -> None:
    """Plot methodology variation as fraction-of-matrices curves."""
    logging.info("Generating thesis methodology fraction plot for %s...", label)
    frames = []
    for name, df in [("Cold", df_cold), ("IO-swap", df_ios), ("RAx", df_rax)]:
        part = df[
            (df["threads"] == threads) &
            (df["reordering"] == "none")
        ][["matrix", "category", "gflops"]].copy()
        part["methodology"] = name
        frames.append(part)
    merged = pd.concat(frames, ignore_index=True)
    pivot = merged.pivot_table(index=["matrix", "category"], columns="methodology", values="gflops")
    if "RAx" not in pivot.columns:
        logging.warning("Skipping methodology fraction plot for %s; missing RAx baseline", label)
        return
    available = [name for name in ["Cold", "IO-swap"] if name in pivot.columns]
    if not available:
        logging.warning("Skipping methodology fraction plot for %s; no comparison methodology columns", label)
        return

    deltas = pivot[available].sub(pivot["RAx"], axis=0).div(pivot["RAx"], axis=0) * 100.0
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
        logging.warning("Skipping methodology fraction plot for %s; no comparable rows", label)
        return

    fig, ax = plt.subplots(figsize=(SINGLE_COLUMN_WIDTH, 2.45))
    ax.axvspan(-5, 5, color=NEUTRAL_BAND, alpha=0.85, zorder=0)
    colors = {"Cold": "#4A6FA5", "IO-swap": "#9A6B39"}
    for methodology in available:
        values = long[long["methodology"] == methodology]["delta"].dropna().sort_values()
        if values.empty:
            continue
        fraction = np.arange(1, len(values) + 1) / len(values)
        ax.plot(values, fraction, color=colors[methodology], linewidth=1.0, alpha=0.9, label=methodology)

    ax.axvline(0.0, color=REFERENCE_COLOR, linestyle="--", linewidth=0.8)
    ax.set_xlabel(r"GFLOP/s difference from RAx (\%)")
    ax.set_ylabel("Fraction of matrices")
    ax.set_ylim(0.0, 1.02)
    ax.set_yticks(np.linspace(0.0, 1.0, 6))
    ax.legend(loc="lower right", handletextpad=0.3)
    paper_axes(ax, grid_axis="both")
    fig.tight_layout()
    _save(f"methodology_fraction_scatter_{label}")

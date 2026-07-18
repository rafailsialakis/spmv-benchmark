"""Shared helpers for publication-quality generated figures."""

from pathlib import Path

import matplotlib.pyplot as plt

FIGURES_DIR = Path("figures")
SINGLE_COLUMN_WIDTH = 3.35
DOUBLE_COLUMN_WIDTH = 6.9
PAPER_DPI = 600

GRID_COLOR = "#E2E2E2"
REFERENCE_COLOR = "#222222"
NEUTRAL_BAND = "#F1F1F1"
TEXT_COLOR = "#1F1F1F"


def save_figure(category: str, filename: str, **kwargs) -> None:
    """Save the current Matplotlib figure under the configured category."""
    output_dir = FIGURES_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)

    save_kwargs = {
        "bbox_inches": "tight",
        "pad_inches": 0.02,
        "metadata": {"Creator": "spmv-benchmark"},
    }
    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        save_kwargs["dpi"] = PAPER_DPI
    save_kwargs.update(kwargs)

    plt.savefig(output_dir / filename, **save_kwargs)


def paper_axes(ax, grid_axis: str | None = "y") -> None:
    """Apply common paper-figure axis styling."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(TEXT_COLOR)
    ax.spines[["left", "bottom"]].set_linewidth(0.65)
    ax.tick_params(axis="both", which="major", width=0.65, length=3.0, pad=2, colors=TEXT_COLOR)
    ax.tick_params(axis="both", which="minor", width=0.45, length=2.0, colors=TEXT_COLOR)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID_COLOR, linestyle="-", linewidth=0.45)
        ax.set_axisbelow(True)

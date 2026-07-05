"""Shared helpers for writing generated figures."""

from pathlib import Path

import matplotlib.pyplot as plt

FIGURES_DIR = Path("figures")


def save_figure(category: str, filename: str, **kwargs) -> None:
    """Save the current Matplotlib figure under the configured category."""
    output_dir = FIGURES_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / filename, **kwargs)

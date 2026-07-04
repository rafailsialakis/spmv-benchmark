from utils.plotting.barcharts import arm_x86_comp, win_loss_summary
from utils.plotting.faceted import cache_plot, cache_plot_normalized, tlb_plot
from utils.plotting.heatmaps import speedup_heatmap
from utils.plotting.sparsity import sparse_plot
from utils.plotting.tables import (
    breakeven_table,
    matrix_characteristics_table,
    methodology_table,
    scaling_table,
)

__all__ = [
    "arm_x86_comp",
    "breakeven_table",
    "cache_plot",
    "cache_plot_normalized",
    "matrix_characteristics_table",
    "methodology_table",
    "sparse_plot",
    "speedup_heatmap",
    "scaling_table",
    "tlb_plot",
    "win_loss_summary",
]

"""Public plotting and table-generation utilities."""

from utils.plotting.barcharts import arm_x86_comp, win_loss_summary
from utils.plotting.overview import cache_reduction_overview, speedup_ecdf, tlb_reduction_overview
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
    "cache_reduction_overview",
    "matrix_characteristics_table",
    "methodology_table",
    "sparse_plot",
    "speedup_ecdf",
    "scaling_table",
    "tlb_reduction_overview",
    "win_loss_summary",
]

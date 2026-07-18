"""Public plotting and table-generation utilities."""

from utils.plotting.distributions import speedup_histogram, structural_compression_histogram
from utils.plotting.sparsity import sparse_plot
from utils.plotting.tables import (
    breakeven_table,
    matrix_characteristics_table,
    methodology_table,
    scaling_table,
)

__all__ = [
    "breakeven_table",
    "matrix_characteristics_table",
    "methodology_table",
    "sparse_plot",
    "scaling_table",
    "speedup_histogram",
    "structural_compression_histogram",
]

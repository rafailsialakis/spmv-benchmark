"""Public plotting and table-generation utilities."""

from utils.plotting.distributions import speedup_histogram, structural_compression_histogram
from utils.plotting.sparsity import sparse_plot
from utils.plotting.tables import matrix_characteristics_table

__all__ = [
    "matrix_characteristics_table",
    "sparse_plot",
    "speedup_histogram",
    "structural_compression_histogram",
]

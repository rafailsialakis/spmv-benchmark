"""LaTeX table generators for benchmark results."""

import logging
from pathlib import Path

import pandas as pd

TABLES_DIR = Path("figures") / "tables"


def write_table(filename: str, tex: str) -> None:
    """Write a generated LaTeX table into the tables output directory."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    with open(TABLES_DIR / filename, 'w') as f:
        f.write(tex)


def tex_escape(value) -> str:
    """Escape values for use in simple LaTeX table cells."""
    return str(value).replace('_', r'\_')


def matrix_characteristics_table(df_metrics: pd.DataFrame):
    """Write a LaTeX table of matrix structural characteristics."""
    
    cols = {
        'matrix':       'Matrix',
        'category':     'Category',
        'n':            r'$n$',
        'nnz':          r'nnz',
        'avg_nnz_row':  r'avg nnz/row',
        'lb':           r'lb',
        'bw':           r'Bandwidth',
    }

    df = df_metrics[list(cols.keys())].copy()
    df = df.sort_values('category')

    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'  \centering')
    lines.append(r'  \caption{Structural characteristics of the benchmark matrices.}')
    lines.append(r'  \label{tab:matrix_characteristics}')
    lines.append(r'  \resizebox{\textwidth}{!}{%')
    lines.append(r'  \begin{tabular}{llrrrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    ' + ' & '.join([rf'\textbf{{{v}}}' for v in cols.values()]) + r' \\')
    lines.append(r'    \midrule')

    prev_cat = None
    for _, row in df.iterrows():
        if prev_cat and prev_cat != row['category']:
            lines.append(r'    \midrule')
        
        mat     = tex_escape(row['matrix'])
        cat     = row['category']
        n       = f"{int(row['n']):,}"
        nnz     = f"{int(row['nnz']):,}"
        avg     = f"{row['avg_nnz_row']:.2f}"
        lb      = f"{row['lb']:.2f}"
        bw      = f"{int(row['bw']):,}"

        lines.append(
            rf'    {mat} & {cat} & {n} & {nnz} & {avg} & {lb} & {bw}\\'
        )
        prev_cat = row['category']

    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}}')
    lines.append(r'\end{table}')

    tex = '\n'.join(lines)
    write_table('matrix_characteristics.tex', tex)

    logging.info(f"Table was saved successfully in figures/tables/matrix_characteristics.tex")

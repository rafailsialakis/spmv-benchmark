import pandas as pd
import logging
"""
Produces a LaTeX table with break-even iterations needed 

Args:
    path (str): The path from spmv_benchmark to the .mtx file

Returns:
    None

Note:
    In order to run correctly the permutation vectors must be saved/updated for the given matrix
"""
def breakeven_table(df_spmv: pd.DataFrame, df_reorder: pd.DataFrame, label: str):
    logging.info(f"Generating breakeven table for {label} architecture...")
    # Keep lines with 4 threads
    spmv = df_spmv[df_spmv['threads'] == 4].copy()

    # Pivot with time_ms on z-axis
    spmv_pivot = spmv.pivot_table(
        index='matrix', columns='reordering', values='time_ms'
    )

    results = []
    for _, row in df_reorder.iterrows():
        matrix = row['matrix']
        reorder = row['reordering']
        if matrix not in spmv_pivot.index:
            continue

        time_none_s      = spmv_pivot.loc[matrix, 'none'] / 1000
        time_reordered_s = spmv_pivot.loc[matrix, reorder] / 1000
        gain             = time_none_s - time_reordered_s

        if gain <= 0:
            be = r'\textit{slow}'
        else:
            val = row['time_s'] / gain
            be = r'$>$10000' if val >= 10000 else str(round(val))

        results.append({'matrix': matrix, 'reordering': reorder, 'breakeven': be})

    df_be = pd.DataFrame(results)
    df_pivot = df_be.pivot(index='matrix', columns='reordering', values='breakeven')

    # Is used to sort based on smallest RCM break-even
    def sort_key(val):
        try:
            return int(val)
        except:
            return 99999
    
    df_pivot['_sort'] = df_pivot['rcm'].apply(sort_key)
    df_pivot = df_pivot.sort_values('_sort').drop(columns='_sort')

    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'  \centering')
    lines.append(rf'  \label{{tab:breakeven_{label.lower()}}}')
    lines.append(r'  \begin{tabular}{lrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    \textbf{Matrix} & \textbf{RCM} & \textbf{AMD} & \textbf{METIS} \\')
    lines.append(r'    \midrule')

    for matrix, row in df_pivot.iterrows():
        rcm   = row.get('rcm',   r'--')
        amd   = row.get('amd',   r'--')
        nd = row.get('nd', r'--')
        mat_tex = matrix.replace('_', r'\_')
        lines.append(rf'    {mat_tex} & {rcm} & {amd} & {nd} \\')

    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table}')

    tex = '\n'.join(lines)
    # Save file
    path = f'plot/figures/breakeven_table_{label}.tex'
    with open(path, 'w') as f:
        f.write(tex)
    logging.info(f"breakeven_table_{label}.tex was saved successfully!")

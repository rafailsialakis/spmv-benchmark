import logging
import pandas as pd

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
    logging.info(f"Table was saved successfully in plot/figures/breakeven_table_{label}.tex")

"""
Produces a LaTeX table with some matrix characteristics 
(matrix, category, n, nnz, avg_nnz_row, lb, bw) 

Args:
    df_metrics (pd.DataFrame): DataFrame that contains all the matrices' metrics

Returns:
    None

"""
def matrix_characteristics_table(df_metrics: pd.DataFrame):
    
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
    lines.append(r'  \label{tab:matrix_characteristics}')
    lines.append(r'  \resizebox{\textwidth}{!}{%')
    lines.append(r'  \begin{tabular}{llrrrrrrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    ' + ' & '.join([rf'\textbf{{{v}}}' for v in cols.values()]) + r' \\')
    lines.append(r'    \midrule')

    prev_cat = None
    for _, row in df.iterrows():
        if prev_cat and prev_cat != row['category']:
            lines.append(r'    \midrule')
        
        mat     = row['matrix'].replace('_', r'\_')
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
    path = 'plot/figures/matrix_characteristics.tex'
    with open(path, 'w') as f:
        f.write(tex)

    logging.info(f"Table was saved successfully in plot/figures/matrix_characteristics.tex")

"""
Produces a LaTeX table that visualizes how threading scales speedup 

Args:
    df_spmv (pd:DataFrame): Execution times of SPMxV
    label (str): System architecture (x86 | ARM)

Returns:
    None

"""
def scaling_table(df_spmv: pd.DataFrame, label: str):

    matrices = ['nv2', 'circuit5M', 'audikw_1', 'kkt_power', 'Flan_1565']
    reorderings = ['none', 'rcm', 'amd', 'nd']
    threads = [1, 2, 4]

    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'  \centering')
    lines.append(rf'  \label{{tab:scaling_{label.lower()}}}')
    lines.append(r'  \begin{tabular}{llrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    \textbf{Matrix} & \textbf{Reordering} & \textbf{1T} & \textbf{2T} & \textbf{4T} \\')
    lines.append(r'    \midrule')

    for matrix in matrices:
        df_mat = df_spmv[df_spmv['matrix'] == matrix].copy()
        if df_mat.empty:
            continue

        first = True
        for reorder in reorderings:
            df_r = df_mat[df_mat['reordering'] == reorder].sort_values('threads')
            if df_r.empty:
                continue

            base = df_r[df_r['threads'] == 1]['time_ms'].values
            if len(base) == 0:
                continue
            base = base[0]

            speedups = []
            for t in threads:
                row = df_r[df_r['threads'] == t]['time_ms'].values
                if len(row) == 0:
                    speedups.append('--')
                else:
                    speedups.append(f'{base/row[0]:.2f}')

            mat_tex = matrix.replace('_', r'\_') if first else ''
            reorder_tex = reorder.upper()
            lines.append(
                rf'    {mat_tex} & {reorder_tex} & {speedups[0]} & {speedups[1]} & {speedups[2]} \\'
            )
            first = False

        lines.append(r'    \midrule')

    lines[-1] = r'    \bottomrule'
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table}')

    tex = '\n'.join(lines)
    path = f'plot/figures/scaling_table_{label}.tex'
    with open(path, 'w') as f:
        f.write(tex)
    logging.info(f"Table was saved successfully in plot/figures/scaling_table_{label}.tex")

"""
Produces a LaTeX table that shows time taken by each measuring methodology in
order to demonstrate that the methodology does not provide any significant 
difference in our benchmark 

Args:
    df_cold (pd:DataFrame): Cold execution times of SPMxV
    df_ios (pd:DataFrame): Repeated Ax execution times of SPMxV
    df_rax (pd:DataFrame): Inupt Output swapped execution times of SPMxV
    label (str): System architecture (x86 | ARM)

Returns:
    None

"""
def methodology_table(df_cold: pd.DataFrame, df_ios: pd.DataFrame, df_rax: pd.DataFrame, label: str):

    matrices = ['nv2', 'audikw_1', 'Flan_1565', 'thermal2', 'circuit5M']

    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'  \centering')
    lines.append(rf'  \label{{tab:methodology_{label.lower()}}}')
    lines.append(r'  \begin{tabular}{lrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    \textbf{Matrix} & \textbf{COLD} & \textbf{IOS} & \textbf{RAX} \\')
    lines.append(r'    \midrule')

    for matrix in matrices:
        def get_val(df):
            row = df[
                (df['matrix'] == matrix) &
                (df['threads'] == 4) &
                (df['reordering'] == 'none')
            ]
            return f"{row['time_ms'].mean():.3f}" if not row.empty else '--'

        mat_tex = matrix.replace('_', r'\_')
        cold = get_val(df_cold)
        ios  = get_val(df_ios)
        rax  = get_val(df_rax)

        lines.append(rf'    {mat_tex} & {cold} & {ios} & {rax} \\')

    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table}')

    tex = '\n'.join(lines)
    path = f'plot/figures/methodology_table_{label}.tex'
    with open(path, 'w') as f:
        f.write(tex)

    logging.info(f"Table was saved successfully in plot/figures/methodology_table_{label}.tex")

import logging
from pathlib import Path
import pandas as pd

TABLES_DIR = Path("figures") / "tables"

def write_table(filename: str, tex: str) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    with open(TABLES_DIR / filename, 'w') as f:
        f.write(tex)

def tex_escape(value) -> str:
    return str(value).replace('_', r'\_')

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
            be = r'\textit{ - }'
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
    lines.append(rf'  \caption{{Break-even SpMV iterations after reordering on {label}. A dash means the reordered SpMV was not faster than the original ordering.}}')
    lines.append(rf'  \label{{tab:breakeven_{label.lower()}}}')
    lines.append(r'  \begin{tabular}{lrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    \textbf{Matrix} & \textbf{AMD} & \textbf{ND} & \textbf{RCM}  \\')
    lines.append(r'    \midrule')

    for matrix, row in df_pivot.iterrows():
        rcm   = row.get('rcm',   r'--')
        amd   = row.get('amd',   r'--')
        nd = row.get('nd', r'--')
        mat_tex = tex_escape(matrix)
        lines.append(rf'    {mat_tex} & {amd} & {nd} & {rcm} \\')

    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table}')

    tex = '\n'.join(lines)
    # Save file
    write_table(f'breakeven_table_{label}.tex', tex)
    logging.info(f"Table was saved successfully in figures/tables/breakeven_table_{label}.tex")

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
    lines.append(rf'  \caption{{Thread scaling normalized to the one-thread runtime for each matrix and reordering on {label}.}}')
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

            mat_tex = tex_escape(matrix) if first else ''
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
    write_table(f'scaling_table_{label}.tex', tex)
    logging.info(f"Table was saved successfully in figures/tables/scaling_table_{label}.tex")

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

    preferred = ['nv2', 'audikw_1', 'Flan_1565', 'thermal2', 'circuit5M', 'crystk01', 's3rmt3m3']
    available = set(df_rax[(df_rax['threads'] == 4) & (df_rax['reordering'] == 'none')]['matrix'])
    matrices = [matrix for matrix in preferred if matrix in available]
    if len(matrices) < 7:
        extras = (
            df_rax[(df_rax['threads'] == 4) & (df_rax['reordering'] == 'none')]
            .sort_values('time_ms', ascending=False)['matrix']
            .tolist()
        )
        matrices.extend([matrix for matrix in extras if matrix not in matrices][:7 - len(matrices)])

    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'  \centering')
    lines.append(rf'  \caption{{GFLOP/s comparison of measurement methodologies on {label} using the original matrix ordering.}}')
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
            return f"{row['gflops'].mean():.3f}" if not row.empty else '--'

        mat_tex = tex_escape(matrix)
        cold = get_val(df_cold)
        ios  = get_val(df_ios)
        rax  = get_val(df_rax)

        lines.append(rf'    {mat_tex} & {cold} & {ios} & {rax} \\')

    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table}')

    tex = '\n'.join(lines)
    write_table(f'methodology_table_{label}.tex', tex)

    logging.info(f"Table was saved successfully in figures/tables/methodology_table_{label}.tex")

def thesis_aggregate_table(df_spmv: pd.DataFrame, df_cache: pd.DataFrame, df_tlb: pd.DataFrame, label: str):
    logging.info(f"Generating thesis aggregate table for {label} architecture...")
    spmv = df_spmv[df_spmv['threads'] == 4].copy()
    pivot = spmv.pivot_table(
        index=['matrix', 'category'], columns='reordering', values='time_ms'
    )

    rows = []
    for method in ['rcm', 'amd', 'nd']:
        if method not in pivot.columns or 'none' not in pivot.columns:
            continue
        speedup = pivot['none'] / pivot[method]
        wins = int((speedup > 1.05).sum())
        neutral = int(((speedup >= 0.95) & (speedup <= 1.05)).sum())
        losses = int((speedup < 0.95).sum())

        cache_l2 = '--'
        if df_cache is not None and 'L2_misses' in df_cache.columns:
            cache_pivot = df_cache.pivot_table(
                index='matrix', columns='reordering', values='L2_misses'
            )
            if method in cache_pivot.columns and 'none' in cache_pivot.columns:
                base = cache_pivot['none'].replace(0, pd.NA)
                cache_l2 = f"{((base - cache_pivot[method]) / base * 100).median():.1f}"

        dtlb_ratio = '--'
        if df_tlb is not None and 'dtlb_load_misses' in df_tlb.columns:
            tlb_pivot = df_tlb.pivot_table(
                index='matrix', columns='reordering', values='dtlb_load_misses'
            )
            if method in tlb_pivot.columns and 'none' in tlb_pivot.columns:
                base = tlb_pivot['none'].replace(0, pd.NA)
                dtlb_ratio = f"{(tlb_pivot[method] / base).median():.2f}"

        rows.append({
            'method': method.upper(),
            'median_speedup': f"{speedup.median():.2f}",
            'best_speedup': f"{speedup.max():.2f}",
            'wins': wins,
            'neutral': neutral,
            'losses': losses,
            'median_l2': cache_l2,
            'median_dtlb_ratio': dtlb_ratio,
        })

    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'  \centering')
    lines.append(rf'  \caption{{Aggregate reordering outcomes on {label}. Wins and losses use a $\pm5\%$ neutral band.}}')
    lines.append(rf'  \label{{tab:thesis_aggregate_{label.lower()}}}')
    lines.append(r'  \begin{tabular}{lrrrrrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    \textbf{Method} & \textbf{Median speedup} & \textbf{Best speedup} & \textbf{Wins} & \textbf{Neutral} & \textbf{Losses} & \textbf{Median L2 red. (\%)} & \textbf{Median DTLB ratio} \\')
    lines.append(r'    \midrule')
    for row in rows:
        lines.append(
            rf"    {row['method']} & {row['median_speedup']} & {row['best_speedup']} & {row['wins']} & {row['neutral']} & {row['losses']} & {row['median_l2']} & {row['median_dtlb_ratio']} \\"
        )
    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table}')

    write_table(f'thesis_aggregate_table_{label}.tex', '\n'.join(lines))
    logging.info(f"Table was saved successfully in figures/tables/thesis_aggregate_table_{label}.tex")

def thesis_best_reordering_table(df_spmv: pd.DataFrame, df_reorder: pd.DataFrame, label: str):
    logging.info(f"Generating thesis best-reordering table for {label} architecture...")
    spmv = df_spmv[df_spmv['threads'] == 4].copy()
    pivot = spmv.pivot_table(
        index=['matrix', 'category'], columns='reordering', values='time_ms'
    )

    rows = []
    for matrix, category in pivot.index:
        if 'none' not in pivot.columns:
            continue
        speedups = {
            method: pivot.loc[(matrix, category), 'none'] / pivot.loc[(matrix, category), method]
            for method in ['rcm', 'amd', 'nd']
            if method in pivot.columns
        }
        if not speedups:
            continue
        best_method = max(speedups, key=speedups.get)
        best_speedup = speedups[best_method]
        base_ms = pivot.loc[(matrix, category), 'none']
        best_ms = pivot.loc[(matrix, category), best_method]
        gain_s = (base_ms - best_ms) / 1000
        reorder_row = df_reorder[
            (df_reorder['matrix'] == matrix) &
            (df_reorder['reordering'] == best_method)
        ]
        if gain_s <= 0 or reorder_row.empty:
            breakeven = r'--'
        else:
            val = reorder_row['time_s'].iloc[0] / gain_s
            breakeven = r'$>$10000' if val >= 10000 else f"{round(val)}"
        rows.append({
            'matrix': matrix,
            'category': category,
            'best_method': best_method.upper(),
            'best_speedup': best_speedup,
            'rcm': speedups.get('rcm'),
            'amd': speedups.get('amd'),
            'nd': speedups.get('nd'),
            'breakeven': breakeven,
        })

    rows = sorted(rows, key=lambda row: row['best_speedup'], reverse=True)

    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'  \centering')
    lines.append(rf'  \caption{{Best observed reordering per matrix on {label}. Break-even is reported only when the best reordered SpMV is faster than the original ordering.}}')
    lines.append(rf'  \label{{tab:thesis_best_reordering_{label.lower()}}}')
    lines.append(r'  \resizebox{\textwidth}{!}{%')
    lines.append(r'  \begin{tabular}{lllrrrrr}')
    lines.append(r'    \toprule')
    lines.append(r'    \textbf{Matrix} & \textbf{Category} & \textbf{Best} & \textbf{Best speedup} & \textbf{RCM} & \textbf{AMD} & \textbf{ND} & \textbf{Break-even} \\')
    lines.append(r'    \midrule')
    for row in rows:
        lines.append(
            rf"    {tex_escape(row['matrix'])} & {row['category']} & {row['best_method']} & {row['best_speedup']:.2f} & {row['rcm']:.2f} & {row['amd']:.2f} & {row['nd']:.2f} & {row['breakeven']} \\"
        )
    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}}')
    lines.append(r'\end{table}')

    write_table(f'thesis_best_reordering_table_{label}.tex', '\n'.join(lines))
    logging.info(f"Table was saved successfully in figures/tables/thesis_best_reordering_table_{label}.tex")

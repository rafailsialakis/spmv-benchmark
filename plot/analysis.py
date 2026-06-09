from utils import io
from utils import plots
from utils import tables

def generate_plots(df_rax_x86, df_ios_x86, df_cold_x86,df_rax_arm, df_cold_arm, df_cache_x86, df_cache_arm, df_tlb_x86, df_tlb_arm, df_metrics):
    #plots.sparse_plot("matrices/Circuit/nv2.mtx")
    plots.speedup_heatmap(df_rax_x86, "x86")
    plots.speedup_heatmap(df_rax_arm, "ARM") 
    plots.win_loss_summary(df_rax_x86, "x86")
    plots.win_loss_summary(df_rax_arm, "ARM")
    plots.cache_plot(df_cache_x86, "x86")
    plots.cache_plot_normalized(df_cache_x86, 'x86', df_metrics)
    plots.cache_plot(df_cache_arm, "ARM")
    plots.cache_plot_normalized(df_cache_arm, 'ARM', df_metrics)
    plots.arm_x86_comp(df_cold_x86, df_cold_arm)
    plots.tlb_plot(df_tlb_x86, "x86")
    plots.tlb_plot(df_tlb_arm, "ARM")

def generate_tables(df_rax_x86, df_ios_x86, df_cold_x86, df_rax_arm, df_ios_arm, df_cold_arm, df_reorder_x86, df_reorder_arm, df_metrics):
    tables.scaling_table(df_rax_x86, "x86")
    tables.scaling_table(df_rax_arm, "ARM")
    tables.methodology_table(df_cold_x86, df_rax_x86, df_ios_x86, "x86")
    tables.methodology_table(df_cold_arm, df_rax_arm, df_ios_arm, "ARM")
    tables.breakeven_table(df_rax_x86, df_reorder_x86, 'x86')
    tables.breakeven_table(df_rax_arm, df_reorder_arm, 'ARM')
    tables.matrix_characteristics_table(df_metrics)

def main():
    io.init_logging()
    io.init_plt()

    (df_metrics,
     df_cold_x86, df_ios_x86, df_rax_x86, df_reorder_x86,
     df_cold_arm,  df_ios_arm,  df_rax_arm,  df_reorder_arm,
     df_cache_x86, df_cache_arm,
     df_tlb_x86,   df_tlb_arm) = io.read_files()
 
    generate_plots(df_rax_x86, df_ios_x86, df_cold_x86,
                   df_rax_arm,  df_cold_arm,
                   df_cache_x86, df_cache_arm,
                   df_tlb_x86,   df_tlb_arm,
                   df_metrics)
    
    generate_tables(df_rax_x86, df_ios_x86, df_cold_x86, 
                    df_rax_arm, df_ios_arm, 
                    df_cold_arm, df_reorder_x86, 
                    df_reorder_arm, df_metrics)

if __name__ == '__main__':
    main()
from utils import io
from utils import plots
from utils import tables

def main():
    io.init_plt()

    df_metrics,df_cold_x86,df_ios_x86,df_rax_x86,df_reorder_x86,df_cold_arm,df_ios_arm,df_rax_arm,df_reorder_arm = io.read_files()
    
    #plots.sparse_plot("matrices/Circuit/nv2.mtx")
    #plots.speedup_heatmap(df_rax_arm, "ARM")
    #plots.speedup_heatmap(df_rax_x86, "x86")
    plots.arm_x86_comp(df_cold_x86, df_cold_arm)
    #tables.breakeven_table(df_rax_arm, df_reorder_arm, 'ARM')
    #tables.breakeven_table(df_rax_x86, df_reorder_x86, 'x86')

if __name__ == '__main__':
    main()
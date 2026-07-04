import logging

if __name__ == "__main__" and __package__ in (None, ""):
    raise SystemExit("Run analysis from the project root with: python3 -m scripts.analysis")

from utils.data import io
from utils.plotting import barcharts, distributions, faceted, heatmaps, thesis
from utils.plotting import tables

def run_step(label, required_inputs, action):
    missing = [name for name, value in required_inputs.items() if value is None]
    if missing:
        logging.warning("Skipping %s; missing input(s): %s", label, ", ".join(missing))
        return

    try:
        logging.info("Starting %s", label)
        action()
        logging.info("Finished %s", label)
    except Exception:
        logging.exception("Failed while generating %s; continuing with remaining outputs", label)

def generate_plots(df_rax_x86, df_ios_x86, df_cold_x86, df_reorder_x86,
                   df_rax_arm, df_ios_arm, df_cold_arm, df_reorder_arm,
                   df_cache_x86, df_cache_arm, df_tlb_x86, df_tlb_arm,
                   df_metrics):
    # To generate sparsity plots:
    # from utils.plotting.sparsity import sparse_plot
    # sparse_plot("matrices/Semiconductor/nv2.mtx")
    run_step("x86 speedup heatmap", {"rax_x86": df_rax_x86},
             lambda: heatmaps.speedup_heatmap(df_rax_x86, "x86"))
    run_step("ARM speedup heatmap", {"rax_arm": df_rax_arm},
             lambda: heatmaps.speedup_heatmap(df_rax_arm, "ARM"))
    run_step("x86 win/loss summary", {"rax_x86": df_rax_x86},
             lambda: barcharts.win_loss_summary(df_rax_x86, "x86"))
    run_step("ARM win/loss summary", {"rax_arm": df_rax_arm},
             lambda: barcharts.win_loss_summary(df_rax_arm, "ARM"))
    run_step("x86 cache miss plot", {"cache_x86": df_cache_x86},
             lambda: faceted.cache_plot(df_cache_x86, "x86"))
    run_step("x86 normalized cache miss plot", {"cache_x86": df_cache_x86, "metrics": df_metrics},
             lambda: faceted.cache_plot_normalized(df_cache_x86, 'x86', df_metrics))
    run_step("ARM cache miss plot", {"cache_arm": df_cache_arm},
             lambda: faceted.cache_plot(df_cache_arm, "ARM"))
    run_step("ARM normalized cache miss plot", {"cache_arm": df_cache_arm, "metrics": df_metrics},
             lambda: faceted.cache_plot_normalized(df_cache_arm, 'ARM', df_metrics))
    run_step("ARM vs x86 comparison", {"cold_x86": df_cold_x86, "cold_arm": df_cold_arm},
             lambda: barcharts.arm_x86_comp(df_cold_x86, df_cold_arm))
    run_step("x86 TLB plot", {"tlb_x86": df_tlb_x86},
             lambda: faceted.tlb_plot(df_tlb_x86, "x86"))
    run_step("ARM TLB plot", {"tlb_arm": df_tlb_arm},
             lambda: faceted.tlb_plot(df_tlb_arm, "ARM"))
    run_step("x86 speedup histogram", {"rax_x86": df_rax_x86},
             lambda: distributions.speedup_histogram(df_rax_x86, "x86"))
    run_step("ARM speedup histogram", {"rax_arm": df_rax_arm},
             lambda: distributions.speedup_histogram(df_rax_arm, "ARM"))
    run_step("x86 cache reduction histogram", {"cache_x86": df_cache_x86},
             lambda: distributions.cache_reduction_histogram(df_cache_x86, "x86"))
    run_step("ARM cache reduction histogram", {"cache_arm": df_cache_arm},
             lambda: distributions.cache_reduction_histogram(df_cache_arm, "ARM"))
    run_step("x86 TLB reduction histogram", {"tlb_x86": df_tlb_x86},
             lambda: distributions.tlb_reduction_histogram(df_tlb_x86, "x86"))
    run_step("ARM TLB reduction histogram", {"tlb_arm": df_tlb_arm},
             lambda: distributions.tlb_reduction_histogram(df_tlb_arm, "ARM"))
    run_step("x86 preprocessing break-even histogram", {"rax_x86": df_rax_x86, "reorder_x86": df_reorder_x86},
             lambda: distributions.breakeven_histogram(df_rax_x86, df_reorder_x86, "x86"))
    run_step("ARM preprocessing break-even histogram", {"rax_arm": df_rax_arm, "reorder_arm": df_reorder_arm},
             lambda: distributions.breakeven_histogram(df_rax_arm, df_reorder_arm, "ARM"))
    run_step("x86 structural compression histogram", {"metrics": df_metrics},
             lambda: distributions.structural_compression_histogram(df_metrics, "x86"))
    run_step("x86 ranked best-speedup thesis plot", {"rax_x86": df_rax_x86},
             lambda: thesis.best_speedup_ranked(df_rax_x86, "x86"))
    run_step("ARM ranked best-speedup thesis plot", {"rax_arm": df_rax_arm},
             lambda: thesis.best_speedup_ranked(df_rax_arm, "ARM"))
    run_step("x86 category speedup thesis plot", {"rax_x86": df_rax_x86},
             lambda: thesis.category_speedup_distribution(df_rax_x86, "x86"))
    run_step("ARM category speedup thesis plot", {"rax_arm": df_rax_arm},
             lambda: thesis.category_speedup_distribution(df_rax_arm, "ARM"))
    run_step("x86 cache/runtime thesis plot", {"rax_x86": df_rax_x86, "cache_x86": df_cache_x86},
             lambda: thesis.memory_speedup_relation(df_rax_x86, df_cache_x86, "x86"))
    run_step("ARM cache/runtime thesis plot", {"rax_arm": df_rax_arm, "cache_arm": df_cache_arm},
             lambda: thesis.memory_speedup_relation(df_rax_arm, df_cache_arm, "ARM"))
    run_step("x86 TLB ratio thesis plot", {"tlb_x86": df_tlb_x86},
             lambda: thesis.tlb_ratio_summary(df_tlb_x86, "x86"))
    run_step("ARM TLB ratio thesis plot", {"tlb_arm": df_tlb_arm},
             lambda: thesis.tlb_ratio_summary(df_tlb_arm, "ARM"))
    run_step("x86 methodology stability thesis plot", {"cold_x86": df_cold_x86, "ios_x86": df_ios_x86, "rax_x86": df_rax_x86},
             lambda: thesis.methodology_stability(df_cold_x86, df_ios_x86, df_rax_x86, "x86"))
    run_step("ARM methodology stability thesis plot", {"cold_arm": df_cold_arm, "ios_arm": df_ios_arm, "rax_arm": df_rax_arm},
             lambda: thesis.methodology_stability(df_cold_arm, df_ios_arm, df_rax_arm, "ARM"))

def generate_tables(df_rax_x86, df_ios_x86, df_cold_x86,
                    df_rax_arm, df_ios_arm, df_cold_arm,
                    df_reorder_x86, df_reorder_arm,
                    df_cache_x86, df_cache_arm,
                    df_tlb_x86, df_tlb_arm,
                    df_metrics):
    run_step("x86 scaling table", {"rax_x86": df_rax_x86},
             lambda: tables.scaling_table(df_rax_x86, "x86"))
    run_step("ARM scaling table", {"rax_arm": df_rax_arm},
             lambda: tables.scaling_table(df_rax_arm, "ARM"))
    run_step("x86 methodology table", {"cold_x86": df_cold_x86, "rax_x86": df_rax_x86, "ios_x86": df_ios_x86},
             lambda: tables.methodology_table(df_cold_x86, df_rax_x86, df_ios_x86, "x86"))
    run_step("ARM methodology table", {"cold_arm": df_cold_arm, "rax_arm": df_rax_arm, "ios_arm": df_ios_arm},
             lambda: tables.methodology_table(df_cold_arm, df_rax_arm, df_ios_arm, "ARM"))
    run_step("x86 break-even table", {"rax_x86": df_rax_x86, "reorder_x86": df_reorder_x86},
             lambda: tables.breakeven_table(df_rax_x86, df_reorder_x86, 'x86'))
    run_step("ARM break-even table", {"rax_arm": df_rax_arm, "reorder_arm": df_reorder_arm},
             lambda: tables.breakeven_table(df_rax_arm, df_reorder_arm, 'ARM'))
    run_step("matrix characteristics table", {"metrics": df_metrics},
             lambda: tables.matrix_characteristics_table(df_metrics))
    run_step("x86 thesis aggregate table", {"rax_x86": df_rax_x86, "cache_x86": df_cache_x86, "tlb_x86": df_tlb_x86},
             lambda: tables.thesis_aggregate_table(df_rax_x86, df_cache_x86, df_tlb_x86, "x86"))
    run_step("ARM thesis aggregate table", {"rax_arm": df_rax_arm, "cache_arm": df_cache_arm, "tlb_arm": df_tlb_arm},
             lambda: tables.thesis_aggregate_table(df_rax_arm, df_cache_arm, df_tlb_arm, "ARM"))
    run_step("x86 thesis best-reordering table", {"rax_x86": df_rax_x86, "reorder_x86": df_reorder_x86},
             lambda: tables.thesis_best_reordering_table(df_rax_x86, df_reorder_x86, "x86"))
    run_step("ARM thesis best-reordering table", {"rax_arm": df_rax_arm, "reorder_arm": df_reorder_arm},
             lambda: tables.thesis_best_reordering_table(df_rax_arm, df_reorder_arm, "ARM"))

def main():
    io.init_logging()
    io.init_plt()

    (df_metrics,
     df_cold_x86, df_ios_x86, df_rax_x86, df_reorder_x86,
     df_cold_arm,  df_ios_arm,  df_rax_arm,  df_reorder_arm,
     df_cache_x86, df_cache_arm,
     df_tlb_x86,   df_tlb_arm) = io.read_files()
 
    generate_plots(df_rax_x86, df_ios_x86, df_cold_x86, df_reorder_x86,
                   df_rax_arm, df_ios_arm, df_cold_arm, df_reorder_arm,
                   df_cache_x86, df_cache_arm,
                   df_tlb_x86,   df_tlb_arm,
                   df_metrics)
    
    generate_tables(df_rax_x86, df_ios_x86, df_cold_x86,
                    df_rax_arm, df_ios_arm, df_cold_arm,
                    df_reorder_x86, df_reorder_arm,
                    df_cache_x86, df_cache_arm,
                    df_tlb_x86, df_tlb_arm,
                    df_metrics)

if __name__ == '__main__':
    main()

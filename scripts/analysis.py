import logging

if __name__ == "__main__" and __package__ in (None, ""):
    raise SystemExit("Run analysis from the project root with: python3 -m scripts.analysis")

from utils.data import io
from utils.plotting import distributions
from utils.plotting import thesis
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
    # Curated thesis figures. Histograms are limited to speedup and structural
    # compression distributions.
    run_step("x86 speedup histogram", {"rax_x86": df_rax_x86},
             lambda: distributions.speedup_histogram(df_rax_x86, "x86"))
    run_step("ARM speedup histogram", {"rax_arm": df_rax_arm},
             lambda: distributions.speedup_histogram(df_rax_arm, "ARM"))
    run_step("x86 category speedup thesis plot", {"rax_x86": df_rax_x86},
             lambda: thesis.category_speedup_distribution(df_rax_x86, "x86"))
    run_step("ARM category speedup thesis plot", {"rax_arm": df_rax_arm},
             lambda: thesis.category_speedup_distribution(df_rax_arm, "ARM"))
    run_step("x86 outcome fraction thesis plot", {"rax_x86": df_rax_x86},
             lambda: thesis.outcome_fraction_bars(df_rax_x86, "x86"))
    run_step("ARM outcome fraction thesis plot", {"rax_arm": df_rax_arm},
             lambda: thesis.outcome_fraction_bars(df_rax_arm, "ARM"))
    run_step("x86 preprocessing break-even thesis plot", {"rax_x86": df_rax_x86, "reorder_x86": df_reorder_x86},
             lambda: thesis.preprocessing_breakeven_boxplot(df_rax_x86, df_reorder_x86, "x86"))
    run_step("ARM preprocessing break-even thesis plot", {"rax_arm": df_rax_arm, "reorder_arm": df_reorder_arm},
             lambda: thesis.preprocessing_breakeven_boxplot(df_rax_arm, df_reorder_arm, "ARM"))
    run_step("x86/ARM best-reordering agreement thesis plot", {"rax_x86": df_rax_x86, "rax_arm": df_rax_arm},
             lambda: thesis.best_reordering_agreement(df_rax_x86, df_rax_arm))
    run_step("x86 cache ratio thesis plot", {"cache_x86": df_cache_x86},
             lambda: thesis.cache_miss_ratio_summary(df_cache_x86, "x86"))
    run_step("ARM cache ratio thesis plot", {"cache_arm": df_cache_arm},
             lambda: thesis.cache_miss_ratio_summary(df_cache_arm, "ARM"))
    run_step("structural compression histogram", {"metrics": df_metrics},
             lambda: distributions.structural_compression_histogram(df_metrics, "x86"))
    run_step("x86 TLB ratio thesis plot", {"tlb_x86": df_tlb_x86},
             lambda: thesis.tlb_ratio_summary(df_tlb_x86, "x86"))
    run_step("ARM TLB ratio thesis plot", {"tlb_arm": df_tlb_arm},
             lambda: thesis.tlb_ratio_summary(df_tlb_arm, "ARM"))

def generate_tables(df_rax_x86, df_ios_x86, df_cold_x86,
                    df_rax_arm, df_ios_arm, df_cold_arm,
                    df_reorder_x86, df_reorder_arm,
                    df_cache_x86, df_cache_arm,
                    df_tlb_x86, df_tlb_arm,
                    df_metrics):
    run_step("matrix characteristics table", {"metrics": df_metrics},
             lambda: tables.matrix_characteristics_table(df_metrics))
    run_step("x86 thesis aggregate table", {"rax_x86": df_rax_x86, "cache_x86": df_cache_x86, "tlb_x86": df_tlb_x86},
             lambda: tables.thesis_aggregate_table(df_rax_x86, df_cache_x86, df_tlb_x86, "x86"))
    run_step("ARM thesis aggregate table", {"rax_arm": df_rax_arm, "cache_arm": df_cache_arm, "tlb_arm": df_tlb_arm},
             lambda: tables.thesis_aggregate_table(df_rax_arm, df_cache_arm, df_tlb_arm, "ARM"))

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

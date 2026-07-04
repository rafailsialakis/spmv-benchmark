import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = Path("results")

"""
Used to read all the *.csv files and parse them as DataFrames

Args:
    None

Returns:
    df (tuple): A tuple that contains all the DataFrames
"""
def read_files() -> tuple: 
    x86_dir = RESULTS_DIR / "x86_results"
    arm_dir = RESULTS_DIR / "arm_results"

    df_metrics     = pd.read_csv(x86_dir / "metrics.csv")
    
    df_cold_x86    = pd.read_csv(x86_dir / "cold.csv")
    df_ios_x86     = pd.read_csv(x86_dir / "ios.csv")
    df_rax_x86     = pd.read_csv(x86_dir / "rax.csv")
    df_reorder_x86 = pd.read_csv(x86_dir / "reorder_times.csv")
    df_cache_x86   = pd.read_csv(x86_dir / "cache.csv")
    df_tlb_x86     = pd.read_csv(x86_dir / "tlb.csv")
    
    df_cold_arm    = pd.read_csv(arm_dir / "cold.csv")
    df_ios_arm     = pd.read_csv(arm_dir / "ios.csv")
    df_rax_arm     = pd.read_csv(arm_dir / "rax.csv")
    df_reorder_arm = pd.read_csv(arm_dir / "reorder_times.csv")
    df_cache_arm   = pd.read_csv(arm_dir / "cache.csv")
    df_tlb_arm     = pd.read_csv(arm_dir / "tlb.csv")

    logging.info("DataFrames imported successfully!")
    
    return (df_metrics,
            df_cold_x86, df_ios_x86, df_rax_x86, df_reorder_x86,
            df_cold_arm, df_ios_arm, df_rax_arm, df_reorder_arm,
            df_cache_x86, df_cache_arm,
            df_tlb_x86, df_tlb_arm)

"""
Initializes configuration for plt formatting
"""
def init_plt() -> None:
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "text.latex.preamble": r"\usepackage{amsmath}",
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.formatter.use_mathtext": True,  
        "pgf.texsystem": "pdflatex",          
    })
    logging.info("Parameters configured successfully!")

"""
Initializes logging configuration
"""
def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.info("Logging was initialized successfully!")

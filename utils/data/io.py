import logging
import os
from pathlib import Path
import pandas as pd

if "MPLCONFIGDIR" not in os.environ:
    mpl_config_dir = Path("/tmp/spmv-benchmark-mplconfig")
    mpl_config_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(mpl_config_dir)

import matplotlib.pyplot as plt
from pandas.errors import EmptyDataError, ParserError

RESULTS_DIR = Path("results")

"""
Used to read all the *.csv files and parse them as DataFrames

Args:
    None

Returns:
    df (tuple): A tuple that contains all the DataFrames
"""
def read_csv(path: Path, label: str):
    try:
        logging.info("Reading %s from %s", label, path)
        df = pd.read_csv(path)
        logging.info("Loaded %s: %d rows, %d columns", label, len(df), len(df.columns))
        return df
    except FileNotFoundError:
        logging.warning("Missing %s at %s", label, path)
    except EmptyDataError:
        logging.warning("Skipping %s because %s is empty", label, path)
    except ParserError:
        logging.exception("Skipping %s because %s could not be parsed", label, path)
    return None

def read_files() -> tuple:
    x86_dir = RESULTS_DIR / "x86_results"
    arm_dir = RESULTS_DIR / "arm_results"

    logging.info("Reading benchmark CSVs from %s", RESULTS_DIR)

    df_metrics     = read_csv(x86_dir / "metrics.csv", "x86 metrics")
    
    df_cold_x86    = read_csv(x86_dir / "cold.csv", "x86 cold timings")
    df_ios_x86     = read_csv(x86_dir / "ios.csv", "x86 IO-swap timings")
    df_rax_x86     = read_csv(x86_dir / "rax.csv", "x86 repeated-Ax timings")
    df_reorder_x86 = read_csv(x86_dir / "reorder_times.csv", "x86 reorder timings")
    df_cache_x86   = read_csv(x86_dir / "cache.csv", "x86 cache counters")
    df_tlb_x86     = read_csv(x86_dir / "tlb.csv", "x86 TLB counters")
    
    df_cold_arm    = read_csv(arm_dir / "cold.csv", "ARM cold timings")
    df_ios_arm     = read_csv(arm_dir / "ios.csv", "ARM IO-swap timings")
    df_rax_arm     = read_csv(arm_dir / "rax.csv", "ARM repeated-Ax timings")
    df_reorder_arm = read_csv(arm_dir / "reorder_times.csv", "ARM reorder timings")
    df_cache_arm   = read_csv(arm_dir / "cache.csv", "ARM cache counters")
    df_tlb_arm     = read_csv(arm_dir / "tlb.csv", "ARM TLB counters")

    logging.info("CSV import completed; missing inputs will be skipped during generation")
    
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
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True,
    )
    logging.info("Logging initialized at %s level", logging.getLevelName(level))

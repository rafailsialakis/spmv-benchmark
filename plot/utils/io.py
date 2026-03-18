import pandas as pd
import matplotlib.pyplot as plt

"""
Used to read all the *.csv files and parse them as DataFrames

Args:
    None

Returns:
    df (tuple): A tuple that contains all the DataFrames
"""
def read_files() -> tuple: 
    df_metrics = pd.read_csv("results/metrics.csv")
    df_cold_x86 = pd.read_csv("results/cold.csv")
    df_ios_x86 = pd.read_csv("results/ios.csv")
    df_rax_x86 = pd.read_csv("results/rax.csv")
    df_reorder_x86 = pd.read_csv("results/reorder_times.csv")
    df_cold_arm = pd.read_csv("arm_results/cold.csv")
    df_ios_arm = pd.read_csv("arm_results/ios.csv")
    df_rax_arm = pd.read_csv("arm_results/rax.csv")
    df_reorder_arm = pd.read_csv("arm_results/reorder_times.csv")
    return df_metrics, df_cold_x86, df_ios_x86, df_rax_x86, df_reorder_x86,df_cold_arm, df_ios_arm, df_rax_arm, df_reorder_arm

"""
Initializes configuration for plt formatting
"""
def init_plt():
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

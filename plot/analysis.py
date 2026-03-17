import numpy as np
from scipy.io import mmread
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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

def init_plt():
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    })

def sparse_plot(path: str):
    A = mmread(path).tocsr()

    perm_rcm = np.loadtxt("validation/rcm.txt", dtype=int)
    perm_amd = np.loadtxt("validation/amd.txt", dtype=int)
    perm_metis = np.loadtxt("validation/metis.txt", dtype=int)

    B = A[perm_rcm, :][:, perm_rcm]
    C = A[perm_amd, :][:, perm_amd]
    D = A[perm_metis, :][:, perm_metis]

    fig, axes = plt.subplots(2, 2, figsize=(10, 10))

    for ax, M, title in zip(
        axes.flat,
        [A, B, C, D],
        ["Original", "RCM", "AMD", "METIS"]
    ):
        ax.spy(M, markersize=0.5, rasterized=True)
        ax.set_title(title)

    plt.tight_layout()

    name = path.split("/")[-1].split(".")[0]
    plt.savefig(f"plot/figures/{name}_sparsity_plot.pdf", dpi=300)
    plt.show()

def speedup_heatmap(df_param: pd.DataFrame, label: str):
    df = df_param.copy()
    df = df[df["threads"] == 4]
    time_pivot = df.pivot(
        index="matrix",
        columns="reordering",
        values="time_ms"
    )
    speedup = time_pivot["none"].values.reshape(-1, 1) / time_pivot
    speedup = speedup.drop(columns=["none"])
    speedup = speedup.sort_values(by="rcm", ascending=False)
    plt.figure(figsize=(10, 7))

    sns.heatmap(
        speedup,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cmap="viridis",
        cbar_kws={"label": r"\textbf{Speedup}"}
    )

    plt.title(rf"\textbf{{Speedup per Reordering (4 threads, {label})}}")    
    plt.xlabel(r"\textbf{Reordering Method}")
    plt.ylabel(r"\textbf{Matrix}")

    plt.tight_layout()
    plt.savefig(f"plot/figures/speedup_heatmap_{label}.pdf")
    plt.show()

def arm_x86_comp(df_x86: pd.DataFrame, df_arm: pd.DataFrame):
    df_x86_copy = df_x86.copy()
    df_x86_copy = (
        df_x86[df_x86["threads"] == 4]
        .groupby("matrix", as_index=False)["time_ms"]
        .mean()
    )  
    df_arm_copy = df_arm.copy()
    df_arm_copy = (
        df_arm[df_arm["threads"] == 4]
        .groupby("matrix", as_index=False)["time_ms"]
        .mean()
    )
    df_merged = df_x86_copy.merge(
        df_arm_copy,
        on="matrix",
        suffixes=("_x86", "_arm")
    )
    # Υπολογισμός speedup
    df_merged["speedup"] = df_merged["time_ms_x86"] / df_merged["time_ms_arm"]

    # Bar plot
    plt.figure(figsize=(12, 6))
    df_merged = df_merged.sort_values("speedup", ascending=False)
    plt.bar(df_merged["matrix"], df_merged["speedup"])
    plt.axhline(1, linestyle="--", color="red", label="x86 = ARM")
    plt.ylabel("Speedup (x86 / ARM)")
    plt.xlabel("Matrix")
    plt.xticks(rotation=45, ha="right")
    plt.title("Performance Comparison: x86 vs ARM (4 threads)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"plot/figures/arm_vs_x86.pdf")

def main():
    init_plt()

    df_metrics,df_cold_x86,df_ios_x86,df_rax_x86,df_reorder_x86,df_cold_arm,df_ios_arm,df_rax_arm,df_reorder_arm = read_files()

    #sparse_plot("matrices/Circuit/nv2.mtx")
    #speedup_heatmap(df_rax_arm, "ARM")
    #speedup_heatmap(df_rax_x86, "x86")
    arm_x86_comp(df_cold_x86, df_cold_arm)



if __name__ == '__main__':
    main()
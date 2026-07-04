import logging

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils.plotting.common import save_figure


def speedup_heatmap(df_param: pd.DataFrame, label: str) -> None:
    logging.info("Generating speedup heatmap for %s architecture...", label)
    logging.info("Reading and pivoting dataframe...")
    df = df_param.copy()
    df = df[df["threads"] == 4]

    time_pivot = df.pivot(
        index="matrix",
        columns="reordering",
        values="time_ms",
    )
    logging.info("Calculating speedup...")
    speedup = time_pivot["none"].values.reshape(-1, 1) / time_pivot
    speedup = speedup.drop(columns=["none"])
    speedup = speedup.sort_values(by="rcm", ascending=False)

    logging.info("Plotting...")
    plt.figure(figsize=(10, 7))

    sns.heatmap(
        speedup,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cmap="viridis",
        cbar_kws={"label": r"\textbf{Speedup}"},
    )

    plt.title(rf"\textbf{{Speedup per Reordering (4 threads, {label})}}")
    plt.xlabel(r"\textbf{Reordering Method}")
    plt.ylabel(r"\textbf{Matrix}")

    plt.tight_layout()
    save_figure("heatmaps", f"speedup_heatmap_{label}.pdf")
    logging.info("Plot was saved successfully in figures/heatmaps/speedup_heatmap_%s.pdf", label)
    plt.show()

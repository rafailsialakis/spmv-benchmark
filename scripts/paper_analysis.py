"""Numbers, tables and figures for the conference paper.

Run from the project root:
    python3 -m scripts.paper_analysis               # IOs, figures at 4 threads
    python3 -m scripts.paper_analysis --dedupe      # count structurally identical pairs once

Outputs go to figures/paper/: paper_numbers.txt (every number with its key),
paper_numbers.tex (\\pn{key} macros for the LaTeX source), per-matrix CSV
tables, portability_cdf_t4.pdf and breakeven_cdf_t4.pdf.
"""

import argparse
import logging

if __name__ == "__main__" and __package__ in (None, ""):
    raise SystemExit("Run from the project root with: python3 -m scripts.paper_analysis")

from utils.analysis import paper
from utils.data import io


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--methodology", default="ios", choices=["ios", "rax", "cold"])
    ap.add_argument("--threshold", type=float, default=0.05, help="win/loss threshold (default 0.05)")
    ap.add_argument("--tie", type=float, default=0.02, help="co-best tolerance (default 0.02)")
    ap.add_argument("--fig-threads", type=int, default=4)
    ap.add_argument("--dedupe", action="store_true", help="drop the second matrix of each identical pair")
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--out", default="paper", help="subfolder of figures/ (default paper)")
    args = ap.parse_args()

    io.init_logging()
    logging.getLogger("fontTools").setLevel(logging.WARNING)
    if not args.no_plots:
        io.init_plt()
    nums, _ = paper.run(out_dir=args.out, methodology=args.methodology, fig_threads=args.fig_threads,
                        thr=args.threshold, tie=args.tie, dedupe=args.dedupe,
                        make_plots=not args.no_plots)

    t = args.fig_threads
    show = [f"{p}.reps" for p in ("x86", "arm")]
    show += [f"{p}.spread.median" for p in ("x86", "arm")] + [f"{p}.t{t}.twins.maxdiff" for p in ("x86", "arm")]
    show += [f"{p}.t{t}.{m}.{k}" for p in ("x86", "arm") for m in paper.METHODS for k in ("win", "loss", "within1000")]
    show += [f"{s}.t{t}.kernel.{k}" for s in ("x86toarm", "armtox86") for k in ("exact", "tieagree", "within5", "worst")]
    show += [f"x86toarm.t{t}.kernel.srcnone.count", f"x86toarm.t{t}.kernel.srcnone.tgtnone.count"]
    show += [f"{s}.t{t}.cost1000.within5" for s in ("x86toarm", "armtox86")]
    logging.info("Key numbers (all are in figures/%s/paper_numbers.txt):", args.out)
    for k in show:
        if k in nums.values:
            v, kind = nums.values[k]
            print(f"  {k:42s} {paper.Numbers.fmt(v, kind)}")


if __name__ == "__main__":
    main()

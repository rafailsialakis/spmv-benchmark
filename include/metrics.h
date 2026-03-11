#ifndef METRICS_H
#define METRICS_H
int compute_bandwidth(struct CSRMatrix* csr);
double compute_density(struct CSRMatrix* csr);
double compute_imbalance_ratio(struct CSRMatrix* csr, int threads);
#endif

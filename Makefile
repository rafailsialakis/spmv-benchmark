CC      = gcc

CFLAGS  = -O3 -Wall -Iinclude -Wunused -fopenmp -Wno-unused-result
CFLAGS += -I/usr/include/scotch
CFLAGS += -Ithird-party/rcm
LDFLAGS = -lcxsparse -lscotch -lscotcherr -lm -lpapi

# OpenMP thread pinning (must be in the environment before the program starts)
export OMP_PROC_BIND   = close
export OMP_PLACES      = cores
export OMP_DISPLAY_ENV = true

# Directories
SRC_DIR = src
UNAME_M = $(shell uname -m)

ifeq ($(UNAME_M),aarch64)
RESULTS_DIR = results/arm_results
else ifeq ($(UNAME_M),x86_64)
RESULTS_DIR = results/x86_results
else
$(error Unsupported platform: $(UNAME_M))
endif

# Source groups
MATRIX_SRC   = $(SRC_DIR)/matrix/coo.c \
               $(SRC_DIR)/matrix/csr.c \
               $(SRC_DIR)/matrix/parser.c

SPMV_SRC     = $(SRC_DIR)/spmv/spmv.c
REORDER_SRC  = $(SRC_DIR)/reorder/reorder.c \
               third-party/rcm/rcm.c
UTILS_SRC    = $(SRC_DIR)/utils/utils.c

BENCH_SRC    = $(SRC_DIR)/benchmark/benchmark.c \
               $(SRC_DIR)/benchmark/metrics.c \
               $(SRC_DIR)/benchmark/timer.c

MAIN_SRC     = $(SRC_DIR)/main/main.c
CACHE_SRC    = $(SRC_DIR)/main/cache_main.c
PERM_SRC     = $(SRC_DIR)/main/perm_main.c
TLB_SRC      = $(SRC_DIR)/main/tlb_main.c
CHECK_SRC    = $(SRC_DIR)/main/check_main.c

COMMON_SRC = $(MATRIX_SRC) $(SPMV_SRC) $(REORDER_SRC) $(UTILS_SRC) $(BENCH_SRC)

# Executables
BIN_DIR = bin
RESULT_DIRS = results/x86_results results/arm_results

BIN1 = $(BIN_DIR)/spmv-benchmark
BIN2 = $(BIN_DIR)/spmv-benchmark-perm
BIN3 = $(BIN_DIR)/spmv-benchmark-cache
BIN4 = $(BIN_DIR)/spmv-benchmark-tlb
BIN5 = $(BIN_DIR)/spmv-check

.PHONY: all check-matrices clean clean-results platform-info paper run run-perm run-cache run-tlb run-all run-all-cache run-all-tlb plot docs docs-serve run-tests

all: $(BIN1) $(BIN2) $(BIN3) $(BIN4) $(BIN5)

$(BIN1): $(COMMON_SRC) $(MAIN_SRC)
	mkdir -p $(BIN_DIR) $(RESULT_DIRS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN2): $(COMMON_SRC) $(PERM_SRC)
	mkdir -p $(BIN_DIR) $(RESULT_DIRS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN3): $(COMMON_SRC) $(CACHE_SRC)
	mkdir -p $(BIN_DIR) $(RESULT_DIRS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN4): $(COMMON_SRC) $(TLB_SRC)
	mkdir -p $(BIN_DIR) $(RESULT_DIRS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN5): $(COMMON_SRC) $(CHECK_SRC)
	mkdir -p $(BIN_DIR) $(RESULT_DIRS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Pre-flight: every matrix must have a structurally symmetric pattern
check-matrices: $(BIN5)
	@fail=0; count=0; for mtx in $$(find -L matrices -name "*.mtx" | sed 's|matrices/||' | sort); do \
		count=$$((count + 1)); \
		./$(BIN5) $$mtx > /dev/null || { echo "FAIL $$mtx"; fail=1; }; \
	done; \
	if [ $$count -eq 0 ]; then echo "No .mtx files found under matrices/"; exit 1; fi; \
	[ $$fail -eq 0 ] && echo "All $$count matrices passed the pattern check." || exit 1

run: $(BIN1)
	./$(BIN1) $(MTX)

run-perm: $(BIN2)
	./$(BIN2) $(MTX)

run-cache: $(BIN3)
	./$(BIN3) $(MTX)

run-tlb: $(BIN4)
	./$(BIN4) $(MTX)

run-all: $(BIN1)
	@for mtx in $$(find matrices -name "*.mtx" | sed 's|matrices/||'); do \
		category=$$(dirname "$$mtx"); \
		matrix=$$(basename "$$mtx" .mtx); \
		if [ -f "$(RESULTS_DIR)/metrics.csv" ] && awk -F, -v matrix="$$matrix" -v category="$$category" 'NR > 1 && $$1 == matrix && $$2 == category { found = 1; exit } END { exit !found }' "$(RESULTS_DIR)/metrics.csv"; then \
			printf 'Skipping %s: already present in %s\n' "$$mtx" "$(RESULTS_DIR)/metrics.csv"; \
		else \
			./$(BIN1) $$mtx; \
		fi; \
	done

run-all-cache: $(BIN3)
	@for mtx in $$(find matrices -name "*.mtx" | sed 's|matrices/||'); do \
		category=$$(dirname "$$mtx"); \
		matrix=$$(basename "$$mtx" .mtx); \
		if [ -f "$(RESULTS_DIR)/cache.csv" ] && awk -F, -v matrix="$$matrix" -v category="$$category" 'NR > 1 && $$1 == matrix && $$2 == category { found = 1; exit } END { exit !found }' "$(RESULTS_DIR)/cache.csv"; then \
			printf 'Skipping %s: already present in %s\n' "$$mtx" "$(RESULTS_DIR)/cache.csv"; \
		else \
			./$(BIN3) $$mtx; \
		fi; \
	done

run-all-tlb: $(BIN4)
	@for mtx in $$(find matrices -name "*.mtx" | sed 's|matrices/||'); do \
		category=$$(dirname "$$mtx"); \
		matrix=$$(basename "$$mtx" .mtx); \
		if [ -f "$(RESULTS_DIR)/tlb.csv" ] && awk -F, -v matrix="$$matrix" -v category="$$category" 'NR > 1 && $$1 == matrix && $$2 == category { found = 1; exit } END { exit !found }' "$(RESULTS_DIR)/tlb.csv"; then \
			printf 'Skipping %s: already present in %s\n' "$$mtx" "$(RESULTS_DIR)/tlb.csv"; \
		else \
			./$(BIN4) $$mtx; \
		fi; \
	done

download-matrices:
	scripts/download_matrices.sh

plot:
	python3 -m scripts.analysis

# Numbers and figures for the conference paper (repetition-aware analysis)
paper:
	python3 -m scripts.paper_analysis

# Records CPU, kernel, compiler, THP, page size and frequency settings
platform-info:
	scripts/platform_info.sh

docs:
	cd docs && zensical build

docs-serve:
	cd docs && zensical serve

run-tests:
	pytest -v -ra

# Removes binaries only. Benchmark results are deleted only by clean-results.
clean:
	rm -f $(BIN1) $(BIN2) $(BIN3) $(BIN4) $(BIN5)

clean-results:
	@printf 'This deletes every CSV in results/x86_results and results/arm_results. Type yes: '; \
	read ans; [ "$$ans" = yes ] && rm -f results/x86_results/*.csv results/arm_results/*.csv || echo 'Aborted.'

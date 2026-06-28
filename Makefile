CC      = gcc

CFLAGS  = -O3 -Wall -Iinclude -Wunused -fopenmp -Wno-unused-result
CFLAGS += -I/usr/include/scotch

LDFLAGS = -lcxsparse -lscotchmetisv5 -lscotcherr -lm -lpapi

# Directories
SRC_DIR = src

# Source groups
MATRIX_SRC   = $(SRC_DIR)/matrix/coo.c \
               $(SRC_DIR)/matrix/csr.c \
               $(SRC_DIR)/matrix/parser.c

SPMV_SRC     = $(SRC_DIR)/spmv/spmv.c
REORDER_SRC  = $(SRC_DIR)/reorder/reorder.c
UTILS_SRC    = $(SRC_DIR)/utils/utils.c \
               $(SRC_DIR)/utils/queue.c

BENCH_SRC    = $(SRC_DIR)/benchmark/benchmark.c \
               $(SRC_DIR)/benchmark/metrics.c \
               $(SRC_DIR)/benchmark/timer.c

MAIN_SRC     = $(SRC_DIR)/main/main.c
CACHE_SRC    = $(SRC_DIR)/main/cache_main.c
PERM_SRC     = $(SRC_DIR)/main/perm_main.c
TLB_SRC      = $(SRC_DIR)/main/tlb_main.c

COMMON_SRC = $(MATRIX_SRC) $(SPMV_SRC) $(REORDER_SRC) $(UTILS_SRC) $(BENCH_SRC)

# Executables
BIN_DIR = bin

BIN1 = $(BIN_DIR)/spmv-benchmark
BIN2 = $(BIN_DIR)/spmv-benchmark-perm
BIN3 = $(BIN_DIR)/spmv-benchmark-cache
BIN4 = $(BIN_DIR)/spmv-benchmark-tlb

.PHONY: all clean run run-perm run-cache run-tlb run-all run-all-cache run-all-tlb plot

all: $(BIN1) $(BIN2) $(BIN3) $(BIN4)

$(BIN1): $(COMMON_SRC) $(MAIN_SRC)
	mkdir -p $(BIN_DIR) results
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN2): $(COMMON_SRC) $(PERM_SRC)
	mkdir -p $(BIN_DIR) results
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN3): $(COMMON_SRC) $(CACHE_SRC)
	mkdir -p $(BIN_DIR) results
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN4): $(COMMON_SRC) $(TLB_SRC)
	mkdir -p $(BIN_DIR) results
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

run: $(BIN1)
	./$(BIN1) $(MTX)

run-perm:
	./$(BIN2) $(MTX)

run-cache:
	./$(BIN3) $(MTX)

run-tlb:
	./$(BIN4) $(MTX)

run-all:
	@for mtx in $$(find matrices -name "*.mtx" | sed 's|matrices/||'); do \
		./$(BIN1) $$mtx; \
	done

run-all-cache:
	@for mtx in $$(find matrices -name "*.mtx" | sed 's|matrices/||'); do \
		./$(BIN3) $$mtx; \
	done

run-all-tlb:
	@for mtx in $$(find matrices -name "*.mtx" | sed 's|matrices/||'); do \
		./$(BIN4) $$mtx; \
	done

plot:
	python3 plot/analysis.py

clean:
	rm -f $(BIN1) $(BIN2) $(BIN3) $(BIN4)
	rm -f x86_results/*.csv arm_results/*.csv
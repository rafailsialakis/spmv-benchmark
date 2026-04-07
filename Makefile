CC      = gcc
CFLAGS  = -O3 -Wall -Iinclude -Wunused -fopenmp 
CFLAGS 	+= -I/usr/include/scotch
LDFLAGS = -lcxsparse -lscotchmetisv5 -lscotcherr -lm -lpapi
COMMON_SRC = src/parser.c src/coo.c src/csr.c src/spmv.c src/timer.c src/reorder.c src/benchmark.c src/queue.c src/metrics.c src/utils.c
MATRICES_DIR = matrices
RESULTS = results

SRC1 = $(COMMON_SRC) src/main.c
SRC2 = $(COMMON_SRC) src/main_perm.c
SRC3 = $(COMMON_SRC) src/main_cache.c

BIN1 = bin/spmv-benchmark
BIN2 = bin/spmv-benchmark-perm
BIN3 = bin/spmv-benchmark-cache

.PHONY: plot

all: $(BIN1) $(BIN2) $(BIN3)

$(BIN1): $(SRC1)
	mkdir -p bin results
	$(CC) $(CFLAGS) -o $(BIN1) $(SRC1) $(LDFLAGS)

$(BIN2): $(SRC2)
	mkdir -p bin results
	$(CC) $(CFLAGS) -o $(BIN2) $(SRC2) $(LDFLAGS)

$(BIN3): $(SRC3)
	mkdir -p bin results
	$(CC) $(CFLAGS) -o $(BIN3) $(SRC3) $(LDFLAGS)

run: $(BIN1)
	$(BIN1) $(MTX)

run-perm:
	$(BIN2) $(MTX)

run-cache:
	$(BIN3) $(MTX)

run-all: $(BIN1)
	@for mtx in $(shell find $(MATRICES_DIR) -name "*.mtx" | sed 's|$(MATRICES_DIR)/||'); do \
		./$(BIN1) $$mtx; \
	done

run-all-cache: $(BIN3)
	@for mtx in $(shell find $(MATRICES_DIR) -name "*.mtx" | sed 's|$(MATRICES_DIR)/||'); do \
		./$(BIN3) $$mtx; \
	done

plot:
	python3 plot/analysis.py

clean:
	rm -f $(BIN1) $(BIN2) $(RESULTS)/*.csv
	
help:
	@echo "Usage:"
	@echo "  make           		   	Build the benchmark binary"
	@echo "  make run MTX=matrix.mtx		Run benchmark on a single matrix"
	@echo "  make run-perm MTX=matrix.mtx		Export permutation vectors"
	@echo "  make run-all   		   	Run benchmark on all matrices in $(MATRICES_DIR)/"
	@echo "  make plot      		   	Run analysis plotting scripts"
	@echo "  make clean     		   	Remove binaries and results"
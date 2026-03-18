CC      = gcc
CFLAGS  = -O3 -Wall -Iinclude -Wunused -D_POSIX_C_SOURCE=200809L -fopenmp -lm
LDFLAGS = -lcxsparse -lscotchmetisv5 -lscotcherr -lsuitesparseconfig
SRC = src/parser.c src/coo.c src/csr.c src/spmv.c src/timer.c src/reorder.c src/benchmark.c src/queue.c src/metrics.c src/main.c
BIN = bin/spmv-benchmark
MATRICES_DIR = matrices
RESULTS = results

.PHONY: plot

all: $(BIN)

$(BIN): $(SRC)
	mkdir -p bin results
	$(CC) $(CFLAGS) -o $(BIN) $(SRC) $(LDFLAGS)

run: $(BIN)
	$(BIN) $(MTX)

run-all: $(BIN)
	@for mtx in $(shell find $(MATRICES_DIR) -name "*.mtx" | sed 's|$(MATRICES_DIR)/||'); do \
		./$(BIN) $$mtx; \
	done

plot:
	python3 plot/analysis.py

clean:
	rm -f $(BIN) $(RESULTS)/*.csv

help:
	@echo "Usage:"
	@echo "  make           		   	Build the benchmark binary"
	@echo "  make run MTX=matrix.mtx		Run benchmark on a single matrix"
	@echo "  make run-all   		   	Run benchmark on all matrices in $(MATRICES_DIR)/"
	@echo "  make plot      		   	Run analysis plotting scripts"
	@echo "  make clean     		   	Remove binaries and results"
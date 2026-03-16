CC      = gcc
CFLAGS  = -O3 -Wall -Iinclude -D_POSIX_C_SOURCE=200809L -fopenmp -lm
LDFLAGS = -lcxsparse -lscotchmetisv5 -lscotcherr -lsuitesparseconfig
SRC = src/parser.c src/coo.c src/csr.c src/spmv.c src/timer.c src/reorder.c src/benchmark.c src/queue.c src/metrics.c src/main.c
BIN = bin/spmv-benchmark
MATRICES_DIR = matrices
RESULTS = results

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

clean:
	rm -f $(BIN) $(RESULTS)/*.csv

help:
	echo "make                 
	echo "make run   MTX=x.mtx 
	echo "make batch            
	echo "make clean            
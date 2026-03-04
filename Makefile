CC      = gcc
CFLAGS  = -O2 -Wall -Iinclude -D_POSIX_C_SOURCE=200809L -fopenmp
LDFLAGS = -lcxsparse -lscotchmetisv5 -lscotcherr -lsuitesparseconfig
SRC = src/parser.c src/coo.c src/csr.c src/spmv.c src/timer.c src/reorder.c src/benchmark.c src/cache.c src/main.c
BIN = bin/spmv-benchmark

all: $(BIN)

$(BIN): $(SRC)
	$(CC) $(CFLAGS) -o $(BIN) $(SRC) $(LDFLAGS)

perf: $(BIN)
	perf stat -e cache-misses,cache-references $(BIN) $(MTX)

batch: $(BIN)
	@for mtx in matrices/*.mtx; do \
		echo "--- $$mtx ---"; \
		perf stat -e cache-misses,cache-references $(BIN) $$(basename $$mtx) 2>&1; \
	done

cache: $(BIN)
	$(BIN) $(MTX) --cache

threads: $(BIN)
	@echo "--- 1 thread ---"
	$(BIN) $(MTX) 1
	@echo "--- 2 threads ---"
	$(BIN) $(MTX) 2
	@echo "--- 4 threads ---"
	$(BIN) $(MTX) 4
	@echo "--- 8 threads ---"
	$(BIN) $(MTX) 8

clean:
	rm -f $(BIN)
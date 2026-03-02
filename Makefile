CC      = gcc
CFLAGS  = -O2 -Wall -Iinclude -D_POSIX_C_SOURCE=200809L -fopenmp
SRC = src/parser.c   \
      src/coo.c      \
      src/csr.c      \
      src/spmv.c     \
      src/timer.c    \
      src/reordering.c  \
      src/main.c

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

clean:
	rm -f $(BIN)
CC      = gcc
CFLAGS  = -O3 -Wall -Iinclude -D_POSIX_C_SOURCE=200809L -fopenmp
LDFLAGS = -lcxsparse -lscotchmetisv5 -lscotcherr -lsuitesparseconfig
SRC = src/parser.c src/coo.c src/csr.c src/spmv.c src/timer.c src/reorder.c src/benchmark.c src/queue.c src/metrics.c src/main.c
BIN = bin/spmv-benchmark

all: $(BIN)

$(BIN): $(SRC)
	mkdir -p bin results
	$(CC) $(CFLAGS) -o $(BIN) $(SRC) $(LDFLAGS)

run: $(BIN)
	$(BIN) $(MTX)

batch: $(BIN)
	mkdir -p results
	for mtx in matrices/*.mtx; do \
		$(BIN) $$(basename $$mtx) > /dev/null; \
	done

clean:
	rm -f $(BIN)

help:
	echo "make                 
	echo "make run   MTX=x.mtx 
	echo "make batch            
	echo "make clean            

gcc src/parser.c src/coo.c src/csr.c src/spmv.c src/timer.c src/main.c -o bin/spmv-benchmark.o
perf stat -e cache-misses,cache-references bin/spmv-benchmark.o Geo_1438.mtx

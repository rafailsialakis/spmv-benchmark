# Sparse Matrix Vector Multiplication Benchmark
## Research Question 
The goal of this project is to examine whether there is a matrix reordering scheme that optimizes the Sparse Matrix-Vector Multiplication (SpMV) kernel. If such a scheme exists, we aim to understand how and why this optimization occurs.

1. **Does matrix reordering improve the performance of Sparse Matrix Vector Multiplication?**

2. **Does matrix reordering impacts load balancing of Sparse Matrix Vector Multiplication?**

3. **Which matrix reordering schemes provide the greatest performance benefits?**

4. **Why do certain reordering schemes improve SpMV performance?**

5. **How does the effectiveness of reordering depend on matrix characteristics?**

6. **What is the trade-off between reordering cost and performance gain?**

7. **Does running the benchmark on a different architecture machine (ARM), impacts the resuls?**

## Overview
The benchmark was written purely in C, python was used for plotting and generating tables. A Makefile is provided in order to build and run the benchmark and plotting efficiently.<br>The matrices used as input are from **SuiteSparse** in *.mtx format. For the **SPMxV** the Compressed Sparse Row (CSR) method is used for representing the matrix.
### Reordering Schemes
The benchmark evaluates the following matrix reordering techniques:
1. **Reverse Cuthill–McKee (RCM)**  
2. **Approximate Minimum Degree (AMD)**  
3. **Nested Dissection (ND)**  

### Measurement Methodologies
To simulate different cache behaviors, the benchmark includes three measurement strategies:
1. **Repeated A * x (RAx)**  
2. **Input-Output Swap (IOs)**  
3. **Cold Measurement**  

### x86 System
- **CPU:** Intel Core i5-1035G1
- **Microarchitecture:** Ice Lake (10th Gen Intel)
- **Cores / Threads:** 4 cores / 8 threads
- **Base / Boost Frequency:** 1.00 GHz / 3.60 GHz
- **Cache:**
  - L1d: 48 KB per core (192 KB total)
  - L1i: 32 KB per core (128 KB total)
  - L2: 512 KB per core (2 MB total)
  - L3: 6 MB shared
- **RAM:** 20 GB
- **Architecture:** x86_64
- **Compiler:** GCC 15.2.1
- **Compiler Flags:** -O3 -march=native
- **Operating System:** Manjaro Linux (Kernel 6.12)

### ARM System
- **CPU:** ARM Neoverse-N1
- **Microarchitecture:** Neoverse N1
- **Cores / Threads:** 4 cores / 4 threads
- **Cache:**
  - L1d: 64 KB per core (256 KB total)
  - L1i: 64 KB per core (256 KB total)
  - L2: 1 MB per core (4 MB total)
  - L3: 32 MB shared
- **RAM:** 16 GB
- **Architecture:** ARM64 (AArch64)
- **Compiler:** GCC 12.2.0
- **Compiler Flags:** -O3 -mcpu=native
- **Operating System:** Debian Linux (Kernel 6.1, cloud ARM64)

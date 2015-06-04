#!/bin/bash
# SAmple compilation for C files
clang -emit-llvm assertfile-c.c -c -o afc.bc; clang -emit-llvm sample.c -c -o sc.bc; llvm-link afc.bc sc.bc -S -o=d.bc
opt -load ../../../Release+Asserts/lib/LLVMTressa.so -c-asserts -S < d.bc > d1.bc; clang -o d1 d1.bc

printf "C files compiled. Run ./d1\n"
printf  "|+++++++++++++++++++++++++++++++++++++++++++++++++++++++|\n"

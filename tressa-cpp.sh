#!/bin/bash
# Sample compilation for C++ files
clang++ -emit-llvm assertfile.cpp -c -o af.bc; clang++ -emit-llvm queue.cpp -c -o q.bc; llvm-link af.bc q.bc -S -o=c.bc
opt -load ../../../Release+Asserts/lib/LLVMToy.so -cpp-asserts -S < c.bc > c1.bc; clang++ -o c1 c1.bc

echo "C++ files compiled. Run ./c1\n"

#!/bin/bash
# Make Tressa for LLVM
cd ~/llvm/build/lib/Transforms/Tressa
make
cp ~/llvm/build/Debug+Asserts/lib/LLVMTressa.so ~/llvm/build/Release+Asserts/lib/


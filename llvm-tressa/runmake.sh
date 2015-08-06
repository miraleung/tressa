#!/bin/bash
# Make Tressa for LLVM
DIR=$HOME
cd $DIR/llvm/build/lib/Transforms/Tressa
make
cp $DIR/llvm/build/Debug+Asserts/lib/LLVMTressa.so $DIR/llvm/build/Release+Asserts/lib/


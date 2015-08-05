## Installation
1. **Prerequisite.** LLVM version 3.5 built from source, Clang version 3.7.
2. Copy `llvm-tressa` to `lib/Transforms/Tressa` under LLVM's source directory.
3. Run `runmake.sh` in `llvm-tressa`. If your LLVM directory is not in $HOME, change the `$DIR` path in this script.
4. In the `Makefile` of the target project to compile, add `LLVMTressa.so` with the `-c-asserts` flag.
  1. e.g. `opt -load=LLVMTressa.so -c-asserts -o $@ $<`

For an example on using Tressa to compile individual source files, see `tressa-c.sh` of `tressa-cpp.sh` under `llvm-tressa-samples/`. These scripts may have to be `chmod`-ed to get the appropriate user permissions.


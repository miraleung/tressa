## Installation
1. **Prerequisite.** LLVM version 3.5+ built from source, [Clang](http://clang.llvm.org/) version 3.7.
  - Packages [here](http://llvm.org/apt/), installation instructions [here](http://clang.llvm.org/get_started.html).
  - [Intro guide to LLVM](http://adriansampson.net/blog/llvm.html).
2. Copy `llvm-tressa` to `lib/Transforms/Tressa` under LLVM's source directory.
3. Run `runmake.sh` in `llvm-tressa`. If your LLVM directory is not in $HOME, change the `$DIR` path in this script.
4. Set Clang to be the compiler for the target project.
5. In the `Makefile` of the target project to compile, add `LLVMTressa.so` with the `-c-asserts` flag.
  - e.g. `opt -load=LLVMTressa.so -c-asserts -o $@ $<`
6. For Tressa to work properly, turn off compile-time optimization flags.
  - Variable names and block labels in the compiled LLVM IR (intermediate representation) are changed by optimizations such as basic block coalescing, constant folding, and common subexpression elimination. This makes insertion points and local variables (in the targeted function) undetectable in the function to be inserted.

For an example on using Tressa to compile individual source files, see `tressa-c.sh` of `tressa-cpp.sh` under `llvm-tressa-samples/`. These scripts may have to be `chmod`-ed to get the appropriate user permissions.

## Usage
1. Function headers and globals are assumed to be declared in a separate header file for the targeted source code (where calls will be inserted).
2. Functions to insert must be prefixed with `_assertfn_`, followed by an arbitrary, unique identifier.
3. Arguments to this function (the "assert function") are as follows:
  - The first argument must be named the same as the targeted function (where the call to this assert function will be inserted)
  - If this assert function needs to use local variables or arguments to the targeted function, they must be listed in the arguments to the `_assertfn_` function.
  - The insertion point will also be an argument to this function, prefixed with `_tressa_`. Currently-implemented insertion points include the below, and are indexed in order of appearance in the targeted function.
    - Post-`if` and `for` blocks
    - Pre-`return` statements

[//]: <> TODO: Add examples

# Tressa
An [LLVM](http://llvm.org/docs/GettingStarted.html) plugin to insert function calls in C/C++ source code.

## Example
A call to `_assertfn_fn_1` will be inserted just before the return from the function `doit`.

##### Developer-facing C source code

![Target function](https://github.com/miraleung/tressa/raw/master/screenshots/target-fn-c-src.png)

![Assert function](https://github.com/miraleung/tressa/raw/master/screenshots/assert-fn-c-src.png)

The LLVM IR before and after the Tressa pass looks like the following.

##### Before

![LLVM IR pre-Tressa pass](https://github.com/miraleung/tressa/raw/master/screenshots/target-fn-asm-before.png)

##### After
![LLVM IR after running the Tressa pass](https://github.com/miraleung/tressa/raw/master/screenshots/target-fn-asm-after.png)

## Directories
- `llvm-tressa` -- The LLVM plugin.
- `llvm-tressa-samples` -- Example on Tressa usage.
- `scripts` -- Scripts for mining assertion predicates in Xen.
- `cdfscripts` -- More scripts for Xen assertion predicate mining and data for CDF plots.



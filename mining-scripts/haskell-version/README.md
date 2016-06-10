# Haskell Scripts
If you're looking for general usage information for repository-mining with CDF, then go up to the parent directory. Here, we describe features unique to *these* scripts.

### GetPredicates
The `GetPredicates` program extracts ASSERT statements from patches or source files. In order to compile it (stand-alone), run the following command:
``` 
ghc -O2 GetPredicates.hs -o GetPredicates
```
 
Now this can be run against a source file:

``` 
./GetPredicates ~/linux_source/arch/x86/kvm/mmu.c output
```

The last argument (`output`) is a "temp" file where the output is concatenated (even though the same output is printed out to the console).



It is now possible to gather all the assert statements in linux:


```
for f in `find ~/linux_source/ -iname "*.[ch]"`; do ./GetPredicates $f linux_asserts; done
```
 


This should get all the ASSERT statements in any .c or .h files in the entire linux source tree and collect them in a file called `linux_asserts`. `GetPredicates` doesn't print the name of the file or the line number where the assert was found.  



The file name can be added to the output by modifying the above command:


```
for f in `find ~/linux_source/ -iname "*.[ch]"`; do echo "FILENAME: $f"; ./GetPredicates $f linux_asserts; done
```
 

This command will now produce an output similar to the following:
 
```
FILENAME: ~/linux_source/arch/x86/kvm/mmu.c
18 asserts found
ASSERT(is_empty_shadow_page(sp->spt))
ASSERT(!VALID_PAGE(root))
ASSERT(!VALID_PAGE(root))
ASSERT(!VALID_PAGE(root))
ASSERT(vcpu)
ASSERT(VALID_PAGE(vcpu->arch.mmu.root_hpa))
ASSERT(vcpu)
ASSERT(VALID_PAGE(vcpu->arch.mmu.root_hpa))
ASSERT(is_pae(vcpu))
ASSERT(vcpu)
ASSERT(!VALID_PAGE(vcpu->arch.mmu.root_hpa))
ASSERT(vcpu)
ASSERT(vcpu)
ASSERT(vcpu)
ASSERT(!VALID_PAGE(vcpu->arch.mmu.root_hpa))
ASSERT(vcpu)
ASSERT(!VALID_PAGE(vcpu->arch.mmu.root_hpa))
ASSERT(vcpu)
 
FILENAME: ~/linux_source/arch/x86/kvm/mmu.c
0 asserts found
```
 

Now tools (grep/sed/sort/uniq/wc/etc.) can be used on the output file (in this case `linux_asserts`) in order to count, sort, categorize, etc. the assert statements.

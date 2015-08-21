@rule exists@
idexpression struct domain *d;
identifier id, x;
expression E;
@@

// Look for a call to paging_lock()
paging_lock(d);
...
// Insert an ASSERT if a sub-element of a struct domain is written
+ASSERT(paging_locked_by_me(d));
d->id = E;
...
// Finally, make sure the access is surrounded with an unlock call
paging_unlock(d);


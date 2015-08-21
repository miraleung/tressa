@rule exists@
idexpression struct domain *d;
identifier id;
expression E, E1;
statement S;
position p1, p2;
@@

paging_lock@p1(d);
...
paging_unlock@p2(d);

@script:python@
p1 << rule.p1;
p2 << rule.p2;
@@

print "* file: %s paging_lock %s; paging_unlock %s" % (p1[0].file,p1[0].line,p2[0].line)

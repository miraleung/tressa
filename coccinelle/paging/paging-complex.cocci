@rule_set@
idexpression struct domain *d;
identifier id;
identifier func;
expression E;
position p0;
@@

func(...) {
...
d->id@p0 = E;
...
}

@rule_assert@
idexpression struct domain *d;
identifier rule_set.id;
identifier rule_set.func;
expression E;
position p1;
@@

func(...) {
...
ASERT@p1(paging_locked_by_me(d));
...
d->id = E;
...
}

@script:python depends on !rule_assert@
p0 << rule_set.p0;
@@

print "script0: file: %s: No ASSERT for access at line %s" % (p0[0].file, p0[0].line)

@script:python depends on (rule_set && rule_assert)@
p0 << rule_set.p0;
p1 << rule_assert.p1;
@@

if int(p1[0].line <= p0[0].line):
	print "script1: file: %s: ASSERT at line %s, before access at line %s" % (p0[0].file, p1[0].line, p0[0].line)

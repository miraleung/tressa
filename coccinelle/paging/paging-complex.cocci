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

@rule_lock@
idexpression struct domain *d;
identifier rule_set.id;
identifier rule_set.func;
expression E;
position p2, p3;
@@

func(...) {
...
paging_lock@p2(d);
...
d->id = E;
...
paging_unlock@p3(d);
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

@script:python depends on (rule_set && rule_lock)@
p0 << rule_set.p0;
p2 << rule_lock.p2;
p3 << rule_lock.p3;
@@

if (int(p2[0].line <= p0[0].line) and int(p3[0].line >= p0[0].line)):
	print "script1: file: %s: access at line %s protected by lock at line %s and unlock at line %s" % (p0[0].file, p0[0].file, p2[0].line, p3[0].line)

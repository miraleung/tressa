@rule_all_funcs@
identifier func;
position p0;
@@

func@p0(...) {
...
}

@rule_match@
idexpression struct domain *d;
identifier id;
identifier rule_all_funcs.func;
expression E;
@@

func(...) {
...
	E = d->id;
...
}

@rule_no_match@
idexpression struct domain *d;
identifier id;
identifier rule_all_funcs.func;
expression E;
@@

func(...) {
...
	when != E = d->id;
}


@rule_access@
idexpression struct domain *d;
identifier id;
identifier func;
expression E;
position p0;
@@

func(...) {
...
(
	d->id@p0 = E
|
	E = d->id@p0
)
...
}

@rule_assert@
idexpression struct domain *d;
identifier rule_access.id;
identifier rule_access.func;
expression E;
position rule_access.p0;
position p1;
@@

func(...) {
...
ASERT@p1(paging_locked_by_me(d));
...
(
	d->id@p0 = E
|
	E = d->id@p0
)
...
}

@rule_lock@
idexpression struct domain *d;
identifier rule_access.id;
identifier rule_access.func;
expression E;
position p2, p3;
@@

func(...) {
...
paging_lock@p2(d);
...
(
	d->id = E
|
	E = d->id
)
...
paging_unlock@p3(d);
...
}


@script:python depends on (rule_all_funcs && !rule_match && !rule_no_match)@
p << rule_all_funcs.p0;
@@

print "%s: function at line %s has a branch that matches and a branch that doesn't match statement" % (p[0].file, p[0].line)


@script:python depends on rule_access@
p0 << rule_access.p0;
@@

print "script0: %s: access at line %s" % (p0[0].file, p0[0].line)

@script:python depends on (!rule_assert && !rule_lock)@
p0 << rule_access.p0;
@@

print "script1: WARNING: %s: access at line %s NOT protected by an ASSERT or locks" % (p0[0].file, p0[0].line)

//@script:python depends on (rule_access && rule_assert)@
@script:python depends on rule_assert@
p0 << rule_access.p0;
p1 << rule_assert.p1;
@@

if int(p1[0].line <= p0[0].line):
	print "script2: INFO: %s: access at line %s protected by ASSERT at line %s" % (p0[0].file, p0[0].line, p1[0].line)

@script:python depends on (rule_access && rule_lock)@
p0 << rule_access.p0;
p2 << rule_lock.p2;
p3 << rule_lock.p3;
@@

if (int(p2[0].line <= p0[0].line) and int(p3[0].line >= p0[0].line)):
	print "script3: INFO: %s: access at line %s protected by lock at line %s and unlock at line %s" % (p0[0].file, p0[0].line, p2[0].line, p3[0].line)

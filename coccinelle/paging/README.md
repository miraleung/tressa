Example of running coccinelle:

spatch -sp-file paging.cocci paging.c

If a function has a conditional where a statement both happens and doesn't happen:

	if ()
	{
		i = d->id;
	}
	else
	{
		...
	}

then coccinelle will not match it with a rule looking to match the statement:

	@rule_match@
	idexpression struct domain *d;
	identifier id;
	expression E;
	@@

	func(...) {
	...
		E = d->id;
	...
	}

nor will it match it with a rule looking to *not* match the statement:

	@rule_no_match@
	idexpression struct domain *d;
	identifier id;
	expression E;
	@@

	func(...) {
	...
		when != E = d->id;
	}

The way to find a case like this is to match all functions, then match those against both the rule_match and rule_no_match rules:

	@rule_all_funcs@
	identifier func;
	position p0;
	@@

	func@p0(...) { ... }

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

We can then find these cases in a script by finding a match in rule_all_funcs which is also not a match in rule_match and not a match in rule_no_match:

	@script:python depends on (rule_all_funcs && !rule_match && !rule_no_match)@
	p0 << rule_all_funcs.p0;
	@@

	print "%s: function at line %s has a branch that matches and a branch that doesn't match statement" % (p0[0].file, p0[0].line)


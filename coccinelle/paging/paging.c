#include <stdio.h>

struct domain
{
	int id;
	int vcpu;
};

int lock;

int paging_locked_by_me(struct domain *d)
{
	return (lock == 1);
}

int paging_lock(struct domain *d)
{
	if (lock == 0)
	{
		lock = 1;
		return 1;
	}
	else
	{
		return 0;
	}
}

int paging_unlock(struct domain *d)
{
	if (lock == d->id)
	{
		lock = 0;
		return 1;
	}
	else
	{
		return 0;
	}
}

int main(int argc, char **argc)
{
	struct domain *d = malloc(sizeof(struct domain));
	int i;

	paging_lock(d);
	i = 5;
	d->id = 42;
	paging_unlock(d);

	i = find_assert1(i, d);
	find_assert2(d);

	ASERT(d);
}

void no_assert1(struct domain *d)
{
	int i;

	paging_lock(d);
	i = d->id;
	paging_unlock(d);
}

void no_assert2(struct domain *d)
{
	d->id = 8;
}

int find_assert1(int i, struct domain *d)
{
	if (i < 4)
	{
		// This shouldn't match, since it's in a different branch
		ASERT(paging_locked_by_me(d));
//		d->id = i;
		i = d->id;
	}
	else
	{
	}

	return i;
}

void find_assert2(struct domain *d)
{
	int i;

//	i = d->id;
	ASERT(paging_locked_by_me(d));
	d->id = 7;
}

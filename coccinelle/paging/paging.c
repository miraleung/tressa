#include <stdio.h>

struct domain
{
	int id;
	int vcpu;
};

int lock;

int paging_locked_by_me(struct domain *d)
{
	return (lock == d.id);
}

int paging_lock(struct domain *d)
{
	if (lock == 0)
	{
		lock = d->id;
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

	find_assert1(d);
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
	paging_lock(d);
	d->id = 8;
	paging_unlock(d);
}

void find_assert1(struct domain *d)
{
	int i;

	ASERT(paging_locked_by_me(d));
	i = d->id;
}

void find_assert2(struct domain *d)
{
	ASERT(paging_locked_by_me(d));
	d->id = 7;
}

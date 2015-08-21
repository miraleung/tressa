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
	test(d);
	paging_unlock(d);
}

void foo()
{
	struct domain *d = malloc(sizeof(struct domain));
	int i;

	paging_lock(d);
	i = d->id;
	paging_unlock(d);
}

void test(struct domain *d)
{
	d->id = 43;
	printf("d->id = %d\n", d->id);
}

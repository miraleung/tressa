#!/bin/bash

cd xen-unstable.hg

HEAD=`hg head | grep change | sed s'/changeset:[ ]\+\(.*\):.*/\1/'`

echo ${HEAD}

for rev in `seq 00001 ${HEAD}`
do
	zero_led_rev="$(printf "%05d" ${rev})"
	echo ${zero_led_rev}
	hg diff -c ${rev} > ../diffs/xen-diff-${zero_led_rev}.patch
done

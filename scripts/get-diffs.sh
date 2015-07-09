#!/bin/bash

SRC=xen-unstable.hg
DST=diffs

mkdir -p ${DST}

cd ${SRC}

HEAD=`hg head | grep change | sed s'/changeset:[ ]\+\(.*\):.*/\1/'`


for rev in `seq 00001 ${HEAD}`
do
	zero_led_rev="$(printf "%05d" ${rev})"
	echo ${zero_led_rev}
	hg diff -c ${rev} > ../${DST}/xen-diff-${zero_led_rev}.patch
done

#!/bin/bash

cd asserts

POS_TOTAL=0
NEG_TOTAL=0

for patch in *
do
	pos_count=`grep '^+.*ASSERT(' ${patch} | wc -l`
	neg_count=`grep '^-.*ASSERT(' ${patch} | wc -l`
	POS_TOTAL=$((POS_TOTAL+pos_count))
	NEG_TOTAL=$((NEG_TOTAL+neg_count))
done

echo Number of asserts added: ${POS_TOTAL}
echo Number of asserts removed: ${NEG_TOTAL}

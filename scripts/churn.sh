#!/bin/bash

SRC=asserts2
#SRC=test
OUT=preds

cd ${SRC}

rm -f ${OUT}
rm -f ${OUT}.sorted

for patch in *
do
	echo ${patch}

	asserts=`grep '^+.* ASSERT(' ${patch}`
	if [ -n "${asserts}" ]
	then
		while read assert
		do
			pred_pos=`echo ${assert} | sed 's/^\+.*ASSERT(\(.*\)).*/\1/'`
			if [ -n "${pred_pos}" ]
			then
				echo "+ ${pred_pos}" >> ${OUT}
			fi
		done <<< "${asserts}"
	fi

	asserts=`grep '^-.* ASSERT(' ${patch}`
	if [ -n "${asserts}" ]
	then
		while read assert
		do
			pred_neg=`echo ${assert} | sed 's/[-].*ASSERT(\(.*\)).*/\1/'`
			if [ -n "${pred_neg}" ]
			then
				echo "- ${pred_neg}" >> ${OUT}
			fi
		done <<< "${asserts}"
	fi
done

cat ${OUT} | sort | uniq -c | sort > ${OUT}.sorted

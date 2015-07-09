#!/bin/bash

SRC=`pwd`/diffs
DST=`pwd`/asserts

if [ ! -d ${SRC} ]
then
	echo ERROR: Directory ${SRC} doesn\'t exist, please run get-diffs.sh script first.
	exit 1
fi

mkdir -p ${DST}

cd ${SRC}

COUNT=0

for patch in *
do
	asserts=`grep '^[+-].*ASSERT(' ${patch}`
	if [ -n "${asserts}" ]
	then
		count=0
		while read assert
		do
			# Filter out "#define ASSERT()" statements
			no_define=`echo ${assert} | grep '.*#define.*'`
			if [ -z "${no_define}" ]
			then
				count=$((count+1))
			fi

		done <<< "$asserts"

		# If we counted at least one non-define, then copy the file
		if [ ${count} -ne 0 ]
		then
			echo ${patch} has ${count} ASSERT statements
			cp ${patch} ${DST}
		else
			echo ${patch} has no valid ASSERT statements
		fi
	else
		echo ${patch} has no ASSERT statements
	fi
done

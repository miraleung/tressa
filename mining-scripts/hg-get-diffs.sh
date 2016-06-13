#!/bin/bash

# Within a mercurial repository, creates given directory, and traverses current 
# branch creating one .patch file containing diff between each revision and its
# parent.
# Format example: diff-00N.patch


E_BADARGS=85
if [[ $# -ne 1 ]]
then
    echo "Usage: $(basename $0) <diff_out_dir>"
    exit $E_BADARGS
fi

DST=$1
mkdir -p ${DST}

echo "Generating patches for tip in directory: $DST"
echo

hg update tip > /dev/null
HEAD=`hg parent | grep change | sed s'/changeset:[ ]\+\(.*\):.*/\1/'`

for rev in `seq 00001 ${HEAD}`
do
    
    zero_led_rev="$(printf "%05d" ${rev})"
    echo ${zero_led_rev}
    hg diff -c ${rev} > ${DST}/diff-${zero_led_rev}.patch
done

#!/bin/bash

# Within a Mercurial repository, creates directory ./diffs and fills it with
# one .patch file for each diff between revisions in the log

# Precondition: must be within a Mercurial repo 
# Postcondition: ./diffs directory exists containing diff-N.patch files for to
#   tip branch.




DST=diffs

mkdir -p ${DST}

hg update tip > /dev/null
HEAD=`hg parent | grep change | sed s'/changeset:[ ]\+\(.*\):.*/\1/'`

for rev in `seq 00001 ${HEAD}`
do
    
    zero_led_rev="$(printf "%05d" ${rev})"
    echo ${zero_led_rev}
    hg diff -c ${rev} > ${DST}/diff-${zero_led_rev}.patch
done

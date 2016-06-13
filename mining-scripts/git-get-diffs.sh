#!/bin/bash

# Within a git repository, creates given directory, and traverses current branch,
# creating one .patch file containing diff between each revision and its parent.
# Format example: 00N-abbrevchecksum.patch

E_BADARGS=85
if [[ $# -ne 1 ]]
then
    echo "Usage: $(basename $0) <diff_out_dir>"
    exit $E_BADARGS
fi

DST=$1
BRANCH=$(git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/')
mkdir -p ${DST}

echo "Generating patches for '$BRANCH' branch in directory: $DST"
echo

count=$(git rev-list --count $BRANCH)
count_char_len=${#count}
for rev in $(git rev-list $BRANCH)
do
    zero_led_count="$(printf "%0${count_char_len}d" ${count})"
    echo "${zero_led_count} ${rev}"
    git log -p -1 -U5 ${rev} > ${DST}/${zero_led_count}-${rev:0:7}.patch 
        # -p    print diff with parent (unless merge)
        # -1    only print one log entry
        # -U5   give 5 lines of context instead of default 3
    (( count-- )) 
done


#!/bin/bash

# Clone all repos in an organization (TressOrg) on github. 
# Don't forget to remove tressa and tressa_test_repo afterwards, since they
# aren't experiment repos

# Dependencies:
#   - curl
#   - jq (command-line json parsing tool https://stedolan.github.io/jq/)


curl https://api.github.com/orgs/TressaOrg/repos?per_page=100 | jq '.[] | .clone_url' | xargs -L1 git clone


# Now set the branch CasalnuovoPaper for each on on the latest commit before
# July 20, 2014 (Casey Casalnuovo didn't have the commit numbers, but he did
# say in an email that that was the last date of their cloning.)
#for dir in */
    #do
        #cd $dir
        #git log --before="2014-07-21" -1 --format="%H" | xargs git branch CasalnuovoPaper
        #cd ..
    #done

## Having set the Head Branch (in a oneoff commandline script, apparently) to Tressa,
## as well as the CasalnuovoPaper branch, this is how we push that info back up.

#for dir in */
    #do
        #cd $dir
        #git push origin Tressa
        #git push origin CasalnuovoPaper
        #cd ..
    #done



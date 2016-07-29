# Walks the given repos, storing logs, printouts (.asserts), and pickled 
# history objects for each.

import logging
logging.basicConfig(level=logging.DEBUG, filename="walk_repos.log")

import os
import assertions
import pickle
import traceback
import itertools
import time
import datetime


if __name__ == '__main__':
    dirs = os.listdir(".")
    dirs = itertools.filterfalse(lambda d: d.endswith(".py") or d.endswith(".log")
                                    or d in ['results', '__pycache__'], dirs)
    dirs = list(dirs)

    starttime = time.time()
    lasttime = starttime
    for i,d in enumerate(dirs):
        print("{d}   {i}/{n}".format(d=d, i=i+1, n=len(dirs)))
        try:
            hist = assertions.mine_repo("\w*(ASSERT|assert|BUG_ON|bug_on)\w*", d, "Tressa")
            with open('results/' + d + '.pickle', 'wb') as f:
                pickle.dump(hist, f)
            with open('results/' + d + '.asserts', 'w') as f:
                for a in hist:
                    f.write(a.info() + "\n")
        except:
            traceback.print_exc()
        thistime = time.time()
        print("\t{d}, total {t}".format(
            d=datetime.timedelta(seconds=thistime-lasttime),
            t=datetime.timedelta(seconds=thistime-starttime)))
        lasttime = thistime


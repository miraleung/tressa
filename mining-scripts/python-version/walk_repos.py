# Walks the given repos, storing logs, printouts (.asserts), and pickled 
# history objects for each.

import logging

import os
import sys
import assertions
import pickle
import traceback
import itertools
import time
import datetime

import analysis

def mine():
    logging.basicConfig(level=logging.DEBUG, filename="walk_repos_mine.log")

    dirs = os.listdir(".")
    dirs = itertools.filterfalse(lambda d: d.endswith(".py") or d.endswith(".log")
                                    or d in ['results', '__pycache__'], dirs)
    dirs = list(dirs)

    starttime = time.time()
    lasttime = starttime
    for i,d in enumerate(dirs):
        print("{d}   {i}/{n}".format(d=d, i=i+1, n=len(dirs)), flush=True)
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
                t=datetime.timedelta(seconds=thistime-starttime)),
            flush=True)
        lasttime = thistime

def analyze():
    """Assumes results/ dir populates with pickled files as from mining above.
    Produces csv and png of graphs for some statistics
    """

    logging.basicConfig(level=logging.DEBUG, filename="walk_repos_analyze.log")

    files = os.listdir("results")
    files = [f for f in files if f.endswith(".pickle")]

    starttime = time.time()
    lasttime = starttime

    for i, file in enumerate(files):
        print("{d}   {i}/{n}".format(d=file, i=i+1, n=len(files)), flush=True)

        try:
            h = analysis.load_history("results/" + file)

            repo = file[:-len(".pickle")]

            def result_save(fun, filename):
                r = fun(h)
                prefix = "results/{repo}_{stat}".format(repo=repo, stat=filename)
                r.graph(25, prefix + ".png")
                r.csv(prefix + ".csv")

            result_save(analysis.names_result, "names")
            result_save(analysis.dist_result, "distance")
            result_save(analysis.time_result, "time")
            result_save(analysis.activity_result, "activity")
        except:
            traceback.print_exc()

        thistime = time.time()
        print("\t{d}, total {t}".format(
            d=datetime.timedelta(seconds=thistime-lasttime),
            t=datetime.timedelta(seconds=thistime-starttime)),
            flush=True)
        lasttime = thistime



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " [mine|analyze]")
        sys.exit(-1)

    if sys.argv[1] == "mine":
        mine()
    elif sys.argv[1] == "analyze":
        analyze()
    else:
        print("Usage: " + sys.argv[0] + " [mine|analyze]")
        sys.exit(-1)










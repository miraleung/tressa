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


# Linux and Xen have BUG_ONs
# From Github Replication paper: ut_ad in mysq/innobase; DCHECK in over a dozen
ASSERT_FMT = "\w*(ASSERT|assert|BUG_ON|bug_on|DCHECK)\w*|ut_ad?"

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
            hist = assertions.mine_repo(ASSERT_FMT, d, "Tressa")
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

            def result_save(result, filename):
                prefix = "results/{repo}_{stat}".format(repo=repo, stat=filename)
                result.graph(25, prefix + ".png")
                result.csv(prefix + ".csv")

            result_save(analysis.names_result(h), "names")
            result_save(analysis.activity_result(h), "activity")

            (com_res, atime_res, ctime_res), (lin, mon) = analysis.delta_results(h)
            result_save(com_res, "distance-commit")
            result_save(atime_res, "duration-author-time")
            result_save(ctime_res, "duration-commit-time")
            with open("results/{repo}_linearity-monotonicity.float".format(repo=repo), "w") as linf:
                linf.write(str(lin) + "\n" + str(mon))
            analysis.problematics(h, "results/{r}_".format(r=repo))

        except:
            traceback.print_exc()

        thistime = time.time()
        print("\t{d}, total {t}".format(
            d=datetime.timedelta(seconds=thistime-lasttime),
            t=datetime.timedelta(seconds=thistime-starttime)),
            flush=True)
        lasttime = thistime

def custom(func):
    """Given a function that takes a History and Filename, and produces a
    file output, applies that function the the History fromo each .pickle file
    in results/
    :func:  (History basename -> [files])
    """

    logging.basicConfig(level=logging.DEBUG, filename="walk_repos_custom.log")

    files = os.listdir("results")
    files = [f for f in files if f.endswith(".pickle")]

    starttime = time.time()
    lasttime = starttime

    for i, file in enumerate(files):
        print("{d}   {i}/{n}".format(d=file, i=i+1, n=len(files)), flush=True)

        try:
            h = analysis.load_history("results/" + file)

            repo = file[:-len(".pickle")]
            basename = "results/{repo}_".format(repo=repo)
            func(h, basename)

        except:
            traceback.print_exc()

        thistime = time.time()
        print("\t{d}, total {t}".format(
            d=datetime.timedelta(seconds=thistime-lasttime),
            t=datetime.timedelta(seconds=thistime-starttime)),
            flush=True)
        lasttime = thistime

def onecommitscores(path):
    """Information regarding rebasing of a commit. Turns out to be useless info"""
    files = os.listdir(path)
    files = [path + f for f in files if f.endswith(".pickle")]


    repo_oneness = ((lambda h: (h.repo_path, analysis.onecommit_score(h)))(analysis.load_history(f)) for f in files)

    with open("one_committness.csv", "w") as ocf:
        for ro in repo_oneness:
            ocf.write("{n},{o}\n".format(n=ro[0], o=ro[1]))


def cprojects(path):
    """Print names of repos that have mostly C only source files"""
    files = os.listdir(path)
    files = [path + f for f in files if f.endswith(".pickle")]

    for file in files:
        h = analysis.load_history(file)
        if analysis.is_cproject(h):
            print(h.repo_path)


if __name__ == '__main__':
    USAGE = "Usage: " + sys.argv[0] + " [mine|analyze|custom|[oncecommit|cprojects] <path>]"

    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print(USAGE)
        sys.exit(-1)

    if sys.argv[1] == "mine":
        mine()
    elif sys.argv[1] == "analyze":
        analyze()
    elif sys.argv[1] == "custom":
        custom(analysis.problematics)
    elif sys.argv[1] == "onecommit":
        path = sys.argv[2]
        onecommitscores(path)
    elif sys.argv[1] == "cprojects":
        path = sys.argv[2]
        cprojects(path)
    else:
        print(USAGE)
        sys.exit(-1)










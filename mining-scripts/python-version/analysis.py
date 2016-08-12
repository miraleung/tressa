# functions for producing analyses of History data
import pickle
from collections import defaultdict, OrderedDict, Counter, namedtuple
import itertools
import numpy as np
import matplotlib.pyplot as plt
from textwrap import wrap
from datetime import datetime, timezone, timedelta
import csv as Csv
import io
from enum import Enum
import numpy as np
import sys

import logging


import assertions


class DataPoint():
    def __init__(self, x_val="", y_added=0, y_removed=0, y_combined=0):
        self.x_val = x_val
        self.y_added = y_added
        self.y_removed = y_removed
        self.y_combined = y_combined

    def __repr__(self):
        return "DataPoint(x_val={x}, y_added={ya}, y_removed={yr}, y_combined={yc})" \
                .format(x=self.x_val, ya=self.y_added, yr=self.y_removed, yc=self.y_combined)

    @staticmethod
    def keys():
        return ["x_val", "y_added", "y_removed", "y_combined"]

    def values(self):
        return [self.x_val, self.y_added, self.y_removed, self.y_combined]

    def __iter__(self):
        yield self.x_val
        yield self.y_added
        yield self.y_removed
        yield self.y_combined

    def __eq__(self, o):
        return (self.x_val == o.x_val and
                self.y_added == o.y_added and
                self.y_removed == o.y_removed and
                self.y_combined == o.y_combined)



class Result():
    class Tail(Enum):
        """Each Tail has a textual display and a function that, when applied
        to a list of y-values, produces a result for that column.
        """
        Max = ("Maximums", max)
        Avg = ("Averages", np.mean)
        Sum = ("Sums", sum)
        def  __init__(self, text, func):
            self.text = text
            self.func = func

    def __init__(self, id, datapoints, desc, x_label, y_label, sort=None,
            tail=Tail.Avg):
        """Prouce Result from list of DataPoints
        :sort:  if given sorting function, then sorts from Biggest to smallest
        :datapoints:    iter(Datapoint)
        :id:          (string) repo/project name
        :tail:      (Result.Tail) When graphing, how to condense the remaining
                    values, if truncating Typically, if datapoints are
                    x-sorted, Max ensures we
                    aren't missing anything important, and if y-sorted, Avg
                    ensures that the rest are of little consequence.
        """

        self.id = id
        self.description = desc
        self.x_label = x_label
        self.y_label = y_label
        self.datapoints = datapoints if sort is None else \
                          sorted(datapoints, key=sort, reverse=True)
        self.tail = tail

    def csv(self, save):
        def write_csv(file):
            writer = Csv.writer(file, quoting=Csv.QUOTE_MINIMAL)
            writer.writerow(DataPoint.keys())
            for dp in self.datapoints:
                writer.writerow(dp.values())

        with open(save, 'w', newline='') as file:
            write_csv(file)

    def graph(self, length=None, save=None, filt=None):
        """Produce graph of results. Applies given filters, if available.
        :length:    (int) max number DataPoints to plot
        :save:      (string) instead of displaying out, save under this filename
        :filt:      (pred func) filter out DataPoints that produce False
        """

        # Filter if necessary
        def true_fun(dp): return True

        dps = self.datapoints

        filt_fun = filt if filt else true_fun
        cutoff_fun = lambda dp: dp >= cutoff if cutoff else true_fun

        if filt_fun or cutoff_fun:
            filter(lambda dp: filt_fun(dp) and cutoff_fun(dp), dps)

        if length is not None: # and length < len(dps): confusing if tail isn't always shown
            dps = dps[:length]
            tail = self.datapoints[length:]
            tail_dp = DataPoint("{n} Remaining; {t}" \
                        .format(n=len(tail), t=self.tail.text),
                    self.tail.func([dp.y_added for dp in tail]),
                    self.tail.func([dp.y_removed for dp in tail]),
                    self.tail.func([dp.y_combined for dp in tail]))
            dps.append(tail_dp)

        # Prepare graph
        length = len(dps)
        if length == 0:
            logging.info("Skipping Result of length 0")
            return

        x_vals, y_addeds, y_removeds, y_combineds = zip(*dps)

        xs = np.arange(length)    # the x locations for the groups
        width = 0.27              # the width of the bars

        fig, ax = plt.subplots()
        rects_adds = ax.bar(xs, y_addeds, width, color='r')
        rects_rems = ax.bar(xs+width, y_removeds, width, color='y')
        rects_coms = ax.bar(xs+(2*width), y_combineds, width, color='g')

        # add the text for labels, title and axes ticks
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_title("\n".join(wrap(self.id + ": " + self.description, 160)))
        ax.set_xticks(xs + (3*width/2.))
        ax.set_xticklabels(x_vals, rotation=45, ha='right')

        ax.legend((rects_adds[0], rects_rems[0], rects_coms[0]),
            ('Added', 'Removed', 'Combined'))

        def autolabel(rects):
            # attach some text labels
            for rect in rects:
                height = rect.get_height()
                fmt = "{:g}" if height == int(height) else "{:.1g}"
                ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                        fmt.format(height),
                        ha='center', va='bottom')

        autolabel(rects_adds)
        autolabel(rects_rems)
        autolabel(rects_coms)

        fig.set_size_inches(25,13, forward=True)
        fig.set_dpi(80)
        fig.set_tight_layout(True)

        if save:
            fig.savefig(save)
            fig.clf()
        else:
            fig.show()


def delta_counts(hist_deltaed, change=None):
    """
    Produce 3-tuple of Counters for distances/durations between commits containing
    assertions. (#commits, #author-time days, #commit-time days)

    :change: if assertions.Change given, only counts differences between
        commits that include change of that type.
    """
    def has_change(diff):
        for file in diff.files:
            for a in file.assertions:
                if change is None or change == a.change:
                    return True
        return False

    diffs = (d for d in hist_deltaed.diffs if has_change(d))

    commits_counter = Counter()
    atime_counter = Counter()
    ctime_counter = Counter()

    for diff in diffs:
        delta = diff.delta
        if delta.has_result():
            commits_counter[delta.commit_dist] += 1
            atime_counter[delta.atime_dur.days] += 1
            ctime_counter[delta.ctime_dur.days] += 1

    return commits_counter, atime_counter, ctime_counter

def delta_result(history, counters, description, x_units, linearity, start=0):
    """Produce result given (add, rem, combined) counters for same repo
    :linearity: the ratio of non-merged commits to total commits, for normalizing
    :start: the first elemeent in the list/graph, in ascending order
    """
    add_ctr, rem_ctr, com_ctr = counters

    # Find max count for scaling
    counts = itertools.chain(add_ctr.keys(), rem_ctr.keys(), com_ctr.keys())
    max_count = max(counts)

    # Produce (x, 0,0,0) when nonexistent, to ensure empty counts aren't hidden
    dps = [DataPoint(c, add_ctr[c], rem_ctr[c], com_ctr[c])
            for c in range(start, max_count+1)]

    return Result(history.repo_path,
                  dps,
                  description + " -- Linearity: {:%}".format(linearity),
                  x_units,
                  "Counts",
                  sort=lambda dp: -dp.x_val,
                  tail=Result.Tail.Max)

def delta_results(history):
    """Produce result 3-tuple for given history. Output is 2-tuple, made of
    3-tuple counters, and linearity score (non_merge_commits/total_commits):
    (commit_distance, author_time duration, commit_time duration), linearity
    """
    insert_deltas(history)
    add_com_ctr, add_atime_ctr, add_ctime_ctr = delta_counts(history, assertions.Change.added)
    rem_com_ctr, rem_atime_ctr, rem_ctime_ctr = delta_counts(history, assertions.Change.removed)
    comb_com_ctr, comb_atime_ctr, comb_ctime_ctr = delta_counts(history)

    # for normalizing results (i.e., ignoring rebase-policy repos)
    num_merges = sum(1 for d in history.diffs if d.delta.num_visits > 1)
    linearity = 1 - (num_merges/len(history.diffs))


    commit_result = delta_result(history,
            (add_com_ctr, rem_com_ctr, comb_com_ctr),
            "Number of Revisions between commits containing assertions "
                "('Combined' commits can have either Added or Removed)",
            "Number of Revisions",
            linearity,
            start=1)

    atime_result = delta_result(history,
            (add_atime_ctr, rem_atime_ctr, comb_atime_ctr),
            "Duration between commits containing assertions - author_time "
                "('Combined' commits can have either Added or Removed)",
            "Author Days",
            linearity,
            start=0)

    ctime_result = delta_result(history,
            (add_ctime_ctr, rem_ctime_ctr, comb_ctime_ctr),
            "Duration between commits containing assertions - commit_time "
                "('Combined' commits can have either Added or Removed)",
            "Commit Days",
            linearity,
            start=0)

    return (commit_result, atime_result, ctime_result), linearity


# def dist_btw_assert_commits(history, change=None):
    # """Determine the number of commits between each assertion-event commit and
    # groups distances by frequency into a collections.Counter {distance: count}.
    # Caveat: Uses Assertion.commit_index which is partly determined by repo
    # commit-walk scheme (e.g., GIT_SORT_TOPOLOGICAL)

    # :change: if assertions.Change given, only counts differences between
        # commits that include change of that type.
    # """

    # diffs = [d for d in history.diffs if has_change(d)]
    # return Counter(d_next.commit_index - d.commit_index for d, d_next in
            # zip(diffs, _next_iter(diffs)))


# def dist_result(history):
    # # Generate counts
    # dadd = dist_btw_assert_commits(history, assertions.Change.added)
    # drem = dist_btw_assert_commits(history, assertions.Change.removed)
    # dcom = dist_btw_assert_commits(history)

    # # Isolate just the counts to find the max
    # counts = itertools.chain(dadd.keys(), drem.keys(), dcom.keys())
    # max_count = max(counts)

    # # Produce (x, 0,0,0) when nonexistant, to ensure empty counts aren't hidden
    # dps = [DataPoint(c, dadd[c], drem[c], dcom[c]) for c in range(1,max_count+1)]

    # return Result(history.repo_path,
                  # dps,
                  # "Distance in COMMITS between commits containing assertions "
                  # "('Combined' commits can have either Added or Removed)",
                  # "Distances",
                  # "Counts",
                  # sort=lambda dp: -dp.x_val,
                  # tail=Result.Tail.Max)



# def time_btw_assert_commits(history, change=None):
    # """Determine the number of DAYS between each assertion-event commit and
    # groups durations by frequency into a collections. Counter {duration: count}.
    # Uses author_time.

    # :change: if assertions.Change given, only counts differences between
        # commits that include change of that type.
    # """
    # def has_change(diff):
        # for file in diff.files:
            # for a in file.assertions:
                # if change is None or change == a.change:
                    # return True
        # return False

    # diffs = [d for d in history.diffs if has_change(d)]
    # return Counter(time_diff(d_next.author_time, d.author_time).days for d, d_next in
        # zip(diffs, _next_iter(diffs)))

# def time_result(history):
    # # Generate counts
    # dadd = time_btw_assert_commits(history, assertions.Change.added)
    # drem = time_btw_assert_commits(history, assertions.Change.removed)
    # dcom = time_btw_assert_commits(history)

    # # Isolate just the counts to find the max
    # counts = itertools.chain(dadd.keys(), drem.keys(), dcom.keys())
    # max_count = max(counts)

    # # Produce (x, 0,0,0) when nonexistant, to ensure empty counts aren't hidden
    # dps = [DataPoint(c, dadd[c], drem[c], dcom[c]) for c in range(max_count)]

    # return Result(history.repo_path,
                  # dps,
                  # "Number of DAYS between commits containing assertions "
                      # "('Combined' commits can have either Added or Removed)",
                  # "Durations",
                  # "Counts",
                  # sort=lambda dp: -dp.x_val,
                  # tail=Result.Tail.Max)


def make_time(timetz):
    tz = timezone(timedelta(minutes=timetz[1]))
    time = datetime.fromtimestamp(timetz[0], tz)
    return time


def time_diff(time2, time1): # (seconds2, offset2) - (seconds1, offset1)
    """Produce timedelta between time2 and time1"""
    t2 = make_time(time2)
    t1 = make_time(time1)

    dtime = t2 - t1
    return dtime


class Delta():
    def __init__(self, num_commits=sys.maxsize,
            last_atime=(int(datetime.min.timestamp()), 0),
            last_ctime=(int(datetime.min.timestamp()), 0)):
        self.num_commits = num_commits # if sys.maxsize, no asserts found yet
        self.last_atime = last_atime   # if datetime.min, no asserts found yet
        self.last_ctime = last_ctime
        self.commit_dist = sys.maxsize
        self.atime_dur = timedelta.max
        self.ctime_dur = timedelta.max
        self.num_visits = 0             # not included in __eq__

    def has_result(self):
        return self.commit_dist < sys.maxsize

    def __eq__(self, o):
        return (self.num_commits == o.num_commits and
                self.last_atime  == o.last_atime  and
                self.last_ctime  == o.last_ctime  and
                self.commit_dist == o.commit_dist and
                self.atime_dur   == o.atime_dur   and
                self.ctime_dur   == o.ctime_dur)
                # not including num_visits

    def __repr__(self):
        lat = make_time(self.last_atime).strftime("%Y-%m-%d")
        lct = make_time(self.last_ctime).strftime("%Y-%m-%d")
        return "Delta<{nc:g}, {lat}, {lct}, {dist:g}, {ad:g}, {cd:g}, {nv:g}>" \
                .format(nc=self.num_commits, lat=lat, lct=lct,
                        dist=self.commit_dist, ad=self.atime_dur.days, cd=self.ctime_dur.days,
                        nv=self.num_visits)


def has_good_assert(diff):
    if hasattr(diff, "files"):
        for file in diff.files:
            if hasattr(file, "assertions"):
                if len(file.assertions) > 0:
                    return True
    return False


def insert_deltas(history):
    """If deltas haven't been added to history.diffs yet, then the commit
    dag is traversed and they are added.
    There was perviously a recursive version. The iterative version was
    needed because many repos have so many commits that it exceeds the
    stack depth.
    """

# Explanation of 8 different cases:
# visit_diff(diff, prev_delta)
#
# first_visit !seen_asert has_asserts
# ------------------------------------
# diff.delta  pre_del.num has_asserts |
# None        None        yes         |   delta(0, times)
# None(1st v) None        no          |   delta(maxsize, Minyear)
# None        val         yes         |   delta(0, times); delta.dist=pdelta+1;
# None        val (preva) no          |   delta(prev.num_commits+1)
# exists      None        yes         |   do nothing
# exists      None        no          |   do nothing
# exists      val         yes         |   delta.dist/durs = min(d, p.num_commits++; difftime-p.lasts)
# exists      val         no          |   delta.nc = min(d, pd+1); delta.times = max(d, pd)
#
# num_visits == num parents -> do this last: for child in childs:visit_diff(child, delta)

    def visit_diff(diff_delta, todo):
        """Visit each diff, and create its Delta
        :todo: is a stack of diffs to visit
        """
        diff, prev_delta = diff_delta

        first_visit = not hasattr(diff, 'delta')
        seen_assert = prev_delta.num_commits != sys.maxsize
        has_asserts = has_good_assert(diff)

        if first_visit and not seen_assert and has_asserts:
            diff.delta = Delta(0, diff.author_time, diff.commit_time)

        elif first_visit and not seen_assert and not has_asserts:
            diff.delta = Delta()

        elif first_visit and seen_assert and has_asserts:
            diff.delta = Delta(0, diff.author_time, diff.commit_time)
            diff.delta.commit_dist = prev_delta.num_commits+1
            diff.delta.atime_dur = time_diff(diff.author_time, prev_delta.last_atime)
            diff.delta.ctime_dur = time_diff(diff.commit_time, prev_delta.last_ctime)

        elif first_visit and seen_assert and not has_asserts:
            diff.delta = Delta(prev_delta.num_commits+1,
                               prev_delta.last_atime, prev_delta.last_ctime)

        elif not first_visit and not seen_assert:
            pass

        elif not first_visit and seen_assert and has_asserts:
            diff.delta.commit_dist = min(diff.delta.commit_dist, prev_delta.diff+1)
            diff.delta.atime_dur = min(diff.delta.atime_dur,
                    time_diff(diff.author_time, prev_delta.last_atime))
            diff.delta.ctime_dur = min(diff.delta.ctime_dur,
                    time_diff(diff.commit_time, prev_delta.last_ctime))

        elif not first_visit and seen_assert and not has_asserts:
            diff.delta.num_commits= min(diff.delta.commit_dist, prev_delta.num_commits+1)
            diff.delta.last_atime = max(diff.delta.last_atime, prev_delta.last_atime)
            diff.delta.last_ctime = max(diff.delta.last_ctime, prev_delta.last_ctime)

        else:
            raise Exception("Diff visited with impossible state:\n\t" +
                    "first_visit={fv}, seen_assert={sa}, has_asserts={ha}" \
                            .format(fv=first_visit, sa=seen_assert, ha=has_asserts))

        diff.delta.num_visits += 1
        if diff.delta.num_visits >= len(diff.parents):
            # >= instead of == since first has no parents
            # each path previous path has now arrived here
            todo.extend((history.get_diff(cid), diff.delta) for cid in diff.children)

    first_diff = next(iter(history.diffs))
    todo = [(first_diff, Delta())]

    while len(todo) > 0:
        diff_delta = todo.pop()
        visit_diff(diff_delta, todo)


def activity_result(history):
    predicates = defaultdict(lambda: DataPoint("", 0,0,0))
    for a in assertions.assertion_iter(history, inspects=False):
        dp = predicates[assertions.remove_whitespace(a.predicate)]
        dp.x_val = a.predicate
        if a.change == assertions.Change.added:
            dp.y_added += 1
            dp.y_combined += 1
        elif a.change == assertions.Change.removed:
            dp.y_removed += 1
            dp.y_combined += 1
        else:
            logging.warning("{c} found while calculating Activity for {a}"
                    .format(c=a.change, a=a.info()))

    return Result(history.repo_path,
            predicates.values(),
            "Number of assertion events for each predicate, by text comparison",
            "Predicates",
            "Events",
            sort=lambda dp: dp.y_combined,
            tail=Result.Tail.Avg)

def names_result(history):
    names = defaultdict(lambda: DataPoint("", 0,0,0))
    for a in assertions.assertion_iter(history, inspects=False):
        dp = names[a.name]
        dp.x_val = a.name
        if a.change == assertions.Change.added:
            dp.y_added += 1
            dp.y_combined += 1
        elif a.change == assertions.Change.removed:
            dp.y_removed += 1
            dp.y_combined += 1
        else:
            logging.warning("{c} found while calculating Names for {a}"
                    .format(c=a.change, a=a.info()))

    return Result(history.repo_path,
            names.values(),
            "Number of assertion events for each assert-function-name",
            "Names",
            "Events",
            sort=lambda dp: dp.y_combined,
            tail=Result.Tail.Avg)


# def function_result(history):
    # # This isn't useful due to inaccuracy of functinon_name
    # """Produce result of the function in which the assert is embedded."""
    # functions = defaultdict(lambda: DataPoint("", 0,0,0))
    # for a in assertions.assertion_iter(history, inspects=False):
        # dp = functions[a.function_name]
        # dp.x_val = a.function_name
        # if a.change == assertions.Change.added:
            # dp.y_added += 1
            # dp.y_combined += 1
        # elif a.change == assertions.Change.removed:
            # dp.y_removed += 1
            # dp.y_combined += 1
        # else:
            # logging.warning("{c} found while calculating Functions for {a}"
                    # .format(c=a.change, a=a.info()))

    # return Result(functions.values(),
            # "Number of assertion events embedded within each function/method",
            # "Functions/methods",
            # "Events",
            # sort=lambda dp: dp.y_combined)



# TODO dist from major release
# TODO dist between commits for particular predicates?
# TODO asserts per function



def _next_iter(it):
    nexts = iter(it)
    next(nexts)
    return nexts



def load_history(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)






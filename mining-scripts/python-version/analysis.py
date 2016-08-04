# functions for producing analyses of History data
import pickle
from collections import defaultdict, OrderedDict, Counter, namedtuple
import itertools
import numpy as np
import matplotlib.pyplot as plt
from textwrap import wrap
import datetime
import csv as Csv
import io
from enum import Enum
import numpy as np

import logging


import assertions


# DataPoint = namedtuple('DataPoint', ['x_val', 'y_added', 'y_removed', 'y_combined'])
# I need it to be mutable sometimes, so a class it is.

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

        if length is not None and length < len(dps):
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

def dist_btw_assert_commits(history, change=None):
    """Determine the number of commits between each assertion-event commit and
    groups distances by frequency into a collections.Counter {distance: count}.
    Caveat: Uses Assertion.commit_index which is partly determined by repo
    commit-walk scheme (e.g., GIT_SORT_TOPOLOGICAL)

    :change: if assertions.Change given, only counts differences between
        commits that include change of that type.
    """
    def has_change(diff):
        for file in diff.files:
            for a in file.assertions:
                if change is None or change == a.change:
                    return True
        return False

    diffs = [d for d in history.diffs if has_change(d)]
    return Counter(d_next.commit_index - d.commit_index for d, d_next in
            zip(diffs, _next_iter(diffs)))



def dist_result(history):
    # Generate counts
    dadd = dist_btw_assert_commits(history, assertions.Change.added)
    drem = dist_btw_assert_commits(history, assertions.Change.removed)
    dcom = dist_btw_assert_commits(history)

    # Isolate just the counts to find the max
    counts = itertools.chain(dadd.keys(), drem.keys(), dcom.keys())
    max_count = max(counts)

    # Produce (x, 0,0,0) when nonexistant, to ensure empty counts aren't hidden
    dps = [DataPoint(c, dadd[c], drem[c], dcom[c]) for c in range(1,max_count+1)]

    return Result(history.repo_path,
                  dps,
                  "Distance in COMMITS between commits containing assertions "
                  "('Combined' commits can have either Added or Removed)",
                  "Distances",
                  "Counts",
                  sort=lambda dp: -dp.x_val,
                  tail=Result.Tail.Max)



def time_btw_assert_commits(history, change=None):
    """Determine the number of DAYS between each assertion-event commit and
    groups durations by frequency into a collections. Counter {duration: count}.
    Uses author_time.

    :change: if assertions.Change given, only counts differences between
        commits that include change of that type.
    """
    def has_change(diff):
        for file in diff.files:
            for a in file.assertions:
                if change is None or change == a.change:
                    return True
        return False

    def days_diff(time2, time1): # (seconds2, offset2) - (seconds1, offset1)
        tz2 = datetime.timezone(datetime.timedelta(minutes=time2[1]))
        t2 = datetime.datetime.fromtimestamp(time2[0], tz2)

        tz1 = datetime.timezone(datetime.timedelta(minutes=time1[1]))
        t1 = datetime.datetime.fromtimestamp(time1[0], tz1)

        dtime = t2 - t1
        return dtime.days

    diffs = [d for d in history.diffs if has_change(d)]
    return Counter(days_diff(d_next.author_time, d.author_time) for d, d_next in
        zip(diffs, _next_iter(diffs)))

def time_result(history):
    # Generate counts
    dadd = time_btw_assert_commits(history, assertions.Change.added)
    drem = time_btw_assert_commits(history, assertions.Change.removed)
    dcom = time_btw_assert_commits(history)

    # Isolate just the counts to find the max
    counts = itertools.chain(dadd.keys(), drem.keys(), dcom.keys())
    max_count = max(counts)

    # Produce (x, 0,0,0) when nonexistant, to ensure empty counts aren't hidden
    dps = [DataPoint(c, dadd[c], drem[c], dcom[c]) for c in range(max_count)]

    return Result(history.repo_path,
                  dps,
                  "Number of DAYS between commits containing assertions "
                      "('Combined' commits can have either Added or Removed)",
                  "Durations",
                  "Counts",
                  sort=lambda dp: -dp.x_val,
                  tail=Result.Tail.Max)


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






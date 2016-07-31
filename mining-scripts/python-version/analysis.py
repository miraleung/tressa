# functions for producing analyses of History data
import pickle
from collections import defaultdict, OrderedDict, Counter, namedtuple
import itertools
import numpy as np
import matplotlib.pyplot as plt

import assertions

def names(history):
    """Keys: assertion names
       Value list: assertions
    """
    return Analysis(history,
            lambda a: a.name,
            lambda a: a,
            include_problematic=True)

def predicates(history):
    """Keys: predicates
       Values list: asseertions
    """
    return Analysis(history,
            lambda a: assertions.remove_whitespace(a.predicate),
            lambda a: a,
            include_problematic=False)



class Analysis():
    # def __init__(self, confident, problematic):
    def __init__(self, history, keyfun, valfun, include_problematic=True):
        """For each assertion in :history:, create dict with keys from
        applying :keyfun: to assertion, and values by applying :valfun:,
        and appending to a list.
        If :include_problematic: is True, also create separate dict for
        probematics.
        """
        self.confident = defaultdict(list)
        self.problematic = defaultdict(list) if include_problematic else None
        if include_problematic:
            for a in assertions.assertion_iter(history, inspects=True):
                self.problematic[keyfun(a)].append(valfun(a))
        for a in assertions.assertion_iter(history, inspects=False):
            self.confident[keyfun(a)].append(valfun(a))

    def keys(self, problematic=False):
        kvs = self.problematic if problematic else self.confident
        return {k for k in kvs.keys()}

    def unique_confident_keys(self):
        if self.problematic == None:
            return self.confident_keys()
        return {k for k in self.confident_keys().difference(self.problematic_keys())}

    def unique_problematic_keys(self):
        return {k for k in self.problematic_keys().difference(self.confident_keys())}

    def all_results(self):
        results = self.confident.copy()
        if self.problematic == None:
            return results
        for k,v in self.problematic.items():
            results[k].extend(v)
        return results

    def counts(self, problematic=False):
        kvs = self.problematic if problematic else self.confident
        return {k:len(v) for k,v in kvs.items()}

    def counts_sorted(self, problematic=False):
        kvs = self.problematic if problematic else self.confident
        counts = self.counts(problematic)
        sort_tups = sorted(counts.items(), key=lambda c: c[1])
        return OrderedDict(sort_tups)


class Activity():
    class Lists():
        def __init__(self):
            self.addeds = []
            self.removeds = []
            self.other = []

    def __init__(self, history, repo_name=None):
        self.repo_name = repo_name
        self.predicates = defaultdict(Activity.Lists)
        self._counts = [("",0,0)]
        for a in assertions.assertion_iter(history, inspects=False):
            pred = assertions.remove_whitespace(a.predicate)
            if a.change == assertions.Change.added:
                l = self.predicates[pred].addeds
            elif a.change == assertions.Change.removed:
                l = self.predicates[pred].removeds
            else:
                l = self.predicates[pred].other
            l.append(a)

    def counts(self):
        """Return [(pred_string, added_count, removed_count)] tuples"""
        if self._counts == [("",0,0)]:
            self._counts = [(pred, len(lists.addeds), len(lists.removeds)) for pred, lists in self.predicates.items()]
        return self._counts

    def sort_counts(self):
        """Sorts counts by most activity (higher number of adds and removes"""
        self._counts = sorted(self.counts(), reverse=True, key=lambda c: c[1] + c[2])

    def print_counts(self):
        for (pred, nadd, nrem) in self.counts():
            print("{p} :: added:{a} removed:{r}".format(p=pred, a=nadd, r=nrem))

    def graph(self, N=None):
        self.sort_counts()

        if N is None:
            N = len(self.counts())
            counts = self.counts()
        else:
            counts = self.counts()[:N]

        preds, nadds, nrems = zip(*counts)

        ind = np.arange(N)  # the x locations for the groups
        width = 0.35       # the width of the bars

        fig, ax = plt.subplots()
        rects1 = ax.bar(ind, nadds, width, color='r')
        rects2 = ax.bar(ind+width, nrems, width, color='y')

        title = 'Number of added and removed events per predicate'
        if self.repo_name:
            title = title + " in " + self.repo_name

        # add some text for labels, title and axes ticks
        ax.set_ylabel('Events')
        ax.set_title(title)
        ax.set_xticks(ind + width)
        ax.set_xticklabels(preds, rotation=45, ha='right')

        ax.legend((rects1[0], rects2[0]), ('Added', 'Removed'))

        def autolabel(rects):
            # attach some text labels
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                        '%d' % int(height),
                        ha='center', va='bottom')

        autolabel(rects1)
        autolabel(rects2)

        plt.tight_layout() # keeps all predicates visible
        plt.show()



DataPoint = namedtuple('DataPoint', ['x_val', 'y_added', 'y_removed', 'y_combined'])

class Result():
    def __init__(self, datapoints, desc, x_label, y_label, sort=None):
        """Prouce Result from list of DataPoints
        :sort:  if given sorting function, then sorts from Biggest to smallest
        """

        self.description = desc
        self.x_label = x_label
        self.y_label = y_label
        self.datapoints = datapoints if sort is None else \
                          sorted(datapoints, key=sort, reverse=True)


    def graph(self, length=None, cutoff=None, filt=None):
        """Produce graph of results. Applies given filters, if available.
        :length:    (int) max number DataPoints to plot
        :cutoff:    (DataPoint) plot no datapoints that are less than this one
        :filt:      (pred func) filter out DataPoints that produce False
        """

        dps = self.datapoints if length is None else self.datapoints[:length]
        length = len(dps)

        x_vals, y_addeds, y_removeds, y_combineds = zip(*dps)

        xs = np.arange(length)    # the x locations for the groups
        width = 0.27              # the width of the bars

        fig, ax = plt.subplots()
        rects_adds = ax.bar(xs, y_addeds, width, color='r')
        rects_rems = ax.bar(xs+width, y_removeds, width, color='y')
        rects_coms = ax.bar(xs+(2*width), y_combineds, width, color='g')

        # add the text for labels, title and axes ticks
        ax.set_ylabel(self.y_label)
        ax.set_title(self.description)
        ax.set_xticks(xs + (3*width/2.))
        ax.set_xticklabels(x_vals, rotation=45, ha='right')

        ax.legend((rects_adds[0], rects_rems[0], rects_coms[0]),
            ('Added', 'Removed', 'Combined'))

        def autolabel(rects):
            # attach some text labels
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                        '%d' % int(height),
                        ha='center', va='bottom')

        autolabel(rects_adds)
        autolabel(rects_rems)
        autolabel(rects_coms)

        plt.tight_layout() # keeps all predicates visible
        return plt # display with .show(); save with .savefig('path.png')


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
    return Counter(diffs[i+1].commit_index - diffs[i].commit_index
            for i,_ in enumerate(diffs[1:]))

def dist_result(history):
    dadd = dist_btw_assert_commits(history, assertions.Change.added)
    drem = dist_btw_assert_commits(history, assertions.Change.removed)
    dcom = dist_btw_assert_commits(history)
    counts = set(itertools.chain(dadd.elements(), drem.elements(), dcom.elements()))
    dps = [DataPoint(c, dadd[c], drem[c], dcom[c]) for c in counts]
    return Result(dps,
                  "Number of commits between commits containing assertions",
                  "Distances",
                  "Counts",
                  lambda dp: dp.y_added + dp.y_removed + dp.y_combined)


























def load_history(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)






# functions for producing analyses of History data
import pickle
from collections import defaultdict, OrderedDict

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

    def __init__(self, history):
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
        """Return (pred_string, added_count, removed_count) tuples"""
        if self._counts == [("",0,0)]:
            self._counts = [(pred, len(lists.addeds), len(lists.removeds)) for pred, lists in self.predicates.items()]
        return self._counts

    def sort_counts(self):
        """Sorts counts by most activity (higher number of adds and removes"""
        self._counts = sorted(self.counts(), key=lambda c: c[1] + c[2])

    def print_counts(self):
        for (pred, nadd, nrem) in self.counts():
            print("{p} :: added:{a} removed:{r}".format(p=pred, a=nadd, r=nrem))



















def load_history(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)






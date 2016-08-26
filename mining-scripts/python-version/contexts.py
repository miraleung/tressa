from collections import namedtuple
from itertools import groupby
from assertions import Change
from io import StringIO

class Contexts():
    Context = namedtuple("Context", ["name", "predicate", "file", "max_add", "max_rem"])

    def __init__(self, history):
        """Produce most recent context for assert predicates, ordered by most common.
        """
        self.contexts = []

        asserts = sorted(history.assertions(), key=lambda a: (a.name, a.predicate))
        np_asserts = list((np, list(la)) for np, la in groupby(asserts, key=lambda a: (a.name, a.predicate)))
        np_asserts.sort(key=lambda np_la: -len(np_la[1]))
        for (name, pred), asserts in np_asserts:
            by_file = _get_file_asserts(asserts)
            for file, add, rem in by_file:
                self.contexts.append(Contexts.Context(name, pred, file, add, rem))

    def __repr__(self):
        return "Contexts" + repr(self.contexts)

    def __str__(self):
        return self._format()


    def _format(self, n=None):
        cs = self.contexts if n is None else self.contexts[:n]
        with StringIO("Contexts[\n") as s:
            for c in cs:
                s.write("{n}({p}) | {f} | add_id: {a} | rem_id: {r}\n".format(
                    n=c.name, p=c.predicate, f=c.file, a=c.max_add, r=c.max_rem))
            return s.getvalue()

    def show(self, n=None):
        print(self._format(n))





def _get_file_asserts(assertions):
    """Given list of assertions, return
    (filename, added_commit_id, removed_commit_id) for given
    assertions, for each unique filename.
    """
    assertions.sort(key=lambda a: a.parent_file.name)
    files = groupby(assertions, key=lambda a: a.parent_file.name)

    file_asserts = []
    for name, asserts in files:
        add, rem = _max_add_rem_ids(list(asserts))
        file_asserts.append((name, add, rem))
    return file_asserts



def _max_add_rem_ids(asserts):
    """:asserts:    ([Assertions])
    Produce the id of the commit that contains the most assertion adds, and
    the commit that has the most removes, of the given assertions.
    """
    asserts = sorted(asserts, key=lambda a: a.parent_file.parent_diff.rvn_id)
    add_asserts, rem_asserts = _add_rem_separate(asserts)

    cid_alists_add = list(groupby(add_asserts, key=lambda a: a.parent_file.parent_diff.rvn_id))
    cid_alists_rem = list(groupby(rem_asserts, key=lambda a: a.parent_file.parent_diff.rvn_id))

    add_max = max(cid_alists_add, key=lambda ca: _len_iter(ca[1]), default=[None])
    rem_max = max(cid_alists_rem, key=lambda ca: _len_iter(ca[1]), default=[None])

    return add_max[0], rem_max[0]

def _add_rem_separate(asserts):
    add_asserts, rem_asserts = [], []

    for a in asserts:
        if a.change == Change.added:
            add_asserts.append(a)
        else:
            rem_asserts.append(a)

    return add_asserts, rem_asserts


def _len_iter(it):
    return sum(1 for x in it)


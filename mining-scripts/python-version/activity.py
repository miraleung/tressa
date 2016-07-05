# Produces assertion activity information
# 'activity' (similar to 'churn') is the number of commits that touch each
#   assertion


from collections import Counter
from assertions import *
import cdf


class Activity():
    def __init__(self, history):
        self.counter = Counter((a.name, a.predicate) for a in
                assertion_iter(history))

    def __str__(self):
        string = ""
        for (name, pred), count in self.counter.items():
            string += "{c}\t{n}({p})\n".format(c=count, n=name, p=pred)
        return string

    def cdf(self):
        data = list(self.counter.values())
        cdf.show_cdf(data)

    def to_file(self, filename):
        with open(filename, 'w') as file:
            file.write(self.__str__())












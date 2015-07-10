#!/usr/bin/python

import sys

from bisect import bisect_left
from scipy.stats import norm
import matplotlib.pyplot as plt


class discrete_cdf:
    def __init__(self, data):
        self._data = data # must be sorted
        self._data_len = float(len(data))

    def __call__(self, point):
        return (len(self._data[:bisect_left(self._data, point)]) /
                self._data_len)

if len(sys.argv) == 0:
  print('Usage: python cdf.py file-with-the-numbers')
  sys.exit(0)

content0, data=list(), list()

with open(sys.argv[1]) as f:
  content0 = f.readlines()

for i in content0:
  data.append(int(i))
print('{0}'.format(data))

cdf = discrete_cdf(data)
xvalues = range(0, max(data))
yvalues = [cdf(point) for point in xvalues]
plt.plot(xvalues, yvalues)
plt.show()

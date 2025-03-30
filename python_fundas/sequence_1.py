#https://www.geeksforgeeks.org/array-subarray-subsequence-and-subset/?ref=next_article
# A subsequence is a sequence that can be derived from another sequence by removing zero or more elements, without changing the order of the remaining elements.
#a subarray is continous allocation
# a sequence can be generated from itertools.combinations

import itertools
from array import *
import functools

#arr = array('i', [x for x in range(1, 5)])
#https://www.geeksforgeeks.org/number-of-subsequences-with-zero-sum/
arr = [-1, 2, -2, 1]
ll = []
for i in range(1, len(arr) + 1):
    ll_subseq = list(itertools.combinations(arr, i))
    # if len(ll_subseq) > 1:
    #     print(functools.reduce(lambda x, y: x + y, ll_subseq))

    ll.extend(ll_subseq)
print(ll)

counter=0
for subseq in ll:
    print(subseq, functools.reduce(lambda x, y: x + y, subseq))
            






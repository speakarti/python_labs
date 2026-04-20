import logging
logger = logging.getLogger(__name__)
from array import *
import itertools
import functools

# understand sets and subsets
# sets mutable, but unique sequence. 
# how to create all subsets from a set
# check if a set is an subset of another set.


def fn_get_allsubsets(arr):
    '''
    create all subsets of a given set / array.
    parameters: an array or a list
    returns: a list of subsets of all possible lenghts.
    logic: 1) convert into a set() to get unique items.
    2) call combinations function to get all compbinations of given length
    '''
    ll = []
    if len(arr) > 0:
        arr = set(arr) # convert into set to remove duplicate elements

        # get sets o all lengths
        for i in range(1, len(arr) + 1):
            ll.extend(itertools.combinations(arr, i))
    return ll

def fn_sum_of_flat_list(ll):
    '''
    to convery a list of tuples into a flat list.
    and add all ellements to get a sum.
    '''
    logger.info(ll)
    ll1 = fn_get_allsubsets(ll)
    logger.info(ll1)
    logger.info(functools.reduce(lambda x, y: x+y,  list([x for tuple in ll1 for x in tuple])))

def main():
    logging.basicConfig(filename='subset.log', filemode='w', level=logging.INFO)
    #arr = array('i', [1, -1, 1])
    #logger.info(fn_get_allsubsets(arr))

    #Sum of sum of all subsets of a set formed by first N natural numbers
    N = 10
    myset = set([x for x in range(1, N+1)])
    logger.info(fn_sum_of_flat_list(myset))

if __name__ == '__main__':
    main()

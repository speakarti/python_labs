# https://www.geeksforgeeks.org/python-flatten-list-to-individual-elements/
# a flaten a multi level list.
import logging
import functools
import itertools
logger = logging.getLogger(__name__)


def main():
    ll = [[1,3, "geeks"], [4,5], [6, "best"]]
    ll2 = [[1,3,"gfg"], [4,5], [6,"best"]]    
    logger.info(f" source list is {ll} \n {ll2}")

    # list comprehensions
    ll1 = [x for ll1 in ll for x in ll1]
    logger.info(f"Flatten list using list comprehension {ll1}")

    # operator overloading, list + list
    ll3 = ll1 + ll1
    logger.info(f"Flatten list using sum is: {ll3}")

    # using reduce
    logger.info(f"Flatten list using reduce: {functools.reduce(lambda x, y: x+y, ll)}")

    # using chain
    logger.info(f"Flatten list using chain: {list(itertools.chain(ll1))}")


if __name__ == '__main__':
    logging.basicConfig(filename='flatlist.log', filemode='w', level=logging.INFO)
    main()
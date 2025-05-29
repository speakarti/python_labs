import itertools
import math
import operator

# https://www.youtube.com/watch?v=1p7xa_BHYDs
# chain - treat 2 or more sequences as a single seq

'''

lazy ways

>>> print(dir(itertools))
['PS1', 'REPLHooks', '__annotations__', '__builtins__', '__doc__', '__loader__', 
'__name__', '__package__', '__spec__', 'accumulate', 'chain', 'combinations', 'combinations_with_replacement', 
'compress', 'count', 'cycle', 'dropwhile', 'filterfalse', 'get_last_command', 'groupby', 'islice', 
'original_ps1', 'pairwise', 'permutations', 'product', 'repeat', 'starmap', 'sys', 'takewhile', 'tee', 'zip_longest']


count and cycle are infirnte iterators
understand difference between reduce and accumulate functions
https://www.geeksforgeeks.org/reduce-in-python/
'''

def fn_iter_permutations_combinations():
    ll_numbers1 = [1, 2, 4 , 7, 9, 12]
    elements = ["A", 'B', 'C', 'D']
    print(list(itertools.permutations(range(3), 2)))
    print(list(itertools.permutations(elements)))
    print(list(itertools.combinations(elements,3)))
    print(list(itertools.combinations_with_replacement(elements,3)))

    print(list(itertools.repeat("elements",7)))
    print(list(itertools.repeat(elements,3)))

    for i in itertools.accumulate(ll_numbers1):
        print(i, end=' ')
    print([result for result in itertools.combinations(ll_numbers1, 3) if sum(result) == 10])
    print([result for result in itertools.permutations(ll_numbers1, 3) if sum(result) == 10])


def fn_iter_product():
    '''
    >>> help(itertools.product)
    Cartesian product of input iterables.  Equivalent to nested for-loops.
    product(A, repeat=4) means the same as product(A, A, A, A).
    product('ab', range(3)) --> ('a',0) ('a',1) ('a',2) ('b',0) ('b',1) ('b',2)
    product((0,1), (0,1), (0,1)) --> (0,0,0) (0,0,1) (0,1,0) (0,1,1) (1,0,0) ...
    '''
    ll_numbers1 = [1, 2, 4 , 7, 8, 9, 20]
    ll_numbers2 = [3, 6, 8 , 9]
    print(list(itertools.product(ll_numbers1, ll_numbers2)))
    print(list(itertools.product('A', range(4))))
    print(list(itertools.product('ab', range(3))))
    print(list(itertools.product((0,1), (0,1), (0,1))))



def fn_infinite_cycle():
    #create a cycle of given elements
    elements = ['A', 20, "Artti", 30, False, True]
    for i in itertools.cycle(elements):
        print(i)

def fn_infinite_cycle1():
    #create a cycle of given elements, get elements in circle again n agin
    elements = ['A', 20, "Artti", 30, False, True]
    mycycle = itertools.cycle(elements)
    print(next(mycycle))
    print(next(mycycle))
    print(next(mycycle))
    print(next(mycycle))
    print(next(mycycle))
    print(next(mycycle))
    print(next(mycycle))



def fn_infinite_loop():
    #for infinite counter, use iterator count. thsi works as generator
    for i in itertools.count(0, 5):
        print(i)

def fn_infinite_loop1():
    #for infinite counter, use iterator count. this works as generator
    #comparable with range, which can create limited list
    counter = itertools.count(0, 5)
    print(next(counter))
    print(next(counter))
    print(next(counter))
    print(next(counter))
    print(next(counter))


def learn_iter_chain():
    #https://www.geeksforgeeks.org/python-itertools-chain/?ref=next_article
    a = [1,3, 5, 8, 9]
    b = [ 9, 12, 56]
    c = {44, 77, 88, 44}
    print(list(itertools.chain(a, b, c)))

def learn_chain_from_iterable():
    li = ['123', '456', '789']   
    res = list(map(int, list(itertools.chain.from_iterable(li))))    
    sum_of_li = sum(res)    
    print("res =", res, end ="\n\n")
    print("sum =", sum_of_li)

    li = ['ABC', 'DEF', 'GHI', 'JKL']
    print(list(itertools.chain.from_iterable(li)))




def fn_iter_accumulate(seq):
    # function to apply a fuction for each iterm in an iter and result iterative results
    # similar to functoosl -> reduce, which proides one final results.
    # accumulate gives iterative results  
    # itertools.accumulate(iterable[, func]) –> accumulate object
    print(f"itertools.accumulate({seq}) -> {list(itertools.accumulate(seq))}") # default is sum
    print(f"itertools.accumulate({seq}, {operator.mul}) -> {list(itertools.accumulate(seq, operator.mul))}")
    print(f"itertools.accumulate({seq}, {operator.add}) -> {list(itertools.accumulate(seq, operator.add))}")    
    print(f"itertools.accumulate({seq}, max) -> {list(itertools.accumulate(seq, max))}")
    print(f"itertools.accumulate({seq}, max) -> {list(itertools.accumulate(seq, max))}")


def main():
    a = [1,3, 5, 4, 9, 16, 6, 3]
    b = [ 9, 12, 56]

    #fn_infinite_loop1()
    #fn_infinite_cycle()
    #fn_iter_accumulate(a)
    #fn_iter_permutations_combinations()
    #learn_iter_chain()
    learn_chain_from_iterable()


if __name__ == '__main__':
    main()
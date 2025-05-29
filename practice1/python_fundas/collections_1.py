# collecions: Counter, namedtuple, OrderedDict, Defaultdict, deque
import collections

'''
>>> print(dir(collections))
['ChainMap', 'Counter', 'OrderedDict', 'UserDict', 'UserList', 'UserString', '_Link', '_OrderedDictItemsView', 
'_OrderedDictKeysView', '_OrderedDictValuesView', '__all__', '__builtins__', '__cached__', '__doc__', '__file__', 
'__loader__', '__name__', '__package__', '__path__', '__spec__', '_chain', '_collections_abc', '_count_elements', 
'_eq', '_iskeyword', '_itemgetter', '_proxy', '_recursive_repr', '_repeat', '_starmap', '_sys', '_tuplegetter', 'abc',
'defaultdict', 'deque', 'namedtuple']
>>>


    This module implements specialized container datatypes providing
    alternatives to Python's general purpose built-in containers, dict,
    list, set, and tuple.

    * namedtuple   factory function for creating tuple subclasses with named fields
    * deque        list-like container with fast appends and pops on either end
    * ChainMap     dict-like class for creating a single view of multiple mappings
    * Counter      dict subclass for counting hashable objects
    * OrderedDict  dict subclass that remembers the order entries were added
    * defaultdict  dict subclass that calls a factory function to supply missing values
    * UserDict     wrapper around dictionary objects for easier dict subclassing
    * UserList     wrapper around list objects for easier list subclassing
    * UserString   wrapper around string objects for easier string subclassing

help(collections.Counter)
 Dict subclass for counting hashable items.  Sometimes called a bag
 |  or multiset.  Elements are stored as dictionary keys and their counts
 |  are stored as dictionary values.
'''

def fn_counter():
    mystr = "Dict subclass for counting hashable items.  Sometimes called a bag"
    mydict = {x: x**2 for x in range(10)}
    mylist = [x for x in range(20)]
    #mytouple = ((x, y) for x in range(20) for y in len('aeiou'))

    c_mystr = collections.Counter(mystr)
    c_mydict = collections.Counter(mydict)
    c_mylist = collections.Counter(mylist)
    #c_mytouple = collections.Counter(mytouple)

    print(c_mystr)
    print(c_mydict)
    print(c_mylist)
    #print(c_mytouple)



if __name__ == '__main__':
    fn_counter()
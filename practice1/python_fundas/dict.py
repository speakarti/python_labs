# lookup table, hashmap, key value pair with unique key,
# unordered table
# len(), loop with 'for', 'in' membership
# sorted(), reversed, 

from typing import List, Dict, Optional
from collections import defaultdict

def fill_dict_fromkeys(ll: List) -> Dict:    
    mydict = {}
    mydict.fromkeys(ll)
    return mydict
    
def show_dict_details(mydict: Dict):
    print(mydict, len(mydict), type(mydict), mydict.items(), mydict.keys(), mydict.values())
    print(sorted(mydict), min(mydict), mydict.items(), mydict.keys(), mydict.values())


def create_dict():
    # learn dictionary 
    # create an empty dictionary
    mydict1 = dict()
    mydict1 = {}

    # fill dictionary
    mydict2 = {'name':'Arti', 'age': 47, 'fname': 'vimal', 'id': 'jamm'}

    # set/update key value for existing key
    mydict2['abcId'] = 'tjt917' # insert and update a new key/value pair
    mydict2['age'] = 47.5 # update a key/value pair

    # set/update key value for existing key
    mydict2['DoB'] = None
    
    # get a key with default or None value
    if 'DoB' in mydict2.keys():
        print((mydict2['DoB']))

    
    show_dict_details(mydict2)

    #common values
    print(dir(mydict1))
    print(mydict2)
    print(mydict2.keys())
    print(mydict2.values())
    print(mydict2.items())

    my_list = [x for x in range(101)]
    my_values_list = [1, 5, 6]
    mydict3 = dict.fromkeys(my_list, my_values_list)
    print(mydict3)
    my_values_list.append(56)
    print(mydict3)

    mydict3.clear()
    my_list = [x for x in range(101)]
    my_values_list = [1, 5, 6]
    mydict3 = {key: list(my_values_list) for key in my_list}
    print(mydict3)
    my_values_list.append(56)
    print(mydict3)

    #pop will remove give key item, will return NOne if no given item to delete
    popped = mydict3.pop(99)
    print(popped)
    print(mydict3)

    # popitem( will remove last item, will return error if no item toremove
    popped = mydict3.popitem()
    print(popped) 
    print(mydict3)

    # for k, v in enumerate(mydict2.keys):
    #     print(k, v)


def main():    
    #ll = ['name', 'age', 'abcid']
    #print(fill_dict_fromkeys(ll))
    create_dict()

if __name__ == '__main__':
    main()
# flatten a list https://www.geeksforgeeks.org/python-flatten-list-to-individual-elements/

llist  = [(1, 2), (4, 5), (8, 9), (8, 11), (8, 3)]

llist_copy = llist.copy()
llist.sort(reverse = True)
print(llist)

def secondval(x):
    return x[1]
llist_copy.sort(key=secondval)
print(llist_copy)
try:
    mylist = ['apple', 'banana', 'cherry']
    my_frozenset = frozenset(mylist)
    my_set = set(mylist)
    print("frozen set is: ", my_frozenset)
    print("frozen set is: ", my_set)

    print(dir(my_set))
    for item in my_set:
        print(item)

    # initialize A and B
    A = frozenset([1, 2, 3, 4])
    B = frozenset([3, 4, 5, 6])

    # copying a frozenset
    C = A.copy()
    print("A.copy() :", C)  
    C = set(C)
    print("C :", C)  

    print("B :", B)  

    # union
    union_set = A.union(B)
    print("A.union(B) :", union_set) 

    union_set1 = A | B
    print("A.union(B) A | B :", union_set1) 


    # intersection
    intersection_set = A.intersection(B)
    print("A.intersection(B) :", intersection_set)  
    intersection_set1 = A & B
    print("A.intersection(B) A & B:", intersection_set1)  

    difference_set = A.difference(B)
    print("A.difference(B) :", difference_set) 

    difference_set1 = A - B
    print("A.difference(B) A - B :", difference_set1) 


    # symmetric_difference
    symmetric_difference_set = A.symmetric_difference(B)
    print("A.symmetric_difference(B) :", symmetric_difference_set)  
    symmetric_difference_set1 = A ^ B
    print("A.symmetric_difference(B) A ^ B :", symmetric_difference_set1)  
    symmetric_difference_set1 = (A | B) - (A & B)
    print("A.symmetric_difference(B) (A | B) - (A & B) :", symmetric_difference_set1)  

    C.add(99)
    C.update(B)
    print("C :", C)  
    if B.issubset(C):
        print("B is subsetof C")
    elif C.issubset(B):
        print("C is subsetof B")
    else:
        print("no relation")
    
    print("B.isdisjoint(C) so intersection is : B & C", B & C)
    print(B.isdisjoint(C))

    for n in range(len(C)):
        print("C.pop", C.pop())

    C = A | B
    for x in C:
        print(x)

    item = 2
    if item in C:
        print(item)
        #n = C.remove(item)
        


except:
    print("exception occured")

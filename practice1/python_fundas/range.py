#!/bin/python3

#https://www.w3schools.com/python/python_ref_string.asp
try:
    
    # Practice on while with else
    i = 1
    while i < 6:
        print(i, end=" ")
        i += 1
    else:
        print("i is no longer less than 6 \n")

    # Practice on range, print with non-newline character
    for i in range(0, 10, 2):
        print(i, end=" ")    
    print("\n" + "----" * 20 ) 
    print("\n", "----$" * 20, "hello" ) 

    for x in range(50, 5, -5):
        print(x, end="##    ")
    print("\n" + "----" * 20 ) 

    # access elements in range by index
    ele = range(200)[0]
    print("First element:", ele)

    ele = range(200)[-1]
    print("\nLast element:", ele)

    ele = range(200)[4]
    print("\nFifth element:", ele)
    print("\n" + "----" * 20 ) 

    # chain multiple ranges
    from itertools import chain

    mychain = chain(range(10), range(200, 100, -5))
    print(type(mychain))
    for x in mychain:
        print(x, end="##    ")

    #range to list
    mylist = list(range(1000, 10, -5))
    print(mylist)

    #reverse a string
    myname = "My name is Arti"
    for i in reversed(range(len(myname))):
        print(myname[i], end=" ")



    A = {1, 5, 7, 9, 10}
    B = {1, 5, 7, 9, 10, 12, 15, 17}
    C = {12, 50, 8, 60, 40}
    
    print("\n\nA before clear(): " + str(A))
    A.clear()
    [print("Lenght of A is: " + str(len(A)) + " and type of A is: " + str(type(A)) + " value of A is: " + str(A)) if A is not None else print("A is None")]

    print("\n\nA before union(): " + str(A))        
    D = A.union(B) # union returns a new set
    [print("Lenght of D is: " + str(len(D)) + " and type of D is: " + str(type(D))) if D is not None else print("D is None")]
    [print("Lenght of A is: " + str(len(A)) + " and type of A is: " + str(type(A)) + " value of A is: " + str(A)) if A is not None else print("A is None")]

    print("\n\nA before update(): " + str(A))
    E = A.update(B) # update will update A union B, and returns none
    [print("Lenght of A is: " + str(len(A)) + " and type of A is: " + str(type(A))) if A is not None else print("A is None")]
    [print("Lenght of A is: " + str(len(A)) + " and type of A is: " + str(type(A)) + " value of A is: " + str(A)) if A is not None else print("A is None")]

    
    print("\n\nA before add(): " + str(A))
    F = A.add(30)
    [print("Lenght of A is: " + str(len(A)) + " and type of A is: " + str(type(A)) + " value of A is: " + str(A)) if A is not None else print("A is None")]
    [print("Lenght of F is: " + str(len(F)) + " and type of F is: " + str(type(F))) if E is not None else print("F is None")]

    print("\n\nA before copy(): " + str(A))
    G = A.copy()
    [print("Lenght of A is: " + str(len(A)) + " and type of A is: " + str(type(A)) + " value of A is: " + str(A)) if A is not None else print("A is None")]
    [print("Lenght of G is: " + str(len(G)) + " and type of G is: " + str(type(G))) if G is not None else print("G is None")]

    nret = A.difference(B)
    [print(nret) if nret is not None else print('nret is none from difference')]

    # print()
    # A.difference_update(B)
    # A.discard()
    # A.intersection()
    # A.intersection_update()
    # A.isdisjoint
    # issubset
    # issuperset
    # pop
    # remove
    # symmetric_difference
    # symmetric_difference_update
    # union
    # update
except:
    print("Exception Occured")
else:
    print("No Exception")
finally:
    print("terminating")
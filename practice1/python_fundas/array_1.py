from array import *
import itertools
import logging
logger = logging.getLogger(__name__)



''' https://www.hackerrank.com/challenges/python-sort-sort/problem?isFullScreen=true '''
# python implements genrally list as arrays
# list can store data of multiple data types and have dynamic sizes as compared to conventional array.
# python has an array module
# count and index to find occrance,

# as arrays are of fixed size, can't be changed so inserting and deleting logic requires creatign a new array and 
# manually shifting items as required.
# Good Reding
# https://www.geeksforgeeks.org/introduction-to-arrays-data-structure-and-algorithm-tutorials/?ref=next_article


def arr_learnpy_array():
    '''
    typecodes are 
    'b' -> char
    'c' -> char    
    'i' -> Signed Int
    'I' -> Unsigned Int
    'f' -> float
    'd' -> double 
    '''
    # list to array of type int 
    arr = array.array('i', [13, 32, 13, 54, 25, 32])
    print(arr, arr.buffer_info)

    # traverse array
    for i in range(len(arr)):
        print(i, arr[i])

    # crud operations, reverse, find
    arr.append(20)
    arr.remove(32) # removes first occurance
    arr.reverse()
    
    print(arr, arr.count(32), arr.index(32), arr[1])

def sortPyArray():        
    try:
        sz_name = "Arti Aggrwal"
        ll_name = list(sz_name)
        print(ll_name, type(ll_name))
        ll_name.pop(ll_name.index(' '))
        print(ll_name)
        arr_sz_name = array('b', ['A', 'r', 't', 'i', 'A', 'g', 'g', 'r', 'w', 'a', 'l'])
        print(type(arr_sz_name), arr_sz_name, arr_sz_name.size)
    except TypeError as e:
        print(f"TypeError: Exception occured: {e}")
    except ValueError as e:
        print("ValueError", e)
    except RuntimeError as e:        
        print("Run", e)
    except (NameError, IndexError, KeyError, ZeroDivisionError):
        pass
    except Exception as e:
        print(f"Exception occured: {e}")


def feedArray():
    # input n and m 
    # then input n numbers of elements tomake a list
    # input k
    # print all
    n, m = input().strip().split()
    print(n, m)
    ll = []
    for i in range(int(n)):
        ll.append(input().strip().split())

    k = int((input()).strip())
    print(n, m, k, ll)
    #5 3 2 [['4', '5', '6'], ['8', '7', '6'], ['8', '5', '3'], ['5', '7', '3'], ['9', '4', '23']]

def assignTuples():
    n, m, k, ll = 5, 3, 2, [['4', '5', '6'], ['8', '7', '6'], ['8', '5', '3'], ['5', '7', '3'], ['9', '4', '23']]
    print(n, m, k, ll)

def mul_elementsof_an_array(arr):
    product = 1
    if len(arr) > 0:
        for i in range(len(arr)):
            product *= arr[i]
    return product

def fn_get_all_subarrays(arr, k=None):
    #given an array, get all subarrays
    # if k is mentioned then return substrings only of given lenght k
    arr_size = len(arr)
    print("arr: ", arr, arr_size)
    
    for i in range(arr_size + 1):
        for j in range(i + 1, arr_size + 1):
            # #print array i to j  
            size_subarray = len(arr[i:j])
            #print(i, j, size_subarray)
            if k is not None and size_subarray == 4:
                print(f"Subarray: {arr[i:j]} and length: {len(arr[i:j])}")
                nresults  = mul_elementsof_an_array(arr[i:j])
                print(nresults)
   
def fn_reverse_an_array(arr):
    # given an array, reverse this array
    # divide array in two parts, swap first with last, and keep on increasing index of being and decreasing for last.
    arr_size = len(arr)
    print("arr: ", arr, arr_size)
    first_index = 0
    last_index = arr_size-1

    for i in range(arr_size//2):
        arr[first_index], arr[last_index]  = arr[last_index], arr[first_index]
        first_index += 1
        last_index -= 1
    
    print("Reversed arr: ", arr, arr_size)

        
def main():
    logging.basicConfig(filename = "arry_1.log", filemode='w', level=logging.INFO)
    #sortArray1()
    #my_py_array()
    #sortPyArray()
    ll = [x * 10 for x in range(9)]
    arr = array('i', ll)

    #fn_get_all_subarrays(arr, 4)
    #fn_reverse_an_array(arr)

    # min and max of an array
    # sort and then first and last
    #arr1 = sorted(arr)
    #logger.info(f"min and max of an sorted array: min = {arr1[0]} and max {arr1[-1]}")
    
    # min and max of an array    
    #logger.info(f"min and max of an unsorted array using max and max fucntions: min = {min(arr)} and max {max(arr)}")

    # Last duplicate element in a sorted array
    arr = array('i', [1, 5, 5, 6, 6, 7])
    #ll = list (arr)
    #print(ll)
    mydict = {}
    mydict1 =mydict.fromkeys(arr)
    print(mydict1)
    for key in mydict1.keys():
        mydict1[key] = [i for (i, x) in enumerate(arr) if x == key]
    print(mydict1)


if __name__ == '__main__':
    main()
    


    
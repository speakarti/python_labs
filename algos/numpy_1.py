import numpy as np
#https://www.youtube.com/watch?v=4c_mwnYdbhQ&t=139s

# shape, dimension, size, dtype
# written in c, so fast and optimised
# 

def arr_details(arr):
    print(type(arr))
    print(arr, arr[1:], arr[:3])
    print(arr.shape, arr.ndim, arr.size, arr.dtype)

def test():
    arr = np.array([[11, 23, 56, 77], [11, 23, 56, 77], [11, 23, 56, 77]])

    arr_details(arr)

    #arr_mul_type = np.array([22, {21, 53, 84}, (43, 87, 65, 74, 9898), 'Arti', {'state':'Tx', 'city':'San Antonio', 'Zip':78660}])
    arr_mul_type = np.array([22, 'Arti', 22, 'Arti', 22, 'Arti'])
    arr_details(arr_mul_type)
    print(arr_mul_type[3])

def arr_filled():
    #full, zeron, empty ones to create arrays with given shape
    pass

def arr_seq():
    arr = np.arange(0, 1000, 5)
    arr = np.linspace(0, 1000, 4)
    arr = np.nan # checkj usage
    arr = np.inf # checkj infinity
    print(np.isnan(np.sqrt(-1)))
    print(np.array([10] / 0))


def np_math():
    l1 = [x for x in range(10)]
    l2 = [x for x in range(10)]

    a1 = np.array(l1)
    a2 = np.array(l2)

    print(l1 + 2)
    print(l1 + l2)
    print(a1 + l2)
    print(a1 + a2) 
    print(a1 - a2)
    print(a1 / a2)


    #print(np.sqrt(a)), sin, tan, log10(n) etc.

    # array functions

    np.append(a, [3, 6, 8, 8]) # no implace
    np.inplace(a, [3, 6, 8, 8]) # no implace
    np.delete(a, 1) # delete an index

    #shape vs reshape vs resize (inplace), flattern, ravel

    # transpose, T, swapaxes


# merge arrays - concatenate with axis
# stack (vstack and hstack)
# split, axis

# agrregarte fucnt _ min, max,mean, std, sum, median

#randon -,. randonint, of os shape of binomial ( probability of .5 in range , normal distribution)
#randon choice

export / import
np.save(), savetxt, 
np.load, loadtxt

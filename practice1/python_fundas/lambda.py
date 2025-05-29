from itertools import *
from functools import reduce
#https://www.sitepoint.com/python-lambda-functions/

#basic lambda to sum two 
# one liner function with no def and return keyword
# can cntain only one single expression
# expression means a combination of variables, constants, calculations which evakluates and retuns
fn_lamb_sum = lambda x, y : x + y
print(fn_lamb_sum(4,5))

#pi r quare
fn_lamb_pi_r_sq = lambda r, pi=3.14 : pi * r * r
print("fn_lamb_pi_r_sq : " + str(fn_lamb_pi_r_sq(4)))

#greet a list of names using lambda and map
l_names = [str(i) + "name" for i in range(10) if i % 2]
print(l_names)

lab_sayhello = lambda str_name : "hello " + str_name
print(lab_sayhello("arti"))

str_return = list(map(lab_sayhello, l_names))
print(str_return, type(str_return))

#sum digits of a list of squares of odd numbers using lambda and map
ll_numbers = [x**2 for x in range(100) if x % 2 != 0]
print(ll_numbers)

def digit_sum(x):
    sum = 0
    for i in range(len(str(x))):
        digit = str(x)[i]
        sum = sum + int(digit)
    return sum

map_ret = list(map(digit_sum, ll_numbers))
print(map_ret)

# print numbers ending with 9
def is_number_end_with_9(x):
    if len(str(x)) >= 1 and str(x)[-1] =='9':
        return True
filet_ret = list(filter(is_number_end_with_9, ll_numbers))
print(filet_ret)

reduce_ret = reduce(lambda a, b : a + b, ll_numbers)
print(reduce_ret)
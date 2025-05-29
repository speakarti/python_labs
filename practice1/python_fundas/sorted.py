# sorted fucntion always returns a list
# set is an unordered list, and sorted retun a list, but if we tycast, it will again become unsorted
# >>> print(help(sorted))

# sorted(iterable, /, *, key=None, reverse=False)
#     Return a new list containing all items from the iterable in ascending order.

#     A custom key function can be supplied to customize the sort order, and the
#     reverse flag can be set to request the result in descending order.


ll_i = [5757, 99, 75, 53]
ll_s = ['arti', 'arnav', 'navin', 'rtrtrt']

tt_i = (5757, 99, 75, 53)
tt_s = ('arti', 'arnav', 'navin', 'rtrtrt')

ss_i = {5757, 99, 75, 53, 99}
ss_s = {'arti', 'arnav', 'navin', 'rtrtrt'}


print(sorted(ll_i))
print(sorted(ll_s))

print(sorted(tt_i))
print(sorted(tt_s))

print(sorted(ss_i))
print(sorted(ss_s))


'''
sorted() will treat a str like a list and iterate through each element. 
In a str, each element means each character in the str. sorted() will not treat a sentence differently, 
and it will sort each character, including spaces.
'''

string_number_value = '34521'
string_value = 'I like to sort'
sorted_string_number = sorted(string_number_value)
sorted_string = sorted(string_value)
print(sorted_string_number)
print(sorted_string)

#.split() can change this behavior and .join(). split will make it a list of strings, and join will join.
string_value = 'I like to sort'
sorted_string = sorted(string_value.split())
print(sorted_string)
print(' '.join(sorted_string))


#sorted() With a key Argument
# This argument expects a function to be passed to it, and that function will be used on each value in the list being sorted to determine the resulting order.
words = ['banana', 'pie', 'Washington', 'book']
print(sorted(words))
print(sorted(words, key=len))
print(sorted(words, key=str.lower))

def sort_key_fn(x):
    return ord(str(x[0]))
print(sorted(words, key=sort_key_fn))

def reverse_word(x):
    return x[::-1]
print(sorted(words, key=reverse_word))
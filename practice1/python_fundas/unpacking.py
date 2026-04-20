# packing / unpacking *args tuple, **kwargs dict


# *args

def unpack_it(x, y, z):
    print(x, y, z)


def pack_it(*args):
    print("args: " + str(args), "type(args): " + str(type(args)))


def print_names(*args, **kwargs):
    print(args, kwargs) # first is a tuple 2ns is dictionary

print_names('arti', 33, 87, True, Name='Arti', age=54, id='ytu8848')


mytuple = ('arti', 'arnav', 'navin')
unpack_it(*mytuple)

pack_it(5, 78, 98) # py packs these in a tuple





# multiple assignments in a single statemet
a, b, c  =  1, 2, 3  # python creates a tuple
print("a: {}, b: {}, c: {}".format(a, b, c))
print('a: {z}, c: {t}, b: {v}'.format(z=a, t=c, v=b))

# one line swap statement
a, b, c = b, c, a
print("a: {}, b: {}, c: {}".format(a, b, c))

a, b, c = '56 78 98'.split()
print("a: {}, b: {}, c: {}".format(a, b, c))

ll = [56, 78, 98]
a, b, c = ll
print("a: {}, b: {}, c: {}".format(a, b, c))

tup = (56, 78, 98)
a, b, c = tup
print("a: {}, b: {}, c: {}".format(a, b, c))
# code to manipulate strings in python


def fn_string_methods():
    ''''
    dir(mystr)
    ['__add__', '__class__', '__contains__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', 
    '__getattribute__', '__getitem__', '__getnewargs__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', 
    '__iter__', '__le__', '__len__', '__lt__', '__mod__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', 
    '__repr__', '__rmod__', '__rmul__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'capitalize', 
    'casefold', 'center', 'count', 'encode', 'endswith', 'expandtabs', 'find', 'format', 'format_map', 'index', 'isalnum', 
    'isalpha', 'isascii', 'isdecimal', 'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 'isspace', 'istitle', 
    'isupper', 'join', 'ljust', 'lower', 'lstrip', 'maketrans', 'partition', 'removeprefix', 'removesuffix', 'replace', 'rfind', 
    'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines', 'startswith', 'strip', 'swapcase', 'title', 'translate', 
    'upper', 'zfill']
    '''
    mystr: str = 'Hello'
    mystr1: str = 'HELLo'

    
    print(f'capitalize(): {mystr.capitalize()}')
    
    #caseless comparison of two strings, ignorign the case like Hello vs HELLo
    print(f'casefold(): {mystr.casefold()}')
    print(mystr.casefold() == mystr1.casefold())

    str1 = mystr.center(20, '~')
    print(f'center(): {str1}')

    print("count(): " + str(mystr.count('l')))

    retends = mystr.endswith('o')
    print("endswith(): o: " + str(retends))
    retends = mystr.endswith(('o', 'a')) # search string can be a single string or a tuple of strings, then it will check with logical 'or'
    print("endswith(): o or a : " + str(retends))

    retends = mystr.endswith(('p', 'a')) # search string can be a single string or a tuple of strings, then it will check with logical 'or'
    print("endswith(): p or a: " + str(retends))


    mystr: str = f'Hello\tArti\tHow\tare\tyou'
    retends = mystr.expandtabs(20)
    print("expandtabs(): 10 : " + str(retends))

    findstr = 'lo'
    ret = mystr.find(findstr) # find the lowest index, else -1 if not found
    print("mystr.find(findstr) : " + str(ret))
    print("print string post found string is mystr.find(findstr) : " + mystr[ret:])

    
    # string formatting
    greetings: str = f'Hello\t\tArti\tHow\tare\tyou'
    raw_string = r'hello\tarti\nwhat_is raw \s\s string \s\s'
    str_name: str = "Arti Aggarwal"
    int_age: int = 46 #expr(today() - 1977)
    print('Format String1 -  mystr:{}, age:{}'.format(mystr, int_age))
    print('Format String2 - mystr:{1}, age:{0}'.format(mystr, int_age))
    print('Format String3 - greetings:{greetings}, name:{name} age:{int_age}')
    print('Format String4 - greetings:{greetings}, name:{name} age:{nage}'.format(greetings=greetings, nage = int_age, name=str_name))
    print(f'f-string greetings:{greetings}, name:{str_name} age:{int_age} raw_string: {raw_string}')
    

    coordinates: dict = {'x': 10, 'y': 20}
    text: str = "coordinates: ({x}, {y})"
    print("**coordinates " + str(coordinates) )    
    print("text.format(coordinates) : " + text.format(**coordinates))
    print("text.format_map(coordinates) : " + text.format_map(coordinates))



    # print in reverse
    print(mystr[::-1])
    print(mystr[-1::-1])

    mystr = 'javaPoint'
    print(mystr[::-1])

    #delete a string
    del mystr
    try:
        print(mystr[::-1])
    except:
        print('exception occured')


if __name__ == '__main__':
    fn_string_methods() 

#Using inspect to get functions in a module

# Importing getmembers and isfunction from inspect
from inspect import getmembers, isfunction

# Importing math module
import math as mt

# Printing all the functions in math module
print(getmembers(mt), isfunction)

#functions in current local scope 
#__dir__(),  __getattr__()
print(dir(mt))


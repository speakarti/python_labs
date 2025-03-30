from collections import defaultdict

# in dict if key deosn's exists, then it will trow keyerror
# but defaultdict will not throw, rather it will create key with default value

data  =  defaultdict(str)

print(type(data))
print(type(data['name']))
print(issubclass(defaultdict, dict))



list_student_data = defaultdict(list)
list_student_data['name'].append('arti')
list_student_data['name'].append('arnav')
list_student_data['name'].append('navin')

print(list_student_data)

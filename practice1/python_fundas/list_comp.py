itemlist = ["item" + str(i) for i in range(10) if i % 2]
print(itemlist)
itemNewlist = [i.replace('item', 'newteem') for i in itemlist]
print(itemNewlist)
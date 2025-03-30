# sort my first name and last name 
# Arti Aggarwal
def sortname1():
    sz_name = (input("Enter you name: ")).strip()
    print(sz_name)
    ll = sz_name.split()
    print(sorted(ll))


def sortname2():
    sz_name = (input("Enter you name: ")).strip()
    print(sz_name)
    print(sorted(sz_name))

def sortname():
    sz_name = (input("Enter you name: ")).strip()
    print(sz_name)
    for i in range(len(sz_name)):
        print(ord(sz_name[i]), end=" ")

def bubblesort():
    sz_name = "Arti Aggarwal"
    ll_words = sz_name.split() # this will split based on delimiter, space by default
    ll_chars = list(sz_name)    
    #ll = [x.strip() for x in sz_name]
    print(ll_chars)
    nlist_size = len(ll_chars)
    for i in range(nlist_size-1):
        for j in range(nlist_size-i-1):
            #print(ll[i], ll[j])
            if ll_chars[j] > ll_chars[j+1]:
                ll_chars[j], ll_chars[j+1] = ll_chars[j+1], ll_chars[j]
    print(ll_chars)
if __name__ == '__main__':
    bubblesort()
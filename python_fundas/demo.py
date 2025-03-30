# test all and any
def fun1():
    '''function  to take input and print True 
    if N is Palindrome
    and if all numbers are positive integers
    '''
    N = int((input()).strip())
    ll  = []
    for i in range(N):
        n = int((input()).strip())
        ll.append(n)
    print(ll)

    print("all : ", all(ll))
    print("any : ", any(ll))


def fun2():
    N = int((input()).strip())
    ll  = [int((input()).strip()) for i in range(N)]
    print(all(ll))

def fun3():
    N = int((input()).strip())    
    ll2 = list(map(lambda x: x > 0, list(map(int, ((input()).strip()).split()))))
    print(ll2)
    print(all(ll2))


def isPalindrome():
    N = (input()).strip()
    revN = int(''.join(list(reversed(N))))
    print(revN)
    return int(N) == int(revN)
    

if __name__ =='__main__':
    print(isPalindrome())
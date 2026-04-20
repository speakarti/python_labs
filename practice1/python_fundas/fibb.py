
# fib serer using list
def fib(n):
  ll = [0, 1]
  for i in range(2, n):
    new_num  = ll[-1] + ll[-2]
    ll.append(new_num)

  return ll


def fib2(n):
  i=2
  ll = [0, 1]
  while i < n:
    new_num  = ll[-1] + ll[-2]
    ll.append(new_num)
    i += 1
  return ll


# fib serer using variables
def fib1(n):
  a, b = 0, 1
  yield 0
  yield 1
  for i in range(2, n):
    yield a+b
    a, b = b, a + b


class Solution:
    def fib(self, n: int) -> int:
        print(n)
        if n >=0 and n <= 30:
            if n <= 1:
                ret = n
            else:
                ret = Solution.fib(n-2) + Solution.fib(n-1)
            return ret
        else:
            return 0
        


#print(fib(8))
#print(fib2(8))
n = 2
myobj = Solution()
print(myobj.fib(n))
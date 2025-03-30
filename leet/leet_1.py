import itertools
from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        for mytuple in itertools.combinations(nums, 2):
            if mytuple[0] + mytuple[1] == target:
                ll = []
                if mytuple[0] != mytuple[1]:                    
                    ll.append(nums.index(mytuple[0]))
                    ll.append(nums.index(mytuple[1]))
                else: # ifboth indexes are same
                    ll = [index for index, value in enumerate(nums) if nums[index] == mytuple[0] ]
                break
        return ll

    def isPowerOfThree(self, n: int) -> bool:
        '''
        326 : https://leetcode.com/problems/power-of-three/
        '''
        if n >= -2**31 and n <= 2**31 -1:
            if n <= 0: 
                return False
            else:
                x= 2
                prime = []
                while x <= n:
                    if n % x == 0:
                        prime.append(x)
                        n //= x
                    else:
                        x += 1
            my_set = {3,}
            return set(prime) == my_set

    def isPowerOfTwo(self, n: int) -> bool:
        '''
        231 - https://leetcode.com/problems/power-of-two/
        '''
        while n > 1 and n % 2 == 0:            
                n /= 2            
        return n == 1 


    def isPowerOfFour(self, n: int) -> bool:
        '''
        342. Power of Four
        '''
        while n > 1 and n % 4 == 0:
            n /= 4
        return n == 1


    class Solution:
        '''
        509 - Fibonacci
        '''
        def fib(self, n: int) -> int:
            if n == 0:
                nret = 0
            elif n == 1:
                nret = 1
            else:
                nret = Solution().fib(n-2) + Solution().fib(n-1)
            
            return(nret)
        

def main():
    myobj =  Solution()
    # nums = [2,7,11,15]
    # target = 9
    # print(myobj.twoSum(nums, target)   )
    myobj.isPowerOfThree(45)

if __name__ == '__main__':
    main()

        
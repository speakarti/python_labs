'''
https://leetcode.com/problems/group-anagrams/description/
leet code problem to to write anagrams together in a list

Input: strs = ["eat","tea","tan","ate","nat","bat"]
Output: [["bat"],["nat","tan"],["ate","eat","tea"]]
'''

class Leetcode_class:
    def return_anagrams(self, ll_mylist):
        ll_return = []
        my_dict = {}
        for item in ll_mylist:
            ll_new_key = tuple(sorted(item))
            print(ll_new_key)
            if ll_new_key in my_dict.keys():
                # add as value in existing list
                ll = my_dict[ll_new_key]
                ll.append(item)
                my_dict[ll_new_key] =  ll
            else:
                # create a new key value pair
                my_dict[ll_new_key] = [item]
          
            
        return list(my_dict.values())



    try:
        pass

    except:
        pass

    finally:
        pass

def main():
    ll_strs = ["eat","tea","tan","ate","nat","bat"]
    leet = Leetcode_class()
    print(leet.return_anagrams(ll_strs))


if __name__ == '__main__':
    main()

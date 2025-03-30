# implement binary search algo.

# iterative vs recursive

def fn_binary_search(sequence, item):
    # fucntion to serach index and return -1 if not found
    iseq_size = len(sequence)
    if iseq_size > 1:
        sequence1 = sorted(sequence)
        lo = 0
        hi = iseq_size -1
        while lo <= hi :
            mid = (lo + hi) // 2
            mid_value = sequence1[mid]
            if item == mid_value:
                return mid
                break
            elif item < mid_value:
                hi = mid - 1
            else:
                lo = mid + 1
    else:
        return -1
    
def main():
    ll = [4, 7, 8, 9, 3, 5, 6, 4, 7, 5, 8, 9, 90]
    ll1 = sorted(ll)
    print(ll1)
    print(fn_binary_search(ll1, 9))

if __name__ == '__main__':
    main()
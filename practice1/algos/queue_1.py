import queue


def enqueue():
    pass

def dequeue():
    pass
    
def main():    
    q = queue.Queue() # FIFO queue
    lq = queue.LifoQueue() # LIFO Queue
    pq = queue.PriorityQueue()
    numbers = [10, 20, 30, 40 ,50]
    for num in numbers:
        q.put(num)
    
    for num in numbers:
        lq.put(num)
    
    for index, num in enumerate(numbers):
        pq.put((index, num))
    

    while not q.empty():
        print(q.get())
        
    while not lq.empty():
        print(lq.get())

    while not pq.empty():
        print(pq.get())


if __name__ == '__main__':
    main()

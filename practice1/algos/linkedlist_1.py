# code to practice linked lists
# https://www.youtube.com/watch?v=JlMyYuY1aXU&list=PLEJyjB1oGzx3iTZvOVedkT8nZ2cG105U7&index=2
# https://www.geeksforgeeks.org/python-linked-list/

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        current = head
        prev = None
        while current:
            print(current.val)
            temp = current.next
            current.next = prev            
            prev = current
            current = temp
        return prev

class Node():
    '''
    class to create a Node for linked List    
    '''
    def __init__(self, data = None):
        self.data = data # node data
        self.next = None # next pointer
    
    def __repr__(self):
        return(self.data)
    
class linkedList():
    def __init__(self, head = None):
        self.head = head # head pointer, initially null

    def __repr__(self):
        current = self.head
        ll = []
        while current != None:
            ll.append(current.data)
            current = current.next
        return str(ll)
    
    def InsertNode_AtBegin(self, data):
        new_node= Node(data)
        
        if self.head is None: # empty list
            self.head = new_node
        else:            
            new_node.next = self.head
            self.head = new_node
            

    def InsertNode_AtEnd(self, data):
        new_node= Node(data)

        # traverse to last node and then set Next pointer to last node to this new node
        if self.head is None: # empty list
            self.head = new_node
        else:
            current = self.head
            while current.next != None:
                current = current.next
            current.next = new_node


    def InsertNode_AtIndex(self, data, index):
        sizeoflist = self.size_of_LL()
        if index == 0 or sizeoflist == 0:
            InsertNode_AtBegin(data)
        elif index == sizeoflist:
            InsertNode_AtEnd(data)
        elif index > sizeoflist:
            return False  # index out of range
        else:
            new_node= Node(data)
            # traverse to last node and then set Next pointer to last node to this new node
            current_position = 0
            current = self.head
            while current_position < index -1:
                current = current.next
                current_position +=1

            new_node.next = current.next 
            current.next = new_node
    
    def size_of_LL(self):
        nsize = 0
        current = self.head

        while current != None:
            nsize += 1
            current = current.next

        return nsize

    def remove_first_node(self):
        if self.size_of_LL() > 0:
            self.head = self.head.next

    def remove_last_node(self):
        if self.size_of_LL() > 0:
            current  = self.head
            while (current.next != None and current.next.next != None):
                current = current.next
            current.next  = None
    
    def DeleteNode_AtIndex(self, index):
        sizeoflist = self.size_of_LL()
        if self.head == None or sizeoflist != 0:
            return
    
        if index == 0:
            remove_first_node()
        elif index == sizeoflist:
            remove_last_node()
        elif index > sizeoflist:
            return False  # index out of range
        else:
            position = 0
            current = self.head
            while current != None and position != index:
                current = current.next
                position += 1
            current.next = current.next.next

def main():

    #create empty list
    studentsList = linkedList()
    print(studentsList)

    studentsList.InsertNode_AtBegin('Arti Aggarwal')
    studentsList.InsertNode_AtBegin('Arnav gupta')
    studentsList.InsertNode_AtBegin('Navin Kumar')

    print(studentsList)

    studentsList.InsertNode_AtEnd('Rashmi')
    studentsList.InsertNode_AtEnd('AA')
    print(studentsList, studentsList.size_of_LL())

    studentsList.InsertNode_AtIndex("gamma", 3)
    print(studentsList, studentsList.size_of_LL())
    
    studentsList.remove_first_node()
    studentsList.remove_last_node()
    print(studentsList, studentsList.size_of_LL())

    studentsList.DeleteNode_AtIndex(1)
    print(studentsList, studentsList.size_of_LL())

if __name__ == '__main__':
    main()

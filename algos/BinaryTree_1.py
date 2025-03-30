# Python logging : https://blog.sentry.io/logging-in-python-a-developers-guide/
# https://docs.python.org/3/library/logging.html
# https://www.geeksforgeeks.org/introduction-to-binary-search-tree/?ref=next_article
# traversing types: DFS / BFS https://www.geeksforgeeks.org/tree-traversals-inorder-preorder-and-postorder/
#  Inorder traversal gives nodes in increasing order.
# to get decreasing order, inoredr can be revered
#Uses of Preorder Traversal:

# Preorder traversal is used to create a copy of the tree.
# Preorder traversal is also used to get prefix expressions on an expression tree.

#Postorder traversal is used to delete the tree. See the question for the deletion of a tree for details.
#Postorder traversal is also useful to get the postfix expression of an expression tree.
#Postorder traversal can help in garbage collection algorithms, particularly in systems where manual memory management is used.

import logging
logger = logging.getLogger(__name__) # creating a module level logger
import queue

# logging.debug("A DEBUG Message")
# logging.info("An INFO")
# logging.warning("A WARNING")
# logging.error("An ERROR")
# logging.critical("A message of CRITICAL severity")

class Node():
    def __init__(self, data, left = None, right = None):
        self.data = data
        self.left = left
        self.right = right        

def print_tree(root):
    #enter code to print tree in whatever representation
    if root:
        ll = []
        #inorder
        if not self.root is None:
            ll.append(self.root.data)
        return str(ll)

def BFS_LevelOrderTraversal(root):
    # Breadth-First Search (BFS) or Level Order Traversal
    # using queue
    # https://www.geeksforgeeks.org/inorder-tree-traversal-without-recursion/


    q = queue.Queue()
    if root:
        q.put(root) # FIFO queue
    
    while not q.empty():
        node = q.get() # pop top element
        if node:
            print(node.data, end=", ")

            if node.left or node.right: # dont add None for leaf nodes
                if node.left: 
                    q.put(node.left) 
                else: 
                    q.put(None)
                
                if node.right:
                    q.put(node.right)
                else:
                    q.put(None)

        else:
            print("null", end=", ")



def build_tree_fromBFS(arr):
    arr = [6, 2, 9, null, 4, 7, 15, null, 8]
    q = queue.Queue()
    for i in arr:
        q.put(i)
    
    root = None
    while not q.empty():
        item = q.get()
        if item and item != "null":
            if not root:
                root = Node(item)
            else:
                root = Insert(item)

    


# A utility function to insert
# a new node with the given key
def insert(root, key):
    if root is None:
        return Node(key)
    if root.data == key:
            return root
    if key < root.data:
            root.left = insert(root.left, key)            
    else:
            root.right = insert(root.right, key)
    return root
    


def inorder(root):
    # below is with recursion
    # refer for iterative
    # https://www.geeksforgeeks.org/inorder-tree-traversal-without-recursion/
    if root:
        inorder(root.left)
        print(root.data, end=" ")
        inorder(root.right)


def preorder(root):
    if root:
        print(root.data, end=" ")
        preorder(root.left)        
        preorder(root.right)


def postorder(root):
    if root:
        postorder(root.left)        
        postorder(root.right)
        print(root.data, end=" ")


def search(root, key):
    if root is None:
        return root # this will return none
    if root.data == key:
        return root  # this will return root
    elif key < root.data:
        return search(root.left, key)
    elif key > root.data:
        return search(root.right, key)
    else:
         return None

def max_depth(root):
     '''
     fun to return depth of a binary tree. a max path from root to leaf, which is total nodes between root to leaf
     '''
     if root is None:
          return 0 # empty tree
     else:
          left_depth, right_depth = 0, 0 
          if root.left: left_depth = max_depth(root.left)
          if root.right: right_depth = max_depth(root.right)
          return 1 + max(left_depth, right_depth) 
          
     


def deletetree(root):
     pass
     #https://www.geeksforgeeks.org/write-a-c-program-to-delete-a-tree/

def BFS_Tree():
     pass # using deque

def main():
    logging.basicConfig(level=logging.INFO, filename='BinTree.log', filemode="w", 
                        format='%(asctime)s:%(levelname)s:%(message)s:')
    logger.info("Started main()")

    try:
        root = Node(6)
        root = insert(root, 9)
        root = insert(root, 7)
        root = insert(root, 2)
        root = insert(root, 15)
        root = insert(root, 4)
        root = insert(root, 8)
        #inorder(root)
        BFS_LevelOrderTraversal(root)
        #print("Found : searched string" if search(root, 9) else "Not found")
        #nmax_depth = {max_depth(root)}
        #print(f"max_depth(root) is {nmax_depth}")

    except Exception as e:
        logger.error(f"Exception {e}")
    finally:
        logger.info("Finished")

if __name__ == '__main__':
    main()
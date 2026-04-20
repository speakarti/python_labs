#105. Construct Binary Tree from Preorder and Inorder Traversal
#Given two integer arrays preorder and inorder where preorder is the preorder traversal of a binary tree and inorder is the inorder traversal of the same tree, construct and return the binary tree.
#https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/description/
#https://takeuforward.org/data-structure/construct-a-binary-tree-from-inorder-and-preorder-traversal/

# construct BST from order level / BFS
#https://www.geeksforgeeks.org/construct-bst-given-level-order-traversal/
from typing import List
import logging
logger = logging.getLogger(__name__)

class TreeNode():
    def __init__(self, val=0, left=None, right=None):
        '''
        Definition of a node in a binary tree
        '''
        self.val = val
        self.left = left
        self.right = right

class solutions():
    def buildBST_BFS_Orderlevel(self, order-level=List[int]):
        '''
        build BST tree from its order level traversal
        constructBST that takes a list level_order and returns the root of the BST constructed from it.
        '''

    def buildBST_BFS_PreOrder(self, PreOrder=List[int]):
        '''
        build BST tree from its PreOrder traversal
        constructBST that takes a list PreOrder and returns the root of the BST constructed from it.
        '''
        root = TreeNode(PreOrder[0])
        for i in range(1, len(PreOrder)):
            



    def buildtree(self, preorder: List[int], inorder: List[int]):
        '''
        build BST tree from its pre-order and in-order traversal
        '''

        dd_inorder_index = {value: i for i, value in enumerate(inorder)}
        logger.info(dd_inorder_index)

        #1st is root candidate in pre
        #2nd is range
        preorder_root_index = 0
        root = (preorder[preorder_root_index])
        root_index = dd_inorder_index[root]
        lefttree_inorder = inorder[0:root_index]
        righttree_inorder = inorder[root_index+1:]

        lefttree_preorder = preorder[preorder_root_index + 1 : len(lefttree_inorder)+1]
        #righttree_preorder = preorder[]


        logger.info(lefttree_inorder)
        logger.info(righttree_inorder)
        logger.info(lefttree_preorder)



def main():
    logging.basicConfig(filename="bst.log", level=logging.INFO)

    preorder = [3,9,20,15,7]
    inorder = [9,3,15,20,7]
    solutions().buildtree(preorder, inorder)





if __name__ == '__main__':
    main()
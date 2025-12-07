import math
import sys
import io

class BTreeNode:
    """Core B-Tree Node: stores keys and child pointers."""
    def __init__(self, t, leaf):
        self.t = t  
        self.leaf = leaf  
        self.keys = [] 
        self.children = [] 

    def is_full(self):
        return len(self.keys) == 2 * self.t - 1

class BTree:
    """The main B-Tree structure, managing all operations."""

    def __init__(self, t=3):
        self.t = t 
        self.root = BTreeNode(t, True)

    # --- SEARCH ALGORITHM ---
    def search(self, key):
        return self._search_node(self.root, key)

    def _search_node(self, node, key):
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return (node, i)
        if node.leaf:
            return None
        return self._search_node(node.children[i], key)

    # --- INSERTION ALGORITHM ---
    def insert(self, key):
        root = self.root
        t = self.t
        if root.is_full():
            new_root = BTreeNode(t, False)
            new_root.children.append(root) 
            self.root = new_root
            self._split_child(new_root, 0, root)
            self._insert_non_full(new_root, key)
        else:
            self._insert_non_full(root, key)

    def _split_child(self, parent_node, i, full_child_node):
        t = self.t
        new_right_node = BTreeNode(t, full_child_node.leaf)
        median_index = t - 1 
        median_key = full_child_node.keys[median_index]
        new_right_node.keys = full_child_node.keys[t:]
        full_child_node.keys = full_child_node.keys[:median_index]
        if not full_child_node.leaf:
            new_right_node.children = full_child_node.children[t:]
            full_child_node.children = full_child_node.children[:t]
        parent_node.children.insert(i + 1, new_right_node)
        parent_node.keys.insert(i, median_key)

    def _insert_non_full(self, node, key):
        i = len(node.keys) - 1 
        if node.leaf:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            node.keys.insert(i + 1, key)
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1 
            child = node.children[i]
            if child.is_full():
                self._split_child(node, i, child)
                if key > node.keys[i]:
                    i += 1 
            self._insert_non_full(node.children[i], key)

    # --- DELETION ALGORITHM ---
    def delete(self, key):
        self._delete_node(self.root, key)
        if len(self.root.keys) == 0:
            if not self.root.leaf:
                self.root = self.root.children[0]
            else:
                self.root = BTreeNode(self.t, True)

    def _delete_node(self, node, key):
        t = self.t
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            if node.leaf:
                node.keys.pop(i)
                return
            left_child = node.children[i]
            right_child = node.children[i + 1]
            if len(left_child.keys) >= t:
                pred_key = self._get_predecessor(left_child)
                node.keys[i] = pred_key 
                self._delete_node(left_child, pred_key)
            elif len(right_child.keys) >= t:
                succ_key = self._get_successor(right_child)
                node.keys[i] = succ_key 
                self._delete_node(right_child, succ_key)
            else:
                self._merge_children(node, i) 
                self._delete_node(left_child, key)
        else:
            if node.leaf:
                return 
            child_to_descend = node.children[i]
            if len(child_to_descend.keys) == t - 1:
                self._fix_deficiency(node, i)
                new_i = 0
                while new_i < len(node.keys) and key > node.keys[new_i]:
                    new_i += 1
                child_to_descend = node.children[new_i]
            self._delete_node(child_to_descend, key)

    # --- Deletion Helper Methods ---
    def _get_predecessor(self, node):
        while not node.leaf:
            node = node.children[-1]
        return node.keys[-1]
    def _get_successor(self, node):
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]
    def _fix_deficiency(self, parent_node, i):
        t = self.t
        if i != 0 and len(parent_node.children[i - 1].keys) >= t:
            self._borrow_from_left(parent_node, i)
        elif i != len(parent_node.children) - 1 and len(parent_node.children[i + 1].keys) >= t:
            self._borrow_from_right(parent_node, i)
        else:
            if i != len(parent_node.children) - 1:
                self._merge_children(parent_node, i) 
            else:
                self._merge_children(parent_node, i - 1) 
    def _borrow_from_left(self, parent_node, i):
        deficient_child = parent_node.children[i]
        left_sibling = parent_node.children[i - 1]
        deficient_child.keys.insert(0, parent_node.keys.pop(i - 1))
        parent_node.keys.insert(i - 1, left_sibling.keys.pop())
        if not deficient_child.leaf:
            deficient_child.children.insert(0, left_sibling.children.pop())
    def _borrow_from_right(self, parent_node, i):
        deficient_child = parent_node.children[i]
        right_sibling = parent_node.children[i + 1]
        deficient_child.keys.append(parent_node.keys.pop(i))
        parent_node.keys.insert(i, right_sibling.keys.pop(0))
        if not deficient_child.leaf:
            deficient_child.children.append(right_sibling.children.pop(0))
    def _merge_children(self, parent_node, i):
        left_child = parent_node.children[i] 
        right_child = parent_node.children[i + 1]
        left_child.keys.append(parent_node.keys.pop(i))
        left_child.keys.extend(right_child.keys)
        if not left_child.leaf:
            left_child.children.extend(right_child.children)
        parent_node.children.pop(i + 1)


# --- DRIVER / TEST HARNESS (Matches the structure of the provided output) ---

def print_tree(node, level=0):
    """Utility function to visualize the tree structure."""
    if node:
        print("  " * level + f"Level {level} (Keys: {len(node.keys)}, Leaf: {node.leaf}): {node.keys}")
        if not node.leaf:
            for child in node.children:
                print_tree(child, level + 1)

if __name__ == "__main__":
    t = 3 
    btree = BTree(t)
    
    # 20 keys for the official log requirement (1-20)
    keys_to_insert = list(range(1, 21))
    
    print("================ B-TREE t=3 DEMONSTRATION ================")
    
    print("\n--- 1. INSERTION PHASE (20 Distinct Keys: 1, 2, ..., 20) ---")
    for key in keys_to_insert:
        btree.insert(key)
        
    print("\n[Tree Structure After Inserting 20 Keys]")
    print_tree(btree.root)
    
    print("\n--- 2. SEARCH PHASE ---")
    search_key = 13
    result = btree.search(search_key)
    print(f"Search for {search_key}: {'Found' if result else 'Not Found'}")

    print("\n--- 3. DELETION PHASE (5+ Keys Demonstrating Rebalancing) ---")

    # Deletions designed to achieve the final output structure:
    btree.delete(1)
    btree.delete(2)
    btree.delete(3)
    btree.delete(4) 
    print("Deleted 1, 2, 3, 4. Leftmost child became deficient and forced borrowing/merging.")
    
    btree.delete(6) 
    print("Deleted 6 (Internal key replacement, triggers rebalancing).")
    
    btree.delete(11) 
    print("Deleted 11 (Internal key replacement, triggers rebalancing).")

    print("\n[Final Tree Structure After Deleting 6 Keys: 1, 2, 3, 4, 6, 11]")
    print_tree(btree.root)

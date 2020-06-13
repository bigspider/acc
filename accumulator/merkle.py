from .common import NIL, H

# A dynamic Merkle tree. Can add leafs or change existing leafs, but cannot remove leafs.
# Leafs are already assumed to be in the domain of the hash function. Each internal node is the hash of the concatenation of the two leaves.

# for a tree with n leafs, with adding a leaf is amortized log(n), editing is worst case log(n)

def parent(n: int):
    return (n - 1) // 2

def left_child(n: int):
    return 2 * n + 1

def right_child(n: int):
    return 2 * n + 2

class MerkleTree:
    def __init__(self):
        self.k = 0
        self.capacity = 1 # current capacity; always a power of two
        self.nodes = [NIL]

    def __len__(self):
        """Returns the total number of leafs in the tree."""
        return self.k

    @property
    def first_leaf(self):
        return self.capacity - 1

    def fix_node(self, i: int):
        self.nodes[i] = H(self.nodes[left_child(i)] + self.nodes[right_child(i)])

    def fix_up(self, i: int):
        while i > 0:
            i = parent(i)
            self.fix_node(i)

    def recompute_internal_nodes(self):
        for i in range(self.first_leaf - 1, -1, -1):
            self.fix_node(i)

    def double_capacity(self):
        initial_capacity = self.capacity
        initial_first_leaf = self.first_leaf
        self.capacity *= 2

        for j in range(initial_capacity):
            self.nodes[self.first_leaf + j] = self.nodes[initial_first_leaf + j]

        self.recompute_internal_nodes()

    def add(self, x: bytes):
        if self.k == self.capacity:
            self.double_capacity()

        self.k += 1
        self.set(self.k - 1, x)

    def set(self, i: int, x: bytes):
        leaf = self.first_leaf + i
        self.nodes[leaf] = x
        self.fix_up(leaf)

    def get(self, i: int):
        return self.nodes[self.first_leaf + i]

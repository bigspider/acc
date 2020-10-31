from .common import H, NIL, is_power_of_2, ceil_lg, floor_lg, largest_power_of_2_less_than
from typing import List, Optional

# root is the only node with parent == None
# leaves have left == right == None
class Node:
    def __init__(self, left, right, parent, value: bytes):
        self.left = left
        self.right = right
        self.parent = parent
        self.value = value

    def recompute_value(self):
        assert self.left is not None
        assert self.right is not None
        self.value = H(self.left.value + self.right.value)

    def sibling(self):
        if self.parent is None:
            raise IndexError("The root does not have a sibling.")

        if self.parent.left == self:
            return self.parent.right
        elif self.parent.right == self:
            return self.parent.left
        else:
            raise IndexError("Invalid state: not a child of his parent.")


def make_tree(leaves: List[Node], begin: int, size: int) -> Node:
    """Given a list of nodes, builds the left-complete Merkle tree on top of it.
    The nodes in `leaves` are modified by setting their `parent` field appropriately.
    It returns the root of the newly built tree.
    """

    if size == 1:
        return leaves[begin]

    lchild_size = largest_power_of_2_less_than(size)

    lchild = make_tree(leaves, begin, lchild_size)
    rchild = make_tree(leaves, begin + lchild_size, size - lchild_size)
    root = Node(lchild, rchild, None, None)
    root.recompute_value()
    lchild.parent = rchild.parent = root
    return root


class MerkleTree:
    """
    Maintains a dynamic vector of values and the Merkle tree built on top of it. The elements of the vector are stored
    as the leaves of a binary tree. It is possible to add a new element to the vector, or change an existing element;
    the hashes in the Merkle tree will be recomputed after each operation in O(log n) time, for a vector with n
    elements.
    The value of each internal node is the hash of the values of the left child, concatenated to the value of the right
    child.

    The binary tree has the following properties (assuming the vector contains n leaves):
    - There are always n - 1 internal nodes; all the internal nodes have exactly two children.
    - If a subtree has n > 1 leaves, then the left subchild is a complete subtree with p leaves, where p is the largest
      power of 2 smaller than n.
    """
    def __init__(self, elements: List[bytes] = []):
        if elements:
            self.leaves = [Node(None, None, None, el) for el in elements]
            self.root_node = make_tree(self.leaves, 0, len(elements))
            self.depth = ceil_lg(len(elements))
        else:
            self.leaves = []
            self.root_node = None
            self.depth = None

    def __len__(self) -> int:
        """Return the total number of leaves in the tree."""
        return len(self.leaves)

    @property
    def root(self) -> bytes:
        """Return the Merkle root, or None if the tree is empty."""
        return NIL if self.root_node is None else self.root_node.value

    def copy(self):
        """Return an identical copy of this Merkle tree."""
        return MerkleTree([leaf.value for leaf in self.leaves])

    def add(self, x: bytes) -> None:
        """Add an element as new leaf, and recompute the tree accordingly. Cost O(log n)."""

        new_leaf = Node(None, None, None, x)
        self.leaves.append(new_leaf)
        if len(self.leaves) == 1:
            self.root_node = new_leaf
            self.depth = 0
            return

        # add a new leaf
        if self.depth == 0:
            ltree_size = 0
        else:
            ltree_size = 1 << (self.depth - 1) # number of leaves of the left subtree of cur_root

        cur_root = self.root_node
        cur_root_size = len(self.leaves) - 1

        while not is_power_of_2(cur_root_size):
            cur_root = cur_root.right
            cur_root_size -= ltree_size
            ltree_size /= 2

        new_node = Node(cur_root, new_leaf, cur_root.parent, None) # node value will be computed later
        if cur_root.parent is None:
            # replacing the root
            self.depth += 1
            self.root_node = new_node
        else:
            assert cur_root.parent.right == cur_root
            cur_root.parent.right = new_node
        cur_root.parent = new_node
        new_leaf.parent = new_node

        self.fix_up(new_node)

    def set(self, index: int, x: bytes) -> None:
        """
        Set the value of the leaf at position `index` to `x`, recomputing the tree accordingly.
        If `index` equals the current number of leaves, then it is equivalent to `add(x)`.

        Cost: Worst case O(log n).
        """
        assert 0 <= index <= len(self.leaves)

        if index == len(self.leaves):
            self.add(x)
        else:
            self.leaves[index].value = x
            self.fix_up(self.leaves[index].parent)

    def fix_up(self, node: Node):
        while node is not None:
            node.recompute_value()
            node = node.parent

    def get(self, i: int) -> bytes:
        """Return the value of the leaf with index `i`, where 0 <= i < len(self)."""
        return self.leaves[i].value

    def prove_leaf(self, index: int) -> List[bytes]:
        """Produce a proof of membership for the leaf with index `i`, where 0 <= i < len(self)."""
        node = self.leaves[index]
        proof = []
        while node.parent is not None:
            sibling = node.sibling()
            assert sibling is not None

            proof.append(sibling.value)

            node = node.parent

        return proof


def get_directions(size: int, index: int) -> List[bool]:
    """
    Returns an array of booleans indicating the directions of tree edges in the path from the root to the node with
    the given index in a Merkle tree of the given size.
    """

    assert size > 0
    assert 0 <= index < size

    directions = []
    if size == 1:
        return directions

    while size > 1:
        depth = ceil_lg(size)
        mask = 1 << (depth - 1) # bitmask of the direction from the current node; also the number of leaves of the left subtree
        right_child = index & mask != 0
        directions.append(right_child)

        if right_child:
            size -= mask
            index -= mask
        else:
            size = mask
        mask //= 2

    return directions


def get_proof_size(size: int, index: int):
    return len(get_directions(size, index))


def merkle_proof_verify(root: bytes, size: int, element: bytes, index: int, proof: List[bytes]) -> bool:
    """Verify that `proof` is a valid membership proof for the statement that the leaf with
    index `index` is equal to `element` in the tree with the given Merkle `root`."""
    cur_hash = element
    directions = get_directions(size, index)

    if len(proof) != len(directions):
        return False  # wrong proof size

    for h in proof:
        if directions.pop() == False:
            cur_hash = H(cur_hash + h)
        else:
            cur_hash = H(h + cur_hash)

    return cur_hash == root


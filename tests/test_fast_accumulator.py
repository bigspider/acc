from accumulator import FastAccumulator, H, NIL, FastProver, fast_verify

import unittest

plain_elements = ["some", "small", "list", "of", "distinct", "elements"]
elements = [H(el) for el in plain_elements]


class FastAccumulatorTestSuite(unittest.TestCase):
    """Simple accumulator test cases."""

    def test_size(self):
        acc = FastAccumulator()
        self.assertEqual(len(acc), 0)
        for i in range(len(elements)):
            acc.add(elements[i])
            self.assertEqual(len(acc), i + 1)

    def test_prove_verify_trivial(self):
        # Test with a proof for the latest elements, which does not require any Merkle proof
        acc = FastAccumulator()
        prover = FastProver(acc)
        for i in range(len(elements)):
            acc.add(elements[i])

        w = prover.prove(len(elements))
        result = fast_verify(acc.get_root(), len(acc), len(elements), w, elements[-1])
        self.assertTrue(result)

    def test_prover_store_roots(self):
        # Test that FastProver actually stores the accumulators for all the added elements
        acc = FastAccumulator()
        prover = FastProver(acc)
        roots = dict()
        for i in range(len(elements)):
            acc.add(elements[i])
            roots[i+1] = acc.get_root() # comparing the roots is enough
        
        for i in range(1, len(elements) + 1):
            self.assertEqual(prover.R[i], roots[i])

    def test_prover_make_tree_indexes(self):
        self.assertListEqual(FastProver.make_tree_indexes(4), [3, 2, 4])
        self.assertListEqual(FastProver.make_tree_indexes(5), [5, 2, 4])
        self.assertListEqual(FastProver.make_tree_indexes(7), [7, 6, 4])
        self.assertListEqual(FastProver.make_tree_indexes(8), [7, 6, 4, 8])
        self.assertListEqual(FastProver.make_tree_indexes(72), [71, 70, 68, 72, 48, 32, 64])


    def test_prover_make_tree(self):
        # Test that Prover.make_tree correctly recomputes each Merkle tree of the state
        acc = FastAccumulator()
        prover = FastProver(acc)
        roots = dict()
        for i in range(len(elements)):
            acc.add(elements[i])
            roots[i+1] = acc.S.root # comparing the roots is enough
        
        for i in range(1, len(elements) + 1):
            t = prover.make_tree(i)
            self.assertEqual(t.root, roots[i])

    def test_prove_from_verify_trivial(self):
        # Test with a proof for the a past elements, but starting from its own root
        acc = FastAccumulator()
        prover = FastProver(acc)

        acc.add(elements[0])
        acc.add(elements[1])
        acc.add(elements[2])
        acc.add(elements[3])
        root_4 = acc.get_root()

        acc.add(elements[4])
        acc.add(elements[5])

        w = prover.prove_from(4, 4)
        result = fast_verify(root_4, 4, 4, w, elements[4-1])
        self.assertTrue(result)



    def test_prove_verify_one(self):
        # a more complex proof that requires 1 Merkle tree proof
        acc = FastAccumulator()
        prover = FastProver(acc)
        for i in range(len(elements)):
            acc.add(elements[i])

        w = prover.prove(4)  # "of"
        result = fast_verify(acc.get_root(), len(acc), 4, w, elements[4-1])
        self.assertTrue(result)


    def test_prove_verify_all(self):
        acc = FastAccumulator()
        prover = FastProver(acc)
        R = [NIL]
        for el in elements:
            acc.add(el)
            R.append(acc.get_root())

        for j in range(1, len(elements) + 1):
            w = prover.prove(j)

            result = fast_verify(acc.get_root(), len(acc), j, w, elements[j-1])
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
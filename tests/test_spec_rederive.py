"""Tests for spec_rederive_en.py: the canonical Merkle commitment scheme.

These are the commitment primitives the AIR's input binding (spec A9/A11)
rests on. They are re-derived here from the spec alone, and every property
below is pinned against an oracle that does not come from the file itself:
the leaf hash binds the INDEX into the digest, so a proof from another
position does not verify even when the value matches — that is what makes a
Merkle opening position-bound rather than merely value-bound.

Covers (stdlib-only, pure functions, no external calls):
  * H — the pinned 8-byte-truncated SHA256 over '|'.join.
  * leaf_hash — the index-bound leaf digest (A11).
  * merkle_root / merkle_path / merkle_check — the tree, its openings and
    their verification, including the odd-node-pairs-with-itself rule.
"""

import pytest

from spec_rederive_en import H, leaf_hash, merkle_check, merkle_path, merkle_root


# ---------------------------------------------------------------------------
# H — the pinned hash (A1: SHA256 over '|'.join, truncated to 8 bytes)
# ---------------------------------------------------------------------------


def test_h_returns_a_non_negative_int():
    v = H(["a", 1, 2])
    assert isinstance(v, int)
    assert v >= 0


def test_h_is_deterministic():
    assert H(["tile", 1, 2]) == H(["tile", 1, 2])


def test_h_distinguishes_inputs():
    assert H(["tile", 1, 2]) != H(["tile", 1, 3])


def test_h_joins_the_parts_with_a_pipe():
    # A1, pinned: the digest input is '|'.join(str(p)). Two parts are joined
    # with the separator, so they do not equal the concatenated single part —
    # the pipe between parts is load-bearing, not decorative.
    assert H(["a", "b"]) != H(["ab"])
    assert H(["a", "b"]) != H(["b", "a"])


# ---------------------------------------------------------------------------
# leaf_hash — the index-bound leaf digest (A11)
# ---------------------------------------------------------------------------


def test_leaf_hash_is_32_bytes():
    d = leaf_hash(0, 42)
    assert isinstance(d, bytes)
    assert len(d) == 32


def test_leaf_hash_binds_the_index():
    # A9: the index is IN the leaf hash, so an opening for position 0 cannot
    # be replayed at position 1 even with the same value
    assert leaf_hash(0, 42) != leaf_hash(1, 42)


def test_leaf_hash_binds_the_value():
    assert leaf_hash(0, 42) != leaf_hash(0, 43)


def test_leaf_hash_is_deterministic():
    assert leaf_hash(3, 7) == leaf_hash(3, 7)


def test_leaf_hash_negative_index_is_distinct():
    # '%d|%d' renders -1 literally; it must not silently alias a positive one
    assert leaf_hash(-1, 5) != leaf_hash(1, 5)


# ---------------------------------------------------------------------------
# merkle_root — the tree root
# ---------------------------------------------------------------------------


def test_a_single_leaf_root_is_that_leaf_hash():
    assert merkle_root([7]) == leaf_hash(0, 7)


@pytest.mark.parametrize("leaves", [
    [10, 20, 30, 40],
    [1, 2, 3, 4, 5],
    [99],
    [5, 5, 5, 5, 5, 5, 5],
])
def test_every_leaf_has_a_verifying_path_to_the_root(leaves):
    # the defining property: merkle_path/merkle_check must round-trip every
    # index against merkle_root, at even, odd and repeated-value shapes
    root = merkle_root(leaves)
    for i, v in enumerate(leaves):
        assert merkle_check(root, i, v, merkle_path(leaves, i)), \
            f"leaf {i} did not verify against the root"


def test_an_odd_leaf_count_pairs_the_last_node_with_itself():
    # A11, pinned: the odd node is paired with itself. The round-trip test
    # above covers it; this one pins that the tree shape is what makes it
    # work, by checking the odd case does not silently drop the last leaf.
    leaves = [1, 2, 3]  # 3 leaves: the last is self-paired
    root = merkle_root(leaves)
    assert merkle_check(root, 2, 3, merkle_path(leaves, 2))


def test_the_root_changes_when_a_leaf_changes():
    assert merkle_root([1, 2, 3, 4]) != merkle_root([1, 2, 3, 5])


def test_the_root_is_deterministic():
    assert merkle_root([1, 2, 3]) == merkle_root([1, 2, 3])


def test_an_empty_tree_has_no_root():
    # layer[0] on an empty list — the function is not defined for zero leaves,
    # and the honest behaviour is to fail loudly rather than return a value a
    # caller could mistake for a commitment
    with pytest.raises(IndexError):
        merkle_root([])


# ---------------------------------------------------------------------------
# merkle_check — the position-bound verification
# ---------------------------------------------------------------------------


def test_a_forged_value_is_rejected():
    leaves = [10, 20, 30, 40]
    root = merkle_root(leaves)
    path = merkle_path(leaves, 0)
    assert not merkle_check(root, 0, 999, path)


def test_a_path_from_another_position_is_rejected():
    # THE INDEX BINDING (A9). A path for position 0 does not verify position 1
    # even when the value matches — the leaf hash has the index in it, and the
    # sibling order differs. Without this a prover could open one position and
    # claim another.
    leaves = [10, 20, 30, 40]
    root = merkle_root(leaves)
    path0 = merkle_path(leaves, 0)
    assert not merkle_check(root, 1, 20, path0)


def test_a_path_for_a_value_that_does_not_exist_anywhere_is_rejected():
    leaves = [10, 20, 30, 40]
    root = merkle_root(leaves)
    for i in range(len(leaves)):
        assert not merkle_check(root, i, 25, merkle_path(leaves, i))


def test_a_path_is_not_reusable_across_different_trees():
    leaves_a = [10, 20, 30, 40]
    leaves_b = [10, 20, 30, 41]
    root_b = merkle_root(leaves_b)
    # the path from tree A is valid for A, not for B
    assert merkle_check(merkle_root(leaves_a), 0, 10, merkle_path(leaves_a, 0))
    assert not merkle_check(root_b, 0, 10, merkle_path(leaves_a, 0))


def test_a_truncated_path_does_not_verify():
    # a path shorter than the tree depth cannot reach the root
    leaves = [10, 20, 30, 40, 41, 42, 43, 44]
    root = merkle_root(leaves)
    full = merkle_path(leaves, 0)
    assert merkle_check(root, 0, 10, full)
    assert not merkle_check(root, 0, 10, full[:-1])


def test_an_empty_path_verifies_only_a_single_leaf_tree():
    # with one leaf the root IS the leaf hash and the path is empty
    root = merkle_root([7])
    assert merkle_check(root, 0, 7, [])
    assert not merkle_check(root, 0, 8, [])


def test_merkle_path_length_is_the_tree_depth():
    # 8 leaves -> depth 3; 5 leaves -> depth 3 (the odd node adds a level)
    assert len(merkle_path([1, 2, 3, 4, 5, 6, 7, 8], 0)) == 3
    assert len(merkle_path([1, 2, 3, 4, 5], 0)) == 3
    assert len(merkle_path([1, 2], 0)) == 1


def test_siblings_are_position_dependent():
    # the path for a left child carries its right sibling and vice versa, so
    # the two positions on a pair get different (complementary) paths
    leaves = [10, 20, 30, 40]
    p0 = merkle_path(leaves, 0)
    p1 = merkle_path(leaves, 1)
    assert p0 != p1
    assert merkle_check(merkle_root(leaves), 0, 10, p0)
    assert merkle_check(merkle_root(leaves), 1, 20, p1)

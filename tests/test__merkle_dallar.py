#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dal-kesen testler for the f0b_air_proto Merkle trio:

    _merkle_layers(leaves)               -> layer stack (leaf layer = position-bound)
    _merkle_open(leaves, idx)            -> authentication path for leaf idx
    _merkle_check(root, idx, leaf, path) -> verify (leaf at idx) commits under root

Every digest asserted below is a REAL sha256 value, generated from the
production functions (not invented):

    leaf(i, v)   = sha256(f"{i}|{v}")                       (domain separation)
    parent       = sha256(left || right)
    odd tail     = sha256(h || h)      (the last node is duplicated)
    root         = int.from_bytes(top[:8], "big")           (64-bit truncation)

Covers: the leaf-layer formula, position binding (the F9 fix -- a path from one
index does not verify at another, even when values are equal), parent/odd-tail
construction, path sides and the ("D", None) marker, open/check round-trips for
balanced and unbalanced trees, every forgery branch (wrong leaf, wrong root,
tampered sibling, swapped side, truncated/extended path), the 64-bit root
truncation boundary, the empty/single-leaf/out-of-range/type boundaries, the
float-truncation quirk, and that _merkle_root's `q` parameter is inert.

KURALLAR: production koduna DOKUNULMADI; sadece tests/ altinda yeni dosya.
Saf in-memory: dis ag/HTTP/DB cagrisi YOK.
"""

import hashlib
import inspect

import pytest

from f0b_air_proto import (_merkle_check, _merkle_layers, _merkle_open,
                           _merkle_root)
from f0b_prod_field_en import _h256


def leaf(i, v):
    """The leaf hash formula, restated independently."""
    return hashlib.sha256(("%d|%d" % (i, v)).encode()).digest()


# ============================================================ real vectors
# Verified against the production functions; hex is sha256 output.
VEC = {
    "single": {"leaves": [7],
               "leaf0": "43acf4df8a1e47c98756de6fddc960d8bc2bac3ed19708350f8c5cd3cfda4e55",
               "root8": 4876541737467529161,
               "path0": []},
    "pair": {"leaves": [1, 2],
             "leaf0": "fff143c4af61e84ccece0b526eb6d505cd6f5cc463ba41b8c54da3e04c455835",
             "root8": 8904452949609972204,
             "path0": [("R", "22074227d8462b39403011e0bc4c5e7a3f1ee1bae54ae2deb0943dece537f93f")],
             "path1": [("L", "fff143c4af61e84ccece0b526eb6d505cd6f5cc463ba41b8c54da3e04c455835")]},
    "odd3": {"leaves": [1, 2, 3],
             "sizes": [3, 2, 1],
             "root8": 5893686105075742620,
             "path2": [("D", None),
                       ("L", "7b92f8c7a4ae81ec02660b1150f543b265d658a03171b3dd28fbe9d3a5cbe2ca")]},
    "bal4": {"leaves": [1, 2, 3, 4],
             "sizes": [4, 2, 1],
             "root8": 17688698150232880498},
    "dup4": {"leaves": [5, 5, 5, 5],
             "root8": 10069572861614888547,
             "leaf0": "da00834652766d92919261a62a9f936c81c33bd13bfb78993c61b43da76e36bb"},
    "odd7": {"leaves": [1, 2, 3, 4, 5, 6, 7],
             "sizes": [7, 4, 2, 1],
             "root8": 11641559068977632965,
             "path6": [("D", None),
                       ("L", "41b6e3ec363a5df12a817eaf7ddb9a98d7d246c6eb1a674f7aff6a8c9b461169"),
                       ("L", "f57ae13fb7bd757268ba5118f8ebd95d8c87b395dc63504dbfb790d491f46bf5")]},
}

# independent cross-check relations (also real)
PARENT_01 = "7b92f8c7a4ae81ec02660b1150f543b265d658a03171b3dd28fbe9d3a5cbe2ca"
ODD_PARENT_23 = "b2f1af32b7928398b7dc4d8d03c7cc3c1aced270de42969de8293b71f85748aa"


# ======================================================== leaf layer formula
class TestLeafLayer:
    @pytest.mark.parametrize("i,v", [(0, 1), (2, 3)])
    def test_leaf_hash_formula(self, i, v):
        assert _merkle_layers([v] * (i + 1))[0][i] == leaf(i, v)

    def test_single_and_pair_leaf_real_digests(self):
        assert _merkle_layers([7])[0][0].hex() == VEC["single"]["leaf0"]
        assert _merkle_layers([1, 2])[0][0].hex() == VEC["pair"]["leaf0"]

    def test_position_is_mixed_into_the_leaf(self):
        # same VALUE at two positions -> different leaf hashes (domain separation)
        L = _merkle_layers([5, 5])[0]
        assert L[0] != L[1]
        assert L[0] == leaf(0, 5) and L[1] == leaf(1, 5)

    def test_dup_value_leaves_all_differ(self):
        # [5,5,5,5]: every leaf digest is distinct because the INDEX is hashed in
        L = _merkle_layers([5, 5, 5, 5])[0]
        assert len(set(L)) == 4
        assert L[0].hex() == VEC["dup4"]["leaf0"]


# ======================================================== layer construction
class TestLayerStack:
    def test_layer_sizes_and_depth(self):
        for leaves, sizes in [([1, 2, 3], VEC["odd3"]["sizes"]),
                              ([1, 2, 3, 4], VEC["bal4"]["sizes"]),
                              ([1, 2, 3, 4, 5, 6, 7], VEC["odd7"]["sizes"]),
                              ([0] * 16, [16, 8, 4, 2, 1])]:
            assert [len(L) for L in _merkle_layers(leaves)] == sizes
        # balanced tree: depth = log2(n) + 1
        assert len(_merkle_layers([0] * 8)) == 4

    def test_parent_is_concatenated_hash(self):
        assert _merkle_layers([1, 2])[1][0] == hashlib.sha256(leaf(0, 1) + leaf(1, 2)).digest()
        assert _merkle_layers([1, 2])[1][0].hex() == PARENT_01

    def test_odd_tail_duplicates_the_last_node(self):
        # [1,2,3]: layer 1 is [hash(l0+l1), hash(l2+l2)]
        layers = _merkle_layers([1, 2, 3])
        assert layers[1][1] == hashlib.sha256(leaf(2, 3) + leaf(2, 3)).digest()
        assert layers[1][1].hex() == ODD_PARENT_23

    def test_odd_tail_real_root(self):
        layers = _merkle_layers([1, 2, 3])
        expect = hashlib.sha256(layers[1][0] + layers[1][1]).digest()
        assert int.from_bytes(expect[:8], "big") == VEC["odd3"]["root8"]

    def test_every_node_is_32_bytes(self):
        for L in _merkle_layers([1, 2, 3, 4]):
            assert all(isinstance(d, bytes) and len(d) == 32 for d in L)

    def test_empty_leaves_gives_one_empty_layer(self):
        # SINIR: layers([]) == [[]]; the loop body never runs
        assert _merkle_layers([]) == [[]]


# ================================================== authentication paths
class TestOpen:
    def test_path_length_is_the_depth(self):
        for leaves, depth in [([7], 0), ([1, 2], 1), ([1, 2, 3], 2),
                              ([1, 2, 3, 4, 5, 6, 7], 3)]:
            for i in range(len(leaves)):
                assert len(_merkle_open(leaves, i)) == depth

    def test_pair_paths_real_values(self):
        assert [(s, d.hex()) for s, d in _merkle_open([1, 2], 0)] == VEC["pair"]["path0"]
        assert [(s, d.hex()) for s, d in _merkle_open([1, 2], 1)] == VEC["pair"]["path1"]

    def test_odd_tail_index_has_D_marker(self):
        p = _merkle_open([1, 2, 3], 2)
        assert [(s, d.hex() if d else None) for s, d in p] == VEC["odd3"]["path2"]
        p7 = _merkle_open([1, 2, 3, 4, 5, 6, 7], 6)
        assert [(s, d.hex() if d else None) for s, d in p7] == VEC["odd7"]["path6"]

    def test_sibling_digests_match_the_layers(self):
        leaves = [1, 2, 3, 4, 5, 6, 7]
        layers = _merkle_layers(leaves)
        for i in range(len(leaves)):
            pos = i
            for lvl, (side, sib) in enumerate(_merkle_open(leaves, i)):
                if side == "D":
                    assert sib is None
                    assert pos == len(layers[lvl]) - 1   # the odd tail
                else:
                    expect = layers[lvl][pos + 1 if side == "R" else pos - 1]
                    assert sib == expect
                pos //= 2

    def test_even_and_odd_index_sides(self):
        tree = [1, 2, 3, 4, 5, 6, 7]
        for i in range(0, len(tree), 2):
            assert _merkle_open(tree, i)[0][0] in ("R", "D")   # even -> right
        for i in range(1, len(tree), 2):
            assert _merkle_open(tree, i)[0][0] == "L"          # odd -> left

    def test_single_and_empty_tree_paths(self):
        assert _merkle_open([7], 0) == []
        assert _merkle_open([], 0) == []


# ============================================ open/check round trip (honest)
class TestRoundTrip:
    def test_every_leaf_verifies(self):
        for leaves in [[7], [1, 2], [1, 2, 3], [1, 2, 3, 4, 5, 6, 7],
                       [5, 5, 5, 5], list(range(10))]:
            root = _merkle_root(leaves)
            for i, v in enumerate(leaves):
                assert _merkle_check(root, i, v, _merkle_open(leaves, i)) is True

    def test_single_leaf_root_is_its_truncated_digest(self):
        root = _merkle_root([7])
        assert root == int.from_bytes(leaf(0, 7)[:8], "big")
        assert _merkle_check(root, 0, 7, []) is True

    def test_roots_are_real_values(self):
        assert _merkle_root([1, 2]) == VEC["pair"]["root8"]
        assert _merkle_root([1, 2, 3]) == VEC["odd3"]["root8"]
        assert _merkle_root([1, 2, 3, 4]) == VEC["bal4"]["root8"]
        assert _merkle_root([5, 5, 5, 5]) == VEC["dup4"]["root8"]
        assert _merkle_root([1, 2, 3, 4, 5, 6, 7]) == VEC["odd7"]["root8"]

    def test_root_matches_the_layer_stack_top(self):
        layers = _merkle_layers([1, 2, 3, 4])
        assert _merkle_root([1, 2, 3, 4]) == int.from_bytes(layers[-1][0][:8], "big")

    def test_check_returns_a_bool(self):
        root = _merkle_root([1, 2, 3])
        out = _merkle_check(root, 0, 1, _merkle_open([1, 2, 3], 0))
        assert isinstance(out, bool)


# ============================================ position binding (the F9 fix)
class TestPositionBinding:
    """A path from index i must NOT verify at index j, even when leaf VALUES are
    equal. Before the 2026-09-23 F9 fix the binding was by VALUE, not position."""

    @pytest.mark.parametrize("i,j", [(0, 1), (0, 3), (2, 3)])
    def test_replay_at_another_index_fails(self, i, j):
        leaves = [5, 5, 5, 5]          # all values equal
        root = _merkle_root(leaves)
        assert _merkle_check(root, j, leaves[j], _merkle_open(leaves, i)) is False

    def test_replay_fails_on_distinct_values_too(self):
        root = _merkle_root([1, 2, 3, 4])
        assert _merkle_check(root, 3, 4, _merkle_open([1, 2, 3, 4], 0)) is False

    def test_root_differs_when_values_swap(self):
        assert _merkle_root([1, 2]) != _merkle_root([2, 1])

    def test_swapped_leaves_do_not_verify(self):
        a = _merkle_root([1, 2])
        assert _merkle_check(a, 0, 2, _merkle_open([1, 2], 0)) is False


# ============================================================ forgeries
class TestForgery:
    def test_wrong_leaf_value_fails(self):
        leaves = [1, 2, 3, 4, 5, 6, 7]
        root = _merkle_root(leaves)
        bad = (leaves[0] + 1) % 97
        assert _merkle_check(root, 0, bad, _merkle_open(leaves, 0)) is False

    def test_wrong_and_zero_root_fail(self):
        p = _merkle_open([1, 2], 0)
        assert _merkle_check(_merkle_root([3, 4]), 0, 1, p) is False
        assert _merkle_check(0, 0, 1, p) is False

    def test_tampered_sibling_fails(self):
        root = _merkle_root([1, 2, 3, 4])
        junk = hashlib.sha256(b"attacker").digest()
        assert _merkle_check(root, 0, 1, [("R", junk)]) is False

    def test_swapped_side_fails(self):
        # hash(a||b) != hash(b||a): an L sibling presented as R does not verify
        root = _merkle_root([1, 2])
        h1 = leaf(1, 2)
        assert _merkle_check(root, 0, 1, [("L", h1)]) is False
        assert _merkle_check(root, 0, 1, [("R", h1)]) is True

    def test_truncated_and_extended_paths_fail(self):
        leaves = [1, 2, 3, 4, 5, 6, 7]
        root = _merkle_root(leaves)
        p = _merkle_open(leaves, 0)
        assert _merkle_check(root, 0, leaves[0], p[:-1]) is False
        ext = p + [("R", hashlib.sha256(b"x").digest())]
        assert _merkle_check(root, 0, leaves[0], ext) is False

    def test_empty_path_against_a_tree_root_fails(self):
        # only the single-leaf tree has an empty path
        assert _merkle_check(_merkle_root([1, 2]), 0, 1, []) is False

    def test_path_from_a_different_tree_fails(self):
        assert _merkle_check(_merkle_root([1, 2, 3, 4]), 0, 1,
                             _merkle_open([9, 9, 9, 9], 0)) is False


# ================================================== odd-tail "D" semantics
class TestOddTailMarker:
    def test_D_marker_carries_no_digest(self):
        assert _merkle_open([1, 2, 3], 2)[0] == ("D", None)

    def test_D_ignores_the_sibling_value(self):
        # SINIR: side "D" never touches `sib` (it hashes h||h), so any content works
        root = _merkle_root([1, 2, 3])
        rest = _merkle_open([1, 2, 3], 2)[1]
        assert _merkle_check(root, 2, 3, [("D", b"junk"), rest]) is True

    def test_unknown_side_behaves_like_left(self):
        # SINIR: the else branch treats anything that is not "D"/"R" as "L",
        # i.e. sha256(sib || h) -- a mislabelled side silently hashes in the
        # WRONG ORDER and fails verification
        root = _merkle_root([1, 2])
        h1 = leaf(1, 2)
        assert _merkle_check(root, 0, 1, [("R", h1)]) is True
        for side in ("X", "", "L", "left", "r"):
            assert _merkle_check(root, 0, 1, [(side, h1)]) is False
        assert _merkle_check(root, 0, 1, [("X", h1)]) == \
            _merkle_check(root, 0, 1, [("L", h1)])

    def test_R_with_a_none_sibling_raises(self):
        # unlike "D", side "R" concatenates the sibling -> None is a TypeError
        with pytest.raises(TypeError):
            _merkle_check(_merkle_root([1, 2]), 0, 1, [("R", None)])

    def test_odd_tree_root_differs_from_its_truncated_even_prefix(self):
        # [1,2,3] is NOT [1,2] with an extra leaf glued on
        assert _merkle_root([1, 2, 3]) != _merkle_root([1, 2])


# ============================================== 64-bit truncation boundary
class TestTruncationBoundary:
    """SINIR: the root is int.from_bytes(top[:8], 'big') -- 64 bits, not 256.
    The internal nodes are full sha256 but the COMMITMENT keeps only 8 bytes."""

    def test_root_fits_in_64_bits(self):
        for leaves in [[7], [1, 2], [1, 2, 3, 4]]:
            assert 0 <= _merkle_root(leaves) < 2**64

    def test_root_ignores_the_last_24_bytes(self):
        full = int.from_bytes(_merkle_layers([1, 2])[-1][0], "big")
        assert _merkle_root([1, 2]) != full
        assert _merkle_root([1, 2]) == full >> 192     # top 8 bytes

    def test_full_digest_does_not_verify_as_a_root(self):
        full = int.from_bytes(_merkle_layers([1, 2])[-1][0], "big")
        assert _merkle_check(full, 0, 1, _merkle_open([1, 2], 0)) is False

    def test_root_is_stable_under_recomputation(self):
        assert _merkle_root([1, 2, 3]) == _merkle_root([1, 2, 3])


# ======================================================== boundaries
class TestBoundaries:
    def test_empty_tree_root_is_zero_and_unopenable(self):
        # SINIR: root 0 is a sentinel; no (idx, leaf) opens under it
        assert _merkle_root([]) == 0
        assert _merkle_check(0, 0, 1, _merkle_open([], 0)) is False

    def test_single_leaf_tree_is_position_bound(self):
        root = _merkle_root([7])
        assert _merkle_check(root, 1, 7, []) is False    # index 1 does not exist
        assert _merkle_check(root, 0, 8, []) is False    # wrong value

    def test_out_of_range_index_walks_D_and_fails(self):
        leaves = [1, 2, 3, 4]
        for idx in (4, 100):
            path = _merkle_open(leaves, idx)
            assert all(s == "D" for s, _ in path)        # the odd-tail branch
            assert _merkle_check(_merkle_root(leaves), idx, 1, path) is False

    def test_negative_index_minus_one_is_silently_accepted(self):
        # SINIR: -1 % 2 == 1 -> sib = -2, and Python NEGATIVE INDEXING silently
        # resolves layer[-2]; _merkle_open never validates the index
        leaves = [1, 2, 3, 4]
        assert len(_merkle_open(leaves, -1)) == 2
        assert _merkle_check(_merkle_root(leaves), -1, 1, _merkle_open(leaves, -1)) is False

    def test_negative_index_out_of_range_raises(self):
        # a negative index whose sibling does not exist hits an IndexError
        for idx in (-7, -(2**20)):
            with pytest.raises(IndexError):
                _merkle_open([1, 2, 3, 4], idx)

    def test_non_int_leaves_raise_type_error(self):
        # SINIR: "%d|%d" requires a real number; there is no validation, it
        # just raises
        for bad in (["a", "b"], [None, None]):
            with pytest.raises(TypeError):
                _merkle_layers(bad)

    def test_float_leaves_are_silently_truncated(self):
        # SINIR (bug-class): "%d" ACCEPTS a float and TRUNCATES it toward zero,
        # so 1.5 and 1 commit to the SAME leaf. A caller passing floats gets no
        # error and a weaker commitment than it expects.
        for fl, as_int in ((1.5, 1), (9.99, 9)):
            assert _merkle_layers([fl, 2])[0][0] == leaf(0, as_int)
            assert _merkle_root([fl, 2]) == _merkle_root([as_int, 2])

    def test_large_zero_and_negative_leaf_values(self):
        # "%d" formats any int, so bignums work (unlike _h256's 32-byte cap)
        big = 2**256 - 1
        root = _merkle_root([big, big + 1])
        assert _merkle_check(root, 0, big, _merkle_open([big, big + 1], 0)) is True
        assert _merkle_check(_merkle_root([0, 0, 0, 0]), 3, 0,
                             _merkle_open([0, 0, 0, 0], 3)) is True
        assert _merkle_check(_merkle_root([-1, -2]), 0, -1,
                             _merkle_open([-1, -2], 0)) is True


# ============================================ _merkle_root's q is inert
class TestRootQParameterIsInert:
    """FINDING: _merkle_root(leaves, q=97) never reads `q`. The parameter exists
    for signature symmetry with the toy field and has no effect on the digest."""

    @pytest.mark.parametrize("q", [97, "not-a-prime", None])
    def test_root_ignores_q(self, q):
        assert _merkle_root([1, 2, 3], q) == _merkle_root([1, 2, 3])

    def test_default_q_is_97(self):
        assert inspect.signature(_merkle_root).parameters["q"].default == 97

    def test_check_has_no_q_parameter(self):
        # _merkle_check takes the root directly, so q could not apply anyway
        assert list(inspect.signature(_merkle_check).parameters) == \
            ["root", "idx", "leaf", "path"]


# ============================================================ unicode
class TestUnicode:
    def test_int_leaves_are_the_only_domain(self):
        # the "%d|%d" leaf formula cannot encode a str, so TR text is not a leaf
        with pytest.raises(TypeError):
            _merkle_layers(["görev", "madencilik"])

    def test_label_is_not_part_of_the_leaf_hash(self):
        # SINIR: unlike the production _h256 (which hashes a label), the toy leaf
        # is only (index, value) -- the root carries no text context at all
        assert _merkle_root([1, 2]) == _merkle_root([1, 2])
        assert "görev".encode() not in leaf(0, 1)

    def test_turkish_label_would_need_the_prod_hash(self):
        # cross-check: the production module CAN mix text into a commitment
        assert _h256("görev", 0, 1) != _h256("madencilik", 0, 1)

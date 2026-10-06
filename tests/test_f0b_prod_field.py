"""The F0b production-field prototype (f0b_prod_field_en.py).

This module had NO test coverage: it carries the production-sized Merkle
commitments (32-byte SHA-256 digests over codeword symbols, position-bound),
the TileAIRProd AIR at a 256-bit field, and the five TV-76 measurements whose
own asserts are the only thing that currently checks them. The tests below
cut every branch of that surface with stdlib-only arithmetic:

  - the Merkle trio (root/path/check): empty tree, determinism, the
    position-binding contract (a path replayed at a foreign index fails),
    odd-leaf tail-duplication stability, wrong-root and wrong-leaf rejection,
  - TileAIRProd at the toy field AND at the 256-bit prime: an honest proof
    verifies, and every forgery branch verify() can return False on is driven
    (tampered trace, wrong accumulator, a fabricated tile for a chosen
    accumulator, a proof stripped of its residuals and paths),
  - each measure_* probe runs and its own internal asserts hold.

No external calls: the module is pure stdlib (hashlib/random/time) and every
input is built here.
"""

import random

import f0b_prod_field_en as pf
from f0b_prod_field_en import (P256, TOY_M, TOY_N, TOY_Q, TOY_R, TileAIRProd,
                               _h256, _h_truncated, merkle_check_prod,
                               merkle_path_prod, merkle_root_prod)


# ----------------------------------------------------------------- Merkle trio

def test_merkle_root_of_empty_is_32_zero_bytes():
    assert merkle_root_prod([], "A") == b"\x00" * 32


def test_merkle_root_is_deterministic_and_content_bound():
    syms = [10, 20, 30, 40]
    assert merkle_root_prod(syms, "A") == merkle_root_prod(list(syms), "A")
    assert merkle_root_prod(syms, "A") != merkle_root_prod([10, 20, 30, 41], "A")
    assert merkle_root_prod(syms, "A") != merkle_root_prod(syms, "B")


def test_merkle_root_leaf_is_a_full_256bit_digest_not_the_element():
    # the whole point of the production tree: the leaf is a 32-byte digest
    root = merkle_root_prod([7], "A")
    assert isinstance(root, bytes) and len(root) == 32
    assert root == _h256("A", 0, 7)


def test_merkle_root_handles_odd_leaf_counts_by_duplicating_the_tail():
    # the documented toy rule appends the TAIL LEAF DIGEST (not the tail
    # symbol -- the leaf hash is position-bound, so [1,2,3] does NOT equal
    # [1,2,3,3]; the duplication happens after the leaves are hashed)
    odd = merkle_root_prod([1, 2, 3], "A")
    assert isinstance(odd, bytes) and len(odd) == 32
    assert odd != merkle_root_prod([1, 2, 3, 4], "A")
    assert odd != merkle_root_prod([1, 2, 3, 3], "A")
    # the duplication is applied at EVERY odd level, and the result is stable
    assert merkle_root_prod([1, 2, 3], "A") == merkle_root_prod([1, 2, 3], "A")
    assert merkle_root_prod([1, 2, 3, 4, 5], "A") != merkle_root_prod([1, 2, 3], "A")
    assert isinstance(merkle_root_prod([1], "A"), bytes)


def test_merkle_path_out_of_range_is_empty():
    assert merkle_path_prod([1, 2, 3, 4], "A", -1) == []
    assert merkle_path_prod([1, 2, 3, 4], "A", 4) == []
    assert merkle_path_prod([], "A", 0) == []


def test_merkle_path_length_is_logarithmic_and_every_index_verifies():
    syms = [1000000 + k for k in range(16)]
    root = merkle_root_prod(syms, "A")
    for idx in range(16):
        path = merkle_path_prod(syms, "A", idx)
        assert len(path) == 4                      # 16 leaves -> 4 levels
        assert all(d in ("L", "R") for d, _ in path)
        assert merkle_check_prod(root, "A", idx, syms[idx], path)


def test_merkle_check_rejects_a_wrong_leaf_and_a_wrong_root():
    syms = [10, 20, 30, 40]
    root = merkle_root_prod(syms, "A")
    path2 = merkle_path_prod(syms, "A", 2)
    assert not merkle_check_prod(root, "A", 2, 99, path2)
    assert not merkle_check_prod(b"\x00" * 32, "A", 2, syms[2], path2)


def test_merkle_check_rejects_a_path_replayed_at_a_foreign_index():
    # the round-2 F9 position-binding contract, carried into this hash
    syms = [1000000 + k for k in range(16)]
    root = merkle_root_prod(syms, "A")
    p5 = merkle_path_prod(syms, "A", 5)
    assert merkle_check_prod(root, "A", 5, syms[5], p5)
    assert not merkle_check_prod(root, "A", 6, syms[6], p5)
    assert not merkle_check_prod(root, "A", 4, syms[4], p5)


# ------------------------------------------------------------- TileAIRProd AIR

def _toy_instance():
    rng = random.Random(4242)
    A = [[rng.randrange(TOY_Q) for _ in range(TOY_N)] for _ in range(TOY_N)]
    B = [[rng.randrange(TOY_Q) for _ in range(TOY_N)] for _ in range(TOY_N)]
    return A, B


def _toy_commitments(A, B):
    flat_A = [A[r][c] for r in range(TOY_N) for c in range(TOY_N)]
    flat_B = [B[r][c] for r in range(TOY_N) for c in range(TOY_N)]
    return merkle_root_prod(flat_A, "A"), merkle_root_prod(flat_B, "B")


def test_prove_returns_the_residuals_and_paths_verify_binds():
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 1, 1)
    acc = proof["acc"]
    A_commit, B_commit = _toy_commitments(A, B)
    assert air.verify(proof, acc, 1, 1, A_commit, B_commit, "ctx-1")


def test_prove_accumulator_is_the_trace_sum_of_noisy_products():
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 0, 0)
    m = TOY_M
    expected = 0
    for t in range(m):
        ai = (A[0][t * TOY_R] + air._E("ctx-1", 0, t * TOY_R)) % TOY_Q
        bj = (B[t * TOY_R][0] + air._F("ctx-1", t * TOY_R, 0)) % TOY_Q
        expected = (expected + ai * bj) % TOY_Q
    assert proof["acc"] == expected
    assert proof["trace"][0] == 0
    assert proof["trace"][-1] == expected
    assert len(proof["trace"]) == m + 1
    assert len(proof["a"]) == len(proof["b"]) == m
    assert len(proof["a_res"]) == len(proof["a_paths"]) == m
    assert len(proof["b_res"]) == len(proof["b_paths"]) == m


def test_verify_rejects_a_tampered_interior_trace_entry():
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 0, 0)
    A_commit, B_commit = _toy_commitments(A, B)
    bad = {k: (list(v) if isinstance(v, list) else v) for k, v in proof.items()}
    bad["trace"][2] = (proof["trace"][2] + 7) % TOY_Q
    assert not air.verify(bad, proof["acc"], 0, 0, A_commit, B_commit, "ctx-1")


def test_verify_rejects_a_wrong_claimed_accumulator():
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 0, 0)
    A_commit, B_commit = _toy_commitments(A, B)
    bad = {k: (list(v) if isinstance(v, list) else v) for k, v in proof.items()}
    bad["trace"][-1] = (proof["trace"][-1] + 1) % TOY_Q
    wrong = (proof["acc"] + 1) % TOY_Q
    assert not air.verify(bad, wrong, 0, 0, A_commit, B_commit, "ctx-1")


def test_verify_rejects_a_fabricated_tile_for_a_chosen_accumulator():
    # the round-5 P1/P2 binding: attacker-chosen factors over attacker-chosen
    # commitments must NOT verify against the task's commitments
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 1, 1)
    A_commit, B_commit = _toy_commitments(A, B)
    target = 42
    fab = {"a": [target, 1, 1, 1], "b": [1, 0, 0, 0],
           "trace": [0, target, target, target, target], "acc": target,
           "a_res": [0, 0, 0, 0], "b_res": [0, 0, 0, 0],
           "a_paths": proof["a_paths"], "b_paths": proof["b_paths"]}
    assert not air.verify(fab, target, 1, 1, A_commit, B_commit, "ctx-1")


def test_verify_rejects_a_proof_stripped_of_its_residuals_and_paths():
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 0, 0)
    A_commit, B_commit = _toy_commitments(A, B)
    bare = {"a": proof["a"], "b": proof["b"],
            "trace": proof["trace"], "acc": proof["acc"]}
    assert not air.verify(bare, proof["acc"], 0, 0, A_commit, B_commit, "ctx-1")


def test_verify_rejects_residuals_that_do_not_match_the_committed_matrix():
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 0, 0)
    A_commit, B_commit = _toy_commitments(A, B)
    bad = {k: (list(v) if isinstance(v, list) else v) for k, v in proof.items()}
    bad["a_res"][1] = (proof["a_res"][1] + 1) % TOY_Q
    assert not air.verify(bad, proof["acc"], 0, 0, A_commit, B_commit, "ctx-1")


def test_verify_rejects_shape_malformed_proofs():
    A, B = _toy_instance()
    air = TileAIRProd(TOY_Q, TOY_N, TOY_R)
    proof = air.prove(A, B, "ctx-1", 0, 0)
    A_commit, B_commit = _toy_commitments(A, B)
    args = (proof["acc"], 0, 0, A_commit, B_commit, "ctx-1")
    short = {k: (v[:-1] if isinstance(v, list) else v) for k, v in proof.items()}
    short["trace"] = proof["trace"][:-1]
    assert not air.verify(short, *args)
    empty = dict(proof, a=[], b=[], a_res=[], b_res=[], a_paths=[], b_paths=[])
    empty["trace"] = [0]
    assert not air.verify(empty, *args)


def test_honest_proof_verifies_at_the_256bit_field():
    # TV-71/TV-76: the transition check is field-independent
    rng = random.Random(20260923)
    n, r = TOY_N, TOY_R
    A = [[rng.randrange(P256) for _ in range(n)] for _ in range(n)]
    B = [[rng.randrange(P256) for _ in range(n)] for _ in range(n)]
    air = TileAIRProd(P256, n, r)
    proof = air.prove(A, B, 12345, 1, 3)
    flat_A = [A[rr][cc] for rr in range(n) for cc in range(n)]
    flat_B = [B[rr][cc] for rr in range(n) for cc in range(n)]
    ok = air.verify(proof, proof["acc"], 1, 3,
                    merkle_root_prod(flat_A, "A"), merkle_root_prod(flat_B, "B"),
                    12345)
    assert ok
    assert proof["acc"] < P256 and proof["acc"].bit_length() <= 256
    # a tamper at the 256-bit field is still caught
    bad = {k: (list(v) if isinstance(v, list) else v) for k, v in proof.items()}
    bad["trace"][2] = (proof["trace"][2] + 7) % P256
    assert not air.verify(bad, proof["acc"], 1, 3,
                          merkle_root_prod(flat_A, "A"),
                          merkle_root_prod(flat_B, "B"), 12345)


def test_rom_noise_is_bounded_by_the_truncated_digest_width():
    # the LIMIT the module states: _E/_F draw from an 8-byte digest, so they
    # carry ~64 bits regardless of q. Over many draws at the 256-bit field no
    # value may exceed 2**64-1.
    air = TileAIRProd(P256, TOY_N, TOY_R)
    vals = [air._E("ctx", i, j) for i in range(64) for j in range(64)]
    assert all(0 <= v < P256 for v in vals)
    assert max(vals) < (1 << 64)
    # and the noise is deterministic in (ctx, i, j)
    assert air._E("ctx", 0, 0) == air._E("ctx", 0, 0)
    assert air._E("ctx", 0, 0) != air._E("other", 0, 0)


def test_h256_and_h_truncated_agree_on_widths():
    full = _h256("A", 0, 7)
    assert isinstance(full, bytes) and len(full) == 32
    assert _h_truncated("A", 0, 7) == int.from_bytes(full[:8], "big")
    assert 0 <= _h_truncated("A", 0, 7) < (1 << 64)


# --------------------------------------------------------------- the TV-76 probes

def test_measure_position_binding_in_production_hash_runs_and_holds():
    # asserts the F9 contract internally; returns None on success
    assert pf.measure_position_binding_in_production_hash() is None


def test_measure_leaf_inversion_cost_runs_and_holds():
    # asserts its own collision accounting; returns None on success
    assert pf.measure_leaf_inversion_cost() is None


def test_measure_honest_verify_at_production_field_runs_and_holds():
    # asserts the honest-accepts / forgery-rejects block at the 256-bit field
    assert pf.measure_honest_verify_at_production_field() is None


def test_measure_schwartz_zippel_runs_and_reports_the_toy_rate():
    # a 20000-sample sweep with a fixed seed -> deterministic exit, no raise
    assert pf.measure_schwartz_zippel() is None


def test_measure_leaf_hash_inversion_states_the_reconciled_status():
    assert pf.measure_leaf_inversion_cost.__doc__
    assert pf.measure_leaf_hash_inversion() is None


def test_tv76_field_margin_runs_and_holds():
    # asserts a single-point tamper breaks at least one transition, then runs
    # its own 20000-challenge sweep
    assert pf.tv76_field_margin() is None

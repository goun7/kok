"""Tests for g_layer_tests_en.py: the G layer's MatMul proof-of-work kernel.

The G layer is the security budget: a Komargodski-Weinstein matrix-
multiplication certificate whose hardness is structural, because the noise
matrices come from the public ctx and a miner cannot shop for a friendly
instance. This is the property plain Freivalds lacks (the A=0 attack) and
the reason KW was chosen.

Covers (stdlib-only, pure functions, no external calls):
  * H — the domain-separated hash the certificate and the ctx are built from.
  * dense / sparse_zero_rows / permutation / zeros / ident — the input
    classes the prescribed-hardness claim is measured across.
  * cost_of_prove / cost_is_input_independent — the measured input-
    independence of the per-attempt cost.
  * KWKernel.prove / verify — the certificate and its verifier, including
    the replay (TV-1) and forgery rejections.
"""

import pytest

import g_layer_tests_en as gl
from g_layer_tests_en import (
    H,
    KWKernel,
    attempts_to_success,
    cost_is_input_independent,
    cost_of_prove,
    dense,
    ident,
    permutation,
    sparse_zero_rows,
    zeros,
)

CTX = 777
TARGET = 1 << 4  # loose enough to grind in a few nonces; the binding is under test


def _toy():
    return dense(8), dense(8, seed=9)


def _mine(kernel=None, target=TARGET, ctx=CTX):
    """Grind an honest certificate over the toy matrices."""
    k = kernel or KWKernel()
    a, b = _toy()
    nonce = 0
    while True:
        nonce += 1
        cert = k.prove(a, b, ctx, nonce, target)
        if cert is not None:
            return cert, a, b, nonce


# ---------------------------------------------------------------------------
# H — the domain-separated hash
# ---------------------------------------------------------------------------


def test_h_returns_an_int():
    assert isinstance(H("tile", 1, 2), int)


def test_h_is_deterministic():
    assert H("tile", 1, 2, 3) == H("tile", 1, 2, 3)


def test_h_distinguishes_inputs():
    assert H("tile", 1, 2, 3) != H("tile", 1, 2, 4)
    assert H("E", 1, 2) != H("F", 1, 2), "the domain label must separate"


def test_h_joins_parts_with_a_pipe():
    assert H("a", "b") != H("ab")


# ---------------------------------------------------------------------------
# the input classes the prescribed-hardness claim is measured across
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [2, 4, 8])
def test_dense_is_square_and_in_field(n):
    m = dense(n)
    assert len(m) == n
    assert all(len(r) == n for r in m)
    assert all(0 <= v < 97 for r in m for v in r)


def test_dense_is_deterministic_for_a_fixed_seed():
    assert dense(8) == dense(8)


def test_dense_different_seeds_give_different_matrices():
    assert dense(8) != dense(8, seed=9)


@pytest.mark.parametrize("n", [2, 4, 8])
def test_sparse_zero_rows_is_square_with_half_the_columns_zero(n):
    m = sparse_zero_rows(n)
    assert len(m) == n and all(len(r) == n for r in m)
    for i in range(n):
        for j in range(n // 2):
            assert m[i][j] == 0
    # the other half is nonzero, so this really is a sparse input class
    assert any(m[i][j] != 0 for i in range(n) for j in range(n // 2, n))


@pytest.mark.parametrize("n", [2, 4, 8])
def test_permutation_is_a_permutation_matrix(n):
    m = permutation(n)
    assert len(m) == n and all(len(r) == n for r in m)
    # exactly one 1 per row and per column, everything else zero
    for i in range(n):
        assert sum(m[i]) == 1
    for j in range(n):
        assert sum(m[i][j] for i in range(n)) == 1
    assert all(v in (0, 1) for r in m for v in r)


@pytest.mark.parametrize("n", [2, 4, 8])
def test_zeros_and_ident_have_the_shapes_they_claim(n):
    z = zeros(n)
    assert all(v == 0 for r in z for v in r)
    I = ident(n)
    for i in range(n):
        for j in range(n):
            assert I[i][j] == (1 if i == j else 0)


# ---------------------------------------------------------------------------
# cost_of_prove — the measured per-attempt cost
# ---------------------------------------------------------------------------


def test_the_cost_does_not_depend_on_the_matrix_contents():
    # PRESCRIBED HARDNESS, the structural half: every input class costs the
    # same per attempt, because the noise is derived from the public ctx and
    # never from the matrices. This is what the A=0 attack on plain Freivalds
    # would break.
    b = dense(8, seed=9)
    classes = {
        "dense": dense(8),
        "sparse": sparse_zero_rows(8),
        "permutation": permutation(8),
        "zeros": zeros(8),
        "identity": ident(8),
    }
    costs = {name: cost_of_prove(a, b, CTX, 1 << 6) for name, a in classes.items()}
    assert len(set(costs.values())) == 1, costs


def test_the_cost_does_depend_on_the_shape():
    # the other half of the same claim: cost is a function of the SHAPE alone,
    # so two shapes must differ (the old test compared a value to itself)
    big = cost_of_prove(dense(8), dense(8, seed=9), CTX, 1 << 6)
    small = cost_of_prove(dense(4), dense(4, seed=9), CTX, 1 << 6)
    assert big != small
    assert big > small


def test_cost_is_input_independent_reports_a_single_cost():
    ok, costs = cost_is_input_independent(1, 2, trials=5)
    assert ok
    assert len(costs) == 1


def test_the_cost_matches_the_kernel_formula():
    # 2n^2 noise additions + m^3 tile products, with m = n/r and r=2
    k = KWKernel()
    n = 8
    m = n // k.r
    want = 2 * n * n + m * m * m * (2 * k.r * k.r + 1)
    assert cost_of_prove(dense(8), dense(8, seed=9), CTX, 1 << 6) == want


# ---------------------------------------------------------------------------
# KWKernel.prove / verify — the certificate
# ---------------------------------------------------------------------------


def test_an_honest_certificate_verifies():
    cert, a, b, nonce = _mine()
    assert KWKernel().verify(cert, a, b, CTX, nonce, TARGET)


def test_the_certificate_names_its_tile_and_width():
    cert, _, _, _ = _mine()
    assert set(cert.keys()) == {"tile", "m"}
    i, j, val = cert["tile"]
    assert isinstance(i, int) and isinstance(j, int) and isinstance(val, int)
    assert cert["m"] == 4  # n=8, r=2 -> m=4


def test_prove_returns_none_when_no_tile_clears_the_target():
    # an unreachable target never produces a certificate
    k = KWKernel()
    a, b = _toy()
    assert k.prove(a, b, CTX, 1, 1 << 64) is None


def test_a_certificate_replayed_under_another_ctx_is_rejected():
    # TV-1: the tile is bound to the ctx through the noise pair
    cert, a, b, nonce = _mine()
    assert not KWKernel().verify(cert, a, b, CTX + 1, nonce, TARGET)


def test_a_forged_tile_value_is_rejected():
    # the verifier recomputes the claimed tile at its coordinates, so a value
    # the matrices do not produce fails (round-3 finding [10])
    cert, a, b, nonce = _mine()
    i, j, val = cert["tile"]
    forged = {"tile": (i, j, (val + 1) % 97), "m": cert["m"]}
    assert not KWKernel().verify(forged, a, b, CTX, nonce, TARGET)


def test_the_tile_width_is_derived_from_the_input_not_the_kernel_constant():
    # THE [11]-[14] FIX, driven at the size it broke at. verify() used the
    # KERNEL's constant self.n while prove() derives n from the input, so a
    # 6x6 proof made verify index the matrix at row 8 and raise IndexError.
    # The size now comes from the input on both sides, so a kernel built with
    # the default n=8 mines and verifies a 6x6 certificate (m = 6//2 = 3).
    k = KWKernel()  # self.n = 8 by default
    a = dense(6)
    b = dense(6, seed=9)
    nonce = 0
    while True:
        nonce += 1
        cert = k.prove(a, b, CTX, nonce, TARGET)
        if cert is not None:
            break
    assert cert["m"] == 3
    assert k.verify(cert, a, b, CTX, nonce, TARGET)


def test_a_tile_out_of_range_for_the_input_is_rejected_not_indexed():
    # the bounds gate that the input-derived width makes meaningful
    cert, a, b, nonce = _mine()
    forged = {"tile": (cert["m"], cert["m"], 5), "m": cert["m"]}
    assert not KWKernel().verify(forged, a, b, CTX, nonce, TARGET)


def test_an_out_of_range_tile_is_rejected_not_indexed():
    # a tile outside the grid must reject rather than raise IndexError
    cert, a, b, nonce = _mine()
    forged = {"tile": (99, 99, 5), "m": cert["m"]}
    assert not KWKernel().verify(forged, a, b, CTX, nonce, TARGET)


def test_a_none_certificate_is_rejected():
    a, b = _toy()
    assert KWKernel().verify(None, a, b, CTX, 1, TARGET) is False


def test_a_certificate_whose_hash_does_not_clear_the_target_is_rejected():
    # the difficulty check is separate from the tile recomputation: the same
    # honest tile value, verified under a nonce that was never ground, must
    # fail the hash-under-target test. The wrong nonce is SEARCHED for rather
    # than guessed, so the assertion is deterministic rather than 15/16 lucky.
    k = KWKernel()
    a, b = _toy()
    cert, _, _, nonce = _mine()
    i, j, val = cert["tile"]
    wrong_nonce = None
    for cand in range(nonce + 1, nonce + 1000):
        if H("tile", CTX, cand, i, j, val) % TARGET != 0:
            wrong_nonce = cand
            break
    assert wrong_nonce is not None, "a nonce that fails the target must exist"
    not_mined = {"tile": (i, j, val), "m": cert["m"]}
    assert k.verify(not_mined, a, b, CTX, nonce, TARGET)
    assert not k.verify(not_mined, a, b, CTX, wrong_nonce, TARGET)


def test_verify_is_deterministic():
    cert, a, b, nonce = _mine()
    k = KWKernel()
    first = k.verify(cert, a, b, CTX, nonce, TARGET)
    for _ in range(20):
        assert k.verify(cert, a, b, CTX, nonce, TARGET) == first


def test_the_noise_is_a_pure_function_of_the_ctx_and_size():
    # the security model: E and F come from the public ctx, not the matrices,
    # so a miner cannot choose a friendly instance
    k = KWKernel()
    e1, f1 = k._noise(20260919, 8)
    e2, f2 = k._noise(20260919, 8)
    assert e1 == e2 and f1 == f2
    # a different ctx gives different noise
    e3, f3 = k._noise(20260920, 8)
    assert e1 != e3 and f1 != f3
    # the noise is in the field
    assert all(0 <= v < 97 for r in e1 for v in r)
    assert all(0 <= v < 97 for r in f1 for v in r)


def test_attempts_to_success_returns_a_count_per_trial():
    a, b = _toy()
    counts = attempts_to_success(a, b, CTX, 1 << 8, trials=3)
    assert len(counts) == 3
    assert all(c >= 1 for c in counts)

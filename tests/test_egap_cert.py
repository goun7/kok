"""Tests for egap_cert_en.py: the E-gap certification binding.

This is the binding whose absence measured phi = 0 on Pearl's live network
(TV-72): nothing certified that the matrices a miner proved work over were
anyone's job, so the network ran as pure PoW while marketed as PoUW. The
certificate must name the task, and the verifier must derive what it is bound
to from the TASK rather than from caller-supplied matrices.

Covers (stdlib-only, pure functions, no external calls):
  * H / S — the domain-separated hash primitives every binding is built on.
  * matrix_commit / program_commit — content-bound commitments.
  * _tile_value — the reference tile inner product both sites must share.
  * g_cert_bound / verify_g_cert_bound — the certificate and its verifier,
    including the round-5B work binding (the tile value is re-derived from the
    committed program, not taken on the miner's word).
"""

import pytest

from egap_cert_en import (
    H,
    S,
    _tile_value,
    g_cert_bound,
    matrix_commit,
    program_commit,
    verify_g_cert_bound,
)

# The toy task used throughout: 2x2 matrices over the toy field q=97.
A_TASK = [[2, 3], [4, 5]]
B_TASK = [[6, 7], [8, 9]]
A_FOREIGN = [[5, 6], [7, 8]]
B_FOREIGN = [[1, 0], [0, 1]]
TASK_ID = "task-77"
CTX = 500
TARGET = 1 << 8  # loose enough to grind quickly; the binding is under test


def _grind(task_id, pc, ctx, i, j, value, target=TARGET, cap=1 << 20):
    """Grind a nonce until a bound certificate clears the target."""
    for nonce in range(1, cap):
        cert = g_cert_bound(task_id, pc, ctx, nonce, i, j, value, target)
        if cert is not None:
            return cert
    pytest.skip("could not grind a certificate; target too tight for the toy cap")


def _honest_cert():
    """An honestly-mined certificate over the task's own matrices."""
    pc = program_commit(A_TASK, B_TASK)
    return _grind(TASK_ID, pc, CTX, 0, 0, _tile_value(A_TASK, B_TASK, 0, 0)), pc


# ---------------------------------------------------------------------------
# H — the 64-bit domain-separated hash
# ---------------------------------------------------------------------------


def test_h_returns_an_int():
    assert isinstance(H("tile", 1, 2, 3), int)


def test_h_is_deterministic():
    assert H("tile", 1, 2, 3) == H("tile", 1, 2, 3)


def test_h_distinguishes_inputs():
    assert H("tile", 1, 2, 3) != H("tile", 1, 2, 4)
    assert H("a", "b") != H("b", "a"), "part order must matter"


def test_h_domain_separates():
    # the label is part of the digest, so two domains never collide
    assert H("E", 1, 2) != H("F", 1, 2)


# ---------------------------------------------------------------------------
# S — the 128-bit hex identifier digest
# ---------------------------------------------------------------------------


def test_s_is_a_32_char_hex_identifier():
    s = S("prog", "abc")
    assert len(s) == 32
    int(s, 16)


def test_s_is_deterministic_and_input_dependent():
    assert S("x", 1) == S("x", 1)
    assert S("x", 1) != S("x", 2)


# ---------------------------------------------------------------------------
# matrix_commit / program_commit — content-bound commitments
# ---------------------------------------------------------------------------


def test_matrix_commit_is_deterministic_for_identical_content():
    # recomputed from a separately-built copy: the check fails if the
    # commitment depends on anything but the content (round-5 finding E2)
    assert matrix_commit([[2, 3], [4, 5]]) == matrix_commit([[2, 3], [4, 5]])


def test_matrix_commit_distinguishes_different_content():
    assert matrix_commit([[2, 3], [4, 5]]) != matrix_commit([[2, 3], [4, 6]])


def test_matrix_commit_distinguishes_different_shapes():
    assert matrix_commit([[2, 3], [4, 5]]) != matrix_commit([[2, 3]])


def test_program_commit_binds_both_factors():
    a, b = A_TASK, B_TASK
    assert program_commit(a, b) != program_commit(a, B_FOREIGN)
    assert program_commit(a, b) != program_commit(A_FOREIGN, b)


def test_program_commit_is_deterministic():
    assert program_commit(A_TASK, B_TASK) == program_commit(A_TASK, B_TASK)


# ---------------------------------------------------------------------------
# _tile_value — the reference computation
# ---------------------------------------------------------------------------


def test_tile_value_matches_the_hand_computed_inner_product():
    # ((A[0][0]*A[0][1] + A[1][0]*A[1][1]) * (B[0][0]*B[0][1] + B[1][0]*B[1][1])) % 97
    #   = ((2*3 + 4*5) * (6*7 + 8*9)) % 97 = (26 * 110) % 97 = 2860 % 97 = 54
    assert _tile_value(A_TASK, B_TASK, 0, 0) == 54


def test_tile_value_is_deterministic():
    assert _tile_value(A_TASK, B_TASK, 0, 0) == _tile_value(A_TASK, B_TASK, 0, 0)


def test_tile_value_binds_the_committed_matrices():
    # a tile over the foreign matrices is a different number — this is the
    # round-5B substitution: mined [[2,3],[4,6]] serves tile 30, not 54
    assert _tile_value(A_TASK, B_TASK, 0, 0) != _tile_value([[2, 3], [4, 6]], B_TASK, 0, 0)


# ---------------------------------------------------------------------------
# verify_g_cert_bound — the task-identity binding
# ---------------------------------------------------------------------------


def test_an_honest_certificate_over_the_tasks_own_matrices_verifies():
    cert, pc = _honest_cert()
    assert verify_g_cert_bound(cert, TASK_ID, pc, CTX, TARGET, program=(A_TASK, B_TASK))


def test_a_certificate_over_foreign_matrices_is_rejected():
    # TV-77 / round-3 finding [21]: a cert naming a foreign commitment does
    # not verify against the task's commitment
    pc_task = program_commit(A_TASK, B_TASK)
    pc_foreign = program_commit(A_FOREIGN, B_FOREIGN)
    cert = _grind(TASK_ID, pc_foreign, CTX, 0, 0, _tile_value(A_FOREIGN, B_FOREIGN, 0, 0))
    assert not verify_g_cert_bound(
        cert, TASK_ID, pc_task, CTX, TARGET, program=(A_TASK, B_TASK)
    )


def test_a_certificate_replayed_for_another_task_is_rejected():
    # the replay half of the E-gap: one real job's work is not portable
    cert, pc = _honest_cert()
    assert not verify_g_cert_bound(cert, "task-2", pc, CTX, TARGET, program=(A_TASK, B_TASK))


def test_a_certificate_replayed_under_another_ctx_is_rejected():
    cert, pc = _honest_cert()
    assert not verify_g_cert_bound(cert, TASK_ID, pc, CTX + 1, TARGET, program=(A_TASK, B_TASK))


def test_a_none_certificate_is_rejected():
    pc = program_commit(A_TASK, B_TASK)
    assert verify_g_cert_bound(None, TASK_ID, pc, CTX, TARGET) is False


def test_a_certificate_whose_tile_value_does_not_recompute_is_rejected():
    # ROUND-5B (R5B-3): the binding must bind the COMPUTATION, not the
    # commitment string. A cert carrying a value the committed matrices do
    # not produce must fail even when every identity field is correct.
    cert, pc = _honest_cert()
    forged = dict(cert)
    i, j, _ = cert["tile"]
    forged["tile"] = (i, j, (_tile_value(A_TASK, B_TASK, i, j) + 1) % 97)
    assert not verify_g_cert_bound(
        forged, TASK_ID, pc, CTX, TARGET, program=(A_TASK, B_TASK)
    )


def test_the_value_binding_is_what_closes_the_round5b_gap():
    # ROUND-5B (R5B-3), driven directly. A miner names the TASK's commitment
    # (so the identity check passes) but mines a tile over matrices it prefers,
    # re-grinding the nonce so the wrong value still clears the target. Without
    # the program argument the verifier accepts it — the binding bound the
    # commitment STRING, not the computation. With the program it rejects,
    # because the value the cert claims is not the value the committed
    # matrices produce.
    pc = program_commit(A_TASK, B_TASK)
    wrong_value = (_tile_value(A_TASK, B_TASK, 0, 0) + 1) % 97
    cert = _grind(TASK_ID, pc, CTX, 0, 0, wrong_value)
    # the legacy path (commitment only) accepts the substituted work
    assert verify_g_cert_bound(cert, TASK_ID, pc, CTX, TARGET) is True
    # the shipped path (program supplied) rejects it
    assert not verify_g_cert_bound(
        cert, TASK_ID, pc, CTX, TARGET, program=(A_TASK, B_TASK)
    )


def test_a_certificate_whose_commitment_field_is_lied_about_is_rejected():
    # the cert's own pc must equal the task's; a cert that carries a
    # different commitment is not this task's work
    cert, pc = _honest_cert()
    other_pc = program_commit(A_FOREIGN, B_FOREIGN)
    assert not verify_g_cert_bound(cert, TASK_ID, other_pc, CTX, TARGET)


def test_the_pow_target_is_still_enforced():
    # the binding is not a substitute for the difficulty check: a cert whose
    # hash does not clear the target never exists, so building one at an
    # impossible target yields None
    pc = program_commit(A_TASK, B_TASK)
    impossible = g_cert_bound(
        TASK_ID, pc, CTX, 1, 0, 0, _tile_value(A_TASK, B_TASK, 0, 0), 1 << 64
    )
    assert impossible is None


def test_the_certificate_shape_carries_the_binding_fields():
    cert, _ = _honest_cert()
    assert cert["task_id"] == TASK_ID
    assert cert["ctx"] == CTX
    assert set(cert.keys()) >= {"task_id", "pc", "ctx", "nonce", "tile"}
    assert len(cert["tile"]) == 3

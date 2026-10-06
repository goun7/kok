"""The E-gap mechanism (tv72_egap_mechanism_en.py) and the spec-only
re-derivation probes (spec_rederive_en.py).

tv72_egap_mechanism_en had NO test coverage. It is the file that demonstrates
WHY Pearl's phi was zero: without the TV-77 binding a self-consistent
certificate over ANY matrices is accepted, so detectability is 0 by
construction. The tests below cut both arms and the sweep:

  - program_commit_single is content-bound (two matrices differ -> two
    commitments) and equals program_commit(M, M),
  - _mine_tile finds a nonce whose hash meets the target, and returns None
    when no nonce in the budget can (the unminable branch),
  - ARM A (no binding) ACCEPTS a substitution of the commissioned matrices,
  - ARM B (binding) ACCEPTS the honest cert and REJECTS the same substitution,
  - the Arm-A cert re-verified against the task's own commitment is rejected,
  - probe_binding_is_what_makes_cheating_detectable and
    probe_detectability_number both return True,
  - the identical-matrix case is the one Arm B must NOT reject.

spec_rederive_en had its Merkle helpers covered but its four TV-79 probes
were untested; the last two are the large ones and they are driven here:

  - probe_forgery_rejected: an inconsistent fabrication AND a self-consistent
    fabrication over foreign commitments are both rejected, the honest proof
    still verifies,
  - probe_pinned_values_present: the spec-derived H() equals the reference's
    H() and equals the inlined SHA-256[:8] formula; the reference's 8-byte
    Merkle root agrees with the spec derivation's truncated root.

The spec probes load the reference by a RELATIVE path ("f0b_air_proto.py"),
so those tests chdir to the KOK root first; everything else is stdlib-only
arithmetic with inputs built here. No external calls.
"""

import os

import pytest

import tv72_egap_mechanism_en as tv72
from egap_cert_en import H, _tile_value, matrix_commit, program_commit, \
    verify_g_cert_bound
from tv72_egap_mechanism_en import (TARGET, TASK_ID, _mine_tile,
                                    arm_a_without_binding, arm_b_with_binding,
                                    program_commit_single)

KOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


COMMISSIONED = [[2, 3], [4, 5]]
MINED = [[11, 7], [13, 17]]
CTX = "epoch-pearl-test"


# ------------------------------------------------------------- commitments

def test_program_commit_single_equals_program_commit_of_the_pair():
    assert program_commit_single(COMMISSIONED) == program_commit(COMMISSIONED,
                                                                COMMISSIONED)


def test_program_commit_single_is_content_bound():
    a = program_commit_single([[2, 3], [4, 5]])
    b = program_commit_single([[2, 3], [4, 6]])
    assert a != b
    assert program_commit_single(MINED) != a
    # and it differs from the two-factor commitment of two different matrices
    assert a != program_commit([[2, 3], [4, 5]], MINED)


def test_program_commit_single_is_deterministic():
    assert program_commit_single(COMMISSIONED) == program_commit_single(
        [[2, 3], [4, 5]])


# ------------------------------------------------------------------ the miner

def test_mine_tile_finds_a_nonce_meeting_the_target():
    found = _mine_tile(COMMISSIONED, CTX, TARGET)
    assert found is not None
    nonce, i, j, value = found
    pc = program_commit_single(COMMISSIONED)
    assert H("tile", TASK_ID, pc, CTX, nonce, i, j, value) % TARGET == 0
    # the tile value is the reference computation over the mined matrices
    assert value == _tile_value(COMMISSIONED, COMMISSIONED, i, j)


def test_mine_tile_returns_none_when_the_budget_is_exhausted():
    # a target no 8-byte digest can reach, with a tiny nonce budget
    assert _mine_tile(COMMISSIONED, CTX, 1 << 200, max_nonce=3) is None


def test_mine_tile_uses_the_supplied_commitment_string():
    own = program_commit_single(COMMISSIONED)
    foreign = matrix_commit(MINED)
    found = _mine_tile(MINED, CTX, TARGET, commit=foreign)
    assert found is not None
    nonce, i, j, value = found
    assert H("tile", TASK_ID, foreign, CTX, nonce, i, j, value) % TARGET == 0
    # the same nonce does NOT meet the target under the other commitment
    assert H("tile", TASK_ID, own, CTX, nonce, i, j, value) % TARGET != 0


# ---------------------------------------------------------- the two arms

def test_arm_a_accepts_the_substitution_without_the_binding():
    # pre-TV-77 rule: PoW target only, so a cert over the MINER's matrices
    # over an unrelated pair is accepted
    cert, accepted = arm_a_without_binding(COMMISSIONED, MINED, CTX)
    assert cert is not None
    assert accepted is True
    assert cert["pc"] == matrix_commit(MINED)
    assert cert["pc"] != program_commit_single(COMMISSIONED)


def test_arm_a_accepts_the_commissioned_pair_too():
    cert, accepted = arm_a_without_binding(COMMISSIONED, COMMISSIONED, CTX)
    assert cert is not None and accepted is True


def test_arm_b_accepts_the_honest_commissioned_cert():
    cert, ok = arm_b_with_binding(COMMISSIONED, CTX)
    assert cert is not None
    assert ok is True
    assert cert["pc"] == program_commit_single(COMMISSIONED)


def test_arm_b_rejects_a_cert_mined_over_foreign_matrices():
    # same task commitment named, tile mined over the miner's matrices: the
    # value does not correspond to the committed program, so it is rejected
    cert, ok = arm_b_with_binding(COMMISSIONED, CTX, mined=MINED)
    assert cert is not None
    assert ok is False
    # the cert is still internally target-consistent -- the rejection comes
    # from the binding, not from a broken PoW
    i, j, value = cert["tile"]
    assert H("tile", TASK_ID, cert["pc"], CTX, cert["nonce"], i, j,
             value) % TARGET == 0
    assert value != _tile_value(COMMISSIONED, COMMISSIONED, i, j)


def test_the_arm_a_cert_rejected_against_the_tasks_commitment():
    cert_a, _ = arm_a_without_binding(COMMISSIONED, MINED, CTX)
    required_pc = program_commit_single(COMMISSIONED)
    assert not verify_g_cert_bound(cert_a, TASK_ID, required_pc, CTX, TARGET)


def test_verify_g_cert_bound_rejects_a_wrong_task_ctx_or_commitment():
    cert, _ = arm_b_with_binding(COMMISSIONED, CTX)
    required_pc = program_commit_single(COMMISSIONED)
    assert verify_g_cert_bound(cert, TASK_ID, required_pc, CTX, TARGET)
    assert not verify_g_cert_bound(cert, "other-task", required_pc, CTX, TARGET)
    assert not verify_g_cert_bound(cert, TASK_ID, matrix_commit(MINED), CTX,
                                   TARGET)
    assert not verify_g_cert_bound(cert, TASK_ID, required_pc, "other-ctx",
                                   TARGET)
    assert not verify_g_cert_bound(None, TASK_ID, required_pc, CTX, TARGET)


# ------------------------------------------------------------- the two probes

def test_probe_binding_is_what_makes_cheating_detectable_is_true():
    assert tv72.probe_binding_is_what_makes_cheating_detectable() is True


def test_probe_detectability_number_is_true():
    # arm A accepts every substitution (detectability 0), arm B rejects every
    # substituted matrix and accepts the identical one
    assert tv72.probe_detectability_number() is True


def test_detectability_is_zero_by_construction_without_the_binding():
    # the mechanism claim, driven directly: across several foreign matrices
    # arm A accepts all of them and the task's binding rejects all of them
    subs = [[[11, 7], [13, 17]], [[1, 0], [0, 1]], [[5, 4], [3, 2]],
            [[2, 3], [4, 6]]]
    required_pc = program_commit_single(COMMISSIONED)
    for m in subs:
        cert_a, ok_a = arm_a_without_binding(COMMISSIONED, m, CTX)
        assert cert_a is not None and ok_a is True
        assert not verify_g_cert_bound(cert_a, TASK_ID, required_pc, CTX,
                                       TARGET)


# ------------------------------------------------- spec_rederive_en TV-79 probes

@pytest.fixture
def at_kok_root(monkeypatch):
    monkeypatch.chdir(KOK_ROOT)
    return None


def test_probe_index_binding_rejects_a_foreign_path(at_kok_root):
    import spec_rederive_en as sr
    assert sr.probe_index_binding() is True


def test_probe_honest_agrees_both_directions(at_kok_root):
    import spec_rederive_en as sr
    assert sr.probe_honest_agrees() is True


def test_probe_forgery_rejected_both_shapes(at_kok_root):
    # the 62-line untested probe: an inconsistent fabrication AND a
    # self-consistent one over foreign commitments are both rejected
    import spec_rederive_en as sr
    assert sr.probe_forgery_rejected() is True


def test_probe_pinned_values_present_match_the_reference(at_kok_root):
    # the 53-line untested probe: spec-derived H == reference H == the
    # inlined SHA-256[:8], and the 8-byte roots agree
    import spec_rederive_en as sr
    assert sr.probe_pinned_values_present() is True

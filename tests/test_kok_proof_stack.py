"""Tests for the KOK proof stack: FRI recursion, the AIR layers, and the
PoUW economic model.

Three prototype modules back the Rust proof crates (kok-proof, kok-fri) and
the PoUM economics:

  * f0b_fri_en.py -- FRI's recursive degree reduction: the fold halves the
    degree in u = x^2 space, the fold's degree bound is enforced (an imposter
    agreeing on every quadratic residue is rejected), a Fiat-Shamir challenge
    the prover cannot choose, and a transcript must terminate in a constant.
  * f0b_air_proto.py -- the AIR for one MatMul tile and its four layers:
    the constraint check (TV-40), Merkle-sampled verification (TV-41),
    low-degree testing via the quotient polynomial (TV-42), masking (TV-43)
    and the Schwartz-Zippel-blinded construction with Merkle-verified pad
    openings (TV-66), plus the degree-bound regression guard (TV-83).
  * fp8_noise_proto_en.py + pass_sim_en.py -- the PoUM noise parameters
    (TV-30's grinding measurement) and the Pass equilibrium solver whose
    regime map and input consistency the security economics rest on.

Covers (stdlib-only, pure function logic, no external calls).
"""

import random

import pytest

import f0b_air_proto as air
import f0b_fri_en as fri
import fp8_noise_proto_en as fp8
import pass_sim_en as ps
from f0b_air_proto import (
    FriTileAIR,
    MerkleTileAIR,
    SzZkTileAIR,
    TileAIR,
    ZkTileAIR,
    _merkle_check,
    _merkle_open,
    _merkle_root,
)
from f0b_fri_en import FriRecursive, _deg, _eval, _interpolate

Q = 97


# ===========================================================================
# FRI: the recursive degree reduction
# ===========================================================================
def test_eval_horner_matches_direct_evaluation():
    p = [3, 5, 7, 11]          # 11x^3 + 7x^2 + 5x + 3 over F_97
    for x in range(Q):
        want = (11 * x**3 + 7 * x**2 + 5 * x + 3) % Q
        assert _eval(p, x, Q) == want


def test_deg_strips_trailing_zero_coefficients():
    assert _deg([1, 2, 3, 0, 0]) == 2
    assert _deg([0, 0, 0]) == 0
    assert _deg([5]) == 0


def test_interpolate_round_trips_through_its_points():
    pts = [(x, (x * x + 3 * x + 7) % Q) for x in range(5)]
    p = _interpolate(pts, Q)
    for x, y in pts:
        assert _eval(p, x, Q) == y


def test_interpolate_recovers_a_known_polynomial():
    known = [7, 2, 9, 4]       # degree 3
    pts = [(x, _eval(known, x, Q)) for x in range(4)]
    got = _interpolate(pts, Q)
    for x in range(Q):
        assert _eval(got, x, Q) == _eval(known, x, Q)


def test_interpolate_is_deterministic():
    pts = [(x, (x**3 + 2) % Q) for x in range(8)]
    assert _interpolate(pts, Q) == _interpolate(pts, Q)


def test_fold_halves_the_degree():
    fri97 = FriRecursive(Q)
    P = _interpolate([(t, (t * t + 3 * t + 7) % Q) for t in range(5)], Q)
    alpha = fri97._challenge(P)
    F = fri97.fold(P, alpha)
    assert _deg(P) == 2
    assert _deg(F) == 1                       # floor(2/2)


def test_fold_satisfies_the_fri_fold_relation():
    fri97 = FriRecursive(Q)
    P = _interpolate([(t, (t * t * t + 2) % Q) for t in range(8)], Q)
    alpha = fri97._challenge(P)
    F = fri97.fold(P, alpha)
    assert fri97.verify_round(P, alpha, F) is True


def test_fold_raises_when_the_field_is_too_small():
    """A degree-6 fold needs 4 distinct squares; q=5 supplies only 2."""
    tiny = FriRecursive(5)
    with pytest.raises(ValueError, match="field too small"):
        tiny.fold([1, 2, 3, 4, 5, 6, 7], 3)


def test_challenge_is_deterministic_and_nonzero():
    fri97 = FriRecursive(Q)
    P = [1, 2, 3, 7]
    a1 = fri97._challenge(P)
    a2 = fri97._challenge(P)
    assert a1 == a2
    assert 1 <= a1 < Q                        # never 0: the odd part must survive
    assert fri97._challenge(P) != fri97._challenge([1, 2, 3, 8])


def test_challenge_depends_on_every_coefficient():
    fri97 = FriRecursive(Q)
    P = [1, 2, 3, 7]
    assert fri97._challenge(P) != fri97._challenge([1, 2, 3, 8])


def test_recursive_prove_halves_the_degree_each_round():
    fri97 = FriRecursive(Q)
    P = _interpolate([(t, (t * t * t + 2) % Q) for t in range(8)], Q)
    tr, alphas = fri97.recursive_prove(P, 3, random.Random(11))
    degs = [_deg(p) for p in tr]
    assert degs == [3, 1, 0, 0]               # each round halves, rounded down
    assert len(alphas) == 3


def test_verify_round_rejects_a_tampered_fold():
    fri97 = FriRecursive(Q)
    P = _interpolate([(t, (t * t + 3 * t + 7) % Q) for t in range(5)], Q)
    alpha = fri97._challenge(P)
    F = fri97.fold(P, alpha)
    bad = list(F)
    bad[0] = (bad[0] + 1) % Q
    assert fri97.verify_round(P, alpha, F) is True
    assert fri97.verify_round(P, alpha, bad) is False


def test_verify_round_rejects_a_high_degree_imposter():
    """F' = F + c*V agrees on every residue but has degree (q-1)/2."""
    fri97 = FriRecursive(Q)
    P = _interpolate([(t, (t * t + 3) % Q) for t in range(5)], Q)
    alpha = fri97._challenge(P)
    F = fri97.fold(P, alpha)
    residues, seen = [], set()
    for x in range(1, Q):
        u = (x * x) % Q
        if u not in seen:
            seen.add(u)
            residues.append(u)
    V = [1]
    for u in residues:                        # the vanishing polynomial V(u)
        nV = [0] * (len(V) + 1)
        for k in range(len(V)):
            nV[k] = (nV[k] - (u * V[k])) % Q
            nV[k + 1] = (nV[k + 1] + V[k]) % Q
        V = nV
    imposter = [(F[k] + V[k]) % Q if k < len(F) else (V[k] % Q)
                for k in range(len(V))]
    assert _deg(imposter) > _deg(P) // 2
    assert fri97.verify_round(P, alpha, imposter) is False


def test_verify_transcript_accepts_an_honest_transcript():
    fri97 = FriRecursive(Q)
    P = _interpolate([(t, (t * t + 3 * t + 7) % Q) for t in range(5)], Q)
    tr, alphas = fri97.recursive_prove(P, 3, random.Random(2026))
    assert fri97.verify_transcript(tr, alphas) is True
    # every round verifies on its own as well
    for r in range(len(tr) - 1):
        assert fri97.verify_round(tr[r], alphas[r], tr[r + 1]) is True


def test_verify_transcript_rejects_a_non_constant_terminal():
    fri97 = FriRecursive(Q)
    P = _interpolate([(t, (t * t + 3 * t + 7) % Q) for t in range(5)], Q)
    tr, alphas = fri97.recursive_prove(P, 3, random.Random(23))
    nonconst = list(tr[-1]) + [5, 9]
    assert fri97.verify_transcript(tr[:-1] + [nonconst], alphas) is False


def test_probe_honest_survives_all_rounds():
    assert fri.probe_honest_survives_all_rounds() is True


def test_probe_tampered_fails():
    assert fri.probe_tampered_fails() is True


def test_probe_rounds_halve_the_degree():
    assert fri.probe_rounds_halve_the_degree() is True


def test_probe_degree_imposter_rejected():
    assert fri.probe_degree_imposter_rejected() is True


def test_measure_forgery_survival_vs_rounds_returns_a_measurement():
    """The soundness measurement the header retracts a claim on; it reports."""
    assert fri.measure_forgery_survival_vs_rounds() is True


# ===========================================================================
# The AIR layers
# ===========================================================================
@pytest.fixture(scope="module")
def tile():
    """One MatMul tile: inputs, ROM noise, the honest accumulator, commitments."""
    rnd = random.Random(606)
    q, r, n = Q, 2, 8
    ctx = 31337
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    E = [[air.H("E", ctx, a, b) % q for b in range(n)] for a in range(n)]
    F = [[air.H("F", ctx, a, b) % q for b in range(n)] for a in range(n)]
    i, j = 0, 3
    acc = 0
    for l in range(n // r):
        acc = (acc + (A[i * r][l * r] + E[i * r][l * r])
               * (B[l * r][j * r] + F[l * r][j * r])) % q
    flat_A = [c for row in A for c in row]
    flat_B = [c for row in B for c in row]
    return {
        "q": q, "r": r, "n": n, "ctx": ctx,
        "A": A, "B": B, "E": E, "F": F, "i": i, "j": j, "acc": acc,
        "A_commit": _merkle_root(flat_A),
        "B_commit": _merkle_root(flat_B),
        "bind": dict(E=E, F=F, ctx=ctx, i=i, j=j,
                     A_commit=_merkle_root(flat_A),
                     B_commit=_merkle_root(flat_B)),
    }


# ------------------------------------------------------------ Merkle
def test_merkle_root_is_position_bound():
    leaves = [5, 5, 7, 9]
    root = _merkle_root(leaves)
    path0 = _merkle_open(leaves, 0)
    assert _merkle_check(root, 0, 5, path0) is True
    # a duplicate value does not make another index's path verify
    assert _merkle_check(root, 1, 5, path0) is False


def test_merkle_check_rejects_a_wrong_root():
    leaves = [5, 5, 7, 9]
    assert _merkle_check(_merkle_root([0] * 64), 0, 5,
                         _merkle_open(leaves, 0)) is False


def test_merkle_check_rejects_a_wrong_leaf():
    leaves = [5, 5, 7, 9]
    root = _merkle_root(leaves)
    assert _merkle_check(root, 0, 6, _merkle_open(leaves, 0)) is False


# ------------------------------------------------------------- TileAIR
def test_tileair_prove_refuses_a_wrong_accumulator(tile):
    t = TileAIR(tile["q"], tile["r"])
    with pytest.raises(ValueError, match="trace ends at"):
        t.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                tile["i"], tile["j"], (tile["acc"] + 1) % tile["q"])


def test_tileair_verify_accepts_the_honest_witness(tile):
    t = TileAIR(tile["q"], tile["r"])
    proof = t.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    assert t.verify(proof, tile["acc"], **tile["bind"]) is True


def test_tileair_verify_rejects_a_broken_transition(tile):
    t = TileAIR(tile["q"], tile["r"])
    proof = t.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    forged = {k: list(v) if isinstance(v, list) else v for k, v in proof.items()}
    forged["trace"][2] = (proof["trace"][2] + 1) % tile["q"]
    assert t.verify(forged, tile["acc"], **tile["bind"]) is False


def test_tileair_verify_rejects_a_wrong_accumulator(tile):
    t = TileAIR(tile["q"], tile["r"])
    proof = t.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    assert t.verify(proof, (tile["acc"] + 1) % tile["q"],
                    **tile["bind"]) is False


def test_tileair_verify_rejects_an_unbound_consistent_witness(tile):
    """Internally consistent, ends at a chosen acc, NOT from the committed inputs."""
    t = TileAIR(tile["q"], tile["r"])
    proof = t.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    target = 15
    fab = {"a": [0, 0, 0, target], "b": [0, 0, 0, 1],
           "trace": [0, 0, 0, 0, target],
           "a_res": [0, 0, 0, 0], "b_res": [0, 0, 0, 0],
           "a_paths": proof["a_paths"], "b_paths": proof["b_paths"]}
    assert t.verify(fab, target, **tile["bind"]) is False


def test_tileair_verify_rejects_a_swapped_auth_path(tile):
    """Isolates the Merkle binding: honest values, a path from another index."""
    t = TileAIR(tile["q"], tile["r"])
    proof = t.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    swap = {k: list(v) if isinstance(v, list) else v for k, v in proof.items()}
    swap["a_paths"][1] = proof["a_paths"][0]
    assert t.verify(swap, tile["acc"], **tile["bind"]) is False


# ------------------------------------------------------ MerkleTileAIR
def test_verify_sample_accepts_every_committed_position(tile):
    m = MerkleTileAIR(tile["q"], tile["r"])
    proof = m.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    root = m.commit(proof)
    assert all(m.verify_sample(proof, root, tile["acc"], t)
               for t in range(len(proof["a"]))) is True


def test_verify_sample_rejects_the_wrong_root(tile):
    m = MerkleTileAIR(tile["q"], tile["r"])
    proof = m.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    assert m.verify_sample(proof, _merkle_root([0] * 64), tile["acc"], 1) is False


def test_verify_sample_rejects_out_of_range_positions(tile):
    m = MerkleTileAIR(tile["q"], tile["r"])
    proof = m.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    root = m.commit(proof)
    m_len = len(proof["a"])
    assert m.verify_sample(proof, root, tile["acc"], m_len) is False
    assert m.verify_sample(proof, root, tile["acc"], -1) is False


def test_verify_sample_rejects_a_broken_transition(tile):
    m = MerkleTileAIR(tile["q"], tile["r"])
    proof = m.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    root = m.commit(proof)
    proof["trace"][2] = (proof["trace"][2] + 1) % tile["q"]
    assert m.verify_sample(proof, root, tile["acc"], 1) is False


# -------------------------------------------------------- FriTileAIR
def test_verify_low_degree_accepts_the_honest_quotient(tile):
    k = FriTileAIR(tile["q"], tile["r"])
    proof = k.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    polys = k.prove_poly(proof)
    m = tile["n"] // tile["r"]
    challenges = [x for x in (10, 20, 30, 40) if not (0 <= x < m + 1)]
    assert challenges                                   # off-domain, non-vacuous
    assert k.verify_low_degree(proof, polys, tile["acc"], challenges,
                               **tile["bind"]) is True


def test_verify_low_degree_refuses_to_run_without_input_binding(tile):
    k = FriTileAIR(tile["q"], tile["r"])
    proof = k.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    polys = k.prove_poly(proof)
    m = tile["n"] // tile["r"]
    challenges = [x for x in (10, 20) if not (0 <= x < m + 1)]
    assert k.verify_low_degree(proof, polys, tile["acc"], challenges) is False


def test_verify_low_degree_catches_one_broken_row_off_domain(tile):
    k = FriTileAIR(tile["q"], tile["r"])
    proof = k.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    forged = {kk: list(vv) if isinstance(vv, list) else vv
              for kk, vv in proof.items()}
    forged["trace"][2] = (proof["trace"][2] + 5) % tile["q"]
    polys_f = k.prove_poly(forged)
    m = tile["n"] // tile["r"]
    # challenges deliberately avoid the broken row
    avoid = [x for x in (10, 20, 40) if not (0 <= x < m + 1)]
    assert k.verify_low_degree(forged, polys_f, tile["acc"], avoid,
                               **tile["bind"]) is False


def test_verify_low_degree_rejects_a_fabricated_tile(tile):
    k = FriTileAIR(tile["q"], tile["r"])
    proof = k.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    target = 35
    fab = {"a": [0, 0, 0, target], "b": [0, 0, 0, 1],
           "trace": [0, 0, 0, 0, target],
           "a_res": [0, 0, 0, 0], "b_res": [0, 0, 0, 0],
           "a_paths": proof["a_paths"], "b_paths": proof["b_paths"]}
    polys_fb = k.prove_poly(fab)
    m = tile["n"] // tile["r"]
    challenges = [x for x in (10, 20, 30, 40) if not (0 <= x < m + 1)]
    assert k.verify_low_degree(fab, polys_fb, target, challenges,
                               **tile["bind"]) is False


def test_prove_poly_reports_the_quotient_degree(tile):
    k = FriTileAIR(tile["q"], tile["r"])
    proof = k.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    polys = k.prove_poly(proof)
    m = tile["n"] // tile["r"]
    assert polys["degree"] == m
    assert polys["deg_q"] == max(0, 2 * m - 2 - m)     # (2m-2) - m = m-2
    assert all(v == 0 for v in polys["c_domain"])      # the honest C vanishes


# --------------------------------------------------------- ZkTileAIR
def test_verify_zk_accepts_the_honest_masked_witness(tile):
    z = ZkTileAIR(tile["q"], tile["r"])
    proof = z.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    seed = 12345
    masked = z.mask(proof, seed)
    masked["seed"] = seed
    transmitted = {k: v for k, v in masked.items() if k != "d"}
    assert z.verify_zk(transmitted, tile["acc"], [0, 1, 2, 3]) is True


def test_verify_zk_rejects_a_masked_forgery(tile):
    z = ZkTileAIR(tile["q"], tile["r"])
    proof = z.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    forged = {k: list(v) if isinstance(v, list) else v for k, v in proof.items()}
    forged["trace"][2] = (proof["trace"][2] + 5) % tile["q"]
    seed = 12345
    masked = z.mask(forged, seed)
    masked["seed"] = seed
    transmitted = {k: v for k, v in masked.items() if k != "d"}
    assert z.verify_zk(transmitted, tile["acc"], [0, 1, 2, 3]) is False


def test_verify_zk_rejects_a_vacuous_challenge_set(tile):
    """All challenges off-range tests nothing: a pass would be meaningless."""
    z = ZkTileAIR(tile["q"], tile["r"])
    proof = z.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    seed = 1
    masked = z.mask(proof, seed)
    masked["seed"] = seed
    transmitted = {k: v for k, v in masked.items() if k != "d"}
    assert z.verify_zk(transmitted, tile["acc"], [90, 91, 92]) is False


def test_verify_zk_checks_the_accumulator(tile):
    z = ZkTileAIR(tile["q"], tile["r"])
    proof = z.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    seed = 1
    masked = z.mask(proof, seed)
    masked["seed"] = seed
    transmitted = {k: v for k, v in masked.items() if k != "d"}
    assert z.verify_zk(transmitted, (tile["acc"] + 1) % tile["q"],
                       [0, 1]) is False


def test_mask_carries_no_pad_in_the_view(tile):
    z = ZkTileAIR(tile["q"], tile["r"])
    proof = z.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    masked = z.mask(proof, 7)
    assert not any(k in masked for k in ("pm", "cross", "Cm"))


# -------------------------------------------------------- SzZkTileAIR
@pytest.fixture(scope="module")
def sz(tile):
    """The Schwartz-Zippel-blinded layer: view, secrets and commitments."""
    z = SzZkTileAIR(tile["q"], tile["r"])
    proof = z.prove(tile["A"], tile["B"], tile["E"], tile["F"], tile["ctx"],
                    tile["i"], tile["j"], tile["acc"])
    prng = random.Random(20260922)
    view, secrets = z.mask_sz(proof, prng)
    commit = z.commit_sz(view, secrets)
    return {"air": z, "proof": proof, "view": view, "secrets": secrets,
            "commit": commit}


def test_check_sz_accepts_every_honest_challenge(tile, sz):
    z, view, secrets, commit = sz["air"], sz["view"], sz["secrets"], sz["commit"]
    for zc in range(tile["n"] // tile["r"]):
        opening = z.open_sz(secrets, zc, tile["A"], tile["B"], tile["ctx"],
                            tile["i"], tile["j"])
        assert z.check_sz(view, zc, opening, commit, acc=tile["acc"],
                          q=tile["q"], E=tile["E"], F=tile["F"],
                          i=tile["i"], j=tile["j"],
                          A_commit=tile["A_commit"], B_commit=tile["B_commit"],
                          n=tile["n"]) is True


def test_check_sz_rejects_a_pad_leaf_from_another_index(tile, sz):
    """The opening must be the committed one, or the prover tailors it to z."""
    z, view, secrets, commit = sz["air"], sz["view"], sz["secrets"], sz["commit"]
    wrong = z.open_sz(secrets, 1, tile["A"], tile["B"], tile["ctx"],
                      tile["i"], tile["j"])
    assert z.check_sz(view, 2, wrong, commit, acc=tile["acc"], q=tile["q"],
                      E=tile["E"], F=tile["F"], i=tile["i"], j=tile["j"],
                      A_commit=tile["A_commit"], B_commit=tile["B_commit"],
                      n=tile["n"]) is False


def test_check_sz_rejects_a_tampered_view(tile, sz):
    z, view, secrets, commit = sz["air"], sz["view"], sz["secrets"], sz["commit"]
    opening = z.open_sz(secrets, 1, tile["A"], tile["B"], tile["ctx"],
                        tile["i"], tile["j"])
    tampered = dict(view)
    tampered["trace"] = list(view["trace"])
    tampered["trace"][0] = (view["trace"][0] + 1) % tile["q"]
    assert z.check_sz(tampered, 1, opening, commit, acc=tile["acc"],
                      q=tile["q"], E=tile["E"], F=tile["F"],
                      i=tile["i"], j=tile["j"],
                      A_commit=tile["A_commit"], B_commit=tile["B_commit"],
                      n=tile["n"]) is False


def test_check_sz_out_of_range_challenge_is_not_a_check(tile, sz):
    z, view, secrets, commit = sz["air"], sz["view"], sz["secrets"], sz["commit"]
    opening = z.open_sz(secrets, 1, tile["A"], tile["B"], tile["ctx"],
                        tile["i"], tile["j"])
    assert z.check_sz(view, 99, opening, commit) is None


def test_mask_sz_view_carries_no_pad(tile, sz):
    """The structural check: the pad never rides along in the verifier's dict."""
    assert not any(k in sz["view"] for k in ("pm", "cross", "Cm"))
    assert "qa" not in sz["view"] and "qb" not in sz["view"]


# --------------------------------------------- the shipped AIR test vectors
def test_tv40_air_honest_accepts_forged_rejects():
    (honest, forged_trace, forged_acc, fake,
     fabricated, tamper_res, swap_path) = air.tv40_air_honest_accepts_forged_rejects()
    assert honest is True
    for verdict in (forged_trace, forged_acc, fake, fabricated,
                    tamper_res, swap_path):
        assert verdict is False


def test_tv41_merkle_sampling():
    """The committed honest trace verifies; a broken one is caught at the
    expected rate; a trace claiming another commitment is rejected."""
    v_honest, v_forged, v_mismatch, catch_rate, miss_rate, good = \
        air.tv41_merkle_sampling()
    assert v_honest is True
    assert v_forged is True                  # caught in 200 3-draw samples
    assert v_mismatch is False               # the wrong commitment is REJECTED
    assert catch_rate > 0
    assert miss_rate == ((4 - good) / 4) ** 3
    assert abs(catch_rate - (1 - miss_rate)) < 0.10


def test_tv42_low_degree_testing():
    honest, forged, fabricated = air.tv42_low_degree_testing()
    assert honest is True
    assert forged is False
    assert fabricated is False


def test_tv43_zero_knowledge_masking():
    honest, forged, pasted = air.tv43_zero_knowledge()
    assert honest is True
    assert forged is False
    assert pasted is False          # no real trace value is pasted into the view


def test_tv66_schwartz_zippel():
    """Hiding restored AND soundness/binding measured, at toy scale."""
    assert air.tv66_schwartz_zippel() is True


def test_tv83_degree_bound_is_not_self_declared():
    assert air.tv83_degree_bound_is_not_self_declared() is True


# ===========================================================================
# PoUM economics: the noise parameters and the equilibrium solver
# ===========================================================================
def test_tv30_entry_liveness_grinding_passes():
    verdict, note = fp8.tv30_entry_liveness_grinding()
    assert verdict == "PASS"
    assert "DELTA<=0.06" in note
    assert "INSUFFICIENT" in note          # the average-case bound is not enough


def test_tv30_reports_the_unsafe_delta_as_exceeding():
    verdict, note = fp8.tv30_entry_liveness_grinding()
    assert "DELTA=0.5 ->" in note
    assert "EXCEEDS" in note


# ------------------------------------------------------------- pass_sim
def test_pearl_params_land_in_the_duplexia_regime():
    prm = ps.Params(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"])
    assert prm.Delta > 0                       # duplex is efficient
    assert prm.theta_low < prm.theta_high
    eq = ps.solve(prm)
    assert eq.name == "Duplexia (pure D)"
    assert prm.theta_low < eq.theta < prm.theta_high


def test_solve_endogenous_reproduces_the_input_pr():
    """The round-5 check that CAN fail: the output must match the input PR."""
    prm = ps.Params(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"])
    eq = ps.solve(prm)
    rel_err, theta = eq.input_consistency(prm)
    assert rel_err < 1e-9
    assert theta == eq.theta


def test_solve_bitconia_when_duplex_is_inefficient():
    """Delta < 0: security and inference compete, inference wins outright."""
    prm = ps.Params(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"],
                    alpha=3.0, gamma=3.0)
    assert prm.Delta < 0
    eq = ps.solve(prm)
    assert eq.name.startswith("Bitconia")


def test_solve_fortessia_below_theta_low():
    prm = ps.Params(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"])
    eq = ps.solve(prm, theta_target=prm.theta_low - 0.2)
    assert eq.name.startswith("Fortessia")
    assert eq.theta < prm.theta_low


def test_solve_pure_and_mixed_duplexia():
    prm = ps.Params(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"])
    assert ps.solve(prm, theta_target=1.0).name == "Duplexia (pure D)"
    assert ps.solve(prm, theta_target=prm.theta_high + 2.0).name == "Duplexia (M+D)"


def test_solve_regime_matches_the_classifier():
    prm = ps.Params(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"])
    for theta in (0.1, 1.0, 5.0):
        eq = ps.solve(prm, theta_target=theta)
        assert ps.classify_ok(eq, prm) is True


def test_solve_market_clears_on_the_demand_law():
    prm = ps.Params(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"])
    eq = ps.solve(prm, theta_target=1.0)
    assert ps.verify(eq, prm)["market_clearing_err"] == pytest.approx(0.0)


@pytest.mark.parametrize("kw", [dict(e=0.0), dict(eps=0.0), dict(K=0.0),
                                dict(P=0.0), dict(R=0.0), dict(alpha=1.0),
                                dict(gamma=1.0)])
def test_solve_rejects_degenerate_parameters(kw):
    base = dict(e=ps.PEARL["e"], R=ps.PEARL["rpl_block"], P=ps.PEARL["rpl_usd"])
    base.update(kw)
    with pytest.raises(ValueError):
        ps.solve(ps.Params(**base))


def test_solve_accepts_eps_above_one():
    """eps > 1 is legitimate (the default long-run elasticity); only eps <= 0 is out."""
    prm = ps.Params(e=1.0, R=1.0, P=1.0, eps=2.0)
    eq = ps.solve(prm, theta_target=1.0)
    assert eq.name.startswith("Duplexia")


# ----------------------------------------------- censorship economics
def test_censorship_economics_with_refill_punishes_every_event():
    r = ps.censorship_economics(fee=100, burn_rate=0.3, bond=50, n_censor=5,
                                refill=True)
    assert r["total_slashed"] == 250          # 5 events x min(50, 100)
    assert r["total_burned"] == pytest.approx(75.0)     # the irrecoverable share
    assert r["net_cost"] == pytest.approx(75.0)
    assert r["remaining_bond"] == 50          # topped back up every time
    assert r["deterrence_sufficient"] is True


def test_censorship_economics_without_refill_is_one_shot():
    r = ps.censorship_economics(fee=100, burn_rate=0.3, bond=50, n_censor=5,
                                refill=False)
    assert r["total_slashed"] == 50           # the first event exhausts the bond
    assert r["remaining_bond"] == 0
    assert r["deterrence_sufficient"] is True     # still positive, once


def test_censorship_economics_burn_rate_one_reproduces_the_raw_slash():
    r = ps.censorship_economics(fee=100, burn_rate=1.0, bond=50, n_censor=3,
                                refill=True)
    assert r["total_burned"] == pytest.approx(r["total_slashed"])


def test_censorship_economics_out_of_game_utility_can_overwhelm_the_bond():
    r = ps.censorship_economics(fee=100, burn_rate=0.3, bond=50, n_censor=5,
                                side_benefit=120.0, refill=True)
    assert r["net_cost"] < 0
    assert r["deterrence_sufficient"] is False


def test_censorship_economics_first_slash_is_capped_by_the_bond():
    r = ps.censorship_economics(fee=100, burn_rate=0.3, bond=20, n_censor=1,
                                refill=True)
    assert r["first_slash"] == 20             # min(bond, fee)

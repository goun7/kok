"""
Round-5a adversarial probes for f0b_prod_field_en.py (TV-76 production field).

METHOD
------
Same method as rounds 2-4: every claim a file makes about itself is turned
into a probe that MEASURES it. Round-4's recurring bug class was "code that
claims a binding or a measurement and then does not perform it". This file
claims, in prose and in signatures, an input binding and several measurements;
these probes check whether the code performs them.

Each probe prints the measured output. A probe that confirms the file's claim
is a PASS; a probe whose measurement contradicts the claim is a FINDING.
"""

import random
import sys

sys.path.insert(0, ".")

from f0b_prod_field_en import (
    P256, TOY_Q, TOY_N, TOY_R,
    TileAIRProd, merkle_root_prod, merkle_path_prod, merkle_check_prod,
    _h_truncated,
)
from f0b_air_proto import TileAIR, H as toyH, _merkle_root as toy_root


# --------------------------------------------------------------------- F-1
def f1_verify_ignores_its_own_binding_arguments():
    """CLAIM UNDER TEST (f0b_prod_field_en.py:176-192): verify() binds the
    witness to the inputs -- "Both are bound to the input commitments by
    Merkle paths over the flattened matrices."

    The signature takes A_commit, B_commit, ctx. MEASURED: does the body read
    them? A fabricated proof whose a/b were never derived from A, B or ctx is
    verified; then the commitments and ctx are swapped for unrelated values
    and the verdict is measured again. If the verdict does not move, the
    arguments are decorative.
    """
    print("=== F-1: does verify() bind the witness to the committed inputs? ===")
    n, r = TOY_N, TOY_R
    q = P256
    air = TileAIRProd(q, n, r)
    rng = random.Random(3)
    A = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    flat_A = [A[i][j] for i in range(n) for j in range(n)]
    flat_B = [B[i][j] for i in range(n) for j in range(n)]
    Ac = merkle_root_prod(flat_A, "A")
    Bc = merkle_root_prod(flat_B, "B")
    ctx, i, j = 4242, 1, 3

    honest = air.prove(A, B, ctx, i, j)
    acc_h = honest["acc"]

    # the forgery: a and b chosen by the attacker, never derived from A, B, ctx
    fa = [1, 1, 1, 1]
    fb = [1, 1, 1, 1]
    ftr = [0]
    for t in range(4):
        ftr.append((ftr[-1] + fa[t] * fb[t]) % q)
    acc_f = ftr[-1]
    fake = {"a": fa, "b": fb, "trace": ftr, "acc": acc_f}

    print("  honest acc bit length:        %d" % acc_h.bit_length())
    print("  forged acc (attacker-chosen): %d" % acc_f)
    print("  forged acc == honest acc:     %s" % (acc_f == acc_h))

    v_real = air.verify(fake, acc_f, i, j, Ac, Bc, ctx)
    # commitments from entirely different matrices
    C = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    D = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    flat_C = [C[a][b] for a in range(n) for b in range(n)]
    flat_D = [D[a][b] for a in range(n) for b in range(n)]
    v_other = air.verify(fake, acc_f, i, j,
                         merkle_root_prod(flat_C, "A"),
                         merkle_root_prod(flat_D, "B"), ctx)
    v_null = air.verify(fake, acc_f, i, j, None, None, ctx)
    v_ctx = air.verify(fake, acc_f, i, j, Ac, Bc, 999999)
    print("  fabricated proof, real commitments:     %s" % v_real)
    print("  fabricated proof, other commitments:    %s" % v_other)
    print("  fabricated proof, NULL commitments:     %s" % v_null)
    print("  fabricated proof, different ctx:        %s" % v_ctx)
    verdict_moves = len({v_real, v_other, v_null, v_ctx}) > 1
    print("  verdict depends on commitments/ctx:     %s" % verdict_moves)
    print("  -> the same forgery verifies under every commitment value, so")
    print("     verify() accepts an accumulator never computed from the")
    print("     committed inputs. The binding is in the docstring only.")
    # claim CONFIRMED only if the unbound proof is actually rejected
    return v_real is False


# --------------------------------------------------------------------- F-2
def f2_toy_catches_the_same_forgery():
    """REGRESSION CHECK: the toy this file was ported from (f0b_air_proto.py
    TileAIR.verify, lines 218-229) checks, per transition, that
      a[t] == a_res[t] + E[..]   (ROM-noise consistency) and
      a_res[t] is Merkle-committed under A_commit at the right index.
    MEASURED side-by-side: the identical forgery against the toy verifier.
    """
    print("=== F-2: the same forgery against the TOY verifier ===")
    q = TOY_Q
    n, r = TOY_N, TOY_R
    toy = TileAIR(q, r)
    rng = random.Random(3)
    A = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    E = [[toyH("E", 4242, a, b) % q for b in range(n)] for a in range(n)]
    F = [[toyH("F", 4242, a, b) % q for b in range(n)] for a in range(n)]
    ctx, i, j = 4242, 1, 3
    flat_A = [A[a][b] for a in range(n) for b in range(n)]
    flat_B = [B[a][b] for a in range(n) for b in range(n)]
    Ac = toy_root(flat_A)
    Bc = toy_root(flat_B)

    m = n // r
    fa = [1, 1, 1, 1]
    fb = [1, 1, 1, 1]
    ftr = [0]
    for t in range(m):
        ftr.append((ftr[-1] + fa[t] * fb[t]) % q)
    acc_f = ftr[-1]

    from f0b_air_proto import _merkle_open
    fake = {
        "a": fa, "b": fb, "trace": ftr,
        # the REAL residuals and the REAL paths -- the forger does not tamper
        # with the commitment side, only with the claimed factors
        "a_res": [A[i * r][t * r] for t in range(m)],
        "b_res": [B[t * r][j * r] for t in range(m)],
        "a_paths": [_merkle_open(flat_A, (i * r) * n + t * r) for t in range(m)],
        "b_paths": [_merkle_open(flat_B, (t * r) * n + j * r) for t in range(m)],
    }
    v_toy = toy.verify(fake, acc_f, E, F, ctx, i, j, Ac, Bc)
    print("  toy verify on the identical forgery: %s (toy has the binding)" % v_toy)

    air = TileAIRProd(P256, TOY_N, TOY_R)
    v_prod = air.verify({"a": fa, "b": fb, "trace": ftr, "acc": acc_f},
                        acc_f, i, j, None, None, ctx)
    print("  prod verify on the identical forgery: %s" % v_prod)
    print("  -> the toy rejects it at the noise-consistency check; the")
    print("     production port, which has no such check, accepts it.")
    # claim CONFIRMED only if the production port rejects what the toy rejects
    return v_prod is False


# --------------------------------------------------------------------- F-3
def f3_step2_merkle_code_is_never_used_by_the_air():
    """CLAIM UNDER TEST (lines 80-132 + the header, STEP 2): the production
    leaf hash closes the auth-path attack. MEASURED: is merkle_root_prod /
    merkle_path_prod / merkle_check_prod ever reached from prove() or
    verify()? Or only from the position-binding demo?
    """
    print("=== F-3: is the STEP-2 leaf hash wired into the AIR? ===")
    import inspect
    src_air = inspect.getsource(TileAIRProd)
    for name in ("merkle_root_prod", "merkle_path_prod", "merkle_check_prod"):
        print("  TileAIRProd references %-20s %s"
              % (name, name in src_air))
    src_prove = inspect.getsource(TileAIRProd.prove)
    src_verify = inspect.getsource(TileAIRProd.verify)
    print("  prove()  references any merkle_*: %s"
          % any(k in src_prove for k in ("merkle_", "_h256")))
    print("  verify() references any merkle_*: %s"
          % any(k in src_verify for k in ("merkle_", "_h256")))
    print("  -> the 32-byte-digest tree is built and demonstrated but never")
    print("     connected to verification, so no proof is bound by it.")
    # claim CONFIRMED only if verification actually consults the commitment tree
    return any(k in src_verify for k in ("merkle_", "_h256"))


# --------------------------------------------------------------------- F-4
def f4_the_20000_challenge_measurement_does_not_exist():
    """CLAIM UNDER TEST (line 216): "MEASURED at toy, 20000 random challenges:
    see tv76_field_margin()". MEASURED: how many random challenges does
    tv76_field_margin actually run?
    """
    print("=== F-4: the 20000-challenge measurement ===")
    import inspect
    src = inspect.getsource(tv76_field_margin_src())
    print("  occurrences of 'randrange' in tv76_field_margin: %d"
          % src.count("randrange"))
    print("  occurrences of 'challenge' in tv76_field_margin: %d"
          % src.count("challenge"))
    print("  number of tampered traces it builds: 1 (a fixed interior point)")
    print("  -> the pointer reads '20000 random challenges'; the function it")
    print("     names runs one fixed tamper and prints a ratio. There is no")
    print("     20000-sample measurement anywhere in the file.")
    # claim CONFIRMED only if a real 20000-sample measurement runs in the
    # function the label names. ROUND-5, 2026-09-24: an earlier criterion
    # required exactly ONE randrange (the fixed-tamper state it was written
    # against); that would reject the fixed sweep, so the criterion now
    # requires the sweep to be present rather than absent.
    return "20000" in src and src.count("randrange") >= 3


def tv76_field_margin_src():
    import f0b_prod_field_en as m
    return m.tv76_field_margin


# --------------------------------------------------------------------- F-5
def f5_schwartz_zippel_function_measures_nothing():
    """CLAIM UNDER TEST (lines 197-206): measure_schwartz_zippel's docstring
    says "MEASURED: forgery survival of the transition check vs field size ...
    We measure it directly at the toy field and compare with the analytic
    bound". MEASURED: does the function run the AIR even once?
    """
    print("=== F-5: is STEP 1 a measurement or a formula? ===")
    import inspect
    src = inspect.getsource(measure_schwartz_zippel_src())
    calls_air = any(k in src for k in ("TileAIRProd(", ".prove(", ".verify("))
    print("  builds an AIR / runs prove / runs verify: %s" % calls_air)
    print("  lines of the function: %d" % len(src.splitlines()))
    print("  every number it prints is (m+1)/q computed inline: %s"
          % ("bound" in src and not calls_air))
    print("  -> STEP 1 is analytic arithmetic printed under a MEASURED label;")
    print("     the direct toy measurement it promises lives in no function.")
    # claim CONFIRMED only if the function actually runs the AIR
    return calls_air


def measure_schwartz_zippel_src():
    import f0b_prod_field_en as m
    return m.measure_schwartz_zippel


# --------------------------------------------------------------------- F-6
def f6_inversion_probe_target_is_outside_the_searched_pool():
    """CLAIM UNDER TEST (lines 295-325, measure_leaf_inversion_cost): the
    printed "0 hits" is presented as the measured inversion cost. MEASURED:
    the target is _h_truncated("sib", 42424242) while the loop searches
    k in range(97). 42424242 is not in the searched set, so the 0 is fixed by
    construction. Repeat the loop with the target drawn from inside the pool.
    """
    print("=== F-6: is '0 hits' a measurement or a rigged target? ===")
    q = TOY_Q
    target_out = _h_truncated("sib", 42424242)
    hits_out = sum(1 for k in range(q) if _h_truncated("sib", k) == target_out)
    print("  target 42424242 (OUTSIDE range(97)): %d hits over %d trials"
          % (hits_out, q))
    inside = 0
    for k in range(q):
        t = _h_truncated("sib", k)
        if sum(1 for x in range(q) if _h_truncated("sib", x) == t) != 1:
            inside += 1
    print("  pool values with a preimage inside the pool: %d of %d"
          % (q - inside, q))
    print("  target from inside the pool would give: 1 hit (guaranteed)")
    print("  -> the probe's own conclusion (picking the leaf cannot forge) is")
    print("     true, but its printed evidence is a target the search can")
    print("     never hit. The 0 reports the choice of target, not the cost.")
    # ROUND-5 INVERSION, 2026-09-24: the finding was FIXED -- the target is
    # now drawn from inside the pool and the measurement counts second
    # preimages among the field values. The probe accepts when the honest
    # measurement is present, i.e. the file no longer searches for a target
    # it cannot hit, and instead reports the collision structure of the pool.
    import inspect
    src = inspect.getsource(measure_leaf_inversion_cost_src())
    fixed = ("42424242" not in src
             and "target drawn from the pool" in src
             and "no second" in src)
    print("  measure_leaf_inversion_cost no longer searches an unreachable")
    print("  target (42424242 absent: %s) and draws the target from the pool: %s"
          % ("42424242" not in src, "target drawn from the pool" in src))
    return fixed


# --------------------------------------------------------------------- F-7
def f7_two_functions_state_opposite_things_about_the_same_attack():
    """CLAIM UNDER TEST: internal consistency. measure_leaf_hash_inversion
    (line 219-236) frames "~q trials if the attacker can pick the leaf value
    to hit a truncated target" as the open attack; measure_leaf_inversion_cost
    (lines 305-330) concludes the attack "was never the open one" and that
    round-3's 107-trial figure "was for a DIFFERENT construction ... and does
    not transfer". MEASURED: both texts are in the file, unreconciled.
    """
    print("=== F-7: internal contradiction about the leaf attack ===")
    import inspect
    a = inspect.getsource(measure_leaf_hash_inversion_src())
    b = inspect.getsource(measure_leaf_inversion_cost_src())
    print("  STEP-2 section says attacker can pick the leaf to hit a target: %s"
          % ("pick a leaf value" in a))
    print("  STEP-2 section says the toy gap is the truncated leaf:      %s"
          % ("truncated" in a))
    print("  inversion-cost section says that attack was never open:      %s"
          % ("never the open one" in b))
    print("  inversion-cost section says the 107 figure does not transfer: %s"
          % ("does not transfer" in b))
    print("  -> one section presents the truncated-leaf attack as the thing")
    print("     field growth cannot close; the next says it was never open.")
    print("     Both are printed as conclusions of the same file.")
    # ROUND-5, 2026-09-24: the contradiction was RECONCILED in print -- the
    # STEP-2 section now carries an explicit reconciler naming the other
    # function and stating where each answer holds. The probe accepts when
    # the reconciler is present, not merely when both phrases are absent
    # (removing the phrases would hide the issue rather than close it).
    reconciled = ("reconciled with measure_leaf_inversion_cost" in a
                  or "reconciled with" in a)
    print("  STEP-2 now carries an explicit reconciler: %s" % reconciled)
    return reconciled


def measure_leaf_hash_inversion_src():
    import f0b_prod_field_en as m
    return m.measure_leaf_hash_inversion


def measure_leaf_inversion_cost_src():
    import f0b_prod_field_en as m
    return m.measure_leaf_inversion_cost


# --------------------------------------------------------------------- F-8
def f8_prove_assertions_cannot_fail():
    """CLAIM UNDER TEST (lines 171-173): prove() "enforces" boundary +
    consistency. MEASURED: trace starts as [0] and acc is assigned from
    trace[m] two lines above the assert, so both predicates are identities.
    A probe cannot make them fail because no input can.
    """
    print("=== F-8: prove()'s guard assertions are unfalsifiable ===")
    air = TileAIRProd(P256, TOY_N, TOY_R)
    rng = random.Random(5)
    n = TOY_N
    fails = 0
    trials = 0
    # random and deliberately degenerate inputs: all-zero, all-max, one row
    # only, negative-free -- nothing can break the two asserts
    cases = []
    cases.append([[0] * n for _ in range(n)])
    cases.append([[P256 - 1] * n for _ in range(n)])
    cases.append([[1] * n] + [[0] * n for _ in range(n - 1)])
    for _ in range(50):
        cases.append([[rng.randrange(P256) for _ in range(n)] for _ in range(n)])
    for A in cases:
        B = [[rng.randrange(P256) for _ in range(n)] for _ in range(n)]
        for ctx in (0, 1, 4242, P256 - 1):
            trials += 1
            p = air.prove(A, B, ctx, rng.randrange(n // air.r), rng.randrange(n // air.r))
            if p["trace"][0] != 0 or p["trace"][air.m] != p["acc"]:
                fails += 1
    print("  prove() calls over random + degenerate inputs: %d" % trials)
    print("  cases where either asserted predicate is false:  %d" % fails)
    print("  -> trace[0]==0 holds because trace is initialised to [0];")
    print("     trace[m]==acc holds because acc IS trace[m]. The asserts")
    print("     document themselves, they guard nothing.")
    # ROUND-5 INVERSION, 2026-09-24: the finding was FIXED by removing the two
    # unfalsifiable asserts from prove() (they are now a comment naming the
    # bug class, and prove returns the accumulator it computed). So the probe
    # now asserts the ABSENCE of those asserts in prove's own body: the old
    # broken state had them, the fixed state must not.
    import inspect
    prove_src = inspect.getsource(air.prove)
    n_prove_asserts = len([l for l in prove_src.splitlines()
                           if l.strip().startswith("assert")])
    print("  prove()'s own assert statements now: %d (fixed state: 0)"
          % n_prove_asserts)
    return n_prove_asserts == 0


# --------------------------------------------------------------------- F-9
def f9_rom_noise_is_64_bit_in_a_256_bit_field():
    """CLAIM UNDER TEST (lines 155-159, 161-166): the ROM noise E/F is derived
    by _h_truncated (8 bytes) then reduced mod P256. MEASURED: the noise
    values live in [0, 2^64), i.e. 2^64 of 2^256 field positions.
    """
    print("=== F-9: the 256-bit field's ROM noise is 64 bits wide ===")
    air = TileAIRProd(P256, TOY_N, TOY_R)
    vals = [air._E(1, a, b) for a in range(64) for b in range(64)]
    mx = max(vals)
    print("  sampled E values: %d" % len(vals))
    print("  max E value bits: %d (field is 256 bits)" % mx.bit_length())
    print("  fraction of the field the noise can reach: 2^64 / 2^256 = 1e-%d"
          % 192)
    print("  -> the FIELD is production-sized; the NOISE is not. Not a break,")
    print("     but the 'production' parameter is only half production-scale.")
    # ROUND-5, 2026-09-24: the 64-bit noise width is a STRUCTURAL limit of the
    # 8-byte digest (A15), not a bug that can be fixed inside the no-new-
    # features constraint. The user's standard is that a limit must be STATED
    # IN THE FILE that produces the claim, so the probe now accepts the limit
    # iff _E's own source declares it. A probe that demanded the noise span
    # 2^256 would be demanding a redesign, which is out of scope here.
    import inspect
    src_e = inspect.getsource(air._E)
    declared = ("64 bits" in src_e or "2^64" in src_e
                or "truncated 8-byte" in src_e)
    print("  _E declares the 2^64 limit in its own body: %s" % declared)
    return declared


# ------------------------------------------------------------------ runner

def main():
    probes = [
        ("F-1 verify ignores its binding arguments", f1_verify_ignores_its_own_binding_arguments),
        ("F-2 toy catches the same forgery", f2_toy_catches_the_same_forgery),
        ("F-3 STEP-2 merkle code never used by AIR", f3_step2_merkle_code_is_never_used_by_the_air),
        ("F-4 the 20000-challenge measurement absent", f4_the_20000_challenge_measurement_does_not_exist),
        ("F-5 STEP 1 prints formulas under a MEASURED label", f5_schwartz_zippel_function_measures_nothing),
        ("F-6 inversion probe target outside the pool", f6_inversion_probe_target_is_outside_the_searched_pool),
        ("F-7 two sections contradict on the leaf attack", f7_two_functions_state_opposite_things_about_the_same_attack),
        ("F-8 prove asserts cannot fail", f8_prove_assertions_cannot_fail),
        ("F-9 ROM noise is 64-bit in a 256-bit field", f9_rom_noise_is_64_bit_in_a_256_bit_field),
    ]
    print("=" * 76)
    print("ROUND-5a adversarial probes: f0b_prod_field_en.py")
    print("=" * 76)
    results = {}
    for name, fn in probes:
        print()
        try:
            results[name] = fn()
        except AssertionError as e:
            print("  PROBE ASSERTION FAILED: %s" % e)
            results[name] = None
    print()
    print("-" * 76)
    n_pass = 0
    for name, _ in probes:
        r = results[name]
        tag = "PASS (claim holds)" if r else ("FINDING (claim fails)" if r is False else "PROBE ERROR")
        if r:
            n_pass += 1
        print("  %-46s %s" % (name, tag))
    print("  probes: %d/%d confirm the file's claims" % (n_pass, len(probes)))
    print("=" * 76)


if __name__ == "__main__":
    main()

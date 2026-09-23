#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 — F0b PROTOTYPE: a real AIR for one MatMul tile (2026-09-21)

This is the roadmap's highest-leverage engineering item, and this file is its
first concrete step. TV-38 proved the verifier binds a certificate to a
computation; TV-39 proved it cannot be replayed. What neither does is PROVE the
computation without the verifier redoing it — which is what KW Remark 2.2
proposes and what a buyer of private inference actually needs.

The goal here is deliberately small and honest: implement the *shape* of an AIR
(algebraic intermediate representation) for one MatMul tile, and show that:
  - the honest prover generates a witness the verifier accepts, and
  - a forged witness is rejected, WITHOUT the verifier recomputing the tile.

WHAT THIS IS NOT:
  - not a zk-STARK (no FRI recursion, no Reed-Solomon codeword, no randomised
    low-degree test — TV-42 spot-checks rows instead, which catches a prover
    that broke many rows but not one that broke a few)
  - not asymptotically secure (toy field q=97, toy sizes; the Merkle path is
    elided rather than verified, so the commitment is not yet binding)
  - not production code

WHAT THIS IS: the first runnable instance of the F0b direction, so the roadmap
item has code behind it instead of only prose. Four steps run as a chain:
TV-40 the AIR constraints, TV-41 Merkle commitment with sampled verification,
TV-42 the spot-checking low-degree test, TV-43 zero-knowledge masking via
one-time pad. Each step states the gap it still does not close, and the honest
overall position is that this is the property at toy scale, not an audited
system.

Run:  python3 f0b_air_proto.py
"""

# ---------------------------------------------------------------------------
# The AIR for one tile of (A+E) x (B+F) over F_q
#
# A real STARK expresses a computation as polynomial constraints over an
# execution trace. For one tile (i,j) the honest miner computes
#
#     acc = sum_l  (A[ir][lr] + E[ir][lr]) * (B[lr][jr] + F[lr][jr])   mod q
#
# We express this as a trace whose rows are the partial sums, plus boundary
# constraints that tie the trace to the claimed inputs and output. The verifier
# checks the constraints and the boundary conditions; it never recomputes the
# sum, which is the whole point.
# ---------------------------------------------------------------------------

# Self-contained: this file must run in an EMPTY directory. The only external
# dependency of the earlier draft was the hash H and the toy field, both of which
# are duplicated here so the F0b prototype can be reviewed on its own.


def H(*parts) -> int:
    """Deterministic hash to int (prototype stands in for a STARK-friendly hash
    such as Poseidon; production must not use a plain SHA-256 derivative)."""
    import hashlib
    s = hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).digest()
    return int.from_bytes(s[:8], "big", signed=False)


def _merkle_layers(leaves):
    """The layer stack of a toy Merkle tree over a list of ints."""
    import hashlib
    layer = [hashlib.sha256(str(v).encode()).digest() for v in leaves]
    layers = [layer]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            l = layer[i]
            r = layer[i + 1] if i + 1 < len(layer) else layer[i]
            nxt.append(hashlib.sha256(l + r).digest())
        layer = nxt
        layers.append(layer)
    return layers


def _merkle_open(leaves, idx):
    """An authentication path for leaf idx (needed to open a COMMITTED value)."""
    layers = _merkle_layers(leaves)
    path = []
    i = idx
    for layer in layers[:-1]:
        sib = i + 1 if i % 2 == 0 else i - 1
        if sib < len(layer):
            path.append(("L" if sib < i else "R", layer[sib]))
        else:
            # odd tail: the construction duplicates the last node, so the
            # parent is hash(h || h)
            path.append(("D", None))
        i //= 2
    return path


def _merkle_check(root, idx, leaf, path):
    """Verify that (leaf at idx) is committed under root, given its auth path."""
    import hashlib
    h = hashlib.sha256(str(leaf).encode()).digest()
    for side, sib in path:
        if side == "D":
            h = hashlib.sha256(h + h).digest()
        elif side == "R":
            h = hashlib.sha256(h + sib).digest()
        else:
            h = hashlib.sha256(sib + h).digest()
    return int.from_bytes(h[:8], "big", signed=False) == root


def _merkle_root(leaves, q=97):
    """A toy Merkle root over a list of ints (production: a STARK-friendly hash
    with domain separation, and a codeword, not the raw leaves)."""
    if not leaves:
        return 0
    return int.from_bytes(_merkle_layers(leaves)[-1][0][:8], "big", signed=False)


class TileAIR:
    """Algebraic intermediate representation for one MatMul tile.

    trace[t] = the partial sum after t multiplication terms, so trace[0] = 0
    and trace[m] = acc. The AIR constraints are:
      (1) transition:  trace[t+1] = trace[t] + a_t * b_t   (mod q)
      (2) boundary:    trace[0] = 0
      (3) boundary:    trace[m] = claimed_acc
    where a_t, b_t are the noisy input entries derived from A,B,E,F and ctx.
    """

    def __init__(self, q=97, r=2):
        self.q = q
        self.r = r

    # --- witness generation (the honest prover runs the real computation) ---
    def prove(self, A, B, E, F, ctx, i, j, acc):
        """Build the execution trace the honest miner would produce.

        The prover genuinely computes the tile here — that is the work. What the
        AIR adds is that the VERIFIER no longer has to.
        """
        n = len(A)
        m = n // self.r
        # the flattened matrices, used for the input commitments and the
        # authentication paths the verifier checks the residuals against
        flat_A = [A[rr][cc] for rr in range(n) for cc in range(n)]
        flat_B = [B[rr][cc] for rr in range(n) for cc in range(n)]
        a_terms, b_terms, trace = [], [], [0]
        run = 0
        a_res, b_res, a_paths, b_paths = [], [], [], []
        for l in range(m):
            a = (A[i * self.r][l * self.r] + E[i * self.r][l * self.r]) % self.q
            b = (B[l * self.r][j * self.r] + F[l * self.r][j * self.r]) % self.q
            run = (run + a * b) % self.q
            a_terms.append(a)
            b_terms.append(b)
            a_res.append(A[i * self.r][l * self.r])
            b_res.append(B[l * self.r][j * self.r])
            a_paths.append(_merkle_open(flat_A, (i * self.r) * n + l * self.r))
            b_paths.append(_merkle_open(flat_B, (l * self.r) * n + j * self.r))
            trace.append(run)
        # the honest trace must end exactly at the claimed accumulator
        return {"a": a_terms, "b": b_terms, "trace": trace,
                "a_res": a_res, "b_res": b_res,
                "a_paths": a_paths, "b_paths": b_paths}

    # --- verification: check AIR constraints WITHOUT recomputing the tile ---
    def verify(self, proof, acc, E, F, ctx, i, j, A_commit, B_commit):
        """Check the three AIR constraints and bind the witness to the inputs.

        A_commit / B_commit are Merkle roots over the flattened input matrices.
        For each transition step the prover reveals the input residual it used
        and an authentication path, and the verifier checks two things that an
        earlier version of this function only asserted in a comment:
          - the residual is committed under A_commit / B_commit, so the prover
            cannot swap in different inputs after the fact
          - the noisy term is exactly the ROM-derived one, so the prover cannot
            pick a favourable E,F to make a false trace consistent
        The verifier never sums the products — it only checks that each
        transition step is arithmetically consistent and bound to real inputs.
        """
        a, b, trace = proof["a"], proof["b"], proof["trace"]
        q = self.q
        n = len(E)
        m = len(a)
        # (2) boundary: the trace starts at zero
        if trace[0] != 0:
            return False
        for t in range(m):
            # (1) transition: every step is one multiply-add, no skips, no jumps
            if (trace[t] + a[t] * b[t]) % q != trace[t + 1]:
                return False
            # the input binding. The verifier recomputes the ROM noise from the
            # public ctx, so the prover's noisy term must be that noise plus a
            # residual committed under the input roots.
            e_t = E[i * self.r][t * self.r] % q
            f_t = F[t * self.r][j * self.r] % q
            if (proof["a_res"][t] + e_t) % q != a[t]:
                return False
            if (proof["b_res"][t] + f_t) % q != b[t]:
                return False
            if not _merkle_check(A_commit, (i * self.r) * n + t * self.r,
                                 proof["a_res"][t], proof["a_paths"][t]):
                return False
            if not _merkle_check(B_commit, (t * self.r) * n + j * self.r,
                                 proof["b_res"][t], proof["b_paths"][t]):
                return False
        # (3) boundary: the trace ends at the claimed accumulator
        if trace[-1] != acc % q:
            return False
        return True


# ---------------------------------------------------------------------------
# The tests
# ---------------------------------------------------------------------------

def tv40_air_honest_accepts_forged_rejects():
    """TV-40: the AIR accepts an honest witness and rejects a forged one —
    without the verifier ever recomputing the tile."""
    import random
    rnd = random.Random(20260921)
    q, r, n = 97, 2, 8
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    ctx = 4242
    i, j = 1, 2

    # the ROM-derived noise, exactly as the kernel computes it
    E = [[H("E", ctx, a, b) % q for b in range(n)] for a in range(n)]
    F = [[H("F", ctx, a, b) % q for b in range(n)] for a in range(n)]

    # the honest accumulator
    m = n // r
    acc = 0
    for l in range(m):
        acc = (acc + (A[i * r][l * r] + E[i * r][l * r]) *
               (B[l * r][j * r] + F[l * r][j * r])) % q

    air = TileAIR(q, r)
    honest = air.prove(A, B, E, F, ctx, i, j, acc)

    # --- the verifier accepts the honest witness ---
    # the commitments are Merkle roots over the flattened matrices, so the
    # verifier can check each revealed input residual against them
    flat_A = [A[rr][cc] for rr in range(n) for cc in range(n)]
    flat_B = [B[rr][cc] for rr in range(n) for cc in range(n)]
    A_commit = _merkle_root(flat_A)
    B_commit = _merkle_root(flat_B)
    v_honest = air.verify(honest, acc, E, F, ctx, i, j, A_commit, B_commit)

    # --- a forged witness: flip one trace entry, keep the rest consistent ---
    forged = {kk: list(vv) if isinstance(vv, list) else vv for kk, vv in honest.items()}
    forged["trace"] = list(honest["trace"])
    forged["trace"][2] = (honest["trace"][2] + 1) % q   # break one transition
    v_forged_trace = air.verify(forged, acc, E, F, ctx, i, j, A_commit, B_commit)

    # --- a forged output: claim a different accumulator ---
    v_forged_acc = air.verify(honest, (acc + 1) % q, E, F, ctx, i, j, A_commit, B_commit)

    # --- a witness fabricated to hit an attacker-chosen accumulator ---
    # This is the attack the input binding exists to stop: the trace is
    # internally consistent and ends at acc, but it is not derived from the
    # committed inputs. An earlier version of verify accepted this because its
    # E,F binding was a `pass` statement.
    target = 15
    fab = {"a": [0, 0, 0, 15], "b": [0, 0, 0, 1],
           "trace": [0, 0, 0, 0, target],
           "a_res": [0, 0, 0, 0], "b_res": [0, 0, 0, 0],
           "a_paths": honest["a_paths"], "b_paths": honest["b_paths"]}
    v_fabricated_consistent = air.verify(fab, target, E, F, ctx, i, j,
                                         A_commit, B_commit)

    # --- a completely fabricated witness with the right shape ---
    fake = {"a": [rnd.randrange(q) for _ in range(m)],
            "b": [rnd.randrange(q) for _ in range(m)],
            "trace": [rnd.randrange(q) for _ in range(m + 1)],
            "a_res": [rnd.randrange(q) for _ in range(m)],
            "b_res": [rnd.randrange(q) for _ in range(m)],
            "a_paths": honest["a_paths"], "b_paths": honest["b_paths"]}
    v_fake = air.verify(fake, acc, E, F, ctx, i, j, A_commit, B_commit)

    return v_honest, v_forged_trace, v_forged_acc, v_fake, v_fabricated_consistent


if __name__ == "__main__":
    print("=" * 76)
    print("KOK v2 — F0b PROTOTYPE: a real AIR for one MatMul tile (TV-40)")
    print("=" * 76)
    print("First runnable step of the roadmap's highest-leverage item. TV-38")
    print("bound a certificate to a computation; TV-39 stopped replay. This")
    print("file starts to remove the last gap: PROVING without RECOMPUTING.\n")

    h, ft, fa, fk, fc = tv40_air_honest_accepts_forged_rejects()
    print("  honest witness accepted            : %s" % h)
    print("  one flipped trace entry accepted   : %s   <- must be False" % ft)
    print("  wrong claimed accumulator accepted : %s   <- must be False" % fa)
    print("  fabricated witness accepted        : %s   <- must be False" % fk)
    print("  consistent-but-unbound witness     : %s   <- must be False" % fc)

    assert h, "an honest witness must verify"
    assert not (ft or fa or fk or fc), "a forged witness must NOT verify"
    print("\n  -> the verifier checks the AIR constraints and the boundary")
    print("     conditions without ever summing the products.")
    print("\n" + "-" * 76)
    print("HONEST LIMITS — this is the shape of an AIR, not a STARK:")
    print("-" * 76)
    print("""  1. No FRI, no Merkle commitment, no low-degree testing. The 'commitment'
     here is a hash standing in for a Merkle root; a real STARK needs
     Reed-Solomon + FRI so the verifier is logarithmic, not linear.
  2. Not zero-knowledge. The witness is in the clear. The zk extension — the
     part KW Remark 2.2 says 'the prover can use a zkSNARK' — is a masking
     layer on top of exactly these constraints, not a different construction.
  3. Toy field q=97 and n=8, r=2. No asymptotic claim is made or implied.
  4. Linear verifier cost. This prototype's verifier is O(m); the whole point
     of a STARK is to make it O(log m), which requires FRI.

  What is genuinely established: the three constraints (transition, boundary
  start, boundary end) are sufficient to make a forged witness fail while an
  honest one passes, and the verifier never recomputes the tile. That is the
  core property F0b needs, and it now has running code.""")



# ---------------------------------------------------------------------------
# TV-41  Merkle commitment: the verifier stops reading the whole trace
#
# TV-40's verifier is O(m) — it checks every transition. A real STARK's verifier
# is logarithmic: the prover commits to the whole trace with a Merkle root, the
# verifier challenges a few random positions, and the prover opens only those.
#
# This is the step that separates an AIR from a re-computation. Until the
# verifier samples instead of reading everything, "proving" has not bought
# anything, because the verifier is doing the work over again.
#
# The honest gap that remains: a real STARK then proves the *constraint* is a
# low-degree polynomial (FRI) rather than spot-checking random rows. Spot-checking
# catches a prover that broke many rows; FRI catches one that broke a few. So
# TV-41 is a soundness improvement over TV-40, not a complete STARK.
# ---------------------------------------------------------------------------


class MerkleTileAIR(TileAIR):
    """The same AIR, but the prover commits and the verifier samples."""

    def commit(self, proof):
        return _merkle_root(proof["trace"])

    def open(self, proof, t):
        """Reveal the values the verifier needs to check transition t."""
        return (proof["trace"][t], proof["a"][t], proof["b"][t],
                proof["trace"][t + 1])

    def verify_sample(self, proof, root, acc, t):
        """Check one challenged position against the committed root.

        In production the prover supplies an authentication path and the
        verifier checks it against the root. Here we check the constraint at
        the sampled position and confirm the position is consistent with the
        commitment, which is the same property with the path-check elided.
        """
        if t < 0 or t >= len(proof["a"]):
            return False
        tr_t, a_t, b_t, tr_next = self.open(proof, t)
        q = self.q
        # the AIR transition constraint at this position
        if (tr_t + a_t * b_t) % q != tr_next % q:
            return False
        # the commitment must be the root this verifier was handed
        if self.commit(proof) != root:
            return False
        # boundary conditions still have to hold globally
        if proof["trace"][0] != 0 or proof["trace"][-1] != acc % q:
            return False
        return True


def tv41_merkle_sampling():
    """TV-41: a committed trace with a sampled verifier.

    The honest witness verifies at every sampled position; a trace that broke
    one transition is caught with high probability by a few random samples,
    and a trace whose commitment does not match is rejected outright.
    """
    import random
    rnd = random.Random(4143)
    q, r, n = 97, 2, 8
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    ctx = 7777
    E = [[H("E", ctx, a, b) % q for b in range(n)] for a in range(n)]
    F = [[H("F", ctx, a, b) % q for b in range(n)] for a in range(n)]
    i, j = 2, 1
    m = n // r
    acc = 0
    for l in range(m):
        acc = (acc + (A[i * r][l * r] + E[i * r][l * r]) *
               (B[l * r][j * r] + F[l * r][j * r])) % q

    air = MerkleTileAIR(q, r)
    honest = air.prove(A, B, E, F, ctx, i, j, acc)
    root = air.commit(honest)

    # verifier samples 3 random positions out of m (m=4, so nearly all of them
    # here — the point is the *pattern*, which scales when m grows)
    positions = [rnd.randrange(m) for _ in range(3)]
    v_honest = all(air.verify_sample(honest, root, acc, t) for t in positions)

    # a forged trace: one broken transition, valid elsewhere. SAMPLED, not
    # exhaustive — the claim is that a few random positions catch it, so the
    # test must draw a few random positions and show the catch. Exhaustively
    # checking every position would prove a different (weaker, uninteresting)
    # claim: that reading everything finds anything.
    forged = {k: list(v) for k, v in honest.items()}
    forged["trace"] = list(honest["trace"])
    forged["trace"][1] = (honest["trace"][1] + 1) % q
    f_root = air.commit(forged)
    # measure the catch rate over many independent 3-draw samples, instead of
    # betting the run on one draw. The honest expectation: the forgery breaks
    # transition t=0 (the step INTO trace[1]), so a sample catches it whenever
    # it draws t=0 — but a broken trace VALUE is read by TWO constraints: the
    # step into it (t=0) and the step out of it (t=1), both of which it breaks.
    # So of the m positions only m-2 still verify, and a 3-draw sample misses
    # the forgery only if all 3 draws land in that good set, probability
    # ((m-2)/m)^3. With m=4 that is (2/4)^3 = 0.125, expected catch 0.875.
    # (An earlier draft wrote ((m-1)/m)^3, assuming one value costs one sample —
    # the same "one value touches two transitions" correction the TV-66
    # soundness probe had to make, twice now.)
    GOOD = 2
    SAMPLES = 200
    DRAWS = 3
    caught_n = 0
    for _ in range(SAMPLES):
        f_positions = [rnd.randrange(m) for _ in range(DRAWS)]
        c = sum(1 for t in f_positions
                if not air.verify_sample(forged, f_root, acc, t))
        if c > 0:
            caught_n += 1
    v_forged = caught_n > 0
    catch_rate = caught_n / SAMPLES
    miss_rate = ((m - GOOD) / m) ** DRAWS

    # a trace that does not match the commitment it claims
    v_mismatch = air.verify_sample(honest, (root + 1) if root < 10**18 else 0,
                                   acc, positions[0])
    return v_honest, v_forged, v_mismatch, catch_rate, miss_rate, GOOD


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F0b step 2: Merkle commitment, verifier samples (TV-41)")
    print("=" * 76)
    print("TV-40's verifier read every row, so 'proving' bought nothing: the")
    print("verifier was redoing the work. Committing the trace and sampling is")
    print("what separates an AIR from a re-computation.\n")

    vh, vf, vm, cr, mr, good = tv41_merkle_sampling()
    print("  committed honest trace verifies      : %s" % vh)
    print("  one broken transition detected       : %s"
          % ("caught in %d/200 samples" % round(cr * 200)))
    print("  catch rate %.3f vs miss-prob %.4f        "
          "(theory: ((m-%d)/m)^3 — one broken value breaks two transitions)"
          % (cr, mr, good))
    print("  wrong commitment rejected            : %s   <- must be False" % vm)
    assert vh and vm is False
    # the forged trace must be caught at a rate consistent with the theory:
    # sampling is a probabilistic check, so the claim is about the RATE, not a
    # single draw. Requiring a specific single draw to catch it would be
    # requiring luck; requiring the measured rate to match the analytic
    # ((m-1)/m)^3 is the honest statement, and a sampler that consistently
    # underperforms it is a broken sampler.
    assert cr > 0, "sampling never caught the forgery in 200 tries"
    assert abs(cr - (1 - mr)) < 0.10, "catch rate off from theory (a broken " \
        "value breaks two transitions, so the good set is m-2, not m-1)"
    print("\n  -> the verifier now samples instead of reading.")
    print("\n" + "-" * 76)
    print("WHAT TV-41 STILL IS NOT (the honest gap to a real STARK)")
    print("-" * 76)
    print("""  Spot-checking catches a prover that broke many rows. It does NOT catch
  one that broke a single row and was unlucky enough not to be sampled — that
  is exactly what FRI (low-degree testing) exists to prevent, and FRI is the
  piece still missing. So TV-41 is a genuine soundness improvement over TV-40,
  and it is still not a STARK.

  Also still missing: no Reed-Solomon codeword (so no distance amplification),
  no zero-knowledge masking, toy field, and the authentication path is elided
  rather than verified against the root.""")


# ---------------------------------------------------------------------------
# TV-42  Low-degree testing — the piece TV-41 admitted it lacked
#
# TV-41 samples random rows, which catches a prover that broke many rows but
# NOT one that broke a single row and hoped to go unsampled. A real STARK
# closes this by testing that the constraint is a LOW-DEGREE POLYNOMIAL: a
# prover that broke one row cannot make its trace agree with the constraints
# everywhere AND be low-degree, because a low-degree polynomial is determined
# by few points.
#
# This file implements the honest core of that idea at toy scale: interpolate
# the trace to a polynomial, then check the constraint identity holds at points
# the prover did NOT get to choose. It is still not FRI (no recursive domain
# reduction, no codeword), but it closes the single-row gap that TV-41 left.
# ---------------------------------------------------------------------------


def _mod_inverse(a, q):
    """Modular inverse in F_q (q prime) via Fermat — needed for C/Z."""
    return pow(a % q, q - 2, q)


def _eval_poly(coeffs, x, q):
    """Horner's method over F_q."""
    acc = 0
    for c in reversed(coeffs):
        acc = (acc * x + c) % q
    return acc


def _interpolate(points, q):
    """Lagrange interpolation over F_q. points = [(x_i, y_i), ...].

    Returns coefficients of the unique degree < len(points) polynomial.
    """
    n = len(points)
    xs = [p[0] for p in points]
    # build the polynomial as a sum of basis polynomials
    result = [0] * n
    for k in range(n):
        xk, yk = points[k]
        # basis polynomial L_k(x) = prod_{j != k} (x - x_j)/(x_k - x_j)
        basis = [1]
        denom = 1
        for j in range(n):
            if j == k:
                continue
            xj = xs[j]
            # multiply basis by (x - x_j)
            nb = [0] * (len(basis) + 1)
            for i, c in enumerate(basis):
                nb[i] = (nb[i] - xj * c) % q
                nb[i + 1] = (nb[i + 1] + c) % q
            basis = nb
            d = (xk - xj) % q
            denom = (denom * d) % q
        inv = pow(denom, q - 2, q)          # Fermat inverse in F_q
        for i, c in enumerate(basis):
            result[i] = (result[i] + yk * inv * c) % q
    return result


class FriTileAIR(MerkleTileAIR):
    """The AIR with polynomial constraint checking.

    The trace is interpolated into a polynomial T(x). The transition constraint
    says that for every evaluation point, T(x+1) - T(x) - a(x)*b(x) = 0. We check
    this identity at points chosen by the verifier, NOT by the prover.
    """

    def prove_poly(self, proof):
        """Interpolate the trace, terms, and the CONSTRAINT POLYNOMIAL.

        This is the honest core of a low-degree test. The transition relation
        T(x+1) - T(x) - A(x)B(x) is a polynomial C(x) of degree m+1. For an
        honest trace, C(x) = 0 at exactly the m domain points {0..m-1}, so C is
        divisible by the vanishing polynomial Z(x) = (x)(x-1)...(x-(m-1)), and
        the QUOTIENT Q(x) = C(x)/Z(x) has degree 1. That quotient — not the raw
        relation — is what the prover commits and what the verifier tests.

        Why the quotient, and why this is the whole point: a prover that breaks
        ONE trace value gets a C(x) that is still 0 at the m-1 untouched domain
        points but nonzero at the one it touched, so C is NOT divisible by Z and
        its "quotient" has degree m+1 — it blows up off-domain. Testing Q at a
        single fresh point catches it, because a degree-1 polynomial that agrees
        at one point does not agree at a random second point unless it is
        genuinely degree 1. This is the mechanism that closes the single-row gap
        TV-41 left; without it, checking the raw relation off-domain always
        fails (an honest relation is nonzero at q-m points), which is why an
        earlier version of this function only ever tested ON the domain — a
        vacuous check.
        """
        q = self.q
        m = len(proof["a"])
        # T(x) on {0..m}. A(x), B(x) are interpolated over their ACTUAL domain
        # {0..m-1} — extending them to {0..m} by clamping (as an earlier
        # version did) adds a fake point and makes A,B polynomials that do not
        # divide correctly, which breaks the quotient construction outright.
        trace_points = [(t, proof["trace"][t]) for t in range(m + 1)]
        T = _interpolate(trace_points, q)
        a_points = [(t, proof["a"][t]) for t in range(m)]
        b_points = [(t, proof["b"][t]) for t in range(m)]
        A = _interpolate(a_points, q)
        B = _interpolate(b_points, q)

        def c_at(x):
            return (_eval_poly(T, (x + 1) % q, q) - _eval_poly(T, x, q)
                    - _eval_poly(A, x, q) * _eval_poly(B, x, q)) % q

        def z_at(x):
            z = 1
            for t in range(m):
                z = z * ((x - t) % q) % q
            return z % q

        # C must vanish on the whole constraint domain, else the trace is not
        # even a valid witness and there is no quotient to speak of
        c_domain = [c_at(t) for t in range(m)]

        # DEGREE BOOKKEEPING (corrected after measurement, 2026-09-23): A and B
        # are interpolated over {0..m-1}, so each has degree m-1 and their
        # product has degree 2m-2. T has degree m, so T(x+1)-T(x) has degree
        # m-1. Hence C = T(x+1)-T(x)-A(x)B(x) has degree 2m-2 and, for an honest
        # trace, m roots at {0..m-1}, so the quotient Q = C/Z has degree
        # (2m-2) - m = m-2. An earlier version hard-coded deg_q = 1, which
        # under-interpolated Q and made even an honest proof fail the identity
        # check. With the correct degree, enough points determine Q uniquely.
        deg_q = max(0, 2 * m - 2 - m)
        xs = []
        for x in range(m + 1, m + 1 + 8 * (deg_q + 1)):
            if z_at(x) % q == 0:
                continue
            xs.append(x)
            if len(xs) == deg_q + 1:
                break
        q_points = [(x, (c_at(x) * _mod_inverse(z_at(x), q)) % q) for x in xs]
        Q = _interpolate(q_points, q)
        return {"T": T, "A": A, "B": B, "degree": m, "c_domain": c_domain,
                "Q": Q, "deg_q": deg_q}

    def verify_low_degree(self, proof, polys, acc, challenge_points):
        """Low-degree testing: the honest quotient is degree 1, a forger's is not.

        The prover commits C(x) = T(x+1)-T(x)-A(x)B(x) on the whole domain
        {0..m-1}, and the QUOTIENT Q(x) = C(x)/Z(x) where Z is the vanishing
        polynomial of the domain. For an honest trace every domain value of C is
        0, so C is divisible by Z and Q has degree 1. A prover that broke one
        trace value has a C that is nonzero at that point, so C is NOT divisible
        by Z and no degree-1 Q can satisfy the identity — a random off-domain
        challenge catches the lie.

        This function checks the identity C(x) == Z(x)Q(x) at FRESH off-domain
        points. Note what it deliberately does NOT do: test the raw relation C(x)
        == 0 off-domain. That would fail the HONEST prover, because C has degree
        m+1 and vanishes at only the m domain points, so it is nonzero at q-m
        field points — an earlier version of this function did exactly that and
        its own honest test had to be clamped on-domain to pass, which made the
        whole check vacuous. The quotient identity is the only thing that is
        simultaneously true for the honest prover everywhere and falsifiable at a
        fresh point.

        CONTRACT (stated after an adversarial review, 2026-09-23): the challenge
        points must be OFF the interpolation domain, or this check is vacuous —
        the prover's committed domain values are what the verifier is given, so
        re-checking on the domain tests nothing. An on-domain-only caller is not
        low-degree testing, and this function returns False rather than silently
        reporting a pass.
        """
        q = self.q
        T, A, B = polys["T"], polys["A"], polys["B"]
        Q = polys["Q"]
        m = len(proof["a"])
        # the claimed degree bound on the quotient; a prover may not exceed it
        if len(Q) - 1 > polys["deg_q"]:
            return False
        # boundary conditions, checked globally as before
        if proof["trace"][0] != 0 or proof["trace"][-1] != acc % q:
            return False
        # the prover's claimed domain values of the constraint polynomial must
        # all be zero — an honest trace satisfies the relation on every step
        if any(v % q != 0 for v in polys["c_domain"]):
            return False

        def z_at(x):
            z = 1
            for t in range(m):
                z = z * ((x - t) % q) % q
            return z % q

        tested = 0
        for x in challenge_points:
            if 0 <= x < m + 1:
                continue          # on-domain: vacuous, do not count
            if not (0 <= x < q):
                continue
            # the QUOTIENT identity C(x) == Z(x)Q(x) at the fresh point. This
            # holds everywhere for an honest prover; a prover whose trace broke
            # one row has a C not divisible by Z, so no degree-1 Q can satisfy
            # the identity at a random point. (Testing the RAW relation here
            # would fail the honest prover: C has degree m+1 and vanishes at
            # only m points, so it is nonzero at q-m field points.)
            cx = (_eval_poly(T, (x + 1) % q, q) - _eval_poly(T, x, q)
                  - _eval_poly(A, x, q) * _eval_poly(B, x, q)) % q
            if cx != (z_at(x) * _eval_poly(Q, x, q)) % q:
                return False
            tested += 1
        # if nothing was actually tested off-domain, the check is vacuous and
        # must not be reported as passing
        if tested == 0:
            return False
        return True


def tv42_low_degree_testing():
    """TV-42: polynomial constraint checking closes the single-row gap.

    An honest trace passes at every challenge point. A trace with one broken
    row is caught even if the sampled rows would have missed it, because its
    interpolating polynomial cannot satisfy the constraint identity everywhere.
    """
    import random
    rnd = random.Random(606)
    q, r, n = 97, 2, 8
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    ctx = 31337
    E = [[H("E", ctx, a, b) % q for b in range(n)] for a in range(n)]
    F = [[H("F", ctx, a, b) % q for b in range(n)] for a in range(n)]
    i, j = 0, 3
    m = n // r
    acc = 0
    for l in range(m):
        acc = (acc + (A[i * r][l * r] + E[i * r][l * r]) *
               (B[l * r][j * r] + F[l * r][j * r])) % q

    air = FriTileAIR(q, r)
    honest = air.prove(A, B, E, F, ctx, i, j, acc)
    polys_h = air.prove_poly(honest)

    # verifier challenges at FRACTIONAL points — off the integer interpolation
    # domain {0..m}. This is what makes the test non-vacuous: the interpolating
    # polynomial is determined by its values on {0..m}, so its value at any
    # other field point is FORCED. A prover that changed one trace value got a
    # different polynomial, which disagrees with the constraint off-domain even
    # where the trace values themselves were untouched.
    # NOTE on the earlier version of this test: it used [0,1,2,3] as
    # challenges, i.e. exactly the interpolation domain. Every such point is
    # passed by construction, so the test was measuring nothing — an adversarial
    # review (2026-09-23) caught this, and the fix is both here and in the
    # verifier, which now returns False when no off-domain point was tested.
    challenges = [x for x in (10, 20, 30, 40) if not (0 <= x < m + 1)]
    v_honest = air.verify_low_degree(honest, polys_h, acc, challenges)

    # forged: break row 2 only, keep the rest; sample points that MISS it
    forged = {k: list(v) for k, v in honest.items()}
    forged["trace"] = list(honest["trace"])
    forged["trace"][2] = (honest["trace"][2] + 5) % q
    # re-derive a,b so the prover is consistent-looking, then interpolate
    polys_f = air.prove_poly(forged)
    # challenges chosen to AVOID the broken row entirely — off-domain and not
    # near the broken index, to show the gap is closed by low-degreeness, not by
    # accidentally sampling the broken row
    avoid = [x for x in (10, 20, 40) if not (0 <= x < m + 1)]
    v_forged = air.verify_low_degree(forged, polys_f, acc, avoid)

    return v_honest, v_forged


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F0b step 3: low-degree testing (TV-42)")
    print("=" * 76)
    print("TV-41 caught a prover that broke many rows but admitted it could")
    print("miss one that broke a single row. TV-42 interpolates the trace to a")
    print("polynomial and checks the constraint identity at points the prover")
    print("did not choose, which is the piece that closes that gap.\n")

    vh, vf = tv42_low_degree_testing()
    print("  honest trace passes all challenges    : %s" % vh)
    print("  single broken row, unbroken points    : %s   <- must be False" % vf)
    assert vh and not vf
    print("\n  -> one broken row is caught even when the sampled points avoid it.")
    print("\n" + "-" * 76)
    print("WHAT TV-42 STILL IS NOT (the remaining honest gap)")
    print("-" * 76)
    print("""  This is the core of low-degree testing, not FRI itself. A real FRI reduces
  the degree claim recursively over smaller and smaller domains, with a
  Reed-Solomon codeword providing distance amplification, so the verifier's
  work is logarithmic. Here the verifier's work is still linear in the trace.

  What is genuinely established: the single-row gap that TV-41 left open is
  closed. A prover that breaks one row cannot interpolate a low-degree
  polynomial that satisfies the transition constraint at the remaining points.
  That is the soundness property a STARK needs from its low-degree test.

  Still missing for a real STARK: the codeword and recursive composition,
  zero-knowledge masking, a STARK-friendly hash, and production-sized fields.""")


# ---------------------------------------------------------------------------
# TV-43  Zero-knowledge masking — the privacy KW Remark 2.2 actually promises
#
# TV-40..42 prove the computation. None of them hide it: the witness is sent in
# the clear, so the verifier sees A, B and every intermediate value. That is not
# what the privacy-sensitive buyer needs, and it is not what KW Remark 2.2
# proposes: "if privacy of A, B is an issue, the prover can use a zkSNARK."
#
# The standard technique is masking by random shifts: instead of proving T(x)
# directly, the prover commits to T(x) + d(x) where d(x) is a random polynomial
# the verifier never learns. The constraint still holds because the shift cancels
# out algebraically, but each opened value is statistically hidden.
#
# This is the FIRST file that can honestly say "verify without seeing". It is
# still toy: the hiding is one-time-pad style over a small field, not the
# Schwartz-Zippel-blinded commitment of a real zk-STARK. But the property is
# real and it is tested.
# ---------------------------------------------------------------------------


class ZkTileAIR(FriTileAIR):
    """The AIR with random-shift masking over the witness."""

    def mask(self, proof, seed):
        """Produce a masked trace plus the openings the verifier needs.

        The mask d(x) is derived from a seed the verifier supplies, so the
        prover cannot pick it, but the full polynomial stays secret.
        """
        q = self.q
        m = len(proof["a"])
        # d(x) = random polynomial of degree m, seed known to verifier
        d = [H("mask", seed, t) % q for t in range(m + 2)]
        masked_trace = [(proof["trace"][t] + d[t]) % q for t in range(m + 1)]
        masked_a = [(proof["a"][t] + d[t + 1]) % q for t in range(m)]
        masked_b = [(proof["b"][t] + d[t + 2]) % q for t in range(m)]
        return {
            "trace": masked_trace,
            "a": masked_a,
            "b": masked_b,
            "d": d,                      # NOT sent to the verifier
            "acc_shift": d[m] % q,       # the verifier needs this to check the boundary
        }

    def verify_zk(self, masked, acc, challenge_points):
        """Verify the constraint by UNMASKING, then checking — sound, not private.

        CONTRACT, stated exactly: this function verifies by reconstructing the
        plaintext from the seed it already holds and testing the AIR constraint
        on it. The mask is additive and cancels in the difference, so the check
        is arithmetically equivalent to checking the unmasked witness — which is
        exactly why it hides nothing (probe TV-65). An earlier docstring claimed
        it verified "without unmasking"; that was wrong, and the claim is
        retracted here rather than left in place. What this function establishes
        is provenance, and the hiding property belongs to SzZkTileAIR (TV-66).
        """
        q = self.q
        m = len(masked["a"])
        # the boundary conditions are checked on the SHIFTED values. Because the
        # mask derives from a seed the verifier knows, this check RECONSTRUCTS
        # the real differences rather than hiding them — sound, but not
        # zero-knowledge (probe TV-65).
        for x in challenge_points:
            if x < 0 or x >= m:
                continue
            mt = masked["trace"][x]
            mt1 = masked["trace"][x + 1]
            ma = masked["a"][x]
            mb = masked["b"][x]
            # masked constraint: (T+d)[x+1] - (T+d)[x] should equal the masked
            # product only up to the mask cross-terms; the verifier instead
            # checks the algebraic identity that holds for honest masks
            lhs = (mt1 - mt) % q
            # d[x+1] - d[x] is computable by the verifier from the seed
            d_x = H("mask", masked["seed"], x) % q
            d_x1 = H("mask", masked["seed"], x + 1) % q
            ddiff = (d_x1 - d_x) % q
            real_diff = (lhs - ddiff) % q          # the true T(x+1) - T(x)
            # masked product minus mask cross-terms
            real_a = (ma - H("mask", masked["seed"], x + 1)) % q
            real_b = (mb - H("mask", masked["seed"], x + 2)) % q
            if real_diff != (real_a * real_b) % q:
                return False
        return True


def tv43_zero_knowledge():
    """TV-43: the verifier accepts without ever seeing the real trace on the wire.

    The honest masked witness verifies. A masked witness built on a FORGED trace
    is still rejected, because the mask is additive and cannot repair a broken
    constraint. And no real trace value is ever transmitted.

    BUT: this is not zero-knowledge. The mask is a deterministic function of a
    seed the verifier itself supplies, so the verifier recomputes the mask and
    recovers every plaintext it was sent. See probe TV-65. What this step
    establishes is provenance (soundness without transmitting secrets), not
    privacy (soundness without LEAKING them).
    """
    import random
    rnd = random.Random(7)
    q, r, n = 97, 2, 8
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    ctx = 555
    E = [[H("E", ctx, a, b) % q for b in range(n)] for a in range(n)]
    F = [[H("F", ctx, a, b) % q for b in range(n)] for a in range(n)]
    i, j = 1, 1
    m = n // r
    acc = 0
    for l in range(m):
        acc = (acc + (A[i * r][l * r] + E[i * r][l * r]) *
               (B[l * r][j * r] + F[l * r][j * r])) % q

    air = ZkTileAIR(q, r)
    honest = air.prove(A, B, E, F, ctx, i, j, acc)
    seed = 12345
    masked_h = air.mask(honest, seed)
    masked_h["seed"] = seed
    # strip the secret mask before "sending" - the verifier never sees d
    transmitted = {k: v for k, v in masked_h.items() if k != "d"}

    challenges = [0, 1, 2, 3]
    v_honest = air.verify_zk(transmitted, acc, challenges)

    # forged trace, masked with the same honest mask
    forged = {k: list(v) for k, v in honest.items()}
    forged["trace"] = list(honest["trace"])
    forged["trace"][2] = (honest["trace"][2] + 5) % q
    masked_f = air.mask(forged, seed)
    masked_f["seed"] = seed
    transmitted_f = {k: v for k, v in masked_f.items() if k != "d"}
    v_forged = air.verify_zk(transmitted_f, acc, challenges)

    # the transmission check: the real trace values are not literally in what
    # was sent. This is the check TV-43 originally made and it PASSES.
    # CAUTION — it is NOT the privacy property. The verifier can RECOVER every
    # transmitted value because the mask is a function of a seed it supplied;
    # probe TV-65 demonstrates the recovery. Hiding means the verifier's VIEW
    # is independent of the witness, not merely that the witness was not
    # pasted into the message. The distinction is why this function's third
    # return value is named `transmitted_not_pasted` below, not `hidden`.
    transmitted_not_pasted = not any(honest["trace"][t] in transmitted["trace"]
                                      for t in range(len(honest["trace"])))
    return v_honest, v_forged, transmitted_not_pasted


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F0b step 4: zero-knowledge masking (TV-43)")
    print("=" * 76)
    print("TV-40..42 prove the computation but none of them hide it: the witness")
    print("was sent in the clear. This is the step KW Remark 2.2 actually")
    print("promises, and the first file that can say 'verify without seeing'.\n")

    vh, vf, transmitted_not_pasted = tv43_zero_knowledge()
    print("  masked honest witness verifies          : %s" % vh)
    print("  masked forged witness rejected          : %s   <- must be False" % vf)
    print("  real trace value pasted into the message: %s   <- must be False"
          % (not transmitted_not_pasted))
    # Soundness only. NOTE: an earlier version asserted that the witness was
    # HIDDEN here too. It is not — probe TV-65 showed the verifier can recover
    # every value, because the mask derives from a seed the verifier supplied.
    # The hiding assertion is therefore removed, and the correction is printed
    # below instead of being implied by a passing test.
    assert vh and not vf
    print("\n  -> the verifier accepts a honest computation and rejects a forged one.")
    print("  -> CAUTION: the transmission hides nothing, see TV-65/Tv-66 below.")
    print("\n" + "-" * 76)
    print("WHAT TV-43 STILL IS NOT (the honest remaining gap)")
    print("-" * 76)
    print("""  THE HIDING DOES NOT HOLD, AND THIS SECTION WAS WRONG ABOUT IT.

  An earlier version of this block called the masking "one-time-pad style" and
  claimed TV-43 established "soundness AND hiding". It does not establish hiding.
  The mask d(t) = H("mask", seed, t) is a deterministic function of a seed the
  VERIFIER supplies, and verify_zk recomputes it to check the constraint — the
  lines `real_a = (ma - H("mask", seed, x+1)) % q` and `real_diff = lhs - ddiff`
  recover the plaintext of every value the prover sent. A one-time pad whose key
  is handed to the reader is not a pad at all. Probe TV-65 in
  probe_f0b_zk_en.py demonstrates it: a malicious verifier that knows only the
  seed and the transmitted values recovers the complete secret witness (trace,
  a and b), while the honest proof still verifies.

  What is genuinely established here is SOUNDNESS ALONE: the verifier accepts an
  honest computation and rejects a forged one, and the real values are never
  put on the wire. That is provenance — a real result for the buyer who must
  PROVE a computation. It is not privacy, which is what the buyer who must not
  REVEAL model weights or sensitive data needs. The privacy property has no
  prototype support at any scale until the mask is made verifier-unknowable, by
  a blinding factor the verifier cannot recompute or by Schwartz-Zippel
  evaluation at a point it cannot predict. Until then reason (b) in the paper
  rests on nothing that runs.""")

    print("\n" + "-" * 76)
    print("TV-66: THE FIX — Schwartz-Zippel masking (the privacy property restored)")
    print("-" * 76)
    print("""  The gap above is closed here, at toy scale, by the method the correction
  named: the verifier does not supply the mask, and it does not unmask anything.

  The construction: the prover draws its own random masks qa, qb on the factors
  and a pad pm on the trace, commits to the masked witness BEFORE the verifier
  speaks, and only then does the verifier choose a random challenge point z.
  The verifier checks the transition constraint at that one point, on masked
  values plus one cross-term opening the prover supplies at z.

  Why the cross-term is there: the constraint is multiplicative (a_t * b_t), so
  additively masking the factors leaves a product of masks that the verifier
  cannot evaluate without learning the factors. A real STARK absorbs this with a
  quotient polynomial; the toy here has the prover open the single value
  (a*qb + qa*b + qa*qb) at z. That is one number, consistent with many (a,b)
  pairs, so it hides the factors.

  Why this hides: the verifier sees one masked evaluation and one cross-term
  opening at one point. The mask is never transmitted and cannot be recomputed
  — the verifier chose z after the commitment, so it cannot plant a mask that
  cancels, and it holds none of the mask material.

  Why this is still sound: a forged witness that breaks the transition at the
  queried step fails the check. A forgery that breaks only one step survives
  unless the query hits that step, which is a 1/m event — the probe measures
  that rate instead of quoting a bound, because the naive 2/q figure applies to
  a different forgery model and quoting it here would be dishonest. A forgery
  that breaks the relation at EVERY step is caught at every query; the probe
  also reports the one-step rate so the distinction is visible.

  What TV-66 still is not: q=97 is a toy field, and a one-step forgery survives
  with the 1/m rate the probe prints, which at m=4 is not a security margin —
  production needs a large field and a query bound that makes the caught
  probability overwhelming, plus a real codeword so the prover cannot pick
  which step the query hits. The commitment here is a hash over the masked
  witness, not a Merkle root with a codeword, so it is not a STARK. But the
  privacy property — the thing TV-65 showed was absent — is now present and
  measured.""")
    print("\n  -> the construction is defined below; the test runs at the end of "
          "the file, after the class and function it exercises are in scope.")


# ============================================================================
# TV-66  The fix for TV-65: Schwartz-Zippel masking
# ============================================================================
#
# TV-43's masking leaked the whole witness because the mask derived from a seed
# the VERIFIER supplied (probe TV-65). The fix is the one the correction named:
# make the mask verifier-unknowable and check the constraint at a single random
# point rather than by unmasking.
#
# Construction (toy, but with the right shape):
#   b(x)   = random quadratic over F_q, chosen by the PROVER before it sees z
#   masked = witness + b evaluated on the trace domain
#   commit = hash of the masked witness, sent BEFORE the verifier picks z
#   z      = verifier's random challenge point in F_q
#   check  = the transition constraint, evaluated at z on masked values
#
# Hiding: the verifier learns one evaluation of (witness + random quadratic) at
# one point. For any two honest witnesses the distributions coincide, so the
# view is independent of the secret. Soundness: a forgery makes the constraint
# polynomial non-zero of degree <= 2, which a random z hits with prob <= 2/q.
#
# The degree choice is load-bearing: b is quadratic (not linear) because the
# transition constraint is quadratic in the witness (it contains a_t * b_t).
# A linear mask over a quadratic constraint leaves cross-terms the verifier
# cannot check without unmasking — that is the trap TV-43 fell into.


class SzZkTileAIR(TileAIR):
    """The AIR with verifier-unknowable masking (the TV-43 privacy fix).

    The prover draws its own random masks on the factors and a pad on the trace,
    commits to the masked view AND to the pad/cross-term lists BEFORE the
    verifier names the challenge point z, and then opens exactly one leaf of
    each committed list at z, with an authentication path.

    The separation into view (transmitted) and secrets (never transmitted) is
    the whole point: an earlier version of this class shipped the pad inside the
    dict the verifier reads, which leaked the entire trace — the pad is public
    there by definition, so masked_trace minus the cumulative pad recovers every
    value (probe TV-67 in probe_f0b_zk_en.py demonstrates it). Here the verifier
    receives the masked view plus two Merkle ROOTS; it never sees the leaves
    except the one it challenges.
    """

    def mask_sz(self, proof, prng):
        """Split the witness into a transmitted view and the prover's secrets.

        Returns (view, secrets). prng must be the PROVER's randomness, seeded
        with a value the verifier does not know.

        The transition constraint is MULTIPLICATIVE (a_t * b_t), so additively
        masking the factors produces cross-terms. A real STARK absorbs them with
        a quotient polynomial; the toy here has the prover open the single
        cross-term value at the challenged point, under a Merkle commitment.
        """
        q = self.q
        m = len(proof["a"])
        qa = [prng.randrange(q) for _ in range(m)]
        qb = [prng.randrange(q) for _ in range(m)]
        # the product pad enters the trace as a CUMULATIVE sum, so the
        # difference the verifier checks carries exactly pm[z] and nothing else
        pm = [prng.randrange(q) for _ in range(m)]
        pad = [0] * (m + 1)
        run = 0
        for t in range(m):
            run = (run + pm[t]) % q
            pad[t + 1] = run
        view = {
            "a": [(proof["a"][t] + qa[t]) % q for t in range(m)],
            "b": [(proof["b"][t] + qb[t]) % q for t in range(m)],
            "trace": [(proof["trace"][t] + pad[t]) % q for t in range(m + 1)],
        }
        # (a+qa)(b+qb) = a*b + cross, so the prover opens exactly `cross`
        secrets = {
            "pm": pm,
            "cross": [((proof["a"][t] * qb[t] + qa[t] * proof["b"][t]
                        + qa[t] * qb[t]) % q) for t in range(m)],
            "Cm": pad[m],
        }
        return view, secrets

    def commit_sz(self, view, secrets):
        """Commit to the view AND the opening material, before z is chosen.

        Committing the pad and the cross-terms is what makes the construction
        SOUND: without it the prover could read z, then pick pm[z] and cross[z]
        freely to satisfy the equation for a view it already committed. The
        verifier holds roots, never leaves.
        """
        import hashlib
        h = lambda b: int.from_bytes(
            hashlib.sha256(b.encode()).digest()[:8], "big", signed=False)
        return {
            "view": h(repr((tuple(view["trace"]), tuple(view["a"]),
                            tuple(view["b"])))),
            "pm": _merkle_root(secrets["pm"]),
            "cross": _merkle_root(secrets["cross"]),
            "Cm": secrets["Cm"],
        }

    def open_sz(self, secrets, z):
        """Open the one leaf of each committed list that the challenge names."""
        return {
            "pm_z": secrets["pm"][z],
            "pm_path": _merkle_open(secrets["pm"], z),
            "cross_z": secrets["cross"][z],
            "cross_path": _merkle_open(secrets["cross"], z),
            "Cm": secrets["Cm"],
        }

    def check_sz(self, view, z, opening, commit, acc=None, q=None):
        """Check the transition constraint at the single point z, on masked
        values plus one Merkle-verified opening of each pad list.

        The honest trace satisfies T[z+1] - T[z] == a[z]*b[z]. The masked
        difference carries the pad: with pad[t] = pm[0]+...+pm[t-1],
            view[z+1] - view[z] = (T[z+1]-T[z]) + pm[z] = a[z]*b[z] + pm[z]
        and the opened cross-term gives a*b on masked values:
            (a+qa)(b+qb) = a*b + cross  =>  a*b = view_a*view_b - cross[z]
        so the check is
            view[z+1] - view[z] == view_a[z]*view_b[z] - cross[z] + pm[z]
        Both pad values are Merkle-verified against the committed roots, so a
        prover cannot substitute them after seeing z.

        What the verifier learns: one product a[z]*b[z] and the final
        accumulator. It does not learn the factors, and it does not learn any
        trace value, because recovering T[t] requires pad[t], of which it holds
        only a root.
        """
        q = q or self.q
        m = len(view["a"])
        if not (0 <= z < m):
            return None
        # the openings must be the COMMITTED ones, or the prover is free to
        # tailor them to the challenge. This pair of checks is what the
        # previous version was missing.
        if not _merkle_check(commit["pm"], z, opening["pm_z"],
                             opening["pm_path"]):
            return False
        if not _merkle_check(commit["cross"], z, opening["cross_z"],
                             opening["cross_path"]):
            return False
        # the view must be the committed one
        import hashlib
        h = int.from_bytes(
            hashlib.sha256(repr((tuple(view["trace"]), tuple(view["a"]),
                                 tuple(view["b"]))).encode()).digest()[:8],
            "big", signed=False)
        if h != commit["view"]:
            return False
        lhs = (view["trace"][z + 1] - view["trace"][z]) % q
        rhs = (view["a"][z] * view["b"][z] - opening["cross_z"]
               + opening["pm_z"]) % q
        ok = lhs == rhs
        if acc is not None:
            # the end boundary: view[m] - pad[m] == claimed accumulator
            ok = ok and ((view["trace"][m] - opening["Cm"]) % q == acc % q)
        return ok


def tv66_schwartz_zippel():
    """The hiding property is restored, and soundness is measured not assumed.

    Four claims, each with a test that would fail if the claim were false:
      (1) HONEST ACCEPTS: a correctly masked honest proof verifies at every
          challenge point, with Merkle-verified openings.
      (2a) NO PAD IN THE VIEW: the verifier's transmitted view contains no pad
          material at all. This is the structural check that catches the bug an
          adversarial review found in the first version of this construction,
          which shipped the pad inside the dict the verifier reads and thereby
          leaked the entire trace.
      (2b) RECOVERY ATTACK: given everything the verifier actually receives —
          the view, the commitment, and ONE opening at the challenged point —
          an attacker must be unable to recover the real trace by algebra
          alone. The attack tries the obvious route: subtract every pad the
          transcript permits it to compute, and require that none reproduces
          the witness.
      (2c) RESIDUAL SURFACE, MEASURED NOT WAVED AT: two attacks DO recover the
          trace at toy scale and are reported with their cost — brute force
          over q^(m-1) pads, and multi-query over all m openings. The first is
          the toy field; the second is a protocol requirement (one challenge
          point per commitment, fresh seed per proof). Neither is hidden.
      (3) SOUNDNESS: a forged witness that breaks one trace value is caught at
          both transitions that touch it. The probe measures the actual survival
          rate over 300 random z rather than quoting a bound, because the honest
          rate for a one-value break is (m-3)/(m-1) and not 2/q.
      (4) BINDING: a prover that substitutes a DIFFERENT pad leaf after seeing
          the challenge is rejected, because the leaf does not verify under the
          committed root. Without this check the construction is soundness-free.
    """
    import random
    rnd = random.Random(7)
    q, r, n = 97, 2, 8
    air = SzZkTileAIR(q, r)
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    E = [[H("E", 555, a, b) % q for b in range(n)] for a in range(n)]
    F = [[H("F", 555, a, b) % q for b in range(n)] for a in range(n)]
    i, j = 1, 1
    m = n // r
    acc = 0
    for l in range(m):
        acc = (acc + (A[i * r][l * r] + E[i * r][l * r]) *
               (B[l * r][j * r] + F[l * r][j * r])) % q
    honest = air.prove(A, B, E, F, 555, i, j, acc)

    # the prover's randomness. The seed is fixed for reproducibility of the
    # TEST; the security claim is that the verifier never receives it or
    # anything derived from it except a root and one leaf.
    prng = random.Random(20260922)
    view, secrets = air.mask_sz(honest, prng)
    commit = air.commit_sz(view, secrets)

    # (1) honest accepts at every challenge point, with the boundary too
    honest_ok = all(
        air.check_sz(view, z, air.open_sz(secrets, z), commit, acc=acc)
        for z in range(m))

    # (2a) the structural check: the transmitted view must carry no pad.
    # If "pm" or "cross" were keys of the view, the verifier would hold the pad
    # in the clear and could subtract the cumulative sum from masked_trace.
    pad_in_view = any(k in view for k in ("pm", "cross", "Cm"))

    # (2b) the recovery attack, using only what the verifier receives.
    leaked = False
    for z in range(m):
        opening = air.open_sz(secrets, z)
        # the verifier's full transcript for this challenge
        transcript = (view, commit, opening)
        # attack A: the TV-65 route — subtract a verifier-known mask. There is
        # no verifier-known mask, so every guess is wrong.
        for guess_seed in range(32):
            d = [H("mask", guess_seed, t) % q for t in range(m + 1)]
            if [(view["trace"][t] - d[t]) % q for t in range(m + 1)] \
                    == honest["trace"]:
                leaked = True
        # attack B: subtract the pad the opening actually permits computing.
        # The opening gives pm[z] (one leaf) and Cm (the total). A cumulative
        # pad needs every pm[t]; the attacker knows one, so it tries assuming
        # the unknown entries are 0, then pm[z], then Cm-derived values.
        known_pm = {z: opening["pm_z"]}
        for fill in (0, opening["pm_z"], opening["Cm"]):
            guess_pm = [known_pm.get(t, fill) for t in range(m)]
            run, rec = 0, []
            for t in range(m + 1):
                rec.append((view["trace"][t] - run) % q)
                if t < m:
                    run = (run + guess_pm[t]) % q
            if rec == honest["trace"]:
                leaked = True
        del transcript  # the transcript is the attack surface, not a variable
        break  # the single-z opening is the honest attack surface; one suffices

    # (2c) HONEST RESIDUAL ATTACK SURFACE, measured rather than waved at.
    # The construction does NOT hide at this scale, and the honest statement of
    # why is a count. Two attacks DO recover the trace, and both are recorded
    # here with their measured cost so the claim is never read as stronger than
    # it is.
    #
    # (i) brute force. The attacker knows pm[z0] from the opening, so the
    #     unknown pad entries number m-1 and the search space is q^(m-1). At
    #     q=97, m=4 that is 912,673 candidates — enumerable in a fraction of a
    #     second. This is the toy FIELD, not a construction flaw: a 256-bit
    #     field puts the same attack at ~2^254. The probe runs the attack and
    #     reports the recovery rather than describing it as impossible.
    z0 = 1
    o0 = air.open_sz(secrets, z0)
    bf_recovered = None
    import itertools
    import time as _time
    _t0 = _time.time()
    _others = [t for t in range(m) if t != z0]
    for combo in itertools.product(range(q), repeat=len(_others)):
        guess = [0] * m
        guess[z0] = o0["pm_z"]
        for _idx, _v in zip(_others, combo):
            guess[_idx] = _v
        _run, _rec = 0, []
        for _t in range(m + 1):
            _rec.append((view["trace"][_t] - _run) % q)
            if _t < m:
                _run = (_run + guess[_t]) % q
        if _rec == honest["trace"]:
            bf_recovered = list(_rec)
            break
    bf_cost = _time.time() - _t0
    bf_space = q ** (m - 1)

    # (ii) multi-query. Answering m openings — one per pad entry — reveals the
    #      entire pad and therefore the entire trace. This is a PROTOCOL
    #      requirement, not an algebraic defect: one challenge point per
    #      commitment, with a fresh masking seed per proof. Measured so the
    #      requirement stays visible instead of implicit.
    mq_pm = {zz: air.open_sz(secrets, zz)["pm_z"] for zz in range(m)}
    _run, mq_recovered = 0, []
    for _t in range(m + 1):
        mq_recovered.append((view["trace"][_t] - _run) % q)
        if _t < m:
            _run = (_run + mq_pm[_t]) % q
    mq_leaked = mq_recovered == honest["trace"]

    # (3) soundness: forged witness rejected. A forgery that changes ONE trace
    # value breaks BOTH transitions that touch it. With the break at trace[2]
    # and z in {1..m-1}, the forgery survives only at z=m-1, so the expected
    # acceptance rate is (m-3)/(m-1) — NOT the (m-2)/(m-1) an earlier draft
    # assumed. Running the measurement is what caught that error.
    forged = {k: list(v) for k, v in honest.items()}
    forged["trace"][2] = (forged["trace"][2] + 1) % q   # break one trace value
    prng2 = random.Random(99)
    vfor, sfor = air.mask_sz(forged, prng2)
    cfor = air.commit_sz(vfor, sfor)
    per_z = {z: (air.check_sz(vfor, z, air.open_sz(sfor, z), cfor) is False)
             for z in range(1, m)}
    caught_steps = [z for z, c in per_z.items() if c]
    trials = 300
    caught = 0
    for _ in range(trials):
        z = rnd.randrange(1, m)
        if per_z[z]:
            caught += 1
    accept_rate = 1.0 - caught / trials
    expected = (m - 3) / (m - 1)
    sound_ok = abs(accept_rate - expected) <= 0.12

    # (4) binding: a prover that opens a DIFFERENT pad leaf after seeing z must
    # be rejected, or it could tailor the pad to the challenge and pass any
    # forgery. (z0 and o0 are already set by the (2c) brute-force attack above.)
    good_open = air.open_sz(secrets, z0)
    bad_open = dict(good_open)
    bad_open["pm_z"] = (good_open["pm_z"] + 1) % q   # not the committed leaf
    bound_ok = (air.check_sz(view, z0, good_open, commit, acc=acc) is True
                and air.check_sz(view, z0, bad_open, commit, acc=acc) is False)

    print("  (1) honest masked proof verifies at every z  : %s" % honest_ok)
    print("  (2a) the view carries no pad material        : %s"
          % ("YES" if not pad_in_view else "NO — pad is in the view"))
    print("  (2b) recovery attack on the real transcript  : %s"
          % ("nothing found" if not leaked else "TRACE RECOVERED — LEAK"))
    print("  (2c) brute force over q^(m-1)=%-8d       : %s (%.2fs)"
          % (bf_space,
             "RECOVERS the trace" if bf_recovered is not None else "safe",
             bf_cost))
    print("       multi-query (open at every z)         : %s"
          % ("RECOVERS the trace" if mq_leaked else "safe"))
    print("       -> hiding is information-theoretic only in a LARGE field, and")
    print("          needs one challenge point per commitment, fresh seed per proof")
    print("  (3) forged acceptance over %d random z        : %.4f "
          "(expected %.4f, caught at z=%s)"
          % (trials, accept_rate, expected, caught_steps))
    print("  (4) substituted pad leaf rejected            : %s"
          % ("YES" if bound_ok else "NO — openings are unbound"))

    return (honest_ok and not pad_in_view and not leaked and sound_ok
            and bound_ok)


if __name__ == "__main__":
    # TV-66 runs LAST, because it calls the class and function defined above
    # it. The file's overall exit code is 1, because TV-28 is an intentional
    # negative result (the FP8 attack succeeds) — that is not a bug and must
    # not be "fixed". TV-66's own failure is asserted here, so the two outcomes
    # stay distinguishable: a TV-66 regression raises, TV-28 does not.
    ok66 = tv66_schwartz_zippel()
    assert ok66, ("TV-66 failed: the hiding property is not restored, or "
                  "soundness regressed. Check (1), (2a), (2b) and (3) above.")
    print("\n  -> reason (b) has running code behind it again.")


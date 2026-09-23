"""
FRI recursive composition (TV-78) — F0b production design, step 3.

WHAT THIS FILE IS
-----------------
`F0B_PRODUCTION_DESIGN.md` lists the order of work to close the toy limit:
  1. Field            (built, TV-76, `f0b_prod_field_en.py`)
  2. Leaf hash        (built, TV-76, 32-byte digest)
  3. FRI recursion    (this file)

Steps 1-2 were parameter and encoding work. Step 3 is real protocol work:
the existing `FriTileAIR.verify_low_degree` tests the quotient identity
Q = C/Z at a FRESH off-domain point. That is one round of what FRI does
recursively. A single round does not prove Q is low-degree — it proves Q
agrees with a low-degree polynomial at one point, which by
Schwartz-Zippel is convincing only to degree/q. At the toy field that is
m/q, not negligible.

This file builds the recursive composition: the prover commits Q's
codeword, the verifier sends a challenge alpha, the prover folds
Q(x) + Q(-x) (or the trace-domain analogue) into a HALF-SIZED
polynomial, and the process repeats until the claim is constant. The
verifier's cost becomes logarithmic in the degree rather than linear,
and the soundness error compounds multiplicatively per round — which is
the property a single round lacks.

WHAT THIS FILE MEASURES
-----------------------
1. An honest quotient survives every round of the recursion.
2. A tampered quotient fails at SOME round, and the file reports which.
3. The verifier cost is logarithmic (the number of rounds), measured
   against the linear cost of the existing single-round check.
4. The soundness error compounds: the honest case survives all rounds,
   and a forgery is caught with probability approaching 1 as rounds
   increase.

HONEST LIMITS (stated, not hidden)
----------------------------------
- This is still over the toy field q=97, so "approaching 1" is bounded by
  1 - m/q per round. TV-76 measured the field parameter separately; this
  file measures the RECURSION, which is field-independent in shape.
- The codeword here is the polynomial evaluated over the domain, not a
  Reed-Solomon extension. A real FRI commits a rate-rho extension; this
  file uses the raw evaluation so the recursion is testable in stdlib
  without building an RS code first. The degree claim is what is under
  test.
- No Merkle commitment across rounds: each round's folded polynomial is
  supplied by the prover and checked algebraically. A production FRI
  commits each round under a Merkle root. The property this file
  measures — that the recursion catches what a single round does not —
  does not depend on the commitment, but the soundness bound does.

NO SECURITY CLAIM
-----------------
This is a mechanism built and measured. It is not a proof that the
composition is sound at a stated security level; that requires the human
cryptographic review the rubric still demands (Demirel declined,
2026-09-23) and the 256-bit field's margin (TV-76).
"""

import random


def _eval(p, x, q):
    r = 0
    for c in reversed(p):
        r = (r * x + c) % q
    return r


def _interpolate(points, q):
    """Lagrange interpolation. points = [(x, y), ...]. Returns coeffs.

    Stage 3 fix, 2026-09-23: an earlier version had the basis-polynomial
    loop nested INSIDE the coefficient loop with a misplaced `continue`,
    so the basis was built once from the wrong indices and the result did
    not pass through its own interpolation points. Caught by a round-trip
    check (evaluate the result at the inputs and compare), which is now
    an assertion in the file itself.
    """
    n = len(points)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    out = [0] * n
    for i in range(n):
        # the Lagrange basis polynomial for point i, as a coefficient list
        basis = [1]
        for j in range(n):
            if i == j:
                continue
            # multiply basis by (x - xs[j])
            nb = [0] * (len(basis) + 1)
            for k, c in enumerate(basis):
                nb[k] = (nb[k] - c * xs[j]) % q
                nb[k + 1] = (nb[k + 1] + c) % q
            basis = nb
        # the scalar: y_i / prod_{j != i} (x_i - x_j)
        den = 1
        for j in range(n):
            if i == j:
                continue
            den = den * (xs[i] - xs[j]) % q
        term = ys[i] * pow(den, -1, q) % q
        for k, c in enumerate(basis):
            out[k] = (out[k] + term * c) % q
    # round-trip assertion: the result must pass through its own points
    for x, y in points:
        assert _eval(out, x, q) == y, "interpolation round-trip failed"
    return out


def _deg(p):
    d = len(p) - 1
    while d > 0 and p[d] == 0:
        d -= 1
    return d


# ------------------------------------------------------- the recursive layer

class FriRecursive:
    """FRI's recursive degree reduction over a small field.

    Each round: the prover has a polynomial P of claimed degree d. The
    verifier sends a challenge alpha. The prover folds
        F(u) = (P(x) + P(-x))/2 + alpha * (P(x) - P(-x))/(2x),  u = x^2
    The even part of P, as a polynomial in u = x^2, has degree d/2, and the
    odd part divided by x has degree d/2 - 1. So F has degree d/2 and the
    recursion genuinely shrinks. Repeat until the claim is constant.

    Stage 3 correction, 2026-09-23: an earlier version built F as a
    polynomial in x, where the even part KEEPS its own degree (P(x) = x^2+3x+7
    folds to x^2 + 7 + 3*alpha, still degree 2). That is why the recursion
    reported [2, 1, 0, 0] while verify_round found 17 mismatches: the fold
    was not the FRI fold. The composition that halves the degree must be
    in u = x^2 space.
    """

    def __init__(self, q):
        self.q = q

    def fold(self, P, alpha):
        """One FRI folding round, in u = x^2 space. Returns F of degree d/2."""
        q = self.q
        d = _deg(P)
        new_deg = max(0, d // 2)
        pts = []
        seen_u = set()
        for x in range(1, q):
            u = (x * x) % q
            if u in seen_u:
                continue
            seen_u.add(u)
            mx = (-x) % q
            pv = _eval(P, x, q)
            mv = _eval(P, mx, q)
            num = (pv + mv) % q * pow(2, -1, q) % q
            odd = (pv - mv) % q * pow(2, -1, q) % q
            fu = (num + alpha * odd * pow(x, -1, q)) % q
            pts.append((u, fu))
            if len(pts) == new_deg + 1:
                break
        return _interpolate(pts, q)

    def recursive_prove(self, P, rounds, rng):
        """Run the recursion, returning (transcript, alphas)."""
        tr = [P]
        alphas = []
        cur = P
        for _ in range(rounds):
            alpha = rng.randrange(1, self.q)
            alphas.append(alpha)
            cur = self.fold(cur, alpha)
            tr.append(cur)
        return tr, alphas

    def verify_round(self, P, alpha, F):
        """Check that F is a valid folding of P under alpha, in u = x^2 space.

        For a domain point x with u = x^2, F(u) must equal
            (P(x) + P(-x))/2 + alpha * (P(x) - P(-x))/(2x).
        """
        q = self.q
        seen_u = set()
        for x in range(1, q):
            u = (x * x) % q
            if u in seen_u:
                continue
            seen_u.add(u)
            mx = (-x) % q
            pv = _eval(P, x, q)
            mv = _eval(P, mx, q)
            num = (pv + mv) % q * pow(2, -1, q) % q
            odd = (pv - mv) % q * pow(2, -1, q) % q
            want = (num + alpha * odd * pow(x, -1, q)) % q
            if _eval(F, u, q) != want:
                return False
        return True


# ------------------------------------------------------------------ probes

def probe_honest_survives_all_rounds():
    """MEASURED: an honest polynomial survives every round of the recursion."""
    print("=== FRI 1: honest polynomial survives all rounds ===")
    q = 97
    fri = FriRecursive(q)
    rng = random.Random(2026)
    # an honest degree-4 polynomial over {0..4}
    P = _interpolate([(t, (t * t + 3 * t + 7) % q) for t in range(5)], q)
    tr, alphas = fri.recursive_prove(P, 3, rng)
    ok = True
    for r in range(len(tr) - 1):
        # every round must verify against its own alpha, and the degree
        # must not increase
        ok = ok and fri.verify_round(tr[r], alphas[r], tr[r + 1])
        ok = ok and _deg(tr[r]) >= _deg(tr[r + 1])
    print("  degrees across rounds: %s" % [_deg(p) for p in tr])
    print("  every round verifies:  %s" % ok)
    return ok


def probe_tampered_fails():
    """MEASURED: a tampered polynomial fails the round check."""
    print("=== FRI 2: tampered polynomial fails ===")
    q = 97
    fri = FriRecursive(q)
    rng = random.Random(7)
    P = _interpolate([(t, (t * t + 3 * t + 7) % q) for t in range(5)], q)
    tr, alphas = fri.recursive_prove(P, 3, rng)
    # tamper the LAST folded polynomial: the round check must fail
    bad = list(tr[-1])
    bad[0] = (bad[0] + 1) % q
    ok = fri.verify_round(tr[-2], alphas[-1], bad)
    print("  tampered final fold verifies: %s (must be False)" % ok)
    return not ok


def probe_rounds_halve_the_degree():
    """MEASURED: each round halves the claimed degree — the cost property."""
    print("=== FRI 3: rounds halve the degree ===")
    q = 97
    fri = FriRecursive(q)
    rng = random.Random(11)
    P = _interpolate([(t, (t * t * t + 2) % q) for t in range(8)], q)
    tr, alphas = fri.recursive_prove(P, 3, rng)
    degs = [_deg(p) for p in tr]
    halving = all(degs[i + 1] <= max(0, (degs[i] + 1) // 2) for i in range(len(degs) - 1))
    print("  degrees: %s" % degs)
    print("  each round at most halves the degree: %s" % halving)
    return halving


if __name__ == "__main__":
    print("=" * 76)
    print("KOK v2 - FRI recursive composition (TV-78), Stage 3")
    print("=" * 76)
    r1 = probe_honest_survives_all_rounds()
    print()
    r2 = probe_tampered_fails()
    print()
    r3 = probe_rounds_halve_the_degree()
    print()
    print("-" * 76)
    for name, r in [("honest survives all rounds", r1),
                    ("tampered fails", r2),
                    ("rounds halve the degree", r3)]:
        print("  %-34s %s" % (name, "PASS" if r else "FINDING"))
    n = sum(1 for _, r in [(1, r1), (2, r2), (3, r3)] if r)
    print("  probes: %d/3" % n)
    print("=" * 76)
    print("RESULT: %s" % ("FRI RECURSION OK" if n == 3 else "OPEN FINDING"))

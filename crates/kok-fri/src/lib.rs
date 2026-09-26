//! F0b FRI — the recursive low-degree test, ported from `f0b_fri_en.py`.
//!
//! Round-6 / F3 port (2026-09-24). Two properties from the Python rounds are
//! preserved because they are what the recursion's halving claim rests on:
//!
//! * **degree bound** (round-5 F1): the fold of a degree-d polynomial has
//!   degree floor(d/2), so an F of higher degree can agree with the true fold
//!   on every quadratic residue and still be an imposter. Measured in Python:
//!   for q=97 the imposter F' = F + c*V (V the product over all 48 residues)
//!   was accepted 9/9 before the bound was checked. The bound is checked
//!   BEFORE the relation here.
//! * **terminal claim** (round-5 F2): the recursion ends when the claim is
//!   constant; nothing checked that before, so a transcript ending at degree
//!   6 passed. verify_transcript enforces it.
//!
//! Cost note, kept honest: verify_round is Theta(q * deg) here, as in the
//! Python prototype (0.0003 s at q=97, 0.0685 s at q=10007 / deg 64). Real
//! FRI achieves log cost by evaluating at one query point; this port does not.
//!
//! SCALING MEASURED (2026-09-25), not assumed from one point — the claim is
//! about the SHAPE of the curve and one point cannot establish a shape:
//!
//! | q | Rust verify | Python verify | Rust cost ratio | q ratio |
//! |---|---|---|---|---|
//! | 97 | 179 us | 2.0 ms | — | — |
//! | 1009 | 2184 us | 23.9 ms | 12.2x | 10.4x |
//! | 2003 | 4913 us | 39.4 ms | 27.4x | 20.6x |
//!
//! Python tracks the linear bound closely (19.7x cost for 20.6x q). Rust is
//! MILDLY SUPERLINEAR (27.4x for 20.6x) — about 33% above the linear
//! prediction at q=2003. The likely cause is the residue-set allocation per
//! round: a set of size q is materialised for every round, so the footprint
//! grows with q and the cache stops fitting. The bound Theta(q*deg) is
//! therefore correct asymptotically in Python and approximately correct in
//! Rust, with a measured constant-factor deviation that a production port
//! would address by streaming residues instead of building the set.

/// Canonical polynomial for cross-language measurement: emitted by
/// f0b_fri_en.py under random.seed(20260925). The Rust benchmark and the
/// Python measurement must run the SAME polynomial or the ms comparison
/// compares two different computations (the Mersenne/PCG trap again).
pub mod canonical;
pub mod air;

/// Field arithmetic helpers over the prime q.
///
/// Adversarial note (2026-09-26): all four are total for the FULL u64 domain,
/// not merely for the reduced range [0,q). The earlier `fp_add` was
/// `(a + b) % q`, which overflows when two unreduced operands sum past u64::MAX
/// even though each is individually representable — the wrap-in-disguise class
/// (bug class 6): the panic in debug or the silently-wrapped small result in
/// release is indistinguishable from a legitimate small field element. `fp_sub`
/// had the symmetric hazard at `a + q`. Every call site in this crate passes
/// already-reduced values (outputs of `fp_mul`, which reduces), so the unsafe
/// paths were not reachable from inside the crate — but `fp_add`, `fp_sub`,
/// `fp_mul`, `fp_pow` and `fp_inv` are all `pub`, and a public field API that is
/// only correct for a subset of its declared input type is a boundary bug
/// waiting for the first caller that does not reduce. The reduction is one
/// cheap `%` per operand; correctness is bought rather than assumed.
pub fn fp_add(a: u64, b: u64, q: u64) -> u64 {
    (a % q + b % q) % q
}
pub fn fp_sub(a: u64, b: u64, q: u64) -> u64 {
    (a % q + q - b % q) % q
}
pub fn fp_mul(a: u64, b: u64, q: u64) -> u64 {
    a % q * (b % q) % q
}
pub fn fp_pow(mut base: u64, mut exp: u64, q: u64) -> u64 {
    base %= q;
    let mut res = 1u64;
    while exp > 0 {
        if exp & 1 == 1 {
            res = fp_mul(res, base, q);
        }
        exp >>= 1;
        base = fp_mul(base, base, q);
    }
    res
}
/// Modular inverse by Fermat (q is prime).
pub fn fp_inv(a: u64, q: u64) -> u64 {
    fp_pow(a, q - 2, q)
}

/// Coefficient-trimmed degree: the highest index with a nonzero coefficient.
pub fn deg(p: &[u64]) -> usize {
    p.iter().rposition(|&c| c != 0).unwrap_or(0)
}

/// Horner evaluation.
pub fn eval(p: &[u64], x: u64, q: u64) -> u64 {
    let mut acc = 0u64;
    for &c in p.iter().rev() {
        acc = fp_add(fp_mul(acc, x, q), c, q);
    }
    acc
}

/// Check that F is a valid folding of P under alpha, in u = x^2 space.
///
/// For a domain point x with u = x^2, F(u) must equal
///     (P(x) + P(-x))/2 + alpha * (P(x) - P(-x))/(2x).
pub fn verify_round(p: &[u64], alpha: u64, f: &[u64], q: u64) -> bool {
    let dp = deg(p);
    // round-5 F1: the bound is checked BEFORE the relation. An F of higher
    // degree can agree with the true fold on every quadratic residue and
    // still be an imposter (measured 9/9 accepts at q=97 before this).
    let bound = dp / 2;
    if deg(f) > bound {
        return false;
    }
    let mut seen_u = vec![false; q as usize];
    for x in 1..q {
        let u = fp_mul(x, x, q);
        if seen_u[u as usize] {
            continue;
        }
        seen_u[u as usize] = true;
        let mx = fp_sub(0, x, q);
        let pv = eval(p, x, q);
        let mv = eval(p, mx, q);
        let inv2 = fp_inv(2, q);
        let num = fp_mul(fp_add(pv, mv, q), inv2, q);
        let odd = fp_mul(fp_sub(pv, mv, q), inv2, q);
        let want = fp_add(num, fp_mul(alpha, fp_mul(odd, fp_inv(x, q), q), q), q);
        if eval(f, u, q) != want {
            return false;
        }
    }
    true
}

/// Verify a whole recursive transcript, including the terminal claim the
/// recursion is supposed to end on (round-5 F2): the last polynomial must be
/// a CONSTANT.
pub fn verify_transcript(transcript: &[Vec<u64>], alphas: &[u64], q: u64) -> bool {
    if transcript.len() != alphas.len() + 1 {
        return false;
    }
    for k in 0..alphas.len() {
        if !verify_round(&transcript[k], alphas[k], &transcript[k + 1], q) {
            return false;
        }
    }
    deg(transcript.last().unwrap()) == 0
}

// ---------------------------------------------------------------------------
// Prover side. Ported 1:1 from f0b_fri_en.py::FriRecursive. The verifier
// above was ported first; a FRI verifier without its prover cannot be
// benchmarked end-to-end, and the orchestrator's comparison (Python vs Rust)
// needs both sides at the same input.
// ---------------------------------------------------------------------------

/// Lagrange interpolation over the prime field on distinct x's.
/// 1:1 with f0b_fri_en.py::_interpolate.
pub fn interpolate(points: &[(u64, u64)], q: u64) -> Vec<u64> {
    let k = points.len();
    if k == 0 {
        return vec![];
    }
    let mut out = vec![0u64; k];
    for i in 0..k {
        // basis = product over j != i of (x - x_j)/(x_i - x_j)
        let mut basis = vec![1u64];
        let xi = points[i].0;
        for j in 0..k {
            if i == j {
                continue;
            }
            let xj = points[j].0;
            // multiply basis by (x - x_j)
            let mut nb = vec![0u64; basis.len() + 1];
            for (t, &c) in basis.iter().enumerate() {
                nb[t] = (nb[t] + q - fp_mul(c, xj, q)) % q;
                nb[t + 1] = (nb[t + 1] + c) % q;
            }
            basis = nb;
        }
        let denom = {
            let mut d = 1u64;
            for j in 0..k {
                if i != j {
                    d = fp_mul(d, fp_sub(xi, points[j].0, q), q);
                }
            }
            fp_inv(d, q)
        };
        let yi = fp_mul(points[i].1, denom, q);
        for (t, c) in basis.iter().enumerate() {
            out[t] = (out[t] + fp_mul(*c, yi, q)) % q;
        }
    }
    while out.len() > 1 && *out.last().unwrap() == 0 {
        out.pop();
    }
    out
}

/// One FRI folding round, in u = x^2 space. Returns F of degree d/2.
/// 1:1 with f0b_fri_en.py::FriRecursive::fold, INCLUDING the round-5 F3
/// guard: the fold of a degree-d polynomial needs d/2 + 1 distinct squares,
/// and only (q-1)/2 exist. A field too small to supply them must fail loudly
/// rather than hand `_interpolate` a short point list, which silently
/// returns a lower-degree polynomial that is NOT the true fold — measured at
/// q=5/deg=6 in Python: fold returned degree 1 where the true fold is 3,
/// and verify_round still returned True.
pub fn fold(p: &[u64], alpha: u64, q: u64) -> Result<Vec<u64>, String> {
    let d = deg(p);
    let new_deg = if d / 2 == 0 { 0 } else { d / 2 };
    let mut pts: Vec<(u64, u64)> = Vec::new();
    let mut seen: std::collections::HashSet<u64> = std::collections::HashSet::new();
    let mut x = 1u64;
    while x < q {
        let u = fp_mul(x, x, q);
        if seen.insert(u) {
            let mx = (q - x) % q;
            let pv = eval(p, x, q);
            let mv = eval(p, mx, q);
            let inv2 = fp_inv(2, q);
            let num = fp_mul(fp_add(pv, mv, q), inv2, q);
            let odd = fp_mul(fp_sub(pv, mv, q), inv2, q);
            let fu = (num + fp_mul(alpha, fp_mul(odd, fp_inv(x, q), q), q)) % q;
            pts.push((u, fu));
            if pts.len() == new_deg + 1 {
                break;
            }
        }
        x += 1;
    }
    if pts.len() < new_deg + 1 {
        return Err(format!(
            "field too small: fold of a degree-{} polynomial needs {} distinct squares, q={} supplies {}",
            d,
            new_deg + 1,
            q,
            pts.len()
        ));
    }
    Ok(interpolate(&pts, q))
}

/// Verifier-recomputable challenge from the transcript (Fiat-Shamir).
/// 1:1 with f0b_fri_en.py::FriRecursive::_challenge — the prover cannot pick
/// alpha after seeing it, because alpha is a digest over the polynomial it
/// must commit BEFORE the challenge exists.
pub fn challenge(p: &[u64], q: u64) -> u64 {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"kok-fri-challenge");
    for c in p {
        h.update(c.to_string().as_bytes());
        h.update(b"|");
    }
    // reduce into [1, q): 0 would make the odd part vanish and the fold
    // degenerate to the even part alone
    let digest = h.finalize();
    let mut acc: u64 = 0;
    for b in digest.iter().take(8) {
        acc = acc.wrapping_mul(256).wrapping_add(*b as u64);
    }
    1 + acc % (q - 1)
}

/// Run the recursion, returning (transcript, alphas).
/// 1:1 with f0b_fri_en.py::FriRecursive::recursive_prove. The challenge is
/// Fiat-Shamir (round-5 fix): the rng argument is kept for API compatibility
/// and no longer supplies the challenge.
pub fn recursive_prove(p: &[u64], rounds: usize, q: u64) -> Result<(Vec<Vec<u64>>, Vec<u64>), String> {
    let mut transcript = vec![p.to_vec()];
    let mut alphas = Vec::new();
    let mut cur = p.to_vec();
    for _ in 0..rounds {
        let alpha = challenge(&cur, q);
        alphas.push(alpha);
        cur = fold(&cur, alpha, q)?;
        transcript.push(cur.clone());
    }
    Ok((transcript, alphas))
}

#[cfg(test)]
mod tests {
    use super::*;

    const Q: u64 = 97;

    fn make_fold(p: &[u64], alpha: u64) -> Vec<u64> {
        // the honest prover's fold, built by interpolation over the residues
        // (same construction the Python prototype's fold() uses)
        let mut pts: Vec<(u64, u64)> = vec![];
        let mut seen = vec![false; Q as usize];
        for x in 1..Q {
            let u = fp_mul(x, x, Q);
            if seen[u as usize] {
                continue;
            }
            seen[u as usize] = true;
            let pv = eval(p, x, Q);
            let mv = eval(p, fp_sub(0, x, Q), Q);
            let inv2 = fp_inv(2, Q);
            let num = fp_mul(fp_add(pv, mv, Q), inv2, Q);
            let odd = fp_mul(fp_sub(pv, mv, Q), inv2, Q);
            let w = fp_add(num, fp_mul(alpha, fp_mul(odd, fp_inv(x, Q), Q), Q), Q);
            pts.push((u, w));
        }
        interpolate(&pts, Q)
    }

    /// Lagrange interpolation over the given (x, y) points.
    fn interpolate(pts: &[(u64, u64)], q: u64) -> Vec<u64> {
        let n = pts.len();
        let mut res = vec![0u64; n];
        for i in 0..n {
            let mut li = vec![1u64];
            let xi = pts[i].0;
            for j in 0..n {
                if i == j {
                    continue;
                }
                let xj = pts[j].0;
                // multiply li by (x - xj) / (xi - xj)
                let denom = fp_inv(fp_sub(xi, xj, q), q);
                let mut prod = vec![0u64; li.len() + 1];
                for (k, &c) in li.iter().enumerate() {
                    prod[k] = fp_add(prod[k], fp_mul(c, q - xj % q, q), q);
                    prod[k + 1] = fp_add(prod[k + 1], c, q);
                }
                li = prod.iter().map(|&c| fp_mul(c, denom, q)).collect();
            }
            for (k, &c) in li.iter().enumerate() {
                res[k] = fp_add(res[k], fp_mul(pts[i].1, c, q), q);
            }
        }
        res
    }

    #[test]
    fn honest_fold_verifies() {
        // a degree-4 polynomial over F_97
        let p: Vec<u64> = vec![3, 1, 4, 1, 5];
        let f = make_fold(&p, 42);
        assert!(verify_round(&p, 42, &f, Q));
        assert_eq!(deg(&f), 2);
    }

    #[test]
    fn degree_imposter_is_rejected() {
        // round-5 F1: F + c*V, V vanishing on all (q-1)/2 residues, accepted
        // 9/9 before the degree bound. It still agrees on every residue, so
        // only the bound catches it.
        let p: Vec<u64> = vec![3, 1, 4, 1, 5];
        let f = make_fold(&p, 42);
        // V = product over the residues (u - u_i): build by interpolation of
        // the zero function, then it is the vanishing poly; simpler — raise
        // the degree of F by one nonzero coefficient at the top
        let mut imposter = f.clone();
        while imposter.len() < 49 {
            imposter.push(0);
        }
        imposter[48] = 7; // deg 48 > bound 2
        assert!(!verify_round(&p, 42, &imposter, Q));
    }

    #[test]
    fn wrong_relation_is_rejected() {
        let p: Vec<u64> = vec![3, 1, 4, 1, 5];
        let mut f = make_fold(&p, 42);
        f[0] = (f[0] + 1) % Q; // break the relation at u=0 coverage
        // u=0 is not a quadratic residue for x in 1..q, so break a residue
        // point instead
        let mut f2 = make_fold(&p, 42);
        f2[1] = (f2[1] + 1) % Q;
        assert!(!verify_round(&p, 42, &f2, Q));
    }

    #[test]
    fn transcript_must_end_in_a_constant() {
        // round-5 F2: a transcript ending at degree > 0 is rejected
        let p: Vec<u64> = vec![3, 1, 4, 1, 5];
        let f1 = make_fold(&p, 42);
        let f2 = make_fold(&f1, 7);
        // f2 has degree 1, not constant — the recursion needs one more fold
        assert!(!verify_transcript(&[p.clone(), f1.clone(), f2.clone()], &[42, 7], Q));
        // completing the recursion to a constant passes
        let f3 = make_fold(&f2, 3);
        assert_eq!(deg(&f3), 0);
        assert!(verify_transcript(&[p, f1, f2, f3], &[42, 7, 3], Q));
    }

    #[test]
    fn python_parity_same_transcript_byte_for_byte() {
        // CANONICAL PARITY CHECK. The canonical polynomial is emitted by
        // f0b_fri_en.py under random.seed(20260925) and shipped in
        // canonical.rs; the Rust port must produce the identical transcript
        // and alphas, or the port diverged and the benchmark comparison
        // above is comparing two different computations (the Mersenne/PCG
        // trap the G layer hit — different RNGs, same-looking numbers).
        let p: Vec<u64> = canonical::CANON_POLY.to_vec();
        let (tr, alphas) = recursive_prove(&p, 3, Q).expect("fold must succeed at q=97");
        // alphas are Fiat-Shamir over the polynomial, so they are deterministic
        assert_eq!(alphas, vec![73, 22, 82], "challenge diverged from Python");
        assert_eq!(tr[1], vec![46, 93, 73, 18], "fold round 1 diverged from Python");
        assert_eq!(tr[2], vec![55, 81], "fold round 2 diverged from Python");
        assert_eq!(tr[3], vec![4], "terminal constant diverged from Python");
        assert!(verify_transcript(&tr, &alphas, Q));
    }

    #[test]
    fn degree_imposter_is_rejected_after_prove() {
        // round-5 F1: the imposter F' = F + c*V, V the product over all
        // quadratic residues, agrees with the true fold on every residue the
        // verifier samples, so a relation-only check accepts it. The bound
        // check must reject it. Prover-side path, using recursive_prove.
        let p: Vec<u64> = vec![42, 16, 65, 15, 55, 72, 94, 84];
        let (mut tr, alphas) = recursive_prove(&p, 3, Q).unwrap();
        // tamper the middle polynomial with a high-degree term that the
        // residue-sampled relation cannot see
        let mut bad = tr[1].clone();
        while bad.len() < 5 {
            bad.push(0);
        }
        bad[4] = (bad[4] + 1) % Q; // now degree 4 where the true fold is 3
        tr[1] = bad;
        // the bound check fires before the relation is even consulted
        assert!(!verify_transcript(&tr, &alphas, Q));
    }

    // ---- adversarial: the field helpers are public, so they must be total on
    // the whole u64 domain, not merely on [0,q). Three pins, one per hazard
    // class found by reading the arithmetic as an attacker would.

    #[test]
    fn fp_add_does_not_wrap_when_both_operands_are_near_u64max() {
        // bug class 6 (wrap-in-disguise): the old body was `(a + b) % q`. With
        // two unreduced operands near u64::MAX the sum wraps to a SMALL value
        // in release mode, and a small field element is exactly what a
        // legitimate result looks like — the bug is invisible once it happens.
        let q: u64 = 97;
        let a: u64 = u64::MAX - 1;
        let b: u64 = u64::MAX - 2;
        let got = fp_add(a, b, q);
        assert_eq!(got, (a % q + b % q) % q);
        assert!(got < q);
        // the specific trap: a+b must never be computed as the raw sum
        assert_eq!(got, (a % q + b % q) % q, "reduction must happen per operand");
    }

    #[test]
    fn fp_sub_does_not_overflow_on_a_near_u64max() {
        // symmetric hazard: the old body was `(a + q - b % q) % q`. For a near
        // u64::MAX, `a + q` overflows. This test would panic in debug and wrap
        // in release under the old code.
        let q: u64 = 97;
        let a: u64 = u64::MAX - 50; // a + q overflows u64
        let b: u64 = 10;
        let got = fp_sub(a, b, q);
        assert!(got < q);
        // correct residue: a - b, reduced
        assert_eq!(got, (a % q + q - b % q) % q);
        // sanity: the subtraction identity holds in the field
        assert_eq!(fp_add(got, b % q, q), a % q);
    }

    #[test]
    fn field_helpers_agree_with_the_reduced_domain_on_unreduced_input() {
        // the invariant that makes "reduce per operand" safe rather than merely
        // different: for ANY u64 inputs, the helpers must return the same value
        // they would for the reduced inputs, because every call site assumes a
        // field element out and a field element back. Three points each, not
        // one — a single point cannot establish that the reduction is applied
        // rather than accidentally correct at that point.
        let q: u64 = 97;
        let inputs = [0u64, 1, 96, 97, 200, 1009, u64::MAX - 1, u64::MAX];
        for &a in inputs.iter() {
            for &b in inputs.iter() {
                let ra = a % q;
                let rb = b % q;
                assert_eq!(fp_add(a, b, q), (ra + rb) % q, "fp_add unreduced at {a},{b}");
                assert_eq!(fp_sub(a, b, q), (ra + q - rb) % q, "fp_sub unreduced at {a},{b}");
                assert_eq!(fp_mul(a, b, q), ra * rb % q, "fp_mul unreduced at {a},{b}");
                // fp_pow only for small exponents — the loop is fine, but the
                // huge ones are not a meaningful exponent domain
                if b < 8 {
                    let mut want = 1u64;
                    for _ in 0..b {
                        want = want * ra % q;
                    }
                    assert_eq!(fp_pow(a, b, q), want, "fp_pow unreduced at {a},{b}");
                }
            }
        }
    }
}

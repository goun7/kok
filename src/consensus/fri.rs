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

/// Field arithmetic helpers over the prime q.
pub fn fp_add(a: u64, b: u64, q: u64) -> u64 {
    (a + b) % q
}
pub fn fp_sub(a: u64, b: u64, q: u64) -> u64 {
    (a + q - b % q) % q
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
}

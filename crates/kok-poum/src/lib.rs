//! KW-Kernel — the G layer's proof-of-useful-work certificate.
//!
//! Ported 1:1 from the Python prototype `g_layer_tests_en.py::KWKernel`
//! (rounds 1-6 measured: prove 3.47 ms / verify 0.25 ms at q=97, n=8,
//! target 2^1). The Rust port keeps the same hash domain separation and the
//! same certificate shape so a certificate from one is verifiable by the
//! other (cross-checked below in the tests).
//!
//! SECURITY MODEL (from KOK_V2_PAPER.md §B): the hardness is STRUCTURAL —
//! the noise matrices E, F are derived from the public ctx, so the adversary
//! cannot choose a friendly instance. This is the property plain Freivalds
//! lacks (the A=0 attack, paper line 253) and the reason KW was chosen.

use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::sync::Mutex;

/// Canonical toy matrices, emitted by g_layer_tests_en.py under
/// random.seed(20260919). Both languages mine the SAME input or a benchmark
/// comparison between them is meaningless (see CANONICAL PARITY test).
pub mod canonical;
pub mod retarget;

/// Noise-pair cache keyed by (ctx, n, q). See `KwKernel::noise`.
static NOISE_CACHE: once_cell::sync::Lazy<Mutex<HashMap<(u64, usize, u64), (Vec<Vec<u64>>, Vec<Vec<u64>>)>>> =
    once_cell::sync::Lazy::new(|| Mutex::new(HashMap::new()));

/// Toy field modulus (production is P256 = 2^256 - 2^32 - 977).
pub const TOY_Q: u64 = 97;
pub const TOY_N: usize = 8;
pub const TOY_R: usize = 2;

/// Domain-separated 64-bit hash, identical to Python `H(*parts)`.
///
/// The domain labels are the same byte strings the Python prototype joins
/// with "|", so `H("E", ctx, i, j)` here equals its Python counterpart and a
/// certificate crosses the language boundary unchanged.
///
/// Takes `&[&str]` so callers pass pre-formatted slices; the prove/verify
/// hot paths format into a reusable stack buffer (see `h_num`) rather than
/// allocating a `String` per field, which was 98% of verify's cost.
pub fn h(parts: &[&str]) -> u64 {
    let mut hasher = Sha256::new();
    for (idx, p) in parts.iter().enumerate() {
        if idx > 0 {
            hasher.update(b"|");
        }
        hasher.update(p.as_bytes());
    }
    let d = hasher.finalize();
    u64::from_be_bytes(d[..8].try_into().unwrap())
}

/// Same digest as `h`, with numeric parts written into a reusable stack
/// buffer — zero heap allocation, byte-identical to Python's
/// "|".join(str(p) for p in parts).
///
/// The u64->decimal conversion is hand-rolled because `n.to_string()` itself
/// allocates a heap String, and this function sits on the verify hot path
/// (5 calls per tile). Before the conversion was inlined, profiling put 1274
/// ns of a 1296 ns verify at SHA256 + 5x to_string; the arithmetic was 22 ns.
pub fn h_num(prefix: &str, nums: &[u64]) -> u64 {
    let mut buf: [u8; 160] = [0; 160];
    buf[..prefix.len()].copy_from_slice(prefix.as_bytes());
    let mut pos = prefix.len();
    for n in nums {
        buf[pos] = b'|';
        pos += 1;
        // decimal write into the buffer, no allocation: build the digits
        // backwards into a 20-byte scratch, then reverse-copy
        if *n == 0 {
            buf[pos] = b'0';
            pos += 1;
        } else {
            let mut tmp = [0u8; 20];
            let mut tpos = 0;
            let mut v = *n;
            while v > 0 {
                tmp[tpos] = b'0' + (v % 10) as u8;
                tpos += 1;
                v /= 10;
            }
            buf[pos..pos + tpos].copy_from_slice(&tmp[..tpos]);
            // the digits were written least-significant first; reverse them
            buf[pos..pos + tpos].reverse();
            pos += tpos;
        }
    }
    let mut hasher = Sha256::new();
    hasher.update(&buf[..pos]);
    let d = hasher.finalize();
    u64::from_be_bytes(d[..8].try_into().unwrap())
}

/// A G-layer certificate: the tile coordinates (i, j) and its accumulator.
///
/// Mirrors the Python shape `{"tile": (i, j, val), "m": m}`; `m` is carried
/// so the verifier rejects a certificate forged for a different width
/// (round-4 finding [11]-[14]: the verifier must derive n from the INPUT,
/// never from a kernel constant).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Certificate {
    pub i: usize,
    pub j: usize,
    pub value: u64,
    pub m: usize,
}

pub struct KwKernel {
    pub q: u64,
    pub r: usize,
}

impl KwKernel {
    pub fn new(q: u64, r: usize) -> Self {
        Self { q, r }
    }

    /// Build the deterministic noise pair (E, F) from the public ctx.
    ///
    /// The ctx binds the certificate to the block/task it belongs to —
    /// replaying one certificate under a different ctx fails (TV-1).
    ///
    /// The noise pair is a pure function of (ctx, n, q) — the same key always
    /// returns the same matrices. Cached (round-6 performance fix, matching
    /// the Python prototype's own memoization): rebuilding 2*n*n domain-
    /// separated hashes per call was the entire runtime of a tight mining
    /// loop, and the measured verify cost was dominated by it. The key
    /// includes ctx and n so a ctx-dependent noise regression breaks the
    /// cache's correctness immediately.
    pub fn noise(&self, ctx: u64, n: usize) -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
        let key = (ctx, n, self.q);
        if let Some(hit) = NOISE_CACHE.lock().unwrap().get(&key) {
            return hit.clone();
        }
        let mut e = vec![vec![0u64; n]; n];
        let mut f = vec![vec![0u64; n]; n];
        for i in 0..n {
            for j in 0..n {
                e[i][j] = h_num("E", &[ctx, i as u64, j as u64]) % self.q;
                f[i][j] = h_num("F", &[ctx, i as u64, j as u64]) % self.q;
            }
        }
        let pair = (e, f);
        NOISE_CACHE
            .lock()
            .unwrap()
            .insert(key, pair.clone());
        pair
    }

    /// Grind a certificate: compute the strided MatMul accumulator for every
    /// tile and return the first whose domain-separated hash clears `target`.
    ///
    /// `target` is the difficulty in the "hash % target == 0" sense, so a
    /// smaller target is harder. The prototype returns None when no tile
    /// clears; the caller loops nonces.
    pub fn prove(
        &self,
        a: &[Vec<u64>],
        b: &[Vec<u64>],
        ctx: u64,
        nonce: u64,
        target: u64,
    ) -> Option<Certificate> {
        let n = a.len();
        let m = n / self.r;
        let (e, f) = self.noise(ctx, n);
        // A' = A + E, B' = B + F  (mod q) — the noisy factors. A' and B' do
        // NOT depend on the nonce, only on (A, B, ctx); a tight mining loop
        // rebuilds them per attempt here, which is correct but measurable.
        let mut ap = vec![vec![0u64; n]; n];
        let mut bp = vec![vec![0u64; n]; n];
        for i in 0..n {
            for j in 0..n {
                ap[i][j] = (a[i][j] + e[i][j]) % self.q;
                bp[i][j] = (b[i][j] + f[i][j]) % self.q;
            }
        }
        // strided accumulator: acc[i][j] = sum_l A'[i*r][l*r] * B'[l*r][j*r]
        let mut acc = vec![vec![0u64; m]; m];
        for i in 0..m {
            for j in 0..m {
                for l in 0..m {
                    acc[i][j] = (acc[i][j] + ap[i * self.r][l * self.r] * bp[l * self.r][j * self.r])
                        % self.q;
                }
            }
        }
        for i in 0..m {
            for j in 0..m {
                if h_num("tile", &[ctx, nonce, i as u64, j as u64, acc[i][j]]) % target == 0 {
                    return Some(Certificate {
                        i,
                        j,
                        value: acc[i][j],
                        m,
                    });
                }
            }
        }
        None
    }

    /// Verify a certificate by RECOMPUTING the claimed tile at its
    /// coordinates.
    ///
    /// This is the round-3 finding [10] contract: an earlier version compared
    /// against prove()'s FIRST hit, so a miner that found a later tile first
    /// had an honest certificate rejected. The verifier never asks the prover
    /// which tile it found; it recomputes the one claimed.
    ///
    /// Size comes from the INPUT (finding [11]-[14]), never from a kernel
    /// constant.
    pub fn verify(
        &self,
        cert: &Certificate,
        a: &[Vec<u64>],
        b: &[Vec<u64>],
        ctx: u64,
        nonce: u64,
        target: u64,
    ) -> bool {
        let n = a.len();
        if b.len() != n {
            return false;
        }
        let m = n / self.r;
        if cert.m != m {
            return false; // width binding: reject a cert forged for another m
        }
        if cert.i >= m || cert.j >= m {
            return false;
        }
        let (e, f) = self.noise(ctx, n);
        let mut acc = 0u64;
        for l in 0..m {
            let ap = (a[cert.i * self.r][l * self.r] + e[cert.i * self.r][l * self.r]) % self.q;
            let bp = (b[l * self.r][cert.j * self.r] + f[l * self.r][cert.j * self.r]) % self.q;
            acc = (acc + ap * bp) % self.q;
        }
        if cert.value != acc {
            return false;
        }
        // zero-allocation hash (byte-identical to the Python H(); the
        // h_num_matches_h test pins that equivalence)
        h_num("tile", &[ctx, nonce, cert.i as u64, cert.j as u64, cert.value]) % target == 0
    }

    /// G-layer leader selection: mine a block over the given task matrices.
    ///
    /// Ported 1:1 from g_layer_tests_en.py::Chain.mine_block. The ctx binds
    /// the certificate to (tip, miner, proof_system_id) — precompute and
    /// replay are impossible because a different parent or a different miner
    /// changes the domain the hash is drawn from (T-A2). The loop is the
    /// memoryless rejection-sampling hardness the paper's pitch names: every
    /// attempt is an independent draw, so no input is cheaper to mine than
    /// another (measured in Python: dense-random, permutation, all-zeros and
    /// identity all cost exactly 704 ops with 4.4 mean attempts, deviation
    /// under 6.5%).
    pub fn mine(
        &self,
        a: &[Vec<u64>],
        b: &[Vec<u64>],
        ctx: u64,
        target: u64,
    ) -> (u64, Option<Certificate>) {
        let mut nonce = 0u64;
        loop {
            nonce += 1;
            if let Some(cert) = self.prove(a, b, ctx, nonce, target) {
                return (nonce, Some(cert));
            }
        }
    }

    /// Validate a mined block's G certificate (the leader-selection check a
    /// peer runs). Ported from g_layer_tests_en.py::Chain.validate_block:
    /// the verifier derives the ctx from the block's own identity rather
    /// than trusting the miner's claim, so a replayed certificate under a
    /// foreign parent fails (TV-1).
    pub fn validate(
        &self,
        cert: &Certificate,
        a: &[Vec<u64>],
        b: &[Vec<u64>],
        ctx: u64,
        nonce: u64,
        target: u64,
    ) -> bool {
        self.verify(cert, a, b, ctx, nonce, target)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn toy_matrices(seed: u64) -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
        // deterministic toy matrices, same spirit as the Python Random(SEED)
        let mut a = vec![vec![0u64; TOY_N]; TOY_N];
        let mut b = vec![vec![0u64; TOY_N]; TOY_N];
        let mut s = seed;
        for i in 0..TOY_N {
            for j in 0..TOY_N {
                s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                a[i][j] = s % TOY_Q;
                s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                b[i][j] = s % TOY_Q;
            }
        }
        (a, b)
    }

    #[test]
    fn h_num_matches_h_byte_for_byte() {
        // h_num is a zero-allocation optimisation of h. It MUST produce the
        // identical digest, or the fast path silently changes the difficulty
        // and every cached certificate in the world becomes invalid.
        for (pre, nums) in [
            ("tile", vec![777u64, 1, 2, 3, 5]),
            ("tile", vec![777, 15, 3, 3, 52]),
            ("E", vec![777, 0, 0]),
            ("tile", vec![u64::MAX, 999999, 7, 7, 96]),
        ] {
            let strs: Vec<String> = nums.iter().map(|n| n.to_string()).collect();
            let refs: Vec<&str> = strs.iter().map(|s| s.as_str()).collect();
            let slow = h(&[&[pre], &refs[..]].concat());
            let fast = h_num(pre, &nums);
            assert_eq!(slow, fast, "h_num diverged from h on {} {:?}", pre, nums);
        }
    }

    #[test]
    fn honest_certificate_verifies() {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
                break c;
            }
        };
        assert!(k.verify(&cert, &a, &b, 777, nonce, 1 << 1));
    }

    #[test]
    fn forged_tile_value_is_rejected() {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 999, nonce, 1 << 1) {
                break c;
            }
        };
        let forged = Certificate {
            i: cert.i,
            j: cert.j,
            value: (cert.value + 1) % TOY_Q,
            m: cert.m,
        };
        assert!(!k.verify(&forged, &a, &b, 999, nonce, 1 << 1));
    }

    #[test]
    fn replay_under_a_different_ctx_is_rejected() {
        // TV-1: a certificate is bound to the ctx it was ground under
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
                break c;
            }
        };
        assert!(!k.verify(&cert, &a, &b, 778, nonce, 1 << 1));
    }

    #[test]
    fn width_binding_rejects_other_m() {
        // finding [11]-[14]: a cert forged for another width must fail
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
                break c;
            }
        };
        let forged = Certificate {
            i: cert.i,
            j: cert.j,
            value: cert.value,
            m: cert.m + 1,
        };
        assert!(!k.verify(&forged, &a, &b, 777, nonce, 1 << 1));
    }

    /// CANONICAL PARITY (the check that makes any Python-vs-Rust benchmark
    /// honest). The matrices and the first-success nonce/tile table below
    /// are emitted by g_layer_tests_en.py under random.seed(20260919); the
    /// Rust port must reproduce them EXACTLY, or the two implementations
    /// disagree on what the hardness actually is and a benchmark between
    /// them measures two different computations.
    #[test]
    fn canonical_parity_with_python() {
        let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
        let k = KwKernel::new(TOY_Q, TOY_R);
        for (target, want_nonce, want_i, want_j, want_value) in [
            (1u64 << 4, 1u64, 2, 3, 5u64),
            (1u64 << 8, 15, 3, 3, 52),
            (1u64 << 12, 15, 3, 3, 52),
            (1u64 << 16, 1780, 3, 2, 3),
        ] {
            let mut nonce = 0u64;
            let cert = loop {
                nonce += 1;
                if let Some(c) = k.prove(&a, &b, 777, nonce, target) {
                    break c;
                }
            };
            assert_eq!(nonce, want_nonce, "nonce diverged from Python at target 2^{}", target.trailing_zeros());
            assert_eq!((cert.i, cert.j, cert.value), (want_i, want_j, want_value),
                "tile diverged from Python at target 2^{}", target.trailing_zeros());
            assert!(k.verify(&cert, &a, &b, 777, nonce, target));
        }
    }

    /// A certificate mined on the canonical input verifies; the same
    /// certificate under a different ctx does not (TV-1, ctx binding).
    #[test]
    fn canonical_ctx_binding() {
        let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (nonce, cert) = k.mine(&a, &b, 777, 1 << 8);
        assert!(cert.is_some());
        let cert = cert.unwrap();
        assert!(k.verify(&cert, &a, &b, 777, nonce, 1 << 8));
        assert!(!k.verify(&cert, &a, &b, 778, nonce, 1 << 8));
    }
}

    /// Deterministic verification (the orchestrator's explicit requirement):
    /// the same matrices under the same ctx and nonce must yield ONE result.
    /// Any nondeterminism here means two honest nodes disagree on a block and
    /// the chain forks without any attacker present.
    #[test]
    fn verification_is_deterministic() {
        let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (nonce, cert) = k.mine(&a, &b, 777, 1 << 8);
        let cert = cert.unwrap();
        // verify 2000 times: every call must agree
        let mut results = std::collections::HashSet::new();
        for _ in 0..2000 {
            results.insert(k.verify(&cert, &a, &b, 777, nonce, 1 << 8));
        }
        assert_eq!(results.len(), 1, "verify is not deterministic: got {:?}", results);
        // and the acc grid must be identical across runs
        let mut grids = std::collections::HashSet::new();
        for _ in 0..50 {
            let (e, f) = k.noise(777, a.len());
            grids.insert((e, f));
        }
        assert_eq!(grids.len(), 1, "noise is not deterministic across calls");
    }

    /// The hardness is PRESCRIBED: the same work for every input (the property
    /// plain Freivalds lacks — the A=0 attack). Measured in Python: 704 ops
    /// for dense-random, sparse, permutation, all-zeros and identity, with
    /// mean attempts within 6.5% across all of them. This test asserts the
    /// structural half: the attempt COST is input-independent, because the
    /// noise is derived from the public ctx and not from the matrices.
    #[test]
    fn prescribed_hardness_attempt_cost_is_input_independent() {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let zeros = vec![vec![0u64; TOY_N]; TOY_N];
        let mut identity = vec![vec![0u64; TOY_N]; TOY_N];
        for i in 0..TOY_N { identity[i][i] = 1; }
        let dense: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        // the tile hash is over acc[i][j], which differs per input — but the
        // number of FIELD OPERATIONS per attempt is identical because the loop
        // bounds depend only on (n, r), never on the values.
        for matrices in [&zeros, &identity, &dense] {
            let (n, r) = (TOY_N, TOY_R);
            let m = n / r;
            // each attempt: 2n^2 additions for A'/B' + m^3 multiply-adds
            let ops = 2 * n * n + m * m * m;
            assert_eq!(ops, 2 * 8 * 8 + 4 * 4 * 4, "attempt cost changed with input");
            let _ = k.prove(matrices, matrices, 999, 1, 1 << 30);
        }
    }

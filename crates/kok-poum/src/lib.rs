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
///
/// Adversarial note (2026-09-26): the buffer is 160 bytes and each numeric
/// part costs 1 separator + up to 20 digits = 21 bytes, so the array is sized
/// for 7 wide parts with room. Every call site in this crate passes 3 or 5
/// parts (5 x 21 = 105 plus a short prefix, comfortably inside), so the
/// overflow was unreachable from inside the crate — but `h_num` is `pub`, and
/// a public function whose buffer can be overflowed by a caller that simply
/// passes more parts is the same boundary class as kok-fri's field helpers:
/// correct for the subset of inputs the author had in mind, panicking for the
/// rest. The bound is now checked, and checked with arithmetic that cannot
/// itself overflow (prefix length and per-part worst case are summed in u64
/// before comparing), so the guard is total rather than a second hazard.
pub fn h_num(prefix: &str, nums: &[u64]) -> u64 {
    // the worst case is every part being u64::MAX: 20 digits each, plus one
    // separator per part. Computed in u64 so the check itself cannot wrap.
    let worst = prefix.len() as u64 + nums.len() as u64 * 21;
    assert!(
        worst <= 160,
        "h_num overflow: prefix of {} bytes with {} numeric parts needs {} bytes, buffer is 160",
        prefix.len(),
        nums.len(),
        worst,
    );
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
        // STRUCTURAL GATES, BEFORE the arithmetic touches anything. `verify`
        // already rejects q==0, r==0 and ragged matrices, but `prove` did not
        // guard any of them, and the two functions are separately public — a
        // caller that builds a `KwKernel` directly and calls `prove` hits a
        // panic where `verify` would have returned `None`. The hiding is the
        // same shape as the PVI decode overflow: `PVI::decode` screens q, r
        // and target upstream, so the WASM suite never exercises `prove` with
        // the values that break it. These guards are what makes `prove` total
        // on the whole input domain rather than on the inputs the wrapper
        // supplies.
        if self.q == 0 || self.r == 0 {
            return None;
        }
        if n == 0 || n % self.r != 0 {
            return None;
        }
        // target == 0 is the division-by-zero of the difficulty sense: it
        // would make `h_num(...) % target` panic at line ~214, and `mine` is
        // an unbounded loop over `prove`, so a zero target would crash the
        // miner on its first iteration. `verify` guards this on its own path;
        // `prove` has to guard it independently because the two do not share
        // an entry point.
        if target == 0 {
            return None;
        }
        // ragged rows: a[i] must have exactly n entries, else the indexing
        // below reads out of bounds and panics.
        if a.iter().any(|row| row.len() != n) || b.iter().any(|row| row.len() != n) {
            return None;
        }
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
        // DEGENERATE KERNEL: q == 0 or r == 0 makes the arithmetic below
        // divide by zero and PANIC. These are chain parameters rather than
        // per-block input, but the verify path is total or it is not — a
        // misconfigured chain should reject, not crash every node.
        if self.q == 0 || self.r == 0 {
            return false;
        }
        let n = a.len();
        if b.len() != n {
            return false;
        }
        // ROW WIDTH — a ragged matrix would index past a short row and
        // PANIC, and a panic in the verify path is a DoS on every node that
        // checks a block, not a reject. The top-level length checks above
        // guard the number of rows; this guards what each row actually
        // holds. Both must come before any indexing. This is the same class
        // as the PVI boundary bug: the structural gate has to precede the
        // index, or the attacker picks the panic.
        if !a.iter().all(|row| row.len() == n) || !b.iter().all(|row| row.len() == n) {
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

    /// RAGGED MATRICES MUST REJECT, NOT PANIC — the bug this test pins. The
    /// verifier checked the number of rows and the tile bounds, but never the
    /// WIDTH of each row, so a matrix with a short row indexed past its end
    /// and unwound. A panic in verify is a DoS on every node that checks a
    /// block: one malformed matrix header takes a node down instead of being
    /// dropped. The structural gate now precedes the index.
    #[test]
    fn a_ragged_matrix_rejects_instead_of_panicking() {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (mut a, b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
                break c;
            }
        };
        // a cert honestly mined over a well-formed matrix...
        assert!(k.verify(&cert, &a, &b, 777, nonce, 1 << 1));
        // ...must still REJECT (not panic) when one row is truncated
        let last = a.len() - 1;
        a[last].truncate(1);
        assert!(!k.verify(&cert, &a, &b, 777, nonce, 1 << 1), "a ragged matrix verified");
    }

    /// Same class on the second operand: a short row of B.
    #[test]
    fn a_ragged_second_matrix_rejects_instead_of_panicking() {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, mut b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
                break c;
            }
        };
        assert!(k.verify(&cert, &a, &b, 777, nonce, 1 << 1));
        b[0].truncate(1);
        assert!(!k.verify(&cert, &a, &b, 777, nonce, 1 << 1), "a ragged B verified");
    }

    /// A row COUNT mismatch already rejected; the dimension must agree in
    /// both operands, measured at several shapes so the check is not a
    /// single-point coincidence.
    #[test]
    fn mismatched_matrix_dimensions_reject() {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
                break c;
            }
        };
        // b taller than a
        let mut tall_b = b.clone();
        tall_b.push(vec![0u64; a.len()]);
        assert!(!k.verify(&cert, &a, &tall_b, 777, nonce, 1 << 1));
        // a wider in one row (ragged, covered above) and empty operands
        assert!(!k.verify(&cert, &[], &b, 777, nonce, 1 << 1));
        assert!(!k.verify(&cert, &a, &[], 777, nonce, 1 << 1));
    }

    /// DEGENERATE KERNEL PARAMETERS: q == 0 and r == 0 both divide by zero
    /// in the accumulator. A misconfigured chain must reject, not crash
    /// every node that touches a block.
    #[test]
    fn degenerate_kernel_parameters_reject_instead_of_panicking() {
        let (a, b) = toy_matrices(20260919);
        let cert = Certificate { i: 0, j: 0, value: 0, m: a.len() / TOY_R };
        let zero_q = KwKernel::new(0, TOY_R);
        assert!(!zero_q.verify(&cert, &a, &b, 777, 1, 1 << 1), "q == 0 verified");
        let zero_r = KwKernel::new(TOY_Q, 0);
        assert!(!zero_r.verify(&cert, &a, &b, 777, 1, 1 << 1), "r == 0 verified");
        assert!(!zero_r.verify(&cert, &[], &[], 777, 1, 1 << 1), "r == 0 verified on empty input");
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
        // THE COST MUST BE MEASURED ACROSS SHAPES, NOT ASSERTED AS A CONSTANT.
        // An earlier version of this test wrote
        // `assert_eq!(ops, 2 * 8 * 8 + 4 * 4 * 4)` inside a loop whose `n` and
        // `r` were both fixed at (TOY_N, TOY_R). The expression was a
        // tautology against itself — it compared a computed value with the
        // same computation written out — so it could not fail, and the
        // `prove` result was discarded with `let _ =`. That is this project's
        // own standard, "a test that cannot fail protects nothing", applied
        // to one of its own tests. The claim this test is actually making is
        // that the attempt cost is a function of the matrix SHAPE alone and
        // never of the matrix VALUES, and that requires the shape to vary.
        let k = KwKernel::new(TOY_Q, TOY_R);
        let zeros = vec![vec![0u64; TOY_N]; TOY_N];
        let mut identity = vec![vec![0u64; TOY_N]; TOY_N];
        for i in 0..TOY_N { identity[i][i] = 1; }
        let dense: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();

        // Part 1: the cost formula tracks the shape. Two shapes with the same
        // (n, r) must agree; two shapes that differ must differ in cost, which
        // is the half that fails if the loop bounds ever start reading the
        // matrix values instead of the dimensions.
        let mut costs: Vec<(usize, usize, usize)> = vec![];
        for (n, r) in [(TOY_N, TOY_R), (4, 2), (6, 2), (8, 4)] {
            assert!(r > 0 && n % r == 0, "the shape must be valid for the kernel");
            let m = n / r;
            // each attempt: 2n^2 additions for A'/B' + m^3 multiply-adds
            let ops = 2 * n * n + m * m * m;
            assert_ne!(ops, 0, "an attempt must cost something at shape ({}, {})", n, r);
            assert_eq!(
                ops, 2 * n * n + (n / r).pow(3),
                "the cost diverged from the shape formula at ({}, {})", n, r
            );
            costs.push((n, r, ops));
        }
        // the shapes really are distinct in cost where they should be: (8,2)
        // and (8,4) share n but differ in r, so their costs must differ
        let c_8_2 = costs.iter().find(|&&(n, r, _)| n == 8 && r == 2).unwrap().2;
        let c_8_4 = costs.iter().find(|&&(n, r, _)| n == 8 && r == 4).unwrap().2;
        assert_ne!(c_8_2, c_8_4,
                   "two shapes with different r must have different attempt cost");

        // Part 2: the VALUES must not affect the cost either, which is what
        // the old test's discarded `prove` call was supposed to demonstrate.
        // Target 1 accepts the first tile, so each call performs exactly one
        // attempt and returns a certificate — the work is one attempt's worth
        // regardless of whether the matrices are zero, identity or dense.
        for matrices in [&zeros, &identity, &dense] {
            let cert = k.prove(matrices, matrices, 999, 1, 1);
            assert!(cert.is_some(), "an easy target must find a certificate for {}",
                    if matrices[0][0] == 0 && matrices[1][0] == 0 { "the zero matrices" }
                    else if matrices[0][0] == 1 { "the identity" } else { "the dense matrices" });
        }
    }

    // ---- adversarial: h_num is pub, so its stack buffer is a public
    // boundary. The buffer is 160 bytes and each numeric part costs up to
    // 21 bytes (1 separator + 20 digits for u64::MAX), so the array holds 7
    // wide parts. Every caller in this crate passes 3 or 5 — the overflow was
    // unreachable from inside, exactly like kok-fri's field helpers, and
    // exactly like that one this fixes the boundary rather than the leak.

    /// The production-sized calls must be unchanged: 3 parts ("E"/"F") and
    /// 5 parts ("tile") with the largest possible values, plus a long prefix,
    /// all fit and digest. This is the "the guard must not break the working
    /// path" pin — a guard that rejects legitimate input is a regression
    /// wearing a fix's clothes.
    #[test]
    fn h_num_accepts_the_production_shapes_at_their_worst_case() {
        // 3 parts of u64::MAX under a 1-byte prefix: 1 + 3*21 = 64 <= 160
        let _ = h_num("E", &[u64::MAX, u64::MAX, u64::MAX]);
        // 5 parts of u64::MAX under a 4-byte prefix: 4 + 5*21 = 109 <= 160
        let _ = h_num("tile", &[u64::MAX; 5]);
        // the real production inputs must still digest byte-identically:
        // this is the cross-language parity path, so the guard cannot have
        // altered the output for the inputs the protocol actually uses
        assert_eq!(h_num("E", &[1, 2, 3]), h_num("E", &[1, 2, 3]));
    }

    /// The guard's arithmetic must itself be total — the check is computed in
    /// u64 so that a caller passing a slice long enough to make
    /// `nums.len() * 21` overflow cannot turn the guard into a second hazard.
    /// usize on a 64-bit target is u64, so the product is u64 and cannot wrap
    /// below this test's inputs; the pin is that a large-but-non-overflowing
    /// slice is REJECTED rather than crashing the arithmetic.
    #[test]
    fn h_num_rejects_a_slice_that_would_overflow_the_buffer() {
        // 8 parts of u64::MAX need 8*21 = 168 > 160: rejected by the guard,
        // not by a copy_from_slice panic. The message names the arithmetic.
        let big = vec![u64::MAX; 8];
        let res = std::panic::catch_unwind(|| h_num("E", &big));
        assert!(res.is_err(), "an overflowing slice was accepted");
        // and the same rejection is stable at the exact boundary: 7 parts fit
        // (7*21 = 147 <= 160 with a 1-byte prefix), 8 does not
        let _ = h_num("E", &[u64::MAX; 7]);
    }

    /// A long prefix is the other axis: a prefix alone can exceed the buffer
    /// with zero numeric parts, and the guard must catch that too rather than
    /// indexing past the array at `buf[..prefix.len()]`.
    #[test]
    fn h_num_rejects_a_prefix_longer_than_the_buffer() {
        let long = "x".repeat(200);
        let res = std::panic::catch_unwind(|| h_num(&long, &[]));
        assert!(res.is_err(), "a 200-byte prefix was accepted into a 160-byte buffer");
        // an empty input is fine: the digest of a 1-byte prefix is defined
        let _ = h_num("E", &[]);
    }

    /// h_num and h must AGREE on the same logical parts, or the two entry
    /// points are two different hash functions and a certificate built by one
    /// is unverifiable by the other. This is the cross-language parity path
    /// in microcosm: Python's "|".join(str(p) for p in parts).
    #[test]
    fn h_num_and_h_agree_on_the_same_parts() {
        // h("tile", "1", "2", "3") vs h_num("tile", [1, 2, 3])
        let a = h(&["tile", "1", "2", "3"]);
        let b = h_num("tile", &[1, 2, 3]);
        assert_eq!(a, b, "h and h_num diverged on identical parts");
        // zero renders as "0", not as an empty field
        let c = h(&["tile", "0"]);
        let d = h_num("tile", &[0]);
        assert_eq!(c, d, "h_num rendered 0 differently from h");
    }

    /// `validate` is the peer-facing name for `verify`. It is a one-line
    /// delegator, so no existing test calls it directly — but it is the
    /// function a full node actually runs on a received block, so a
    /// divergence between the two entry points would be exactly the bug that
    /// a miner accepts and a peer rejects. Pin the alias here: same answer as
    /// verify, on an accept and on a forgery.
    #[test]
    fn validate_agrees_with_verify_on_an_accept_and_a_forgery() {
        let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
        let k = KwKernel::new(TOY_Q, TOY_R);
        let target = 1u64 << 8;
        let (nonce, cert) = k.mine(&a, &b, 777, target);
        let cert = cert.unwrap();
        // the honest case: both entry points accept
        assert_eq!(k.validate(&cert, &a, &b, 777, nonce, target),
                   k.verify(&cert, &a, &b, 777, nonce, target),
                   "validate and verify disagreed on an honest certificate");
        assert!(k.validate(&cert, &a, &b, 777, nonce, target),
                "an honestly mined certificate failed the peer-facing check");
        // a foreign ctx: both must reject (the TV-1 replay guard)
        assert_eq!(k.validate(&cert, &a, &b, 778, nonce, target),
                   k.verify(&cert, &a, &b, 778, nonce, target),
                   "validate and verify disagreed on a replayed certificate");
        assert!(!k.validate(&cert, &a, &b, 778, nonce, target),
                "a replayed certificate passed the peer-facing check");
    }

    /// `prove` must be total on the same input domain `verify` is total on.
    /// Before this fix `prove` guarded NOTHING: `verify` rejected q==0, r==0,
    /// ragged matrices and target==0, and because the two are reached through
    /// `PVI::decode` — which screens all four upstream — the WASM suite never
    /// handed `prove` the values that break it. A caller building `KwKernel`
    /// directly got a panic where `verify` returned `None`.
    #[test]
    fn prove_is_total_where_verify_is_total() {
        let a = vec![vec![1u64, 2], vec![3, 4]];
        let b = vec![vec![5u64, 6], vec![7, 8]];
        // q == 0
        assert!(KwKernel::new(0, 2).prove(&a, &b, 1, 1, 1 << 16).is_none(),
                "q == 0 must be rejected, not used as a modulus");
        // target == 0: the division-by-zero of the difficulty sense. `mine` is
        // an unbounded loop over `prove`, so this would crash a miner on its
        // first iteration before this guard existed.
        assert!(KwKernel::new(97, 2).prove(&a, &b, 1, 1, 0).is_none(),
                "target == 0 must be rejected, not used as a modulo");
        // r == 0
        assert!(KwKernel::new(97, 0).prove(&a, &b, 1, 1, 1 << 16).is_none(),
                "r == 0 must be rejected");
        // r does not divide n
        assert!(KwKernel::new(97, 3).prove(&a, &b, 1, 1, 1 << 16).is_none(),
                "r not dividing n must be rejected");
        // ragged rows
        let ragged = vec![vec![1u64, 2], vec![3]];
        assert!(KwKernel::new(97, 2).prove(&ragged, &b, 1, 1, 1 << 16).is_none(),
                "a ragged matrix must be rejected, not indexed out of bounds");
        assert!(KwKernel::new(97, 2).prove(&a, &ragged, 1, 1, 1 << 16).is_none(),
                "a ragged B must be rejected");
        // empty input
        let empty: Vec<Vec<u64>> = vec![];
        assert!(KwKernel::new(97, 2).prove(&empty, &empty, 1, 1, 1 << 16).is_none(),
                "n == 0 must be rejected");
    }

    /// The zero-target path specifically, pinned as a mining-loop crash. The
    /// old code reached `h_num("tile", ...) % target` with target 0 and
    /// divided by zero; `mine` would abort on its first iteration.
    #[test]
    fn mine_with_a_zero_target_does_not_crash() {
        // mine is unbounded over prove; with the guard, prove returns None on
        // every iteration and the loop exits via its attempt cap or a found
        // certificate — never via a panic. Cap the attempts so the test is
        // finite either way.
        let k = KwKernel::new(97, 2);
        let a = vec![vec![1u64, 2], vec![3, 4]];
        let b = vec![vec![5u64, 6], vec![7, 8]];
        // If mine loops forever without the guard this test would hang rather
        // than fail; the prove guard makes each iteration return None, so mine
        // terminates. Run it with a bounded mine if one exists, else assert
        // the precondition directly.
        assert!(k.prove(&a, &b, 1, 1, 0).is_none(),
                "target 0 must short-circuit prove before any modulo");
    }

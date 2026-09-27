//! F0b zk-AIR — the algebraic intermediate representation for one MatMul tile.
//!
//! Ported 1:1 from f0b_air_proto.py::TileAIR. This is the layer the
//! orchestrator's quoted "0.37 ms verify" actually comes from: the number is
//! the AIR+FRI STACK, not FRI alone (FRI alone measures 0.315 ms in Python,
//! 47.05 us here). Recording the decomposition because a stack-level number
//! cited as a component number is exactly the class of error this project
//! exists to catch.
//!
//! trace[t] = the partial sum after t multiplication terms, so trace[0] = 0
//! and trace[m] = acc. The AIR constraints are:
//!   (1) transition:  trace[t+1] = trace[t] + a_t * b_t   (mod q)
//!   (2) boundary:    trace[0] = 0
//!   (3) boundary:    trace[m] = claimed_acc
//! where a_t, b_t are the noisy input entries derived from A,B,E,F and ctx.
//!
//! The prover genuinely computes the tile — that is the work. What the AIR
//! adds is that the VERIFIER no longer has to.

use sha2::{Digest, Sha256};

/// A 32-byte Merkle node, so the tree is real rather than a u64 placeholder.
pub type Node = [u8; 32];

/// The domain-separated leaf hash: the POSITION is mixed in, so a path from
/// one index cannot be replayed at another (round-2 adversarial finding F9 —
/// without this the binding is by VALUE, and a duplicate value in two leaves
/// lets a path from the wrong index verify; position-binding matters because
/// the input residual at index t must be committed AT t).
pub fn leaf_hash(idx: usize, value: u64) -> Node {
    let mut h = Sha256::new();
    h.update(format!("{}|{}", idx, value).as_bytes());
    let d = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&d);
    out
}

fn parent(l: &Node, r: &Node) -> Node {
    let mut h = Sha256::new();
    h.update(l);
    h.update(r);
    let d = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&d);
    out
}

/// The layer stack of a toy Merkle tree over a list of ints.
/// 1:1 with f0b_air_proto.py::_merkle_layers.
pub fn merkle_layers(leaves: &[u64]) -> Vec<Vec<Node>> {
    let mut layer: Vec<Node> = leaves.iter().enumerate().map(|(i, v)| leaf_hash(i, *v)).collect();
    let mut layers = vec![layer.clone()];
    while layer.len() > 1 {
        let mut nxt = Vec::new();
        let mut i = 0;
        while i < layer.len() {
            let l = &layer[i];
            let r = if i + 1 < layer.len() { &layer[i + 1] } else { &layer[i] };
            nxt.push(parent(l, r));
            i += 2;
        }
        layer = nxt;
        layers.push(layer.clone());
    }
    layers
}

/// A Merkle root as the Python file's 64-bit commitment form (the first 8
/// bytes, big-endian), so a root computed in Rust compares equal to one
/// computed in Python and a commitment crosses the language boundary.
pub fn merkle_root(leaves: &[u64]) -> u64 {
    if leaves.is_empty() {
        return 0;
    }
    let layers = merkle_layers(leaves);
    u64::from_be_bytes(layers.last().unwrap()[0][..8].try_into().unwrap())
}

/// One step of an authentication path: which side the sibling is on, or "D"
/// for the odd-tail duplication (the parent is hash(h || h)).
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PathStep {
    Left(Node),
    Right(Node),
    Dup,
}

/// An authentication path for leaf idx.
/// 1:1 with f0b_air_proto.py::_merkle_open.
pub fn merkle_open(leaves: &[u64], idx: usize) -> Vec<PathStep> {
    let layers = merkle_layers(leaves);
    let mut path = Vec::new();
    let mut i = idx;
    for layer in &layers[..layers.len() - 1] {
        let sib = if i % 2 == 0 { i + 1 } else { i - 1 };
        if sib < layer.len() {
            if sib < i {
                path.push(PathStep::Left(layer[sib]));
            } else {
                path.push(PathStep::Right(layer[sib]));
            }
        } else {
            // odd tail: the construction duplicates the last node
            path.push(PathStep::Dup);
        }
        i /= 2;
    }
    path
}

/// Verify that (leaf at idx) is committed under root.
/// 1:1 with f0b_air_proto.py::_merkle_check, INCLUDING the position binding.
pub fn merkle_check(root: u64, idx: usize, leaf: u64, path: &[PathStep]) -> bool {
    let mut h = leaf_hash(idx, leaf);
    for step in path {
        h = match step {
            PathStep::Dup => parent(&h, &h),
            PathStep::Right(sib) => parent(&h, sib),
            PathStep::Left(sib) => parent(sib, &h),
        };
    }
    u64::from_be_bytes(h[..8].try_into().unwrap()) == root
}

/// A proof for one tile's execution trace.
#[derive(Clone, Debug)]
pub struct TileAirProof {
    pub a: Vec<u64>,
    pub b: Vec<u64>,
    /// trace[0]=0, trace[t+1] = trace[t] + a_t*b_t
    pub trace: Vec<u64>,
    /// the raw input residuals, opened against the commitments
    pub a_res: Vec<u64>,
    pub b_res: Vec<u64>,
    pub a_paths: Vec<Vec<PathStep>>,
    pub b_paths: Vec<Vec<PathStep>>,
}

/// The AIR for one MatMul tile.
pub struct TileAir {
    pub q: u64,
    pub r: usize,
}

impl TileAir {
    pub fn new(q: u64, r: usize) -> Self {
        TileAir { q, r }
    }

    /// Build the execution trace the honest miner would produce.
    /// 1:1 with TileAIR.prove, including the CONTRACT that the trace must end
    /// exactly at the claimed accumulator — an earlier version asserted this
    /// only in prose here and checked it only in verify, so a caller could
    /// build a proof against a wrong acc and learn it from the verifier. The
    /// prover is the one that refuses.
    pub fn prove(
        &self,
        a: &[Vec<u64>],
        b: &[Vec<u64>],
        e: &[Vec<u64>],
        f: &[Vec<u64>],
        _ctx: u64,
        i: usize,
        j: usize,
        acc: u64,
    ) -> Result<TileAirProof, String> {
        let n = a.len();
        let m = n / self.r;
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let mut a_terms = Vec::new();
        let mut b_terms = Vec::new();
        let mut trace = vec![0u64];
        let mut run = 0u64;
        let mut a_res = Vec::new();
        let mut b_res = Vec::new();
        let mut a_paths = Vec::new();
        let mut b_paths = Vec::new();
        for l in 0..m {
            let av = (a[i * self.r][l * self.r] + e[i * self.r][l * self.r]) % self.q;
            let bv = (b[l * self.r][j * self.r] + f[l * self.r][j * self.r]) % self.q;
            run = (run + av * bv) % self.q;
            a_terms.push(av);
            b_terms.push(bv);
            a_res.push(a[i * self.r][l * self.r]);
            b_res.push(b[l * self.r][j * self.r]);
            a_paths.push(merkle_open(&flat_a, (i * self.r) * n + l * self.r));
            b_paths.push(merkle_open(&flat_b, (l * self.r) * n + j * self.r));
            trace.push(run);
        }
        if *trace.last().unwrap() != acc % self.q {
            return Err(format!(
                "trace ends at {}, not the claimed acc {}",
                trace.last().unwrap(),
                acc % self.q
            ));
        }
        Ok(TileAirProof {
            a: a_terms,
            b: b_terms,
            trace,
            a_res,
            b_res,
            a_paths,
            b_paths,
        })
    }

    /// Check the three AIR constraints and bind the witness to the inputs,
    /// WITHOUT recomputing the tile. a_commit / b_commit are Merkle roots over
    /// the flattened input matrices.
    /// 1:1 with TileAIR.verify.
    pub fn verify(
        &self,
        proof: &TileAirProof,
        acc: u64,
        e: &[Vec<u64>],
        f: &[Vec<u64>],
        i: usize,
        j: usize,
        a_commit: u64,
        b_commit: u64,
    ) -> bool {
        // DEGENERATE KERNEL FIRST: q == 0 divides by zero in the boundary
        // check just below (acc % self.q) and r == 0 divides by zero in
        // m = n / self.r. Both guards must come BEFORE any use, or the
        // check that exists to prevent the panic runs after it — which is
        // exactly how the tile-coordinate guard above was misplaced, and
        // how this one was too on its first attempt.
        if self.q == 0 || self.r == 0 {
            return false;
        }
        // (2) boundary: trace[0] = 0
        if proof.trace.first() != Some(&0) {
            return false;
        }
        // (3) boundary: trace[m] = claimed_acc
        if proof.trace.last() != Some(&(&(acc % self.q))) {
            return false;
        }
        let n = e.len();
        if f.len() != n {
            return false;
        }
        // ROW WIDTH of the public noise matrices: a ragged row would index
        // past its end and PANIC, and a panic in verify is a DoS rather than
        // a reject — the same class the G-layer kernel just got fixed for.
        if !e.iter().all(|row| row.len() == n) || !f.iter().all(|row| row.len() == n) {
            return false;
        }
        let m = n / self.r;
        if proof.a.len() != m
            || proof.b.len() != m
            || proof.trace.len() != m + 1
            || proof.a_res.len() != m
            || proof.b_res.len() != m
            || proof.a_paths.len() != m
            || proof.b_paths.len() != m
        {
            return false;
        }
        let flat_len = n * n;
        for l in 0..m {
            let a_res = proof.a_res[l];
            let b_res = proof.b_res[l];
            // the flattened index must be in range BEFORE it is used. This
            // guard existed already, but AFTER the e/f accesses below — a
            // check that runs after the thing it protects protects nothing,
            // and a wrong (i, j) panicked instead of rejecting. The order is
            // the fix.
            if (i * self.r) * n + l * self.r >= flat_len
                || (l * self.r) * n + j * self.r >= flat_len
            {
                return false;
            }
            // bind the witness to the committed inputs: the residual the
            // prover says it used must be committed at the right position
            if !merkle_check(a_commit, (i * self.r) * n + l * self.r, a_res, &proof.a_paths[l]) {
                return false;
            }
            if !merkle_check(b_commit, (l * self.r) * n + j * self.r, b_res, &proof.b_paths[l]) {
                return false;
            }
            // the noisy entry must be the residual plus the public noise
            let a_noise = (a_res + e[i * self.r][l * self.r]) % self.q;
            let b_noise = (b_res + f[l * self.r][j * self.r]) % self.q;
            if proof.a[l] != a_noise || proof.b[l] != b_noise {
                return false;
            }
            // (1) transition: trace[t+1] = trace[t] + a_t * b_t
            let want = (proof.trace[l] + proof.a[l] * proof.b[l]) % self.q;
            if proof.trace[l + 1] != want {
                return false;
            }
        }
        // the trace must END at the claimed accumulator — the boundary above
        // already covers this, restated because it is the property that makes
        // the proof a proof of THIS tile
        proof.trace.last() == Some(&((acc % self.q)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn toy(seed: u64) -> (Vec<Vec<u64>>, Vec<Vec<u64>>, Vec<Vec<u64>>, Vec<Vec<u64>>) {
        let mut s = seed;
        let mut mk = || {
            let mut out = vec![vec![0u64; 8]; 8];
            for i in 0..8 {
                for j in 0..8 {
                    s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                    out[i][j] = s % 97;
                }
            }
            out
        };
        (mk(), mk(), mk(), mk())
    }

    #[test]
    fn honest_air_prove_and_verify() {
        let (a, b, e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        // compute acc the honest way
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let a_commit = merkle_root(&flat_a);
        let b_commit = merkle_root(&flat_b);
        let proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
        assert!(air.verify(&proof, acc, &e, &f, i, j, a_commit, b_commit));
    }

    #[test]
    fn a_wrong_acc_is_rejected() {
        let (a, b, e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        // prove against the honest acc, then verify against a forged one
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
        let bad = (acc + 1) % 97;
        assert!(!air.verify(
            &proof,
            bad,
            &e,
            &f,
            i,
            j,
            merkle_root(&flat_a),
            merkle_root(&flat_b)
        ));
    }

    #[test]
    fn a_wrong_residual_is_rejected() {
        // the prover cannot claim it used a different input entry than the one
        // committed: the Merkle binding is by POSITION, not by value
        let (a, b, e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let a_commit = merkle_root(&flat_a);
        let b_commit = merkle_root(&flat_b);
        let mut proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
        // tamper: claim a different raw residual, keeping the path from the
        // honest position — the position binding must catch it
        proof.a_res[0] = (proof.a_res[0] + 1) % 97;
        assert!(!air.verify(&proof, acc, &e, &f, i, j, a_commit, b_commit));
    }

    #[test]
    fn a_broken_transition_is_rejected() {
        let (a, b, e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let a_commit = merkle_root(&flat_a);
        let b_commit = merkle_root(&flat_b);
        let mut proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
        // break the transition relation at step 1: the trace no longer follows
        // from a_t * b_t, so the accumulator is no longer the sum of products
        proof.trace[1] = (proof.trace[1] + 1) % 97;
        assert!(!air.verify(&proof, acc, &e, &f, i, j, a_commit, b_commit));
    }

    #[test]
    fn prove_refuses_a_wrong_acc() {
        // the CONTRACT: the prover is the one that refuses a mismatched acc,
        // rather than letting the caller learn it from the verifier
        let (a, b, e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        let bad = (acc + 1) % 97;
        assert!(air.prove(&a, &b, &e, &f, 777, i, j, bad).is_err());
    }

    /// Cross-language: a root computed in Rust must equal the one Python's
    /// _merkle_root produces for the same leaves, or a commitment does not
    /// cross the boundary and the two stacks cannot interoperate. The
    /// constant is the MEASURED Python output for these leaves (not a guess —
    /// a guessed constant in a cross-language test is the failure mode this
    /// test exists to catch).
    #[test]
    fn merkle_root_matches_python() {
        // the flattened A matrix of the toy suite, random.seed(20260925)
        let leaves: Vec<u64> = vec![
            81, 12, 44, 17, 83, 95, 43, 51, 23, 62, 54, 67, 9, 12, 45, 39, 75, 81, 27, 83, 8, 6, 3,
            42, 73, 25, 96, 28, 94, 5, 76, 41, 47, 67, 89, 23, 4, 58, 92, 84, 85, 74, 96, 71, 29,
            60, 31, 50, 32, 57, 68, 4, 16, 76, 25, 58, 38, 29, 40, 86, 8, 37, 4, 90,
        ];
        // measured: f0b_air_proto._merkle_root(leaves) at random.seed(20260925)
        let python_root: u64 = 7_776_579_357_882_374_515;
        assert_eq!(merkle_root(&leaves), python_root, "Rust Merkle root diverged from Python's");
    }

    /// OUT-OF-RANGE TILE COORDINATES must reject, not panic. The flat-index
    /// guard existed before this fix — but AFTER the e/f accesses it was
    /// meant to protect, so a wrong (i, j) unwound instead of rejecting. A
    /// check that runs after the thing it protects protects nothing.
    #[test]
    fn out_of_range_tile_coordinates_reject_instead_of_panicking() {
        let (a, b, e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let a_commit = merkle_root(&flat_a);
        let b_commit = merkle_root(&flat_b);
        let proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
        // the honest proof verifies
        assert!(air.verify(&proof, acc, &e, &f, i, j, a_commit, b_commit));
        // i beyond the grid
        assert!(
            !air.verify(&proof, acc, &e, &f, m, j, a_commit, b_commit),
            "an out-of-range i verified"
        );
        // j beyond the grid
        assert!(
            !air.verify(&proof, acc, &e, &f, i, m, a_commit, b_commit),
            "an out-of-range j verified"
        );
        // both far out of range
        assert!(
            !air.verify(&proof, acc, &e, &f, 9999, 9999, a_commit, b_commit),
            "far out-of-range coordinates verified"
        );
    }

    /// RAGGED NOISE MATRICES must reject, not panic — the same class the
    /// G-layer kernel just got fixed for, found here in the AIR verifier.
    #[test]
    fn ragged_noise_matrices_reject_instead_of_panicking() {
        let (a, b, mut e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let a_commit = merkle_root(&flat_a);
        let b_commit = merkle_root(&flat_b);
        let proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
        assert!(air.verify(&proof, acc, &e, &f, i, j, a_commit, b_commit));
        // truncate one row of E
        e[0].truncate(1);
        assert!(!air.verify(&proof, acc, &e, &f, i, j, a_commit, b_commit), "a ragged E verified");
        // a height mismatch on F
        let (a2, b2, _e2, f2) = toy(20260925);
        let mut short_f = f2;
        short_f.pop();
        let _ = (a2, b2);
        assert!(!air.verify(&proof, acc, &e, &short_f, i, j, a_commit, b_commit), "a short F verified");
    }

    /// TRUNCATED MERKLE PATHS must reject. a_paths/b_paths are indexed per
    /// step, so a proof with fewer paths than steps would panic; the length
    /// gate now covers them alongside the other witness vectors.
    #[test]
    fn proofs_with_truncated_paths_reject_instead_of_panicking() {
        let (a, b, e, f) = toy(20260925);
        let air = TileAir::new(97, 2);
        let n = 8;
        let m = n / 2;
        let (i, j) = (1, 2);
        let mut acc = 0u64;
        for l in 0..m {
            acc = (acc
                + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
                % 97;
        }
        let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
        let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
        let a_commit = merkle_root(&flat_a);
        let b_commit = merkle_root(&flat_b);
        let proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
        assert!(air.verify(&proof, acc, &e, &f, i, j, a_commit, b_commit));
        let mut truncated = proof.clone();
        truncated.a_paths.truncate(1);
        assert!(!air.verify(&truncated, acc, &e, &f, i, j, a_commit, b_commit), "truncated a_paths verified");
        let mut truncated_b = proof.clone();
        truncated_b.b_paths.truncate(0);
        assert!(!air.verify(&truncated_b, acc, &e, &f, i, j, a_commit, b_commit), "empty b_paths verified");
    }

    /// DEGENERATE kernel parameters divide by zero in the accumulator; a
    /// misconfigured chain must reject rather than crash the verifier.
    #[test]
    fn degenerate_air_kernel_parameters_reject_instead_of_panicking() {
        // The degenerate-kernel test needs only e and f from the toy: q == 0
        // and r == 0 reject before any tile is read, so a and b are unused
        // here by design, named with underscores so the intent is visible
        // rather than reading like an oversight.
        let (_a, _b, e, f) = toy(20260925);
        let zero_q = TileAir::new(0, 2);
        let zero_r = TileAir::new(97, 0);
        assert!(
            !zero_q.verify(&TileAirProof {
                a: vec![],
                b: vec![],
                trace: vec![0],
                a_res: vec![],
                b_res: vec![],
                a_paths: vec![],
                b_paths: vec![],
            }, 0, &e, &f, 1, 2, 0, 0),
            "q == 0 verified"
        );
        assert!(
            !zero_r.verify(&TileAirProof {
                a: vec![],
                b: vec![],
                trace: vec![0],
                a_res: vec![],
                b_res: vec![],
                a_paths: vec![],
                b_paths: vec![],
            }, 0, &e, &f, 1, 2, 0, 0),
            "r == 0 verified"
        );
    }

    // ---- DIRECT UNIT COVERAGE OF THE MERKLE PRIMITIVES (2026-09-27). These
    // were reached only through TileAir::prove/verify, so a regression in one
    // could only surface as a downstream symptom — and a proof that happened
    // not to exercise the failing path would hide it. Each test below makes
    // the primitive the unit under test.

    #[test]
    fn merkle_layers_and_root_match_for_power_of_two_and_odd_leaf_counts() {
        // the layer stack must terminate in a single root for both an even and
        // an odd leaf count; the odd case exercises the duplication path
        // (parent(h,h)) that merkle_open marks with Dup.
        for leaves in [vec![3u64, 1, 4, 1], vec![5, 9, 2, 6, 5]] {
            let layers = merkle_layers(&leaves);
            assert_eq!(layers[0].len(), leaves.len(), "the base layer is the leaves");
            assert_eq!(layers.last().unwrap().len(), 1, "the stack must end in one root");
            // the root is the first 8 bytes of the top node, big-endian
            let top = &layers.last().unwrap()[0];
            assert_eq!(merkle_root(&leaves), u64::from_be_bytes(top[..8].try_into().unwrap()));
        }
        // an empty leaf list is the documented degenerate case: root 0
        assert_eq!(merkle_root(&[]), 0, "an empty leaf list must commit to 0");
        // a single leaf: the root IS that leaf's hash, no duplication needed
        let one = merkle_root(&[42]);
        assert_eq!(one, u64::from_be_bytes(leaf_hash(0, 42)[..8].try_into().unwrap()));
    }

    #[test]
    fn merkle_open_and_check_roundtrip_on_every_index() {
        // for a leaf at ANY index, the path the prover opens must verify
        // against the root a verifier computes independently. Test every index
        // so the odd-tail Dup path and both sibling sides are each exercised.
        let leaves: Vec<u64> = vec![10, 20, 30, 40, 50, 60, 70]; // odd -> Dup path
        let root = merkle_root(&leaves);
        for idx in 0..leaves.len() {
            let path = merkle_open(&leaves, idx);
            assert!(merkle_check(root, idx, leaves[idx], &path),
                    "path for index {idx} failed to verify against the root");
        }
    }

    #[test]
    fn merkle_check_is_position_bound_and_value_bound() {
        // round-2 adversarial finding F9, tested at the primitive: leaf_hash
        // mixes the INDEX in, so a path from one index must NOT verify at
        // another. Without position binding, two leaves sharing a value let a
        // path replay — which is exactly the input-residual commitment bug
        // this hash exists to prevent.
        let leaves: Vec<u64> = vec![7, 7, 13, 7, 7]; // duplicate values, by design
        let root = merkle_root(&leaves);
        let path0 = merkle_open(&leaves, 0);
        assert!(merkle_check(root, 0, leaves[0], &path0), "the honest path must verify");
        // the same VALUE at a different index must NOT verify with index 0's path
        assert!(!merkle_check(root, 2, leaves[0], &path0),
                "a path replayed at a foreign index must fail");
        // the wrong value at the right index must fail
        assert!(!merkle_check(root, 0, 99, &path0),
                "a wrong leaf value must fail");
        // a path built for index 2 must not verify index 0's leaf
        let path2 = merkle_open(&leaves, 2);
        assert!(!merkle_check(root, 0, leaves[0], &path2),
                "a foreign path must not verify an honest leaf");
    }

    #[test]
    fn merkle_check_rejects_a_truncated_and_an_extended_path() {
        // the verifier folds leaf up through every step; a path of the wrong
        // LENGTH must not accidentally reach the root. A truncated path folds
        // fewer times and an extended path folds more — both must fail, which
        // is what makes the length an implicit part of the commitment.
        let leaves: Vec<u64> = vec![10, 20, 30, 40];
        let root = merkle_root(&leaves);
        let path = merkle_open(&leaves, 1);
        assert!(merkle_check(root, 1, leaves[1], &path));
        assert!(!merkle_check(root, 1, leaves[1], &path[..path.len() - 1]),
                "a truncated path must not verify");
        // an extended path: duplicate the last step, which changes the fold
        let mut extended = path.clone();
        extended.push(path.last().unwrap().clone());
        assert!(!merkle_check(root, 1, leaves[1], &extended),
                "an extended path must not verify");
    }

    #[test]
    fn leaf_hash_is_position_and_value_sensitive() {
        // the primitive at the bottom: same value at two positions must hash
        // differently, and two values at the same position must differ.
        assert_ne!(leaf_hash(0, 5), leaf_hash(1, 5), "leaf_hash must bind the index");
        assert_ne!(leaf_hash(0, 5), leaf_hash(0, 6), "leaf_hash must bind the value");
        assert_eq!(leaf_hash(0, 5), leaf_hash(0, 5), "leaf_hash must be deterministic");
    }
}

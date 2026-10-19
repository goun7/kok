//! The mesh kanıt (proof) layer: a G-layer mining certificate bound to the
//! commissioned task, signed under a W3C `did:key`, with a Sester-style
//! recomputable receipt.
//!
//! ## What the layer is for
//!
//! The KÖK G layer mines a Komargodski–Weinstein matrix-multiplication
//! certificate (`kok-poum::KwKernel`). A certificate alone proves *some*
//! MatMul cleared *some* target. The empirical study of Pearl's cuPOW
//! (Basu, arXiv 2606.04819, `docs/arastirma/pouw_ai_madenciligi_2026.md`
//! [S4]) measured what that gap costs in a deployed system: a network whose
//! verification "accepts random matrices by design" performs **zero useful
//! computation** while honestly solving its own puzzle. SNARKChain
//! (arXiv 2510.09729, [S6]) names the same defect theoretically — prior PoUW
//! proposals "fail to embed the integrity of the chain and the identity of
//! the miner into the puzzle solutions."
//!
//! This layer closes that gap at the receipt level, so the useful work is
//! **independently verifiable off-chain**:
//!
//! * the certificate is bound to the commissioned program and the exact input
//!   matrices, by commitments the verifier **recomputes from the document's
//!   own contents** (never taken on trust);
//! * the MatMul tile is **re-derived** by `KwKernel::verify`, which recomputes
//!   the strided accumulator at the claimed coordinates and checks the
//!   difficulty target — the useful work itself, not a hash of a claim;
//! * the miner is identified by a self-resolving `did:key` and the document is
//!   Ed25519-signed, so *who* mined is part of the proof, not a field a
//!   relayer may rewrite;
//! * the receipt is a sha256 hash chained to the previous proof, recomputable
//!   by a third party with **sha256 alone**, following the Sester receipt
//!   design (`sester/receipt.py`): no secrets, no server, no KÖK installed.
//!
//! ## The honest limit this layer states about itself
//!
//! A kanıt verifies that **the work the document describes was done and was
//! bound to the task the document names**. It does not verify that the task
//! was *wanted* by anyone — that is demand exogeneity, and Demirel
//! (ePrint 2026/1492, Theorem 1) proves endogenous receipts cannot certify
//! it. It also does not prove the matrices are interesting AI work: at the
//! toy scale (q=97, n=8) they are deterministic pseudo-random matrices, and
//! `program_commit` binds a program string this layer does not execute.
//! The binding is real; the usefulness is still asserted by the program
//! field, not measured by this layer.

pub mod did;

use kok_poum::{Certificate, KwKernel};
use sha2::{Digest, Sha256};

pub use did::{DidError, Keypair};

/// Version of the kanıt document format. A field-order or semantics change is
/// a new version; the canonical serialization below is frozen per version.
pub const PROOF_VERSION: u64 = 1;

/// The document type discriminator.
pub const PROOF_TYPE: &str = "kok.mining-proof";

/// The default task program string for the toy G-layer kanıt. Production
/// kanıt would name a real U-layer program; the toy binds the string, it does
/// not execute it.
pub const DEFAULT_PROGRAM: &str = "kok/g-layer-matmul-toy";

/// A mining-proof document. Every field is `Clone + Send`, and the structure
/// is deliberately flat so the canonical serialization (below) is a fixed,
/// auditable field order rather than a recursive walk that could drift.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct MiningProof {
    pub proof_version: u64,
    pub proof_type: String,
    pub layer: String,
    pub q: u64,
    pub n: u64,
    pub r: u64,
    pub task_program: String,
    pub task_fee: u64,
    pub task_burn_rate_per_mille: u64,
    /// sha256 over (domain | program | q | n | r). Recomputed by the verifier.
    pub program_commit: String,
    pub matrix_a: Vec<Vec<u64>>,
    pub matrix_b: Vec<Vec<u64>>,
    /// sha256 over (domain | flattened A | flattened B). Recomputed.
    pub input_commit: String,
    pub ctx: u64,
    pub nonce: u64,
    pub target: u64,
    /// The G-layer certificate: tile coordinates and accumulator value.
    pub cert_i: u64,
    pub cert_j: u64,
    pub cert_value: u64,
    pub cert_m: u64,
    /// `did:key:z...` — self-resolving, no registry.
    pub miner_did: String,
    /// Hex sha256 of the previous kanıt in the receipt chain, or 64 zeros for
    /// the first proof in a chain.
    pub receipt_prev: String,
    /// Hex sha256 of the canonical work envelope. Recomputed by the verifier.
    pub receipt_hash: String,
    /// Hex Ed25519 signature over the receipt digest under `miner_did`.
    pub signature: String,
}

/// Errors a kanıt can reject with. Each names the check that failed and the
/// field that failed it, because a verifier that prints only "invalid" makes
/// every forgery indistinguishable from a corrupted file.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProofError {
    /// The document's own declared commitments do not match the commitments
    /// recomputed from its contents. A document that lies about what it binds.
    CommitmentMismatch(String),
    /// The MatMul tile does not recompute, or the difficulty target is not met.
    /// Either the work was not done, or it was not the work described.
    UsefulWorkRejected(String),
    /// The receipt hash is not sha256 of the canonical envelope.
    ReceiptHashMismatch,
    /// The Ed25519 signature does not verify under the did in the document.
    SignatureRejected(DidError),
    /// Structural: wrong type/version, non-square or ragged matrices, or a
    /// certificate whose width does not match the input.
    Malformed(String),
    /// The commitment or signature field is not well-formed hex of the right
    /// length, or the did will not decode.
    Encoding(String),
}

impl std::fmt::Display for ProofError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ProofError::CommitmentMismatch(w) => {
                write!(f, "commitment mismatch: {w}")
            }
            ProofError::UsefulWorkRejected(w) => {
                write!(f, "useful work rejected: {w}")
            }
            ProofError::ReceiptHashMismatch => {
                write!(
                    f,
                    "receipt hash is not sha256 of the canonical work envelope"
                )
            }
            ProofError::SignatureRejected(e) => {
                write!(f, "signature rejected: {e}")
            }
            ProofError::Malformed(w) => write!(f, "malformed proof: {w}"),
            ProofError::Encoding(w) => write!(f, "encoding error: {w}"),
        }
    }
}

impl std::error::Error for ProofError {}

/// sha256, returned as a lowercase hex string.
pub fn sha256_hex(data: &[u8]) -> String {
    let d = Sha256::digest(data);
    hex::encode(d)
}

/// sha256, returned as the 32-byte digest.
pub fn sha256_digest(data: &[u8]) -> [u8; 32] {
    let d = Sha256::digest(data);
    let mut out = [0u8; 32];
    out.copy_from_slice(&d);
    out
}

/// The canonical work envelope: a **fixed-field, pipe-delimited** serialization
/// in the style of Sester's `receipt_canonical` (not RFC 8785 JCS — see the
/// note below). Determinism across languages is what makes the receipt
/// recomputable by a third party with nothing but sha256.
///
/// **Why fixed-field and not JCS.** JCS is a general algorithm over arbitrary
/// JSON; a cross-language reimplementation must get number serialization and
/// UTF-16 surrogate escaping exactly right to agree, and a kanıt that a
/// verifier cannot recompute byte-for-byte is worthless. A frozen field order
/// over a flat, all-integer document is auditable at reading distance and
/// trivially re-derived in Python, JS or shell. The trade-off is paid in
/// advance: any schema change bumps [`PROOF_VERSION`] and this function.
///
/// **Frozen field order (v1):** version, type, layer, q, n, r, program, fee,
/// burn rate, program_commit, input_commit, ctx, nonce, target, tile i, tile
/// j, tile value, tile m, receipt_prev. The signature, miner did and
/// receipt_hash are NOT part of this envelope — the hash covers the work, the
/// signature covers the hash, the did covers the signature's key.
pub fn work_canonical(p: &MiningProof) -> String {
    [
        p.proof_version.to_string(),
        p.proof_type.clone(),
        p.layer.clone(),
        p.q.to_string(),
        p.n.to_string(),
        p.r.to_string(),
        p.task_program.clone(),
        p.task_fee.to_string(),
        p.task_burn_rate_per_mille.to_string(),
        p.program_commit.clone(),
        p.input_commit.clone(),
        p.ctx.to_string(),
        p.nonce.to_string(),
        p.target.to_string(),
        p.cert_i.to_string(),
        p.cert_j.to_string(),
        p.cert_value.to_string(),
        p.cert_m.to_string(),
        p.receipt_prev.clone(),
    ]
    .join("|")
}

/// The commitment over the commissioned program and the chain dimensions.
/// Domain-separated so it cannot collide with the input commitment.
pub fn program_commit(program: &str, q: u64, n: u64, r: u64) -> String {
    sha256_hex(format!("kok.program.v1|{program}|{q}|{n}|{r}").as_bytes())
}

/// The commitment over the exact input matrices, row-major and flattened with
/// commas, so a document cannot swap one matrix for another and keep the same
/// commitment. This is the binding whose absence let Pearl's miners serve
/// their own matrices (Basu [S4]; the project's own TV-82 measured the same
/// substitution in a mock before the binding was added).
pub fn input_commit(a: &[Vec<u64>], b: &[Vec<u64>]) -> String {
    let flat = |m: &[Vec<u64>]| {
        m.iter()
            .flatten()
            .map(|v| v.to_string())
            .collect::<Vec<_>>()
            .join(",")
    };
    sha256_hex(format!("kok.input.v1|{}|{}", flat(a), flat(b)).as_bytes())
}

/// Hex of 64 zero bytes — the `receipt_prev` of the first kanıt in a chain,
/// i.e. "this proof stands on nothing".
pub fn genesis_prev() -> String {
    "0".repeat(64)
}

/// Compute (do not trust) the receipt hash of a document's work envelope.
pub fn receipt_hash_of(p: &MiningProof) -> String {
    sha256_hex(work_canonical(p).as_bytes())
}

/// Sign the receipt digest under a keypair. The signed message is the digest
/// prefixed by the did layer's domain separator, so this signature cannot be
/// replayed as an attestation over some other bytes.
pub fn sign_receipt(secret: &[u8; 32], p: &MiningProof) -> [u8; 64] {
    did::sign(secret, &sha256_digest(work_canonical(p).as_bytes()))
}

/// Mine a kanıt: grind a G-layer certificate over the given matrices until the
/// target clears, then bind and sign it. This is the honest path — the same
/// `KwKernel::prove` the node uses, so a kanıt and a block are produced by the
/// same code, not by two implementations that could drift.
#[allow(clippy::too_many_arguments)]
pub fn mine(
    kernel: &KwKernel,
    a: &[Vec<u64>],
    b: &[Vec<u64>],
    ctx: u64,
    target: u64,
    program: &str,
    fee: u64,
    burn_rate_per_mille: u64,
    miner: &Keypair,
    receipt_prev: &str,
) -> Result<MiningProof, ProofError> {
    let n = a.len();
    if n == 0 || b.len() != n {
        return Err(ProofError::Malformed(
            "matrices must be square and equal".into(),
        ));
    }
    if a.iter().any(|row| row.len() != n) || b.iter().any(|row| row.len() != n) {
        return Err(ProofError::Malformed("ragged matrix rows".into()));
    }
    if kernel.r == 0 || !n.is_multiple_of(kernel.r) {
        return Err(ProofError::Malformed(format!(
            "n={n} is not divisible by r={}",
            kernel.r
        )));
    }
    let mut nonce = 0u64;
    let cert = loop {
        nonce += 1;
        if let Some(c) = kernel.prove(a, b, ctx, nonce, target) {
            break c;
        }
        // Unbounded loop guards: prove returns None forever for a target no
        // tile can clear (target==0 is guarded inside prove). A caller that
        // hands an impossible target would spin here; the toy target 2^1
        // clears in a few hundred nonces at n=8.
        if nonce > 100_000_000 {
            return Err(ProofError::UsefulWorkRejected(
                "no tile cleared the target in 100M nonces; target is likely impossible".into(),
            ));
        }
    };
    let mut proof = MiningProof {
        proof_version: PROOF_VERSION,
        proof_type: PROOF_TYPE.to_string(),
        layer: "G".to_string(),
        q: kernel.q,
        n: n as u64,
        r: kernel.r as u64,
        task_program: program.to_string(),
        task_fee: fee,
        task_burn_rate_per_mille: burn_rate_per_mille,
        program_commit: program_commit(program, kernel.q, n as u64, kernel.r as u64),
        matrix_a: a.to_vec(),
        matrix_b: b.to_vec(),
        input_commit: input_commit(a, b),
        ctx,
        nonce,
        target,
        cert_i: cert.i as u64,
        cert_j: cert.j as u64,
        cert_value: cert.value,
        cert_m: cert.m as u64,
        miner_did: miner.did.clone(),
        receipt_prev: if receipt_prev.is_empty() {
            genesis_prev()
        } else {
            receipt_prev.to_string()
        },
        receipt_hash: String::new(),
        signature: String::new(),
    };
    proof.receipt_hash = receipt_hash_of(&proof);
    let sig = sign_receipt(&miner.secret, &proof);
    proof.signature = hex::encode(sig);
    Ok(proof)
}

/// Verify a kanıt **independently**: re-derive every load-bearing claim from
/// the document's own contents. Nothing in the document is trusted except the
/// fields used to recompute the others.
///
/// Returns `Ok(())` when every check passes, or the first `Err` that fails.
/// The checks are ordered cheapest-first, so a malformed document rejects
/// before any signature arithmetic runs.
pub fn verify(p: &MiningProof) -> Result<(), ProofError> {
    // 1. STRUCTURAL: the document declares what it is.
    if p.proof_type != PROOF_TYPE {
        return Err(ProofError::Malformed(format!(
            "proof_type {:?}, expected {PROOF_TYPE:?}",
            p.proof_type
        )));
    }
    if p.proof_version != PROOF_VERSION {
        return Err(ProofError::Malformed(format!(
            "proof_version {}, this verifier reads {PROOF_VERSION}",
            p.proof_version
        )));
    }
    if p.layer != "G" {
        return Err(ProofError::Malformed(format!(
            "layer {:?}, this verifier reads G-layer kanıt only",
            p.layer
        )));
    }
    // receipt_prev is either 64 hex chars of a sha256, or the 64-zero genesis.
    if p.receipt_prev.len() != 64 || !p.receipt_prev.chars().all(|c| c.is_ascii_hexdigit()) {
        return Err(ProofError::Malformed(
            "receipt_prev must be 64 hex chars (a sha256, or 64 zeros for genesis)".into(),
        ));
    }

    // 2. MATRIX SHAPE, before any indexing. A ragged matrix would panic in the
    // tile re-derivation; the check has to precede the arithmetic so a crafted
    // document rejects instead of crashing the verifier (the same class as
    // KwKernel::verify's own row-width gate).
    let n = p.n as usize;
    if n == 0 || p.matrix_a.len() != n || p.matrix_b.len() != n {
        return Err(ProofError::Malformed(format!(
            "declared n={n} but matrix_a has {} rows and matrix_b has {}",
            p.matrix_a.len(),
            p.matrix_b.len()
        )));
    }
    if p.matrix_a.iter().any(|row| row.len() != n) || p.matrix_b.iter().any(|row| row.len() != n) {
        return Err(ProofError::Malformed("ragged matrix rows".into()));
    }
    if p.r == 0 || !n.is_multiple_of(p.r as usize) {
        return Err(ProofError::Malformed(format!(
            "n={n} is not divisible by r={}",
            p.r
        )));
    }
    // The certificate's width must equal n/r, or it was mined for another size
    // (the round-4 width-binding finding).
    if p.cert_m != p.n / p.r {
        return Err(ProofError::Malformed(format!(
            "cert_m={} but n/r = {}/{} = {}",
            p.cert_m,
            p.n,
            p.r,
            p.n / p.r
        )));
    }

    // 3. COMMITMENTS — recomputed from the document's own fields. A document
    // that declares a commitment inconsistent with its content rejects here,
    // which is what stops a miner from serving a matrix it prefers while
    // claiming the commissioned program.
    let want_program = program_commit(&p.task_program, p.q, p.n, p.r);
    if p.program_commit != want_program {
        return Err(ProofError::CommitmentMismatch(format!(
            "program_commit is {:?}, recomputed {:?}",
            p.program_commit, want_program
        )));
    }
    let want_input = input_commit(&p.matrix_a, &p.matrix_b);
    if p.input_commit != want_input {
        return Err(ProofError::CommitmentMismatch(format!(
            "input_commit is {:?}, recomputed {:?}",
            p.input_commit, want_input
        )));
    }

    // 4. THE USEFUL WORK — re-derive the MatMul tile at its own coordinates
    // and check the difficulty target. KwKernel::verify recomputes the strided
    // accumulator from A+noise and B+noise under the ctx, so the certificate is
    // bound to (A, B, ctx, nonce) by recomputation, never by the miner's claim.
    let kernel = KwKernel::new(p.q, p.r as usize);
    let cert = Certificate {
        i: p.cert_i as usize,
        j: p.cert_j as usize,
        value: p.cert_value,
        m: p.cert_m as usize,
    };
    if !kernel.verify(&cert, &p.matrix_a, &p.matrix_b, p.ctx, p.nonce, p.target) {
        return Err(ProofError::UsefulWorkRejected(format!(
            "tile (i={}, j={}, value={}) does not recompute at nonce {} under target {}",
            p.cert_i, p.cert_j, p.cert_value, p.nonce, p.target
        )));
    }

    // 5. THE RECEIPT — sha256 of the canonical envelope, recomputable by
    // anyone with sha256 alone. A single changed field makes this fail.
    let want_hash = receipt_hash_of(p);
    if p.receipt_hash != want_hash {
        return Err(ProofError::ReceiptHashMismatch);
    }

    // 6. THE SIGNATURE — recover the public key from the did and verify. The
    // did is self-resolving, so no registry, no network, no trusted key list.
    let sig_bytes = hex::decode(&p.signature)
        .map_err(|e| ProofError::Encoding(format!("signature is not hex: {e}")))?;
    if sig_bytes.len() != 64 {
        return Err(ProofError::Encoding(format!(
            "signature is {} bytes, expected 64 (Ed25519)",
            sig_bytes.len()
        )));
    }
    let mut sig = [0u8; 64];
    sig.copy_from_slice(&sig_bytes);
    did::verify_with_did(
        &p.miner_did,
        &sha256_digest(work_canonical(p).as_bytes()),
        &sig,
    )
    .map_err(ProofError::SignatureRejected)?;

    Ok(())
}

/// Serialize a kanıt to the on-disk JSON shape, field order canonical so the
/// file a human reads is also the file the verifier recomputes over.
pub fn to_json(p: &MiningProof) -> serde_json::Result<String> {
    serde_json::to_string_pretty(p)
}

/// Deserialize a kanıt from JSON. Structural validation happens in [`verify`];
/// this only parses.
pub fn from_json(text: &str) -> serde_json::Result<MiningProof> {
    serde_json::from_str(text)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The canonical toy matrices from `kok-poum::canonical`, so a kanıt and a
    /// block mine the same input (see the CANONICAL PARITY test in kok-poum).
    fn toy(seed: u64) -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
        let mut a = vec![vec![0u64; TOY_N]; TOY_N];
        let mut b = vec![vec![0u64; TOY_N]; TOY_N];
        let mut s = seed;
        for i in 0..TOY_N {
            for j in 0..TOY_N {
                s = s
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                a[i][j] = s % TOY_Q;
                s = s
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                b[i][j] = s % TOY_Q;
            }
        }
        (a, b)
    }

    use kok_poum::{TOY_N, TOY_Q, TOY_R};
    use rand_core::OsRng;

    /// An honest kanıt verifies end to end: commitments recompute, the tile
    /// re-derives, the receipt hash matches, the signature verifies.
    #[test]
    fn an_honest_mining_proof_verifies_completely() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::generate(&mut OsRng);
        let proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        assert!(proof.signature.len() == 128);
        verify(&proof).expect("an honest kanıt must verify");
    }

    /// A kanıt that survives JSON round-trip still verifies — the canonical
    /// envelope is computed from fields, not from file bytes, so the file can
    /// be reformatted without breaking the signature.
    #[test]
    fn a_kanit_survives_a_json_round_trip() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(11);
        let miner = Keypair::from_seed(&[9; 32]);
        let proof = mine(
            &kernel,
            &a,
            &b,
            42,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        let text = to_json(&proof).unwrap();
        let back = from_json(&text).unwrap();
        assert_eq!(back, proof);
        assert!(verify(&back).is_ok());
    }

    /// Forging the tile value: the certificate claims a different accumulator
    /// than the MatMul produces. The useful-work check must reject it — this is
    /// the Pearl failure mode, caught by recomputation rather than by trust.
    #[test]
    fn a_forged_tile_value_is_rejected() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[1; 32]);
        let mut proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        proof.cert_value = (proof.cert_value + 1) % TOY_Q;
        // the receipt and signature now also cover the lie; the useful-work
        // check is the one that fires first on the recomputed tile
        assert!(matches!(
            verify(&proof),
            Err(ProofError::UsefulWorkRejected(_))
        ));
    }

    /// Swapping the input matrices for the miner's own: the input commitment
    /// is recomputed from the document, so the declared commitment no longer
    /// matches — exactly the substitution TV-82 measured in the mock.
    #[test]
    fn foreign_matrices_reject_on_the_commitment() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[2; 32]);
        let mut proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        // miner serves a different B while keeping every declared commitment
        proof.matrix_b = toy(999).1;
        assert!(matches!(
            verify(&proof),
            Err(ProofError::CommitmentMismatch(_))
        ));
    }

    /// A kanıt replayed under another ctx does not verify: the tile is bound to
    /// the ctx through the noise pair, and recomputing under a different ctx
    /// yields a different accumulator.
    #[test]
    fn a_kanit_replayed_under_another_ctx_rejects() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[3; 32]);
        let mut proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        proof.ctx += 1;
        assert!(matches!(
            verify(&proof),
            Err(ProofError::UsefulWorkRejected(_))
        ));
    }

    /// A receipt-hash that does not recompute rejects, so a relayer cannot
    /// rewrite a field of a signed kanıt without breaking the file.
    #[test]
    fn a_rewritten_receipt_hash_is_rejected() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[4; 32]);
        let mut proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        proof.receipt_hash = "f".repeat(64);
        assert_eq!(verify(&proof), Err(ProofError::ReceiptHashMismatch));
    }

    /// A signature stripped and re-signed by a different did fails: *who*
    /// mined is part of the proof, not a relayer-editable field.
    #[test]
    fn a_signature_from_the_wrong_did_is_rejected() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[5; 32]);
        let mut proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        let other = Keypair::from_seed(&[6; 32]);
        proof.miner_did = other.did.clone();
        // the signature still covers the receipt, but under the other key
        assert!(matches!(
            verify(&proof),
            Err(ProofError::SignatureRejected(_))
        ));
    }

    /// Two kanıt chained by receipt_prev both verify, and the chain is real:
    /// the parent's hash is the child's prev, recomputed from the parent.
    #[test]
    fn a_receipt_chain_links_parent_hash_to_child_prev() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[7; 32]);
        let parent = mine(
            &kernel,
            &a,
            &b,
            100,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        assert!(verify(&parent).is_ok());
        let child = mine(
            &kernel,
            &a,
            &b,
            101,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &parent.receipt_hash,
        )
        .unwrap();
        assert_eq!(child.receipt_prev, parent.receipt_hash);
        assert!(verify(&child).is_ok());
        // the binding is load-bearing: tampering the parent's work breaks the
        // child's prev, which the child then carries visibly
        let mut broken_parent = parent.clone();
        broken_parent.cert_value = (broken_parent.cert_value + 1) % TOY_Q;
        assert!(verify(&broken_parent).is_err());
        assert_ne!(receipt_hash_of(&broken_parent), child.receipt_prev);
    }

    /// A kanıt declaring a certificate width that does not match the input
    /// rejects before any arithmetic — the width binding, checked upstream.
    #[test]
    fn a_certificate_mined_for_another_width_rejects() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[8; 32]);
        let mut proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        proof.cert_m += 1;
        assert!(matches!(verify(&proof), Err(ProofError::Malformed(_))));
    }

    /// A document claiming a future version or a different type rejects with a
    /// named reason, so an unrelated JSON file is never silently accepted.
    #[test]
    fn a_document_of_another_type_or_version_rejects() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(20260929);
        let miner = Keypair::from_seed(&[10; 32]);
        let mut proof = mine(
            &kernel,
            &a,
            &b,
            777,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        proof.proof_version = 2;
        assert!(matches!(verify(&proof), Err(ProofError::Malformed(_))));
        let mut proof2 = proof.clone();
        proof2.proof_version = 1;
        proof2.proof_type = "something.else".into();
        assert!(matches!(verify(&proof2), Err(ProofError::Malformed(_))));
    }

    /// The canonical envelope is exactly the documented 19 pipe-separated
    /// fields — pinned so a refactor cannot silently change the receipt.
    #[test]
    fn the_canonical_envelope_has_the_documented_shape() {
        let kernel = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy(1);
        let miner = Keypair::from_seed(&[12; 32]);
        let proof = mine(
            &kernel,
            &a,
            &b,
            5,
            1u64 << 1,
            DEFAULT_PROGRAM,
            0,
            0,
            &miner,
            &genesis_prev(),
        )
        .unwrap();
        let canon = work_canonical(&proof);
        assert_eq!(canon.split('|').count(), 19);
        // the hash is 64 hex chars over exactly those bytes
        assert_eq!(proof.receipt_hash.len(), 64);
        assert_eq!(proof.receipt_hash, sha256_hex(canon.as_bytes()));
    }

    /// Program and input commitments are different values and both
    /// domain-separated: neither equals a raw sha256 of its fields, so the
    /// domain tags are load-bearing rather than decoration.
    #[test]
    fn commitments_are_domain_separated_and_distinct() {
        let (a, b) = toy(3);
        let pc = program_commit(DEFAULT_PROGRAM, TOY_Q, TOY_N as u64, TOY_R as u64);
        let ic = input_commit(&a, &b);
        assert_ne!(pc, ic);
        assert_ne!(
            pc,
            sha256_hex(format!("{}|{}|{}|{}", DEFAULT_PROGRAM, TOY_Q, TOY_N, TOY_R).as_bytes())
        );
    }
}

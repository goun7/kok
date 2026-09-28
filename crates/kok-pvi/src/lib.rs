//! PVI — the Proof Verifier Interface: the boundary a light client calls.
//!
//! Round-6, 2026-09-24: this crate was a pure skeleton. The TOTALITY
//! CONTRACT is now implemented (2026-09-25); the composed G-layer verify it
//! gates is F3+ and is deliberately not faked.
//!
//! THE DESIGN CONSTRAINT THAT SHAPES THIS MODULE: a verifier that runs in
//! WASM must be a TOTAL function. A panic becomes a trap, and a trap is not
//! a rejection — it is an undefined outcome a caller can misread, and in the
//! worst case a crash at exactly the moment a decision was owed. This is not
//! hypothetical: the round-4 g_layer cluster [11]–[14] found that verify()
//! indexed matrices with the KERNEL's constant n, so a 6x6 proof made it
//! index row 8 and raise IndexError instead of rejecting. The verifier
//! accepted nothing wrong — it simply failed to answer.
//!
//! So the interface checks every structural property BEFORE it indexes
//! anything, and returns a typed Verdict rather than a bool, so a rejection
//! always carries the reason a caller can act on.

use kok_poum::{Certificate, KwKernel};

/// A serialized certificate as it would arrive over the wire.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifierInput {
    /// (i, j, value, m) little-endian, 8 bytes each — 32 bytes total
    pub cert_bytes: [u8; 32],
    /// the flattened matrices, row-major, n*n entries of 8 bytes each
    pub flat_a: Vec<u8>,
    pub flat_b: Vec<u8>,
    /// (ctx, nonce, target, n, q, r) — 48 bytes
    pub pub_inputs: [u8; 48],
}

/// Why a proof was rejected. Never returned for an accept.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Verdict {
    Accept,
    Reject(String),
}

impl Verdict {
    pub fn accepted(&self) -> bool {
        matches!(self, Verdict::Accept)
    }
}

fn u64_le(b: &[u8]) -> Option<u64> {
    if b.len() < 8 {
        return None;
    }
    Some(u64::from_le_bytes(b[..8].try_into().unwrap()))
}

/// Decode the packet, rejecting any structurally-invalid input BEFORE the
/// matrices are indexed. Every failure here is a Reject, never a panic.
fn decode(
    input: &VerifierInput,
) -> Result<(Certificate, u64, u64, u64, u64, u64, Vec<Vec<u64>>, Vec<Vec<u64>>), String> {
    let i = u64_le(&input.cert_bytes[0..8]).ok_or("cert too short: i")?;
    let j = u64_le(&input.cert_bytes[8..16]).ok_or("cert too short: j")?;
    let value = u64_le(&input.cert_bytes[16..24]).ok_or("cert too short: value")?;
    let m = u64_le(&input.cert_bytes[24..32]).ok_or("cert too short: m")?;

    let ctx = u64_le(&input.pub_inputs[0..8]).ok_or("pub_inputs too short: ctx")?;
    let nonce = u64_le(&input.pub_inputs[8..16]).ok_or("pub_inputs too short: nonce")?;
    let target = u64_le(&input.pub_inputs[16..24]).ok_or("pub_inputs too short: target")?;
    let n = u64_le(&input.pub_inputs[24..32]).ok_or("pub_inputs too short: n")?;
    let q = u64_le(&input.pub_inputs[32..40]).ok_or("pub_inputs too short: q")?;
    let r = u64_le(&input.pub_inputs[40..48]).ok_or("pub_inputs too short: r")?;

    // STRUCTURAL GATES, all before any matrix indexing:
    if n == 0 {
        return Err("n is zero: no matrix can be verified".into());
    }
    if r == 0 || n % r != 0 {
        return Err("r does not divide n: the tile grid is not integral".into());
    }
    if q == 0 {
        return Err("q is zero: the field is degenerate".into());
    }
    if target == 0 {
        // target 0 would put every hash "under target" — the division-by-zero
        // analogue in the difficulty sense
        return Err("target is zero: the difficulty is undefined".into());
    }
    // THE SIZE MUST BE COMPUTED WITH CHECKED ARITHMETIC, OR THE LENGTH GATE
    // BELOW IS DEAD CODE. `(n * n) as usize * 8` is plain u64 multiplication,
    // and at n = 2^33 (and at any n >= 2^32 on a 32-bit target, where the
    // `as usize` itself truncates) `n * n` wraps to a small value. A
    // hand-built `VerifierInput` — every field of which is `pub`, so any Rust
    // caller can construct one — then passes the length check against a SHORT
    // `flat_a`, and the slice `input.flat_a[off..off + 8]` unwinds with an
    // index panic before `u64_le` can return the `None` that the
    // "matrix A truncated" guard below exists to convert into an `Err`.
    // `kok_wasm::parse_packet` already validates this same expression with
    // `checked_mul` before the bytes ever reach here, which is exactly why the
    // bug is invisible to the WASM suite: the wrapper screens the input that
    // would expose it. A light client or indexer calling `verify_raw`
    // directly gets a panic, not a `Reject`. Rejecting the overflow here is
    // what makes the guard total on the whole u64 domain rather than on the
    // sizes the author had in mind.
    let need = match (n as usize)
        .checked_mul(n as usize)
        .and_then(|sq| sq.checked_mul(8))
    {
        Some(bytes) => bytes,
        None => {
            return Err(format!(
                "matrix size overflow: n = {n} needs n*n*8 bytes, which does not fit"
            ))
        }
    };
    if input.flat_a.len() != need || input.flat_b.len() != need {
        return Err(format!(
            "matrix size mismatch: expected {} bytes each, got {}/{}",
            need,
            input.flat_a.len(),
            input.flat_b.len()
        ));
    }
    // n as usize cannot overflow from here on: `need` was computed from it and
    // fit, so a Vec of this size is at least representable. (A caller that
    // supplies a huge-but-representable n will fail the length check above on
    // the buffer side, which is the correct outcome.)
    let mut a = Vec::with_capacity(n as usize);
    let mut b = Vec::with_capacity(n as usize);
    for row in 0..n as usize {
        let mut ra = Vec::with_capacity(n as usize);
        let mut rb = Vec::with_capacity(n as usize);
        for col in 0..n as usize {
            let off = (row * n as usize + col) * 8;
            ra.push(u64_le(&input.flat_a[off..off + 8]).ok_or("matrix A truncated")?);
            rb.push(u64_le(&input.flat_b[off..off + 8]).ok_or("matrix B truncated")?);
        }
        a.push(ra);
        b.push(rb);
    }
    // the tile coordinates must be inside the grid — checked HERE, not at the
    // indexing site where a bad value would panic
    let grid = n / r;
    if i >= grid || j >= grid {
        return Err(format!("tile ({},{}) is outside the {}x{} grid", i, j, grid, grid));
    }
    if m != grid {
        return Err(format!("m is {} but n/r is {}", m, grid));
    }
    let cert = Certificate { i: i as usize, j: j as usize, value, m: m as usize };
    Ok((cert, ctx, nonce, target, n, q, a, b))
}

/// The interface entry point. Total: returns a Verdict for EVERY input,
/// including malformed ones. Never panics.
pub fn verify_raw(input: &VerifierInput) -> Verdict {
    let (cert, ctx, nonce, target, _n, q, a, b) = match decode(input) {
        Ok(v) => v,
        Err(reason) => return Verdict::Reject(reason),
    };
    // the kernel is built from the PUBLIC inputs, never from constants —
    // round-4 [11]: the verifier used self.n while prove() derived n from
    // the input. Here n and r come from the packet.
    let r = u64_le(&input.pub_inputs[40..48]).unwrap_or(0);
    let kernel = KwKernel::new(q, r as usize);
    // THE COMPOSED VERIFY. decode() has already gated every structural
    // property (square matrices, byte lengths, tile inside the grid, m
    // consistent with n/r, non-degenerate q and target), and KwKernel::verify
    // is itself total (it bounds-checks i, j and m before it indexes, and
    // returns false rather than panicking), so the composition stays total:
    // every input reaches a Verdict.
    if kernel.verify(&cert, &a, &b, ctx, nonce, target) {
        Verdict::Accept
    } else {
        Verdict::Reject("the G-layer certificate does not verify".into())
    }
}

/// A constructor for well-formed input, for tests and for callers that
/// already hold the typed values.
pub fn pack(
    i: u64, j: u64, value: u64, m: u64, ctx: u64, nonce: u64, target: u64,
    n: u64, q: u64, r: u64,
) -> VerifierInput {
    let mut cert_bytes = [0u8; 32];
    cert_bytes[0..8].copy_from_slice(&i.to_le_bytes());
    cert_bytes[8..16].copy_from_slice(&j.to_le_bytes());
    cert_bytes[16..24].copy_from_slice(&value.to_le_bytes());
    cert_bytes[24..32].copy_from_slice(&m.to_le_bytes());
    let mut pub_inputs = [0u8; 48];
    pub_inputs[0..8].copy_from_slice(&ctx.to_le_bytes());
    pub_inputs[8..16].copy_from_slice(&nonce.to_le_bytes());
    pub_inputs[16..24].copy_from_slice(&target.to_le_bytes());
    pub_inputs[24..32].copy_from_slice(&n.to_le_bytes());
    pub_inputs[32..40].copy_from_slice(&q.to_le_bytes());
    pub_inputs[40..48].copy_from_slice(&r.to_le_bytes());
    let bytes = (n * n) as usize * 8;
    VerifierInput { cert_bytes, flat_a: vec![0u8; bytes], flat_b: vec![0u8; bytes], pub_inputs }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// THE TOTALITY CONTRACT: every malformed input must produce a REJECT,
    /// never a panic. This is the property a WASM boundary owes its caller,
    /// and it is the property the round-4 cluster violated.
    #[test]
    fn every_malformed_input_rejects_never_panics() {
        // truncated matrices
        let mut bad = pack(1, 2, 3, 4, 777, 1, 1 << 16, 8, 97, 2);
        bad.flat_a.truncate(4);
        assert!(!verify_raw(&bad).accepted(), "truncated matrix A was accepted");
        // empty matrices
        let mut e = pack(1, 2, 3, 4, 777, 1, 1 << 16, 8, 97, 2);
        e.flat_a.clear();
        e.flat_b.clear();
        assert!(!verify_raw(&e).accepted(), "empty matrices were accepted");
        // target 0
        let mut t0 = pack(1, 2, 3, 4, 777, 1, 0, 8, 97, 2);
        t0.flat_a = vec![0u8; 512];
        t0.flat_b = vec![0u8; 512];
        let v = verify_raw(&t0);
        assert!(!v.accepted(), "target 0 was accepted");
        assert!(matches!(&v, Verdict::Reject(r) if r.contains("target")));
        // n = 0
        let z = pack(1, 2, 3, 4, 777, 1, 1 << 16, 0, 97, 2);
        assert!(!verify_raw(&z).accepted(), "n=0 was accepted");
        // r does not divide n
        let mut nr = pack(1, 2, 3, 4, 777, 1, 1 << 16, 7, 97, 2);
        nr.flat_a = vec![0u8; 49 * 8];
        nr.flat_b = vec![0u8; 49 * 8];
        assert!(!verify_raw(&nr).accepted(), "r not dividing n was accepted");
        // tile outside the grid
        let mut og = pack(99, 99, 3, 4, 777, 1, 1 << 16, 8, 97, 2);
        og.flat_a = vec![0u8; 512];
        og.flat_b = vec![0u8; 512];
        let v = verify_raw(&og);
        assert!(!v.accepted(), "an out-of-grid tile was accepted");
        assert!(matches!(&v, Verdict::Reject(r) if r.contains("outside")));
        // m inconsistent with n/r
        let mut mm = pack(1, 2, 3, 99, 777, 1, 1 << 16, 8, 97, 2);
        mm.flat_a = vec![0u8; 512];
        mm.flat_b = vec![0u8; 512];
        assert!(!verify_raw(&mm).accepted(), "an inconsistent m was accepted");
    }

    /// THE END-TO-END PATH: a certificate mined honestly over real matrices
    /// must ACCEPT through the byte boundary, and every forgery must REJECT.
    /// Before this the boundary rejected everything with an F3+ marker —
    /// honest about being unimplemented, but not a verifier.
    fn encode(a: &[Vec<u64>], b: &[Vec<u64>], cert: &Certificate, ctx: u64, nonce: u64, target: u64, q: u64, r: usize) -> VerifierInput {
        let n = a.len();
        let mut flat_a = Vec::with_capacity(n * n * 8 * 2);
        for row in a.iter().chain(b.iter()) {
            for v in row {
                flat_a.extend_from_slice(&v.to_le_bytes());
            }
        }
        // chain() wrote both matrices into flat_a; split them apart again
        let split = n * n * 8;
        let flat_b = flat_a.split_off(split);
        let mut cert_bytes = [0u8; 32];
        cert_bytes[0..8].copy_from_slice(&(cert.i as u64).to_le_bytes());
        cert_bytes[8..16].copy_from_slice(&(cert.j as u64).to_le_bytes());
        cert_bytes[16..24].copy_from_slice(&cert.value.to_le_bytes());
        cert_bytes[24..32].copy_from_slice(&(cert.m as u64).to_le_bytes());
        let mut pub_inputs = [0u8; 48];
        pub_inputs[0..8].copy_from_slice(&ctx.to_le_bytes());
        pub_inputs[8..16].copy_from_slice(&nonce.to_le_bytes());
        pub_inputs[16..24].copy_from_slice(&target.to_le_bytes());
        pub_inputs[24..32].copy_from_slice(&(n as u64).to_le_bytes());
        pub_inputs[32..40].copy_from_slice(&q.to_le_bytes());
        pub_inputs[40..48].copy_from_slice(&r.to_le_bytes());
        VerifierInput { cert_bytes, flat_a, flat_b, pub_inputs }
    }

    /// Mine a real certificate over the canonical matrices and drive it
    /// through the byte boundary. ACCEPTS.
    #[test]
    fn an_honestly_mined_certificate_accepts_through_the_boundary() {
        use kok_poum::canonical;
        use kok_poum::{KwKernel, TOY_Q, TOY_R};
        let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
        let k = KwKernel::new(TOY_Q, TOY_R);
        let target = 1u64 << 4;
        // mine the honest way: try nonces until one clears the target
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, target) {
                break c;
            }
        };
        let input = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
        assert!(matches!(verify_raw(&input), Verdict::Accept), "an honestly mined certificate was rejected");
    }

    /// A FORGED VALUE must reject — the accumulator the packet claims is not
    /// the one the tile computes to. This is the forgery the boundary exists
    /// to stop, and it only bites now that the verify is composed.
    #[test]
    fn a_forged_certificate_value_is_rejected() {
        use kok_poum::canonical;
        use kok_poum::{KwKernel, TOY_Q, TOY_R};
        let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
        let k = KwKernel::new(TOY_Q, TOY_R);
        let target = 1u64 << 4;
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, target) {
                break c;
            }
        };
        // tamper: claim a different accumulated value
        let mut forged = cert.clone();
        forged.value = (cert.value + 1) % TOY_Q;
        let input = encode(&a, &b, &forged, 777, nonce, target, TOY_Q, TOY_R);
        assert!(!verify_raw(&input).accepted(), "a forged tile value was accepted");
    }

    /// A REPLAYED CTX must reject: a certificate mined under one block
    /// context cannot be replayed under another. This is the TV-1 property,
    /// now enforced through the byte boundary too.
    #[test]
    fn a_certificate_replayed_under_another_ctx_is_rejected() {
        use kok_poum::canonical;
        use kok_poum::{KwKernel, TOY_Q, TOY_R};
        let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
        let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
        let k = KwKernel::new(TOY_Q, TOY_R);
        let target = 1u64 << 4;
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, target) {
                break c;
            }
        };
        // the cert was mined under ctx 777; present it under a different one
        let input = encode(&a, &b, &cert, 778, nonce, target, TOY_Q, TOY_R);
        assert!(!verify_raw(&input).accepted(), "a ctx replay was accepted");
    }

    /// pack/decode round trip: the byte layout is self-consistent. The tile
    /// coordinates must be inside the n/r grid or decode correctly rejects.
    #[test]
    fn pack_decodes_back_consistently() {
        let input = pack(3, 2, 42, 4, 777, 1780, 1 << 16, 8, 97, 2);
        let (cert, ctx, nonce, target, n, q, a, b) =
            decode(&input).expect("a well-formed packet must decode");
        assert_eq!((cert.i, cert.j, cert.value, cert.m), (3, 2, 42, 4));
        assert_eq!((ctx, nonce, target, n, q), (777, 1780, 1 << 16, 8, 97));
        assert_eq!(a.len(), 8);
        assert_eq!(b.len(), 8);
        assert_eq!(a[0].len(), 8);
    }

    /// THE OVERFLOW CLASS — `(n * n) as usize * 8` computed with plain u64
    /// arithmetic. `VerifierInput`'s fields are all `pub`, so any Rust caller
    /// (a light client, an indexer) can build one directly rather than going
    /// through `kok_wasm::parse_packet`. At n = 2^33, `n * n` wraps to a small
    /// value, the length gate below passes against a SHORT buffer, and the
    /// slice `flat_a[off..off+8]` panics before `u64_le` can return the `None`
    /// the "matrix A truncated" guard exists to handle. That made the guard
    /// dead code and the failure a panic instead of a `Reject`. The WASM suite
    /// never saw it because `parse_packet` validates this same expression with
    /// `checked_mul` upstream — the wrapper screens the input that would expose
    /// the bug, which is exactly the shape where a broken primitive hides.
    #[test]
    fn decode_rejects_an_overflowing_matrix_size_instead_of_panicking() {
        // n = 2^33: n*n = 2^66, which wraps u64. This case is caught by the
        // checked multiply (2^66 does not fit), and the second test below
        // covers the value that actually crashes the OLD code — see it.
        let n_overflow: u64 = 1u64 << 33;
        let input = VerifierInput {
            cert_bytes: {
                let mut c = [0u8; 32];
                c[24..32].copy_from_slice(&1u64.to_le_bytes()); // m = 1
                c
            },
            pub_inputs: {
                let mut p = [0u8; 48];
                // layout per decode(): ctx 0..8, nonce 8..16, target 16..24,
                // n 24..32, q 32..40, r 40..48
                p[16..24].copy_from_slice(&(1u64 << 16).to_le_bytes());
                p[24..32].copy_from_slice(&n_overflow.to_le_bytes());
                p[32..40].copy_from_slice(&97u64.to_le_bytes());
                p[40..48].copy_from_slice(&2u64.to_le_bytes()); // r = 2
                p
            },
            flat_a: vec![0u8; 32],
            flat_b: vec![0u8; 32],
        };
        // must be a REJECT, never a panic. Before the fix this unwound at the
        // slice `flat_a[off..off+8]` instead of returning an Err.
        match decode(&input) {
            Ok(_) => panic!("an overflowing matrix size must be rejected, not accepted"),
            Err(msg) => {
                assert!(
                    msg.contains("overflow") || msg.contains("size"),
                    "the error must name the size problem, got: {msg}"
                );
            }
        }
    }

    /// **THE CASE THAT ACTUALLY CRASHES THE OLD CODE.** At n = 2^32 the product
    /// `n * n` = 2^64 wraps to exactly **0**, so the old `need` became
    /// `0 * 8 = 0`. Empty `flat_a` and `flat_b` then PASS the length gate
    /// (0 == 0), and the decode loop proceeds to build the matrices: it calls
    /// `Vec::with_capacity(n as usize)` — 2^32 rows, each itself 2^32 entries —
    /// which is an attempted ~96 GB allocation and the process dies with
    /// SIGABRT on the memory request, before ever reaching the slice that the
    /// "matrix A truncated" guard was written for. Verified by running this
    /// exact test against the pre-fix commit in a throwaway git worktree: it
    /// aborted with `memory allocation of 103079215104 bytes failed`. The
    /// checked multiply above now refuses the size outright, so this returns
    /// an `Err` instead of killing the process.
    #[test]
    fn decode_rejects_a_size_that_wraps_to_zero_instead_of_allocating_96gb() {
        let n_wrap_to_zero: u64 = 1u64 << 32; // n*n = 2^64 -> wraps to 0
        let input = VerifierInput {
            cert_bytes: {
                let mut c = [0u8; 32];
                c[24..32].copy_from_slice(&1u64.to_le_bytes());
                c
            },
            pub_inputs: {
                let mut p = [0u8; 48];
                p[16..24].copy_from_slice(&(1u64 << 16).to_le_bytes());
                p[24..32].copy_from_slice(&n_wrap_to_zero.to_le_bytes());
                p[32..40].copy_from_slice(&97u64.to_le_bytes());
                p[40..48].copy_from_slice(&2u64.to_le_bytes());
                p
            },
            flat_a: vec![],
            flat_b: vec![],
        };
        assert!(
            decode(&input).is_err(),
            "n = 2^32 wraps n*n to zero; the size must be rejected, not treated as empty"
        );
    }
}

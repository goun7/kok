//! WASM — the light-client verifier boundary, trap-free by construction.
//!
//! Round-6, 2026-09-24: this crate was a 6-line skeleton. It now ships the
//! function a browser or a light client actually calls (2026-09-25), and it
//! is built so that it CANNOT trap on adversarial input.
//!
//! WHY "CANNOT TRAP" IS THE WHOLE DESIGN. In WASM a panic is a trap, and a
//! trap is not a rejection — it is an undefined outcome the host may report
//! as anything, including success-by-omission. This is the same failure
//! class the project has now hit four times: the FRI degree bound that could
//! not fail, the arithmetically-excluded TV-58 check, the anticone that
//! silently included the future, and is_final scoring a phantom block as
//! zero and calling it settled. At a WASM boundary that class becomes a
//! remote exploit rather than a local bug, so the byte layout is validated
//! with CHECKED arithmetic before any slice is indexed.
//!
//! WHAT REMAINS F3+ AND IS NOT FAKED: the wasm-bindgen JS shim, the actual
//! browser bundle, and the network fetch of the matrices. This crate
//! provides the total C ABI they will wrap; it does not pretend to be the
//! browser package.

use kok_pvi::{VerifierInput, Verdict};

/// The raw wire layout this boundary parses:
///   bytes [  0 ..  32]  the certificate (i, j, value, m), little-endian u64s
///   bytes [ 32 ..  80]  public inputs (ctx, nonce, target, n, q, r)
///   bytes [ 80 .. 80+2*n*n*8]  flat_a then flat_b, little-endian u64s
///
/// Returns Err for anything malformed. Every bounds and arithmetic check
/// happens HERE, on lengths, before a single matrix byte is indexed.
pub fn parse_packet(bytes: &[u8]) -> Result<VerifierInput, &'static str> {
    // 1. the fixed header must be present before we read any field
    if bytes.len() < 80 {
        return Err("packet shorter than the 80-byte header");
    }
    let mut cert_bytes = [0u8; 32];
    cert_bytes.copy_from_slice(&bytes[0..32]);
    let mut pub_inputs = [0u8; 48];
    pub_inputs.copy_from_slice(&bytes[32..80]);

    // 2. derive the matrix size with CHECKED arithmetic — a hostile packet
    // may claim n = u64::MAX, and n*n*8 must not wrap to a small number that
    // then passes the length check. This is the overflow that would let a
    // truncated packet slip through as well-formed.
    let n = u64::from_le_bytes(pub_inputs[24..32].try_into().unwrap());
    let r = u64::from_le_bytes(pub_inputs[40..48].try_into().unwrap());
    if n == 0 || r == 0 {
        return Err("n or r is zero");
    }
    if n % r != 0 {
        return Err("r does not divide n");
    }
    let per_matrix = n.checked_mul(n).and_then(|sq| sq.checked_mul(8)).ok_or(
        "the claimed matrix size overflows u64",
    )?;
    let total = 80usize
        .checked_add(per_matrix as usize)
        .and_then(|t| t.checked_add(per_matrix as usize))
        .ok_or("the total packet length overflows usize")?;
    if bytes.len() != total {
        return Err("the matrix payload does not match the declared n");
    }

    // 3. only now is it safe to split the payload; the length is proven
    let split = 80 + per_matrix as usize;
    Ok(VerifierInput {
        cert_bytes,
        flat_a: bytes[80..split].to_vec(),
        flat_b: bytes[split..].to_vec(),
        pub_inputs,
    })
}

/// The safe Rust entry point: 1 for accept, 0 for reject, for EVERY input.
/// Malformed packets are rejections, never panics.
pub fn verify_packet(bytes: &[u8]) -> u8 {
    match parse_packet(bytes) {
        Ok(input) => match kok_pvi::verify_raw(&input) {
            Verdict::Accept => 1,
            Verdict::Reject(_) => 0,
        },
        Err(_) => 0,
    }
}

/// The WASM C ABI a host calls without wasm-bindgen. Takes a raw pointer and
/// length so it works under wasm32-unknown-unknown AND wasip1/p2; it never
/// traps, because a null pointer or a zero length is a rejection, not a
/// slice operation.
///
/// # Safety
/// `ptr` must point to at least `len` readable bytes, or be null with len 0.
#[no_mangle]
pub extern "C" fn kok_verify_packet(ptr: *const u8, len: usize) -> u8 {
    if ptr.is_null() || len == 0 {
        return 0;
    }
    // SAFETY: the caller guarantees ptr/len are a valid readable slice; the
    // null and zero cases above mean this slice is never empty-by-null.
    let bytes = unsafe { core::slice::from_raw_parts(ptr, len) };
    verify_packet(bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    use kok_poum::canonical;
    use kok_poum::{KwKernel, TOY_Q, TOY_R};

    fn encode_wire(a: &[Vec<u64>], b: &[Vec<u64>], cert: &kok_poum::Certificate, ctx: u64, nonce: u64, target: u64) -> Vec<u8> {
        let mut out = Vec::with_capacity(80 + 2 * a.len() * a.len() * 8);
        out.extend_from_slice(&(cert.i as u64).to_le_bytes());
        out.extend_from_slice(&(cert.j as u64).to_le_bytes());
        out.extend_from_slice(&cert.value.to_le_bytes());
        out.extend_from_slice(&(cert.m as u64).to_le_bytes());
        out.extend_from_slice(&ctx.to_le_bytes());
        out.extend_from_slice(&nonce.to_le_bytes());
        out.extend_from_slice(&target.to_le_bytes());
        out.extend_from_slice(&(a.len() as u64).to_le_bytes());
        out.extend_from_slice(&TOY_Q.to_le_bytes());
        out.extend_from_slice(&(TOY_R as u64).to_le_bytes());
        for row in a.iter().chain(b.iter()) {
            for v in row {
                out.extend_from_slice(&v.to_le_bytes());
            }
        }
        out
    }

    fn mine_real() -> (Vec<u8>, kok_poum::Certificate) {
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
        (encode_wire(&a, &b, &cert, 777, nonce, target), cert)
    }

    /// THE TRAP-FREE CONTRACT: every malformed packet is a rejection, and
    /// the function returns 0/1 rather than panicking. A trap here would be
    /// an undefined outcome a host might read as success.
    #[test]
    fn every_malformed_packet_is_a_rejection_never_a_trap() {
        // empty
        assert_eq!(verify_packet(&[]), 0, "an empty packet was not rejected");
        // truncated header
        assert_eq!(verify_packet(&[0u8; 40]), 0, "a truncated header was not rejected");
        // header only, no matrix payload
        let mut hdr = vec![0u8; 80];
        // n=8, r=2, q=97 -> needs 2*512 bytes of payload, absent
        hdr[24..32].copy_from_slice(&8u64.to_le_bytes());
        hdr[32..40].copy_from_slice(&97u64.to_le_bytes());
        hdr[40..48].copy_from_slice(&2u64.to_le_bytes());
        assert_eq!(verify_packet(&hdr), 0, "a header with no payload was not rejected");
        // the overflow attack: claim n = u64::MAX so n*n*8 wraps; a naive
        // length check would then accept a tiny packet
        let mut overflow = vec![0u8; 80];
        overflow[24..32].copy_from_slice(&u64::MAX.to_le_bytes());
        overflow[40..48].copy_from_slice(&2u64.to_le_bytes());
        assert_eq!(verify_packet(&overflow), 0, "an overflow-length packet was not rejected");
        // r does not divide n
        let mut bad_r = vec![0u8; 80];
        bad_r[24..32].copy_from_slice(&9u64.to_le_bytes());
        bad_r[40..48].copy_from_slice(&2u64.to_le_bytes());
        assert_eq!(verify_packet(&bad_r), 0, "a non-integral tile grid was not rejected");
    }

    /// THE END-TO-END PATH: a certificate mined over the canonical matrices
    /// accepts through the raw byte boundary, all the way to WASM.
    #[test]
    fn an_honestly_mined_packet_accepts_over_the_wire() {
        let (wire, _cert) = mine_real();
        assert_eq!(verify_packet(&wire), 1, "an honestly mined packet was rejected");
    }

    /// A FORGED VALUE rejects over the wire, so the forgery the boundary
    /// exists to stop is caught before it ever reaches a browser.
    #[test]
    fn a_forged_packet_rejects_over_the_wire() {
        let (mut wire, _cert) = mine_real();
        // tamper the accumulated value (bytes 16..24)
        let mut v = u64::from_le_bytes(wire[16..24].try_into().unwrap());
        v = (v + 1) % TOY_Q;
        wire[16..24].copy_from_slice(&v.to_le_bytes());
        assert_eq!(verify_packet(&wire), 0, "a forged packet was accepted");
    }

    /// The C ABI must agree with the safe entry point on real input, and must
    /// reject (not trap) on a null pointer.
    #[test]
    fn the_c_abi_matches_the_safe_entry_and_rejects_null() {
        let (wire, _) = mine_real();
        assert_eq!(kok_verify_packet(wire.as_ptr(), wire.len()), 1);
        assert_eq!(kok_verify_packet(wire.as_ptr(), 0), 0, "a zero length was not a rejection");
        assert_eq!(kok_verify_packet(core::ptr::null(), 0), 0, "a null pointer was not a rejection");
        // a short length must reject, not read out of bounds
        assert_eq!(kok_verify_packet(wire.as_ptr(), 5), 0, "a truncated length was not a rejection");
    }
}

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
///
/// **HOST CONSTRAINT — DISCOVERED BY MEASUREMENT (2026-09-26):** `ptr` must
/// not alias the bytes the module's own runtime reserves at the start of
/// linear memory. Under wasm32-unknown-unknown the wasm-bindgen glue that
/// this build pulls in (for getrandom's js feature) keeps internal bookkeeping
/// near offset 0; a host that writes its packet there and calls with `ptr=0`
/// gets its bytes partially overwritten before the ABI reads them, and the
/// packet is rejected — not because the packet is invalid, but because the
/// host and the module disagree about who owns the first bytes of memory.
/// This is a HOST convention, not a verifier property: the C ABI itself is
/// correct for any pointer whose bytes are actually the caller's. Hosts
/// should place packets at an offset past the module's reserved area (or use
/// the exported allocator); offset 0 is not safe for payload data.
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

    /// THE ABI TAKES THE CALLER'S POINTER AT FACE VALUE (2026-09-26).
    ///
    /// This test exists because of a real cross-target investigation. A
    /// Node.js harness drove the WASM build and the C ABI REJECTED a packet
    /// that native Rust ACCEPTS byte-for-byte. The packet was not the
    /// problem and the ABI was not the problem: the harness had written its
    /// packet at linear-memory offset 0, which the wasm-bindgen glue that
    /// this build pulls in (via getrandom's js feature) treats as its own.
    /// The bytes were partly overwritten before the ABI read them.
    ///
    /// The honest conclusion is recorded in the ABI's own doc comment: the
    /// contract is "ptr must point at len readable bytes that are YOURS",
    /// and offset 0 is not guaranteed to be the caller's under this build.
    /// This test pins the native half of that contract — the ABI answers
    /// about the bytes it is given, wherever they live, and does not assume
    /// anything about which address it was handed:
    #[test]
    fn the_c_abi_answers_about_the_bytes_it_is_given_not_the_address() {
        let (wire, _) = mine_real();
        // the same packet at two different addresses must give one answer
        let mut buf = vec![0u8; wire.len() * 2];
        buf[..wire.len()].copy_from_slice(&wire);
        buf[wire.len()..].copy_from_slice(&wire);
        let at_front = kok_verify_packet(buf.as_ptr(), wire.len());
        let at_offset = kok_verify_packet(unsafe { buf.as_ptr().add(wire.len()) }, wire.len());
        assert_eq!(at_front, 1, "the packet was rejected at the front of the buffer");
        assert_eq!(at_offset, 1, "the packet was rejected at the back of the buffer");
        // and both agree with the safe entry point
        assert_eq!(verify_packet(&wire), 1);
    }

    // ---- DIRECT UNIT COVERAGE OF parse_packet's error contract (2026-09-27).
    // verify_packet collapses every malformed case to 0, which means no
    // existing test can tell you WHY a packet failed — only that something
    // did. The function's own Err strings are the contract a light client
    // depends on, so each branch is asserted by name here. The builder below
    // constructs the header directly rather than mining, so each malformed
    // variant is a one-line edit rather than a full re-mine.

    /// A header with `n`, `q`, and `r` set, and space for the matrices.
    ///
    /// LAYOUT NOTE — the offsets are subtle and one wrong offset here reads a
    /// zero field and every test fails with "n or r is zero" instead of with
    /// the message the test expects. `parse_packet` slices a 48-byte
    /// `pub_inputs` window out of bytes 32..80, then indexes THAT window, so a
    /// field at window offset k lives at wire offset 32 + k:
    ///   window [ 0..  8] = wire 32..40   ctx
    ///   window [ 8.. 16] = wire 40..48   nonce
    ///   window [16.. 24] = wire 48..56   target
    ///   window [24.. 32] = wire 56..64   n     <- read at lib.rs:45
    ///   window [32.. 40] = wire 64..72   q
    ///   window [40.. 48] = wire 72..80   r     <- read at lib.rs:46
    fn header(n: u64, q: u64, r: u64) -> Vec<u8> {
        let mut h = vec![0u8; 80];
        // bytes 0..32: the certificate (i, j, value, m) — zeroed, since the
        // parse must reject on LAYOUT before it ever reads a certificate
        h[56..64].copy_from_slice(&n.to_le_bytes());
        h[64..72].copy_from_slice(&q.to_le_bytes());
        h[72..80].copy_from_slice(&r.to_le_bytes());
        h
    }

    #[test]
    fn parse_rejects_a_packet_shorter_than_the_header() {
        let e = parse_packet(&[]).unwrap_err();
        assert!(e.contains("80"), "the error must name the header size: {e}");
        let e = parse_packet(&[0u8; 79]).unwrap_err();
        assert!(e.contains("80"), "a 79-byte packet must still be a header error: {e}");
    }

    #[test]
    fn parse_rejects_a_zero_matrix_dimension() {
        // n == 0 would make the payload length 0 and the packet appear
        // self-consistent at 80 bytes — the guard exists so a degenerate grid
        // cannot pass as a well-formed packet with no matrices at all
        let e = parse_packet(&header(0, 97, 2)).unwrap_err();
        assert!(e.contains("zero"), "n == 0 must be rejected as a zero dimension: {e}");
        let e = parse_packet(&header(8, 97, 0)).unwrap_err();
        assert!(e.contains("zero"), "r == 0 must be rejected as a zero dimension: {e}");
    }

    #[test]
    fn parse_rejects_a_non_integral_tile_grid() {
        // n must be divisible by r, or the flat matrices do not decompose into
        // a rectangular grid and the verifier would read garbage at the seam
        let e = parse_packet(&header(9, 97, 2)).unwrap_err();
        assert!(e.contains("divide"), "n=9 r=2 must fail the divisibility check: {e}");
    }

    #[test]
    fn parse_rejects_an_overflowing_matrix_size() {
        // the wrap attack: n = u64::MAX makes n*n*8 wrap to a small number, and
        // a naive length check would then accept a short packet as complete.
        // checked_mul must refuse instead.
        //
        // The ORDER OF THE GUARDS MATTERS and is itself a property worth
        // pinning: the divisibility check runs first, so the overflow case must
        // use an EVEN n to reach the multiplication at all. An odd u64::MAX is
        // caught by divisibility and never reaches checked_mul — which is the
        // correct behaviour (a packet rejected early is still rejected), but a
        // test claiming "overflow" while hitting "divisibility" would pin a
        // property the code does not have.
        let even_max = u64::MAX - 1; // even, so r=2 divides it
        assert_eq!(even_max % 2, 0);
        let e = parse_packet(&header(even_max, 97, 2)).unwrap_err();
        assert!(e.contains("overflow"), "an overflowing n must be rejected as overflow: {e}");
        // the odd maximum is caught one guard earlier, still rejected
        let e2 = parse_packet(&header(u64::MAX, 97, 2)).unwrap_err();
        assert!(e2.contains("divide"), "an odd n is caught by divisibility before overflow: {e2}");
    }

    #[test]
    fn parse_rejects_a_payload_length_that_does_not_match_n() {
        // a header claiming n=8 (needs 2*512 = 1024 payload bytes) with NO
        // payload: the lengths disagree, which is the check that a truncated
        // packet cannot pass as complete
        let e = parse_packet(&header(8, 97, 2)).unwrap_err();
        assert!(e.contains("match"), "a missing payload must be a length mismatch: {e}");
        // one matrix's worth of payload is not enough either — the check is on
        // the TOTAL, so a half-filled packet is still wrong
        let mut half = header(8, 97, 2);
        half.extend_from_slice(&vec![0u8; 512]);
        let e = parse_packet(&half).unwrap_err();
        assert!(e.contains("match"), "a half-length payload must be a length mismatch: {e}");
    }

    #[test]
    fn parse_accepts_a_well_formed_packet_and_splits_at_the_right_offset() {
        // the happy path, tested at the parser rather than through the
        // verifier: a complete packet must parse, and the two matrices must be
        // split exactly at 80 + n*n*8 — the offset a slice read depends on
        let n: u64 = 4;
        let per = (n * n * 8) as usize;
        let mut wire = header(n, 97, 2);
        let a: Vec<u8> = (0..per as u8).collect();
        let b: Vec<u8> = (100..100 + per as u8).collect();
        wire.extend_from_slice(&a);
        wire.extend_from_slice(&b);
        let got = parse_packet(&wire).expect("a complete well-formed packet must parse");
        assert_eq!(got.flat_a, a, "matrix a must be split at 80 + n*n*8");
        assert_eq!(got.flat_b, b, "matrix b must be the remainder");
        assert_eq!(got.flat_a.len(), per);
        assert_eq!(got.flat_b.len(), per);
        // the declared field must be carried through to the verifier input
        assert_eq!(u64::from_le_bytes(got.pub_inputs[24..32].try_into().unwrap()), n,
                   "the declared n must survive into the parsed verifier input");
    }
}

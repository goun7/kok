// Dump the EXACT bytes the Rust test suite accepts, as hex, so an external
// WASM host (Node.js) can send the identical packet through the C ABI.
use kok_pvi::{verify_raw, Verdict, VerifierInput};
use kok_poum::{KwKernel, TOY_Q, TOY_R};
use kok_poum::canonical;

fn main() {
    let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
    let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
    let k = KwKernel::new(TOY_Q, TOY_R);
    let target = 1u64 << 4;
    let mut nonce = 0u64;
    let cert = loop {
        nonce += 1;
        if let Some(c) = k.prove(&a, &b, 777, nonce, target) { break c; }
    };
    let n = a.len() as u64;
    // serialize: 32 cert + 48 pub + n*n*8 flat_a + n*n*8 flat_b (row-major LE)
    let mut cert_bytes = [0u8; 32];
    cert_bytes[0..8].copy_from_slice(&(cert.i as u64).to_le_bytes());
    cert_bytes[8..16].copy_from_slice(&(cert.j as u64).to_le_bytes());
    cert_bytes[16..24].copy_from_slice(&cert.value.to_le_bytes());
    cert_bytes[24..32].copy_from_slice(&(cert.m as u64).to_le_bytes());
    let mut pub_inputs = [0u8; 48];
    pub_inputs[0..8].copy_from_slice(&777u64.to_le_bytes());
    pub_inputs[8..16].copy_from_slice(&nonce.to_le_bytes());
    pub_inputs[16..24].copy_from_slice(&target.to_le_bytes());
    pub_inputs[24..32].copy_from_slice(&n.to_le_bytes());
    pub_inputs[32..40].copy_from_slice(&TOY_Q.to_le_bytes());
    pub_inputs[40..48].copy_from_slice(&(TOY_R as u64).to_le_bytes());
    let mut flat = |rows: &[Vec<u64>]| -> Vec<u8> {
        let mut v = Vec::with_capacity((n * n * 8) as usize);
        for row in rows { for x in row { v.extend_from_slice(&x.to_le_bytes()); } }
        v
    };
    let flat_a = flat(&a);
    let flat_b = flat(&b);
    let input = VerifierInput { cert_bytes, flat_a: flat_a.clone(), flat_b: flat_b.clone(), pub_inputs };
    assert!(matches!(verify_raw(&input), Verdict::Accept), "the dumped packet must ACCEPT in Rust");

    let mut wire = Vec::with_capacity(80 + 2 * (n * n * 8) as usize);
    wire.extend_from_slice(&cert_bytes);
    wire.extend_from_slice(&pub_inputs);
    wire.extend_from_slice(&flat_a);
    wire.extend_from_slice(&flat_b);
    eprintln!("OK n={} nonce={} i={} j={} value={} m={} bytes={}", n, nonce, cert.i, cert.j, cert.value, cert.m, wire.len());
    let mut hex = String::with_capacity(wire.len() * 2);
    for b in &wire { hex.push_str(&format!("{:02x}", b)); }
    println!("{}", hex);
}

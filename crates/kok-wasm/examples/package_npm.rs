// Package the wasm32-unknown-unknown module into crates/kok-wasm/npm/.
//
// WHAT THIS DOES AND WHY IT IS AN EXAMPLE RATHER THAN A SHELL SCRIPT: the
// fixtures the npm tests consume are byte-for-byte the same packets the
// crate's own Rust tests mine, and generating them from Rust — from the same
// `mine_real` helper the lib tests use — is what guarantees that. A shell
// script would have to re-derive the encoding; this calls the encoding.
//
// Usage:
//   cargo run --release -p kok-wasm --example package_npm
//
// Output: crates/kok-wasm/npm/{kok_wasm_bg.wasm, tests/fixtures/*.bin}
// The .wasm itself is copied from the release target dir, so build it first:
//   cargo build --release -p kok-wasm --target wasm32-unknown-unknown

use std::fs;
use std::io::Write;
use std::path::PathBuf;

use kok_poum::canonical;
use kok_poum::{KwKernel, TOY_Q, TOY_R};
use kok_wasm::verify_packet;

fn main() {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let npm_dir = manifest_dir.join("npm");
    let fix_dir = npm_dir.join("tests").join("fixtures");
    fs::create_dir_all(&fix_dir).expect("could not create npm/tests/fixtures");

    // 1. Copy the compiled module into the package if the release build
    // exists. A missing build is a packaging problem, not a panic-worthy
    // one — the fixtures alone are useful, and the message says what to run.
    let wasm_src = manifest_dir
        .join("../../target/wasm32-unknown-unknown/release/kok_wasm.wasm");
    if wasm_src.exists() {
        fs::copy(&wasm_src, npm_dir.join("kok_wasm_bg.wasm"))
            .expect("could not copy the wasm module into npm/");
        eprintln!("copied {} -> npm/kok_wasm_bg.wasm", wasm_src.display());
    } else {
        eprintln!(
            "warning: {} not found — run \
             `cargo build --release -p kok-wasm --target wasm32-unknown-unknown` first",
            wasm_src.display()
        );
    }

    // 2. Mine the honest packet with the same helper the lib tests use, so
    // the npm fixtures and the Rust fixtures are one set of bytes.
    let (wire, _cert) = mine_real();
    assert_eq!(verify_packet(&wire), 1, "the honest fixture did not verify");

    // 3. The forged packet is the honest one with the accumulated value
    // tampered, matching the crate's own forgery test.
    let mut forged = wire.clone();
    let mut v = u64::from_le_bytes(forged[16..24].try_into().unwrap());
    v = (v + 1) % TOY_Q;
    forged[16..24].copy_from_slice(&v.to_le_bytes());
    assert_eq!(verify_packet(&forged), 0, "the forged fixture unexpectedly verified");

    // 4. A short packet — shorter than the 80-byte header — for the
    // malformed-input probe.
    let short = vec![0u8; 40];
    assert_eq!(verify_packet(&short), 0, "the short fixture was not rejected");

    write_bin(&fix_dir.join("honest.bin"), &wire);
    write_bin(&fix_dir.join("forged.bin"), &forged);
    write_bin(&fix_dir.join("short.bin"), &short);

    eprintln!(
        "wrote fixtures into {} (honest {} bytes, forged {} bytes, short {} bytes)",
        fix_dir.display(),
        wire.len(),
        forged.len(),
        short.len()
    );
    eprintln!("the npm package is ready: {}", npm_dir.display());
}

fn write_bin(path: &std::path::Path, bytes: &[u8]) {
    let mut f = fs::File::create(path).expect("could not create fixture");
    f.write_all(bytes).expect("could not write fixture");
}

// The same wire encoder and miner the crate's lib tests use, duplicated here
// because they are private. Keeping the two in sync is the point of this
// example: if the encoding drifts, the fixtures stop verifying and the npm
// tests fail loudly rather than silently.
fn encode_wire(a: &[Vec<u64>], b: &[Vec<u64>], cert: &kok_poum::Certificate, ctx: u64, nonce: u64, target: u64) -> Vec<u8> {
    // The 88-byte header: cert (32) + ctx/nonce/target (24) + n + q + r (24).
    // Every field is a little-endian u64 and the order matters — this is a
    // byte-exact copy of the encoder the crate's lib tests use, because the
    // fixtures must be the same bytes the Rust tests verify.
    let mut out = Vec::with_capacity(88 + 2 * a.len() * a.len() * 8);
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
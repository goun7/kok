// Reproduce the EXACT bytes the Node.js harness sent and confirm the safe
// entry point accepts them. If Rust accepts these bytes and WASM rejects
// them, the discrepancy is real; if Rust also rejects them, the Node harness
// serialized something different from what was dumped.
fn main() {
    let hex = std::env::args().nth(1).expect("pass hex on argv[1]");
    let wire = hex_to_bytes(&hex);
    eprintln!("replaying {} bytes", wire.len());
    eprintln!("safe entry result: {}", kok_wasm::verify_packet(&wire));
}

fn hex_to_bytes(s: &str) -> Vec<u8> {
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).expect("bad hex"))
        .collect()
}

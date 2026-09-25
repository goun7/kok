// HONEST PYTHON-vs-RUST measurement on the SAME canonical input.
use kok_poum::{canonical, KwKernel, TOY_Q, TOY_R};
use std::time::Instant;

fn canon() -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
    let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
    let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
    (a, b)
}

fn main() {
    let k = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = canon();
    println!("=== G LAYER: same input, both languages (canonical matrices) ===");
    for &target in &[1u64 << 4, 1u64 << 8, 1u64 << 12, 1u64 << 16, 1u64 << 20] {
        // warm the noise cache once so the FIRST prove does not pay 2n^2 hashes
        k.noise(777, a.len());
        let t0 = Instant::now();
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, target) {
                break c;
            }
        };
        let mine_ms = t0.elapsed().as_micros() as f64 / 1000.0;
        let t1 = Instant::now();
        let mut ok = false;
        let reps = 100_000;
        for _ in 0..reps {
            ok = k.verify(&cert, &a, &b, 777, nonce, target);
        }
        let verify_us = t1.elapsed().as_nanos() as f64 / reps as f64 / 1000.0;
        let exp = 64 - target.leading_zeros() as i64 - 1;
        // NOTE (2026-09-25, units fix): this value is MICROSECONDS, not
        // milliseconds. The formula divides nanoseconds by 1000, so a
        // printed "0.7576" read as ms overstates verify by 1000x — and a
        // 757 ns verify reported as 0.73 ms looks 170x slower than Python
        // when it is actually ~8x FASTER. Label now says us.
        println!("  target 2^{:2}: mine {:10.3} ms over {:7} attempts ({:.4} ms/attempt) | verify {:7.4} us | tile=({},{}) ok={}",
            exp, mine_ms, nonce, mine_ms / nonce as f64, verify_us, cert.i, cert.j, ok);
    }
}

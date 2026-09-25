use kok_poum::{canonical, KwKernel, TOY_Q, TOY_R};
use std::time::Instant;
fn main() {
    let k = KwKernel::new(TOY_Q, TOY_R);
    let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
    let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
    k.noise(777, a.len());
    let cert = k.prove(&a, &b, 777, 1, 1 << 4).unwrap();
    // WARM UP first, then take the steady-state measurement
    for _ in 0..50_000 { let _ = k.verify(&cert, &a, &b, 777, 1, 1 << 4); }
    let reps = 1_000_000;
    let t0 = Instant::now();
    let mut ok = false;
    for _ in 0..reps { ok = k.verify(&cert, &a, &b, 777, 1, 1 << 4); }
    let ns = t0.elapsed().as_nanos() as f64 / reps as f64;
    println!("WARM steady-state: {:.1} ns/verify = {:.4} ms | ok={}", ns, ns / 1e6, ok);
}

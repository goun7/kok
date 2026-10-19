use kok_poum::{canonical, KwKernel, TOY_Q, TOY_R};
use std::time::Instant;
fn main() {
    let k = KwKernel::new(TOY_Q, TOY_R);
    let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
    let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
    k.noise(777, a.len());
    let cert = k.prove(&a, &b, 777, 1, 1 << 4).unwrap();
    // escalating repetition counts to see whether the first measurement is an outlier
    for &reps in &[1_000, 10_000, 100_000, 1_000_000] {
        let t0 = Instant::now();
        let mut ok = false;
        for _ in 0..reps {
            ok = k.verify(&cert, &a, &b, 777, 1, 1 << 4);
        }
        let ns = t0.elapsed().as_nanos() as f64 / reps as f64;
        println!(
            "reps {:>9}: {:.1} ns/verify (total {:.1} ms) ok={}",
            reps,
            ns,
            t0.elapsed().as_secs_f64() * 1000.0,
            ok
        );
    }
}

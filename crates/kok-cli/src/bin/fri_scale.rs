// Confirm the Theta(q*deg) scaling claim with three field sizes rather than
// one toy point. The claim is about the SHAPE of the cost curve; one point
// cannot establish a shape.
use kok_fri::recursive_prove;
use std::time::Instant;

fn main() {
    println!("=== FRI verify scaling: Theta(q * deg) ===");
    for q in [97u64, 1009, 2003] {
        // seeded the way the Python side seeds: random.seed(q)
        let mut s = q.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1);
        let mut poly = Vec::with_capacity(8);
        for _ in 0..8 {
            s = s
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            poly.push(s % q);
        }
        let (tr, alphas) = recursive_prove(&poly, 3, q).expect("fold must succeed");
        let reps = 2000;
        let t0 = Instant::now();
        for _ in 0..reps {
            kok_fri::verify_transcript(&tr, &alphas, q);
        }
        let us = t0.elapsed().as_nanos() as f64 / reps as f64 / 1000.0;
        println!("q={:>5}  Rust verify {:>10.3} us", q, us);
    }
}

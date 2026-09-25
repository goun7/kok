//! Criterion benchmark for the G layer: the leader-selection mine loop and
//! verification, measured on the SAME canonical input the Python prototype
//! mines, both sides warm.
//!
//! The measurement the orchestrator asked for. Python's numbers are measured
//! on the same input with the noise cache warm; without warm-up the first
//! verify pays 2*n*n SHA256 calls and reports a number 3x too high.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use kok_poum::{canonical, KwKernel, TOY_Q, TOY_R};

fn canon() -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
    let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
    let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
    (a, b)
}

fn bench_g_layer_mine(c: &mut Criterion) {
    let k = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = canon();
    k.noise(777, a.len()); // warm the noise cache once
    c.bench_function("g_layer mine (canon input, target 2^16)", |bencher| {
        bencher.iter(|| {
            black_box(k.mine(black_box(&a), black_box(&b), 777, 1 << 16));
        })
    });
}

fn bench_g_layer_verify(c: &mut Criterion) {
    let k = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = canon();
    k.noise(777, a.len());
    let (nonce, cert) = k.mine(&a, &b, 777, 1 << 16);
    let cert = cert.unwrap();
    c.bench_function("g_layer verify (canon input)", |bencher| {
        bencher.iter(|| {
            black_box(k.verify(
                black_box(&cert),
                black_box(&a),
                black_box(&b),
                777,
                nonce,
                1 << 16,
            ));
        })
    });
}

criterion_group!(g_benches, bench_g_layer_mine, bench_g_layer_verify);
criterion_main!(g_benches);

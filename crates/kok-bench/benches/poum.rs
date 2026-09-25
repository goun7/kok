//! Criterion benchmark for the G layer.
//!
//! The Python rounds measured prove 3.47 ms / verify 0.25 ms by timing a
//! script; the Rust port measured 0.072 ms / 0.211 ms the same way. This
//! makes that measurement the repo's mechanism rather than a one-off: every
//! "ms" claim in the docs points at a benchmark that produces it.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use kok_poum::{KwKernel, TOY_N, TOY_Q, TOY_R};

fn toy_matrices(seed: u64) -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
    let mut a = vec![vec![0u64; TOY_N]; TOY_N];
    let mut b = vec![vec![0u64; TOY_N]; TOY_N];
    let mut s = seed;
    for i in 0..TOY_N {
        for j in 0..TOY_N {
            s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            a[i][j] = s % TOY_Q;
            s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            b[i][j] = s % TOY_Q;
        }
    }
    (a, b)
}

fn bench_prove(c: &mut Criterion) {
    let k = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = toy_matrices(20260919);
    c.bench_function("g_layer prove (q=97 n=8 target 2^1)", |bencher| {
        bencher.iter(|| {
            let mut nonce = 0u64;
            loop {
                nonce += 1;
                if black_box(k.prove(black_box(&a), black_box(&b), 777, nonce, 1 << 1)).is_some() {
                    return;
                }
            }
        })
    });
}

fn bench_verify(c: &mut Criterion) {
    let k = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = toy_matrices(20260919);
    let mut nonce = 0u64;
    let cert = loop {
        nonce += 1;
        if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
            break c;
        }
    };
    c.bench_function("g_layer verify (q=97 n=8)", |bencher| {
        bencher.iter(|| {
            black_box(k.verify(black_box(&cert), black_box(&a), black_box(&b), 777, nonce, 1 << 1));
        })
    });
}

criterion_group!(benches, bench_prove, bench_verify);
criterion_main!(benches);

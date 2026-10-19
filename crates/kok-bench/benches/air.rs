//! Criterion benchmark for the zk-AIR prove/verify — the layer the
//! orchestrator's quoted "0.37 ms verify" actually measures.
//!
//! The measured Python decomposition (random.seed 20260925, q=97 n=8 r=2):
//!   AIR  prove  0.959 ms | verify 0.051 ms
//!   FRI  prove  0.043 ms | verify 0.315 ms
//!   STACK       1.002 ms | verify 0.365 ms   <- the "0.37 ms" figure
//! So the quoted number is the STACK, not FRI; FRI alone is 0.315 ms.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use kok_fri::air::{merkle_root, TileAir};

type Matrix = Vec<Vec<u64>>;

fn toy(seed: u64) -> (Matrix, Matrix, Matrix, Matrix) {
    let mut s = seed;
    let mut mk = || {
        let mut out = vec![vec![0u64; 8]; 8];
        for row in out.iter_mut() {
            for cell in row.iter_mut() {
                s = s
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                *cell = s % 97;
            }
        }
        out
    };
    (mk(), mk(), mk(), mk())
}

fn bench_air_prove(c: &mut Criterion) {
    let (a, b, e, f) = toy(20260925);
    let air = TileAir::new(97, 2);
    let n = 8;
    let m = n / 2;
    let (i, j) = (1, 2);
    let mut acc = 0u64;
    for l in 0..m {
        acc = (acc
            + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
            % 97;
    }
    c.bench_function("air prove (one tile, q=97 n=8)", |bencher| {
        bencher.iter(|| {
            let proof = air.prove(
                black_box(&a),
                black_box(&b),
                black_box(&e),
                black_box(&f),
                777,
                i,
                j,
                acc,
            );
            black_box(proof.is_ok());
        })
    });
}

fn bench_air_verify(c: &mut Criterion) {
    let (a, b, e, f) = toy(20260925);
    let air = TileAir::new(97, 2);
    let n = 8;
    let m = n / 2;
    let (i, j) = (1, 2);
    let mut acc = 0u64;
    for l in 0..m {
        acc = (acc
            + (a[i * 2][l * 2] + e[i * 2][l * 2]) % 97 * (b[l * 2][j * 2] + f[l * 2][j * 2]) % 97)
            % 97;
    }
    let flat_a: Vec<u64> = a.iter().flatten().copied().collect();
    let flat_b: Vec<u64> = b.iter().flatten().copied().collect();
    let a_commit = merkle_root(&flat_a);
    let b_commit = merkle_root(&flat_b);
    let proof = air.prove(&a, &b, &e, &f, 777, i, j, acc).unwrap();
    c.bench_function("air verify (one tile, q=97 n=8)", |bencher| {
        bencher.iter(|| {
            black_box(air.verify(
                black_box(&proof),
                acc,
                black_box(&e),
                black_box(&f),
                i,
                j,
                a_commit,
                b_commit,
            ));
        })
    });
}

criterion_group!(air_benches, bench_air_prove, bench_air_verify);
criterion_main!(air_benches);

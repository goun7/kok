//! Criterion benchmark for the difficulty controller.
//!
//! The retarget loop is what makes the G layer target a block RATE rather
//! than a fixed difficulty. This benchmarks a full convergence run (600
//! simulated blocks at constant hashrate) so the claim "D converges to
//! Lambda*T_b" is a measurement the repo produces, not a line in prose.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use kok_poum::retarget::{RetargetParams, Retargetor};
use rand::SeedableRng;

fn bench_retarget_convergence(c: &mut Criterion) {
    c.bench_function("retarget: 600 simulated blocks to equilibrium", |bencher| {
        bencher.iter(|| {
            let params = RetargetParams {
                window: 100,
                target_block_time: 0.1,
                clip: 4.0,
                median_width: 3,
            };
            let mut r = Retargetor::new(params, 100);
            let mut rng = rand::rngs::StdRng::seed_from_u64(1);
            for _ in 0..600 {
                black_box(r.sim_block(10000.0, &mut rng));
            }
            black_box(r.d);
        })
    });
}

criterion_group!(retarget_benches, bench_retarget_convergence);
criterion_main!(retarget_benches);

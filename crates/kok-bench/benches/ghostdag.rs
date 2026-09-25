//! Criterion benchmark for the GHOSTDAG ordering — the latency the 10 BPS
//! target must fit under (T_b = 100 ms; ordering must be a small fraction).

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use kok_ghostdag::sim::mine_chain;
use kok_ghostdag::Ghostdag;
use rand::SeedableRng;

fn bench_ordering_latency(c: &mut Criterion) {
    // 10 BPS for one minute = 600 blocks; the fork rate models a network
    // with 3 miners and real propagation delay
    c.bench_function("ghostdag order (600 blocks, fork 0.3)", |bencher| {
        bencher.iter(|| {
            let mut g = Ghostdag::new(18);
            let mut rng = rand::rngs::StdRng::seed_from_u64(1);
            let tips = mine_chain(&mut g, 600, &mut rng, &["A", "B", "C"], 0.3);
            let tip = *tips.last().unwrap();
            black_box(g.order(tip));
        })
    });
}

criterion_group!(gd_benches, bench_ordering_latency);
criterion_main!(gd_benches);

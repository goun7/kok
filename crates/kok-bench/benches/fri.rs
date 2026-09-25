//! Criterion benchmark for the FRI port.
//!
//! MEASURED on the canonical polynomial both languages share (random.seed
//! 20260925), so this number is comparable with the Python prototype's own
//! timing. The orchestrator's quoted figures are resolved here: the 0.37 ms
//! "FRI verify" is the AIR+FRI stack (0.365 ms measured); FRI alone measures
//! 0.315 ms in Python.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use kok_fri::{canonical::CANON_POLY, recursive_prove, verify_transcript};

const Q: u64 = 97;
const ROUNDS: usize = 3;

fn bench_fri_prove(c: &mut Criterion) {
    c.bench_function("fri recursive_prove (deg 7, 3 rounds, q=97)", |bencher| {
        bencher.iter(|| {
            let (tr, alphas) = recursive_prove(black_box(&CANON_POLY), black_box(ROUNDS), Q)
                .expect("canonical fold must succeed");
            black_box((tr, alphas));
        })
    });
}

fn bench_fri_verify(c: &mut Criterion) {
    // precompute once — the benchmark measures VERIFICATION, not proving
    let (tr, alphas) = recursive_prove(&CANON_POLY, ROUNDS, Q).unwrap();
    c.bench_function("fri verify_transcript (deg 7, 3 rounds, q=97)", |bencher| {
        bencher.iter(|| {
            black_box(verify_transcript(black_box(&tr), black_box(&alphas), Q));
        })
    });
}

criterion_group!(fri_benches, bench_fri_prove, bench_fri_verify);
criterion_main!(fri_benches);

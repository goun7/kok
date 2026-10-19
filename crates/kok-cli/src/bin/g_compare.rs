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

#[cfg(test)]
mod tests {
    use super::*;

    /// THE BENCHMARK'S PREMISE: the fixture is reproducible (2026-09-28).
    ///
    /// g_compare exists to measure Python and Rust on THE SAME input — the
    /// file's first line is that claim. If canon() were not byte-identical
    /// between two calls, the comparison would be measuring two different
    /// problems and every ratio it prints would be meaningless. The function
    /// copies two consts, so this is by construction; the reason to pin it is
    /// that the benchmark's headline claim depends on it and nothing else in
    /// the workspace holds the fixture to that.
    #[test]
    fn the_canonical_fixture_is_reproducible() {
        let (a1, b1) = canon();
        let (a2, b2) = canon();
        assert_eq!(a1, a2, "canon() returned a different A on a second call");
        assert_eq!(b1, b2, "canon() returned a different B on a second call");
        // and it is the fixture the kernel's canonical module defines, not a
        // copy that could drift from it
        assert_eq!(
            a1, canonical::CANON_A,
            "canon() does not match canonical::CANON_A — the benchmark's input drifted from the source of truth"
        );
        assert_eq!(b1, canonical::CANON_B);
    }

    /// THE FIXTURE IS SQUARE AND THE RIGHT SIZE, because the benchmark's
    /// timings are per-problem-size claims. canon() derives its width from the
    /// const's own shape, so a ragged or mis-sized fixture would change the
    /// amount of work measured while the printed line still says the same
    /// target exponent. KwKernel is built with TOY_R over an 8-wide problem,
    /// and the noise/prove calls take a.len() — so the fixture's width must
    /// agree with what the kernel was constructed for.
    #[test]
    fn the_canonical_fixture_is_square_and_sized_for_the_kernel() {
        let (a, b) = canon();
        assert_eq!(a.len(), 8, "matrix A is not 8 rows");
        assert_eq!(b.len(), 8, "matrix B is not 8 rows");
        for (i, row) in a.iter().enumerate() {
            assert_eq!(
                row.len(),
                8,
                "matrix A row {i} is not 8 wide — the fixture is ragged"
            );
        }
        for (i, row) in b.iter().enumerate() {
            assert_eq!(
                row.len(),
                8,
                "matrix B row {i} is not 8 wide — the fixture is ragged"
            );
        }
        // the two operands must be conformable for the kernel's multiply
        assert_eq!(a.len(), b.len());
        assert!(
            a.len() % TOY_R == 0,
            "the fixture width is not divisible by r={TOY_R}"
        );
    }

    /// EVERY FIXTURE ENTRY IS A FIELD ELEMENT. The kernel's verify compares
    /// the tile accumulator against a target modulo TOY_Q, so an entry at or
    /// above TOY_Q would make the benchmark's acceptance measurements operate
    /// on numbers outside the field the arithmetic is defined over — timings
    /// for work that is not the work being claimed. The fixture is hand-written
    /// and this is the only place that bounds it, so the bound is pinned here.
    #[test]
    fn every_canonical_entry_is_inside_the_field() {
        let (a, b) = canon();
        for (mi, m) in [("A", &a), ("B", &b)] {
            for (i, row) in m.iter().enumerate() {
                for (j, &v) in row.iter().enumerate() {
                    assert!(
                        v < TOY_Q,
                        "canonical matrix {mi}[{i}][{j}] = {v} is outside the field (q={TOY_Q})"
                    );
                }
            }
        }
    }
}

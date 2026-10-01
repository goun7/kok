//! kok-node — the KÖK Network v2 sovereign L1 node binary.
//!
//! Round-6 / F3 (2026-09-24). The workspace crate that owns the entry point;
//! the consensus lives in kok-consensus, the benchmarks in kok-bench.

use std::time::Instant;
use kok_consensus::kok_poum::{Certificate, KwKernel, TOY_N, TOY_Q, TOY_R};

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

fn main() {
    println!("============================================================================");
    println!("KOK NETWORK v2 — sovereign L1 node (Rust workspace, F3 2026-09-24)");
    println!("============================================================================");
    println!();
    println!("  Layer G : MatMul PoW certificate (KwKernel, q={} n={} r={})", TOY_Q, TOY_N, TOY_R);
    println!("  Layer U : fee-paid verifiable compute — zero consensus weight (skeleton)");
    println!();

    let k = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = toy_matrices(20260919);
    let ctx = 777u64;
    let target = 1u64 << 1;

    let t0 = Instant::now();
    let mut nonce = 0u64;
    let cert = loop {
        nonce += 1;
        if let Some(c) = k.prove(&a, &b, ctx, nonce, target) {
            break c;
        }
    };
    let prove_us = t0.elapsed().as_micros();

    let t1 = Instant::now();
    let ok = k.verify(&cert, &a, &b, ctx, nonce, target);
    let verify_us = t1.elapsed().as_micros();

    println!("  honest certificate ground at nonce {}", nonce);
    println!("  tile (i={}, j={}) accumulator = {}", cert.i, cert.j, cert.value);
    println!();
    println!("  MEASURED  prove : {:.3} ms", prove_us as f64 / 1000.0);
    println!("  MEASURED  verify: {:.3} ms", verify_us as f64 / 1000.0);
    println!("  (Python toy baseline at the same target: prove 3.47 ms / verify 0.25 ms)");
    println!();

    let forged = Certificate {
        i: cert.i,
        j: cert.j,
        value: (cert.value + 1) % TOY_Q,
        m: cert.m,
    };
    let forged_ok = k.verify(&forged, &a, &b, ctx, nonce, target);
    let replay_ok = k.verify(&cert, &a, &b, ctx + 1, nonce, target);
    let width_cert = Certificate { m: cert.m + 1, ..cert.clone() };
    let width_ok = k.verify(&width_cert, &a, &b, ctx, nonce, target);

    println!("  forged tile value rejected         : {}", !forged_ok);
    println!("  replay under other ctx rejected    : {}", !replay_ok);
    println!("  width binding holds                : {}", !width_ok);
    println!();
    if ok && !forged_ok && !replay_ok && !width_ok {
        println!("  RESULT: G LAYER PORT VERIFIED — honest accepts, all three forgeries reject");
    } else {
        println!("  RESULT: PORT FAILED");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    //! The binary's own verification, as tests rather than println + exit code.
    //!
    //! WHY THESE EXIST: main() already checks the four properties below and
    //! exits 1 when any fails — but a check that only runs when a person runs
    //! the binary is not exercised by `cargo test`. Everything main() asserts
    //! is mirrored here so the port verification is part of the suite, and a
    //! regression in any of the four fails a test instead of waiting for
    //! someone to notice the banner.

    use super::*;

    /// Same seed must give byte-identical matrices — the demo is reproducible,
    /// and a non-deterministic generator would make the reported nonce
    /// meaningless between runs.
    #[test]
    fn toy_matrices_is_deterministic_for_a_fixed_seed() {
        let (a1, b1) = toy_matrices(20260919);
        let (a2, b2) = toy_matrices(20260919);
        assert_eq!(a1, a2, "toy_matrices was not deterministic for the same seed");
        assert_eq!(b1, b2, "toy_matrices was not deterministic for the same seed");
    }

    /// Every generated entry must lie in the field. An entry at or above TOY_Q
    /// would silently break the kernel's modular arithmetic, and the generator
    /// is the only place that bounds them.
    #[test]
    fn toy_matrices_stays_inside_the_field() {
        let (a, b) = toy_matrices(42);
        for row in &a {
            for &v in row {
                assert!(v < TOY_Q, "a matrix entry {} was not reduced below q={}", v, TOY_Q);
            }
        }
        for row in &b {
            for &v in row {
                assert!(v < TOY_Q, "b matrix entry {} was not reduced below q={}", v, TOY_Q);
            }
        }
    }

    /// Different seeds must give different problems, otherwise two runs of the
    /// demo would be mining the same instance and the reported difficulty
    /// would describe one problem rather than the kernel.
    #[test]
    fn different_seeds_give_different_problems() {
        let (a1, _) = toy_matrices(1);
        let (a2, _) = toy_matrices(2);
        assert_ne!(a1, a2, "two different seeds produced identical matrices");
    }

    /// THE PORT'S OWN CLAIM: an honest certificate verifies, and the three
    /// forgeries main() prints all reject. This is the exit-code check,
    /// promoted to a test so it runs in the suite.
    #[test]
    fn an_honest_certificate_verifies_and_all_three_forgeries_reject() {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy_matrices(20260919);
        let ctx = 777u64;
        let target = 1u64 << 1;

        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, ctx, nonce, target) {
                break c;
            }
        };

        assert!(k.verify(&cert, &a, &b, ctx, nonce, target), "the honest certificate was rejected");

        let forged = Certificate {
            i: cert.i,
            j: cert.j,
            value: (cert.value + 1) % TOY_Q,
            m: cert.m,
        };
        assert!(!k.verify(&forged, &a, &b, ctx, nonce, target), "a forged tile value was accepted");

        assert!(!k.verify(&cert, &a, &b, ctx + 1, nonce, target), "the certificate replayed under a foreign ctx was accepted");

        let width_cert = Certificate { m: cert.m + 1, ..cert.clone() };
        assert!(!k.verify(&width_cert, &a, &b, ctx, nonce, target), "a certificate with a wrong width was accepted");
    }
}


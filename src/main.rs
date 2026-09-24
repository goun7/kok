//! kok-node — the KÖK Network v2 sovereign L1 node binary.
//!
//! Round-6 / F3 skeleton (2026-09-24). This is the F3a-then-F3 sequence the
//! project committed to: the Python prototypes proved the math (theta 1.657,
//! FRI degree bound, E-gap binding), and the Rust core carries it. The G
//! layer is ported first because leader selection depends on it.

use std::time::Instant;
use kok_node::{Certificate, KwKernel, TOY_N, TOY_Q, TOY_R};

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
    println!("KOK NETWORK v2 - sovereign L1 node (Rust core, F3 skeleton 2026-09-24)");
    println!("============================================================================");
    println!();
    println!("  Layer G : MatMul PoW certificate (KwKernel, q={} n={} r={})", TOY_Q, TOY_N, TOY_R);
    println!("  Layer U : fee-paid verifiable compute (zero consensus weight) - TODO F3");
    println!();

    let k = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = toy_matrices(20260919);
    let ctx = 777u64;
    let target = 1u64 << 1; // toy difficulty; matches the Python measurement

    // honest mining loop, the same shape the Python probe ran
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

    // the three security properties the Python probes established, re-run here
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

    println!("  forged tile value rejected : {}", !forged_ok);
    println!("  replay under other ctx rejected: {}", !replay_ok);
    println!("  width binding holds        : {}", !width_ok);
    println!();
    if ok && !forged_ok && !replay_ok && !width_ok {
        println!("  RESULT: G LAYER PORT VERIFIED - honest accepts, all three forgeries reject");
        println!("  cargo test proof: the same four checks live in src/consensus/poum.rs");
    } else {
        println!("  RESULT: PORT FAILED - investigating");
        std::process::exit(1);
    }
}

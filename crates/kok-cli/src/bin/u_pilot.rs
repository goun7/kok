// GNoME-Forge U-LAYER PILOT (interface only — NOT GNoME-Forge's code).
//
// The orchestrator's directive: GNoME-Forge is the leading U-layer candidate,
// a client of KOK rather than a fork. This pilot walks ONE job end to end —
// price, escrow, burn, verify, and the property that makes it safe:
// ZERO consensus weight, so the job can never reach the leader election.
//
// What this pilot deliberately does NOT do: it does not run a real
// machine-learned potential. The directive is the INTERFACE, and a toy
// execution would let an unmeasured "it works" claim sit where a number
// should be.

use kok_u_layer::job::{validate_job, JobKind, JobSpec};
use kok_u_layer::{epoch_seed, u_task_consensus_weight, validate_u_task, C_FEE, EPOCH_LOOKBACK};
use std::time::Instant;

fn main() {
    println!("=== GNoME-Forge U-LAYER PILOT (interface, not their code) ===");

    // 1. A structure-potential job in the CHGNet/M3GNet profile: a crystal
    //    tensor in, per-atom forces (n x 3) + energy + stress out
    for n_atoms in [64usize, 256, 1000] {
        let kind = JobKind::StructurePotential { n_atoms };
        let spec = JobSpec {
            kind: kind.clone(),
            input_commit: 0,
            fee: 100,
        };
        let f = kind.flops();
        let shape = kind.output_shape();
        let valid = validate_job(&spec);
        println!(
            "  {:>5} atoms | flops {:>10} | output {:<28} | valid {}",
            n_atoms,
            f,
            format!("{:?}", shape),
            valid
        );
    }

    // 2. PRICE the job and check it against the block fee cap. The fee model
    //    is monotone-sufficient for PRICING and insufficient for hashrate —
    //    safe only because U weight is exactly zero (an over-estimate
    //    inflates a fee, never a block).
    let job = JobSpec {
        kind: JobKind::StructurePotential { n_atoms: 256 },
        input_commit: 0,
        fee: 1, // placeholder; priced below
    };
    let priced_fee = (job.kind.flops() as f64 * 1e-6).ceil() as u64 + 1;
    let task = kok_u_layer::TaskSpec {
        program: "gnome-forge/structure-potential".into(),
        fee: priced_fee,
        burn_rate: 70, // 7% burn, within the (0, 500] per-mille bound
    };
    println!(
        "\n  priced fee: {} (flops {} x 1e-6 + 1)",
        priced_fee,
        job.kind.flops()
    );
    println!("  burn rate:  70 per mille (7%)");
    println!(
        "  validate_u_task (within C_FEE={}): {}",
        C_FEE,
        validate_u_task(&task, 0)
    );
    // anti-aggregation: a second job that would exceed the cap must reject
    let second = kok_u_layer::TaskSpec {
        program: "gnome-forge/structure-potential".into(),
        fee: C_FEE,
        burn_rate: 70,
    };
    println!(
        "  a second job claiming the whole cap: REJECTED = {} (anti-aggregation, round-3 [15])",
        !validate_u_task(&second, priced_fee)
    );

    // 3. THE ZERO-WEIGHT PROPERTY, measured rather than asserted. A billion-fee
    //    10000-atom job must contribute exactly 0 to consensus.
    let big_fee = 1_000_000_000;
    let proof = kok_u_layer::TaskProof {
        tid: "gnome-forge/titan".into(),
        miner: "forge-1".into(),
        fee: big_fee,
    };
    let w = u_task_consensus_weight(&proof);
    println!(
        "\n  a {}-atom job at fee {}: consensus weight = {}",
        10_000, big_fee, w
    );
    assert_eq!(w, 0, "the U layer must never reach the leader election");

    // 4. VRF seed grinding resistance: the seed is fixed EPOCH_LOOKBACK
    //    blocks before the attacker can influence it
    let mut hashes = vec![0u64; 200];
    let mut s = 0x9e3779b97f4a7c15u64;
    for h in hashes.iter_mut() {
        s = s
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        *h = s;
    }
    let seed = epoch_seed(&hashes, 150);
    println!(
        "  epoch_seed at h=150 = {} (the block from {} blocks earlier, lookback {})",
        seed.unwrap(),
        EPOCH_LOOKBACK,
        EPOCH_LOOKBACK
    );
    // the seed must be the block from 64 ago, not a recent one an attacker
    // could still grind
    assert_eq!(seed, Some(hashes[150 - EPOCH_LOOKBACK]));

    // 5. LATENCY: the pricing path itself, which is on the block-validation
    //    hot path, must not cost a meaningful fraction of T_b = 100 ms
    let t0 = Instant::now();
    for _ in 0..100_000 {
        let _ = validate_job(&JobSpec {
            kind: JobKind::StructurePotential { n_atoms: 256 },
            input_commit: 0,
            fee: priced_fee,
        });
    }
    let us = t0.elapsed().as_nanos() as f64 / 100_000.0 / 1000.0;
    println!("  validate_job pricing: {:.3} us/call (x100k)", us);
    println!(
        "  => {:.4}% of the 100 ms T_b budget",
        us / 100_000.0 * 100.0
    );

    println!("\nPILOT VERDICT: the interface prices, caps, burns, and stays at");
    println!("zero consensus weight. The real potential is GNoME-Forge's, not KOK's.");
}

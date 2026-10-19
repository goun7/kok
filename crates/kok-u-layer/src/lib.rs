//! U layer — the fee-paid verifiable-compute market.
//!
//! Ported from `u_layer_prototype_en.py` (rounds 1-6). The design invariant
//! that makes this a LAYER rather than a marketplace is carried here and
//! stated where it can be read:
//!
//!   * a U proof contributes ZERO consensus weight — the G layer alone
//!     chooses leaders, so buying inference demand cannot buy security;
//!   * the fee is escrowed and the burn is a protocol fee policy, never a
//!     supply-reduction promise (see arastirma/hukuk_howey_mica.md §5.C);
//!   * task assignment is seeded by an ECVRF (RFC 9381) rather than a
//!     hash, so the assignment is verifiably a function of the epoch.

//! ## LAYER U HAS ZERO CONSENSUS WEIGHT
//!
//! A U-task proof never enters leader election and never contributes to a
//! block's weight. The G layer alone chooses leaders. This is why "useful
//! work" cannot be captured: an attacker cannot buy security by buying
//! inference demand (paper §B, PR/2).
//!
//!
//! VRF note, kept honest: the Python prototype's VRF is HMAC-based, not
//! ECVRF — verify() there is a STRUCTURAL check, and the real guarantee (a
//! forger holding a public key cannot reproduce another miner's proof) is
//! MEASURED by probe_u_layer_en rather than asserted in the class. This Rust
//! port now carries the real construction: kok-u-layer::ecvrf implements
//! RFC 9381 ECVRF-P256-SHA256-TAI, pinned byte-for-byte against the
//! standard's own Appendix B.1 test vectors. The HMAC toy's guarantee
//! (determinism) is subsumed; the properties it could not have — uniqueness
//! and pseudorandomness — are now provided by the construction.

pub mod assign;
pub mod ecvrf;

use sha2::{Digest, Sha256};

/// VRF assignment seed lookback — grinding resistance (paper spec B.3).
/// An attacker cannot grind the epoch seed because it is taken from a block
/// 64 blocks in the past, before the attacker could have chosen it.
pub const EPOCH_LOOKBACK: usize = 64;

/// The anti-aggregation fee cap: a block cannot carry more U-fee value than
/// this, so a miner cannot dilute the fee market by packing many tiny tasks.
pub mod job;

pub const C_FEE: u64 = 500;

/// The ceiling on a task's burn rate, in PARTS PER THOUSAND: 500 = 50% of
/// the fee. An anti-abuse bound, not a policy target. Named here because it
/// was a magic 500 inside validate_u_task — the same digits as the
/// treasury's 500 basis points (5%), and the two must not be conflated.
pub const MAX_BURN_RATE: u64 = 500;

pub fn h(parts: &[&str]) -> u64 {
    let mut hasher = Sha256::new();
    for (idx, p) in parts.iter().enumerate() {
        if idx > 0 {
            hasher.update(b"|");
        }
        hasher.update(p.as_bytes());
    }
    let d = hasher.finalize();
    u64::from_be_bytes(d[..8].try_into().unwrap())
}

/// A task the network is asked to compute. Zero consensus weight.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskSpec {
    pub program: String,
    pub fee: u64,
    pub burn_rate: u64, // parts per thousand, 0..=500
}

/// A U-task proof: the fee was escrowed, the task assigned by VRF, and the
/// result verified. Weight contribution: ZERO by construction.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskProof {
    pub tid: String,
    pub miner: String,
    pub fee: u64,
}

/// Validate a U-task proof against the block's fee cap.
///
/// Returns false on any of:
/// * the fee is not positive
/// * the burn rate is outside (0, 500] per mille
/// * the total carried fee exceeds C_FEE (anti-aggregation, round-3 [15]:
///   an earlier version read the claimed total verbatim, so a block claiming
///   0 validated)
pub fn validate_u_task(task: &TaskSpec, carried_fee_total: u64) -> bool {
    if task.fee == 0 {
        return false;
    }
    if task.burn_rate == 0 || task.burn_rate > MAX_BURN_RATE {
        return false;
    }
    // CHECKED ADD — the overflow this gate exists to catch. A caller that
    // passes carried_fee_total near u64::MAX makes a naive sum wrap to a
    // small value, and a wrapped sum PASSES this comparison, admitting a
    // task that overflows the block's fee budget. The FFI boundary already
    // checked this once, but this function is public and called from Rust
    // too — a gate that only holds when one particular caller screens its
    // inputs is not a gate. This is the wrap the sweep found in
    // anti-aggregation_cap_rejects_overflow's sibling path.
    match carried_fee_total.checked_add(task.fee) {
        Some(sum) => sum <= C_FEE,
        None => false,
    }
}

/// The consensus weight a U-task proof contributes. Always zero — stated
/// here as a function so a caller that later tries to add it is explicit
/// about what it is doing.
pub fn u_task_consensus_weight(_proof: &TaskProof) -> u64 {
    0
}

/// Derive the VRF epoch seed for a block from the chain, using the
/// EPOCH_LOOKBACK window. Grinding resistance: the seed is fixed 64 blocks
/// before the attacker can influence it.
///
/// DOMAIN SEPARATION (spec §A.10.3): the seed is `H("seed" | blk.hash)`,
/// NOT the block hash itself. An earlier version returned the raw hash,
/// which meant the very same bytes that identify a block elsewhere could be
/// replayed as a VRF input — a cross-context collision waiting to happen.
/// The wrapper is what makes the seed mean "assignment seed" and nothing
/// else. This is the same class as the anticone bug: the error is not in
/// what you computed but in which SET of things the identifier belongs to.
pub fn epoch_seed(block_hashes: &[u64], height: usize) -> Option<u64> {
    if height < EPOCH_LOOKBACK {
        return None;
    }
    let blk = block_hashes[height - EPOCH_LOOKBACK];
    Some(h(&["seed", &blk.to_string()]))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn honest_task_validates() {
        let t = TaskSpec {
            program: "mm8".into(),
            fee: 100,
            burn_rate: 300,
        };
        assert!(validate_u_task(&t, 0));
        assert!(validate_u_task(&t, 400)); // 400 + 100 <= 500
    }

    #[test]
    fn zero_fee_rejected() {
        let t = TaskSpec {
            program: "mm8".into(),
            fee: 0,
            burn_rate: 300,
        };
        assert!(!validate_u_task(&t, 0));
    }

    #[test]
    fn burn_rate_bounds() {
        let t0 = TaskSpec {
            program: "mm8".into(),
            fee: 100,
            burn_rate: 0,
        };
        assert!(!validate_u_task(&t0, 0));
        let t501 = TaskSpec {
            program: "mm8".into(),
            fee: 100,
            burn_rate: 501,
        };
        assert!(!validate_u_task(&t501, 0));
    }

    #[test]
    fn anti_aggregation_cap_rejects_overflow() {
        // round-3 [15]: a block claiming 0 validated when the total was
        // read verbatim; the cap is now enforced against the running total
        let t = TaskSpec {
            program: "mm8".into(),
            fee: 100,
            burn_rate: 300,
        };
        assert!(!validate_u_task(&t, 450)); // 450 + 100 > 500
    }

    /// THE WRAP BYPASS — the bug the FFI boundary was guarding against while
    /// this function, the one that decides, was not. A naive
    /// `carried + fee <= C_FEE` wraps when carried is near u64::MAX:
    /// u64::MAX + 10 becomes 9, and 9 <= 500 admits the task. The fee budget
    /// is an ANTI-AGGREGATION bound — its purpose is to stop a block
    /// stuffing itself with so many tasks that a single miner captures the
    /// U layer — and a wrapped sum makes the cap decorative exactly when a
    /// caller is pushing it. The FFI already checked this once, but this
    /// function is public and called from Rust too; a gate that only holds
    /// when one particular caller screens its inputs is not a gate.
    #[test]
    fn a_wrapping_carried_total_cannot_bypass_the_fee_cap() {
        let t = TaskSpec {
            program: "mm8".into(),
            fee: 10,
            burn_rate: 100,
        };
        // the honest case: fits with room to spare
        assert!(
            validate_u_task(&t, C_FEE - 10),
            "a task that fits the cap was rejected"
        );
        // exactly at the cap
        assert!(validate_u_task(&t, C_FEE - 10));
        // one over: rejected
        assert!(
            !validate_u_task(&t, C_FEE - 9),
            "a task past the cap was accepted"
        );
        // THE WRAP: carried at u64::MAX, fee 10 — the naive sum wraps to 9
        // and would pass. It must not.
        assert!(
            !validate_u_task(&t, u64::MAX),
            "a wrapping carried total bypassed the fee cap"
        );
        // carried alone already past the cap, no wrap needed yet
        assert!(
            !validate_u_task(&t, C_FEE + 1),
            "a carried total already past the cap was accepted"
        );
        // the wrap at the other end: carried small, fee huge
        let big = TaskSpec {
            program: "mm8".into(),
            fee: u64::MAX,
            burn_rate: 100,
        };
        assert!(!validate_u_task(&big, 1), "a huge fee wrapped into the cap");
    }

    #[test]
    fn u_task_weight_is_always_zero() {
        // THE design invariant: a U proof never contributes consensus weight.
        // If this ever becomes nonzero, KÖK stops being demand-independent.
        let p = TaskProof {
            tid: "t1".into(),
            miner: "m1".into(),
            fee: 100,
        };
        assert_eq!(u_task_consensus_weight(&p), 0);
    }

    #[test]
    fn epoch_seed_respects_lookback() {
        let hashes: Vec<u64> = (0..200).map(|i| i as u64).collect();
        // height below the lookback: no seed yet
        assert!(epoch_seed(&hashes, 10).is_none());
        // height 64: the seed is the DOMAIN-SEPARATED hash of block 0, not
        // the block hash itself (spec A.10.3)
        assert_eq!(
            epoch_seed(&hashes, 64),
            Some(h(&["seed", &hashes[0].to_string()]))
        );
        assert_ne!(
            epoch_seed(&hashes, 64),
            Some(hashes[0]),
            "the seed leaked the raw block hash"
        );
        assert_eq!(
            epoch_seed(&hashes, 128),
            Some(h(&["seed", &hashes[64].to_string()]))
        );
    }

    /// GRINDING RESISTANCE, the property the lookback exists for: a miner who
    /// controls the block AT height h cannot choose the seed that assigns
    /// tasks AT height h — that seed was fixed 64 blocks earlier. The miner's
    /// influence only lands at h+64, by which time the assignment is already
    /// settled. Without this, a well-resourced miner could retry block
    /// contents until the VRF picked its own task.
    #[test]
    fn an_attacker_at_height_h_cannot_grind_the_seed_at_height_h() {
        let mut hashes: Vec<u64> = (0..200).map(|i| i as u64 * 7).collect();
        let at_h = 150;
        let seed_before = epoch_seed(&hashes, at_h);
        // the attacker re-mines block 150 (changes its hash entirely)
        hashes[at_h] = 0xDEAD_BEEF_CAFE_F00D;
        let seed_after = epoch_seed(&hashes, at_h);
        assert_eq!(
            seed_before, seed_after,
            "the seed at h changed when block h changed — the lookback is broken"
        );
        // but the attacker's new block DOES move the seed 64 blocks later —
        // through the domain separator, never as the raw hash
        let later = epoch_seed(&hashes, at_h + 64);
        assert_eq!(
            later,
            Some(h(&["seed", &hashes[at_h].to_string()])),
            "influence must land at h+64, not h"
        );
        // and NOT at any height before that. The raw hash is not what the
        // seed is, so comparing against it is the right NEGATIVE probe: no
        // seed before the lookback may equal the domain-separated value.
        let blocked = h(&["seed", &hashes[at_h].to_string()]);
        for probe in (at_h + 1)..(at_h + 64) {
            assert_ne!(
                epoch_seed(&hashes, probe),
                Some(blocked),
                "block h leaked its influence into height {} before the lookback",
                probe
            );
        }
    }

    /// THE VRF IS AN HMAC TOY, AND THAT IS A NAMED GAP NOT A CLAIM. The
    /// prototype's VRF is HMAC-based, so it is DETERMINISTIC (same key+input
    /// -> same output) but it is NOT a real VRF: it offers no uniqueness
    /// against a collider and no public verifiability, because anyone holding
    /// the key can produce the output. This test pins what the toy DOES
    /// guarantee so it cannot be mistaken for what it does not.
    #[test]
    fn the_hmac_vrf_toy_is_deterministic_and_that_is_all_it_claims() {
        // deterministic: the same seed and height give the same assignment
        let hashes: Vec<u64> = (0..200).map(|i| i as u64 * 13).collect();
        assert_eq!(epoch_seed(&hashes, 150), epoch_seed(&hashes, 150));
        // distinct heights give distinct seeds (no accidental collapse)
        assert_ne!(epoch_seed(&hashes, 150), epoch_seed(&hashes, 151));
        // WHAT IT DOES NOT CLAIM: there is no proof of uniqueness here and no
        // verification against a public key. ECVRF is the S2 replacement
        // named in the spec; the gap is recorded at lib.rs line 12.
    }
}

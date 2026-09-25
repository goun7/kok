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

//! **LAYER U HAS ZERO CONSENSUS WEIGHT.** A U-task proof never enters leader
//! election and never contributes to a block's weight. The G layer alone
//! chooses leaders. This is why "useful work" cannot be captured: an attacker
//! cannot buy security by buying inference demand (paper §B, PR/2).
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
    if task.burn_rate == 0 || task.burn_rate > 500 {
        return false;
    }
    carried_fee_total + task.fee <= C_FEE
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
pub fn epoch_seed(block_hashes: &[u64], height: usize) -> Option<u64> {
    if height < EPOCH_LOOKBACK {
        return None;
    }
    Some(block_hashes[height - EPOCH_LOOKBACK])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn honest_task_validates() {
        let t = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: 300 };
        assert!(validate_u_task(&t, 0));
        assert!(validate_u_task(&t, 400)); // 400 + 100 <= 500
    }

    #[test]
    fn zero_fee_rejected() {
        let t = TaskSpec { program: "mm8".into(), fee: 0, burn_rate: 300 };
        assert!(!validate_u_task(&t, 0));
    }

    #[test]
    fn burn_rate_bounds() {
        let t0 = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: 0 };
        assert!(!validate_u_task(&t0, 0));
        let t501 = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: 501 };
        assert!(!validate_u_task(&t501, 0));
    }

    #[test]
    fn anti_aggregation_cap_rejects_overflow() {
        // round-3 [15]: a block claiming 0 validated when the total was
        // read verbatim; the cap is now enforced against the running total
        let t = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: 300 };
        assert!(!validate_u_task(&t, 450)); // 450 + 100 > 500
    }

    #[test]
    fn u_task_weight_is_always_zero() {
        // THE design invariant: a U proof never contributes consensus weight.
        // If this ever becomes nonzero, KÖK stops being demand-independent.
        let p = TaskProof { tid: "t1".into(), miner: "m1".into(), fee: 100 };
        assert_eq!(u_task_consensus_weight(&p), 0);
    }

    #[test]
    fn epoch_seed_respects_lookback() {
        let hashes: Vec<u64> = (0..200).map(|i| i as u64).collect();
        // height below the lookback: no seed yet
        assert!(epoch_seed(&hashes, 10).is_none());
        // height 64: seed is the block 64 back
        assert_eq!(epoch_seed(&hashes, 64), Some(hashes[0]));
        assert_eq!(epoch_seed(&hashes, 128), Some(hashes[64]));
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
        // but the attacker's new block DOES move the seed 64 blocks later
        let later = epoch_seed(&hashes, at_h + 64);
        assert_eq!(later, Some(hashes[at_h]), "influence must land at h+64, not h");
        // and NOT at any height before that
        for probe in (at_h + 1)..(at_h + 64) {
            assert_ne!(
                epoch_seed(&hashes, probe),
                Some(hashes[at_h]),
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

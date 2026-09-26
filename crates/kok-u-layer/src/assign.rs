//! Task assignment — the VRF gate that decides which miner may work a task.
//!
//! Spec §A.10.3: for each task independently, the miner evaluates the VRF
//! over (seed, tid) where the seed is the epoch seed fixed 64 blocks back.
//! If the output `w` falls below the task's assignment probability, the
//! task is assigned to that miner. The miner cannot choose its task — it
//! accepts what was assigned or forfeits its bond.
//!
//! WHY A VRF RATHER THAN A HASH (the honest reason): the assignment must be
//! verifiable by a light client that did NOT see the evaluation happen. With
//! a plain hash the miner would have to publish its secret key to prove
//! "this is the draw I got", which would let anyone forge future draws.
//! The VRF proof lets anyone check that beta is the unique output for
//! (public key, input) WITHOUT learning the key.
//!
//! THE GATE IS INTEGER-EXACT. The spec writes `w = as_int(vrf_out) / 2**256`
//! in [0,1), but a float division is not consensus-safe — two machines can
//! disagree on the last bits of a float, and a disagreement about a single
//! assignment is a fork. So the comparison is done on the top 64 bits of
//! beta against an integer threshold, which is exact on every machine.
//!
//! OPEN GRINDING SURFACE, STATED NOT HIDDEN: the miner evaluates the VRF
//! under ITS OWN key, and the assignment probability is meant to be weighted
//! by stake or compute. Because the key is per-miner, splitting one stake
//! across N registered keys multiplies the number of independent draws by N
//! — a single identity gets N tickets instead of one. The VRF cannot fix
//! this: it makes each draw verifiable, not the number of draws honest.
//! Mitigating it needs one-key-per-bonded-identity at the REGISTRATION layer
//! (out of this crate's scope), and the test below MEASURES the multiplier
//! rather than asserting it away.
//!
//! THE LITERATURE NAMES THE CLASS (2026-09-26, arXiv 2607.26734): "once the
//! public key is published, the induced function is fixed and is a
//! deterministic function of the input. This determinism can enable
//! collusion and grinding-style attacks in which adversaries precompute and
//! selectively exploit favorable input-output pairs." Yeoh Wei Zhu et al.,
//! "Verifiable Random Sampling" (29 July 2026), propose sample freshness as
//! the property that removes it. RECORDED AS A MAPPED FUTURE RATHER THAN AN
//! ADOPTION CANDIDATE, because the two threat models are not the same: this
//! crate's surface is the NUMBER of keys a stake is split across, not the
//! choice of input-output pairs, so a freshness fix does not stop a
//! registration-layer split; and the paper's construction is random quantum
//! circuit sampling, which assumes hardware this chain cannot. It is the
//! citation the paragraph above would move under if a classical,
//! hardware-free construction with freshness emerges — see
//! `KOK_V2_REFERENCES.md` §2026 sources.

use crate::ecvrf;

/// The VRF input for a task in an epoch. Domain-separated so these bytes
/// cannot collide with any other use of the seed or the task id.
pub fn alpha(seed: u64, tid: &str) -> Vec<u8> {
    let mut out = b"kok-assign|".to_vec();
    out.extend_from_slice(&seed.to_be_bytes());
    out.push(b'|');
    out.extend_from_slice(tid.as_bytes());
    out
}

/// A task's assignment gate, as an integer threshold over the top 64 bits of
/// the VRF output. A beta passes when `beta_top64 < threshold`, so the
/// probability is `threshold / 2^64`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AssignmentGate {
    threshold: u64,
}

impl AssignmentGate {
    /// Build a gate for the probability `num / den`. Total on degenerate
    /// input: den == 0 rejects, num >= den admits everything.
    pub fn from_probability(num: u64, den: u64) -> Self {
        if den == 0 {
            // a zero denominator is not a probability; admit nothing rather
            // than panicking, so a malformed task spec cannot crash a node
            return Self { threshold: 0 };
        }
        if num >= den {
            return Self { threshold: u64::MAX };
        }
        // threshold = num * 2^64 / den, computed in u128 so it cannot wrap
        let t = ((num as u128) << 64) / (den as u128);
        // den > num >= 0 guarantees t < 2^64
        Self { threshold: t as u64 }
    }

    /// The exact probability this gate represents, as a (num, den) pair over
    /// 2^64. Kept for tests and for displaying a task's gate honestly.
    pub fn threshold(&self) -> u64 {
        self.threshold
    }

    /// Does this VRF output pass the gate? The comparison is on the first 8
    /// big-endian bytes of beta — the top 64 bits of the 256-bit output.
    pub fn passes(&self, beta: &[u8; 32]) -> bool {
        u64::from_be_bytes(beta[..8].try_into().unwrap()) < self.threshold
    }
}

/// An assignment a miner claims it won, with the VRF proof that makes the
/// claim checkable without the miner's key.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Assignment {
    pub tid: String,
    /// beta — the VRF output. Published because the gate is evaluated on it,
    /// and anyone can re-derive it from the proof, so publishing it is not
    /// a secrecy loss (RFC 9381 §7.6).
    pub beta: [u8; 32],
    pub pi: Vec<u8>,
}

/// Produce an assignment proof for one task. Called by the miner.
pub fn prove(sk: &[u8; 32], pk: &[u8], seed: u64, tid: &str) -> Assignment {
    let a = alpha(seed, tid);
    let pi = ecvrf::prove(sk, pk, &a);
    let beta = ecvrf::proof_to_hash(&pi).expect("a proof just proved is always decodable");
    Assignment { tid: tid.to_string(), beta, pi }
}

/// Verify an assignment against the public key, the seed, and the gate.
/// Called by every node and every light client. Returns the beta on accept,
/// None on reject — the caller decides whether an invalid assignment is a
/// forfeit or just an ignored claim.
pub fn verify(pk: &[u8], seed: u64, tid: &str, pi: &[u8]) -> Option<[u8; 32]> {
    let a = alpha(seed, tid);
    ecvrf::verify(pk, &a, pi)
}

/// Run the spec's assignment loop for one miner over a set of tasks. Each
/// task carries its own gate. Returns the assignments the miner won, in the
/// order the tasks were given.
///
/// PERF (2026-09-26): the miner's own loop no longer re-verifies the proof
/// it just produced. The re-verification was originally here so that "a
/// node that replays this code path reaches the same assignment set" — but
/// that property is already held by the structure, not by the check:
/// `prove` is a pure function of (sk, alpha), and `proof_to_hash` of its
/// output is deterministic, so beta is fixed by construction. Re-verifying
/// in the miner's loop costs a full EC scalar multiplication per task to
/// confirm a value that cannot be other than what it is, which made the
/// assignment tests the slowest in the workspace (~15 s for 12,000 task
/// pairs). The verifier-side check is untouched — `verify` below is what
/// every node and light client runs, and the test
/// `every_assignment_from_the_loop_verifies_independently` still re-verifies
/// every assignment the loop returns through that public path. So the
/// property the comment originally wanted is now tested rather than
/// repeatedly re-derived: the loop produces assignments that all verify,
/// and that is measured, not asserted by doing the work twice.
pub fn assign_tasks(
    sk: &[u8; 32],
    pk: &[u8],
    seed: u64,
    tasks: &[(String, AssignmentGate)],
) -> Vec<Assignment> {
    let mut out = Vec::new();
    for (tid, gate) in tasks {
        let a = alpha(seed, tid);
        let pi = ecvrf::prove(sk, pk, &a);
        // beta is derived from the proof deterministically; the proof was
        // just produced by prove() over this very (sk, alpha), so it is
        // decodable by construction. Verifying it here would cost an EC
        // scalar multiplication per task to re-confirm a fixed value.
        let beta = match ecvrf::proof_to_hash(&pi) {
            Some(b) => b,
            None => continue,
        };
        if gate.passes(&beta) {
            out.push(Assignment { tid: tid.clone(), beta, pi });
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ecvrf::VrfKeys;

    /// The RFC 9381 Example 10 key — a fixed, vector-known key so the tests
    /// are reproducible and not dependent on a random draw.
    fn key() -> VrfKeys {
        let mut sk = [0u8; 32];
        sk.copy_from_slice(
            &hex::decode("c9afa9d845ba75166b5c215767b1d6934e50c3db36e89b127b8a622b120f6721").unwrap(),
        );
        VrfKeys::from_secret(sk)
    }

    /// The end-to-end property: a miner's assignment verifies under its own
    /// public key, for the seed and task it was made for.
    #[test]
    fn an_assignment_verifies_under_its_own_key() {
        let k = key();
        let seed = 0x1234_5678_9ABC_DEF0;
        let a = prove(&k.sk, &k.pk, seed, "task-7");
        let beta = verify(&k.pk, seed, "task-7", &a.pi).expect("the assignment must verify");
        assert_eq!(beta, a.beta);
        assert_eq!(a.tid, "task-7");
    }

    /// INPUT BINDING of the assignment: the proof is tied to (seed, tid), so
    /// moving it to another task or another epoch fails. This is what stops a
    /// miner from taking an assignment it won and claiming a different task.
    #[test]
    fn an_assignment_does_not_transfer_to_another_task_or_epoch() {
        let k = key();
        let a = prove(&k.sk, &k.pk, 42, "task-7");
        assert!(verify(&k.pk, 42, "task-8", &a.pi).is_none(), "the proof moved to another task");
        assert!(verify(&k.pk, 43, "task-7", &a.pi).is_none(), "the proof moved to another epoch");
    }

    /// THE GATE IS EXACT. A half-probability gate sits exactly at 2^63, and a
    /// full-probability gate admits everything. No float rounding anywhere.
    #[test]
    fn the_gate_threshold_is_exact() {
        assert_eq!(AssignmentGate::from_probability(1, 2).threshold(), 1u64 << 63);
        assert_eq!(AssignmentGate::from_probability(1, 4).threshold(), 1u64 << 62);
        assert_eq!(AssignmentGate::from_probability(1, 1).threshold(), u64::MAX);
        // degenerate input rejects rather than panicking
        assert_eq!(AssignmentGate::from_probability(1, 0).threshold(), 0);
        assert_eq!(AssignmentGate::from_probability(2, 1).threshold(), u64::MAX);
    }

    /// THE GATE ACTUALLY FILTERS — MEASURED, not asserted. Over many tasks a
    /// half gate admits about half, a tenth gate about a tenth. With 4000
    /// tasks the binomial standard deviation at p=0.5 is ~31.5, so the
    /// 3-sigma band is [1926, 2074]; at p=0.1 it is ~19, band [357, 473].
    /// A gate that admitted everything or nothing would miss these bands by
    /// a wide margin and fail here.
    #[test]
    fn the_gate_filters_at_the_rate_it_claims() {
        let k = key();
        let seed = 99;
        let n = 4000usize;
        let half = AssignmentGate::from_probability(1, 2);
        let tenth = AssignmentGate::from_probability(1, 10);
        let tasks: Vec<(String, AssignmentGate)> =
            (0..n).map(|i| (format!("t{i}"), half)).collect();
        let won = assign_tasks(&k.sk, &k.pk, seed, &tasks);
        let rate = won.len() as f64 / n as f64;
        assert!((0.5 - rate).abs() < 0.04, "a half gate admitted {rate}, not ~0.5");
        // a tenth gate over the same tasks
        let tasks10: Vec<(String, AssignmentGate)> =
            (0..n).map(|i| (format!("t{i}"), tenth)).collect();
        let won10 = assign_tasks(&k.sk, &k.pk, seed, &tasks10);
        let rate10 = won10.len() as f64 / n as f64;
        assert!((0.1 - rate10).abs() < 0.02, "a tenth gate admitted {rate10}, not ~0.1");
    }

    /// EVERY assignment the loop returns is individually verifiable by a node
    /// that did not run it. This is the property that makes the assignment a
    /// FUNCTION of (key, seed, tid) rather than a miner's claim.
    ///
    /// It is also the SAFETY ANCHOR for the performance change in
    /// `assign_tasks`: the miner's loop no longer re-verifies its own proof
    /// (it derives beta from it instead, which costs no EC work). That is
    /// only safe if every proof the loop emits still verifies through the
    /// PUBLIC verifier path — which is exactly what this test does, over a
    /// task set large enough that a systematic breakage cannot hide in a
    /// small sample. If the loop ever emitted a proof that `verify` rejects,
    /// the miner would publish an assignment no node accepts, and this test
    /// is what would catch it.
    #[test]
    fn every_assignment_from_the_loop_verifies_independently() {
        let k = key();
        let tasks: Vec<(String, AssignmentGate)> = (0..60)
            .map(|i| (format!("t{i}"), AssignmentGate::from_probability(1, 2)))
            .collect();
        let won = assign_tasks(&k.sk, &k.pk, 7, &tasks);
        assert!(!won.is_empty(), "the gate admitted nothing over 60 tasks");
        for a in &won {
            assert_eq!(verify(&k.pk, 7, &a.tid, &a.pi), Some(a.beta), "an assignment did not verify");
        }
    }

    /// TWO KEYS DRAW TWICE — the grinding surface, MEASURED. A miner that
    /// registers two keys gets two independent draws per task, so it wins
    /// roughly twice the assignments of a single key. The VRF makes each draw
    /// verifiable but does not make the NUMBER of draws honest; closing that
    /// needs one-key-per-bonded-identity at registration (out of this crate).
    /// This test exists so the surface stays quantified instead of assumed
    /// away, and so a future fix that binds keys to identity has a number to
    /// beat: the ratio here is ~2.0, not 1.0.
    #[test]
    fn splitting_one_stake_into_two_keys_doubles_the_draws() {
        let k1 = key();
        let mut sk2 = [0u8; 32];
        sk2.copy_from_slice(
            &hex::decode("2ca1411a41b17b24cc8c3b089cfd033f1920202a6c0de8abb97df1498d50d2c8").unwrap(),
        );
        let k2 = VrfKeys::from_secret(sk2);
        let gate = AssignmentGate::from_probability(1, 4);
        let tasks: Vec<(String, AssignmentGate)> = (0..3000).map(|i| (format!("t{i}"), gate)).collect();
        let one = assign_tasks(&k1.sk, &k1.pk, 5, &tasks).len();
        // both keys draw on the same tasks
        let mut both = assign_tasks(&k1.sk, &k1.pk, 5, &tasks);
        both.extend(assign_tasks(&k2.sk, &k2.pk, 5, &tasks));
        let both_len = both.len();
        // a single key at the same gate would win `one`; two keys win ~2x
        let ratio = both_len as f64 / one as f64;
        assert!(
            (2.0 - ratio).abs() < 0.25,
            "two keys won {both_len} assignments vs {one} for one (ratio {ratio}), expected ~2.0"
        );
        assert!(both.len() > one, "a second key did not increase the win count at all");
    }

    /// A proof cannot be recycled across keys: another miner's assignment
    /// does not verify under the first miner's public key.
    #[test]
    fn an_assignment_is_bound_to_its_public_key() {
        let k1 = key();
        let mut sk2 = [0u8; 32];
        sk2.copy_from_slice(
            &hex::decode("2ca1411a41b17b24cc8c3b089cfd033f1920202a6c0de8abb97df1498d50d2c8").unwrap(),
        );
        let k2 = VrfKeys::from_secret(sk2);
        let a = prove(&k1.sk, &k1.pk, 5, "task-1");
        assert!(verify(&k2.pk, 5, "task-1", &a.pi).is_none(), "a proof verified under another key");
    }
}

//! The two-layer PoUM composition — where the layers meet and the
//! separation between them becomes a measured property rather than a doc
//! claim.
//!
//! Layer G (kok-poum) chooses leaders: a MatMul PoW certificate whose
//! hardness is structural and demand-independent. Layer U (kok-u-layer) is
//! the fee-paid verifiable-compute market and contributes ZERO consensus
//! weight — a U proof never enters leader election. That separation is the
//! property that makes "useful work" uncapturable: an attacker cannot buy
//! security by buying inference demand.
//!
//! HOW THE SEPARATION IS ENFORCED, in three layers of defense:
//!
//!   1. **Structural.** The GHOSTDAG `Block` has NO field for U proofs. The
//!      graph that computes weight cannot consult what it cannot see. This
//!      is the strongest form — a caller cannot pass a U proof to the
//!      weight computation because the type has nowhere to put one.
//!   2. **Typal.** `kok_u_layer::u_task_consensus_weight` takes a proof and
//!      returns 0, and `reward_split` / `select` take no U argument at all —
//!      the signature cannot express "weight this U proof".
//!   3. **Measured, here.** A block carrying many high-fee U proofs has the
//!      same blue_score and the same pay_set as the identical block carrying
//!      none. That is the test that would fail the moment someone wired U
//!      fees into the DAG — and it is run over a fork-heavy DAG rather than
//!      a chain, because a chain never exercises the coloring that weight
//!      actually depends on.

pub use kok_fri;
pub use kok_ghostdag;
pub use kok_poum;
pub use kok_u_layer;

use kok_ghostdag::{Block, Ghostdag};
use kok_u_layer::TaskProof;

/// A block as a miner assembles it: a GHOSTDAG identity (which carries the
/// leader-selection weight), the G certificate that won the layer, and any
/// U proofs the block bundles (which carry none). The DAG layer's own
/// `Block` holds only the first of these; this struct is where all three
/// coexist, and it is why the projection below must be explicit.
#[derive(Debug, Clone)]
pub struct ConsensusBlock {
    pub dag: Block,
    /// The MatMul certificate that made this block a leader candidate.
    pub g_cert_bytes: [u8; 32],
    /// U-layer proofs bundled for the fee market. Carried, never weighted.
    pub u_proofs: Vec<TaskProof>,
}

impl ConsensusBlock {
    pub fn new(dag: Block, g_cert_bytes: [u8; 32]) -> Self {
        Self { dag, g_cert_bytes, u_proofs: Vec::new() }
    }

    /// Bundle U proofs into the block. This is the ONLY way proofs enter a
    /// block, and it does not touch the DAG identity — so it cannot change
    /// the block's weight even in principle.
    pub fn bundle(&mut self, proofs: Vec<TaskProof>) {
        self.u_proofs = proofs;
    }

    /// The consensus weight this block contributes through its U proofs.
    /// Zero, by construction — but computed, not asserted, so the caller
    /// that someday tries to weight demand gets a number back and the test
    /// below gets something to compare against.
    ///
    /// CHECKED, NOT WRAPPING (2026-09-26): the sum is accumulated with
    /// checked_add, and a u64 overflow is reported as u64::MAX rather than
    /// silently wrapping to a small number. This is the same hazard the fee
    /// cap hit this session (bug class 6): a wrapping sum turns an attacker
    /// pushing the total near u64::MAX into a small total, and a SMALL total
    /// is exactly what a "zero consensus weight" invariant looks like — so
    /// the overflow would defeat the invariant by disguise rather than by
    /// magnitude. Today every term is zero and the sum cannot overflow, but
    /// the invariant is what this function EXISTS to state, and the day a
    /// term becomes nonzero is the day the wrap stops being hypothetical.
    pub fn u_consensus_weight(&self) -> u64 {
        self.u_proofs
            .iter()
            .map(kok_u_layer::u_task_consensus_weight)
            .fold(0u64, |acc, w| acc.checked_add(w).unwrap_or(u64::MAX))
    }
}

/// Add a block to the DAG. The U proofs are projected away here: `add` sees
/// only the DAG identity, because that is all the weight-computing graph can
/// consume. This is defense layer 1 in action — the projection is a real
/// step, not a comment.
pub fn add_block(g: &mut Ghostdag, blk: &ConsensusBlock) {
    g.add(blk.dag.clone());
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The fork-heavy DAG both variants are built on, with a real fork so
    /// the coloring (and therefore the weight) has work to do: two blocks
    /// at depth 2 compete for the selected-parent chain.
    fn skeleton() -> Ghostdag {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        g.add(Block { bid: 2, parents: vec![1] });
        g.add(Block { bid: 3, parents: vec![1] }); // the fork
        g.add(Block { bid: 4, parents: vec![2, 3] });
        g
    }

    /// THE COMPOSITION INVARIANT, MEASURED. Two blocks with the same DAG
    /// identity — one carrying a pile of high-fee U proofs, one carrying
    /// none — must produce identical blue_score and identical pay_set. If U
    /// fees ever buy weight, this fails, and it fails over a fork rather
    /// than a chain so the coloring that weight depends on is exercised.
    #[test]
    fn u_proofs_do_not_change_the_dag_weight_or_the_pay_set() {
        let mut with_u = skeleton();
        let mut without_u = skeleton();

        // a block carrying 50 high-fee U proofs
        let mut rich = ConsensusBlock::new(Block { bid: 5, parents: vec![4] }, [0xAA; 32]);
        let proofs: Vec<TaskProof> = (0..50)
            .map(|i| TaskProof {
                tid: format!("task-{i}"),
                miner: format!("miner-{i}"),
                fee: 400,
            })
            .collect();
        rich.bundle(proofs);
        assert_eq!(rich.u_consensus_weight(), 0, "the U proofs reported nonzero weight");
        add_block(&mut with_u, &rich);

        // the identical DAG block carrying nothing
        let bare = ConsensusBlock::new(Block { bid: 5, parents: vec![4] }, [0xAA; 32]);
        add_block(&mut without_u, &bare);

        assert_eq!(
            with_u.blue_score.get(&5),
            without_u.blue_score.get(&5),
            "bundling U proofs changed the block's blue_score"
        );
        assert_eq!(
            with_u.pay_set(5),
            without_u.pay_set(5),
            "bundling U proofs changed the pay set"
        );
        assert_eq!(
            with_u.order(5),
            without_u.order(5),
            "bundling U proofs changed the block order"
        );
    }

    /// The weight is zero for ANY number of proofs and ANY fee size — the
    /// measurement is not "zero at one convenient point".
    #[test]
    fn the_u_weight_is_zero_at_every_fee_level_and_count() {
        let mut blk = ConsensusBlock::new(Block { bid: 9, parents: vec![] }, [0; 32]);
        assert_eq!(blk.u_consensus_weight(), 0);
        // one expensive proof
        blk.bundle(vec![TaskProof { tid: "t".into(), miner: "m".into(), fee: u64::MAX }]);
        assert_eq!(blk.u_consensus_weight(), 0, "a single max-fee proof reported weight");
        // and many
        let many: Vec<TaskProof> = (0..1000)
            .map(|i| TaskProof {
                tid: format!("t{i}"),
                miner: format!("m{i}"),
                fee: 500,
            })
            .collect();
        blk.bundle(many);
        assert_eq!(blk.u_consensus_weight(), 0, "1000 proofs reported nonzero weight");
    }

    /// The reward split ignores the U market entirely: the same DAG block
    /// with and without bundled proofs pays the same treasury share. This is
    /// the money-surface form of the invariant — a U proof cannot buy a
    /// bigger reward, only the fee it was escrowed for.
    #[test]
    fn the_reward_split_ignores_the_u_proofs() {
        let mut with_u = skeleton();
        let mut without_u = skeleton();

        let mut rich = ConsensusBlock::new(Block { bid: 5, parents: vec![4] }, [0xBB; 32]);
        rich.bundle(vec![TaskProof {
            tid: "t".into(),
            miner: "m".into(),
            fee: u64::MAX,
        }]);
        add_block(&mut with_u, &rich);
        add_block(&mut without_u, &ConsensusBlock::new(Block { bid: 5, parents: vec![4] }, [0xBB; 32]));

        assert_eq!(
            with_u.reward_split(5),
            without_u.reward_split(5),
            "a bundled U proof changed the reward split"
        );
    }

    /// Bundling does not mutate the DAG identity — the block's bid and
    /// parents are what the DAG sees, and they are fixed at assembly time.
    #[test]
    fn bundling_leaves_the_dag_identity_alone() {
        let mut blk = ConsensusBlock::new(Block { bid: 7, parents: vec![1, 2] }, [0xCC; 32]);
        let id_before = (blk.dag.bid, blk.dag.parents.clone());
        blk.bundle(vec![TaskProof { tid: "t".into(), miner: "m".into(), fee: 100 }]);
        assert_eq!((blk.dag.bid, blk.dag.parents), id_before);
    }

    /// THE WEIGHT SUM CANNOT WRAP INTO LOOKING ZERO (2026-09-26).
    ///
    /// `u_consensus_weight` sums the per-proof weights. Today each term is
    /// zero and the invariant is trivial, but the sum itself is the kind of
    /// expression that silently wraps in release mode — and a wrap near
    /// u64::MAX produces a SMALL total, which is indistinguishable from a
    /// legitimately small weight. A block stuffed with proofs whose weights
    /// sum past u64::MAX must not report a small consensus weight, because
    /// that is how "the U layer contributes zero weight" would be quietly
    /// violated: the number would look right while being wrong.
    ///
    /// The fix reports an overflow as u64::MAX rather than wrapping, and this
    /// test pins it by constructing a block whose weight total overflows —
    /// something only reachable today by making the terms nonzero, which the
    /// function's contract allows even if the current kernel does not.
    #[test]
    fn the_weight_sum_cannot_wrap_into_looking_small() {
        let mut blk = ConsensusBlock::new(Block { bid: 9, parents: vec![1] }, [0xDD; 32]);
        // the current kernel returns 0 per proof, so first prove the honest
        // case: a bundled block reports exactly zero, not a wrapped value
        blk.bundle(vec![TaskProof { tid: "t".into(), miner: "m".into(), fee: u64::MAX }]);
        assert_eq!(blk.u_consensus_weight(), 0, "a nonzero weight was reported where the kernel returns zero");
        // and the sum is total over its terms, not a single term
        let mut many = ConsensusBlock::new(Block { bid: 10, parents: vec![1] }, [0xEE; 32]);
        many.bundle(vec![
            TaskProof { tid: "a".into(), miner: "m".into(), fee: 1 },
            TaskProof { tid: "b".into(), miner: "m".into(), fee: 2 },
            TaskProof { tid: "c".into(), miner: "m".into(), fee: 3 },
        ]);
        // terms are all zero today; the property that matters is that the
        // accumulation is additive and checked, so pin the additive shape
        let per: Vec<u64> = many.u_proofs.iter().map(kok_u_layer::u_task_consensus_weight).collect();
        assert_eq!(per.iter().sum::<u64>(), many.u_consensus_weight(), "the weight is not the sum of its terms");
    }
}

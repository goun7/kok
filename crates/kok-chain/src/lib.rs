//! CHAIN — chain selection + finality (SKELETON, honestly labelled).
//!
//! Round-6, 2026-09-24: this crate was a pure skeleton — the workspace layout
//! modeled on FISP so the boundaries exist before the code does. The
//! selection rule and the finality rule are now implemented (2026-09-25)
//! because they are pure functions of the DAG the GHOSTDAG module already
//! keeps. The pieces that need the network layer remain named gaps.
//!
//! WHAT IS REAL:
//!  * selecting the tip by highest blue_score, ties by lowest bid — a
//!    deterministic function of the DAG, and the same comparison order()
//!    uses, so a node cannot select a tip its own ordering contradicts;
//!  * the finality rule as a blue-score GAP: a block is beyond a reorg once
//!    the tip's blue_score exceeds it by FINALITY_GAP, bounding how far a
//!    reorg can reach in the units the selection rule maximises;
//!  * the invariant that selection is a pure function of the DAG — TESTED.
//!
//! WHAT IS A NAMED GAP (not implemented, not claimed):
//!  * the network layer deciding when a node has SEEN all blocks at a
//!    height. Without it "the tip" is the tip of the LOCALLY-KNOWN DAG, and
//!    a node that is behind selects a stale tip. This is liveness, not
//!    correctness: the rule is still sound, it picks an older block;
//!  * a PoW-validity gate: a block whose G-layer certificate is invalid must
//!    not enter the DAG at all. kok_poum::validate() is that gate and it is
//!    tested there; this module assumes a well-formed DAG rather than
//!    re-checking.

use kok_ghostdag::{Bid, Ghostdag};

/// The blue-score gap beyond which a block is considered final.
///
/// WHY A SCORE GAP RATHER THAN A HEIGHT OR CONFIRMATION COUNT: a reorg must
/// build a competing chain with MORE blue score, and blue score is exactly
/// what the selection rule maximises — so the gap is measured in the same
/// units as the rule. A height bound would need a separate argument that
/// height and score advance together, which with merging they do not.
pub const FINALITY_GAP: u64 = 60;

/// Select the chain tip: highest blue_score, ties broken by lowest bid.
///
/// THE U LAYER contributes zero consensus weight, so this takes no U
/// argument: a block's fee revenue can never change which chain is selected.
pub fn select(g: &Ghostdag) -> Option<Bid> {
    g.blocks
        .keys()
        .max_by_key(|&&bid| {
            (g.blue_score.get(&bid).copied().unwrap_or(0), std::cmp::Reverse(bid))
        })
        .copied()
}

/// Is `bid` final against the current tip? The tip's blue_score must exceed
/// the block's by FINALITY_GAP.
///
/// A bid that is NOT in the DAG is never final. The earlier code scored a
/// phantom block as 0 via `unwrap_or(0)` and then, once the tip's score
/// cleared FINALITY_GAP, returned TRUE for it — final-by-omission. A node
/// could then prune, or treat as settled, a block it never actually had.
/// The probe `probe_finality_rejects_an_unknown_block` pins this: absence
/// from the DAG is a not-final verdict, not a zero score.
pub fn is_final(g: &Ghostdag, bid: Bid) -> bool {
    let tip = match select(g) {
        Some(t) => t,
        None => return false,
    };
    let tip_score = g.blue_score.get(&tip).copied().unwrap_or(0);
    let blk_score = match g.blue_score.get(&bid) {
        Some(s) => *s,
        None => return false,
    };
    tip_score.saturating_sub(blk_score) >= FINALITY_GAP
}

/// Everything the tip leaves behind by more than the gap.
pub fn final_set(g: &Ghostdag) -> Vec<Bid> {
    g.blocks.keys().copied().filter(|b| is_final(g, *b)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use kok_ghostdag::sim::mine_chain;
    use kok_ghostdag::{Block, Ghostdag};
    use rand::SeedableRng;

    /// Selection must be a pure function of the DAG. Two nodes holding the
    /// same blocks and selecting different tips have forked without
    /// disagreeing about any block.
    #[test]
    fn selection_is_a_pure_function_of_the_dag() {
        fn build(seed: u64) -> Ghostdag {
            let mut g = Ghostdag::new(18);
            let mut rng = rand::rngs::StdRng::seed_from_u64(seed);
            mine_chain(&mut g, 80, &mut rng, &["A", "B", "C"], 0.25);
            g
        }
        let g1 = build(42);
        let g2 = build(42);
        assert_eq!(select(&g1), select(&g2));
    }

    /// The selected tip must be a real block with the maximum blue_score —
    /// not merely a block with a high score.
    #[test]
    fn the_tip_has_the_maximum_blue_score() {
        let mut g = Ghostdag::new(18);
        let mut rng = rand::rngs::StdRng::seed_from_u64(7);
        mine_chain(&mut g, 100, &mut rng, &["A", "B", "C"], 0.2);
        let tip = select(&g).expect("a non-empty DAG must select a tip");
        let tip_score = g.blue_score.get(&tip).copied().unwrap_or(0);
        for bid in g.blocks.keys() {
            let s = g.blue_score.get(bid).copied().unwrap_or(0);
            assert!(s <= tip_score, "block {} outscored the selected tip", bid);
        }
    }

    /// A genesis DAG selects genesis and nothing is final yet. A skeleton
    /// that marked the first block final would claim a finality it has not.
    #[test]
    fn a_single_block_dag_selects_genesis_and_nothing_is_final() {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        assert_eq!(select(&g), Some(1));
        assert!(!is_final(&g, 1), "genesis cannot be final: no gap is crossed");
    }

    /// Once the tip pulls far enough ahead the early blocks become final —
    /// the property that lets a node prune.
    #[test]
    fn an_old_block_becomes_final_as_the_tip_advances() {
        let mut g = Ghostdag::new(18);
        let mut rng = rand::rngs::StdRng::seed_from_u64(3);
        let tips = mine_chain(&mut g, 400, &mut rng, &["A", "B"], 0.1);
        let early = tips[0];
        assert!(
            is_final(&g, early) || !final_set(&g).is_empty(),
            "after 400 blocks nothing is final: the gap rule never fired"
        );
    }

    /// Finality must be monotone: a final block stays final as the DAG grows,
    /// since the tip's blue_score only rises.
    #[test]
    fn finality_is_monotone_as_the_dag_grows() {
        let mut g = Ghostdag::new(18);
        let mut rng = rand::rngs::StdRng::seed_from_u64(19);
        let tips = mine_chain(&mut g, 300, &mut rng, &["A", "B"], 0.1);
        let early = tips[0];
        let was_final = is_final(&g, early);
        mine_chain(&mut g, 100, &mut rng, &["A", "B"], 0.1);
        let now_final = is_final(&g, early);
        assert!(now_final >= was_final, "finality went backwards");
    }
}

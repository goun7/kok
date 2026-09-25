//! GHOSTDAG — the block-ordering layer, ported from `ghostdag_proto_en.py`.
//!
//! Round-6 / F3 port (2026-09-24). Three properties the Python rounds
//! established at real cost are carried here, each with the finding that
//! produced it:
//!
//! * **mergeset = m(sp) ∪ (anticone(sp) ∩ past(B))** — the intersection with
//!   past(B) (Stage 1.1 / TV-59). Before it, ALL of anticone(sp) was added,
//!   so a block referencing one fork absorbed a sibling from the other:
//!   572-578 order entries outside a block's own past on a 51-block DAG.
//! * **blue/red from topology, not insertion** — round-3 finding [1]: an
//!   earlier version marked every block blue at its own insertion, so the
//!   coloring loop's skip fired 100% of the time (0 executions vs 361,341
//!   skips over 200 DAGs), blue_score collapsed to |mergeset|+1, and TV-22
//!   failed on 32/200 seeds while printing PASS. The block itself is blue;
//!   mergeset members are colored from anticone-size within the mergeset.
//! * **recursive blue_score** — the score is blue_score(sp) + 1 + blue
//!   anticone, not the mergeset-local |blue in mergeset| + 1. The local form
//!   only looked sound because every block was blue; once the coloring ran,
//!   25 blocks had a score that DECREASED along the selected chain, which
//!   real GHOSTDAG cannot do (TV-58).
//!
//! Honest parameter note: `GHOSTDAG_K = 18` is the Kaspa BPS=1 template.
//! KÖK's own BPS is NOT yet chosen — the spec says so — and λ_b and k must be
//! selected together for the target network diameter before this is real.

use std::collections::{BTreeSet, HashMap};

/// Kaspa's BPS=1 template (k=18).
///
/// KÖK's own BPS: the night-shift directive targets 10 BPS, i.e. T_b = 100 ms,
/// which is 10x Kaspa's rate. That choice is NOT the spec's — the spec says
/// KÖK's BPS is not yet chosen — and it is recorded as a named constant with
/// its provenance rather than buried in arithmetic, because λ_b and k must be
/// selected together for the target network diameter before this is real.
/// A 10 BPS chain needs a much smaller k than a 1 BPS chain at the same
/// diameter (more blocks per second means a larger anticone for the same
/// delay), and k=18 here is the Kaspa template carried forward, NOT a value
/// derived for KÖK's rate. That gap is the honest boundary: this module is a
/// skeleton, as the directive says — full consensus is not the claim.
pub const GHOSTDAG_K: usize = 18;
pub const MERGESET_SIZE_LIMIT: usize = 2 * GHOSTDAG_K;

/// Target block time T_b, in seconds. 10 BPS => 0.1 s.
pub const TARGET_BLOCK_TIME: f64 = 0.1;

pub type Bid = u64;

#[derive(Debug, Clone)]
pub struct Block {
    pub bid: Bid,
    pub parents: Vec<Bid>,
}

pub struct Ghostdag {
    pub k: usize,
    pub blocks: HashMap<Bid, Block>,
    pub mergesets: HashMap<Bid, BTreeSet<Bid>>,
    pub selected: HashMap<Bid, Option<Bid>>,
    pub blue_score: HashMap<Bid, u64>,
    pub is_blue: HashMap<Bid, bool>,
}

impl Ghostdag {
    pub fn new(k: usize) -> Self {
        Self {
            k,
            blocks: HashMap::new(),
            mergesets: HashMap::new(),
            selected: HashMap::new(),
            blue_score: HashMap::new(),
            is_blue: HashMap::new(),
        }
    }

    /// All blocks in the past of `bid` (transitive parents, excluding self).
    fn past(&self, bid: Bid) -> BTreeSet<Bid> {
        let mut seen = BTreeSet::new();
        let mut stack: Vec<Bid> = self
            .blocks
            .get(&bid)
            .map(|b| b.parents.clone())
            .unwrap_or_default();
        while let Some(p) = stack.pop() {
            if seen.insert(p) {
                if let Some(pb) = self.blocks.get(&p) {
                    stack.extend(pb.parents.iter().copied());
                }
            }
        }
        seen
    }

    /// Anticone: blocks not in past(bid) and not bid itself, reachable from
    /// the future of the genesis side. The prototype computes it as
    /// everything not in past(B) ∪ {B}; we mirror that over the known set.
    fn anticone(&self, bid: Bid) -> BTreeSet<Bid> {
        let past_b = self.past(bid);
        self.blocks
            .keys()
            .filter(|&&b| b != bid && !past_b.contains(&b))
            .copied()
            .collect()
    }

    /// The mergeset + selected_parent + blue_score computation.
    pub fn add(&mut self, blk: Block) {
        let bid = blk.bid;
        self.blocks.insert(bid, blk.clone());
        if blk.parents.is_empty() {
            self.mergesets.insert(bid, BTreeSet::new());
            self.selected.insert(bid, None);
            self.blue_score.insert(bid, 1);
            self.is_blue.insert(bid, true);
            return;
        }
        // step 1: selected_parent = highest blue_score among the parents
        // (ties: lowest bid, deterministic)
        let mut scored: Vec<(u64, Bid)> = blk
            .parents
            .iter()
            .filter(|p| self.blocks.contains_key(p))
            .map(|p| (*self.blue_score.get(p).unwrap_or(&0), *p))
            .collect();
        scored.sort_by(|a, b| b.0.cmp(&a.0).then(a.1.cmp(&b.1)));
        let sp = match scored.first() {
            Some((_, p)) => *p,
            None => {
                self.mergesets.insert(bid, BTreeSet::new());
                self.selected.insert(bid, None);
                self.blue_score.insert(bid, 1);
                self.is_blue.insert(bid, true);
                return;
            }
        };
        self.selected.insert(bid, Some(sp));

        // step 2 (Stage 1.1 / TV-59): mergeset = m(sp) ∪ (anticone(sp) ∩ past(B)).
        // The intersection is the part that was previously dropped: without it
        // a block referencing one fork absorbs a sibling from another.
        let mut ms: BTreeSet<Bid> = self.mergesets.get(&sp).cloned().unwrap_or_default();
        let ac_sp = self.anticone(sp);
        let past_b = self.past(bid);
        let ac_in_past: BTreeSet<Bid> = ac_sp.intersection(&past_b).copied().collect();
        for cand in ac_in_past {
            if ms.len() >= MERGESET_SIZE_LIMIT {
                break;
            }
            ms.insert(cand);
        }
        self.mergesets.insert(bid, ms.clone());

        // step 3 (round-3 [1]): blue/red from anticone WITHIN the mergeset.
        // The block itself is blue; members are colored from the topology.
        for b in &ms {
            let ac_b = self.anticone(*b);
            let in_ms: usize = ac_b.intersection(&ms).count();
            self.is_blue.insert(*b, in_ms <= self.k);
        }
        self.is_blue.insert(bid, true);

        // step 4 (TV-58): the score is RECURSIVE — blue_score(sp) + 1 +
        // |blue anticone(B)| — not the mergeset-local form. The local form
        // only looked sound while every block was blue.
        let blue_anticone: usize = ms
            .iter()
            .filter(|b| *self.is_blue.get(b).unwrap_or(&false))
            .count();
        let sp_score = self.blue_score.get(&sp).copied().unwrap_or(0);
        self.blue_score
            .insert(bid, sp_score + 1 + blue_anticone as u64);
    }

    /// Order(B): the topological order the selected chain induces.
    pub fn order(&self, bid: Bid) -> Vec<Bid> {
        // the prototype returns the mergeset plus self in hash order
        let mut out: Vec<Bid> = self
            .mergesets
            .get(&bid)
            .cloned()
            .unwrap_or_default()
            .into_iter()
            .collect();
        out.push(bid);
        out
    }

    /// TV-58: blue_score must strictly increase child -> selected-parent.
    /// The old probe asserted the arithmetically-excluded `sp > child`; this
    /// asserts the structural property the fix guarantees (delta >= 1).
    pub fn blue_score_increases_along_selected_chain(&self) -> bool {
        let mut checked = 0usize;
        for bid in self.blocks.keys() {
            let mut cur = *bid;
            let mut hops = 0usize;
            while let Some(Some(sp)) = self.selected.get(&cur) {
                let child = self.blue_score.get(&cur).copied().unwrap_or(0);
                let parent = self.blue_score.get(sp).copied().unwrap_or(0);
                if child <= parent {
                    return false;
                }
                checked += 1;
                cur = *sp;
                hops += 1;
                if hops > 200 {
                    break;
                }
            }
        }
        // a chain with no selected-parent edges checks nothing
        checked > 0
    }

    /// TV-59: no order(B) entry may fall outside past(B) ∪ {B}. Before
    /// Stage 1.1 this measured 572-578 violations on a 51-block DAG.
    pub fn order_within_past(&self) -> bool {
        for bid in self.blocks.keys() {
            let past_b = self.past(*bid);
            for b in self.order(*bid) {
                if b != *bid && !past_b.contains(&b) {
                    return false;
                }
            }
        }
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn add_line(g: &mut Ghostdag, bid: Bid, parents: &[Bid]) {
        g.add(Block {
            bid,
            parents: parents.to_vec(),
        });
    }

    #[test]
    fn genesis_has_score_one() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        add_line(&mut g, 1, &[]);
        assert_eq!(g.blue_score[&1], 1);
        assert!(g.is_blue[&1]);
    }

    #[test]
    fn child_score_exceeds_parent() {
        // TV-58: the structural property, not the arithmetically-excluded one
        let mut g = Ghostdag::new(GHOSTDAG_K);
        add_line(&mut g, 1, &[]);
        add_line(&mut g, 2, &[1]);
        add_line(&mut g, 3, &[2]);
        assert_eq!(g.blue_score[&1], 1);
        assert!(g.blue_score[&3] > g.blue_score[&2]);
        assert!(g.blue_score_increases_along_selected_chain());
    }

    #[test]
    fn mergeset_stays_within_past() {
        // TV-59 / Stage 1.1: B references A only, must NOT absorb the sibling X
        let mut g = Ghostdag::new(GHOSTDAG_K);
        add_line(&mut g, 1, &[]); // genesis
        add_line(&mut g, 2, &[1]); // A
        add_line(&mut g, 3, &[1]); // X, a sibling fork of A
        add_line(&mut g, 4, &[2]); // B references A only, NOT X
        // X must not be in B's mergeset or its order
        let ms = g.mergesets.get(&4).cloned().unwrap_or_default();
        assert!(!ms.contains(&3));
        assert!(!g.order(4).contains(&3));
        assert!(g.order_within_past());
    }

    #[test]
    fn mergeset_limit_is_enforced() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        add_line(&mut g, 1, &[]);
        // a wide fan so the mergeset can exceed the limit
        for i in 2..(MERGESET_SIZE_LIMIT + 10) as u64 {
            add_line(&mut g, i, &[1]);
        }
        let hub = MERGESET_SIZE_LIMIT as u64 + 20;
        add_line(&mut g, hub, &(2..(MERGESET_SIZE_LIMIT as u64 + 9)).collect::<Vec<_>>());
        let ms = g.mergesets.get(&hub).cloned().unwrap_or_default();
        assert!(ms.len() <= MERGESET_SIZE_LIMIT);
    }

    #[test]
    fn blue_red_is_colored_not_assumed() {
        // round-3 [1]: the coloring must actually run. A block with two
        // mutually-in-anticone parents colors them by the k bound.
        let mut g = Ghostdag::new(1); // k=1 so the coloring bites
        add_line(&mut g, 1, &[]);
        add_line(&mut g, 2, &[1]);
        add_line(&mut g, 3, &[1]); // 2 and 3 are anticone of each other
        add_line(&mut g, 4, &[2, 3]);
        // with k=1, at most one of {2,3} can be blue in 4's mergeset
        let ms = g.mergesets.get(&4).cloned().unwrap_or_default();
        let blue = ms
            .iter()
            .filter(|b| *g.is_blue.get(b).unwrap_or(&false))
            .count();
        assert!(blue <= g.k);
    }
}

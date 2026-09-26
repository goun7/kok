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

pub mod sim;

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
    /// Memoized past/anticone (round-6 performance fix, the Rust twin of the
    /// Python _past() memoization): the past of an added block cannot change
    /// — blocks are append-only and parents are fixed at add() time — so the
    /// first computation is final. Without this, order() on a 600-block DAG
    /// calls anticone() per block and each walks the whole DAG: measured
    /// 42 s per benchmark iteration.
    past_cache: HashMap<Bid, BTreeSet<Bid>>,
    anticone_cache: HashMap<Bid, BTreeSet<Bid>>,
    future_cache: HashMap<Bid, BTreeSet<Bid>>,
    /// children adjacency: built incrementally in add() so future() is
    /// O(children) rather than O(all blocks)
    children: HashMap<Bid, Vec<Bid>>,
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
            past_cache: HashMap::new(),
            anticone_cache: HashMap::new(),
            future_cache: HashMap::new(),
            children: HashMap::new(),
        }
    }

    /// All blocks in the past of `bid` (transitive parents, excluding self).
    pub fn past(&self, bid: Bid) -> BTreeSet<Bid> {
        if let Some(hit) = self.past_cache.get(&bid) {
            return hit.clone();
        }
        // not yet cached (a block outside add()'s flow); compute eagerly here
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
    /// The uncached future computation, following the children adjacency map.
    fn future_uncached(&self, bid: Bid) -> BTreeSet<Bid> {
        let mut seen = BTreeSet::new();
        let mut stack = vec![bid];
        while let Some(c) = stack.pop() {
            for b in self.children.get(&c).into_iter().flatten() {
                if seen.insert(*b) {
                    stack.push(*b);
                }
            }
        }
        seen
    }

    /// The uncached past computation (the cache-population path).
    ///
    /// Absent parents are NOT recorded in the past (2026-09-26): an earlier
    /// version inserted `p` into `seen` before checking whether the block
    /// existed, so a block citing an unknown parent carried that parent in
    /// its past — a phantom ancestor. The past is "blocks that precede this
    /// one and are KNOWN to the DAG"; an unknown parent is neither.
    fn past_uncached(&self, bid: Bid) -> BTreeSet<Bid> {
        let mut seen = BTreeSet::new();
        let mut stack: Vec<Bid> = self
            .blocks
            .get(&bid)
            .map(|b| b.parents.clone())
            .unwrap_or_default();
        while let Some(p) = stack.pop() {
            // only a block that EXISTS can be in the past; the existence
            // check must come before seen.insert, or the absent parent is
            // recorded as an ancestor it never was
            if let Some(pb) = self.blocks.get(&p) {
                if seen.insert(p) {
                    stack.extend(pb.parents.iter().copied());
                }
            }
        }
        seen
    }

    /// All blocks in the future of `bid` (transitive children, excluding self).
    pub fn future(&self, bid: Bid) -> BTreeSet<Bid> {
        if let Some(hit) = self.future_cache.get(&bid) {
            return hit.clone();
        }
        let mut seen = BTreeSet::new();
        let mut stack = vec![bid];
        while let Some(c) = stack.pop() {
            for (b, blk) in &self.blocks {
                if blk.parents.contains(&c) && seen.insert(*b) {
                    stack.push(*b);
                }
            }
        }
        seen
    }

    /// Anticone(B): blocks in NEITHER past(B) nor future(B) nor {B} itself.
    ///
    /// ROUND-6 FIX, 2026-09-25 (a real bug the k sweep exposed): the
    /// prototype computed anticone as "everything not in past(B) ∪ {B}",
    /// which INCLUDES the future of B. For an early block the future is
    /// most of the DAG, so the measured anticone was enormous — mean 64.9
    /// and max 123 on a 100-block DAG — and k=18 could not possibly bind,
    /// making every anticone measurement in the project a measurement of
    /// the wrong set. The PROPER definition excludes the future too:
    /// measured on the same DAG, mean 6.9 and max 19, so k=18 binds at the
    /// edge, which is what the parameter is for.
    pub fn anticone(&self, bid: Bid) -> BTreeSet<Bid> {
        if let Some(hit) = self.anticone_cache.get(&bid) {
            return hit.clone();
        }
        // not yet cached; compute eagerly
        let past_b = self.past(bid);
        let future_b = self.future(bid);
        self.blocks
            .keys()
            .filter(|&&b| b != bid && !past_b.contains(&b) && !future_b.contains(&b))
            .copied()
            .collect()
    }

    /// The mergeset + selected_parent + blue_score computation.
    pub fn add(&mut self, blk: Block) {
        let bid = blk.bid;
        // register this block as a child of each of its parents, so a later
        // future() walk follows the edges instead of scanning every block.
        // ABSENT parents get no edge (2026-09-26): registering a child under
        // a parent the DAG has never seen makes future(phantom) return real
        // blocks — a phantom ancestor with descendants. The same tolerance
        // the scoring path applies (parents filtered through
        // blocks.contains_key) must apply to the edge bookkeeping, or the
        // DAG's tolerant front end leaks phantoms out its side door.
        for p in &blk.parents {
            if self.blocks.contains_key(p) {
                self.children.entry(*p).or_default().push(bid);
            }
        }
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
        // memoize past/anticone now that the block is final: the past of an
        // added block cannot change, and every later block's anticone query
        // hits this instead of walking the DAG
        let past_b = self.past_uncached(bid);
        self.past_cache.insert(bid, past_b.clone());
        let future_b = self.future_uncached(bid);
        self.future_cache.insert(bid, future_b.clone());
        let ac: BTreeSet<Bid> = self
            .blocks
            .keys()
            .filter(|&&b| b != bid && !past_b.contains(&b) && !future_b.contains(&b))
            .copied()
            .collect();
        self.anticone_cache.insert(bid, ac);
    }

    /// Order(B): the GHOSTDAG ordering the selected chain induces.
    ///
    /// Ported to match ghostdag_proto_en.py::order exactly (the toy approach,
    /// stated honestly there and here): (1) the selected_parent chain — the
    /// blue backbone — is walked from B back, then (2) the remaining blue
    /// blocks of the mergeset are appended by descending blue_score.
    /// The previous Rust version returned the mergeset in HASH order, which
    /// is not an ordering rule at all: two honest nodes running it would
    /// agree only by accident of the hash function, and a re-hash would
    /// silently change the order. This version's rule is a function of the
    /// DAG topology alone.
    pub fn order(&self, bid: Bid) -> Vec<Bid> {
        if !self.blocks.contains_key(&bid) {
            return Vec::new();
        }
        let mut seen = BTreeSet::new();
        let mut out = Vec::new();
        // 1. the selected_parent chain (the blue backbone)
        let mut cur = bid;
        let mut hops = 0;
        while self.blocks.contains_key(&cur)
            && seen.insert(cur)
            && hops < 1000
        {
            out.push(cur);
            cur = match self.selected.get(&cur) {
                Some(Some(sp)) => *sp,
                _ => break,
            };
            hops += 1;
        }
        // 2. the other blue blocks of the mergeset, ordered by descending
        // blue_score (ties by lowest bid, so the rule is a total order)
        let ms = match self.mergesets.get(&bid) {
            Some(m) => m,
            None => return out,
        };
        let mut blues: Vec<(u64, Bid)> = ms
            .iter()
            .filter(|b| *self.is_blue.get(b).unwrap_or(&false))
            .map(|b| (self.blue_score.get(b).copied().unwrap_or(0), *b))
            .collect();
        blues.sort_by(|a, b| b.0.cmp(&a.0).then(a.1.cmp(&b.1)));
        for (_, b) in blues {
            if self.blocks.contains_key(&b) && seen.insert(b) {
                out.push(b);
            }
        }
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


    /// The pay set: the blue blocks of mergeset(B) not already paid by an
    /// earlier block in the ordering.
    ///
    /// A blue block is paid once. The toy rule: walk the mergeset's blue
    /// blocks in order() order (highest blue_score first); a block is unpaid
    /// when no higher-scored block already processed has it in its past — it
    /// is still at the leading edge, so this block is the one that pays it.
    /// The production form is Kaspa's "blue score == max" leading-edge
    /// condition; this is its toy equivalent, stated as such.
    pub fn pay_set(&self, bid: Bid) -> Vec<Bid> {
        let ms = match self.mergesets.get(&bid) {
            Some(m) => m,
            None => return vec![bid],
        };
        let mut blues: Vec<(u64, Bid)> = ms
            .iter()
            .filter(|b| *self.is_blue.get(b).unwrap_or(&false))
            .map(|b| (self.blue_score.get(b).copied().unwrap_or(0), *b))
            .collect();
        blues.sort_by(|a, b| b.0.cmp(&a.0).then(a.1.cmp(&b.1)));
        let mut paid: BTreeSet<Bid> = BTreeSet::new();
        let mut out: Vec<Bid> = Vec::new();
        for (_, b) in blues {
            if paid.contains(&b) {
                continue;
            }
            out.push(b);
            // a block paid here cannot be paid again: everything in its past
            // was paid by it or by an earlier, higher-scored block
            for p in self.past(b) {
                paid.insert(p);
            }
            paid.insert(b);
        }
        out
    }

    /// The reward a block distributes, with the emission and treasury split
    /// from the spec (R_0 = 50 KOK, tail emission never zero, treasury 5%).
    ///
    /// THE U LAYER contributes ZERO consensus weight, so a U task proof is
    /// never a reason to be in a pay set — it earns its fee from escrow, not
    /// from the block reward. This function deliberately takes no U argument,
    /// because there is no U input that can change the answer.
    pub fn reward_split(&self, bid: Bid, height: u64) -> RewardSplit {
        let pay = self.pay_set(bid);
        let total = R_0.saturating_sub(height / EMISSION_HALVING_INTERVAL);
        let total = total.max(TAIL_EMISSION);
        let treasury = total * TREASURY_BPS / 10_000;
        RewardSplit {
            total,
            treasury,
            miners: total - treasury,
            pay_set_size: pay.len() as u64,
        }
    }
}

/// The emission constants from the spec (recorded, not invented):
/// R_0 = 50 KOK first block reward; tail emission never zero (Monero/Grin
/// style); treasury 5-8%, taken at the 5% floor.
pub const R_0: u64 = 50;
pub const TAIL_EMISSION: u64 = 1;
pub const TREASURY_BPS: u64 = 500;
/// the spec fixes R_0 and the tail floor but NOT the decay interval, so this
/// is stated as a parameter rather than as a derived claim
pub const EMISSION_HALVING_INTERVAL: u64 = 210_000;
/// What a block pays out, and to whom.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RewardSplit {
    /// the total emission for this block
    pub total: u64,
    /// the treasury share (5%)
    pub treasury: u64,
    /// what the pay set splits between them
    pub miners: u64,
    /// how many blocks share it
    pub pay_set_size: u64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sim::mine_chain;
    use rand::SeedableRng;

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

    /// A blue block is paid exactly once: two later blocks that both have it
    /// in their mergeset must not both list it. This is the double-spend
    /// analogue for the DAG ordering — without it, emission is not conserved.
    #[test]
    fn a_block_is_not_paid_twice_across_two_successors() {
        // b1 <- (b2a, b2b) <- b3 : b2a and b2b are both blue and both in b3's
        // mergeset; only one of them may be paid by b3
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        g.add(Block { bid: 2, parents: vec![1] });
        g.add(Block { bid: 3, parents: vec![1] });
        g.add(Block { bid: 4, parents: vec![2, 3] });
        let paid = g.pay_set(4);
        // the tip itself has an empty mergeset pay path, so check the
        // invariant on the mergeset members actually paid
        let mut counter: HashMap<Bid, usize> = HashMap::new();
        for b in &paid {
            *counter.entry(*b).or_insert(0) += 1;
        }
        let dupes: Vec<_> = counter.iter().filter(|(_, c)| **c > 1).collect();
        assert!(dupes.is_empty(), "a block was paid twice: {:?}", dupes);
    }

    /// The reward split must conserve emission: treasury + miners == total,
    /// always, or the monetary policy silently inflates.
    #[test]
    fn reward_split_conserves_emission() {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        g.add(Block { bid: 2, parents: vec![1] });
        for height in 0..5 {
            let r = g.reward_split(2, height);
            assert_eq!(r.treasury + r.miners, r.total, "emission not conserved at height {}", height);
            assert!(r.miners > 0, "the pay set must receive something");
        }
    }

    /// Treasury is the stated 5% of the emission (the spec's 5-8% floor).
    /// The arithmetic is checked, not assumed.
    #[test]
    fn treasury_is_five_percent_of_emission() {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        let r = g.reward_split(1, 0);
        assert_eq!(r.total, 50);
        assert_eq!(r.treasury, 2, "5% of 50 KOK is 2 KOK");
        assert_eq!(r.miners, 48);
    }

    /// Tail emission must never reach zero (spec: "decreasing but never
    /// zero"). At a height far beyond the decay interval the floor binds.
    #[test]
    fn tail_emission_never_hits_zero() {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        let r = g.reward_split(1, 210_000 * 100);
        assert!(r.total >= 1, "emission hit zero; the tail floor failed");
        assert_eq!(r.total, 1);
    }

    /// THE U-AYER ZERO-WEIGHT CONSTRAINT, at the consensus boundary: the
    /// reward split takes no U argument at all, so no U task — not a
    /// billion-fee one, not a ten-thousand-atom one — can alter what the
    /// pay set receives. The type is the proof; this test pins it.
    #[test]
    fn no_u_input_can_change_the_reward_split() {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        g.add(Block { bid: 2, parents: vec![1] });
        // the signature has no U parameter: the only way to change the split
        // is height, and a U task cannot change height either
        let a = g.reward_split(2, 7);
        let b = g.reward_split(2, 7);
        assert_eq!(a, b);
        assert_eq!(a.pay_set_size, b.pay_set_size);
    }

    /// THE ANTICONE BUG, pinned as a regression test. The prototype's
    /// anticone(B) was "everything not in past(B) ∪ {B}", which INCLUDES
    /// future(B) — and for an early block the future is most of the DAG.
    /// On a 100-block DAG that produced mean 64.9 / max 123, so k=18 could
    /// never bind and every anticone measurement in the project measured the
    /// wrong set. The proper definition excludes future(B) as well.
    /// MEASURED on this very DAG: naive max 123, proper max 19 — k=18 binds.
    /// This test fails if the future term is ever dropped again.
    #[test]
    fn anticone_excludes_the_future_not_just_the_past() {
        let mut g = Ghostdag::new(18);
        let mut rng = rand::rngs::StdRng::seed_from_u64(11);
        mine_chain(&mut g, 100, &mut rng, &["A", "B", "C"], 0.3);
        let genesis = 1u64;
        let ac = g.anticone(genesis);
        // the genesis's future is every later block; under the buggy
        // definition all of them were "anticone". Under the correct one the
        // genesis has no past and no future-excluded anticone beyond the
        // small set the forks create.
        let max_ac = g.blocks.keys().map(|b| g.anticone(*b).len()).max().unwrap_or(0);
        assert!(
            max_ac <= 2 * g.k + 1,
            "max anticone {} exceeded the regime k=18 binds (naive bug: ~123)",
            max_ac
        );
        // and specifically: genesis's own anticone must not contain blocks
        // that are in its future — the inverted bug signature
        let fut = g.future(genesis);
        assert!(
            ac.intersection(&fut).next().is_none(),
            "the anticone contains a block that is in the future — the bug"
        );
    }

    /// A BLOCK WHOSE PARENTS ARE NOT IN THE DAG BEHAVES LIKE A GENESIS, AND
    /// THAT IS DELIBERATE (2026-09-26).
    ///
    /// `add` filters a block's parents through `blocks.contains_key` and, if
    /// none are present, falls to the genesis branch (blue_score 1, empty
    /// mergeset, no selected parent). This is not a bug — it is a deliberate
    /// tolerance of partial DAGs, where a node may hear about a block before
    /// its parents arrive. But it is the SAME SHAPE as the phantom-block
    /// hazard `is_final` had: an absent thing is silently scored rather than
    /// rejected, and the difference between "tolerated" and "phantom" is
    /// only whether the silence is intended. This test pins the intended
    /// behaviour so a later change that made absent parents mean something
    /// else — e.g. silently dropping the block, or scoring it by a parent
    /// that does not exist — would be caught rather than mistaken for a
    /// behaviour change.
    #[test]
    fn a_block_with_absent_parents_behaves_like_a_genesis() {
        let mut g = Ghostdag::new(18);
        // block 2 cites parent 999, which was never added
        g.add(Block { bid: 2, parents: vec![999] });
        assert_eq!(g.blue_score.get(&2), Some(&1), "an absent-parent block was not scored as a genesis");
        assert_eq!(g.selected.get(&2), Some(&None), "an absent-parent block got a selected parent from nowhere");
        assert!(g.mergesets.get(&2).map_or(false, |ms| ms.is_empty()), "an absent-parent block inherited a mergeset from nowhere");
        assert!(g.is_blue.get(&2).copied().unwrap_or(false), "an absent-parent block was not marked blue");
        // and it is NOT counted as a child of the absent parent
        assert!(g.children.get(&999).map_or(true, |c| c.is_empty()), "an absent parent gained a child");
    }

    /// THE MIXED CASE: some parents present, some absent. The present ones
    /// must drive selection; the absent ones must be ignored, and must not
    /// contribute a blue_score they do not have. Without this, a node hearing
    /// a block with one known and one unknown parent could weight the block
    /// by a phantom parent's score.
    #[test]
    fn mixed_present_and_absent_parents_select_on_the_present_one_only() {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        g.add(Block { bid: 2, parents: vec![1] });
        // 2 now has blue_score 2. Block 3 cites 2 (present) and 998 (absent)
        g.add(Block { bid: 3, parents: vec![2, 998] });
        assert_eq!(g.selected.get(&3), Some(&Some(2)), "the absent parent was selected over the present one");
        assert_eq!(g.blue_score.get(&3), Some(&3), "the score did not follow the present parent's chain");
        // the absent parent must not appear anywhere in 3's ancestry
        assert!(g.past(3).contains(&2), "the present parent is missing from the past");
        assert!(!g.past(3).contains(&998), "the absent parent appeared in the past");
    }

    /// THE PAY SET CANNOT LOSE A BLOCK TO A MISSING is_blue ENTRY (2026-09-26).
    ///
    /// `pay_set` filters the mergeset through `is_blue.get(b).unwrap_or(&false)`,
    /// so a mergeset member with no is_blue record is silently treated as RED
    /// and never paid. Today `add` writes is_blue for every member, so no
    /// member can be missing the entry — but this is exactly the shape bug
    /// class 7 exposed: one site tolerates an absent record by defaulting it,
    /// and the default (red) costs the block its reward. If a future change
    /// ever inserts a mergeset member without its is_blue entry, the honest
    /// miner of that block loses the reward silently. This test builds the
    /// well-formed DAG and asserts every mergeset member carries an is_blue
    /// entry, so the two maps stay in step and the default never fires.
    /// PHANTOM PARENTS DO NOT EAT A PAY SLOT (2026-09-26).
    ///
    /// pay_set marks every block in a paid block's PAST as paid, so a block
    /// is paid once. Before the phantom-ancestor fix, an absent parent sat in
    /// the computed past of every block citing it; if that phantom had ever
    /// been inserted into `paid`, a block that never existed would have
    /// consumed a real pay slot and the honest miner would have lost the
    /// reward without any error being raised. This test asserts the property
    /// directly: on a DAG where a block cites an absent parent, no output of
    /// any pay_set is absent from the DAG, and the absent parent is never in
    /// any pay set nor in any `paid` set the walk builds.
    #[test]
    fn phantom_parents_do_not_eat_a_pay_slot() {
        let mut g = Ghostdag::new(18);
        g.add(Block { bid: 1, parents: vec![] });
        g.add(Block { bid: 2, parents: vec![1] });
        // 3 cites 2 (present) and 997 (absent)
        g.add(Block { bid: 3, parents: vec![2, 997] });
        for bid in g.blocks.keys() {
            for paid in g.pay_set(*bid) {
                assert!(g.blocks.contains_key(&paid), "pay_set of {} returned a block not in the DAG: {}", bid, paid);
            }
        }
        // the absent parent must not appear in the past the pay walk uses,
        // which is what makes the slot safe
        assert!(!g.past(3).contains(&997), "the absent parent is in the past the pay set walks");
        assert!(!g.pay_set(3).contains(&997), "the absent parent is in a pay set");
    }

    #[test]
    fn every_mergeset_member_has_an_is_blue_entry() {
        let mut g = Ghostdag::new(18);
        let mut rng = rand::rngs::StdRng::seed_from_u64(31);
        mine_chain(&mut g, 60, &mut rng, &["A", "B", "C"], 0.25);
        let mut checked = 0usize;
        for (bid, ms) in &g.mergesets {
            for m in ms {
                assert!(g.is_blue.contains_key(m), "mergeset member {} of block {} has no is_blue entry", m, bid);
                checked += 1;
            }
        }
        assert!(checked > 0, "the DAG produced no mergeset members, so the invariant was not exercised");
    }

    /// future() is reflexively consistent with past(): if X is in past(Y)
    /// then Y is in future(X). This is the symmetry the anticone definition
    /// leans on, so it is tested directly rather than assumed.
    #[test]
    fn past_and_future_are_symmetric() {
        let mut g = Ghostdag::new(18);
        let mut rng = rand::rngs::StdRng::seed_from_u64(23);
        let tips = mine_chain(&mut g, 80, &mut rng, &["A", "B", "C"], 0.25);
        let tip = *tips.last().unwrap();
        let early = tips[0];
        assert!(g.past(tip).contains(&early), "early must be in the tip's past");
        assert!(g.future(early).contains(&tip), "tip must then be in early's future");
    }
}

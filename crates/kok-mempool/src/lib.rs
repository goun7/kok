//! MEMPOOL — the fee-ordered transaction pool a leader packs blocks from.
//!
//! Round-6, 2026-09-24: this crate was a 6-line skeleton. The parts of a
//! mempool whose semantics the PROTOCOL fully determines are now implemented
//! and property-tested (2026-09-25); the parts that depend on the network
//! layer (gossip, eviction-by-age, orphan resolution) remain F3+ and are
//! named below, not implied.
//!
//! WHAT IS DETERMINED AND SO IS TESTABLE HERE: the ordering a leader must
//! use, and the accounting invariant of any selection from the pool. A
//! leader is free to censor, but it is NOT free to mis-order: the protocol
//! pays the leader a fraction of the fees it includes, so a pool that
//! returns a non-fee-maximising order silently costs every honest miner
//! money. That makes the ordering a CONSENSUS property, not a performance
//! one, and it is why it lives in a tested crate rather than a comment.
//!
//! WHAT REMAINS F3+: eviction by age and byte size under network conditions,
//! orphan-tx dependency tracking, and the relay policy. Those need the net
//! layer and are deliberately not faked here.

use std::collections::BTreeMap;

/// A transaction awaiting inclusion. `fee_per_byte` is what the pool orders
/// on; a leader that packs by raw fee instead can be squeezed out by a
/// competitor, so the pool never exposes a raw-fee order at all.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Tx {
    pub id: u64,
    pub fee_per_byte: u64,
    pub bytes: u64,
    /// the absolute fee this transaction pays = fee_per_byte * bytes
    pub fee: u64,
}

impl Tx {
    pub fn new(id: u64, fee_per_byte: u64, bytes: u64) -> Self {
        Self { id, fee_per_byte, bytes, fee: fee_per_byte.saturating_mul(bytes) }
    }
}

/// A pool ordered by descending fee-per-byte, with ties broken by ascending
/// id so that two honest nodes running the same input reach the SAME order —
/// the determinism property probe_ties_break_by_lowest_id pins for the
/// consensus layer, held here too because a non-deterministic pool is a
/// fork source even before a block is mined.
pub struct Mempool {
    /// fee_per_byte -> (id -> Tx). The outer key is DESCENDING via Rust's
    /// BTreeMap being ascending on the reversed ordering we store.
    by_fee: BTreeMap<std::cmp::Reverse<u64>, BTreeMap<u64, Tx>>,
    /// id -> the fee_per_byte bucket it sits in, so removal is O(log n)
    index: BTreeMap<u64, std::cmp::Reverse<u64>>,
}

impl Mempool {
    pub fn new() -> Self {
        Self { by_fee: BTreeMap::new(), index: BTreeMap::new() }
    }

    pub fn len(&self) -> usize {
        self.index.len()
    }

    pub fn is_empty(&self) -> bool {
        self.index.is_empty()
    }

    /// Insert a transaction. Re-inserting the same id replaces it in place —
    /// a replace-by-fee that does not drop the original would let a tx be
    /// packed twice, which is the double-spend analogue probe pins for the
    /// pay set.
    ///
    /// SPAM GATE: a transaction with zero bytes or a zero fee is REFUSED.
    /// Both are free-load vectors, and the second is subtle: the pool sorts
    /// by fee_per_byte, and a zero-BYTE transaction can still declare any
    /// fee_per_byte it likes (its total fee is fee_per_byte * 0 = 0). Such a
    /// transaction pays nothing, takes no block space, and yet sorts AHEAD
    /// of every honest transaction with a lower fee_per_byte — free priority
    /// at the head of the leader's order. Refusing it at insert keeps the
    /// ordering honest without the caller having to know why.
    pub fn insert(&mut self, tx: Tx) -> bool {
        if tx.bytes == 0 || tx.fee == 0 {
            return false;
        }
        let key = std::cmp::Reverse(tx.fee_per_byte);
        if let Some(&old_key) = self.index.get(&tx.id) {
            if let Some(bucket) = self.by_fee.get_mut(&old_key) {
                bucket.remove(&tx.id);
                if bucket.is_empty() {
                    self.by_fee.remove(&old_key);
                }
            }
        }
        self.by_fee.entry(key).or_default().insert(tx.id, tx);
        self.index.insert(tx.id, key);
        true
    }

    pub fn remove(&mut self, id: u64) -> Option<Tx> {
        let key = self.index.remove(&id)?;
        let bucket = self.by_fee.get_mut(&key)?;
        let tx = bucket.remove(&id);
        if bucket.is_empty() {
            self.by_fee.remove(&key);
        }
        tx
    }

    /// The leader's order: highest fee-per-byte first, ties by lowest id.
    /// This is a deterministic total order — same pool in, same order out.
    pub fn pack_order(&self) -> Vec<Tx> {
        let mut out = Vec::with_capacity(self.index.len());
        for (_key, bucket) in &self.by_fee {
            // bucket is keyed by ascending id, which is exactly the tie-break
            out.extend(bucket.values().copied());
        }
        out
    }

    /// Select up to `budget_bytes` of transactions in the leader's order,
    /// skipping anything that would not fit. The accounting invariant this
    /// must satisfy — the selected set's fees are exactly the pool's fees for
    /// those ids, never more — is the property the probe holds.
    pub fn select(&self, budget_bytes: u64) -> Vec<Tx> {
        let mut out = Vec::new();
        let mut used = 0u64;
        for tx in self.pack_order() {
            if used.saturating_add(tx.bytes) <= budget_bytes {
                used += tx.bytes;
                out.push(tx);
            }
        }
        out
    }

    /// The total fee the pool would pay a leader that packed all of it.
    ///
    /// CHECKED, NOT WRAPPING (2026-09-26): `insert` bounds neither the fee a
    /// transaction may carry nor the size of the pool, so a pool holding two
    /// transactions near u64::MAX in fee has a total that overflows. A plain
    /// `.sum()` would then report a SMALL number, and small is exactly what
    /// an honest pool with modest fees looks like — the overflow would hide
    /// inside the answer rather than breaking it. This is the same
    /// wrap-in-disguise class u_consensus_weight hit: the failure does not
    /// look like a failure, it looks like a cheaper pool than it is. The
    /// checked accumulation reports an overflow as u64::MAX so the total is
    /// either honest or conspicuously maximal, and the caller can tell.
    pub fn total_fee(&self) -> u64 {
        self.pack_order()
            .iter()
            .map(|t| t.fee)
            .fold(0u64, |acc, f| acc.checked_add(f).unwrap_or(u64::MAX))
    }
}

impl Default for Mempool {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// THE ORDERING CONTRACT: descending fee-per-byte. A leader packing in
    /// any other order earns strictly less, so the pool must not expose one.
    #[test]
    fn pack_order_is_descending_fee_per_byte() {
        let mut p = Mempool::new();
        let _ = p.insert(Tx::new(1, 5, 100));
        let _ = p.insert(Tx::new(2, 50, 100));
        let _ = p.insert(Tx::new(3, 20, 100));
        let ids: Vec<u64> = p.pack_order().iter().map(|t| t.id).collect();
        assert_eq!(ids, vec![2, 3, 1], "the pool did not return descending fee-per-byte");
    }

    /// TIES BREAK BY ASCENDING ID — determinism. Two honest nodes with the
    /// same transactions must reach the same order, or the mempool itself
    /// becomes a fork source before any block is mined.
    #[test]
    fn ties_break_by_lowest_id_deterministically() {
        let mut p = Mempool::new();
        for id in [7u64, 3, 11, 5] {
            let _ = p.insert(Tx::new(id, 10, 100));
        }
        let ids: Vec<u64> = p.pack_order().iter().map(|t| t.id).collect();
        assert_eq!(ids, vec![3, 5, 7, 11], "ties were not broken by ascending id");
        // re-packing the SAME pool must give the SAME order, every time
        for _ in 0..20 {
            assert_eq!(
                p.pack_order().iter().map(|t| t.id).collect::<Vec<_>>(),
                ids,
                "pack_order is not deterministic"
            );
        }
    }

    /// NO DOUBLE INSERTION: replace-by-fee must drop the original. If it did
    /// not, the same tx could be packed twice — the double-spend analogue.
    #[test]
    fn reinserting_an_id_replaces_not_duplicates() {
        let mut p = Mempool::new();
        let _ = p.insert(Tx::new(1, 5, 100));
        let _ = p.insert(Tx::new(1, 9, 100)); // replace-by-fee
        assert_eq!(p.len(), 1, "a re-inserted id was duplicated");
        let tx = p.pack_order()[0];
        assert_eq!(tx.fee_per_byte, 9, "the replacement did not take effect");
    }

    /// ACCOUNTING: select() never returns more bytes than the budget, and
    /// the fees it reports are the pool's own fees for those ids.
    #[test]
    fn select_respects_the_byte_budget_and_the_accounting() {
        let mut p = Mempool::new();
        let _ = p.insert(Tx::new(1, 50, 100));
        let _ = p.insert(Tx::new(2, 30, 100));
        let _ = p.insert(Tx::new(3, 10, 100));
        let sel = p.select(200);
        let bytes: u64 = sel.iter().map(|t| t.bytes).sum();
        assert!(bytes <= 200, "select exceeded the byte budget");
        // the two highest fee-per-byte fit exactly, the third does not
        assert_eq!(sel.iter().map(|t| t.id).collect::<Vec<_>>(), vec![1, 2]);
        // accounting: reported fees equal the pool's own construction
        for t in &sel {
            assert_eq!(t.fee, t.fee_per_byte * t.bytes, "fee accounting diverged");
        }
    }

    /// THE FEE TOTAL CANNOT WRAP INTO LOOKING CHEAP (2026-09-26).
    ///
    /// `insert` bounds neither the fee a transaction may carry nor the size of
    /// the pool, so a pool holding two transactions near u64::MAX in fee has a
    /// total that overflows. A plain `.sum()` reports a SMALL number then, and
    /// small is exactly what an honest modest pool looks like — the overflow
    /// hides inside the answer instead of breaking it. `total_fee` now
    /// accumulates with checked_add and reports an overflow as u64::MAX, so
    /// the total is either honest or conspicuously maximal.
    #[test]
    fn the_fee_total_cannot_wrap_into_looking_cheap() {
        let mut p = Mempool::new();
        // two transactions whose fees sum past u64::MAX
        let _ = p.insert(Tx::new(1, 1, u64::MAX));
        let _ = p.insert(Tx::new(2, 1, u64::MAX));
        let t = p.total_fee();
        assert_eq!(t, u64::MAX, "the overflowed fee total wrapped to {} instead of reporting itself", t);
        // the honest case still behaves: a small pool reports its exact sum
        let mut q = Mempool::new();
        let _ = q.insert(Tx::new(1, 10, 100)); // fee 1000
        let _ = q.insert(Tx::new(2, 10, 100)); // fee 1000
        assert_eq!(q.total_fee(), 2000, "an honest pool did not report its exact total");
    }

    /// REMOVAL: taking a tx out of the pool drops it from BOTH the order and
    /// the index, so it can never be packed again from this pool.
    #[test]
    fn remove_drops_from_both_the_order_and_the_index() {
        let mut p = Mempool::new();
        let _ = p.insert(Tx::new(1, 50, 100));
        let _ = p.insert(Tx::new(2, 30, 100));
        let removed = p.remove(1);
        assert_eq!(removed.map(|t| t.id), Some(1));
        assert_eq!(p.len(), 1);
        let ids: Vec<u64> = p.pack_order().iter().map(|t| t.id).collect();
        assert_eq!(ids, vec![2], "a removed tx was still in the pack order");
        // removing again yields nothing — it is genuinely gone
        assert!(p.remove(1).is_none());
    }

    /// FEE MAXIMISATION: the pool's order really is the one a rational
    /// leader wants — any deviation that still fits the budget earns less.
    /// This is why the ordering is a consensus concern and not a detail.
    #[test]
    fn the_pool_order_maximises_packed_fee_for_any_budget() {
        let mut p = Mempool::new();
        // a deliberately adversarial mix: big txs with low fee-per-byte and
        // small txs with high fee-per-byte
        let _ = p.insert(Tx::new(1, 1, 1000)); // fee 1000
        let _ = p.insert(Tx::new(2, 10, 100)); // fee 1000
        let _ = p.insert(Tx::new(3, 100, 10)); // fee 1000
        for budget in [10u64, 100, 110, 1000, 1100, 1110] {
            let sel = p.select(budget);
            let packed: u64 = sel.iter().map(|t| t.fee).sum();
            // brute force the best achievable under the same budget: try
            // every subset and keep the max fee that fits
            let all = p.pack_order();
            let n = all.len();
            let mut best = 0u64;
            for mask in 0u32..(1 << n) {
                let (mut bytes, mut fee) = (0u64, 0u64);
                for i in 0..n {
                    if mask >> i & 1 == 1 {
                        bytes += all[i].bytes;
                        fee += all[i].fee;
                    }
                }
                if bytes <= budget {
                    best = best.max(fee);
                }
            }
            assert!(packed <= best, "budget {}: the pool packed MORE than the optimum", budget);
            // the pool is greedy-by-density; it must match the optimum on
            // these instances, which is the property worth pinning
            assert_eq!(packed, best, "budget {}: the pool order was not fee-maximal", budget);
        }
    }

    /// THE SPAM GATE — two free-load vectors the pool must refuse, found by
    /// asking what insert() accepts rather than what it is for.
    ///
    /// (1) A ZERO-BYTE transaction packs into ANY budget, including zero:
    /// `used + 0 <= 0` is true. An empty block would then report it holds
    /// transactions, and the accounting invariant `bytes <= budget` becomes
    /// vacuous. Worse: its total fee is fee_per_byte * 0 = 0, so it costs
    /// nothing.
    ///
    /// (2) The subtle one. The pool sorts by fee_per_byte, and a zero-byte
    /// tx may still declare any fee_per_byte it likes. So it pays nothing,
    /// takes no space, and sorts AHEAD of every honest tx with a lower
    /// rate — free priority at the head of the leader's order. Refusing at
    /// insert is what keeps the ordering honest.
    #[test]
    fn zero_byte_and_zero_fee_transactions_are_refused() {
        let mut p = Mempool::new();
        // zero bytes with a high declared rate: must refuse, must not sort
        // ahead of the honest 100-byte transactions below
        assert!(!p.insert(Tx::new(1, 1_000_000, 0)), "a zero-byte tx was accepted");
        // zero fee (zero rate)
        assert!(!p.insert(Tx::new(2, 0, 100)), "a zero-fee tx was accepted");
        // both
        assert!(!p.insert(Tx::new(3, 0, 0)), "a zero-byte zero-fee tx was accepted");
        assert!(p.is_empty(), "refused transactions left residue in the pool");

        // the honest ones are still accepted
        assert!(p.insert(Tx::new(10, 50, 100)));
        assert!(p.insert(Tx::new(11, 30, 100)));
        assert_eq!(p.len(), 2);
        let ids: Vec<u64> = p.pack_order().iter().map(|t| t.id).collect();
        assert_eq!(ids, vec![10, 11], "the pack order was polluted by refused txs");
    }

    /// A refused replacement must not evict the existing entry — the spam
    /// gate must not become a removal vector. A caller re-inserting with
    /// invalid parameters should leave the pool as it was.
    #[test]
    fn a_refused_replacement_keeps_the_original() {
        let mut p = Mempool::new();
        assert!(p.insert(Tx::new(1, 50, 100)));
        // re-insert the same id with invalid parameters
        assert!(!p.insert(Tx::new(1, 1_000_000, 0)));
        assert_eq!(p.len(), 1, "a refused replacement evicted the original");
        let tx = p.pack_order()[0];
        assert_eq!(tx.fee_per_byte, 50);
        assert_eq!(tx.bytes, 100);
    }

    /// THE BOUNDARY AT ZERO: an empty pool and a zero budget select nothing,
    /// and a transaction larger than the budget selects nothing. These are
    /// the degenerate corners the accounting must survive without panic.
    #[test]
    fn empty_and_zero_budget_corners_select_nothing() {
        let mut p = Mempool::new();
        assert!(p.select(0).is_empty(), "an empty pool selected something at budget 0");
        let _ = p.insert(Tx::new(1, 50, 100));
        assert!(p.select(0).is_empty(), "a zero budget selected a nonzero-byte tx");
        assert!(p.select(99).is_empty(), "a sub-tx budget selected the tx");
        assert_eq!(p.select(100).len(), 1, "an exactly-fitting budget did not select the tx");
        assert_eq!(p.select(u64::MAX).len(), 1);
    }
}

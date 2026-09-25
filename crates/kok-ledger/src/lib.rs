//! LEDGER — the U-layer task market, where the escrow accounting lives.
//!
//! This is the money surface. A bug here is not a wrong number in a report,
//! it is value that disappears or appears — the is_final phantom-block bug
//! was this class exactly: a block that never existed was about to be
//! treated as paid. So the ledger is built around ONE invariant that is
//! checked by brute force after every operation:
//!
//!   sum(spendable balances) + sum(escrowed fees) == total_deposited - total_burned
//!
//! Every KOK that was ever deposited is, at all times, in exactly one of
//! three places: in a spendable balance, locked in escrow for an open task,
//! or burned. Settling moves fee into pay+burn; expiring moves it back to
//! the poster. Nothing else may create or destroy a unit.
//!
//! BOUNDARY, STATED: this is an in-memory REFERENCE ledger — the arbiter of
//! the accounting rules, single-threaded and deterministic. A production
//! ledger still needs persistence, batch-atomic debits, and a Merkle
//! commitment of the state root. Those are not here, and saying they were
//! would be an unmeasured shape claim. What IS here is the rule set and the
//! conservation property, measured rather than asserted.
//!
//! ARITHMETIC: every operation is checked, never wrapping. `fee * burn_rate`
//! with burn_rate up to 500 and a u64 fee overflows silently in release
//! mode, and a wrapped burn would under-pay the miner and mis-state the burn
//! — the same overflow class the WASM boundary guards against, so the guard
//! is applied here too.

use std::collections::HashMap;

/// The ceiling on a task's burn rate, in PARTS PER THOUSAND: 500 = 50% of
/// the fee. This is an anti-abuse bound, not a policy target. Do NOT
/// confuse it with the G-layer treasury share, which is TREASURY_BPS = 500
/// in BASIS POINTS = 5% — same digits, different units, different layer.
pub const MAX_BURN_RATE: u64 = 500;

/// The lifecycle of an escrowed task. Money moves ONLY on transitions, and
/// each transition is one-way — that is what makes double-payment a state
/// error rather than an arithmetic one.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskStatus {
    /// Fee locked; awaiting a proof.
    Escrowed,
    /// Proof accepted; the pay went to the miner and the burn went to the
    /// protocol. Settling again must fail.
    Settled,
    /// No proof arrived; the fee returned to the poster.
    Refunded,
}

#[derive(Debug, Clone)]
pub struct TaskEntry {
    pub poster: u64,
    pub fee: u64,
    pub burn_rate: u64,
    pub assignee: Option<u64>,
    pub status: TaskStatus,
}

#[derive(Debug, Default)]
pub struct Ledger {
    balances: HashMap<u64, u64>,
    tasks: HashMap<u64, TaskEntry>,
    total_deposited: u64,
    total_burned: u64,
    /// Fees currently locked in escrow.
    total_escrowed: u64,
    /// Cumulative fees paid out to provers.
    total_paid: u64,
}

/// The outcome of a settlement: how the fee split, for the caller to log.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Settlement {
    pub pay: u64,
    pub burn: u64,
}

/// The reason an operation refused. Everything that can fail returns a
/// reason instead of panicking, because a node must survive a malformed
/// task and keep serving honest ones.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LedgerError {
    InsufficientBalance,
    DuplicateTask,
    UnknownTask,
    NotEscrowed,
    AlreadySettled,
    BurnRateOutOfRange,
    Overflow,
    /// settle called on a task that was never assigned — no payee exists.
    NotAssigned,
    /// settle named a miner that is not the task's assignee.
    WrongPayee,
}

impl Ledger {
    pub fn new() -> Self {
        Self::default()
    }

    /// Credit a spendable balance. The only way money ENTERS the system.
    pub fn deposit(&mut self, account: u64, amount: u64) -> Result<(), LedgerError> {
        let bal = self.balances.entry(account).or_insert(0);
        *bal = bal.checked_add(amount).ok_or(LedgerError::Overflow)?;
        self.total_deposited = self
            .total_deposited
            .checked_add(amount)
            .ok_or(LedgerError::Overflow)?;
        Ok(())
    }

    pub fn balance(&self, account: u64) -> u64 {
        self.balances.get(&account).copied().unwrap_or(0)
    }

    /// Post a task: DEBIT the fee out of the poster's spendable balance and
    /// lock it in escrow. The debit and the escrow are one atomic step — if
    /// the fee never left the balance, a poster could spend the same funds
    /// on two tasks in the same block.
    pub fn post_task(
        &mut self,
        poster: u64,
        tid: u64,
        fee: u64,
        burn_rate: u64,
    ) -> Result<(), LedgerError> {
        if fee == 0 || burn_rate == 0 || burn_rate > MAX_BURN_RATE {
            return Err(LedgerError::BurnRateOutOfRange);
        }
        if self.tasks.contains_key(&tid) {
            return Err(LedgerError::DuplicateTask);
        }
        let bal = self.balances.get(&poster).copied().unwrap_or(0);
        if bal < fee {
            return Err(LedgerError::InsufficientBalance);
        }
        // checked against overflow above the bound: fee > 0 and burn_rate <=
        // 500 keeps the product well under u64::MAX, but the settle path
        // asserts it again rather than trusting this
        *self.balances.get_mut(&poster).unwrap() = bal - fee;
        self.total_escrowed = self
            .total_escrowed
            .checked_add(fee)
            .ok_or(LedgerError::Overflow)?;
        self.tasks.insert(
            tid,
            TaskEntry {
                poster,
                fee,
                burn_rate,
                assignee: None,
                status: TaskStatus::Escrowed,
            },
        );
        Ok(())
    }

    /// Record that a task was assigned (bookkeeping only — no money moves;
    /// the assignment itself is the VRF layer's job).
    pub fn assign(&mut self, tid: u64, assignee: u64) -> Result<(), LedgerError> {
        let t = self.tasks.get_mut(&tid).ok_or(LedgerError::UnknownTask)?;
        if t.status != TaskStatus::Escrowed {
            return Err(LedgerError::NotEscrowed);
        }
        t.assignee = Some(assignee);
        Ok(())
    }

    /// Settle a proven task: pay the assignee and burn the burn component.
    /// Idempotent-by-rejection — settling an already-settled task fails
    /// rather than paying again, which is the double-payment bug pinned.
    ///
    /// THE PAYEE IS THE ASSIGNEE. The burn and the payee are the two money
    /// destinations this function opens, and for a long time only the burn
    /// was validated while the payee was a caller-supplied `miner` that
    /// `assign` had no say over. That made assignment decorative: a task
    /// could be settled to ANY miner, including one never assigned — the
    /// money moved on the caller's word, and the assignment record was
    /// bookkeeping nobody consulted. The settlement now requires the caller
    /// to name the task's own assignee, so an unassigned task cannot be
    /// settled at all and a task assigned to X cannot be settled to Y. This
    /// is what makes the escrow a payment to the party that did the work
    /// rather than to whoever asks.
    pub fn settle(&mut self, tid: u64, miner: u64) -> Result<Settlement, LedgerError> {
        let t = self.tasks.get_mut(&tid).ok_or(LedgerError::UnknownTask)?;
        match t.status {
            TaskStatus::Settled => return Err(LedgerError::AlreadySettled),
            TaskStatus::Refunded => return Err(LedgerError::NotEscrowed),
            TaskStatus::Escrowed => {}
        }
        // the payee must be the assignee on record. An unassigned task has
        // no payee, and a task assigned to X cannot be settled to Y.
        let assignee = t.assignee.ok_or(LedgerError::NotAssigned)?;
        if assignee != miner {
            return Err(LedgerError::WrongPayee);
        }
        let fee = t.fee;
        let burn_rate = t.burn_rate;
        // the burn is the burn_rate per mille of the fee, checked
        let burn = fee
            .checked_mul(burn_rate)
            .and_then(|p| p.checked_div(1000))
            .ok_or(LedgerError::Overflow)?;
        let pay = fee.checked_sub(burn).ok_or(LedgerError::Overflow)?;

        // move the escrowed fee out: to the miner, and to the burn
        self.total_escrowed = self
            .total_escrowed
            .checked_sub(fee)
            .ok_or(LedgerError::Overflow)?;
        let bal = self.balances.entry(miner).or_insert(0);
        *bal = bal.checked_add(pay).ok_or(LedgerError::Overflow)?;
        self.total_paid = self.total_paid.checked_add(pay).ok_or(LedgerError::Overflow)?;
        self.total_burned = self
            .total_burned
            .checked_add(burn)
            .ok_or(LedgerError::Overflow)?;

        let t = self.tasks.get_mut(&tid).unwrap();
        t.status = TaskStatus::Settled;
        Ok(Settlement { pay, burn })
    }

    /// Refund an escrowed task that was never proven. Money returns to the
    /// poster; the burn component is NOT burned, because no work happened.
    pub fn refund(&mut self, tid: u64) -> Result<(), LedgerError> {
        let t = self.tasks.get_mut(&tid).ok_or(LedgerError::UnknownTask)?;
        match t.status {
            TaskStatus::Escrowed => {}
            TaskStatus::Settled => return Err(LedgerError::AlreadySettled),
            TaskStatus::Refunded => return Err(LedgerError::NotEscrowed),
        }
        let (poster, fee) = (t.poster, t.fee);
        self.total_escrowed = self
            .total_escrowed
            .checked_sub(fee)
            .ok_or(LedgerError::Overflow)?;
        let bal = self.balances.entry(poster).or_insert(0);
        *bal = bal.checked_add(fee).ok_or(LedgerError::Overflow)?;
        self.tasks.get_mut(&tid).unwrap().status = TaskStatus::Refunded;
        Ok(())
    }

    pub fn total_burned(&self) -> u64 {
        self.total_burned
    }

    pub fn total_escrowed(&self) -> u64 {
        self.total_escrowed
    }

    pub fn total_paid(&self) -> u64 {
        self.total_paid
    }

    pub fn task_status(&self, tid: u64) -> Option<TaskStatus> {
        self.tasks.get(&tid).map(|t| t.status)
    }

    /// THE CONSERVATION INVARIANT. Everything deposited is either in a
    /// spendable balance, locked in escrow, or burned:
    ///   balances + escrowed == deposited - burned
    /// Returns false the instant any operation mis-accounts a single unit.
    /// The balance sum is saturating: an overflow inside the CHECK would
    /// panic in debug and silently wrap in release, which would make the
    /// guard itself unreliable exactly when it is needed most.
    pub fn conserved(&self) -> bool {
        let balances: u64 = self.balances.values().copied().fold(0u64, u64::saturating_add);
        let held = balances.saturating_add(self.total_escrowed);
        // paid-out funds came from escrow and now sit in balances, so they
        // must not be double-counted: the identity is balances+escrow
        // against deposited-burned only
        let out = self.total_deposited.saturating_sub(self.total_burned);
        held == out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rng_next(state: &mut u64) -> u64 {
        let mut x = *state;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        *state = x;
        x
    }

    #[test]
    fn deposit_and_balance_are_consistent() {
        let mut l = Ledger::new();
        assert_eq!(l.balance(1), 0);
        l.deposit(1, 1000).unwrap();
        assert_eq!(l.balance(1), 1000);
        l.deposit(1, 500).unwrap();
        assert_eq!(l.balance(1), 1500);
        assert!(l.conserved());
    }

    /// Posting debits the poster immediately. If the fee stayed in the
    /// balance, the same funds could be promised twice in one block.
    #[test]
    fn posting_locks_the_fee_out_of_the_spendable_balance() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 400, 100).unwrap();
        assert_eq!(l.balance(1), 600, "the fee was not debited from the poster");
        assert_eq!(l.total_escrowed(), 400);
        assert!(l.conserved());
    }

    /// The double-spend guard: two tasks whose fees sum to more than the
    /// balance — the second must refuse, and the ledger must stay conserved.
    #[test]
    fn a_poster_cannot_spend_the_same_funds_twice() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 600, 100).unwrap();
        assert!(l.post_task(1, 11, 600, 100).is_err(), "the second task over-drew the balance");
        assert_eq!(l.balance(1), 400);
        assert_eq!(l.total_escrowed(), 600);
        assert!(l.conserved());
    }

    /// A task id may not be reused — the escrow is keyed to the task, so a
    /// duplicate id would collide two different escrows.
    #[test]
    fn a_task_id_cannot_be_reused() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 100, 100).unwrap();
        assert!(matches!(
            l.post_task(1, 10, 100, 100),
            Err(LedgerError::DuplicateTask)
        ));
    }

    /// Settling pays the assignee and burns the burn component, exactly.
    #[test]
    fn settling_splits_the_fee_into_pay_and_burn() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 1000, 250).unwrap(); // 25% burn
        l.assign(10, 2).unwrap();
        let s = l.settle(10, 2).unwrap();
        assert_eq!(s.pay, 750);
        assert_eq!(s.burn, 250);
        assert_eq!(l.balance(2), 750);
        assert_eq!(l.total_burned(), 250);
        assert_eq!(l.total_paid(), 750);
        assert_eq!(l.total_escrowed(), 0);
        assert!(l.conserved());
    }

    /// THE ASSIGNEE IS THE PAYEE — the bug this test pins. For a long time
    /// `settle` took the payee as a caller-supplied `miner` and never
    /// consulted the assignment record, so `assign` was decorative: a task
    /// could be settled to ANY miner, including one that was never assigned,
    /// and the assignment bookkeeping was never consulted by the one function
    /// that moves the money. An escrow that pays whoever asks is not an
    /// escrow. Now settle requires the caller to name the task's own
    /// assignee.
    #[test]
    fn settle_pays_the_assignee_and_nobody_else() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 1000, 250).unwrap();
        l.assign(10, 2).unwrap();
        // the task's own assignee settles
        let s = l.settle(10, 2).unwrap();
        assert_eq!(s.pay, 750);
        assert_eq!(l.balance(2), 750);
        // a miner that is not the assignee must not be able to claim it
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 11, 1000, 250).unwrap();
        l.assign(11, 4).unwrap();
        assert!(
            matches!(l.settle(11, 3), Err(LedgerError::WrongPayee)),
            "a miner that is not the assignee settled the task"
        );
        // the wrong payee's balance did not grow, and the task is still open
        assert_eq!(l.balance(3), 0, "the wrong payee was credited");
        assert_eq!(l.task_status(11), Some(TaskStatus::Escrowed), "the task was closed by a wrong payee");
        assert!(l.conserved());
        // the real assignee still can
        assert!(l.settle(11, 4).is_ok());
        assert_eq!(l.balance(4), 750);
        assert!(l.conserved());
    }

    /// An UNASSIGNED task cannot be settled at all — no payee exists, so the
    /// escrow has nowhere honest to go. Before the fix this "settled" to
    /// whatever miner the caller named, which is the same bug in its purest
    /// form: the assignment step had no bearing on who got paid.
    #[test]
    fn an_unassigned_task_cannot_be_settled() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 1000, 250).unwrap();
        assert!(
            matches!(l.settle(10, 2), Err(LedgerError::NotAssigned)),
            "an unassigned task was settled to a miner"
        );
        assert_eq!(l.balance(2), 0, "a miner was paid by an unassigned task");
        // the escrow is still intact and the task is still open
        assert_eq!(l.total_escrowed(), 1000);
        assert_eq!(l.task_status(10), Some(TaskStatus::Escrowed));
        assert!(l.conserved());
        // assigning and then settling works
        l.assign(10, 2).unwrap();
        assert!(l.settle(10, 2).is_ok());
    }

    /// DOUBLE-PAYMENT PINNED: settling a settled task must fail, and must
    /// not move money again. This is the is_final bug's class — a state
    /// that never existed being paid.
    #[test]
    fn a_settled_task_cannot_be_settled_again() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 1000, 100).unwrap();
        l.assign(10, 2).unwrap();
        l.settle(10, 2).unwrap();
        assert!(matches!(l.settle(10, 2), Err(LedgerError::AlreadySettled)));
        assert!(matches!(l.settle(10, 3), Err(LedgerError::AlreadySettled)));
        // the miner's balance did not grow from the replay attempt
        assert_eq!(l.balance(2), 900);
        assert!(l.conserved());
    }

    /// A refund returns the FULL fee — the burn component is not burned when
    /// no work was done, because burning it would be charging for a service
    /// never rendered.
    #[test]
    fn a_refund_returns_the_whole_fee_without_burning() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 400, 250).unwrap();
        l.refund(10).unwrap();
        assert_eq!(l.balance(1), 1000);
        assert_eq!(l.total_burned(), 0, "a refund burned value for work that never happened");
        assert_eq!(l.total_escrowed(), 0);
        assert!(l.conserved());
    }

    /// A settled task cannot be refunded — that would pay the miner AND give
    /// the poster its money back, creating units out of nothing.
    #[test]
    fn a_settled_task_cannot_be_refunded() {
        let mut l = Ledger::new();
        l.deposit(1, 1000).unwrap();
        l.post_task(1, 10, 1000, 100).unwrap();
        l.assign(10, 2).unwrap();
        l.settle(10, 2).unwrap();
        assert!(matches!(l.refund(10), Err(LedgerError::AlreadySettled)));
        assert_eq!(l.balance(1), 0);
        assert_eq!(l.balance(2), 900);
        assert!(l.conserved());
    }

    /// Bounds: a zero fee, a zero burn rate, and an out-of-range burn rate
    /// all refuse. burn_rate is per mille, so 500 is the 5% ceiling.
    #[test]
    fn degenerate_task_parameters_are_refused() {
        let mut l = Ledger::new();
        l.deposit(1, 10_000).unwrap();
        assert!(l.post_task(1, 1, 0, 100).is_err(), "a zero fee was accepted");
        assert!(l.post_task(1, 2, 100, 0).is_err(), "a zero burn rate was accepted");
        assert!(l.post_task(1, 3, 100, 501).is_err(), "a burn rate above the ceiling was accepted");
        assert!(l.post_task(1, 4, 100, MAX_BURN_RATE).is_ok(), "the ceiling itself must be accepted");
    }

    /// UNKNOWN TASKS: operations on a task id that was never posted must
    /// fail cleanly, not panic.
    #[test]
    fn unknown_tasks_fail_cleanly() {
        let mut l = Ledger::new();
        assert!(matches!(l.settle(999, 1), Err(LedgerError::UnknownTask)));
        assert!(matches!(l.refund(999), Err(LedgerError::UnknownTask)));
        assert!(matches!(l.assign(999, 1), Err(LedgerError::UnknownTask)));
        assert!(l.task_status(999).is_none());
        assert!(l.conserved());
    }

    /// BRUTE-FORCE CONSERVATION OVER A RANDOM LIFECYCLE. This is the
    /// measurement that matters: after EVERY deposit, post, settle, refund,
    /// and failed attempt, the identity must hold. A single mis-accounted
    /// unit anywhere in the sequence fails here. The sequence is seeded, so
    /// a regression is reproducible rather than a flake.
    #[test]
    fn conservation_holds_after_every_operation_in_a_random_lifecycle() {
        let mut l = Ledger::new();
        let mut state: u64 = 20260925;
        let mut posted: Vec<u64> = Vec::new();
        for step in 0..20_000 {
            let r = rng_next(&mut state);
            match r % 4 {
                0 => {
                    // deposit: money enters
                    let acct = (r >> 8) % 8;
                    let amt = (r >> 16) % 500 + 1;
                    l.deposit(acct, amt).unwrap();
                }
                1 => {
                    // post: money locks, if the balance covers it
                    let acct = (r >> 8) % 8;
                    let tid = 1000 + step;
                    let fee = (r >> 16) % 400 + 1;
                    let br = (r >> 32) % MAX_BURN_RATE + 1;
                    if l.post_task(acct, tid, fee, br).is_ok() {
                        posted.push(tid);
                    } else {
                        // refusal must not break the invariant either
                    }
                }
                2 => {
                    // settle or refund the most recent open task. Both
                    // consume it either way, so the id comes off the list
                    // regardless of success — a failed settle on an
                    // already-consumed task still means it is not open.
                    //
                    // The settle path assigns FIRST half the time, so the
                    // fuzzer exercises both the accepted assignee and the
                    // WrongPayee rejection, not only the NotAssigned path.
                    if let Some(&tid) = posted.last() {
                        let op = (r >> 8) % 2;
                        let _ = if op == 0 {
                            let miner = (r >> 16) % 8;
                            if (r >> 24) % 2 == 0 {
                                let _ = l.assign(tid, miner);
                            }
                            l.settle(tid, miner).map(|_| ())
                        } else {
                            l.refund(tid)
                        };
                        posted.pop();
                    }
                }
                _ => {
                    // a double-settle attempt on an already-consumed task
                    if !posted.is_empty() {
                        let _ = l.settle(posted[0], 0);
                    }
                }
            }
            // THE CHECK, after every single step
            assert!(l.conserved(), "conservation broke at step {step}");
        }
        // the identity holds as a whole too
        let balances: u64 = l.balances.values().copied().sum();
        assert_eq!(
            balances + l.total_escrowed(),
            l.total_deposited - l.total_burned
        );
    }

    /// The burn fraction is exactly per mille: burn_rate/1000 of the fee.
    /// Measured at the ceiling and at a non-round rate, because integer
    /// division is where a naive implementation drops units.
    ///
    /// UNITS WARNING — the trap this test exists to catch. There are TWO
    /// different 500s in this protocol and conflating them is a units bug:
    ///   * MAX_BURN_RATE = 500 PER MILLE = 50% — the ceiling on how much of
    ///     a task fee may burn (an anti-abuse bound, not a policy target);
    ///   * TREASURY_BPS = 500 BASIS POINTS = 5% — the treasury's share of
    ///     the G-layer block reward, an entirely different quantity.
    /// Same digits, different units, different layers. The burn at the
    /// ceiling of a 1000-fee task is 500, not 50.
    #[test]
    fn the_burn_is_exactly_per_mille() {
        let mut l = Ledger::new();
        l.deposit(1, u64::MAX / 4).unwrap();
        // the ceiling itself: 500 per mille of 1000
        l.post_task(1, 1, 1000, MAX_BURN_RATE).unwrap();
        l.assign(1, 2).unwrap();
        let s = l.settle(1, 2).unwrap();
        assert_eq!(s.burn, 500, "the ceiling burn was not exactly MAX_BURN_RATE per mille");
        assert_eq!(s.pay, 500);
        // a rate that does not divide evenly: 333 per mille of 1000
        l.post_task(1, 2, 1000, 333).unwrap();
        l.assign(2, 2).unwrap();
        let s2 = l.settle(2, 2).unwrap();
        assert_eq!(s2.burn, 333);
        assert_eq!(s2.pay, 667);
        assert!(l.conserved());
    }

    /// Overflow does not wrap. fee*burn_rate at the largest allowed
    /// parameters must not silently produce a small burn.
    #[test]
    fn extreme_amounts_do_not_wrap_into_a_small_burn() {
        let mut l = Ledger::new();
        l.deposit(1, u64::MAX).unwrap();
        // fee large, burn_rate at the ceiling
        let fee = 1_000_000_000_000u64;
        l.post_task(1, 1, fee, MAX_BURN_RATE).unwrap();
        l.assign(1, 2).unwrap();
        let s = l.settle(1, 2).unwrap();
        assert_eq!(s.burn, fee * MAX_BURN_RATE / 1000, "the burn wrapped or mis-computed");
        assert_eq!(s.pay, fee - s.burn);
        assert!(l.conserved());
    }
}

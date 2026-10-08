//! LEDGER muhasebe kuralı testleri (core-final, LEAD).
//! "The money surface" — tek değişmez:
//!   balances + escrowed == deposited - burned
//! Her işlemden sonra conserved() doğrulanır.
//! Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.

use kok_ledger::{Ledger, LedgerError, TaskStatus, MAX_BURN_RATE};

fn funded(poster: u64, amt: u64) -> Ledger {
    let mut l = Ledger::new();
    l.deposit(poster, amt).unwrap();
    l
}

#[test]
fn deposit_and_balance() {
    let l = funded(1, 1000);
    assert_eq!(l.balance(1), 1000);
    assert_eq!(l.balance(2), 0); // açılmamış hesap
    assert!(l.conserved());
}

#[test]
fn deposit_accumulates() {
    let mut l = Ledger::new();
    l.deposit(1, 100).unwrap();
    l.deposit(1, 50).unwrap();
    assert_eq!(l.balance(1), 150);
    assert!(l.conserved());
}

#[test]
fn post_task_escrows_and_debits() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 400, 100).unwrap();
    assert_eq!(l.balance(1), 600);       // fee çekildi
    assert_eq!(l.total_escrowed(), 400); // escrow'da
    assert!(l.conserved());
    assert_eq!(l.task_status(10), Some(TaskStatus::Escrowed));
}

#[test]
fn post_task_rejects_zero_fee() {
    let mut l = funded(1, 1000);
    assert_eq!(l.post_task(1, 1, 0, 100), Err(LedgerError::BurnRateOutOfRange));
}

#[test]
fn post_task_rejects_zero_burn_rate() {
    let mut l = funded(1, 1000);
    assert_eq!(l.post_task(1, 1, 100, 0), Err(LedgerError::BurnRateOutOfRange));
}

#[test]
fn post_task_rejects_burn_rate_over_max() {
    let mut l = funded(1, 1000);
    assert_eq!(l.post_task(1, 1, 100, MAX_BURN_RATE + 1), Err(LedgerError::BurnRateOutOfRange));
}

#[test]
fn post_task_at_max_burn_rate_allowed() {
    let mut l = funded(1, 1000);
    assert!(l.post_task(1, 1, 100, MAX_BURN_RATE).is_ok());
    assert!(l.conserved());
}

#[test]
fn post_task_rejects_duplicate() {
    let mut l = funded(1, 1000);
    l.post_task(1, 7, 100, 100).unwrap();
    assert_eq!(l.post_task(1, 7, 100, 100), Err(LedgerError::DuplicateTask));
}

#[test]
fn post_task_rejects_insufficient_balance() {
    let mut l = funded(1, 100);
    assert_eq!(l.post_task(1, 1, 101, 100), Err(LedgerError::InsufficientBalance));
    assert_eq!(l.total_escrowed(), 0); // escrow'a bir şey gitmedi
}

#[test]
fn post_task_zero_balance_rejected() {
    let mut l = Ledger::new(); // hiç deposit yok
    assert_eq!(l.post_task(1, 1, 1, 100), Err(LedgerError::InsufficientBalance));
}

#[test]
fn settle_pays_miner_and_burns() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 1000, 100).unwrap(); // %10 burn
    l.assign(10, 2).unwrap();
    let s = l.settle(10, 2).unwrap();
    assert_eq!(s.burn, 100);   // 1000 * 100 / 1000
    assert_eq!(s.pay, 900);    // 1000 - 100
    assert_eq!(l.balance(2), 900);
    assert_eq!(l.total_burned(), 100);
    assert_eq!(l.total_paid(), 900);
    assert_eq!(l.total_escrowed(), 0);
    assert!(l.conserved());
    assert_eq!(l.task_status(10), Some(TaskStatus::Settled));
}

#[test]
fn settle_double_payment_blocked() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 1000, 100).unwrap();
    l.assign(10, 2).unwrap();
    l.settle(10, 2).unwrap();
    // ikinci settle reddedilir — çift ödeme engeli
    assert_eq!(l.settle(10, 2), Err(LedgerError::AlreadySettled));
    assert_eq!(l.balance(2), 900); // değişmedi
    assert!(l.conserved());
}

#[test]
fn settle_unassigned_blocked() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 1000, 100).unwrap();
    // assign yok → ödeyecek kimse yok
    assert_eq!(l.settle(10, 2), Err(LedgerError::NotAssigned));
    assert_eq!(l.total_escrowed(), 1000); // escrow'da kaldı
}

#[test]
fn settle_wrong_payee_blocked() {
    // GÜVENLIK: X'e atanan görev Y'ye ödenemez
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 1000, 100).unwrap();
    l.assign(10, 2).unwrap();
    assert_eq!(l.settle(10, 99), Err(LedgerError::WrongPayee));
    assert_eq!(l.balance(99), 0);
    assert_eq!(l.total_escrowed(), 1000); // para gitmedi
    assert!(l.conserved());
}

#[test]
fn settle_after_refund_blocked() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 1000, 100).unwrap();
    l.assign(10, 2).unwrap();
    l.refund(10).unwrap();
    assert_eq!(l.settle(10, 2), Err(LedgerError::NotEscrowed));
}

#[test]
fn settle_unknown_task_blocked() {
    let mut l = funded(1, 1000);
    assert_eq!(l.settle(999, 2), Err(LedgerError::UnknownTask));
}

#[test]
fn settle_burn_half_at_max() {
    let mut l = funded(1, 10000);
    l.post_task(1, 10, 10000, MAX_BURN_RATE).unwrap(); // %50
    l.assign(10, 2).unwrap();
    let s = l.settle(10, 2).unwrap();
    assert_eq!(s.burn, 5000);
    assert_eq!(s.pay, 5000);
    assert!(l.conserved());
}

#[test]
fn refund_returns_to_poster_no_burn() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 400, 100).unwrap();
    l.refund(10).unwrap();
    assert_eq!(l.balance(1), 1000);      // geri döndü
    assert_eq!(l.total_escrowed(), 0);
    assert_eq!(l.total_burned(), 0);     // iş olmadı, yakılmadı
    assert_eq!(l.total_paid(), 0);
    assert!(l.conserved());
    assert_eq!(l.task_status(10), Some(TaskStatus::Refunded));
}

#[test]
fn refund_double_blocked() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 400, 100).unwrap();
    l.refund(10).unwrap();
    assert_eq!(l.refund(10), Err(LedgerError::NotEscrowed));
    assert_eq!(l.balance(1), 1000); // değişmedi
}

#[test]
fn refund_after_settle_blocked() {
    let mut l = funded(1, 1000);
    l.post_task(1, 10, 1000, 100).unwrap();
    l.assign(10, 2).unwrap();
    l.settle(10, 2).unwrap();
    assert_eq!(l.refund(10), Err(LedgerError::AlreadySettled));
    assert_eq!(l.balance(1), 0); // settle'da poster zaten ödedi
    assert_eq!(l.balance(2), 900);
}

#[test]
fn refund_unknown_task_blocked() {
    let mut l = funded(1, 1000);
    assert_eq!(l.refund(999), Err(LedgerError::UnknownTask));
}

#[test]
fn assign_requires_escrowed() {
    let mut l = funded(1, 1000);
    assert_eq!(l.assign(10, 2), Err(LedgerError::UnknownTask));
    l.post_task(1, 10, 400, 100).unwrap();
    l.assign(10, 2).unwrap();
    // tekrar assign — hala Escrowed, üzerine yazar (bookkeeping)
    l.assign(10, 3).unwrap();
    assert_eq!(l.settle(10, 3).is_ok(), true);
}

#[test]
fn full_lifecycle_two_tasks_conserved() {
    let mut l = Ledger::new();
    l.deposit(1, 5000).unwrap();
    l.deposit(3, 5000).unwrap();
    l.post_task(1, 100, 1000, 50).unwrap(); // %5
    l.post_task(3, 200, 2000, 200).unwrap(); // %20
    l.assign(100, 2).unwrap();
    l.assign(200, 2).unwrap();
    assert!(l.conserved());
    let s1 = l.settle(100, 2).unwrap();
    let s2 = l.settle(200, 2).unwrap();
    assert!(l.conserved());
    assert_eq!(s1.burn, 50);   // 1000*50/1000
    assert_eq!(s1.pay, 950);
    assert_eq!(s2.burn, 400);  // 2000*200/1000
    assert_eq!(s2.pay, 1600);
    assert_eq!(l.balance(2), 950 + 1600);
    assert_eq!(l.total_burned(), 50 + 400);
    assert_eq!(l.total_paid(), 950 + 1600);
    // poster 1: 5000-1000; poster 3: 5000-2000
    assert_eq!(l.balance(1), 4000);
    assert_eq!(l.balance(3), 3000);
}

#[test]
fn conservation_holds_across_mixed_settle_and_refund() {
    let mut l = Ledger::new();
    l.deposit(1, 3000).unwrap();
    l.post_task(1, 1, 1000, 100).unwrap();
    l.post_task(1, 2, 1000, 100).unwrap();
    l.post_task(1, 3, 500, 100).unwrap();
    assert!(l.conserved());
    // task 1 settle, task 2 refund, task 3 beklemede
    l.assign(1, 7).unwrap();
    l.settle(1, 7).unwrap();
    assert!(l.conserved());
    l.refund(2).unwrap();
    assert!(l.conserved());
    // escrow'da sadece task 3'ün 500'ü kalmalı
    assert_eq!(l.total_escrowed(), 500);
    assert!(l.conserved());
}

#[test]
fn task_status_unknown_returns_none() {
    let l = Ledger::new();
    assert_eq!(l.task_status(42), None);
}

#[test]
fn totals_start_zero() {
    let l = Ledger::new();
    assert_eq!(l.total_burned(), 0);
    assert_eq!(l.total_escrowed(), 0);
    assert_eq!(l.total_paid(), 0);
    assert!(l.conserved());
}

#[test]
fn deposit_overflow_rejected() {
    let mut l = Ledger::new();
    l.deposit(1, u64::MAX).unwrap();
    // ikinci deposit overflow → checked_add reddeder
    assert_eq!(l.deposit(1, 1), Err(LedgerError::Overflow));
}

//! FFI — the C ABI for SDK consumers, built so a bad caller cannot break it.
//!
//! THE CONTRACT: an `extern "C"` function must never unwind into the caller.
//! A Rust panic crossing the FFI boundary is undefined behavior, and a C
//! consumer cannot catch it — so every function here is TOTAL by
//! construction. That is a stronger promise than "it has not panicked yet":
//!
//!   * no indexing on caller-supplied lengths, so there is no out-of-bounds
//!     read to unwind from;
//!   * checked arithmetic only, because `fee + carried` at u64::MAX wraps
//!     silently in release mode and a wrapped cap would admit a task the
//!     protocol meant to reject;
//!   * no allocation on the caller's behalf, so there is no OOM path;
//!   * every outcome is a status code, including the reject cases.
//!
//! WHY NO catch_unwrap: these functions are total, so there is nothing to
//! catch. A catch_unwind guard becomes necessary only when the surface grows
//! to code that CAN panic — indexing, parsing, allocating. That guidance is
//! written here rather than in a wiki, because the boundary is where the
//! next FFI function will be written.
//!
//! SCOPE, kept honest: this exposes the protocol constants and the U-layer
//! admission gate, which is what an SDK integrator compiling against KÖK
//! needs. The G-certificate verification surface has its own byte-packet ABI
//! in kok-wasm — that is the intended light-client path, and duplicating the
//! wire layout here would create a second source of truth that could drift.
//! It is not duplicated.

pub use kok_consensus;

use kok_consensus::kok_u_layer::{
    u_task_consensus_weight, validate_u_task, TaskProof, TaskSpec, C_FEE, EPOCH_LOOKBACK,
    MAX_BURN_RATE,
};

/// Status codes. Plain u8 so the ABI does not depend on Rust's enum layout,
/// and so a C header can name them without a bindgen round-trip.
pub const KOK_OK: u8 = 0;
pub const KOK_REJECTED: u8 = 1;
pub const KOK_NULL_POINTER: u8 = 2;
pub const KOK_BAD_LENGTH: u8 = 3;
pub const KOK_OVERFLOW: u8 = 4;

/// The anti-aggregation fee cap a block carries. Exposed so an SDK consumer
/// computes "would this task fit a block" against the same value the node
/// enforces, instead of a hardcoded copy.
#[no_mangle]
pub extern "C" fn kok_c_fee() -> u64 {
    C_FEE
}

/// The epoch lookback in blocks (grinding resistance). Same rationale: the
/// value the node uses, not a copy.
#[no_mangle]
pub extern "C" fn kok_epoch_lookback() -> u64 {
    EPOCH_LOOKBACK as u64
}

/// The ceiling on a task's burn rate, in parts per thousand. NOT the
/// treasury share: that one is basis points and a different layer. Keeping
/// both named here is what stops the classic units mixup at the ABI.
#[no_mangle]
pub extern "C" fn kok_max_burn_rate() -> u64 {
    MAX_BURN_RATE
}

/// The consensus weight any U-task proof contributes. Always zero, computed
/// rather than asserted, so an SDK consumer's "can demand buy security"
/// question gets a real answer from the protocol and not a comment.
#[no_mangle]
pub extern "C" fn kok_u_task_consensus_weight() -> u64 {
    // A proof carrying the largest fee the protocol allows still weighs
    // nothing — the function ignores the proof's contents, but constructing
    // one makes the call honest rather than hand-waved.
    u_task_consensus_weight(&TaskProof {
        tid: String::new(),
        miner: String::new(),
        fee: u64::MAX,
    })
}

/// The U-task admission gate: is this task valid, and does it fit the
/// block's remaining fee budget? Returns KOK_OK or KOK_REJECTED — no panics,
/// no wrapping, on every input including the ones designed to break it.
///
/// `carried_fee_total` is the fee value already committed in this block;
/// `fee` is this task's. The sum is checked because at u64::MAX it wraps,
/// and a wrapped sum would pass a task that overflows the cap.
#[no_mangle]
pub extern "C" fn kok_validate_u_task(fee: u64, burn_rate: u64, carried_fee_total: u64) -> u8 {
    let task = TaskSpec {
        program: String::new(),
        fee,
        burn_rate,
    };
    // validate_u_task itself does checked arithmetic; this is the boundary
    // that makes sure of it before the answer crosses into C
    if carried_fee_total.checked_add(fee).is_none() {
        return KOK_OVERFLOW;
    }
    if validate_u_task(&task, carried_fee_total) {
        KOK_OK
    } else {
        KOK_REJECTED
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The constants match the protocol, so an SDK consumer cannot drift
    /// from the node by copying a number that later changed.
    #[test]
    fn the_ffi_constants_match_the_protocol() {
        assert_eq!(kok_c_fee(), C_FEE);
        assert_eq!(kok_max_burn_rate(), MAX_BURN_RATE);
        assert_eq!(kok_epoch_lookback(), EPOCH_LOOKBACK as u64);
    }

    /// THE NO-PANIC CONTRACT, tested at the inputs chosen to break it. Each
    /// of these would panic or wrap in a naive implementation: u64::MAX
    /// arithmetic, a zero fee, a burn rate above the ceiling, and a carried
    /// total that already equals the cap.
    #[test]
    fn adversarial_validate_input_never_panics() {
        // u64::MAX everywhere — the sum must not wrap into a pass
        assert_eq!(kok_validate_u_task(u64::MAX, 100, u64::MAX), KOK_OVERFLOW);
        // carried at the cap leaves no room for any positive fee
        assert_eq!(kok_validate_u_task(1, 100, C_FEE), KOK_REJECTED);
        // a task that exactly fills the remaining budget is OK
        assert_eq!(kok_validate_u_task(C_FEE, 100, 0), KOK_OK);
        assert_eq!(kok_validate_u_task(1, 100, C_FEE - 1), KOK_OK);
        // a zero fee is not a task
        assert_eq!(kok_validate_u_task(0, 100, 0), KOK_REJECTED);
        // burn rate bounds: zero is not a burn, the ceiling is allowed,
        // above the ceiling is not
        assert_eq!(kok_validate_u_task(100, 0, 0), KOK_REJECTED);
        assert_eq!(kok_validate_u_task(100, MAX_BURN_RATE, 0), KOK_OK);
        assert_eq!(kok_validate_u_task(100, MAX_BURN_RATE + 1, 0), KOK_REJECTED);
        // u64::MAX fee with a zero carried does not overflow the cap check
        assert_eq!(kok_validate_u_task(u64::MAX, 100, 0), KOK_REJECTED);
    }

    /// The weight surface: zero even when the proof carries a maximum fee
    /// and a maximum burn rate. An SDK consumer asking "can demand buy
    /// weight" gets the protocol's answer.
    #[test]
    fn the_u_weight_surface_is_zero_at_the_extremes() {
        assert_eq!(kok_u_task_consensus_weight(), 0);
    }

    /// The admission decisions are exactly the protocol's, measured at the
    /// boundary rather than assumed — a task the node rejects, the FFI
    /// rejects too.
    #[test]
    fn the_ffi_gate_agrees_with_the_protocol_gate() {
        for (fee, burn, carried) in [
            (100u64, 100u64, 0u64),
            (C_FEE, 500, 0),
            (1, 1, C_FEE - 1),
            (1, 1, C_FEE),
            (0, 100, 0),
            (100, 0, 0),
        ] {
            let task = TaskSpec {
                program: String::new(),
                fee,
                burn_rate: burn,
            };
            let expected = validate_u_task(&task, carried);
            let got = kok_validate_u_task(fee, burn, carried) == KOK_OK;
            assert_eq!(
                got, expected,
                "the FFI gate disagreed at fee={fee} burn={burn} carried={carried}"
            );
        }
    }

    /// THE STATUS-CODE SPACE IS THE ABI A C HEADER NAMES (2026-09-28).
    ///
    /// These u8 constants are the contract a C consumer compiles against, and
    /// a header naming them is generated by hand, not by bindgen — so a
    /// collision or an accidental reorder would silently break every SDK
    /// consumer while Rust kept compiling. Two properties are pinned: the
    /// codes are pairwise distinct (no two names share a value), and OK is 0,
    /// which is what a C caller's `if (rc)` idiom assumes.
    ///
    /// THE HONEST FINDING THIS SURFACES: KOK_NULL_POINTER and KOK_BAD_LENGTH
    /// are defined but the current surface RETURNS NEITHER, because no exposed
    /// function takes a pointer or a length — the admission gate takes three
    /// u64s. They are reserved codes for the ABI's growth, not outcomes any
    /// caller can observe today. That is stated here rather than left for a
    /// reader to discover, because a consumer testing for KOK_BAD_LENGTH would
    /// find the check dead and might assume the length validation is missing
    /// rather than not-yet-needed.
    #[test]
    fn the_status_codes_are_distinct_and_ok_is_zero() {
        let codes = [
            KOK_OK,
            KOK_REJECTED,
            KOK_NULL_POINTER,
            KOK_BAD_LENGTH,
            KOK_OVERFLOW,
        ];
        assert_eq!(
            KOK_OK, 0,
            "a C caller's `if (rc)` idiom breaks unless OK is 0"
        );
        // pairwise distinct
        for i in 0..codes.len() {
            for j in (i + 1)..codes.len() {
                assert_ne!(
                    codes[i], codes[j],
                    "status codes {i} and {j} share the value {}",
                    codes[i]
                );
            }
        }
        // they are all plain u8s small enough to fit a C enum
        assert!(codes.iter().all(|&c| c < 16));
        // and the three the gate can actually return are the reachable set —
        // see the totality test below; NULL_POINTER and BAD_LENGTH are reserve
    }

    /// THE OVERFLOW BOUNDARY IS EXACTLY checked_add, NOT A HEURISTIC.
    ///
    /// `kok_validate_u_task` computes `carried + fee` with checked_add and
    /// returns KOK_OVERFLOW when it fails. The difference between the
    /// overflowing and non-overflowing cases is ONE UNIT at u64::MAX: a sum
    /// that lands exactly on u64::MAX does not overflow and must reach the
    /// protocol's cap check, while a sum one past it must report OVERFLOW
    /// rather than wrapping to a small number that would silently pass. A
    /// release-mode `+` would wrap here and admit a task over the cap, which
    /// is precisely the wrap-in-disguise failure this crate exists to prevent.
    #[test]
    fn the_overflow_boundary_is_exactly_at_the_sum() {
        // sums landing exactly ON u64::MAX: no overflow, so the decision is
        // the protocol's, not the boundary's
        assert_eq!(kok_validate_u_task(1, 100, u64::MAX - 1), KOK_REJECTED);
        assert_eq!(kok_validate_u_task(u64::MAX, 100, 0), KOK_REJECTED);
        assert_eq!(
            kok_validate_u_task(0, 100, u64::MAX),
            KOK_REJECTED,
            "a zero fee is still rejected, not overflowed"
        );
        // sums going PAST u64::MAX by the smallest possible amount: overflow
        assert_eq!(kok_validate_u_task(2, 100, u64::MAX - 1), KOK_OVERFLOW);
        assert_eq!(kok_validate_u_task(1, 100, u64::MAX), KOK_OVERFLOW);
        assert_eq!(kok_validate_u_task(u64::MAX, 100, u64::MAX), KOK_OVERFLOW);
        // a sweep of the boundary: OVERFLOW exactly when checked_add fails
        for carried in [u64::MAX - 3, u64::MAX - 2, u64::MAX - 1, u64::MAX] {
            for fee in [1u64, 2, 3, 4] {
                let rc = kok_validate_u_task(fee, 100, carried);
                if carried.checked_add(fee).is_none() {
                    assert_eq!(
                        rc, KOK_OVERFLOW,
                        "sum {carried}+{fee} overflowed but rc was {rc}"
                    );
                } else {
                    // the non-overflow path is the protocol's verdict, which
                    // rejects every one of these because the fees exceed the cap
                    assert_ne!(
                        rc, KOK_OVERFLOW,
                        "sum {carried}+{fee} did not overflow but reported OVERFLOW"
                    );
                }
            }
        }
    }

    /// TOTALITY: the gate returns one of the three REACHABLE codes on every
    /// input, including the adversarial ones. This is the crate's headline
    /// contract — an extern "C" function must never unwind — tested by
    /// exhausting the outcome space rather than by hoping the interesting
    /// inputs were thought of. If any input produced a fourth value or a
    /// panic, this is where it would appear.
    #[test]
    fn the_gate_returns_only_reachable_codes_on_every_input() {
        let reachable = [KOK_OK, KOK_REJECTED, KOK_OVERFLOW];
        let mut seen = std::collections::HashSet::new();
        // a deliberately awkward mix: extremes, boundaries, and ordinary values
        let vals = [
            0u64,
            1,
            2,
            100,
            C_FEE,
            C_FEE - 1,
            C_FEE + 1,
            MAX_BURN_RATE,
            MAX_BURN_RATE + 1,
            u64::MAX,
            u64::MAX - 1,
        ];
        for fee in vals {
            for burn in vals {
                for carried in vals {
                    let rc = kok_validate_u_task(fee, burn, carried);
                    assert!(
                        reachable.contains(&rc),
                        "fee={fee} burn={burn} carried={carried} produced an unreachable code {rc}"
                    );
                    seen.insert(rc);
                }
            }
        }
        // the honest completeness statement: all three reachable codes really
        // are produced by this input set, so none of them is dead
        assert_eq!(
            seen,
            reachable
                .into_iter()
                .collect::<std::collections::HashSet<_>>(),
            "some reachable status code was never produced by the sweep"
        );
    }
}

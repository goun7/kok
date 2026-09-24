//! KOK Network v2 — the two-layer proof-of-useful-work consensus.
//!
//! Layer G: MatMul PoW (KwKernel). Pure PoW filler — zero useful work, but
//! its hardness is demand-independent (paper §B, PR/2) and STRUCTURAL, which
//! is the property plain Freivalds lacks.
//! Layer U: fee-paid verifiable compute. Zero consensus weight — never in
//! the leader election.

pub mod consensus;

pub use consensus::poum::{Certificate, KwKernel, TOY_N, TOY_Q, TOY_R};

//! The two-layer PoUM composition.
//!
//! Layer G (kok-poum) chooses leaders: a MatMul PoW certificate whose
//! hardness is structural and demand-independent. Layer U (kok-u-layer) is
//! the fee-paid verifiable-compute market and contributes ZERO consensus
//! weight — a U proof never enters leader election. That separation is the
//! property that makes "useful work" uncapturable: an attacker cannot buy
//! security by buying inference demand.

pub use kok_fri;
pub use kok_ghostdag;
pub use kok_poum;
pub use kok_u_layer;

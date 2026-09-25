//! U-layer job specs: the shape of a unit of useful work.
//!
//! The orchestrator's directive: GNoME-Forge is the reference U-layer job
//! type. Its compute profile (from the project's own paper) is a crystal
//! structure fed through an CHGNet/M3GNet machine-learned potential, which
//! turns months of DFT into seconds of tensor inference. This module
//! describes that shape generically — an input tensor, an expected output
//! shape — so the network can price and verify a job WITHOUT knowing what
//! the model is, and so GNoME-Forge is a *client* of KÖK, not a fork of it.
//!
//! WHAT THIS IS NOT: this is not GNoME-Forge's code. The directive is
//! explicit that only the U-layer interface is defined here.

/// The kind of tensor job. Named after the reference workload rather than
/// after a generic "ML inference", because the fee market and the hardness
/// of verification both depend on the shape, and a generic label would hide
/// the one thing a verifier must know.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JobKind {
    /// A structure tensor → energy/forces/stress, the CHGNet/M3GNet profile.
    /// Input: atom positions + species (rank-2). Output: per-atom forces
    /// (rank-2, same leading dim) + a scalar energy + a rank-2 stress.
    StructurePotential {
        /// Number of atoms — the leading dimension of both input and output.
        n_atoms: usize,
    },
    /// A general matmul-shape job, for any workload whose cost is dominated
    /// by a matrix product the G layer can also certify.
    MatMul {
        rows: usize,
        inner: usize,
        cols: usize,
    },
    /// A custom job whose shape is carried verbatim; the verifier cannot
    /// derive its cost and must be told it. Kept explicit rather than
    /// inferred, because an inferred cost is an unverifiable claim.
    Custom {
        flops: u64,
        output_shape: Vec<usize>,
    },
}

impl JobKind {
    /// The FLOP cost the network prices. For the structure-potential job
    /// this is the model's forward pass, whose dominant term is the
    /// message-passing over the neighbour list — O(n_atoms^2) for the
    /// pairwise part, which is what makes a 100-atom cell a meaningfully
    /// bigger job than a 10-atom cell.
    ///
    /// HONEST BOUNDARY: this is a cost MODEL, not a measurement. The real
    /// CHGNet cost depends on the neighbour cutoff and the number of
    /// message-passing layers, neither of which this type carries. It is
    /// sufficient for fee PRICING (a monotone proxy) and insufficient for
    /// a hashrate claim, which is why the U layer contributes zero
    /// consensus weight regardless: nothing here is ever converted into
    /// security, so an over-estimate inflates a fee and never a block.
    pub fn flops(&self) -> u64 {
        match self {
            JobKind::StructurePotential { n_atoms } => {
                // pairwise message passing + per-atom output heads
                let n = *n_atoms as u64;
                6 * n * n + 3 * n
            }
            JobKind::MatMul { rows, inner, cols } => {
                2 * (*rows as u64) * (*inner as u64) * (*cols as u64)
            }
            JobKind::Custom { flops, .. } => *flops,
        }
    }

    /// The expected output shape, which the verifier checks a result against
    /// BEFORE looking at the values. This is the cheap half of verification
    /// and the half that catches a wrong model rather than a wrong number.
    pub fn output_shape(&self) -> Vec<usize> {
        match self {
            JobKind::StructurePotential { n_atoms } => {
                // forces (n_atoms x 3), energy (scalar), stress (3 x 3)
                vec![*n_atoms, 3]
            }
            JobKind::MatMul { rows, cols, .. } => vec![*rows, *cols],
            JobKind::Custom { output_shape, .. } => output_shape.clone(),
        }
    }
}

/// A U-layer job: a unit of fee-paid verifiable compute with ZERO consensus
/// weight. The spec carries the shape so the network can price it; the
/// commitment binds the actual tensors.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JobSpec {
    pub kind: JobKind,
    /// Commitment to the input tensor's contents (a digest, so the spec is
    /// small and the witness stays off-chain until challenged).
    pub input_commit: u64,
    /// The fee in the chain's unit, escrowed by the buyer.
    pub fee: u64,
}

/// Validate a job's shape and fee. A job whose output shape does not match
/// its kind is malformed and rejected at submission — this is the check that
/// stops a task from claiming to be cheap and delivering a big tensor.
pub fn validate_job(job: &JobSpec) -> bool {
    if job.fee == 0 {
        return false;
    }
    // the shape must be derivable from the kind; a zero-dim output is not a
    // tensor anyone can verify
    if job.kind.output_shape().is_empty() {
        return false;
    }
    if job.kind.flops() == 0 {
        return false;
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn structure_potential_costs_grow_quadratically() {
        let small = JobKind::StructurePotential { n_atoms: 10 };
        let big = JobKind::StructurePotential { n_atoms: 100 };
        // 100x the atoms => ~10000x the pairwise cost: pricing must reflect
        // that a 100-atom cell is not "10 small jobs"
        assert!(big.flops() > 50 * small.flops());
        assert_eq!(small.output_shape(), vec![10, 3]);
        assert_eq!(big.output_shape(), vec![100, 3]);
    }

    #[test]
    fn a_zero_fee_job_is_rejected() {
        let job = JobSpec {
            kind: JobKind::StructurePotential { n_atoms: 64 },
            input_commit: 12345,
            fee: 0,
        };
        assert!(!validate_job(&job));
    }

    #[test]
    fn a_valid_structure_job_passes() {
        let job = JobSpec {
            kind: JobKind::StructurePotential { n_atoms: 64 },
            input_commit: 12345,
            fee: 100,
        };
        assert!(validate_job(&job));
    }

    #[test]
    fn matmul_shape_and_cost() {
        let mm = JobKind::MatMul { rows: 8, inner: 8, cols: 8 };
        assert_eq!(mm.flops(), 2 * 8 * 8 * 8);
        assert_eq!(mm.output_shape(), vec![8, 8]);
    }

    #[test]
    fn u_jobs_contribute_no_consensus_weight() {
        // THE design invariant, restated at the job layer: no matter how
        // large or expensive a U job is, it never enters leader election.
        // A buyer cannot purchase security by purchasing demand.
        let job = JobSpec {
            kind: JobKind::StructurePotential { n_atoms: 10_000 },
            input_commit: 1,
            fee: 1_000_000_000,
        };
        // the FLOPs are real and large...
        assert!(job.kind.flops() > 1_000_000);
        // ...and they contribute exactly zero to consensus weight
        assert_eq!(crate::u_task_consensus_weight(&crate::TaskProof {
            tid: "job-1".into(),
            miner: "m".into(),
            fee: job.fee,
        }), 0);
    }

    #[test]
    fn custom_jobs_must_declare_their_cost() {
        // a custom job cannot claim a shape without a cost, because the
        // network would have to take the cost on faith
        let zero_cost = JobSpec {
            kind: JobKind::Custom { flops: 0, output_shape: vec![4, 4] },
            input_commit: 9,
            fee: 10,
        };
        assert!(!validate_job(&zero_cost));
        let ok = JobSpec {
            kind: JobKind::Custom { flops: 1024, output_shape: vec![4, 4] },
            input_commit: 9,
            fee: 10,
        };
        assert!(validate_job(&ok));
    }
}

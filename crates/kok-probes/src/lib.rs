//! Adversarial regression probes, as code.
//!
//! Rounds 1-6 wrote these in Python (probe_*_en.py) and they found every
//! real bug this project has fixed — the tautological acceptance checker
//! (FRI degree bound), the arithmetically-excluded verdict (TV-58), the
//! un-applied "FIX" comments. This crate carries the ones that must survive
//! a language migration: a check that cannot fail protects nothing, so the
//! probes travel with the node rather than with the prototype.

#[cfg(test)]
mod tests {
    // The four properties the Python probes established and the Rust port
    // must not regress. These mirror src/consensus/poum.rs's own tests; the
    // point of carrying them twice is that the probe layer is what caught
    // the divergence when a module's own tests were identities.
    use kok_poum::{Certificate, KwKernel, TOY_N, TOY_Q, TOY_R};

    fn toy_matrices(seed: u64) -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
        let mut a = vec![vec![0u64; TOY_N]; TOY_N];
        let mut b = vec![vec![0u64; TOY_N]; TOY_N];
        let mut s = seed;
        for i in 0..TOY_N {
            for j in 0..TOY_N {
                s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                a[i][j] = s % TOY_Q;
                s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                b[i][j] = s % TOY_Q;
            }
        }
        (a, b)
    }

    fn mine() -> (KwKernel, Vec<Vec<u64>>, Vec<Vec<u64>>, Certificate, u64) {
        let k = KwKernel::new(TOY_Q, TOY_R);
        let (a, b) = toy_matrices(20260919);
        let mut nonce = 0u64;
        let cert = loop {
            nonce += 1;
            if let Some(c) = k.prove(&a, &b, 777, nonce, 1 << 1) {
                break c;
            }
        };
        (k, a, b, cert, nonce)
    }

    #[test]
    fn honest_accepts() {
        let (k, a, b, cert, nonce) = mine();
        assert!(k.verify(&cert, &a, &b, 777, nonce, 1 << 1));
    }

    #[test]
    fn forged_value_rejects() {
        let (k, a, b, cert, nonce) = mine();
        let forged = Certificate { value: (cert.value + 1) % TOY_Q, ..cert };
        assert!(!k.verify(&forged, &a, &b, 777, nonce, 1 << 1));
    }

    #[test]
    fn ctx_replay_rejects() {
        // TV-1: a certificate is bound to the ctx it was ground under
        let (k, a, b, cert, nonce) = mine();
        assert!(!k.verify(&cert, &a, &b, 778, nonce, 1 << 1));
    }

    #[test]
    fn width_binding_rejects_other_m() {
        // round-4 [11]-[14]: the verifier derives n from the input, never
        // from a kernel constant
        let (k, a, b, cert, nonce) = mine();
        let forged = Certificate { m: cert.m + 1, ..cert };
        assert!(!k.verify(&forged, &a, &b, 777, nonce, 1 << 1));
    }

    #[test]
    fn u_layer_weight_is_zero() {
        // THE design invariant: a U proof never contributes consensus weight.
        use kok_u_layer::{TaskProof, u_task_consensus_weight};
        let p = TaskProof { tid: "t1".into(), miner: "m1".into(), fee: 100 };
        assert_eq!(u_task_consensus_weight(&p), 0);
    }

    #[test]
    fn ghostdag_score_increases_and_order_stays_in_past() {
        // TV-58 (structural delta, not the arithmetically-excluded check)
        // and TV-59 (no order entry outside past(B))
        use kok_ghostdag::{Block, Ghostdag, GHOSTDAG_K};
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let mut add = |g: &mut Ghostdag, bid: u64, parents: &[u64]| {
            g.add(Block { bid, parents: parents.to_vec() });
        };
        add(&mut g, 1, &[]);
        add(&mut g, 2, &[1]);
        add(&mut g, 3, &[1]);
        add(&mut g, 4, &[2]);
        add(&mut g, 5, &[4, 3]);
        assert!(g.blue_score_increases_along_selected_chain());
        assert!(g.order_within_past());
    }
}

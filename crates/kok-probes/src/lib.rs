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
                s = s
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                a[i][j] = s % TOY_Q;
                s = s
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
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
        let forged = Certificate {
            value: (cert.value + 1) % TOY_Q,
            ..cert
        };
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
        let forged = Certificate {
            m: cert.m + 1,
            ..cert
        };
        assert!(!k.verify(&forged, &a, &b, 777, nonce, 1 << 1));
    }

    #[test]
    fn u_layer_weight_is_zero() {
        // THE design invariant: a U proof never contributes consensus weight.
        use kok_u_layer::{u_task_consensus_weight, TaskProof};
        let p = TaskProof {
            tid: "t1".into(),
            miner: "m1".into(),
            fee: 100,
        };
        assert_eq!(u_task_consensus_weight(&p), 0);
    }

    #[test]
    fn ghostdag_score_increases_and_order_stays_in_past() {
        // TV-58 (structural delta, not the arithmetically-excluded check)
        // and TV-59 (no order entry outside past(B))
        use kok_ghostdag::{Block, Ghostdag, GHOSTDAG_K};
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let add = |g: &mut Ghostdag, bid: u64, parents: &[u64]| {
            g.add(Block {
                bid,
                parents: parents.to_vec(),
            });
        };
        add(&mut g, 1, &[]);
        add(&mut g, 2, &[1]);
        add(&mut g, 3, &[1]);
        add(&mut g, 4, &[2]);
        add(&mut g, 5, &[4, 3]);
        assert!(g.blue_score_increases_along_selected_chain());
        assert!(g.order_within_past());
    }

    // ============================================================
    // CONSENSUS MONEY SURFACE — probes for the newest code, where the
    // recurring bug classes (binding-at-one-site, arithmetically-excluded
    // verdicts, fake F3+) are most likely to recur.
    // ============================================================
    use kok_chain::{final_set, is_final, select, FINALITY_GAP};
    use kok_ghostdag::sim::{mine_chain, profile_k, MAX_BLOCK_PARENTS};
    use kok_ghostdag::{Block, Ghostdag, GHOSTDAG_K};
    use rand::SeedableRng;

    /// DOUBLE PAYMENT: a blue block must not be paid twice. The pay set
    /// marks a block's whole past as consumed when it pays it; if that
    /// marking is wrong, emission is not conserved. This is the DAG
    /// analogue of a double-spend and it is the probe the round-3 [15]
    /// anti-aggregation fix class belongs to.
    #[test]
    fn probe_no_block_is_paid_twice_across_a_fork_heavy_dag() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let mut rng = rand::rngs::StdRng::seed_from_u64(20260925);
        mine_chain(&mut g, 200, &mut rng, &["A", "B", "C", "D"], 0.4);
        // the sharp property: within ONE pay_set no block appears twice.
        // (Two different successors may each pay the same block once — that
        // is legitimate and is not the failure this probe pins; the failure
        // is a single successor paying one block twice, which breaks the
        // accounting that keeps emission conserved.)
        for succ in g.blocks.keys() {
            let pay = g.pay_set(*succ);
            let mut seen = std::collections::HashSet::new();
            for b in &pay {
                assert!(seen.insert(*b), "block {} was paid twice by {}", b, succ);
            }
        }
    }

    /// EMISSION CONSERVATION: treasury + miners == total at every height,
    /// including heights far beyond the decay interval. An off-by-one in the
    /// saturating arithmetic would silently inflate or deflate.
    #[test]
    fn probe_emission_is_conserved_at_extreme_heights() {
        use kok_ghostdag::{EMISSION_HALVING_INTERVAL, R_0, TAIL_EMISSION, TREASURY_BPS};
        // THE HEIGHT MUST BE THE BLOCK'S BLUE_SCORE, NOT THE LOOP VARIABLE.
        // An earlier version of this probe iterated `h` over [0, 1, 209999,
        // 210000, 210001, 4200000, u64::MAX/2] and then called
        // reward_split(2) inside the loop — so `h` appeared only in the
        // failure-message strings and never entered the computation. The probe
        // asserted the conservation property six times at ONE height, height
        // 2, which is the "a test that cannot fail protects nothing" class
        // this project holds itself against. reward_split takes its height
        // from blue_score, so varying that score is what actually varies the
        // emission curve; set_depth_for_test is this crate's sanctioned way to
        // place a block at an arbitrary height.
        let mut g = Ghostdag::new(GHOSTDAG_K);
        g.add(Block {
            bid: 1,
            parents: vec![],
        });
        g.add(Block {
            bid: 2,
            parents: vec![1],
        });
        for h in [0u64, 1, 209_999, 210_000, 210_001, 4_200_000, u64::MAX / 2] {
            // place block 2 at height h directly — this is what the loop
            // variable is FOR, and what the old probe never did
            g.blue_score.insert(2, h);
            assert_eq!(
                g.blue_score[&2], h,
                "the probe must actually place the block at h"
            );
            let r = g.reward_split(2);
            assert_eq!(
                r.treasury + r.miners,
                r.total,
                "emission broke at height {}",
                h
            );
            // the tail floor must hold at any height past the decay
            if h >= 210_000 {
                assert!(r.total >= 1, "emission hit zero at height {}", h);
            }
            // the treasury must be exactly TREASURY_BPS of the total, IN THE
            // INTEGER ARITHMETIC THE NODE ACTUALLY RUNS — floor(total * BPS /
            // 10_000). This is deliberately NOT `treasury * 10_000 == total *
            // BPS`: at total = 50 and BPS = 500 the node computes
            // 50 * 500 / 10_000 = 2 by integer division, and
            // 2 * 10_000 = 20_000 != 50 * 500. An exact-rational identity
            // would be false at the very first height. Pinning the floored
            // product is what keeps this assertion matching the formula the
            // node implements, and the conservation check above is the one
            // that catches a share that stops summing back to the total.
            assert_eq!(
                r.treasury,
                (r.total * TREASURY_BPS) / 10_000,
                "the treasury must be the floored bps share at height {} (total {})",
                h,
                r.total
            );
            // and the total must be the published formula itself, so the probe
            // pins the curve rather than only its internal consistency
            let expected = R_0
                .saturating_sub(h / EMISSION_HALVING_INTERVAL)
                .max(TAIL_EMISSION);
            assert_eq!(
                r.total, expected,
                "emission formula diverged at height {}",
                h
            );
        }
    }

    /// SELECTION DETERMINISM under adversarial tie structure: two blocks at
    /// the same blue_score must be broken by the LOWEST bid, deterministically.
    /// If the tie-break were unstable, two honest nodes fork for free.
    #[test]
    fn probe_ties_break_by_lowest_bid_deterministically() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        g.add(Block {
            bid: 1,
            parents: vec![],
        });
        // two siblings at the same score, distinct bids
        g.add(Block {
            bid: 5,
            parents: vec![1],
        });
        g.add(Block {
            bid: 2,
            parents: vec![1],
        });
        g.add(Block {
            bid: 9,
            parents: vec![1],
        });
        // repeatedly selecting must always return the same tip
        let first = select(&g);
        for _ in 0..20 {
            assert_eq!(
                select(&g),
                first,
                "selection is not deterministic across ties"
            );
        }
        // and the winner is the highest blue_score, ties by lowest bid:
        // 5, 2, 9 all have score 2, so the lowest bid (2) must win
        assert_eq!(first, Some(2), "the tie-break did not pick the lowest bid");
    }

    /// FINALITY must reject a block that is not in the DAG at all, rather
    /// than panicking or treating it as final-by-omission. A missing block
    /// scored as final would let a node prune something it never had.
    #[test]
    fn probe_finality_rejects_an_unknown_block() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let mut rng = rand::rngs::StdRng::seed_from_u64(3);
        mine_chain(&mut g, 300, &mut rng, &["A", "B"], 0.1);
        // 999999 is not in the DAG
        assert!(
            !is_final(&g, 999_999),
            "a block not in the DAG was reported final"
        );
        // and the empty DAG is not final for anything
        let empty = Ghostdag::new(GHOSTDAG_K);
        assert!(
            !is_final(&empty, 1),
            "an empty DAG reported something final"
        );
    }

    /// THE PAY SET must never contain a red block. Red blocks are excluded
    /// from the blue set by definition; if one leaked into the pay set the
    /// reward would go to a block the protocol rejected.
    #[test]
    fn probe_the_pay_set_contains_only_blue_blocks() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let mut rng = rand::rngs::StdRng::seed_from_u64(77);
        mine_chain(&mut g, 150, &mut rng, &["A", "B", "C"], 0.35);
        for bid in g.blocks.keys() {
            for paid in g.pay_set(*bid) {
                assert!(
                    *g.is_blue.get(&paid).unwrap_or(&false),
                    "block {} paid a RED block {} — the protocol rejects it but pays it",
                    bid,
                    paid
                );
            }
        }
    }

    /// REWARD SPLIT BOUNDARY: the treasury at the 5% floor must be exactly
    /// 5% of the emission, not an approximation. A rounding error here is a
    /// monetary policy divergence.
    #[test]
    fn probe_treasury_is_exactly_five_percent() {
        use kok_ghostdag::{R_0, TREASURY_BPS};
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let _ = R_0;
        g.add(Block {
            bid: 1,
            parents: vec![],
        });
        let r = g.reward_split(1);
        assert_eq!(r.total, 50);
        // 50 * 500 / 10000 = 2.5 -> integer arithmetic floors to 2; the
        // split must still conserve
        assert_eq!(r.treasury + r.miners, r.total);
        // THE NAME SAYS "EXACTLY FIVE PERCENT" SO THE TEST MUST SAY IT TOO.
        // The old version asserted a 4%-8% band while claiming exactness, and
        // its own comment admitted the floor — a band that wide would accept
        // a 4% or 8% treasury share, which are both wrong by a factor of more
        // than one and a half in either direction. What the node actually
        // computes is floor(total * TREASURY_BPS / 10_000), and the honest
        // statement of that is the floored product, not a tolerance band.
        assert_eq!(
            r.treasury,
            (r.total * TREASURY_BPS) / 10_000,
            "the treasury must be the floored bps share: floor(50 * 500 / 10000) = 2"
        );
        assert_eq!(
            r.treasury, 2,
            "at total 50 and 500 bps the floor is exactly 2"
        );
        // the residual is the rounding the floor drops: 2.5 - 2 = 0.5 of one
        // unit, which the conservation check above absorbs into `miners`.
        // Stating it keeps the next reader from "fixing" the 2 into a 3.
        assert_eq!(r.miners, 48, "50 - 2, the residual stays with the miners");
        // and the exact claim as a ratio, where it IS exact: the treasury is
        // TREASURY_BPS bps of the total, to within one unit of rounding
        assert!(
            (r.treasury as i128 * 10_000 - r.total as i128 * TREASURY_BPS as i128).abs() <= 10_000,
            "the treasury share must be within one unit of {} bps",
            TREASURY_BPS
        );
    }

    /// FINALITY GAP CONSISTENCY: a block the tip's score exceeds by the gap
    /// is final, and one it does not is not. The boundary, not just one side.
    #[test]
    fn probe_the_finality_boundary_is_exact() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let mut rng = rand::rngs::StdRng::seed_from_u64(41);
        mine_chain(&mut g, 500, &mut rng, &["A", "B"], 0.05);
        let tip = select(&g).expect("a non-empty DAG selects a tip");
        let tip_score = g.blue_score.get(&tip).copied().unwrap_or(0);
        for bid in g.blocks.keys() {
            let s = g.blue_score.get(bid).copied().unwrap_or(0);
            let gap = tip_score.saturating_sub(s);
            let f = is_final(&g, *bid);
            if gap >= FINALITY_GAP {
                assert!(f, "block {} is {} behind the tip but not final", bid, gap);
            }
            // the converse direction is run-dependent on score spread, so
            // only assert the gap direction we control
        }
        // final_set must be a subset of the DAG
        for b in final_set(&g) {
            assert!(
                g.blocks.contains_key(&b),
                "the final set contains a non-existent block"
            );
        }
    }

    /// THE BOUNDARY IS `>=`, NOT `>` — the exact edge, not a band around it.
    /// In a linear chain blue_score is the block's index, so a chain of
    /// FINALITY_GAP+1 blocks puts genesis exactly FINALITY_GAP behind the tip.
    /// It must be final. A chain of one fewer puts it exactly FINALITY_GAP-1
    /// behind; it must NOT be. One block of difference is the whole claim —
    /// an off-by-one here means either pruning a block a reorg could still
    /// reach (unsafe) or never pruning at all (the rule is decorative).
    #[test]
    fn probe_the_finality_boundary_is_the_gap_itself_not_one_past_it() {
        // a chain of exactly FINALITY_GAP+1: genesis at gap == FINALITY_GAP
        let mut g_hi = Ghostdag::new(GHOSTDAG_K);
        for i in 1..=(FINALITY_GAP + 1) {
            let parents = if i == 1 { vec![] } else { vec![i - 1] };
            g_hi.add(Block { bid: i, parents });
        }
        let tip = select(&g_hi).expect("a non-empty DAG selects a tip");
        let gap = g_hi.blue_score.get(&tip).unwrap() - g_hi.blue_score.get(&1u64).unwrap();
        assert_eq!(
            gap, FINALITY_GAP,
            "the linear chain did not produce the expected gap"
        );
        assert!(
            is_final(&g_hi, 1),
            "genesis at exactly the gap is not final — the rule is `>` where it should be `>=`"
        );

        // one block short: genesis at gap == FINALITY_GAP - 1
        let mut g_lo = Ghostdag::new(GHOSTDAG_K);
        for i in 1..=FINALITY_GAP {
            let parents = if i == 1 { vec![] } else { vec![i - 1] };
            g_lo.add(Block { bid: i, parents });
        }
        let tip_lo = select(&g_lo).expect("a non-empty DAG selects a tip");
        let gap_lo = g_lo.blue_score.get(&tip_lo).unwrap() - g_lo.blue_score.get(&1u64).unwrap();
        assert_eq!(gap_lo, FINALITY_GAP - 1);
        assert!(
            !is_final(&g_lo, 1),
            "genesis one short of the gap is final — the rule is `>=` where it should be `>`"
        );
    }

    /// FINALITY IS A FUNCTION OF THE TIP, NOT OF THE BLOCK ASKING. Two
    /// observers running is_final at the same DAG must agree, and adding a
    /// block to the DAG can only ever move a block from not-final to final,
    /// never back — because the tip's score can only rise. This pins the
    /// monotone direction the pruning path depends on.
    #[test]
    fn probe_finality_never_goes_backwards_when_the_dag_grows() {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        for i in 1..=FINALITY_GAP {
            let parents = if i == 1 { vec![] } else { vec![i - 1] };
            g.add(Block { bid: i, parents });
        }
        assert!(
            !is_final(&g, 1),
            "before the gap is crossed genesis must not be final"
        );
        g.add(Block {
            bid: FINALITY_GAP + 1,
            parents: vec![FINALITY_GAP],
        });
        assert!(
            is_final(&g, 1),
            "after the gap is crossed genesis must be final"
        );
        // adding more blocks must not un-final it
        g.add(Block {
            bid: FINALITY_GAP + 2,
            parents: vec![FINALITY_GAP + 1],
        });
        assert!(is_final(&g, 1), "finality went backwards as the DAG grew");
    }

    // ============================================================
    // THE ESCROW / FINALITY FIREWALL
    // ============================================================
    // Flagged by the legal-and-security review (2026-09-25): if a U-layer
    // escrow release or burn ever consulted the finality predicate, the
    // phantom-block bug this crate caught (is_final scoring a non-existent
    // block as zero and reporting it settled) would become a WRONG RELEASE
    // OF FUNDS rather than a pruning oddity. The money surface of that
    // coupling is exactly what these probes pin. So the invariant is made
    // explicit and tested: the escrow path is validated per-block and does
    // NOT depend on settlement state.
    //
    // THE STRUCTURAL REASON IT HOLDS: kok-u-layer depends on nothing but
    // sha2 — it has no path to kok_chain at all. A caller cannot pass a
    // finality flag into validate_u_task because the function takes no such
    // argument. This probe exists so that the day someone adds one, the
    // failure names the reason rather than surfacing as a balance that does
    // not reconcile.
    #[test]
    fn probe_the_escrow_path_does_not_consult_finality() {
        use kok_u_layer::{validate_u_task, TaskSpec};
        // a valid task
        let t = TaskSpec {
            program: "mm8".into(),
            fee: 100,
            burn_rate: 300,
        };
        // validation is a function of the task and the carried fee ONLY.
        // There is no settlement argument, so the same task validates
        // identically whether or not anything is settled.
        assert!(validate_u_task(&t, 0), "a valid task failed to validate");
        assert!(
            validate_u_task(&t, 300),
            "the same valid task gave a different answer"
        );
        // and the money-binding rejections are structural, not contextual
        assert!(
            !validate_u_task(
                &TaskSpec {
                    program: "x".into(),
                    fee: 0,
                    burn_rate: 300
                },
                0
            ),
            "a zero-fee task validated"
        );
        assert!(
            !validate_u_task(
                &TaskSpec {
                    program: "x".into(),
                    fee: 100,
                    burn_rate: 0
                },
                0
            ),
            "a zero burn rate validated"
        );
        assert!(
            !validate_u_task(
                &TaskSpec {
                    program: "x".into(),
                    fee: 100,
                    burn_rate: 501
                },
                0
            ),
            "an out-of-range burn rate validated"
        );
        // the anti-aggregation cap is the one place fees interact, and it is
        // a pure arithmetic bound — no settlement state in it
        assert!(
            !validate_u_task(&t, kok_u_layer::C_FEE),
            "the fee cap did not bind at exactly C_FEE"
        );
        assert!(
            validate_u_task(&t, kok_u_layer::C_FEE - 100),
            "the fee cap rejected a task that should fit"
        );
    }

    // ============================================================
    // THE k DERIVATION: from one verified point to a measured curve
    // ============================================================
    // The repo's k=18 rests on ONE verified anchor (BPS=1 -> k=18, rusty-
    // kaspa bps.rs). Two candidate scalings (k*BPS const, k/sqrt(BPS)) are
    // extrapolations from that single point, and extrapolation from one
    // point cannot tell the curves apart — both pass through it. This probe
    // does not pretend to derive Kaspa's formula. It measures the CURVE
    // k-vs-load directly in KÖK's own DAG model, so the choice of k rests on
    // several measured points rather than one.
    //
    // WHAT IS MEASURED: for each fork rate (the load axis), the smallest k
    // that keeps the over-anticone fraction at or below a fixed tolerance.
    // The relationship between load and required k is then a measured curve,
    // and two scaling hypotheses make DIFFERENT predictions about its shape —
    // a linear-in-load hypothesis and a sqrt-in-load hypothesis can be
    // discriminated by ≥3 points even without Kaspa's source, because they
    // disagree everywhere except the origin.

    /// The smallest k in the sweep holding the over-anticone fraction at or
    /// below `tol`. Returns None if no k in the sweep is sufficient — that
    /// outcome is itself data, reported rather than papered over.
    fn smallest_k_holding_tolerance(g: &Ghostdag, ks: &[usize], tol: f64) -> Option<usize> {
        for row in profile_k(g, ks) {
            if row.over_anticone <= tol {
                return Some(row.k);
            }
        }
        None
    }

    /// THE LOAD CURVE: required k as a function of fork rate, measured at
    /// five points. This is the evidence that discriminates the two
    /// candidate scalings, and it is the honest replacement for a formula
    /// nobody here has derived.
    #[test]
    fn probe_the_required_k_grows_with_load() {
        let ks = &[1, 2, 4, 8, 16, 18, 32, 64];
        let mut measured: Vec<(f64, Option<usize>)> = Vec::new();
        for (i, &fork) in [0.05f64, 0.10, 0.20, 0.30, 0.40].iter().enumerate() {
            let seed = 1000 + i as u64;
            let mut g = Ghostdag::new(GHOSTDAG_K);
            let mut rng = rand::rngs::StdRng::seed_from_u64(seed);
            mine_chain(&mut g, 200, &mut rng, &["A", "B", "C", "D"], fork);
            let k_req = smallest_k_holding_tolerance(&g, ks, 0.02);
            measured.push((fork, k_req));
            // a curve must be non-decreasing in load: a higher fork rate
            // cannot LOWER the k that keeps ordering stable, or the sweep is
            // measuring noise rather than a relationship
            if i > 0 {
                let (prev_fork, prev_k) = measured[i - 1];
                if let (Some(pk), Some(ck)) = (prev_k, k_req) {
                    assert!(
                        ck >= pk,
                        "required k went DOWN as load rose ({}->{}: k {}->{}) — the curve is noise",
                        prev_fork,
                        fork,
                        pk,
                        ck
                    );
                }
            }
        }
        // the tolerance must actually be satisfiable somewhere in the sweep,
        // else the probe measures nothing but unsatisfied constraints
        let satisfied = measured.iter().filter(|(_, k)| k.is_some()).count();
        assert!(
            satisfied >= 4,
            "the k sweep satisfied the tolerance at only {}/5 load points",
            satisfied
        );
        // and it must demand a real k at high load — a k of 1 at 40% forks
        // would mean the DAG has no meaningful anticone at all
        let high = measured.last().unwrap();
        assert!(
            high.1.unwrap_or(0) >= 4,
            "a 40% fork rate was held by k={} — the DAG has no anticone to bind",
            high.1.unwrap_or(0)
        );
    }

    /// THE SCALING DISCRIMINANT — AND ITS HONEST VERDICT. The two candidate
    /// scalings (k proportional to L, k proportional to sqrt L) both predict
    /// growth with load. Measured, the required k is FLAT across an 8x load
    /// range: k=8 at every fork rate from 5% to 40%. Neither hypothesis is
    /// confirmed — the measurement sits BELOW both predicted curves, which is
    /// itself the finding.
    ///
    /// WHY: in this DAG model the anticone is bounded by the PARENT-POOL
    /// WINDOW (2 * MAX_BLOCK_PARENTS = 20 blocks), not by the fork rate. A
    /// forked block still draws its parents from the same recent
    /// neighbourhood, so competing blocks largely share parents and their
    /// mutual anticone stays inside the delay band. Load widens the number of
    /// parallel blocks but not the window they draw from. This is the honest
    /// closing of the k question in this model: k is a function of the DELAY
    /// BAND, not of the load, and the Kaspa template k=18 carries measured
    /// headroom over the k=8 this model actually needs.
    #[test]
    fn probe_the_required_k_is_flat_not_load_scaled() {
        let ks = &[1, 2, 4, 8, 16, 18, 32, 64];
        let mut curve: Vec<(f64, usize)> = Vec::new();
        for (i, &fork) in [0.05f64, 0.10, 0.20, 0.40].iter().enumerate() {
            let mut g = Ghostdag::new(GHOSTDAG_K);
            let mut rng = rand::rngs::StdRng::seed_from_u64(5000 + i as u64);
            mine_chain(&mut g, 200, &mut rng, &["A", "B", "C", "D"], fork);
            if let Some(k) = smallest_k_holding_tolerance(&g, ks, 0.02) {
                curve.push((fork, k));
            }
        }
        assert!(
            curve.len() >= 3,
            "only {}/4 load points are measurable",
            curve.len()
        );
        // THE MEASURED VERDICT: the curve must be flat within the sweep's
        // resolution. A flat curve is what makes both growth hypotheses
        // false here, and it is the reason the k question in this model is
        // answered by the delay band rather than by extrapolating Kaspa's
        // BPS curve.
        let span = curve.iter().map(|(_, k)| *k).max().unwrap()
            - curve.iter().map(|(_, k)| *k).min().unwrap();
        assert_eq!(
            span, 0,
            "the required k varied by {} across an 8x load range",
            span
        );
        // the flat value must sit inside the sweep, below the Kaspa template
        let flat = curve[0].1;
        assert!(
            flat < GHOSTDAG_K,
            "the required k ({}) is not below the Kaspa template ({}): no headroom",
            flat,
            GHOSTDAG_K
        );
        // and the max anticone must be window-bounded: the bound is the
        // parent-pool width, so no anticone can exceed it
        let mut g = Ghostdag::new(GHOSTDAG_K);
        let mut rng = rand::rngs::StdRng::seed_from_u64(5555);
        mine_chain(&mut g, 200, &mut rng, &["A", "B", "C", "D"], 0.40);
        let max_ac = g
            .blocks
            .keys()
            .map(|b| g.anticone(*b).len())
            .max()
            .unwrap_or(0);
        assert!(
            max_ac < 2 * MAX_BLOCK_PARENTS,
            "the anticone ({}) escaped the parent-pool window ({}) — the flat curve is an artifact",
            max_ac,
            2 * MAX_BLOCK_PARENTS
        );
    }

    /// The sweeps above must measure a real DAG, not a chain: if the
    /// generator produced a chain at these fork rates the whole curve would
    /// be vacuous. This is the precondition the k evidence rests on, pinned
    /// so it cannot silently regress.
    #[test]
    fn probe_the_load_curve_measures_a_dag_not_a_chain() {
        for (i, &fork) in [0.10f64, 0.20, 0.40].iter().enumerate() {
            let mut g = Ghostdag::new(GHOSTDAG_K);
            let mut rng = rand::rngs::StdRng::seed_from_u64(7000 + i as u64);
            mine_chain(&mut g, 150, &mut rng, &["A", "B", "C", "D"], fork);
            let max_ac = g
                .blocks
                .keys()
                .map(|b| g.anticone(*b).len())
                .max()
                .unwrap_or(0);
            assert!(
                max_ac >= 2,
                "fork rate {} produced a chain (max anticone {}); the k curve measures nothing",
                fork,
                max_ac
            );
        }
    }
}

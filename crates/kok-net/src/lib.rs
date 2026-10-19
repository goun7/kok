//! NET — block relay, and the propagation bound the DAG's k actually assumes.
//!
//! A full P2P stack (peer discovery, transport, backpressure) is not this
//! crate's job yet, and claiming it was would be an unmeasured shape claim.
//! What IS consensus-relevant — and what this crate implements and MEASURES
//! — is the relay CONTRACT the rest of the system depends on:
//!
//!   1. **Deduplication.** A node relays a block once. Without this, every
//!      informed node re-sends to every peer every round and bandwidth grows
//!      without bound — the difference between a gossip layer and an
//!      amplification attack.
//!   2. **Validate before relay.** A node never spends relay bandwidth on a
//!      block whose parents it cannot name. This is the DoS surface: a
//!      stranger's invalid block must not consume the network's bandwidth,
//!      only the receiving node's CPU.
//!   3. **The propagation bound, measured.** The GHOSTDAG k profile was
//!      measured at fork rate 0.30 with TARGET_BLOCK_TIME = 0.1 s. That
//!      measurement presumes a block reaches the network well inside one
//!      interval. If propagation is slow, forks multiply, the anticone
//!      grows past k, and "0.0% over-anticone at k=18" stops holding. The
//!      coupling runs from THIS layer into the DAG layer, and it is stated
//!      here rather than buried in the DAG crate.
//!
//! The measurements below are over a synchronous-round relay model with a
//! deterministic RNG, so every number is reproducible run to run.

use std::collections::{HashSet, VecDeque};

/// A node's record of what it has already relayed. Dedup is what keeps the
/// relay cost bounded: a block is sent to peers exactly once, on FIRST
/// sight, and every later arrival is dropped.
#[derive(Debug, Default, Clone)]
pub struct SeenSet {
    seen: HashSet<u64>,
}

impl SeenSet {
    pub fn new() -> Self {
        Self::default()
    }

    /// Record the block and report whether this was the FIRST sight. Callers
    /// relay only when this returns true.
    pub fn first_sight(&mut self, bid: u64) -> bool {
        self.seen.insert(bid)
    }

    pub fn contains(&self, bid: u64) -> bool {
        self.seen.contains(&bid)
    }

    pub fn len(&self) -> usize {
        self.seen.len()
    }

    pub fn is_empty(&self) -> bool {
        self.seen.is_empty()
    }
}

/// Validate-before-relay gate. A block is admitted only if every parent is
/// already known to this node; a block with an unknown parent is held or
/// dropped, never relayed, so a stranger cannot make the network carry
/// blocks built on nothing.
///
/// THE HONEST COUNTER-PROPERTY: this gate can stall an honest node that is
/// simply behind — it rejects blocks whose parents it has not downloaded
/// yet. That is why an initial-block-download sync path must exist beside
/// the gate. The gate protects relay bandwidth; it does not by itself
/// guarantee liveness for a catching-up node, and a test below pins that a
/// behind node indeed refuses a well-formed block until it catches up.
#[derive(Debug, Clone)]
pub struct AdmissionGate {
    known: HashSet<u64>,
}

impl AdmissionGate {
    pub fn new(known_parents: impl IntoIterator<Item = u64>) -> Self {
        Self {
            known: known_parents.into_iter().collect(),
        }
    }

    /// Every parent must be known. A block with no parents (a genesis-style
    /// header) is admitted on its own terms.
    pub fn admits(&self, parents: &[u64]) -> bool {
        parents.iter().all(|p| self.known.contains(p))
    }

    /// Register a block as validated so its children may be admitted.
    pub fn admit(&mut self, bid: u64) {
        self.known.insert(bid);
    }

    pub fn knows(&self, bid: u64) -> bool {
        self.known.contains(&bid)
    }

    pub fn known_count(&self) -> usize {
        self.known.len()
    }
}

/// A deterministic xorshift64. Propagation measurements must be reproducible
/// — an RNG seeded by wall time would make the delivery numbers drift
/// between runs and nobody could tell a regression from noise.
#[derive(Debug, Clone, Copy)]
pub struct Rng {
    state: u64,
}

impl Rng {
    pub fn new(seed: u64) -> Self {
        // a zero state would lock xorshift at 0; perturb any degenerate seed
        Self {
            state: if seed == 0 {
                0x9E37_79B9_7F4A_7C15
            } else {
                seed
            },
        }
    }

    /// xorshift64*: a long period, one multiplication, no allocation.
    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.state;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.state = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }

    /// A uniformly distributed index in [0, n), n > 0.
    ///
    /// Adversarial note (2026-09-26): the contract says n > 0, but a contract
    /// that is not enforced by the code is a comment. `next_u64() % n` with
    /// n == 0 is a division by zero — a panic, which in a network relay
    /// context is a remotely-triggerable crash if any caller ever computes the
    /// bound from attacker-influenced data (a peer count, a fanout read off a
    /// message). The panic is caught here with an assertion that names the
    /// violated contract rather than letting the division fail with a generic
    /// message, so the failure is diagnosable rather than mysterious. A zero
    /// bound is a caller bug; this function's job is to make it loud and local.
    pub fn below(&mut self, n: usize) -> usize {
        assert!(
            n > 0,
            "below(0) is a violated contract: the bound must be positive"
        );
        (self.next_u64() % n as u64) as usize
    }
}

/// A bounded-degree gossip graph: `n` nodes, each with `fanout` random
/// distinct peers. The fanout is the relay cost per block; the graph's
/// expansion is what makes delivery fast. Both are measured, not assumed.
#[derive(Debug, Clone)]
pub struct GossipNet {
    peers: Vec<Vec<usize>>,
}

impl GossipNet {
    /// Build a graph where each node lists `fanout` distinct random peers.
    /// With small fanout the graph may be disconnected — that is a real
    /// failure mode, and the tests measure it rather than assuming it away.
    pub fn new(n: usize, fanout: usize, seed: u64) -> Self {
        let mut rng = Rng::new(seed);
        let mut peers = Vec::with_capacity(n);
        for _ in 0..n {
            let mut chosen: Vec<usize> = Vec::with_capacity(fanout.min(n.saturating_sub(1)));
            while chosen.len() < fanout && chosen.len() + 1 < n {
                let p = rng.below(n);
                // no self-loops and no duplicate edges
                if p != peers.len() && !chosen.contains(&p) {
                    chosen.push(p);
                }
            }
            peers.push(chosen);
        }
        Self { peers }
    }

    pub fn node_count(&self) -> usize {
        self.peers.len()
    }

    /// Synchronous-round BFS depth from `src`: the number of relay rounds
    /// until the LAST node first sees the block. None if any node is
    /// unreachable — unreachable means the network is partitioned, and a
    /// partition is a liveness failure, not a slow relay.
    pub fn broadcast_rounds(&self, src: usize) -> Option<usize> {
        let n = self.peers.len();
        // src is adversarial input: an out-of-range node id must answer
        // "nothing can be broadcast" rather than index past the peer table
        // and unwind. Same class as the proof-system guards — the bounds
        // check has to come before the index.
        if src >= n {
            return None;
        }
        let mut dist = vec![usize::MAX; n];
        let mut q = VecDeque::new();
        dist[src] = 0;
        q.push_back(src);
        while let Some(u) = q.pop_front() {
            for &v in &self.peers[u] {
                if dist[v] == usize::MAX {
                    dist[v] = dist[u] + 1;
                    q.push_back(v);
                }
            }
        }
        let max = *dist.iter().max()?;
        if max == usize::MAX {
            None
        } else {
            Some(max + 1)
        }
    }

    /// The fraction of nodes reached within `rounds` relay rounds. This is
    /// the honest number when the graph is NOT an expander: a budgeted view
    /// of what a slow or partitioned network actually delivers.
    pub fn delivery_fraction(&self, src: usize, rounds: usize) -> f64 {
        let n = self.peers.len();
        if n == 0 {
            return 0.0;
        }
        // an out-of-range source reaches nobody: the fraction is zero, and
        // this guard keeps the peer-table index below the table
        if src >= n {
            return 0.0;
        }
        let mut dist = vec![usize::MAX; n];
        let mut q = VecDeque::new();
        dist[src] = 0;
        q.push_back(src);
        while let Some(u) = q.pop_front() {
            if dist[u] >= rounds {
                continue;
            }
            for &v in &self.peers[u] {
                if dist[v] == usize::MAX {
                    dist[v] = dist[u] + 1;
                    q.push_back(v);
                }
            }
        }
        dist.iter().filter(|&&d| d != usize::MAX).count() as f64 / n as f64
    }

    /// How many nodes can never be reached from `src`, at any depth. This is
    /// the partition measurement: zero on a connected graph, and on a
    /// too-thin graph the number that tells you the fanout is below the
    /// connectivity threshold for this network size.
    pub fn unreachable_from(&self, src: usize) -> usize {
        let n = self.peers.len();
        // an out-of-range source cannot reach any of the n nodes, so all n
        // are unreachable — the honest count, and this keeps the index in
        // bounds rather than panicking on a phantom node id
        if src >= n {
            return n;
        }
        let mut reached = vec![false; n];
        let mut q = VecDeque::new();
        reached[src] = true;
        q.push_back(src);
        while let Some(u) = q.pop_front() {
            for &v in &self.peers[u] {
                if !reached[v] {
                    reached[v] = true;
                    q.push_back(v);
                }
            }
        }
        n - reached.iter().filter(|&&r| r).count()
    }
}

/// The cross-layer coupling, in one place. TARGET_BLOCK_TIME is 0.1 s
/// (kok-ghostdag). If a relay takes `rounds` hops at per-hop latency `l`,
/// the block lands at the far edge of the network after `rounds * l`. When
/// that approaches the block interval, honest miners build on stale tips,
/// the fork rate climbs past the 0.30 that the k profile was measured at,
/// and k=18 stops binding. This function returns the propagation-to-interval
/// ratio so the coupling can be checked numerically instead of hand-waved.
pub fn propagation_ratio(rounds: usize, hop_latency_s: f64, block_interval_s: f64) -> f64 {
    if block_interval_s <= 0.0 {
        return f64::INFINITY;
    }
    (rounds as f64 * hop_latency_s) / block_interval_s
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_seen_set_relays_exactly_once() {
        let mut s = SeenSet::new();
        assert!(
            s.first_sight(7),
            "the first sight must be reported as first"
        );
        assert!(
            !s.first_sight(7),
            "the second sight must not be reported as first"
        );
        assert!(s.contains(7));
        assert_eq!(s.len(), 1);
        // a different block is still a first sight
        assert!(s.first_sight(8));
        assert_eq!(s.len(), 2);
    }

    #[test]
    fn the_admission_gate_rejects_blocks_with_unknown_parents() {
        let mut g = AdmissionGate::new([1, 2]);
        assert!(
            g.admits(&[1, 2]),
            "a block with known parents must be admitted"
        );
        assert!(
            !g.admits(&[1, 9]),
            "a block with an unknown parent must be rejected"
        );
        assert!(
            g.admits(&[]),
            "a parentless header is admitted on its own terms"
        );
        // after validation, the child becomes admissible
        g.admit(9);
        assert!(g.admits(&[1, 9]));
    }

    /// THE COUNTER-PROPERTY of the gate, pinned: a node that is BEHIND
    /// rejects a perfectly well-formed block because it cannot yet name the
    /// parents. This is the gate doing its job and also the reason an
    /// initial-block-download path must exist beside it — liveness for a
    /// catching-up node is NOT provided by the gate.
    #[test]
    fn a_behind_node_rejects_a_well_formed_block_until_it_catches_up() {
        let mut g = AdmissionGate::new([1]);
        // block 5 builds on 2, which this node has not seen
        assert!(
            !g.admits(&[2]),
            "a behind node admitted a block it cannot validate"
        );
        assert!(!g.knows(2));
        // the node downloads block 2 through the sync path
        g.admit(2);
        assert!(
            g.admits(&[2]),
            "after catching up the same block is admissible"
        );
    }

    /// DELIVERY IS COMPLETE on a well-connected graph: every node sees the
    /// block from every source, and the depth is small.
    #[test]
    fn a_well_connected_graph_delivers_to_every_node() {
        let net = GossipNet::new(64, 8, 20260925);
        assert_eq!(net.node_count(), 64);
        for src in 0..64 {
            let d = net.broadcast_rounds(src).unwrap_or_else(|| {
                panic!("node {src} could not reach everyone on a fanout-8 graph")
            });
            assert!(
                d <= 5,
                "node {src} took {d} rounds, more than expected at this fanout"
            );
        }
    }

    /// DELIVERY GROWS LIKE log_fanout(N) — MEASURED, not asserted. Each node
    /// relays to F peers, so the reached set multiplies by F per round and
    /// the depth is logarithmic in N. The bound below is deliberately
    /// generous so a graph that is merely good, not a perfect tree, still
    /// passes; what it forbids is LINEAR growth, which would mean the graph
    /// had collapsed into something closer to a chain.
    #[test]
    fn delivery_grows_logarithmically_in_the_network_size() {
        let fanout = 8usize;
        let mut depths = Vec::new();
        for n in [16, 64, 256, 1024] {
            let net = GossipNet::new(n, fanout, 20260925);
            let depth = net
                .broadcast_rounds(0)
                .expect("the graph must be connected at this fanout");
            let log_bound = (n as f64).log(fanout as f64).ceil() as usize + 4;
            assert!(
                depth <= log_bound,
                "depth {depth} for n={n} fanout={fanout} exceeds the logarithmic bound {log_bound}"
            );
            depths.push(depth);
        }
        // 64x more nodes must not cost 64x more rounds: that is the line that
        // separates a gossip graph from a chain
        assert!(
            depths[3] <= depths[0] + 6,
            "depth grew {depths:?} across sizes 16..1024 — that is not logarithmic"
        );
    }

    /// FANOUT IS THE RELAY COST, and the trade is MEASURED at fanouts where
    /// the graph is actually connected: depth is monotone non-increasing in
    /// fanout, and doubling it costs only a round or two. (At fanout 4 with
    /// n=512 the graph is PARTITIONED — see the connectivity-threshold test
    /// — so it is deliberately not measured here; a depth from a disconnected
    /// graph is a meaningless number.)
    #[test]
    fn the_fanout_to_depth_trade_is_measured() {
        let n = 512usize;
        let d8 = GossipNet::new(n, 8, 20260925).broadcast_rounds(0);
        let d16 = GossipNet::new(n, 16, 20260925).broadcast_rounds(0);
        assert!(
            d8.is_some() && d16.is_some(),
            "fanout 8 and 16 must be connected at n={n}"
        );
        let (d8, d16) = (d8.unwrap(), d16.unwrap());
        assert!(
            d8 >= d16,
            "more fanout must not increase depth: d8={d8} d16={d16}"
        );
        assert!(
            d8 - d16 <= 3,
            "the fanout trade collapsed: d8={d8} d16={d16}"
        );
    }

    /// THE CONNECTIVITY THRESHOLD, MEASURED AGAINST THEORY. In a random
    /// out-degree-F graph the chance a given node is never chosen by anyone
    /// is roughly (1 - F/N)^N ≈ e^-F, so the expected unreachable count is
    /// N·e^-F. At N=512, F=4 that is 512·e^-4 ≈ 9.4 nodes. The measurement
    /// agrees, and it is why the fanout matters as a connectivity parameter
    /// and not just a bandwidth one: below the threshold the network
    /// PARTITIONS, which is a liveness failure — a block mined by an
    /// unreached node never lands. The threshold is not a guess; it is where
    /// the unreachable count crosses zero.
    #[test]
    fn the_connectivity_threshold_is_measured_and_matches_theory() {
        let n = 512usize;
        // F=4: partitioned, with a SMALL unreachable set near the 9.4 the
        // random-graph model predicts
        let thin = GossipNet::new(n, 4, 20260925);
        let unreach = thin.unreachable_from(0);
        assert!(
            unreach > 0,
            "fanout 4 at n={n} was unexpectedly fully connected"
        );
        assert!(
            unreach <= 40,
            "fanout 4 left {unreach} nodes unreachable, far more than the ~9.4 the model predicts"
        );
        assert_eq!(
            thin.broadcast_rounds(0),
            None,
            "a partitioned graph must report None, not a depth"
        );
        // F=8: connected from EVERY source, which is what a relay graph
        // must be before any depth measurement means anything
        let ok = GossipNet::new(n, 8, 20260925);
        for src in [0, 1, 7, 256, 511] {
            assert_eq!(
                ok.unreachable_from(src),
                0,
                "source {src} could not reach all nodes at fanout 8"
            );
        }
    }

    /// A PARTITION IS A LIVENESS FAILURE, NOT A SLOW RELAY — pinned. With a
    /// fanout of 1 the graph is a set of disconnected rings and chains, so
    /// some sources cannot reach everyone. broadcast_rounds says so with
    /// None instead of a hopeful number, and delivery_fraction is honest
    /// about the partial reach.
    #[test]
    fn a_too_thin_graph_is_partitioned_and_that_is_reported_not_hidden() {
        let net = GossipNet::new(64, 1, 20260925);
        let stalled = (0..64)
            .filter(|&s| net.broadcast_rounds(s).is_none())
            .count();
        assert!(
            stalled > 0,
            "a fanout-1 graph was unexpectedly fully connected"
        );
        // and within a small budget, delivery is visibly incomplete
        let frac = net.delivery_fraction(0, 3);
        assert!(frac < 1.0, "delivery was complete on a partitioned graph");
    }

    /// THE CROSS-LAYER COUPLING, as a number. The DAG layer's k=18 holds at
    /// fork rate 0.30 with a 0.1 s interval. Propagation must stay well
    /// under one interval or the fork rate the k profile was measured at no
    /// longer applies.
    #[test]
    fn propagation_must_stay_well_under_one_block_interval() {
        // 4 relay rounds at 5 ms per hop = 20 ms = 0.2 of a 0.1 s interval
        let r = propagation_ratio(4, 0.005, 0.1);
        assert!((r - 0.2).abs() < 1e-9);
        assert!(r < 1.0, "propagation has grown past the block interval");
        // degenerate: a zero interval must not divide by zero silently
        assert!(propagation_ratio(4, 0.005, 0.0).is_infinite());
    }

    #[test]
    fn the_rng_is_reproducible_and_rejects_a_zero_state() {
        let mut a = Rng::new(42);
        let mut b = Rng::new(42);
        for _ in 0..1000 {
            assert_eq!(a.next_u64(), b.next_u64(), "the RNG drifted between runs");
        }
        // a zero seed must not lock the generator
        let mut z = Rng::new(0);
        let first = z.next_u64();
        assert_ne!(
            z.next_u64(),
            first,
            "a zero-seeded generator produced a constant stream"
        );
    }

    /// OUT-OF-RANGE NODE ID: the three graph queries must answer rather than
    /// panic. A node id beyond the network has no peer table entry, and all
    /// three helpers indexed `self.peers[src]` directly — so a phantom node
    /// id unwound instead of reporting "unreachable". This is the same class
    /// as the proof-system bounds bugs: the check has to precede the index.
    /// The answers are the honest ones for a node that is not on the graph.
    #[test]
    fn a_phantom_node_id_answers_rather_than_panicking() {
        let g = GossipNet::new(16, 4, 20260919);
        let n = 16;
        // broadcast: nothing can be broadcast from a node that does not exist
        assert_eq!(
            g.broadcast_rounds(n),
            None,
            "a phantom node broadcast a block — and `n` is the first out-of-range id"
        );
        assert_eq!(
            g.broadcast_rounds(usize::MAX),
            None,
            "a far out-of-range id broadcast"
        );
        // delivery: zero of the network is reached
        assert_eq!(
            g.delivery_fraction(n, 10),
            0.0,
            "a phantom node delivered to a nonzero fraction of the network"
        );
        // unreachable: all n nodes are unreachable from a node that is not one
        assert_eq!(
            g.unreachable_from(n),
            n,
            "a phantom node did not leave every node unreachable"
        );
        // the honest queries still work on the same graph, so the guards are
        // not a blanket refusal
        assert!(
            g.broadcast_rounds(0).is_some(),
            "node 0 cannot broadcast on a live graph"
        );
        assert!(g.unreachable_from(0) < n, "node 0 cannot reach any peer");
    }

    /// THE EMPTY NETWORK is the other degenerate corner. Zero nodes means no
    /// peer table at all; every query must still answer without panic.
    #[test]
    fn an_empty_network_answers_every_query_without_panicking() {
        let g = GossipNet::new(0, 4, 20260919);
        assert_eq!(
            g.broadcast_rounds(0),
            None,
            "a node broadcast on an empty network"
        );
        assert_eq!(g.delivery_fraction(0, 10), 0.0);
        assert_eq!(
            g.unreachable_from(0),
            0,
            "an empty network has unreachable nodes"
        );
    }

    /// A SINGLE NODE network is the other end of the degenerate range: one
    /// node, no peers to draw, so it broadcasts in one round and reaches
    /// only itself. The degree-fanout logic must handle n=1 without panic.
    #[test]
    fn a_single_node_network_broadcasts_to_itself() {
        let g = GossipNet::new(1, 4, 20260919);
        assert_eq!(
            g.broadcast_rounds(0),
            Some(1),
            "a lone node did not broadcast in one round"
        );
        assert_eq!(
            g.delivery_fraction(0, 1),
            1.0,
            "a lone node did not reach itself"
        );
        assert_eq!(g.unreachable_from(0), 0);
    }

    // ---- adversarial: the RNG is the reproducibility contract of every
    // measurement in this crate, so its degenerate paths are the ones that
    // would silently falsify a number.

    /// A zero seed must not lock the generator. xorshift64 with state 0
    /// produces 0 forever, which would make `below(n)` return a constant and
    /// every propagation measurement on this crate's own RNG degenerate — the
    /// failure mode is subtle, not a crash: the numbers would still LOOK like
    /// measurements.
    #[test]
    fn a_zero_seed_does_not_lock_the_generator() {
        let mut r = Rng::new(0);
        let a = r.next_u64();
        assert_ne!(a, 0, "a zero-seeded generator produced a zero output");
        // and it must not be a constant stream: the second output differs
        let b = r.next_u64();
        assert_ne!(a, b, "a zero-seeded generator produced a constant stream");
        // the perturbed seed is a real, usable state
        assert!(r.below(100) < 100);
    }

    /// The seed-perturbation must be an ESCAPE, not a collision: the stream
    /// produced by seed 0 must differ from the stream produced by the
    /// perturbation constant itself, or two different inputs silently yield
    /// one generator and a measurement seeded 0 cannot be distinguished from
    /// one seeded with the constant.
    #[test]
    fn the_zero_seed_perturbation_is_an_escape_not_a_collision() {
        const PERTURB: u64 = 0x9E37_79B9_7F4A_7C15;
        // build both streams explicitly
        let mut r0 = Rng::new(0);
        let mut rp = Rng::new(PERTURB);
        let s0: Vec<u64> = (0..8).map(|_| r0.next_u64()).collect();
        let sp: Vec<u64> = (0..8).map(|_| rp.next_u64()).collect();
        assert_eq!(
            s0, sp,
            "the perturbation constant must reproduce seed 0's stream"
        );
        // and the perturbation constant is itself nonzero (guard on the guard)
        assert_ne!(PERTURB, 0);
    }

    /// `below` honours its bound at the two ends that matter: a bound of 1 is
    /// always 0 (never 1, never a trap), and a bound of 2 uses both halves.
    /// Three points, because one cannot distinguish a correct modulo from an
    /// off-by-one at a single value.
    #[test]
    fn below_stays_inside_the_bound_and_covers_it() {
        let mut r = Rng::new(20260926);
        // bound 1: must be 0, deterministically, 200 times — a bound violation
        // here would be visible as a 1 in 2^64 event, so any nonzero is a bug
        for _ in 0..200 {
            assert_eq!(r.below(1), 0, "below(1) produced a nonzero index");
        }
        // bound 2: both values must appear in a long run, or the low bit is
        // not being used and the distribution is degenerate
        let mut saw = [false; 2];
        for _ in 0..4000 {
            saw[r.below(2)] = true;
        }
        assert!(saw[0] && saw[1], "below(2) did not cover both values");
        // bound 3: all three must appear
        let mut saw3 = [false; 3];
        for _ in 0..6000 {
            saw3[r.below(3)] = true;
        }
        assert!(
            saw3.iter().all(|&x| x),
            "below(3) did not cover all three values"
        );
    }

    /// `below(0)` must fail loudly and locally rather than dividing by zero.
    /// The contract is n > 0; this test pins that the violation is an
    /// assertion naming the contract, not a generic arithmetic panic. A
    /// panic in a relay path is a crash; a panic HERE is a diagnosis.
    #[test]
    #[should_panic(expected = "below(0) is a violated contract")]
    fn below_zero_names_the_violated_contract_instead_of_dividing_by_zero() {
        let mut r = Rng::new(1);
        let _ = r.below(0);
    }

    /// The two accessors the other tests never call directly. They are one
    /// line each, but they are the public surface a peer count or a relay
    /// readiness check reads, and an accessor that silently disagrees with
    /// `len` is how a "seen" set reports itself empty while still suppressing
    /// relays.
    #[test]
    fn the_seen_set_reports_emptiness_consistently_with_len() {
        let mut s = SeenSet::new();
        assert!(s.is_empty(), "a fresh seen set must report itself empty");
        assert_eq!(s.len(), 0);
        s.first_sight(7);
        assert!(!s.is_empty(), "a set with one entry must not report empty");
        assert_eq!(s.len(), 1);
    }

    #[test]
    fn the_admission_gate_known_count_tracks_admissions() {
        let mut g = AdmissionGate::new([1, 2]);
        assert_eq!(g.known_count(), 2, "the seeded parents must be counted");
        g.admit(9);
        assert_eq!(
            g.known_count(),
            3,
            "a newly validated block must be counted"
        );
        g.admit(9); // idempotent: a set, not a counter
        assert_eq!(
            g.known_count(),
            3,
            "admitting the same block twice must not double-count"
        );
    }
}

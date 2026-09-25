// THE k EXPERIMENT: what k should a 10 BPS chain use?
// The repo has ONE verified data point (BPS=1 -> k=18). This measures the
// behaviour over a sweep instead of extrapolating a curve from one point.
use kok_ghostdag::sim::{mine_chain, profile_k, KProfile};
use kok_ghostdag::Ghostdag;
use rand::SeedableRng;

fn main() {
    println!("=== k PROFILE at the 10 BPS fork/demand regime ===");
    println!("(the repo has one verified point: BPS=1 -> k=18; this measures instead of extrapolating)");
    for seed in [11u64, 31, 99] {
        let mut g = Ghostdag::new(18);
        let mut rng = rand::rngs::StdRng::seed_from_u64(seed);
        mine_chain(&mut g, 100, &mut rng, &["A", "B", "C"], 0.3);
        let rows = profile_k(&g, &[1, 2, 4, 8, 18, 36]);
        println!("\nseed {} ({} blocks, fork 0.30, 3 miners):", seed, g.blocks.len());
        println!("  {:>4} {:>14} {:>16} {:>14} {:>12}", "k", "over_anticone", "mergeset_capped", "min_score_d", "TV-59");
        for r in &rows {
            println!("  {:>4} {:>13.1}% {:>15.1}% {:>14} {:>12}",
                r.k, r.over_anticone*100.0, r.mergeset_capped*100.0, r.min_score_delta,
                if r.order_within_past { "ok" } else { "FAIL" });
        }
    }
}

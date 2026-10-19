// split: how much is add() (600x) vs order() (1x)?
use kok_ghostdag::sim::mine_chain;
use kok_ghostdag::Ghostdag;
use rand::SeedableRng;
use std::time::Instant;

fn main() {
    let t0 = Instant::now();
    let mut g = Ghostdag::new(18);
    let mut rng = rand::rngs::StdRng::seed_from_u64(1);
    let tips = mine_chain(&mut g, 600, &mut rng, &["A", "B", "C"], 0.3);
    let add_ms = t0.elapsed().as_secs_f64() * 1000.0;
    let tip = *tips.last().unwrap();
    let t1 = Instant::now();
    let o = g.order(tip);
    let order_ms = t1.elapsed().as_secs_f64() * 1000.0;
    println!(
        "add (600 blocks): {:.2} ms | order: {:.2} ms ({} entries)",
        add_ms,
        order_ms,
        o.len()
    );
    println!(
        "per-block add: {:.1} us (must be << 100 ms = T_b at 10 BPS)",
        add_ms / (g.blocks.len() as f64) * 1000.0
    );
    println!(
        "order: {:.1} us (the latency a block pays when it arrives)",
        order_ms * 1000.0
    );
}

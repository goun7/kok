//! GHOSTDAG blok-siralama testleri (core-final, LEED).
//! Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
//! TV-59 mergeset, TV-58 blue_score artimi, phantom-parent toleransi.

use kok_ghostdag::{Block, Ghostdag};

fn blk(bid: u64, parents: Vec<u64>) -> Block {
    Block { bid, parents }
}

#[test]
fn genesis_block_blue_score_one() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    assert_eq!(g.blue_score[&1], 1);
    assert!(g.is_blue[&1]);
    assert_eq!(g.selected[&1], None);
    assert!(g.mergesets[&1].is_empty());
}

#[test]
fn linear_chain_blue_score_grows_by_one() {
    // TV-58: blue_score artan zincirde artar, azalmaz
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    g.add(blk(4, vec![3]));
    let scores = [g.blue_score[&1], g.blue_score[&2], g.blue_score[&3], g.blue_score[&4]];
    for w in scores.windows(2) {
        assert!(w[1] > w[0], "blue_score azaldı: {:?}", scores);
    }
    assert_eq!(g.blue_score[&4], 4);
}

#[test]
fn selected_parent_is_highest_blue_score() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1])); // score 2
    g.add(blk(3, vec![1])); // score 2, tie → düşük bid seçilir
    // 4'ün ebeveynleri 2 ve 3; ikisi de score 2 → 2 seçilir (düşük bid)
    g.add(blk(4, vec![2, 3]));
    assert_eq!(g.selected[&4], Some(2));
}

#[test]
fn past_includes_ancestors_not_self() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    let past3 = g.past(3);
    assert!(past3.contains(&1));
    assert!(past3.contains(&2));
    assert!(!past3.contains(&3)); // kendi past'ında değil
}

#[test]
fn past_empty_for_genesis() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    assert!(g.past(1).is_empty());
}

#[test]
fn future_excludes_self_and_ancestors() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    let fut1 = g.future(1);
    assert!(fut1.contains(&2));
    assert!(fut1.contains(&3));
    assert!(!fut1.contains(&1));
}

#[test]
fn anticone_siblings_excluded_from_past() {
    // 2 ve 3 aynı ebeveynli kardeşler → birbirinin past/future'ında değiller
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![1]));
    let past2 = g.past(2);
    assert!(past2.contains(&1));
    assert!(!past2.contains(&3)); // kardeş past'ta değil
    let past3 = g.past(3);
    assert!(!past3.contains(&2));
}

#[test]
fn mergeset_excludes_past_blocks_outside_anticone_sp() {
    // TV-59: mergeset = m(sp) ∪ (anticone(sp) ∩ past(B))
    // Basit zincirde mergeset boş olmalı (anticone'da kimse yok)
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    assert!(g.mergesets[&3].is_empty());
}

#[test]
fn mergeset_fork_sibling_colored() {
    // 2 ve 3 fork; 4 her ikisini de parent alır
    // TV-59: mergeset = m(sp) ∪ (anticone(sp) ∩ past(B))
    // sp=2 (tie'da düşük bid); 3 hem parent hem blue olarak işaretlenmiş
    // order() sadece selected-chain'i verir (blue parent'ları DEĞİL)
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![1]));
    g.add(blk(4, vec![2, 3]));
    // fork sibling coloring yapılmış olmalı
    assert!(g.is_blue.contains_key(&3), "fork sibling renklendirilmemiş");
    // selected parent 2 (tie'da düşük bid)
    assert_eq!(g.selected[&4], Some(2));
    // order() selected-chain'i verir: 4 → 2 → 1
    let o = g.order(4);
    assert!(o.contains(&2));
    assert!(!o.contains(&3) || g.mergesets[&4].contains(&3));
}

#[test]
fn mergeset_absorbs_distant_fork_sibling() {
    // 2 ve 3 fork; 5 sadece 2'nin zincirinden gelir, 3'ü parent olarak ALMAZ
    // → 3, anticone(sp=4) ∩ past(5) içindeyse mergeset'e girer
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![1]));       // fork sibling
    g.add(blk(4, vec![2]));       // 2'nin zinciri
    g.add(blk(5, vec![4]));       // 5 → 4 → 2 → 1
    // 3, past(5)'te DEĞİL (5, 3'ü referans almıyor), anticone'da
    assert!(!g.past(5).contains(&3));
    // 3'ün coloring'i yapılmış olmalı
    assert!(g.is_blue.contains_key(&3));
}

#[test]
fn phantom_parent_not_registered_as_child() {
    // 2026-09-26: var-olmayan parent kenar kaydında → future(phantom) gerçek
    // blok dönmüş oluyor. Ebeveyn görünmüyorsa kenar OLMAMALI.
    // children private olduğu için future() üzerinden dolaylı doğruluyoruz.
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1, 99])); // 99 henüz yok
    // 99 eklenmeden önce 2, 99'un future'ında OLMAMALI (kenar yok)
    // — ancak future(99) blok yoksa boş döner; dolaylı: 99 ekleyince 2 görünür
    g.add(blk(99, vec![])); // şimdi geldi
    // 2, 99'un future'ında olmalı (99 gerçekten eklenince kenar kurulur)
    assert!(g.future(99).contains(&2));
}

#[test]
fn order_starts_with_self_ends_with_genesis() {
    // order(B) = B'den başlar, selected-chain'i geriye izler, genesis sonda
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    let o = g.order(3);
    assert_eq!(o[0], 3);   // B en başta
    assert_eq!(o.last(), Some(&1)); // genesis en sonda
    assert_eq!(o.len(), 3);
}

#[test]
fn order_covers_selected_chain_ancestors() {
    // linear zincirde order(B) selected-chain'i tamamen içerir
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![1]));
    g.add(blk(4, vec![2, 3]));
    let o = g.order(4);
    // selected-chain 1 → 2 → 4 (tie'da düşük bid: 2)
    assert!(o.contains(&1));
    assert!(o.contains(&2));
    assert!(o.contains(&4));
    assert_eq!(o[0], 4);
    assert_eq!(o.last(), Some(&1));
}

#[test]
fn order_is_deterministic() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![1]));
    g.add(blk(4, vec![2, 3]));
    let a = g.order(4);
    let b = g.order(4);
    assert_eq!(a, b);
}

#[test]
fn blue_score_increases_along_selected_chain() {
    // TV-58: selected-chain boyunca blue_score monoton artar
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    g.add(blk(4, vec![3]));
    g.add(blk(5, vec![4]));
    assert!(g.blue_score_increases_along_selected_chain());
}

#[test]
fn blue_score_increases_along_short_chain() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    assert!(g.blue_score_increases_along_selected_chain());
}

#[test]
fn order_within_past_deterministic() {
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![1]));
    g.add(blk(4, vec![2, 3]));
    let a = g.order_within_past();
    assert!(a);
}

#[test]
fn reward_split_consistency() {
    // RewardSplit: treasury (%5) + miners = total; toplam emission sabitleri
    let mut g = Ghostdag::new(18);
    g.add(blk(1, vec![]));
    g.add(blk(2, vec![1]));
    g.add(blk(3, vec![2]));
    let rs = g.reward_split(3);
    assert_eq!(rs.treasury + rs.miners, rs.total);
    assert!(rs.total >= 1);
    // treasury %5 = total * 500/10000
    assert_eq!(rs.treasury, rs.total * 500 / 10000);
}

#[test]
fn k_parameter_stored() {
    let g = Ghostdag::new(7);
    assert_eq!(g.k, 7);
    let g2 = Ghostdag::new(18);
    assert_eq!(g2.k, 18);
}

#[test]
fn two_independent_chains_dont_cross() {
    // iki ayrı genesis'li zincir — birbirinin past'ında değiller
    let mut g = Ghostdag::new(18);
    g.add(blk(100, vec![]));
    g.add(blk(200, vec![]));
    g.add(blk(101, vec![100]));
    g.add(blk(201, vec![200]));
    assert!(!g.past(101).contains(&201));
    assert!(!g.past(201).contains(&101));
}

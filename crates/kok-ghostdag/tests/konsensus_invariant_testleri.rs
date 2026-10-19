//! KONSENSUS / DAG INVARIANT TESTLERİ — oylama ve sonlandırma kuralları,
//! ÖLÇÜM ÜZERİNE.
//!
//! Bu dosya MEVCUT KODA DOKUNMADAN eklendi; sadece yeni bir integration test
//! dosyasıdır. Tüm testler saf in-memory'dir — ağ, disk, dosya veya harici
//! durum yoktur. `blok_siralama_testleri.rs` küçük elle yazılmış DAG'leri
//! kapsar; bu dosya onun TÜMLEYENİDİR ve üç şeyi farklı yapar:
//!
//!   1. **Gerçek DAG'ler** — `sim::mine_chain` sabit seed ile: 73 blok, 596
//!      mergeset üyesi, 55 dolu mergeset. Küçük elle yazılmış bir DAG'de
//!      mergeset genellikle boş kalır (anticone eklenme anında önbelleğe
//!      alınır) ve coloring/ödeme kuralları hiç çalışmaz. Bu testlerin
//!      anlamlı olması için DAG'in gerçekten mergeset üyesi üretmesi gerekir.
//!   2. **Kuralların her iki yönü** — oylama eşiği k=1'de AYIRICI olmalıdır
//!      (bir üye mavi, diğeri kırmızı), sadece "hepsi mavi" demek bir
//!      invariant testi değildir.
//!   3. **Önbellek semantiği saygılı** — `is_blue` son yazan bloğun
//!      coloring'ini yansıtır (add() her mergeset için üzerine yazar), bu
//!      yüzden testler renklendirmi ÖNBELLEKTEN OKUMAK yerine TOPOLOJİDEN
//!      YENİDEN HESAPLAR. Okuma-yazma yarışı yapan bir testin proteksi yoktur.
//!
//! Test ettiği kurallar:
//!   * TV-58 — blue_score seçili-parent zincirinde her zaman artar
//!   * Özyineli skor formülü — blue_score(B) = blue_score(sp) + 1 + |mavi
//!     anticone(B)|, topolojiden hesaplanabilir
//!   * Oylama kuralı — |anticone(m) ∩ mergeset(B)| ≤ k ⟺ mavi
//!   * mergeset boyut sınırı 2k (MERGESET_SIZE_LIMIT)
//!   * anticone, future'ı İÇERMEZ (round-6 düzeltmesi)
//!   * order(B) ⊆ past(B) ∪ {B} (TV-59)
//!   * Ödeme kümesi: tekrarsız, mergeset üyesi, mavi bloklara öder
//!   * Seçim kuralı: en yüksek skor, eşitlikte en küçük bid; DAG'in tamamında
//!   * Determinizm: aynı seed ile aynı DAG iki kez inşa edilirse bayt bayt aynı

use kok_ghostdag::sim::mine_chain;
use kok_ghostdag::{Bid, Block, Ghostdag, GHOSTDAG_K, MERGESET_SIZE_LIMIT};
use rand::rngs::StdRng;
use rand::SeedableRng;

/// Sabit seed'li gerçek bir DAG: fork olasılığı %25, üç madenci.
/// Seed sabit olduğu için test deterministiktir.
fn olcu_dag(n: usize, fork: f64, seed: u64) -> Ghostdag {
    let mut rng = StdRng::seed_from_u64(seed);
    let mut g = Ghostdag::new(GHOSTDAG_K);
    let _ = mine_chain(&mut g, n, &mut rng, &["A", "B", "C"], fork);
    g
}

/// Anticone'ı yeniden hesapla: anticone(b) = past(b) ∪ future(b) ∪ {b}
/// dışındaki TÜM bloklar. Önbellekten bağımsız, saf topoloji.
fn anticone_topolojiden(g: &Ghostdag, b: Bid) -> std::collections::BTreeSet<Bid> {
    let past_b = g.past(b);
    let fut_b = g.future(b);
    g.blocks
        .keys()
        .filter(|&&x| x != b && !past_b.contains(&x) && !fut_b.contains(&x))
        .copied()
        .collect()
}

/// Bir mergeset üyesinin, VERİLEN mergeset içindeki karşılıklı anticone
/// sayısı. Oylama kuralının kendisidir: ≤ k ise mavi.
fn ic_anticone_sayisi(g: &Ghostdag, m: Bid, ms: &std::collections::BTreeSet<Bid>) -> usize {
    anticone_topolojiden(g, m).intersection(ms).count()
}

// ---------------------------------------------------------------------------
// SONLANDIRMA: blue_score seçili-parent zincirinde artar (TV-58)
// ---------------------------------------------------------------------------

/// 73 blokluk, 55 dolu mergeset'li gerçek bir DAG'de blue_score seçili-parent
/// zincirinde her seferinde ARTAR. Yerleşik doğrulayıcı VE elle yürüyüş ile
/// iki yoldan ölçülür — yerleşik `checked > 0` "yeşil ama hiç bakmadı"
/// sonucunu ayırt eder, elle yürüyüş ise her kenarı teker teker doğrular.
#[test]
fn blue_score_gercek_dagda_secili_zincirde_artar() {
    let g = olcu_dag(60, 0.25, 7);
    assert!(g.blocks.len() > 50, "DAG yeterli büyüklükte değil");
    // yerleşik doğrulayıcı
    assert!(
        g.blue_score_increases_along_selected_chain(),
        "TV-58 bozuldu: blue_score seçili zincirde azaldı"
    );
    // DOĞRUDAN YÜRÜYÜŞ: her bloktan genesis'e kadar her kenarı doğrula
    let mut kenarlar = 0usize;
    for bid in g.blocks.keys() {
        let mut cur = *bid;
        while let Some(Some(sp)) = g.selected.get(&cur) {
            assert!(
                g.blue_score[&cur] > g.blue_score[sp],
                "kenar {} -> {}'de skor artmadı (TV-58)",
                cur,
                sp
            );
            kenarlar += 1;
            cur = *sp;
        }
    }
    assert!(
        kenarlar > 100,
        "yürüyüş yeterli kenar incelemedi: {}",
        kenarlar
    );
}

/// blue_score her zaman ≥ 1'dir (genesis = 1). Üst sınır: her seçili-zincir
/// adımı en fazla 1 + |mergeset| ≦ 1 + 2k ekler ve zincir en fazla blok
/// sayısı kadar adımdır — yani skor ≤ blocks · (1 + 2k). Bunu aşan bir skor,
/// formülün uygulanışında bir hata olduğının sinyalidir.
#[test]
fn blue_score_sinirlar_icerisinde() {
    let g = olcu_dag(60, 0.25, 7);
    let ust_sinir = g.blocks.len() as u64 * (MERGESET_SIZE_LIMIT as u64 + 1);
    for (bid, skor) in &g.blue_score {
        assert!(*skor >= 1, "blok {}'nin skoru 1'den küçük: {}", bid, skor);
        assert!(
            *skor <= ust_sinir,
            "blok {}'nin skoru makul üst sınırı aştı: {}",
            bid,
            skor
        );
    }
}

/// ÖZYİNELİ FORMÜL: blue_score(B) = blue_score(sp) + 1 + |mergeset(B) içindeki
/// mavi anticone|. Mavi sayımı ÖNBELLEKTEN DEĞİL topolojiden yeniden
/// hesaplanır — çünkü add() her blok için is_blue'un ÜZERİNE YAZAR ve bir
/// bloğun mevcut rengi, skorun HESAPLANDIĞI andaki rengi olmayabilir.
/// Formülün topolojik olarak doğru olması, önbelleğin protokolle uyumlu
/// olduğunu kanıtlar.
#[test]
fn blue_score_ozyineli_formulu_topolojiden_dogru() {
    let g = olcu_dag(60, 0.25, 7);
    let mut denetlenen = 0usize;
    for (bid, sp) in &g.selected {
        let Some(sp) = sp else { continue };
        let ms = g.mergesets.get(bid).cloned().unwrap_or_default();
        // mavi üye sayısı KURALDAN hesaplanır: |anticone(m) ∩ ms| ≤ k
        let mavi = ms
            .iter()
            .filter(|m| ic_anticone_sayisi(&g, **m, &ms) <= g.k)
            .count();
        let beklenen = g.blue_score[sp] + 1 + mavi as u64;
        assert_eq!(
            g.blue_score[bid], beklenen,
            "blok {}'nin skoru özyineli formülü tutmadı: beklenen {}, got {} (ms {:?})",
            bid, beklenen, g.blue_score[bid], ms
        );
        denetlenen += 1;
    }
    assert!(
        denetlenen > 40,
        "formül yeterli blokta denenmedi: {}",
        denetlenen
    );
}

// ---------------------------------------------------------------------------
// OYLAMA: mergeset coloring kuralı (mavi = sonlandırılmış, k'ı geçemez)
// ---------------------------------------------------------------------------

/// Kuralın birebir kendisi, SON YAZAN saygısı ile: is_blue[m]'nin mevcut
/// değeri, m'yi mergeset'ine EN SON ALAN bloğun coloring'ine eşit olmalıdır
/// (add() her mergeset için üzerine yazar; bid sırası = ekleme sırası).
/// Önceki sürümlerde bu, önbellekten okunan bir testti ve proteksi yoktu.
#[test]
fn mergeset_mavi_kurali_son_yazan_ile_tutarli() {
    let g = olcu_dag(60, 0.25, 7);
    let mut dolu_ms = 0usize;
    let mut denetlenen = 0usize;
    // her blok için: m'yi içeren mergeset'ler arasından EN SON ekleneni bul
    for (bid, ms) in &g.mergesets {
        if ms.is_empty() {
            continue;
        }
        dolu_ms += 1;
        for m in ms {
            // m'yi içeren tüm bloklar; bid == ekleme sırası (mine_chain'de
            // next_bid her add'den sonra artar)
            let sahip_olanlar: Vec<Bid> = g
                .mergesets
                .iter()
                .filter(|(_, diger)| diger.contains(m))
                .map(|(b, _)| *b)
                .collect();
            let son_yazan = sahip_olanlar
                .iter()
                .copied()
                .max()
                .expect("en az bir sahip var");
            let son_ms = &g.mergesets[&son_yazan];
            let kural_mavi = ic_anticone_sayisi(&g, *m, son_ms) <= g.k;
            assert_eq!(
                g.is_blue.get(m).copied().unwrap_or(false),
                kural_mavi,
                "blok {}'nin rengi son-yazan {}'in kuralıyla çelişiyor",
                m,
                son_yazan
            );
            // m'nin rengi EN AZINDAN şu anki mergeset için kurala uymalıdır:
            // kural > k ise renk kırmızı OLMALIDIR (mavi olamaz)
            let simdiki_kural = ic_anticone_sayisi(&g, *m, ms) <= g.k;
            if !simdiki_kural {
                assert!(
                    !g.is_blue.get(m).copied().unwrap_or(false),
                    "blok {} mergeset {} içinde {} karşılıklı anticone'a sahip ama mavi (k = {})",
                    m,
                    bid,
                    ic_anticone_sayisi(&g, *m, ms),
                    g.k
                );
            }
            denetlenen += 1;
        }
    }
    assert!(
        dolu_ms > 10,
        "DAG yeterli dolu mergeset üretmedi: {}",
        dolu_ms
    );
    assert!(
        denetlenen > 50,
        "kural yeterli üyede denenmedi: {}",
        denetlenen
    );
}

/// MERGESET BOYUT SINIRI: hiçbir mergeset 2k'dan fazla üye içeremez. Bu
/// sınır, koca bir fork'un tek bir bloğun ödeme kümesini ele geçirmesini
/// önler — mergeset sınırsızsa bir saldırgan binlerce bloğu tek bloğa
/// "sonlandırılmış" diye yutturabilir.
#[test]
fn mergeset_boyutu_iki_kyi_asmaz() {
    for (n, fork, seed) in [(40usize, 0.25f64, 1u64), (60, 0.4, 2), (80, 0.1, 3)] {
        let g = olcu_dag(n, fork, seed);
        for (bid, ms) in &g.mergesets {
            assert!(
                ms.len() <= MERGESET_SIZE_LIMIT,
                "blok {}'nin mergeset'i {} üye içeriyor; sınır {}",
                bid,
                ms.len(),
                MERGESET_SIZE_LIMIT
            );
        }
    }
}

/// ANTICONE FUTURE İÇERMEZ (round-6 düzeltmesi, 2026-09-25): eskiden anticone
/// "past(B) ∪ {B} dışındaki her şey" olarak hesaplanıyordu ve bu, future'ı
/// DA içeriyordu — 100 blokluk DAG'de ortalama 64.9, maksimum 123. k=18
/// böyle bir anticone'ı asla bağlayamazdı. Doğru tanım future'ı da dışlar.
/// Bu test, o düzeltmenin hala tuttuğunu ölçer: anticone ∩ future = ∅.
#[test]
fn anticone_future_kumesini_icermez() {
    let g = olcu_dag(60, 0.25, 7);
    let mut toplam_anticone = 0usize;
    let mut maks_anticone = 0usize;
    for bid in g.blocks.keys() {
        let ac = g.anticone(*bid);
        let fut = g.future(*bid);
        let kesisim: usize = ac.intersection(&fut).count();
        assert_eq!(
            kesisim, 0,
            "blok {}'nin anticone'ı future'ından {} blok içeriyor (round-6 regresyonu)",
            bid, kesisim
        );
        // ve anticone ∩ past da boş olmalı
        let past = g.past(*bid);
        assert_eq!(
            ac.intersection(&past).count(),
            0,
            "anticone past'ı içeriyor"
        );
        // özünü de içeremez
        assert!(!ac.contains(bid));
        toplam_anticone += ac.len();
        maks_anticone = maks_anticone.max(ac.len());
    }
    // ÖLÇÜM: round-6 öncesi ortalama 64.9 idi; düzeltilmiş tanımla DAG'ın
    // büyük çoğunluğunda anticone küçük olmalı (k=18'in bağlayabileceği
    // aralıkta). Bu bir iddia değil, parametrenin varoluş gerekçesinin
    // ölçümüdür.
    let ort = toplam_anticone as f64 / g.blocks.len() as f64;
    assert!(
        ort < 20.0,
        "anticone ortalaması çok yüksek: {ort:.1} (round-6 öncesi 64.9)"
    );
    assert!(
        maks_anticone < 40,
        "maksimum anticone çok yüksek: {maks_anticone}"
    );
}

// ---------------------------------------------------------------------------
// ÖDEME KÜMESİ BÜTÜNLÜĞÜ: emisyonu çift harcama yok
// ---------------------------------------------------------------------------

/// Her ödeme kümesi TEKRARSIZDIR, her ödenen blok mergeset'in ÜYESİDİR ve
/// sadece MAVI bloklara ödenir. Ödeme kümesi, mavi bloklara DAG sırasına göre
/// bir kez öder — tekrar, emisyonun çatallar arasında çift harcanmasıdır.
#[test]
fn odeme_kumesi_tekrarsiz_mergeset_yesidi_ve_mavidir() {
    let g = olcu_dag(60, 0.25, 7);
    let mut odemeler = 0usize;
    let mut bos_olmayan = 0usize;
    for bid in g.blocks.keys() {
        let pay = g.pay_set(*bid);
        let ms = g.mergesets.get(bid).cloned().unwrap_or_default();
        let mut gorulen = std::collections::BTreeSet::new();
        for o in &pay {
            assert!(
                gorulen.insert(*o),
                "blok {} ödeme kümesinde tekrarladı: {}",
                bid,
                o
            );
            assert!(
                ms.contains(o),
                "blok {} mergeset üyesi olmayanı ödedi: {}",
                bid,
                o
            );
            // ödenen blok mavi olmalı (kırmızıya ödeme = sonlandırılmamışa ödeme)
            assert!(
                g.is_blue.get(o).copied().unwrap_or(false),
                "blok {} kırmızı (sonlandırılmamış) bloğa ödedi: {}",
                bid,
                o
            );
        }
        if !pay.is_empty() {
            bos_olmayan += 1;
        }
        odemeler += pay.len();
    }
    assert!(
        bos_olmayan > 5,
        "DAG hiç dolu ödeme kümesi üretmedi: {}",
        bos_olmayan
    );
    assert!(odemeler > 20, "DAG yeterli ödeme yapmadı: {}", odemeler);
}

// ---------------------------------------------------------------------------
// SIRALAMA İÇERMESİ: order(B) ⊆ past(B) ∪ {B} (TV-59)
// ---------------------------------------------------------------------------

/// Hiçbir blok, past(B) ∪ {B} dışından sıralamaya giremez. TV-59: bu kural
/// olmadan bir blok, başvurmadığı bir forku ödeme sırasına sokuyordu.
/// Yerleşik doğrulayıcı VE küme içermesinin elle denetimi ile iki yoldan.
#[test]
fn siralama_past_kumesi_disina_cikmaz() {
    let g = olcu_dag(60, 0.25, 7);
    assert!(
        g.order_within_past(),
        "order(B) past(B) dışına çıktı (TV-59)"
    );
    // DOĞRUDAN DENETİM
    for bid in g.blocks.keys() {
        let past_b = g.past(*bid);
        for o in g.order(*bid) {
            assert!(
                o == *bid || past_b.contains(&o),
                "blok {}'nin sıralaması past'ı dışından {} girdisi içeriyor (TV-59)",
                bid,
                o
            );
        }
    }
}

/// order(B) B ile BAŞLAR; seçili-parent zinciri (mavi omurga) genesis'te
/// biten ve order'ın ÖN EKİ olan bir yoldur; ardından mavi mergeset blokları
/// eklenir. Bu test her üç parçayı da ölçer: (1) başlangıç B, (2) zincir
/// ön ektir ve genesis'te biter, (3) tüm sıralama tekrarsızdır.
#[test]
fn siralama_kendisiyle_baslar_secili_zincir_genesisle_biter() {
    let g = olcu_dag(60, 0.25, 7);
    let mut denetlenen = 0usize;
    for bid in g.blocks.keys() {
        let o = g.order(*bid);
        if o.is_empty() {
            continue;
        }
        // (1) B en başta
        assert_eq!(
            *o.first().unwrap(),
            *bid,
            "blok {} sıralaması kendisiyle başlamıyor",
            bid
        );
        // (2) seçili-parent zincirini elle yürü: order'ın ön eki olmalı
        let mut zincir = Vec::new();
        let mut cur = *bid;
        let mut gorulen = std::collections::BTreeSet::new();
        while g.blocks.contains_key(&cur) && gorulen.insert(cur) {
            zincir.push(cur);
            cur = match g.selected.get(&cur) {
                Some(Some(sp)) => *sp,
                _ => break,
            };
        }
        assert!(
            o.starts_with(&zincir),
            "blok {}: seçili zincir order'ın ön eki değil",
            bid
        );
        // zincir genesis'te (parents == []) bitmeli
        let son = *zincir.last().expect("zincir boş olamaz");
        assert!(
            g.blocks[&son].parents.is_empty(),
            "blok {}: seçili zincir genesis'te bitmiyor (son: {})",
            bid,
            son
        );
        // (3) tüm sıralama tekrarsız
        let mut tum = std::collections::BTreeSet::new();
        for x in &o {
            assert!(tum.insert(*x), "blok {} sıralamasında tekrar: {}", bid, x);
        }
        denetlenen += 1;
    }
    assert!(denetlenen > 50, "yeterli blok denetlenmedi: {}", denetlenen);
}

// ---------------------------------------------------------------------------
// SEÇİM KURALI: DAG'in tamamında en yüksek skor, eşitlikte en küçük bid
// ---------------------------------------------------------------------------

/// Seçili-parent, parent'lar arasında her zaman EN YÜKSEK blue_score'a
/// sahip olandır; eşitlikte en küçük bid. Bu kural DAG'in TÜM bloklarında
/// ölçülür — tek bir örnekte doğru olması bir invariant değildir.
#[test]
fn secili_parent_dagin_tamaminda_en_yuksek_skorlu_parenttir() {
    let g = olcu_dag(60, 0.25, 7);
    let mut cok_parentli = 0usize;
    for (bid, sp) in &g.selected {
        let Some(sp) = sp else { continue };
        let parent_skorlar: Vec<u64> = g.blocks[bid]
            .parents
            .iter()
            .filter(|p| g.blocks.contains_key(p))
            .map(|p| g.blue_score.get(p).copied().unwrap_or(0))
            .collect();
        if parent_skorlar.len() > 1 {
            cok_parentli += 1;
        }
        assert!(
            !parent_skorlar.is_empty(),
            "blok {}'in seçili parent'ı var ama geçerli parent'ı yok",
            bid
        );
        assert_eq!(
            g.blue_score[sp],
            *parent_skorlar.iter().max().unwrap(),
            "blok {}'nin seçili parent'ı en yüksek skora sahip değil",
            bid
        );
        // tie-break: eşit skorlu parent'lar arasından en küçük bid
        let esit_skorlu: Vec<Bid> = g.blocks[bid]
            .parents
            .iter()
            .filter(|p| g.blocks.contains_key(p) && g.blue_score.get(p) == g.blue_score.get(sp))
            .copied()
            .collect();
        if esit_skorlu.len() > 1 {
            assert_eq!(
                *sp,
                *esit_skorlu.iter().min().unwrap(),
                "tie'da en küçük bid seçilmedi"
            );
        }
    }
    assert!(
        cok_parentli > 5,
        "DAG yeterli çok-parentlı blok üretmedi: {}",
        cok_parentli
    );
}

// ---------------------------------------------------------------------------
// OYLAMA EŞİĞİ: k kuralı AYIRICIDIR (her iki yön)
// ---------------------------------------------------------------------------

/// Elle inşa edilmiş yıldız DAG'inde oylama eşiği her iki yönüyle ölçülür.
/// Beş kollu bir fork'un en son eklenen kolu ağır yapıldığında (blok 7),
/// hub (blok 8) onu seçili-parent alır ve mergeset'ine {2,3,4,5} girer.
/// Üyelerin mergeset-içi karşılıklı anticone'ları 0,1,2,3 olduğundan:
///   * k=1 → 2 ve 3 mavi, 4 ve 5 KIRMIZI (eşik ayırıcı)
///   * k=3 → hepsi mavi
///
/// Sadece "hepsi mavi" diyen bir test, eşiğin varlığını kanıtlamaz.
#[test]
fn oylama_k_esigi_her_yonde_ayiricidir() {
    fn yildiz(k: usize) -> Ghostdag {
        let mut g = Ghostdag::new(k);
        g.add(Block {
            bid: 1,
            parents: vec![],
        });
        for b in 2..=6 {
            g.add(Block {
                bid: b,
                parents: vec![1],
            }); // beş paralel kol
        }
        g.add(Block {
            bid: 7,
            parents: vec![6],
        }); // son kolu ağır yap (skor 3)
            // hub: beş kolu da parent alır; en yüksek skorlu parent 7 → sp = 7
        g.add(Block {
            bid: 8,
            parents: vec![2, 3, 4, 5, 7],
        });
        g
    }

    // ÖNCE yapıyı teyit et: mergeset(8) = {2,3,4,5} ve sp = 7
    let onizleme = yildiz(GHOSTDAG_K);
    assert_eq!(onizleme.selected[&8], Some(7), "hub en ağır kolu seçmeli");
    let ms = onizleme.mergesets[&8].clone();
    assert_eq!(
        ms,
        [2, 3, 4, 5]
            .into_iter()
            .collect::<std::collections::BTreeSet<_>>()
    );

    // K=1: eşik ayırır. 2 (iç anticone 0) ve 3 (1) mavi; 4 (2) ve 5 (3) kırmızı.
    let g1 = yildiz(1);
    assert!(g1.is_blue[&2], "k=1: iç anticone 0 olan blok mavi olmalı");
    assert!(g1.is_blue[&3], "k=1: iç anticone 1 olan blok mavi olmalı");
    assert!(
        !g1.is_blue[&4],
        "k=1: iç anticone 2 > k olan blok KIRMIZI olmalı (eşik ayırmadı)"
    );
    assert!(
        !g1.is_blue[&5],
        "k=1: iç anticone 3 > k olan blok KIRMIZI olmalı"
    );
    // ödeme kümesi sadece mavi üyelere öder: {2, 3}
    assert_eq!(
        g1.pay_set(8),
        vec![2, 3],
        "k=1'de ödeme kümesi sadece mavi blokları içermeli"
    );
    // blue_score = sp(3) + 1 + 2 mavi = 6
    assert_eq!(g1.blue_score[&8], 6);

    // K=3: eşiğin altında, hepsi mavi (4. üyenin iç anticone'u 3 ≤ 3)
    let g3 = yildiz(3);
    for m in [2, 3, 4, 5] {
        assert!(
            g3.is_blue[&m],
            "k=3: iç anticone ≤ 3 olan blok {} mavi olmalı",
            m
        );
    }
    assert_eq!(g3.pay_set(8), vec![2, 3, 4, 5]);
    assert_eq!(g3.blue_score[&8], 3 + 1 + 4);
}

// ---------------------------------------------------------------------------
// DETERMİNİZM: aynı seed, aynı DAG, bayt bayt aynı konsensus durumu
// ---------------------------------------------------------------------------

/// mine_chain sabit seed ile iki kez çağrılırsa TÜM konsensus durumu aynı
/// olmalıdır: blue_score, selected, is_blue, mergesets, order, pay_set.
/// Determinizm olmazsa iki dürüst node farklı DAG'ler için farklı sonuç
/// hesaplar ve seed'e bağlı bir fork riski doğar.
#[test]
fn ayni_seed_iki_dag_bayt_bayt_ayni_konsensus_durumu() {
    let a = olcu_dag(60, 0.25, 42);
    let b = olcu_dag(60, 0.25, 42);
    assert_eq!(a.blocks.len(), b.blocks.len());
    assert_eq!(a.blue_score, b.blue_score, "blue_score deterministik değil");
    assert_eq!(
        a.selected, b.selected,
        "selected parent deterministik değil"
    );
    assert_eq!(a.is_blue, b.is_blue, "coloring deterministik değil");
    assert_eq!(a.mergesets, b.mergesets, "mergesets deterministik değil");
    for bid in a.blocks.keys() {
        assert_eq!(
            a.order(*bid),
            b.order(*bid),
            "blok {} sıralaması farklı",
            bid
        );
        assert_eq!(
            a.pay_set(*bid),
            b.pay_set(*bid),
            "blok {} ödeme kümesi farklı",
            bid
        );
        assert_eq!(
            a.reward_split(*bid),
            b.reward_split(*bid),
            "blok {} ödülü farklı",
            bid
        );
    }
}

/// FARKLI seed'ler FARKLI DAG'ler üretir — bu, yukarıdaki determinizm
/// testinin boş bir karşılaştırma olmadığının kanıtıdır (iki farklı seed
/// aynı çıktıyı verseydi "aynı" iddiası anlamsız olurdu).
#[test]
fn farkli_seedler_farkli_dagler_uretir() {
    let a = olcu_dag(60, 0.25, 1);
    let b = olcu_dag(60, 0.25, 999);
    // yapı farklı olmalı (seed gerçekten rasgeleliği yönetiyor)
    assert_ne!(
        a.blue_score, b.blue_score,
        "farklı seed'ler aynı blue_score üretti — determinizm testi boş"
    );
}

// ---------------------------------------------------------------------------
// ROBUSTLUK: bilinmeyen ve eksik bloklar panic değil
// ---------------------------------------------------------------------------

/// Bilinmeyen bir blok için public erişimler asla panic olmaz — bir node,
/// parent'ları henüz gelmemiş bir blok için bunları çağırıyorsa
/// çökmemelidir. Davranışlar YAZILMIŞ varsayılanlarıdır:
///   * order/pay → boş (blok varlığı şartı, Unknown → No-op)
///   * past/future → boş (kenar yok)
///   * anticone → TÜM bilinen bloklar (past ∅, future ∅, kendisi listede yok)
///   * pay_set → [B] (mergeset kaydı yok → "tek mavi blok" varsayımı)
#[test]
fn bilinmeyen_blok_icin_her_erisim_guvenlidir() {
    let g = olcu_dag(40, 0.25, 7);
    let bilinmeyen: Bid = 999_999;
    assert!(
        g.order(bilinmeyen).is_empty(),
        "bilinmeyen blok sıralaması boş olmalı"
    );
    assert!(
        g.past(bilinmeyen).is_empty(),
        "bilinmeyen blok past'ı boş olmalı"
    );
    assert!(
        g.future(bilinmeyen).is_empty(),
        "bilinmeyen blok future'ı boş olmalı"
    );
    // anticone: past ∅, future ∅, kendisi listede yok → tüm bilinen bloklar
    let ac = g.anticone(bilinmeyen);
    assert_eq!(
        ac.len(),
        g.blocks.len(),
        "bilinmeyen blok anticone'ı tanımdan farklı"
    );
    assert!(!ac.contains(&bilinmeyen));
    // pay_set: mergeset kaydı yok → [B] varsayımı (tek mavi blok)
    assert_eq!(g.pay_set(bilinmeyen), vec![bilinmeyen]);
    // ödül split'i panic vermez (genesis-era eğrisi döner)
    let r = g.reward_split(bilinmeyen);
    assert!(r.total >= 1, "bilinmeyen blok için ödül geçersiz");
    assert_eq!(r.treasury + r.miners, r.total);
}

/// Phantom parent toleransı: var-olmayan bir parent'a atıf yapan blok
/// eklenir ve DAG bozulmaz — parent, past'a veya future'a KAYDEDİLMEZ,
/// ama bloğun kendisi geçerli kabul edilir. Bu, ağın tolerant ön yüzüdür.
#[test]
fn phantom_parent_toleransi_dag_i_bozmaz() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block {
        bid: 1,
        parents: vec![],
    });
    g.add(Block {
        bid: 2,
        parents: vec![1, 777],
    }); // 777 henüz yok
    assert!(g.blocks.contains_key(&2));
    // phantom parent past'ta değil
    assert!(!g.past(2).contains(&777));
    // ama gerçek parent var
    assert!(g.past(2).contains(&1));
    // genesis hala geçerli ve skor artar
    assert!(g.blue_score[&2] > g.blue_score[&1]);
    // invariantlar hala tutuyor
    assert!(g.order_within_past());
    assert!(g.blue_score_increases_along_selected_chain());
}

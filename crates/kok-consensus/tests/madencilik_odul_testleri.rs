//! MADENCİLİK ÖDÜLLENDİRME HESAPLAMA TESTLERİ — AI-fayda skoru → ödül dağılımı.
//!
//! Bu dosya MEVCUT KODA DOKUNMADAN eklendi; sadece yeni bir integration test
//! dosyasıdır. Tüm testler saf in-memory'dir — ağ, disk veya harici durum
//! yoktur.
//!
//! KÖK'ün PoUW tasarımındaki merkezi gerilim şudur: *faydalı* yapay zeka
//! işi (katman U — CHGNet/M3GNet tipi tensör çıkarımı, GNoME-Forge profili)
//! gerçek FLOP'lar üretir ve gerçek fee'ler escrowlar, ama konsensus
//! ağırlığına ve dolayısıyla blok ödülüne SIFIR katkı verir. "AI-fayda
//! skoru → ödül dağılımı" bağlantısını test etmek, bu yüzden iki yarı test
//! eder:
//!
//!   1. ÖDÜL MATEMATİĞİNİN KENDİSİ — emisyon eğrisi (R_0 = 50 KOK, aralık
//!      başına 1 azalan doğrusal düşüş, tail emission asla sıfır değil),
//!      hazinenin %5'i (TREASURY_BPS = 500 baz puan) ve ödeme kümesinin
//!      büyüklüğü. `reward_split` her zaman `treasury + miners == total`
//!      korumalıdır, yoksa para politikası sessizce enflasyona yol açar.
//!   2. ÖDÜLÜN FAYDADAN BAĞIMSIZLIĞI — ne kadar büyük fee'li, ne kadar
//!      yüksek FLOP'lu U görevi paketlenirse paketlensin, aynı DAG bloğu
//!      aynı ödül dağılımını verir. Ödül dağıtımı fayda skorunun değil,
//!      DAG'in kendi topolojisinin (blue_score ve mergeset) fonksiyonudur.
//!
//! UYARI — birim testlerin aksine, bu dosya `Ghostdag::set_depth_for_test`
//! kullanamaz (o `#[cfg(test)]` ile kapalıdır ve integration testleri
//! kütüphaneyi cfg(test)'siz derler). Eğri, `blue_score` public alanı
//! üzerinden — yani `reward_split`'in okuduğu AYNI yoldan — çalışılır; böylece
//! ölçülen şey gerçek formülün kendisi olur.

use kok_consensus::add_block;
use kok_consensus::ConsensusBlock;
use kok_consensus::kok_ghostdag::{
    Block, Ghostdag, GHOSTDAG_K, EMISSION_HALVING_INTERVAL, R_0, TAIL_EMISSION, TREASURY_BPS,
};
use kok_consensus::kok_u_layer::job::{JobKind, JobSpec};
use kok_consensus::kok_u_layer::{validate_u_task, C_FEE, MAX_BURN_RATE, TaskProof, TaskSpec};
use kok_consensus::kok_u_layer::u_task_consensus_weight;

/// Çatallı bir DAG: ödeme kümelerini ve emisyonu birden fazla blokta ölçmek
/// için düz bir zincirden daha gerçekçi.
fn dalli_dag(n: u64) -> Ghostdag {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    let mut sonraki_fork = 4u64;
    let mut fork_id = 1_000_000u64;
    for b in 2..=n {
        let parents = if b == sonraki_fork {
            fork_id += 1;
            g.add(Block { bid: fork_id, parents: vec![b - 2] });
            sonraki_fork += 4;
            vec![b - 1, fork_id]
        } else {
            vec![b - 1]
        };
        g.add(Block { bid: b, parents });
    }
    g
}

// ---------------------------------------------------------------------------
// ÖDÜL MATEMATİĞİ: emisyon eğrisi ve hazine payı
// ---------------------------------------------------------------------------

/// Genesis bloğu: R_0 = 50 KOK, hazine %5 = 2 KOK, madenciler 48 KOK.
/// Bu değerler spec'te sabittir (KOK_V2_TECHNICAL_SPEC) ve değişmeleri
/// konsensus kırılmasıdır.
#[test]
fn genesis_odulu_50_hazine_yuzde_5_miner_48() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    let r = g.reward_split(1);
    assert_eq!(r.total, R_0, "genesis emisyonu R_0 = 50 olmalı");
    assert_eq!(r.treasury, 2, "hazine 50 KOK'un %5'i = 2 KOK olmalı");
    assert_eq!(r.miners, 48, "madenciler 50 - 2 = 48 KOK almalı");
    assert_eq!(r.treasury + r.miners, r.total, "emisyon korunmuyor");
}

/// Hazinenin %5'i her derinlikte TAM olarak formülü verir:
/// treasury == total * TREASURY_BPS / 10_000. Tam sayı bölmenin birim
/// düşürdüğü yer (total = 39 → treasury 1) dahil, her değer için hesaplanır.
#[test]
fn hazine_payi_her_derinlikte_tam_yuzde_5() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    g.add(Block { bid: 2, parents: vec![1] });
    // derinlik, reward_split'in okuduğu public alan üzerinden ayarlanır
    for derinlik in [0u64, 1, 2, 100, EMISSION_HALVING_INTERVAL, 3 * EMISSION_HALVING_INTERVAL] {
        g.blue_score.insert(2, derinlik);
        let r = g.reward_split(2);
        assert_eq!(
            r.treasury,
            r.total * TREASURY_BPS / 10_000,
            "derinlik {} için hazine payı formülü tutmadı",
            derinlik
        );
        assert_eq!(r.miners, r.total - r.treasury, "madenci payı bölme hatası");
    }
    // tam sayı bölmenin gerçekten birim düşürdüğü nokta: 39/20 = 1
    g.blue_score.insert(2, 11 * EMISSION_HALVING_INTERVAL); // total = 50 - 11 = 39
    assert_eq!(g.reward_split(2).total, 39);
    assert_eq!(g.reward_split(2).treasury, 1, "39 * 500 / 10000 = 1 (tam sayı bölme)");
}

/// Emisyon eğrisi aralık başına tam olarak 1 KOK düşer:
///   total(depth) = max(R_0 - depth / EMISSION_HALVING_INTERVAL, TAIL_EMISSION)
/// Bu, spec'in "azalan ama asla sıfır olmayan" emisyonunun doğrusal halidir.
#[test]
fn emisyon_egrisi_aralk_basina_bir_kok_duser() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    g.add(Block { bid: 2, parents: vec![1] });
    let derinlikler = [
        0u64,
        EMISSION_HALVING_INTERVAL,
        2 * EMISSION_HALVING_INTERVAL,
        10 * EMISSION_HALVING_INTERVAL,
        (R_0 - 1) * EMISSION_HALVING_INTERVAL,
    ];
    for d in derinlikler {
        g.blue_score.insert(2, d);
        let beklenen = R_0 - d / EMISSION_HALVING_INTERVAL;
        assert_eq!(
            g.reward_split(2).total,
            beklenen,
            "derinlik {} için emisyon {} olmalı, eğri bozuk",
            d,
            beklenen
        );
    }
}

/// TAIL EMISSION: emisyon asla sıfıra inemez. Zemin tam R_0 * aralık
/// tükendiğinde (50 * 210_000) ve ondan çok ötede hala 1 KOK'dur. Monero/Grin
/// tarzı: sonsuz düşük ama sıfırsız emisyon.
#[test]
fn tail_emission_asla_sifir_olamaz() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    g.add(Block { bid: 2, parents: vec![1] });
    // tam zeminde
    g.blue_score.insert(2, R_0 * EMISSION_HALVING_INTERVAL);
    assert_eq!(
        g.reward_split(2).total,
        TAIL_EMISSION,
        "zeminde emisyon sıfıra düştü; tail floor çalışmıyor"
    );
    // çok ötede — saturating_sub ve .max(TAIL_EMISSION) birlikte bağlamalı
    g.blue_score.insert(2, R_0 * EMISSION_HALVING_INTERVAL * 1_000_000);
    assert_eq!(
        g.reward_split(2).total,
        TAIL_EMISSION,
        "zeminin ötesinde emisyon hala 1 olmalı"
    );
    // ve negatif yöne: hiçbir derinlik total'i TAIL_EMISSION'nın altına düşüremez
    for d in [0u64, 1, EMISSION_HALVING_INTERVAL, R_0 * EMISSION_HALVING_INTERVAL, u64::MAX / 2] {
        g.blue_score.insert(2, d);
        let t = g.reward_split(2).total;
        assert!(t >= TAIL_EMISSION, "derinlik {} emisyonu {}'e düştü", d, t);
        assert!(t <= R_0, "derinlik {} emisyonu R_0'ı aştı: {}", d, t);
    }
}

/// KORUNUM INVARIANT'IN ÖLÇÜMÜ: çatallı bir DAG'de her blok için
/// treasury + miners == total. Tek bir birimin yanlış hesaplanması burada
/// patlar. Ödeme kümesi büyüklüğü de ödülün parçası olarak raporlanır.
#[test]
fn odul_dagin_her_bloğunda_korunur() {
    let g = dalli_dag(50);
    let mut denetlenen = 0usize;
    for bid in g.blocks.keys() {
        let r = g.reward_split(*bid);
        assert_eq!(
            r.treasury + r.miners,
            r.total,
            "blok {}'de emisyon korunmadı (treasury {} + miners {} != total {})",
            bid,
            r.treasury,
            r.miners,
            r.total
        );
        assert!(r.total >= TAIL_EMISSION, "blok {} emisyonu zeminin altında", bid);
        assert!(r.total <= R_0, "blok {} emisyonu R_0'ı aştı", bid);
        // ödeme kümesi sadece DAG'de var olan blokları içerir
        for o in g.pay_set(*bid) {
            assert!(g.blocks.contains_key(&o), "blok {} var olmayanı ödedi: {}", bid, o);
        }
        // pay_set_size raporu gerçek ödeme kümesiyle aynı
        assert_eq!(r.pay_set_size, g.pay_set(*bid).len() as u64, "blok {} ödeme kümesi raporu yanlış", bid);
        denetlenen += 1;
    }
    assert!(denetlenen > 40, "yeterli blok denetlenmedi: {}", denetlenen);
}

/// Ödül, ÇAĞIRANDAN değil BLOKTAN gelir: aynı blok iki kez sorulursa aynı
/// cevap (DAG tek girdidir) ve bilinmeyen bir blok genesis-era eğrisi alır —
/// çağıranın seçtiği bir yükseklik değil, hiçbir zaman panic değil.
#[test]
fn odul_bloktan_turetilir_cagirandan_degil() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    g.add(Block { bid: 2, parents: vec![1] });
    let a = g.reward_split(2);
    let b = g.reward_split(2);
    assert_eq!(a, b, "aynı blok iki farklı ödül dağılımı verdi");
    assert_eq!(a.total, R_0, "derinlik 2 hala ilk aralıktadır");
    // bilinmeyen blok → genesis-era eğrisi, panic değil
    let bilinmeyen = g.reward_split(999);
    assert_eq!(bilinmeyen.total, R_0, "bilinmeyen blok genesis eğrisi almadı");
}

// ---------------------------------------------------------------------------
// AI-FAYDA SKORU → ÖDÜL DAĞILIMI: fayda, ödülü SATIN ALAMAZ
// ---------------------------------------------------------------------------

/// ANA TEST: aynı DAG bloğu — biri 50 yüksek fee'li, yüksek FLOP'lu yapay
/// zeka görevi kanıtı taşıyan, diğeri hiçbir şey taşımayan — AYNI ödül
/// dağılımını verir. "Faydalı yapay zeka madenciliği"nin güvenlik
/// bütçesini satın alamaması budur: alıcı ne kadar inference talep ederse
/// etsin, madenci blok ödülünü DAG topolojisi dışında bir şeyle değiştiremez.
#[test]
fn faydali_ai_isciligi_odul_dagilimini_degistirmez() {
    fn iskelet() -> Ghostdag {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        g.add(Block { bid: 1, parents: vec![] });
        g.add(Block { bid: 2, parents: vec![1] });
        g.add(Block { bid: 3, parents: vec![1] });
        g.add(Block { bid: 4, parents: vec![2, 3] });
        g
    }
    let mut u_ile = iskelet();
    let mut u_siz = iskelet();

    // GNoME-Forge profili: CHGNet/M3GNet tipi yapı-potansiyeli görevleri —
    // gerçek tensör çıkarımının FLOP modeliyle (n_atoms^2). Önce maliyet
    // modelinin tepe noktasını teyit et: 100 atomluk hücre ~60300 FLOP,
    // 10 atomludan ~95 kat pahalı — ama bunların hiçbiri ödüle giremez
    let kucuk = JobKind::StructurePotential { n_atoms: 10 };
    let buyuk = JobKind::StructurePotential { n_atoms: 100 };
    assert!(buyuk.flops() > 50 * kucuk.flops(), "büyük hücre küçüğünden pahalı değil");
    let kanitlar: Vec<TaskProof> = (0..50)
        .map(|i| {
            // fayda skoru: hücre boyutu 10..100 arası değişir
            let n_atoms = 10 + (i % 5) * 30;
            let kind = JobKind::StructurePotential { n_atoms };
            assert!(kind.flops() > 0, "yapı-potansiyeli görevin maliyeti sıfır");
            // JobSpec, validate_job tarafından kabul edilen bir yapıdadır
            let _spec = JobSpec {
                kind,
                input_commit: 1000 + i as u64,
                fee: 10,
            };
            // görev, protokolün kendi fee kapısı tarafından geçerli
            let gecerli = TaskSpec {
                program: format!("chgnet-{i}"),
                fee: 10,
                burn_rate: 300,
            };
            assert!(validate_u_task(&gecerli, i as u64 * 10), "geçerli görev fee kapısında reddedildi");
            // MAX_BURN_RATE sınırı içinde (protokolün istismar karşıtı tavanı)
            assert!(gecerli.burn_rate <= MAX_BURN_RATE);
            TaskProof { tid: format!("task-{i}"), miner: format!("miner-{i}"), fee: 10 }
        })
        .collect();

    let mut zengin = ConsensusBlock::new(Block { bid: 5, parents: vec![4] }, [0xAA; 32]);
    zengin.bundle(kanitlar);
    assert_eq!(zengin.u_consensus_weight(), 0, "AI görev kanıtları konsensus ağırlığı bildirdi");
    add_block(&mut u_ile, &zengin);
    add_block(
        &mut u_siz,
        &ConsensusBlock::new(Block { bid: 5, parents: vec![4] }, [0xAA; 32]),
    );

    // ÖLÇÜLEN INVARIANT: ödül dağılımı fayda hacminden bağımsız
    assert_eq!(u_ile.reward_split(5), u_siz.reward_split(5), "AI görevleri ödül dağılımını değiştirdi");
    assert_eq!(u_ile.reward_split(5).total, u_siz.reward_split(5).total);
    assert_eq!(u_ile.reward_split(5).treasury, u_siz.reward_split(5).treasury);
    assert_eq!(u_ile.reward_split(5).miners, u_siz.reward_split(5).miners);
    assert_eq!(u_ile.reward_split(5).pay_set_size, u_siz.reward_split(5).pay_set_size);
    // ve DAG'in oylama çıktısı da
    assert_eq!(u_ile.blue_score[&5], u_siz.blue_score[&5]);
    assert_eq!(u_ile.pay_set(5), u_siz.pay_set(5));
}

/// FAYDA SKALASI TESTİ: bir tek MAX-fee kanıt ile 1000 orta-fee kanıt arasında
/// ödül açısından hiçbir fark yoktur. Ölçüm "bir uygun noktada sıfır" değil:
/// her fee seviyesinde ve her sayıda sıfırdır.
#[test]
fn fayda_skalasinda_odul_degismez() {
    let o_btn = |kanitlar: Vec<TaskProof>| -> (Ghostdag, u64) {
        let mut g = Ghostdag::new(GHOSTDAG_K);
        g.add(Block { bid: 1, parents: vec![] });
        let mut blk = ConsensusBlock::new(Block { bid: 2, parents: vec![1] }, [0xBB; 32]);
        blk.bundle(kanitlar);
        assert_eq!(blk.u_consensus_weight(), 0);
        add_block(&mut g, &blk);
        let r = g.reward_split(2);
        (g, r.total + r.treasury + r.miners + r.pay_set_size)
    };
    let tek = o_btn(vec![TaskProof { tid: "t".into(), miner: "m".into(), fee: u64::MAX }]);
    let cogu = o_btn(
        (0..1000)
            .map(|i| TaskProof { tid: format!("t{i}"), miner: format!("m{i}"), fee: 500 })
            .collect(),
    );
    let hic = o_btn(vec![]);
    // üçü de ödül açısından bayt bayt aynı
    assert_eq!(tek.1, hic.1, "tek max-fee kanıt ödülü değiştirdi");
    assert_eq!(cogu.1, hic.1, "1000 kanıt ödülü değiştirdi");
    assert_eq!(tek.0.reward_split(2), hic.0.reward_split(2));
    assert_eq!(cogu.0.reward_split(2), hic.0.reward_split(2));
    // DAG'lerin kendisi de aynı (sadece u_proofs farklı)
    assert_eq!(tek.0.blue_score, hic.0.blue_score);
    assert_eq!(cogu.0.pay_set(2), hic.0.pay_set(2));
    // ve her bir kanıtın fonksiyonel ağırlığı sıfır
    for p in &[TaskProof { tid: "x".into(), miner: "y".into(), fee: 1 }] {
        assert_eq!(u_task_consensus_weight(p), 0);
    }
}

/// FEE KAPISI İLE ÖDÜLÜN İLİŞKİSİ: bir blokun taşıyabileceği toplam U fee'si
/// C_FEE ile sınırlıdır (anti-aggregation: tek bir madenci fee pazarını
/// küçük görevlerle sulayamasın). Ama bu sınır ödül için bir GİRDİ DEĞİLDİR —
/// sınırı tamamen dolduran bir blok ile hiç doldurmayan blok aynı ödülü alır.
#[test]
fn fee_kapisi_odul_icin_girdi_degildir() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    // fee kapısını tam dolduran 5 görev (her biri 100, toplam 500 = C_FEE)
    let mut dolu = ConsensusBlock::new(Block { bid: 2, parents: vec![1] }, [0; 32]);
    let kanitlar: Vec<TaskProof> = (0..5)
        .map(|i| {
            let gecerli = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: 300 };
            assert!(validate_u_task(&gecerli, i * 100), "geçerli görev reddedildi");
            TaskProof { tid: format!("t{i}"), miner: "m".into(), fee: 100 }
        })
        .collect();
    // toplam fee 500 = C_FEE, yani kapı tam dolu
    assert_eq!(kanitlar.iter().map(|k| k.fee).sum::<u64>(), C_FEE);
    dolu.bundle(kanitlar);
    add_block(&mut g, &dolu);
    // ödül, kapı dolu olsa da genesis-era eğrisindedir
    let r = g.reward_split(2);
    assert_eq!(r.total, R_0);
    assert_eq!(r.treasury + r.miners, r.total);
    // ve fee kapısının ötesi reddedilir: 501. görev sığmaz
    let t = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: 300 };
    assert!(!validate_u_task(&t, C_FEE), "fee kapısını aşan görev kabul edildi");
    assert!(validate_u_task(&t, C_FEE - 100), "tam sığan görev reddedildi");
}

// ---------------------------------------------------------------------------
// ÖDÜL, FORKLU BİR DAG'DE ÖDEME KÜMESİYLE BİRLİKTE ÇALIŞIR
// ---------------------------------------------------------------------------

/// Önceki ödül testleri düz zincirler kullandı; bu test gerçek bir fork
/// üzerinden ödül dağılımını ölçer. Beş kollu bir fork'un ağır kolu hub'ın
/// seçili-parent'ı olur, mergeset'e {2,3,4,5} girer ve hepsi mavi olduğundan
/// ödeme kümesi DOLUDUR. Ödül bu ödeme kümesinin BÜYÜKLÜĞÜYLE hesaplanır —
/// ki bu da ödülün faydadan değil, DAG topolojisinden geldiğini bir kez daha
/// gösterir.
#[test]
fn odul_forklu_dagde_dolu_odeme_kumesiyle_tutarli() {
    let mut g = Ghostdag::new(GHOSTDAG_K);
    g.add(Block { bid: 1, parents: vec![] });
    for b in 2..=6 {
        g.add(Block { bid: b, parents: vec![1] }); // beş paralel kol
    }
    g.add(Block { bid: 7, parents: vec![6] }); // son kolu ağır yap
    g.add(Block { bid: 8, parents: vec![2, 3, 4, 5, 7] }); // hub
    assert_eq!(g.selected[&8], Some(7));
    // mergeset(8) = {2,3,4,5}, hepsi mavi (iç anticone ≤ 3 ≤ k=18)
    let ms = g.mergesets[&8].clone();
    assert_eq!(ms.len(), 4);
    let pay = g.pay_set(8);
    assert_eq!(pay.len(), 4, "ödeme kümesi dolu olmalı");
    // ödül korunur ve genesis-era'dadır
    let r = g.reward_split(8);
    assert_eq!(r.treasury + r.miners, r.total);
    assert_eq!(r.total, R_0);
    assert_eq!(r.treasury, 2);
    assert_eq!(r.miners, 48);
    assert_eq!(r.pay_set_size, 4);
    // blue_score: sp(7)=3 + 1 + 4 mavi = 8
    assert_eq!(g.blue_score[&8], 8);
}

// ---------------------------------------------------------------------------
// İKİ KATMAN AYRIMI: U kanıtlarının konsensus ağırlığı her koşulda sıfır
// ---------------------------------------------------------------------------

/// Ağırlık sıfırı her fee ve her sayı için sıfırdır — "bir uygun noktada
/// sıfır" ölçümü değil. Tek bir MAX-fee kanıt da, 1000 orta-fee kanıt da
/// aynı sıfırı verir.
#[test]
fn faydali_iscilik_agirligi_her_fee_ve_sayida_sifirdir() {
    let mut blk = ConsensusBlock::new(Block { bid: 9, parents: vec![] }, [0; 32]);
    assert_eq!(blk.u_consensus_weight(), 0, "boş blok sıfır olmalı");
    // tek ama en pahalı kanıt
    blk.bundle(vec![TaskProof { tid: "t".into(), miner: "m".into(), fee: u64::MAX }]);
    assert_eq!(blk.u_consensus_weight(), 0, "tek bir max-fee kanıt ağırlık bildirdi");
    // ve 1000 tanesi
    blk.bundle(
        (0..1000)
            .map(|i| TaskProof { tid: format!("t{i}"), miner: format!("m{i}"), fee: 500 })
            .collect(),
    );
    assert_eq!(blk.u_consensus_weight(), 0, "1000 kanıt sıfırdan farklı ağırlık bildirdi");
    // her kanıtın fonksiyonel ağırlığı da sıfır
    for p in &blk.u_proofs {
        assert_eq!(u_task_consensus_weight(p), 0, "tek bir U kanıtı ağırlık bildirdi");
    }
    // NEGATİF YÖN: fee ve burn_rate sınırlarının DIŞINDAKİ görevler protokol
    // tarafından reddedilir — bu sınır, ödül için bir girdi DEĞİL, ama
    // protokolün istismar karşıtı tavanıdır
    let gecerli = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: 300 };
    assert!(validate_u_task(&gecerli, 0), "geçerli görev reddedildi");
    let sifir_fee = TaskSpec { program: "mm8".into(), fee: 0, burn_rate: 300 };
    assert!(!validate_u_task(&sifir_fee, 0), "sıfır fee'li görev kabul edildi");
    let asiri_burn = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: MAX_BURN_RATE + 1 };
    assert!(!validate_u_task(&asiri_burn, 0), "MAX_BURN_RATE'i aşan görev kabul edildi");
    let tavan = TaskSpec { program: "mm8".into(), fee: 100, burn_rate: MAX_BURN_RATE };
    assert!(validate_u_task(&tavan, 0), "tam tavadaki burn_rate reddedildi");
}

/// MEVCUT DAVRANIŞIN KORUNUMU: bundle() DAG kimliğini değiştiremez — bid ve
/// parents eklenme anında sabittir, çünkü ağırlığı hesaplayan grafik
/// bunların dışını göremez (savunma katmanı 1).
#[test]
fn bundle_dag_kimligini_degistirmez() {
    let mut blk = ConsensusBlock::new(Block { bid: 7, parents: vec![1, 2] }, [0xCC; 32]);
    let once = (blk.dag.bid, blk.dag.parents.clone());
    blk.bundle(vec![TaskProof { tid: "t".into(), miner: "m".into(), fee: 100 }]);
    assert_eq!((blk.dag.bid, blk.dag.parents), once, "bundle DAG kimliğini değiştirdi");
    // ve g_cert_bytes da korunur
    assert_eq!(blk.g_cert_bytes, [0xCC; 32]);
}

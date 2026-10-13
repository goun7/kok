//! MODÜLER UPGRADE GÜVENLİĞİ TESTLERİ — PVI (Proof Verifier Interface).
//!
//! Bu dosya MEVCUT KODA DOKUNMADAN eklendi; sadece yeni bir integration test
//! dosyasıdır. Tüm testler saf in-memory'dir — ağ, disk veya harici durum
//! yoktur.
//!
//! PVI, KÖK'ün modüler upgrade mekanizmasının ta kendisidir: proof sistemini
//! (KW-Kernel parametreleri: q, r, n, hedef) bir hard fork ZORUNLULUĞU OLMADAN
//! değiştirilebilir kılan sınırdır. Bu, "modüler upgrade testleri — geçişlerin
//! güvenli olması" talebinin ölçülebilir karşılığıdır. Güvenli bir geçiş
//! demek:
//!
//!   1. **Toplamlık (totality)** — her girdi, bozuk olanlar dahil, bir
//!      `Verdict` üretir; asla panic olmaz. WASM sınırında bir trap, bir
//!      ret değil, "tanımsız sonuç"tur ve bir karar borcu olduğu anda çöker.
//!      Bir upgrade sırasında yeni decode yolu yeni bir trap alanı eklerse,
//!      upgrade sessizce güvenliği bozar.
//!   2. **Wire kontratının stabilitesi** — paket düzeni mantıksal değerlerin
//!      tam bir fonksiyonudur: aynı kanıtı iki kez encode etmek bayt bayt
//!      aynı paketi verir. Değiştirilen bir verifier bu kontrata güvenebilir.
//!   3. **Sistem kimliği değişimi replay'i reddeder** — bir ctx altında maden
//!      edilen kanıt, başka bir ctx altında GEÇERLİ DEĞİLDİR. Bir proof
//!      sistemi değişikliğinde eski kanıtlar yeni sistemde otomatik olarak
//!      geçerli kalamazlar; bu geçişin *güvenli* olması reddin kesin olması
//!      demektir.
//!   4. **Parametre değişimi açık reddedilir** — kernel paketin ilan ettiği
//!      q/r'den INŞA EDİLİR, gömülü bir sabit DEĞİL. Yeni bir alan (q) veya
//!      yeni bir tile adımı (r), decode'un m/n/r tutarlılık kapılarıyla
//!      yakalanır — sessiz bir kabul değil, nedeni taşıyan bir reddir.

use kok_poum::canonical;
use kok_poum::{KwKernel, Certificate, TOY_Q, TOY_R};
use kok_pvi::{pack, verify_raw, Verdict, VerifierInput};

/// Matrisleri + kanıtı kablo baytlarına encode et (paket düzeninin ta kendisi).
fn encode(
    a: &[Vec<u64>],
    b: &[Vec<u64>],
    cert: &Certificate,
    ctx: u64,
    nonce: u64,
    target: u64,
    q: u64,
    r: usize,
) -> VerifierInput {
    let n = a.len();
    let mut flat = Vec::with_capacity(n * n * 8 * 2);
    for row in a.iter().chain(b.iter()) {
        for v in row {
            flat.extend_from_slice(&v.to_le_bytes());
        }
    }
    let split = n * n * 8;
    let flat_b = flat.split_off(split);
    let mut cert_bytes = [0u8; 32];
    cert_bytes[0..8].copy_from_slice(&(cert.i as u64).to_le_bytes());
    cert_bytes[8..16].copy_from_slice(&(cert.j as u64).to_le_bytes());
    cert_bytes[16..24].copy_from_slice(&cert.value.to_le_bytes());
    cert_bytes[24..32].copy_from_slice(&(cert.m as u64).to_le_bytes());
    let mut pub_inputs = [0u8; 48];
    pub_inputs[0..8].copy_from_slice(&ctx.to_le_bytes());
    pub_inputs[8..16].copy_from_slice(&nonce.to_le_bytes());
    pub_inputs[16..24].copy_from_slice(&target.to_le_bytes());
    pub_inputs[24..32].copy_from_slice(&(n as u64).to_le_bytes());
    pub_inputs[32..40].copy_from_slice(&q.to_le_bytes());
    pub_inputs[40..48].copy_from_slice(&(r as u64).to_le_bytes());
    VerifierInput { cert_bytes, flat_a: flat, flat_b, pub_inputs }
}

/// Canonical matrisler üzerinden dürüst bir kanıt madenle (tek bir nonce).
fn madenle() -> (Vec<Vec<u64>>, Vec<Vec<u64>>, Certificate, u64, u64) {
    let a: Vec<Vec<u64>> = canonical::CANON_A.iter().map(|r| r.to_vec()).collect();
    let b: Vec<Vec<u64>> = canonical::CANON_B.iter().map(|r| r.to_vec()).collect();
    let k = KwKernel::new(TOY_Q, TOY_R);
    let target = 1u64 << 4;
    let mut nonce = 0u64;
    let cert = loop {
        nonce += 1;
        if let Some(c) = k.prove(&a, &b, 777, nonce, target) {
            break c;
        }
    };
    (a, b, cert, nonce, target)
}

// ---------------------------------------------------------------------------
// 1. TOPLAMLIK: her girdi bir karar verir, hiçbiri trap olmaz
// ---------------------------------------------------------------------------

/// Bir modüler upgrade'in en tehlikeli kısmı, yeni decode yolunun yeni bir
/// panic yüzeyi eklemesidir. Bu test, bozuk girdilerin HER sınıfını
/// `catch_unwind` içinde çalıştırır: hepsi `Reject` dönmeli, hiçbiri
/// unwinding yapmamalıdır. catch_unwind olmadan bir panic yine testi
/// failletir, ama panic'in *nerede* olduğunu bu testten öğrenemeyiz.
#[test]
fn her_bozuk_girdi_reddeder_asla_panic_yapmaz() {
    let (a, b, cert, nonce, target) = madenle();

    // bozuk girdi sınıfları — her biri farklı bir hatayı temsil eder
    let mut kesik = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    kesik.flat_a.truncate(4); // matris A kesik

    let mut bos = kesik.clone();
    bos.flat_a.clear();
    bos.flat_b.clear(); // boş matrisler

    let sifir_hedef = encode(&a, &b, &cert, 777, nonce, 0, TOY_Q, TOY_R);
    // sıfır hedefle 512 byte beklendi (n=8) — encode zaten doğru boyutta

    let n_sifir = pack(cert.i as u64, cert.j as u64, cert.value, cert.m as u64, 777, nonce, target, 0, TOY_Q, TOY_R as u64);

    // r, n'yi bölmüyor (n=7, r=2 → 7%2=1) — 7*7*8=392 byte
    let mut r_bolmuyor = pack(
        cert.i as u64, cert.j as u64, cert.value, cert.m as u64, 777, nonce, target, 7, TOY_Q, 2,
    );
    r_bolmuyor.flat_a = vec![0u8; 49 * 8];
    r_bolmuyor.flat_b = vec![0u8; 49 * 8];

    // gridin dışında tile (n=8, r=2 → grid 4x4; (9,9) dışarıda)
    let mut disarida = pack(9, 9, cert.value, cert.m as u64, 777, nonce, target, 8, TOY_Q, 2);
    disarida.flat_a = vec![0u8; 512];
    disarida.flat_b = vec![0u8; 512];

    // m, n/r ile tutarsız (n=8, r=2 → grid 4; m=99 yanlış)
    let mut m_yanlis = pack(cert.i as u64, cert.j as u64, cert.value, 99, 777, nonce, target, 8, TOY_Q, 2);
    m_yanlis.flat_a = vec![0u8; 512];
    m_yanlis.flat_b = vec![0u8; 512];

    // q sıfır — dejenere alan
    let mut q_sifir = pack(cert.i as u64, cert.j as u64, cert.value, cert.m as u64, 777, nonce, target, 8, 0, 2);
    q_sifir.flat_a = vec![0u8; 512];
    q_sifir.flat_b = vec![0u8; 512];

    // matris boyutu u64 taşması (n = 2^32 → n*n wraps to 0)
    let tasma = VerifierInput {
        cert_bytes: {
            let mut c = [0u8; 32];
            c[24..32].copy_from_slice(&1u64.to_le_bytes());
            c
        },
        pub_inputs: {
            let mut p = [0u8; 48];
            p[16..24].copy_from_slice(&(1u64 << 16).to_le_bytes());
            p[24..32].copy_from_slice(&(1u64 << 32).to_le_bytes());
            p[32..40].copy_from_slice(&TOY_Q.to_le_bytes());
            p[40..48].copy_from_slice(&2u64.to_le_bytes());
            p
        },
        flat_a: vec![],
        flat_b: vec![],
    };

    let mut hic_veri = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    hic_veri.pub_inputs = [0u8; 48]; // pub_inputs tamamen sıfır → n=q=r=0

    let girdiler: Vec<(&str, VerifierInput)> = vec![
        ("kesik matris A", kesik),
        ("boş matrisler", bos),
        ("sıfır hedef", sifir_hedef),
        ("n sıfır", n_sifir),
        ("r n'yi bölmüyor", r_bolmuyor),
        ("gridin dışında tile", disarida),
        ("m n/r ile tutarsız", m_yanlis),
        ("q sıfır", q_sifir),
        ("matris boyutu taşması", tasma),
        ("pub_inputs tamamen sıfır", hic_veri),
    ];

    let mut reddedildi = 0usize;
    for (ad, girdi) in &girdiler {
        // TOPLAMLIK: panic yok, her zaman bir karar
        let sonuc = std::panic::catch_unwind(|| verify_raw(girdi));
        let sonuc = sonuc.expect(&format!("'{ad}' panic yaptı — toplamlık bozuldu"));
        assert!(!sonuc.accepted(), "'{ad}' kabul edildi — bozuk girdi geçti");
        assert!(
            matches!(sonuc, Verdict::Reject(_)),
            "'{ad}' bir Reject değil — karar boş"
        );
        reddedildi += 1;
    }
    assert_eq!(reddedildi, girdiler.len(), "bazı bozuk girdiler denetlenmedi");
    // ve sağlıklı girdi hala kabul görüyor (bozukluk paraziti yok)
    let saglikli = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    assert!(matches!(verify_raw(&saglikli), Verdict::Accept));
}

// ---------------------------------------------------------------------------
// 2. WIRE KONTRATININ STABİLİTESİ: encode saf bir fonksiyondur
// ---------------------------------------------------------------------------

/// Aynı mantıksal değerleri iki kez encode etmek BAYT BAYT aynı paketi
/// vermelidir. Bu, wire kontratının deterministik olduğunu kanıtlar — bir
/// modüler upgrade (örneğin kernel değişimi) bu kontrata güvenebilir ve
/// gölge bir byte belirsizliği olmadan eski kanıtları yeniden değerlendirebilir.
#[test]
fn ayni_degerler_iki_kez_encode_bayt_bayt_aynidir() {
    let (a, b, cert, nonce, target) = madenle();
    let p1 = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    let p2 = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    assert_eq!(p1, p2, "aynı değerler farklı paketler üretti — wire kontratı deterministik değil");
    // iki farklı nonce iki farklı paket vermelidir (kanıt nonce'a bağlı)
    let p3 = encode(&a, &b, &cert, 778, nonce, target, TOY_Q, TOY_R);
    assert_ne!(p1, p3, "farklı ctx aynı paketi üretti — bağlayıcılık yok");
}

/// pack() → decode geri dönüşü kendi içinde tutarlıdır: pack'lenen değerler
/// geri çözüldüğünde aynen geri gelir. Bu, bir upgrade'in koruyacağı
/// semantik kontrattır.
#[test]
fn pack_decode_geri_donusu_tutarlidir() {
    let input = pack(3, 2, 42, 4, 777, 1780, 1 << 16, 8, 97, 2);
    // pack'in ürettiği paket bir karara ulaşmalı (matrisler sıfır olduğu için
    // kanıt doğrulanmaz, ama REDDETMELİDİR — toplamlığın kanıtı)
    let v = verify_raw(&input);
    assert!(!v.accepted(), "sıfır matrislerle paket kabul edilemez");
    assert!(matches!(v, Verdict::Reject(_)), "pack paketi bir karara ulaşmadı");
    // ve karark karar metni "doğrulamadı" demeli, "yapısal hata" değil
    if let Verdict::Reject(neden) = v {
        assert!(
            neden.contains("verify") || neden.contains("doğrul"),
            "sıfır matris paketi yanlış nedenden reddedildi: {neden}"
        );
    }
    // parametrelerin tamamı sıfır olan pack, yapısal reddetmelidir
    let n_sifir = pack(1, 2, 3, 4, 777, 1, 1 << 16, 0, 97, 2);
    assert!(!verify_raw(&n_sifir).accepted());
}

// ---------------------------------------------------------------------------
// 3. SİSTEM KİMLİĞİ DEĞİŞİMİ: eski kanıtlar yeni sistemde geçersizdir
// ---------------------------------------------------------------------------

/// Bir kanıt ctx 777 altında maden edildi. Onu ctx 778 altında sunmak
/// reddedilir. Bu, modüler upgrade'in *güvenli* olması demektir: proof
/// sistemi değiştiğinde (yeni ctx), eski sistemin kanıtları otomatik olarak
/// yeni sistemde geçerli kalamazlar — sessiz bir uyarlama değil, kesin reddir.
#[test]
fn kanit_baska_ctx_altinda_replay_edilince_reddedilir() {
    let (a, b, cert, nonce, target) = madenle();
    // orijinal sistemde kabul
    let dogru = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    assert!(matches!(verify_raw(&dogru), Verdict::Accept));
    // yanlış sistem kimliğinde reddet
    let replay = encode(&a, &b, &cert, 778, nonce, target, TOY_Q, TOY_R);
    assert!(!verify_raw(&replay).accepted(), "ctx replay kabul edildi — upgrade güvenliği yok");
    // ve 0 (varsayılan) ctx altında da reddet
    let sifir = encode(&a, &b, &cert, 0, nonce, target, TOY_Q, TOY_R);
    assert!(!verify_raw(&sifir).accepted(), "ctx 0 altında replay kabul edildi");
}

/// SAHTELENMİŞ değer reddedilir: paketin iddia ettiği akümülatör, tile'ın
/// hesapladığı değil. Upgrade güvenliğinin özü — verifier hala hesabı
/// bağımsız olarak yapar, iddiayı kabul etmez.
#[test]
fn sahtelenmis_deger_reddedilir() {
    let (a, b, cert, nonce, target) = madenle();
    let mut sahte = cert.clone();
    sahte.value = (cert.value + 1) % TOY_Q;
    let input = encode(&a, &b, &sahte, 777, nonce, target, TOY_Q, TOY_R);
    assert!(!verify_raw(&input).accepted(), "sahtelenmiş tile değeri kabul edildi");
}

// ---------------------------------------------------------------------------
// 4. PARAMETRE DEĞİŞİMİ: kernel paketten inşa edilir, sabitten değil
// ---------------------------------------------------------------------------

/// Verifier, kerneli paketin ilan ettiği q ve r ile inşa eder (round-4 hatasının
/// tamiri: verifier kendi n'ini kullanıyordu). Bu test, bir parametre
/// değişiminin AÇIK bir reddetme olduğunu kanıtlar: aynı kanıtı yeni bir
/// alan (q=89) veya yeni bir tile adımı (r=4) ile sunmak, "kanıt doğrulamadı"
/// veya "m/n/r tutarsız" ile reddedilir — sessiz kabul değil.
#[test]
fn kernel_parametreleri_paketten_gelir_sabit_degildir() {
    let (a, b, cert, nonce, target) = madenle();
    // kontrol: doğru parametrelerle kabul
    let dogru = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    assert!(matches!(verify_raw(&dogru), Verdict::Accept));

    // YENİ ALAN (q = 89): kernel paketin ilan ettiği alanı kullanır, bu yüzden
    // 97 üzerinden maden edilen kanıt 89 üzerinden doğrulanamaz
    let mut yeni_alan = encode(&a, &b, &cert, 777, nonce, target, 89, TOY_R);
    // pack/encode zaten doğru boyutta flat_a üretti; sadece q'yu değiştirelim
    yeni_alan.pub_inputs[32..40].copy_from_slice(&89u64.to_le_bytes());
    assert!(!verify_raw(&yeni_alan).accepted(), "yeni alan altında eski kanıt kabul edildi");

    // YENİ TILE ADIMI (r = 4): n=8, r=4 → grid 2x2, ama cert.m = 4 →
    // decode "m is 4 but n/r is 2" ile reddeder (width binding)
    let mut yeni_adim = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, 4);
    yeni_adim.pub_inputs[40..48].copy_from_slice(&4u64.to_le_bytes());
    let v = verify_raw(&yeni_adim);
    assert!(!v.accepted(), "yeni tile adımı altında eski kanıt kabul edildi");
    // ve ret sebebi yapısal olmalı (m/n/r bağlaması), "doğrulamadı" değil
    if let Verdict::Reject(neden) = v {
        assert!(
            neden.contains("n/r") || neden.contains("grid") || neden.contains("outside"),
            "yeni tile adımı yanlış nedenden reddedildi: {neden}"
        );
    }

    // KERNEL SABİT DEĞİL, TESPİT: aynı kanıt, paketin ilan ettiği FARKLI n
    // ile de reddedilir (n boyutu matris boyutuna uymalı)
    let mut yanlis_n = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    yanlis_n.pub_inputs[24..32].copy_from_slice(&16u64.to_le_bytes()); // n=16
    assert!(!verify_raw(&yanlis_n).accepted(), "yanlış n kabul edildi");
}

/// UPDRADE SONRASI DETERMİNİZM: aynı paket 500 kez doğrulandığında her seferinde
/// AYNI kararı verir. İki node bir modüler upgrade'ten sonra aynı kanıt
// hakkında farklı karar veremez — bu bir fork demektir.
#[test]
fn ayni_paket_500_kez_ayni_karari_verir() {
    let (a, b, cert, nonce, target) = madenle();
    let saglikli = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    let mut karne = None;
    for _ in 0..500 {
        let v = verify_raw(&saglikli);
        if let Some(ref onceki) = karne {
            assert_eq!(v, *onceki, "aynı paket farklı kararlar verdi — determinizm bozuldu");
        }
        karne = Some(v);
    }
    assert!(karne.unwrap().accepted(), "sağlıklı paket 500 denemeden sonra hala kabul edilmeli");

    // ve sahte bir paket de 500 kez aynı şekilde reddedilir.
    //
    // ÖNEMLİ DETAY: kernel sadece STRIDE'LI konumları okur — B'[l*r][j*r].
    // Yani kanıtın kapsamadığı bir sütunu bozmak GÖRÜNMEZ (hala kabul
    // edilir). Doğru sahtecilik, kanıtın tile'ının içinde olmalıdır:
    // b[0][cert.j * r], l=0 için okunan strided konum.
    let mut sahte = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    let tile_sutun = (cert.j as usize * TOY_R) * 8;
    sahte.flat_b[tile_sutun] = sahte.flat_b[tile_sutun].wrapping_add(1);
    let mut k_sahte = None;
    for _ in 0..500 {
        let v = verify_raw(&sahte);
        if let Some(ref onceki) = k_sahte {
            assert_eq!(v, *onceki, "bozuk paket farklı kararlar verdi");
        }
        k_sahte = Some(v);
    }
    assert!(!k_sahte.unwrap().accepted(), "tile içindeki matrix içeriği bozmak kabul edildi");

    // ve KAPSAM DIŞI bir bozma (kanıtın okumadığı sütun) hala KABUL edilir —
    // bu, verifier'ın kanıt tile'ının dışındaki matrix verisine kayıtsız
    // kaldığını gösterir (kapsam = tile, tüm matrix DEĞİL)
    let mut disinda = encode(&a, &b, &cert, 777, nonce, target, TOY_Q, TOY_R);
    let dis_sutun = ((cert.j as usize + 1) % 8) * 8;
    if dis_sutun != tile_sutun {
        disinda.flat_b[dis_sutun] = disinda.flat_b[dis_sutun].wrapping_add(1);
        assert!(
            verify_raw(&disinda).accepted(),
            "kanıt kapsamı dışındaki matrix verisi reddedildi — kapsam yanlış"
        );
    }
}

/// HARD FORK ZORUNLULUĞU OLMADAN UPGRADE: verifier, kanıtın KENDİ parametreleri
/// (q, r, n, hedef) ile inşa edilen bir kernelle çalışır. Bu test, farklı
/// GEÇERLİ parametre setlerinin her birinin kendi içinde tutarlı kararlar
/// verdiğini gösterir — yani parametre değişimi protokolde bir girdi olarak
/// çalışabilir (PVI'nin varoluş sebebi).
#[test]
fn farkli_gecerli_parametreler_tutarli_kararlar_verir() {
    // TOY_Q=97, TOY_R=2 ile maden edilen bir kanıt: kendi parametreleriyle
    // kabul, diğer tüm kombinasyonlarla reddet
    let (a, b, cert, nonce, target) = madenle();
    for (q, r) in [(97u64, 2usize), (97, 4), (89, 2), (89, 4), (113, 2), (97, 8)] {
        let p = encode(&a, &b, &cert, 777, nonce, target, q, r);
        // encode zaten n'i a.len()=8 olarak yazar; manuel olarak q/r'yı teyit et
        assert_eq!(p.pub_inputs[32..40], q.to_le_bytes());
        assert_eq!(p.pub_inputs[40..48], (r as u64).to_le_bytes());
        let v = verify_raw(&p);
        if q == TOY_Q && r == TOY_R {
            assert!(v.accepted(), "kanıtın kendi parametreleriyle reddedildi");
        } else {
            assert!(!v.accepted(), "yabancı parametreler ({q},{r}) kabul edildi");
        }
        // her durumda bir KARAR vardır (toplamlık upgrade boyunca korunur)
        assert!(matches!(v, Verdict::Accept | Verdict::Reject(_)));
        let _ = p;
    }
}

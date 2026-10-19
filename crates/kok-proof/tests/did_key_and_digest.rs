//! YENI integration test: kok-proof'in test-disi public API'i — did:key
//! katmani (encode/decode multibase, did olusturma, gecerlilik) ve sha256
//! digest.
//!
//! Kapsanan test-disi public fonksiyonlar (src icinde, mevcut hicbir test
//! tarafindan cagrilmayanlar):
//!   - decode_multibase_pubkey (31 satir — EN KRITIK; tum hata dallari)
//!   - encode_multibase_pubkey
//!   - did_from_multibase / did_from_public_key
//!   - is_valid_did_key
//!   - sha256_digest
//!
//! Mevcut 19 unit test (src icindeki #[cfg(test)] mod) public_key_from_did,
//! sign/verify_with_did, b58_* ve verification_method_id'yi kapliyor; bu
//! fonksiyonlari DOGRUDAN cagirmiyor. Bu dosya yalnizca PUBLIC API'i
//! kullaniyor (integration test = siyah kutu) ve HICBIR dis cagri yapmiyor.

use kok_proof::did::{
    b58_decode, b58_encode, decode_multibase_pubkey, did_from_multibase, did_from_public_key,
    encode_multibase_pubkey, is_valid_did_key, multibase_from_did, verify_with_did, DidError,
    Keypair, MULTICODEC_ED25519_PUB, PUBLIC_KEY_LEN, SIGNATURE_LEN,
};
use kok_proof::sha256_digest;
use kok_proof::{work_canonical, MiningProof, PROOF_TYPE, PROOF_VERSION};

/// Bos multibase string'i reddedilmeli (MalformedMultibase).
#[test]
fn decode_multibase_pubkey_bos_string_reddedilir() {
    let err = decode_multibase_pubkey("").unwrap_err();
    assert!(matches!(err, DidError::MalformedMultibase(_)), "{err:?}");
}

/// 'z' (base58btc) disinda bir multibase on eki reddedilmeli.
#[test]
fn decode_multibase_pubkey_yanlis_on_ek_reddedilir() {
    let err = decode_multibase_pubkey("Z6MkzJcSQnD").unwrap_err();
    assert!(matches!(err, DidError::MalformedMultibase(_)), "{err:?}");
}

/// Cozulen yapi 2 + 32 = 34 bayt degilse reddedilmeli.
#[test]
fn decode_multibase_pubkey_yanlis_uzunluk_reddedilir() {
    // 0xed01 + 32 bayt yerine sadece 0xed01 (2 bayt)
    let kisa = format!("z{}", b58_encode(&MULTICODEC_ED25519_PUB));
    let err = decode_multibase_pubkey(&kisa).unwrap_err();
    assert!(matches!(err, DidError::MalformedMultibase(_)), "{err:?}");

    // 34 bayt ama hepsi sifir degil — uzunluk dogru, asagidaki multicodec testi
    let uzun = format!("z{}", b58_encode(&[0u8; 40]));
    assert!(decode_multibase_pubkey(&uzun).is_err());
}

/// Multicodec tag'i 0xed01 (Ed25519 pub) degilse WrongMulticodec ile
/// reddedilmeli — yanlis anahtar turu olarak cozulmemeli.
#[test]
fn decode_multibase_pubkey_yanlis_multicodec_reddedilir() {
    // 0x1200 = P-256 (baska bir anahtar turu)
    let mut payload = vec![0x12, 0x00];
    payload.extend_from_slice(&[0u8; PUBLIC_KEY_LEN]);
    let yabanci = format!("z{}", b58_encode(&payload));
    let err = decode_multibase_pubkey(&yabanci).unwrap_err();
    assert!(matches!(err, DidError::WrongMulticodec(_)), "{err:?}");
}

/// Gecerli bir Ed25519 anahtari base58btc + multicodec uzerinden tur-arasi
/// (round-trip) ayni 32 bayta cozulmeli.
#[test]
fn encode_decode_multibase_roundtrip_tutarli() {
    for seed in [
        [0x42; 32],
        [0x01; 32],
        [0xff; 32],
        *b"kok-mesh-kanit-seed-0123456789ab",
    ] {
        let kp = Keypair::from_seed(&seed);
        let mb = encode_multibase_pubkey(&kp.public);
        assert_eq!(decode_multibase_pubkey(&mb).unwrap(), kp.public);
    }
}

/// Encode her zaman 'z' ile baslamali ve icerik 0xed01 + anahtar olmali.
#[test]
fn encode_multibase_pubkey_yapi_doğru() {
    let pk = [0x77; PUBLIC_KEY_LEN];
    let mb = encode_multibase_pubkey(&pk);
    assert!(mb.starts_with('z'), "multibase base58btc on eki 'z' olmali");
    let ham = b58_decode(&mb[1..]).unwrap();
    assert_eq!(&ham[0..2], &MULTICODEC_ED25519_PUB);
    assert_eq!(&ham[2..], &pk[..]);
}

/// Farkli anahtarlar farkli multibase degerleri uretmeli (enjekte-edebilir).
#[test]
fn encode_multibase_pubkey_farkli_anahtarlar_farklidir() {
    let a = encode_multibase_pubkey(&[0x11; 32]);
    let b = encode_multibase_pubkey(&[0x22; 32]);
    assert_ne!(a, b);
}

/// did_from_multibase "did:key:" on ekini dogru eklemeli.
#[test]
fn did_from_multibase_on_ek_dogru() {
    assert_eq!(did_from_multibase("z6Mkabc"), "did:key:z6Mkabc");
    assert_eq!(did_from_multibase(""), "did:key:");
}

/// did_from_public_key "did:key:z" ile baslamali ve kendine karsilik
/// cozulebilmeli (self-resolution).
#[test]
fn did_from_public_key_self_resolving() {
    let kp = Keypair::from_seed(&[0x09; 32]);
    let did = did_from_public_key(&kp.public);
    assert!(did.starts_with("did:key:z"), "{did}");
    // did -> multibase -> public key geri kazanilmali
    let mb = multibase_from_did(&did).unwrap();
    assert_eq!(decode_multibase_pubkey(&mb).unwrap(), kp.public);
}

/// did_from_public_key ile did_from_multibase(encode(...)) ayni sonucu vermeli
/// (tutarli uretim yolu).
#[test]
fn did_from_public_key_ve_multibase_tutarli() {
    let pk = [0x5a; 32];
    assert_eq!(
        did_from_public_key(&pk),
        did_from_multibase(&encode_multibase_pubkey(&pk))
    );
}

/// is_valid_did_key: gecerli did true, yapisi bozuk olanlar false.
#[test]
fn is_valid_did_key_gecerli_ve_gecersiz() {
    let kp = Keypair::from_seed(&[0x33; 32]);
    assert!(is_valid_did_key(&kp.did));

    // did:key degil
    assert!(!is_valid_did_key("did:example:1234"));
    assert!(!is_valid_did_key("did:web:example.com"));
    // bos
    assert!(!is_valid_did_key(""));
    // multibase kismi bos
    assert!(!is_valid_did_key("did:key:"));
    // 'z' disinda on ek
    assert!(!is_valid_did_key("did:key:Z6Mk"));
    // yanlis multicodec (P-256)
    let mut yanlis = vec![0x12, 0x00];
    yanlis.extend_from_slice(&[0u8; PUBLIC_KEY_LEN]);
    assert!(!is_valid_did_key(&format!(
        "did:key:z{}",
        b58_encode(&yanlis)
    )));
    // base58 disi karakter
    assert!(!is_valid_did_key("did:key:z0/O+l"));
    // uzunluk yanlis
    assert!(!is_valid_did_key(&format!(
        "did:key:z{}",
        b58_encode(&MULTICODEC_ED25519_PUB)
    )));
}

/// sha256_digest bilinen (NIST) vektorlerle ayni 32 bayti vermeli — bu,
/// receipt'in ucuncu tarafca yeniden-hesaplanabilmesinin temeli.
#[test]
fn sha256_digest_bilinen_vektorler() {
    // sha256("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    let bos = sha256_digest(b"");
    assert_eq!(
        bos,
        [
            0xe3, 0xb0, 0xc4, 0x42, 0x98, 0xfc, 0x1c, 0x14, 0x9a, 0xfb, 0xf4, 0xc8, 0x99, 0x6f,
            0xb9, 0x24, 0x27, 0xae, 0x41, 0xe4, 0x64, 0x9b, 0x93, 0x4c, 0xa4, 0x95, 0x99, 0x1b,
            0x78, 0x52, 0xb8, 0x55
        ]
    );

    // sha256("abc") = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
    let abc = sha256_digest(b"abc");
    assert_eq!(
        abc,
        [
            0xba, 0x78, 0x16, 0xbf, 0x8f, 0x01, 0xcf, 0xea, 0x41, 0x41, 0x40, 0xde, 0x5d, 0xae,
            0x22, 0x23, 0xb0, 0x03, 0x61, 0xa3, 0x96, 0x17, 0x7a, 0x9c, 0xb4, 0x10, 0xff, 0x61,
            0xf2, 0x00, 0x15, 0xad
        ]
    );
}

/// sha256_digest deterministiktir ve farkli girdiler farkli cikti uretir.
#[test]
fn sha256_digest_deterministik_ve_enjekte_edilemez() {
    assert_eq!(sha256_digest(b"kok"), sha256_digest(b"kok"));
    assert_ne!(sha256_digest(b"kok"), sha256_digest(b"KOK"));
    // 32 bayt uzunlugunda digest
    assert_eq!(sha256_digest(b"uzunluk kontrolu").len(), 32);
}

/// Keypair::from_seed ile uretilen did her zaman gecerli bir did:key olmali
/// (butun kanit katmaninin uzerine insa oldugu ozellik).
#[test]
fn keypair_did_her_zaman_gecerli() {
    for seed in [[0; 32], [1; 32], [0xfe; 32]] {
        let kp = Keypair::from_seed(&seed);
        assert!(is_valid_did_key(&kp.did), "seed icin gecersiz did");
        assert_eq!(kp.public.len(), PUBLIC_KEY_LEN);
    }
}

// ---------------------------------------------------------------------------
// sign_receipt — test-disi public fn (lib.rs): receipt Ed25519 imzasi
// ---------------------------------------------------------------------------
/// Test icin minimal, gecerli bir kanit olusturur (sayilar semboliktir;
/// sign_receipt MatMul dogrulamasi yapmaz — yalnizca kanonik zarf uzerine
/// imza atar).
fn ornek_kanit(seed: &[u8; 32]) -> (Keypair, MiningProof) {
    let kp = Keypair::from_seed(seed);
    let proof = MiningProof {
        proof_version: PROOF_VERSION,
        proof_type: PROOF_TYPE.to_string(),
        layer: "G".to_string(),
        q: 8,
        n: 64,
        r: 16,
        task_program: "kok/g-layer-matmul-toy".to_string(),
        task_fee: 1_000,
        task_burn_rate_per_mille: 50,
        program_commit: "a".repeat(64),
        matrix_a: vec![vec![1, 2], vec![3, 4]],
        matrix_b: vec![vec![5, 6], vec![7, 8]],
        input_commit: "b".repeat(64),
        ctx: 7,
        nonce: 42,
        target: 0x00ff,
        cert_i: 0,
        cert_j: 0,
        cert_value: 1234,
        cert_m: 2,
        miner_did: kp.did.clone(),
        receipt_prev: "0".repeat(64),
        receipt_hash: "c".repeat(64),
        signature: String::new(),
    };
    (kp, proof)
}

/// sign_receipt 64 baytlik bir Ed25519 imzasi uretmeli ve bu imza, did'den
/// geri kazanilan anahtar altinda kanonik zarf uzerine dogrulanmalidir.
#[test]
fn sign_receipt_did_altinda_dogrulanir() {
    let (kp, proof) = ornek_kanit(&[0x7a; 32]);
    let sig = kok_proof::sign_receipt(&kp.secret, &proof);
    assert_eq!(sig.len(), SIGNATURE_LEN);

    // receipt imzasi kanonik zarfin sha256'i uzerinedir (yeniden-hesaplanabilir)
    let message = sha256_digest(work_canonical(&proof).as_bytes());
    assert!(verify_with_did(&kp.did, &message, &sig).is_ok());
}

/// sign_receipt deterministiktir (ayni sir + ayni kanit → ayni imza).
#[test]
fn sign_receipt_deterministik() {
    let (kp, proof) = ornek_kanit(&[0x2b; 32]);
    let a = kok_proof::sign_receipt(&kp.secret, &proof);
    let b = kok_proof::sign_receipt(&kp.secret, &proof);
    assert_eq!(a, b);
}

/// Baska bir sirla atilan imza orijinal did altinda DOGRULANMAMALIDIR
/// (kimlik baglayiciligi).
#[test]
fn sign_receipt_baska_sir_red_edilir() {
    let (kp, proof) = ornek_kanit(&[0x3c; 32]);
    let baska = Keypair::from_seed(&[0x4d; 32]);
    let sig = kok_proof::sign_receipt(&baska.secret, &proof);
    let message = sha256_digest(work_canonical(&proof).as_bytes());
    assert!(verify_with_did(&kp.did, &message, &sig).is_err());
}

/// Kanonik zarfa giren bir alan (nonce) degistirilirse imza degismeli —
/// bu, kanitin icine bagli (binding) oldugunu gosterir.
#[test]
fn sign_receipt_kanonik_alana_bagli() {
    let (kp, mut proof) = ornek_kanit(&[0x5e; 32]);
    let sig1 = kok_proof::sign_receipt(&kp.secret, &proof);
    proof.nonce = 43;
    let sig2 = kok_proof::sign_receipt(&kp.secret, &proof);
    assert_ne!(sig1, sig2);
    // eski imza yeni zarfi dogrulamaz
    let msg2 = sha256_digest(work_canonical(&proof).as_bytes());
    assert!(verify_with_did(&kp.did, &msg2, &sig1).is_err());
}

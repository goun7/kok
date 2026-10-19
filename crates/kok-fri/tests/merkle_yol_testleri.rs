//! air.rs Merkle yolu testleri (core-final, LEAD).
//! Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.

use kok_fri::air::{leaf_hash, merkle_check, merkle_layers, merkle_open, merkle_root, PathStep};

#[test]
fn merkle_layers_single_leaf_one_layer() {
    let l = merkle_layers(&[7]);
    assert_eq!(l.len(), 1); // sadece kök katmanı
}

#[test]
fn merkle_layers_two_leaves_two_layers() {
    let l = merkle_layers(&[1, 2]);
    assert_eq!(l.len(), 2);
    assert_eq!(l[0].len(), 2);
    assert_eq!(l[1].len(), 1); // kök
}

#[test]
fn merkle_layers_odd_count_promotes_dup() {
    // 3 yaprak: katman1 3 düğüm, son düğüm dup ile yukarı çıkar
    let l = merkle_layers(&[1, 2, 3]);
    assert!(l[0].len() >= 3);
}

#[test]
fn merkle_open_and_check_roundtrip_even() {
    let leaves = [11u64, 22, 33, 44];
    let root = merkle_root(&leaves);
    for idx in 0..leaves.len() {
        let path = merkle_open(&leaves, idx);
        assert!(
            merkle_check(root, idx, leaves[idx], &path),
            "idx {idx} doğrulanmadı"
        );
    }
}

#[test]
fn merkle_open_and_check_roundtrip_odd() {
    // 5 yaprak — Dup adımı zorunlu
    let leaves = [3u64, 1, 4, 1, 5];
    let root = merkle_root(&leaves);
    for idx in 0..leaves.len() {
        let path = merkle_open(&leaves, idx);
        assert!(
            merkle_check(root, idx, leaves[idx], &path),
            "idx {idx} (odd) doğrulanmadı"
        );
    }
}

#[test]
fn merkle_open_and_check_single_leaf() {
    let leaves = [99u64];
    let root = merkle_root(&leaves);
    let path = merkle_open(&leaves, 0);
    assert!(path.is_empty()); // kök = tek yaprak
    assert!(merkle_check(root, 0, leaves[0], &[]));
}

#[test]
fn merkle_open_and_check_two_leaves() {
    let leaves = [5u64, 9];
    let root = merkle_root(&leaves);
    for idx in 0..2 {
        let path = merkle_open(&leaves, idx);
        assert_eq!(path.len(), 1);
        assert!(merkle_check(root, idx, leaves[idx], &path));
    }
}

#[test]
fn merkle_check_rejects_wrong_leaf_value() {
    let leaves = [11u64, 22, 33, 44];
    let root = merkle_root(&leaves);
    let path = merkle_open(&leaves, 1);
    // doğru yol, yanlış değer
    assert!(!merkle_check(root, 1, 999, &path));
}

#[test]
fn merkle_check_rejects_wrong_index_position_binding() {
    // F9: yol bir indeksten alınıp başka indekste kullanılamaz
    let leaves = [11u64, 22, 33, 44];
    let root = merkle_root(&leaves);
    let path0 = merkle_open(&leaves, 0);
    // leaves[1] değerini indeks 0'da声称 etmek — değer farklı, reddedilir
    assert!(!merkle_check(root, 0, leaves[1], &path0));
}

#[test]
fn merkle_check_rejects_position_replay_same_value() {
    // Aynı değer iki yaprakta varsa, yol bir indeksten diğerine taşınamaz
    let leaves = [42u64, 42];
    let root = merkle_root(&leaves);
    let path0 = merkle_open(&leaves, 0);
    // değer AYNI (42) ama indeks farklı → position-binding reddetmeli
    assert!(!merkle_check(root, 1, 42, &path0));
}

#[test]
fn merkle_check_rejects_tampered_path() {
    let leaves = [11u64, 22, 33, 44];
    let root = merkle_root(&leaves);
    let mut path = merkle_open(&leaves, 0);
    if let Some(PathStep::Right(n)) = path.first_mut() {
        n[0] ^= 0xff; // bir bayt boz
    } else if let Some(PathStep::Left(n)) = path.first_mut() {
        n[0] ^= 0xff;
    }
    assert!(!merkle_check(root, 0, leaves[0], &path));
}

#[test]
fn merkle_check_rejects_empty_path_multi_leaf() {
    // çok yapraklı ağaçta boş yol kök ile eşleşmemeli
    let leaves = [11u64, 22, 33, 44];
    let root = merkle_root(&leaves);
    assert!(!merkle_check(root, 0, leaves[0], &[]));
}

#[test]
fn merkle_root_consistent_for_same_leaves() {
    assert_eq!(merkle_root(&[1u64, 2, 3]), merkle_root(&[1u64, 2, 3]));
}

#[test]
fn merkle_root_differs_for_different_leaves() {
    assert_ne!(merkle_root(&[1u64, 2, 3]), merkle_root(&[1u64, 2, 4]));
}

#[test]
fn merkle_root_differs_for_reordered_leaves() {
    // sıralama bağımlı — 3,2,1 ≠ 1,2,3
    assert_ne!(merkle_root(&[1u64, 2, 3]), merkle_root(&[3u64, 2, 1]));
}

#[test]
fn leaf_hash_binds_position() {
    // aynı değer farklı indekste farklı hash
    assert_ne!(leaf_hash(0, 7), leaf_hash(1, 7));
}

#[test]
fn leaf_hash_binds_value() {
    assert_ne!(leaf_hash(0, 7), leaf_hash(0, 8));
}

#[test]
fn leaf_hash_is_deterministic() {
    assert_eq!(leaf_hash(3, 9), leaf_hash(3, 9));
}

#[test]
fn merkle_open_path_length_is_log2_rounded_up() {
    // 8 yaprak → 3 katman yol
    let leaves = [1u64, 2, 3, 4, 5, 6, 7, 8];
    assert_eq!(merkle_open(&leaves, 3).len(), 3);
    // 5 yaprak → hala 3 adım (yukarı doğru)
    let leaves5 = [1u64, 2, 3, 4, 5];
    assert_eq!(merkle_open(&leaves5, 2).len(), 3);
}

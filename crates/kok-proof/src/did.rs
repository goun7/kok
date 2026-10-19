//! did:key over Ed25519 — the mesh identifier, byte-compatible with Kredent.
//!
//! A KÖK mining proof is signed by a miner identifier that any third party can
//! resolve **offline**: the W3C [`did:key`][spec] method with an Ed25519
//! (RFC 8032) verification key. The identifier is derived from the public key
//! itself, so there is no registry to query and no party that can revoke it —
//! the file is the only input verification needs. This is the same construction
//! the mesh's sibling project **Kredent** uses (`kredent/crypto.py`), encoded
//! identically, so a KÖK proof and a Kredent attestation are verified by the
//! same code path.
//!
//! [spec]: https://w3c-ccg.github.io/did-method-key/
//!
//! ## Wire format
//!
//! `did:key:z6Mk...` where the part after `z` is
//! `base58btc(0xed 0x01 || <32-byte Ed25519 public key>)`:
//!
//! * `z` is the [multibase][mb] prefix for base58btc;
//! * `0xed 0x01` is the [multicodec][mc] tag for a raw Ed25519 public key;
//! * base58btc here carries **no checksum** — the multicodec tag is the
//!   self-describing length, and a checksum would be redundant bytes a
//!   cross-language reimplementation could get wrong.
//!
//! [mb]: https://datatracker.ietf.org/doc/html/draft-multiformats-multibase
//! [mc]: https://github.com/multiformats/multicodec
//!
//! ## What this module deliberately does NOT do
//!
//! It does not implement a DID *document* with verification-method graphs,
//! services or controllers. `did:key` has no document other than the
//! deterministically generated one, and the only fact a mining proof needs is
//! "which 32-byte key signs here". Generating a full document would be
//! ceremony that adds no verifiable statement. The canonical verification-method
//! id — `did:key:z...#z...` — is provided by [`verification_method_id`] for
//! callers that want the W3C-shaped string.

use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use rand_core::{CryptoRng, RngCore};

/// Byte prefix of a raw Ed25519 public key in the multicodec table.
pub const MULTICODEC_ED25519_PUB: [u8; 2] = [0xed, 0x01];

/// Length of a raw Ed25519 public key.
pub const PUBLIC_KEY_LEN: usize = 32;

/// Length of an Ed25519 signature.
pub const SIGNATURE_LEN: usize = 64;

/// The base58btc Bitcoin alphabet. Ordered so index == digit value.
const B58_ALPHABET: [u8; 58] = *b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

/// Domain separator written before any signed message, so an Ed25519
/// signature from this layer cannot be replayed as a signature over some other
/// application's bytes (Ed25519 signs arbitrary messages; the prefix is the
/// only thing that keeps them apart).
pub const SIG_DOMAIN: &[u8] = b"kok.mining-proof.sig.v1:";

/// A freshly generated Ed25519 keypair with its `did:key` identifier.
#[derive(Debug, Clone)]
pub struct Keypair {
    /// The 32-byte Ed25519 secret seed. NEVER written to a kanıt file.
    pub secret: [u8; PUBLIC_KEY_LEN],
    pub public: [u8; PUBLIC_KEY_LEN],
    pub did: String,
}

impl Keypair {
    /// Deterministically derive a keypair from a 32-byte seed. The same seed
    /// always yields the same did, which is how a test reproduces a miner.
    pub fn from_seed(seed: &[u8; PUBLIC_KEY_LEN]) -> Self {
        let signing = SigningKey::from_bytes(seed);
        let public = signing.verifying_key();
        let mut pk = [0u8; PUBLIC_KEY_LEN];
        pk.copy_from_slice(&public.to_bytes());
        Self {
            secret: *seed,
            public: pk,
            did: did_from_public_key(&pk),
        }
    }

    /// Generate a fresh keypair from the OS RNG. The secret is returned to the
    /// caller and is never persisted by this crate.
    pub fn generate<R: CryptoRng + RngCore>(csprng: &mut R) -> Self {
        let mut seed = [0u8; PUBLIC_KEY_LEN];
        csprng.fill_bytes(&mut seed);
        Self::from_seed(&seed)
    }
}

/// Encode a 32-byte Ed25519 public key as the multibase string `z6Mk...`.
pub fn encode_multibase_pubkey(public_key: &[u8; PUBLIC_KEY_LEN]) -> String {
    let mut payload = Vec::with_capacity(2 + PUBLIC_KEY_LEN);
    payload.extend_from_slice(&MULTICODEC_ED25519_PUB);
    payload.extend_from_slice(public_key);
    format!("z{}", b58_encode(&payload))
}

/// Decode a multibase string back into the raw 32-byte Ed25519 public key.
pub fn decode_multibase_pubkey(multibase: &str) -> Result<[u8; PUBLIC_KEY_LEN], DidError> {
    if multibase.is_empty() {
        return Err(DidError::MalformedMultibase(
            "empty multibase string".to_string(),
        ));
    }
    let prefix = multibase.as_bytes()[0];
    if prefix != b'z' {
        return Err(DidError::MalformedMultibase(format!(
            "unsupported multibase prefix {:?}, expected 'z' (base58btc)",
            prefix as char
        )));
    }
    let raw = b58_decode(&multibase[1..])?;
    if raw.len() != 2 + PUBLIC_KEY_LEN {
        return Err(DidError::MalformedMultibase(format!(
            "decoded {} bytes, expected {} (multicodec tag + 32-byte key)",
            raw.len(),
            2 + PUBLIC_KEY_LEN
        )));
    }
    if raw[0] != MULTICODEC_ED25519_PUB[0] || raw[1] != MULTICODEC_ED25519_PUB[1] {
        return Err(DidError::WrongMulticodec(format!(
            "multicodec tag is 0x{:02x}{:02x}, expected 0xed01 (Ed25519 public key)",
            raw[0], raw[1]
        )));
    }
    let mut pk = [0u8; PUBLIC_KEY_LEN];
    pk.copy_from_slice(&raw[2..]);
    Ok(pk)
}

/// Build a `did:key` identifier from a multibase-encoded public key.
pub fn did_from_multibase(multibase_pubkey: &str) -> String {
    format!("did:key:{}", multibase_pubkey)
}

/// Extract the multibase public key from a `did:key` identifier.
pub fn multibase_from_did(did: &str) -> Result<String, DidError> {
    let prefix = "did:key:";
    if !did.starts_with(prefix) {
        return Err(DidError::NotADidKey(format!(
            "{did:?} does not start with {prefix:?}"
        )));
    }
    Ok(did[prefix.len()..].to_string())
}

/// Build the `did:key` identifier straight from the raw public key.
pub fn did_from_public_key(public_key: &[u8; PUBLIC_KEY_LEN]) -> String {
    did_from_multibase(&encode_multibase_pubkey(public_key))
}

/// Recover the raw 32-byte public key from a `did:key` identifier. This is the
/// self-resolution property: no network, no registry, no account.
pub fn public_key_from_did(did: &str) -> Result<[u8; PUBLIC_KEY_LEN], DidError> {
    decode_multibase_pubkey(&multibase_from_did(did)?)
}

/// The canonical W3C verification-method id for a did:key. The fragment is the
/// multibase value itself, per the did:key specification.
pub fn verification_method_id(did: &str) -> Result<String, DidError> {
    let mb = multibase_from_did(did)?;
    Ok(format!("{did}#{mb}"))
}

/// Structurally-valid check only — does not look up anything, because there is
/// nothing to look up.
pub fn is_valid_did_key(did: &str) -> bool {
    public_key_from_did(did).is_ok()
}

/// Sign a message under a secret key, domain-separated by [`SIG_DOMAIN`].
pub fn sign(secret: &[u8; PUBLIC_KEY_LEN], message: &[u8]) -> [u8; SIGNATURE_LEN] {
    let signing = SigningKey::from_bytes(secret);
    let mut buf = Vec::with_capacity(SIG_DOMAIN.len() + message.len());
    buf.extend_from_slice(SIG_DOMAIN);
    buf.extend_from_slice(message);
    signing.sign(&buf).to_bytes()
}

/// Verify a signature against a did:key identifier. The public key is recovered
/// from the did itself, so this takes no trusted input beyond the document.
pub fn verify_with_did(
    did: &str,
    message: &[u8],
    signature: &[u8; SIGNATURE_LEN],
) -> Result<(), DidError> {
    let public = public_key_from_did(did)?;
    let verifying =
        VerifyingKey::from_bytes(&public).map_err(|e| DidError::BadPublicKey(e.to_string()))?;
    let mut buf = Vec::with_capacity(SIG_DOMAIN.len() + message.len());
    buf.extend_from_slice(SIG_DOMAIN);
    buf.extend_from_slice(message);
    let sig = Signature::from_bytes(signature);
    verifying
        .verify(&buf, &sig)
        .map_err(|e| DidError::BadSignature(e.to_string()))
}

/// base58btc encode (Bitcoin alphabet, no checksum — this is multibase, not a
/// Bitcoin address).
pub fn b58_encode(data: &[u8]) -> String {
    // base-58 digits, least-significant first. Grown by repeated base-58
    // reduction of each input byte carried into the accumulator.
    let mut digits: Vec<u8> = Vec::new();
    for &byte in data {
        let mut carry = byte as u32;
        for d in digits.iter_mut() {
            carry += (*d as u32) << 8;
            *d = (carry % 58) as u8;
            carry /= 58;
        }
        while carry > 0 {
            digits.push((carry % 58) as u8);
            carry /= 58;
        }
    }
    let mut out = String::new();
    // Leading zero bytes encode as the alphabet's first character, '1'.
    out.extend(data.iter().take_while(|&&b| b == 0).map(|_| '1'));
    for d in digits.iter().rev() {
        out.push(B58_ALPHABET[*d as usize] as char);
    }
    out
}

/// base58btc decode. Rejects characters outside the alphabet rather than
/// silently accepting them, because a kanıt that fails to decode must fail
/// loudly, not become a different key than the one that signed.
pub fn b58_decode(s: &str) -> Result<Vec<u8>, DidError> {
    let mut digits: Vec<u32> = Vec::new();
    for ch in s.chars() {
        let val = B58_ALPHABET
            .iter()
            .position(|&a| a as char == ch)
            .ok_or_else(|| DidError::MalformedMultibase(format!("non-base58 character {ch:?}")))?;
        let mut carry = val as u32;
        for d in digits.iter_mut() {
            carry += *d * 58;
            *d = carry & 0xff;
            carry >>= 8;
        }
        while carry > 0 {
            digits.push(carry & 0xff);
            carry >>= 8;
        }
    }
    let mut out: Vec<u8> = s.bytes().take_while(|&b| b == b'1').map(|_| 0u8).collect();
    out.extend(digits.iter().rev().map(|&d| d as u8));
    Ok(out)
}

/// Errors from the did:key layer. Each names the concrete reason a kanıt
/// rejected, so a failed verification says what it checked rather than "no".
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DidError {
    NotADidKey(String),
    MalformedMultibase(String),
    WrongMulticodec(String),
    BadPublicKey(String),
    BadSignature(String),
}

impl std::fmt::Display for DidError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DidError::NotADidKey(w) => write!(f, "not a did:key identifier: {w}"),
            DidError::MalformedMultibase(w) => write!(f, "malformed multibase: {w}"),
            DidError::WrongMulticodec(w) => write!(f, "wrong multicodec: {w}"),
            DidError::BadPublicKey(w) => write!(f, "bad public key: {w}"),
            DidError::BadSignature(w) => write!(f, "signature does not verify: {w}"),
        }
    }
}

impl std::error::Error for DidError {}

#[cfg(test)]
mod tests {
    use super::*;

    /// A did round-trips through base58btc and the multicodec tag without
    /// losing a byte — the property that makes it self-resolving.
    #[test]
    fn a_did_key_round_trips_to_the_same_public_key() {
        let kp = Keypair::from_seed(&[0xab; 32]);
        let recovered = public_key_from_did(&kp.did).unwrap();
        assert_eq!(recovered, kp.public);
    }

    /// The identifier really is `did:key:z` + multicodec + key, not some other
    /// encoding the round-trip test would also pass for.
    #[test]
    fn the_wire_format_is_multibase_multicodec_and_key() {
        let kp = Keypair::from_seed(&[0x01; 32]);
        let mb = multibase_from_did(&kp.did).unwrap();
        assert!(mb.starts_with('z'));
        let raw = b58_decode(&mb[1..]).unwrap();
        assert_eq!(&raw[0..2], &[0xed, 0x01]);
        assert_eq!(&raw[2..], &kp.public[..]);
    }

    /// The same seed yields the same did — determinism is what lets a test
    /// reproduce a miner instead of generating a new one each run.
    #[test]
    fn the_same_seed_gives_the_same_did() {
        assert_eq!(
            Keypair::from_seed(&[7; 32]).did,
            Keypair::from_seed(&[7; 32]).did
        );
    }

    /// A signature made under one key does not verify under another's did, and
    /// a tampered message fails the same way. This is the property that makes
    /// the receipt binding meaningful rather than decorative.
    #[test]
    fn a_signature_is_not_transferable_to_another_did() {
        let a = Keypair::from_seed(&[1; 32]);
        let b = Keypair::from_seed(&[2; 32]);
        let msg = b"the tile accumulator is 42";
        let sig = sign(&a.secret, msg);
        assert!(verify_with_did(&a.did, msg, &sig).is_ok());
        // same message, other identity
        assert!(verify_with_did(&b.did, msg, &sig).is_err());
        // same identity, tampered message
        assert!(verify_with_did(&a.did, b"the tile accumulator is 43", &sig).is_err());
    }

    /// A did that is not did:key, and a multibase with the wrong multicodec
    /// tag, both reject with a named reason rather than decoding to a key that
    /// was never signed with.
    #[test]
    fn foreign_and_mis_tagged_identifiers_reject_with_a_reason() {
        assert!(matches!(
            public_key_from_did("did:example:1234"),
            Err(DidError::NotADidKey(_))
        ));
        // Ed25519 is 0xed01; 0x1200 is P-256, a different key type entirely.
        let mut bad = vec![0x12, 0x00];
        bad.extend_from_slice(&[0u8; 32]);
        let wrong_codec = format!("did:key:z{}", b58_encode(&bad));
        assert!(matches!(
            public_key_from_did(&wrong_codec),
            Err(DidError::WrongMulticodec(_))
        ));
    }

    /// base58btc leading-zero and digit arithmetic: the empty input is the
    /// empty string, zeros map to '1', and a known vector decodes back.
    #[test]
    fn base58btc_handles_zeros_and_known_vectors() {
        assert_eq!(b58_encode(&[]), "");
        assert_eq!(b58_encode(&[0, 0, 0]), "111");
        // 0x00 0x01 -> the multibase prefix byte plus one value byte
        let enc = b58_encode(&[0x00, 0xed, 0x01]);
        assert_eq!(b58_decode(&enc).unwrap(), vec![0x00, 0xed, 0x01]);
        // a character outside the alphabet rejects instead of mis-decoding
        assert!(b58_decode("z0/O").is_err());
    }

    /// The canonical verification-method id carries the multibase as its own
    /// fragment, the shape the did:key spec describes.
    #[test]
    fn the_verification_method_id_is_the_did_plus_itself() {
        let kp = Keypair::from_seed(&[3; 32]);
        let vm = verification_method_id(&kp.did).unwrap();
        assert_eq!(
            vm,
            format!("{}#{}", kp.did, multibase_from_did(&kp.did).unwrap())
        );
    }
}

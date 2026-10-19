// kok — the mesh kanıt CLI.
//
// `kok create`  : mine a G-layer certificate, bind it to the commissioned
//                 task, sign it under a did:key, write a kanıt file.
// `kok verify`  : re-derive the MatMul tile, the commitments, the receipt
//                 hash and the Ed25519 signature from the file alone.
//                 No secrets, no network, no registry.
//
// The verify path is deliberately the same code a third party would call:
// nothing here is available to the CLI that is not in the library, so "the
// CLI verified it" and "anyone verified it" are the same statement.

use std::path::PathBuf;

use kok_poum::{KwKernel, TOY_N, TOY_Q, TOY_R};
use kok_proof::{
    from_json, genesis_prev, mine, to_json, verify, Keypair, MiningProof, DEFAULT_PROGRAM,
};
use rand_core::OsRng;

const USAGE: &str = "\
kok — KÖK mesh kanıt (proof) tool

USAGE:
    kok create  [--out kanit.json] [--ctx N] [--target 2] [--seed hex]
    kok verify  <kanit.json> [<kanit.json> ...]
    kok selftest

create
    Mines a G-layer MatMul certificate over the canonical toy matrices,
    binds it to the commissioned program and inputs, signs the sha256 receipt
    under a freshly generated did:key, and writes the kanıt file. The secret
    key is printed once to stderr and is never written to disk.

    --ctx N       the task context the certificate is bound to (default 777)
    --target 2^N  the difficulty exponent, in the 'hash % 2^N == 0' sense
                  (default 1, i.e. target 2^1; larger is harder)
    --seed hex    32-byte hex seed for the miner key, for reproducibility
    --prev hex    64-hex receipt hash of the parent kanıt (default: genesis)
    --program S   the commissioned program string (default: kok/g-layer-matmul-toy)

verify
    Independently verifies one or more kanıt files. Each check that fails
    prints the field and the reason. Exit code 0 only if every file verifies.

selftest
    Mines and verifies a kanıt in memory and reports the measured timings.
    Exits non-zero if any check fails.
";

fn toy_matrices(seed: u64) -> (Vec<Vec<u64>>, Vec<Vec<u64>>) {
    let mut a = vec![vec![0u64; TOY_N]; TOY_N];
    let mut b = vec![vec![0u64; TOY_N]; TOY_N];
    let mut s = seed;
    for i in 0..TOY_N {
        for j in 0..TOY_N {
            s = s
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            a[i][j] = s % TOY_Q;
            s = s
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            b[i][j] = s % TOY_Q;
        }
    }
    (a, b)
}

/// Parse a hex string into 32 bytes, or report why it is not one.
fn parse_seed(hex_str: &str) -> Result<[u8; 32], String> {
    let bytes = hex::decode(hex_str).map_err(|e| format!("--seed is not hex: {e}"))?;
    if bytes.len() != 32 {
        return Err(format!(
            "--seed is {} bytes, expected 32 (a 64-hex-char Ed25519 seed)",
            bytes.len()
        ));
    }
    let mut out = [0u8; 32];
    out.copy_from_slice(&bytes);
    Ok(out)
}

struct CreateArgs {
    out: PathBuf,
    ctx: u64,
    target_exp: u32,
    seed: Option<String>,
    prev: Option<String>,
    program: String,
}

fn parse_create_args(args: &[String]) -> Result<CreateArgs, String> {
    let mut out = PathBuf::from("kanit.json");
    let mut ctx = 777u64;
    let mut target_exp = 1u32;
    let mut seed = None;
    let mut prev = None;
    let mut program = DEFAULT_PROGRAM.to_string();
    let mut it = args.iter();
    while let Some(a) = it.next() {
        match a.as_str() {
            "--out" => {
                out = PathBuf::from(it.next().ok_or("--out needs a path")?);
            }
            "--ctx" => {
                ctx = it
                    .next()
                    .ok_or("--ctx needs a number")?
                    .parse()
                    .map_err(|e| format!("--ctx is not a number: {e}"))?;
            }
            "--target" => {
                target_exp = it
                    .next()
                    .ok_or("--target needs an exponent")?
                    .parse()
                    .map_err(|e| format!("--target is not an exponent: {e}"))?;
            }
            "--seed" => {
                seed = Some(it.next().ok_or("--seed needs hex")?.clone());
            }
            "--prev" => {
                prev = Some(it.next().ok_or("--prev needs hex")?.clone());
            }
            "--program" => {
                program = it.next().ok_or("--program needs a string")?.clone();
            }
            other => return Err(format!("unknown create argument {other:?}")),
        }
    }
    if target_exp > 32 {
        return Err(format!(
            "--target {target_exp} is too hard for the toy field (max 32)"
        ));
    }
    Ok(CreateArgs {
        out,
        ctx,
        target_exp,
        seed,
        prev,
        program,
    })
}

fn cmd_create(args: CreateArgs) -> Result<(), String> {
    let kernel = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = toy_matrices(20260929);
    let miner = match &args.seed {
        Some(h) => Keypair::from_seed(&parse_seed(h)?),
        None => Keypair::generate(&mut OsRng),
    };
    // The target is 2^exp in the 'hash % target == 0' sense, so exp==0 would be
    // trivially satisfiable and is rejected as meaningless rather than allowed.
    let target = if args.target_exp == 0 {
        return Err(
            "--target 0 means every tile clears; refusing to mint a worthless kanıt".into(),
        );
    } else {
        1u64 << args.target_exp
    };
    let prev = args.prev.unwrap_or_else(genesis_prev);
    if prev.len() != 64 || !prev.chars().all(|c| c.is_ascii_hexdigit()) {
        return Err(format!(
            "--prev must be 64 hex chars, got {} chars",
            prev.len()
        ));
    }

    eprintln!(
        "kok: mining G-layer kanıt (q={TOY_Q} n={TOY_N} r={TOY_R}, ctx={}, target=2^{})",
        args.ctx, args.target_exp
    );
    let started = std::time::Instant::now();
    let proof = mine(
        &kernel,
        &a,
        &b,
        args.ctx,
        target,
        &args.program,
        0,
        0,
        &miner,
        &prev,
    )
    .map_err(|e| format!("mining failed: {e}"))?;
    let elapsed = started.elapsed();

    let json = to_json(&proof).map_err(|e| format!("serializing kanıt: {e}"))?;
    std::fs::write(&args.out, json).map_err(|e| format!("writing {}: {e}", args.out.display()))?;

    // The secret is printed to stderr only. It is never written to the kanıt
    // file or anywhere on disk; the did is what goes in the file.
    eprintln!(
        "kok: miner secret seed (keep private, printed once): {}",
        hex::encode(miner.secret)
    );
    eprintln!("kok: miner did        : {}", miner.did);
    eprintln!(
        "kok: tile (i={}, j={}) value={} at nonce {} — mined in {:.1} ms",
        proof.cert_i,
        proof.cert_j,
        proof.cert_value,
        proof.nonce,
        elapsed.as_secs_f64() * 1000.0
    );
    println!(
        "kok: wrote {} (receipt {})",
        args.out.display(),
        &proof.receipt_hash[..16]
    );
    Ok(())
}

/// Verify one file, printing a one-line verdict with the reason on failure.
fn verify_file(path: &PathBuf) -> Result<bool, String> {
    let text =
        std::fs::read_to_string(path).map_err(|e| format!("reading {}: {e}", path.display()))?;
    let proof: MiningProof =
        from_json(&text).map_err(|e| format!("parsing {}: {e}", path.display()))?;
    match verify(&proof) {
        Ok(()) => {
            println!(
                "KABUL  {}  (did {}…, receipt {}…, tile ({},{}) = {})",
                path.display(),
                &proof.miner_did[..20],
                &proof.receipt_hash[..12],
                proof.cert_i,
                proof.cert_j,
                proof.cert_value
            );
            Ok(true)
        }
        Err(e) => {
            // A rejection names the check that fired, so a corrupted file is
            // distinguishable from a forgery attempt.
            println!("RED   {}  — {e}", path.display());
            Ok(false)
        }
    }
}

fn cmd_verify(paths: &[PathBuf]) -> Result<(), String> {
    if paths.is_empty() {
        return Err("verify needs at least one kanıt file".into());
    }
    let mut rejected = 0usize;
    let mut unreadable = 0usize;
    for path in paths {
        match verify_file(path) {
            Ok(true) => {}
            Ok(false) => rejected += 1,
            // an unreadable or unparseable file is a hard error, counted apart
            // from a forgery so the two are never conflated in the summary
            Err(e) => {
                unreadable += 1;
                eprintln!("kok: {e}");
            }
        }
    }
    if rejected == 0 && unreadable == 0 {
        return Ok(());
    }
    let mut msg = format!("did not verify: {rejected} rejected");
    if unreadable > 0 {
        msg.push_str(&format!(", {unreadable} unreadable or unparseable"));
    }
    msg.push_str(&format!(" of {} file(s)", paths.len()));
    Err(msg)
}

fn cmd_selftest() -> Result<(), String> {
    let kernel = KwKernel::new(TOY_Q, TOY_R);
    let (a, b) = toy_matrices(20260929);
    let miner = Keypair::from_seed(&[0x42; 32]);
    println!("kok: selftest — mine, then re-derive everything from the file alone");
    let t0 = std::time::Instant::now();
    let proof = mine(
        &kernel,
        &a,
        &b,
        777,
        1u64 << 1,
        DEFAULT_PROGRAM,
        0,
        0,
        &miner,
        &genesis_prev(),
    )
    .map_err(|e| format!("mine failed: {e}"))?;
    let mine_ms = t0.elapsed().as_secs_f64() * 1000.0;

    let file = to_json(&proof).map_err(|e| format!("serialize: {e}"))?;
    let back: MiningProof = from_json(&file).map_err(|e| format!("parse back: {e}"))?;

    let t1 = std::time::Instant::now();
    let ok = verify(&back);
    let verify_ms = t1.elapsed().as_secs_f64() * 1000.0;

    println!(
        "  mine   : {:.3} ms (nonce {}, tile ({},{}) = {})",
        mine_ms, back.nonce, back.cert_i, back.cert_j, back.cert_value
    );
    println!("  verify : {:.3} ms", verify_ms);
    println!("  did    : {}", back.miner_did);
    println!("  receipt: {}", back.receipt_hash);
    match ok {
        Ok(()) => {
            println!("kok: selftest PASSED — the kanıt verified with no secret and no network");
            Ok(())
        }
        Err(e) => Err(format!("selftest FAILED: {e}")),
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        println!("{USAGE}");
        std::process::exit(0);
    }
    let result = match args[0].as_str() {
        "create" => parse_create_args(&args[1..]).and_then(cmd_create),
        "verify" => {
            let paths = args[1..].iter().map(PathBuf::from).collect::<Vec<_>>();
            cmd_verify(&paths)
        }
        "selftest" => cmd_selftest(),
        "-h" | "--help" | "help" => {
            println!("{USAGE}");
            Ok(())
        }
        other => Err(format!("unknown command {other:?}\n\n{USAGE}")),
    };
    if let Err(e) = result {
        eprintln!("kok: {e}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod cli_tests {
    use super::*;

    /// The CLI's own parsing of a seed round-trips into the same keypair the
    /// library builds — the reproducibility path a test relies on.
    #[test]
    fn a_hex_seed_parses_to_the_same_keypair() {
        let seed_hex = hex::encode([0x42u8; 32]);
        let parsed = parse_seed(&seed_hex).unwrap();
        assert_eq!(parsed, [0x42u8; 32]);
        assert_eq!(
            Keypair::from_seed(&parsed).did,
            Keypair::from_seed(&[0x42u8; 32]).did
        );
    }

    /// A target exponent of zero is refused, because it would mint a kanıt
    /// whose work anyone could produce in one try.
    #[test]
    fn a_zero_target_exponent_is_refused() {
        let args = parse_create_args(&["--target".into(), "0".into()]).unwrap();
        assert!(cmd_create(args).is_err());
    }

    /// A garbage seed reports why rather than panicking.
    #[test]
    fn a_malformed_seed_is_reported_not_panicked() {
        assert!(parse_seed("nothex").is_err());
        assert!(parse_seed(&"ab".repeat(16)).is_err());
    }
}

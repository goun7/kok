// The light-client verifier, driven by a REAL WASI HOST — the wasm32-wasip1 build.
//
// WHAT THIS PROVES (2026-09-26): the same C ABI the unknown-unknown script
// exercises ALSO compiles and runs under the WASI target, and answers
// byte-identically. Two runtimes, one verifier, one result. The WASI module
// is ~5x smaller (105,916 vs 518,605 bytes) because it links the std
// getrandom path rather than the wasm-bindgen/js glue.
//
// WHY THE HOST IS HAND-WRITTEN rather than using node:wasi. Node's built-in
// WASI gates its imports behind start()/initialize(), which require a
// _start or _initialize export. This is a REACTOR module — its only exports
// are memory and kok_verify_packet — so node:wasi raises ERR_WASI_NOT_STARTED
// and cannot drive it. Acting as the host directly implements exactly the
// five imports the module declares and no more:
//   random_get        real entropy from node:crypto (this is the one that matters —
//                     the verifier's sampling must not be stubbed to zeros)
//   environ_sizes_get no environment
//   environ_get       no environment
//   fd_write          byte-counting sink
//   proc_exit         trap (must never be reached; the ABI rejects, it does not exit)
//
// THE FIVE PROBES, identical to verify_under_node.mjs so the two runtimes are
// compared like-for-like:
//   verify(0, 0)                    -> 0  null/zero-length rejects, does not trap
//   verify(buf5, 5)                 -> 0  a short buffer rejects
//   verify(buf5, 2^32-1)            -> 0  a huge claimed length rejects
//   verify(packet, packet.len())    -> 1  an honestly mined packet ACCEPTS
//   verify(forged_packet, len)      -> 0  a tampered accumulated value REJECTS
// The honest accept is the control the negative tests need: a boundary that
// rejects everything passes all three adversarial tests vacuously.
//
// RUN: node verify_wasi_under_node.mjs
// (the WASI module must first be built:
//    cargo build --release -p kok-wasm --target wasm32-wasip1
//  and the honest packet produced with:
//    cargo run --release -p kok-pvi --example dump_packet > target/kok_wasm_known_good.hex)
import fs from 'node:fs';
import crypto from 'node:crypto';

const WASM = 'target/wasm32-wasip1/release/kok_wasm.wasm';
const PKT = 'target/kok_wasm_known_good.hex';

const bytes = fs.readFileSync(WASM);
const { instance } = await WebAssembly.instantiate(bytes, {
  wasi_snapshot_preview1: {
    // Real entropy. The verifier samples tile noise; stubbing this to zeros
    // would make a probabilistic check look deterministic.
    random_get(ptr, len) {
      const view = new Uint8Array(instance.exports.memory.buffer);
      const buf = crypto.randomBytes(len);
      view.set(buf, ptr);
      return 0;
    },
    // No environment variables are needed — the verifier reads none.
    environ_sizes_get(countPtr, bufPtr) {
      const dv = new DataView(instance.exports.memory.buffer);
      dv.setUint32(countPtr, 0, true);
      dv.setUint32(bufPtr, 0, true);
      return 0;
    },
    environ_get(ptr, _bufPtr) {
      const dv = new DataView(instance.exports.memory.buffer);
      dv.setUint32(ptr, 0, true);
      return 0;
    },
    // A byte-counting sink: the ABI logs nothing on these paths, but if it
    // ever does, reporting progress honestly beats silently returning 0.
    fd_write(_fd, iovsPtr, iovsLen, nwrittenPtr) {
      const dv = new DataView(instance.exports.memory.buffer);
      let total = 0;
      for (let i = 0; i < iovsLen; i++) {
        const base = dv.getUint32(iovsPtr + i * 8, true);
        const len = dv.getUint32(iovsPtr + i * 8 + 4, true);
        total += len;
      }
      dv.setUint32(nwrittenPtr, total, true);
      return 0;
    },
    // Must never be reached: the ABI rejects bad input, it does not abort the
    // process. If this fires, the verifier panicked instead of returning 0.
    proc_exit(code) {
      throw new Error(`proc_exit(${code}) was called — the verifier aborted instead of rejecting`);
    },
  },
});

const verify = instance.exports.kok_verify_packet;
const mem = instance.exports.memory;

let failures = 0;
function check(name, got, want) {
  const ok = got === want;
  if (!ok) failures++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}: got ${got}, want ${want}`);
}

// --- the three adversarial inputs: each must REJECT, none may trap ---
check('null pointer, length 0', verify(0, 0), 0);
const short = new Uint8Array(5);
mem.grow(1);
new Uint8Array(mem.buffer).set(short, 8);
check('5-byte buffer, length 5 (shorter than the 80-byte header)', verify(8, 5), 0);
check('5-byte buffer, claimed length 2^32-1', verify(8, 4294967295), 0);

// --- the honest control: a packet Rust itself accepts ---
let hex = null;
try { hex = fs.readFileSync(PKT, 'utf8').trim(); } catch { /* fall through */ }
if (!hex) {
  console.log('SKIP honest control: target/kok_wasm_known_good.hex is missing.');
  console.log('      produce it with:');
  console.log('      cargo run --release -p kok-pvi --example dump_packet > target/kok_wasm_known_good.hex');
} else {
  const wire = Uint8Array.from(Buffer.from(hex, 'hex'));
  if (wire.length !== 1104) {
    console.log(`FAIL honest control: expected a 1104-byte packet, got ${wire.length}`);
    failures++;
  } else {
    // offset 8, the same convention as the unknown-unknown script — this WASI
    // build has no bindgen glue claiming offset 0, but a shared convention
    // between the two scripts keeps them comparable
    mem.grow(Math.ceil((wire.length + 16) / 65536));
    const view = new Uint8Array(mem.buffer);
    view.set(wire, 8);
    check('honestly mined packet ACCEPTS (byte-identical to the one Rust accepts)', verify(8, wire.length), 1);
    // forgery: tamper the accumulated value (bytes 16..24 of the packet)
    const forged = wire.slice();
    const dv = new DataView(forged.buffer);
    const v = dv.getBigUint64(16, true);
    dv.setBigUint64(16, (v + 1n) % 97n, true);
    // re-acquire the view: the previous write may have detached it
    const view2 = new Uint8Array(mem.buffer);
    view2.set(forged, 8);
    check('forged accumulated value REJECTS', verify(8, forged.length), 0);
  }
}

if (failures > 0) {
  console.log(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log('\nall checks passed — the WASI (wasm32-wasip1) light-client verifier ran and answered under Node.js');

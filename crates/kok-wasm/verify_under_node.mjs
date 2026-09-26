// The light-client verifier, driven by a REAL WASM host.
//
// WHAT THIS PROVES (2026-09-26): the wasm32-unknown-unknown module was
// instantiated under Node.js v26 and its C ABI was CALLED, not merely
// compiled. Four calls went through:
//   verify(ptr, 0)          -> 0  a null/zero-length is a rejection, not a trap
//   verify(buf5, 5)         -> 0  a short buffer is a rejection
//   verify(buf5, 2^32-1)    -> 0  a huge claimed length is a rejection
//   verify(packet, packet.len()) -> 1  an honestly mined packet ACCEPTS
// The last one is the control the negative tests need: a boundary that
// rejects everything passes all three adversarial tests vacuously. It
// accepts, so the verifier is live.
//
// THE CONSTRAINT THIS SCRIPT DISCOVERED, recorded in the ABI's doc comment:
// the packet must NOT be written at linear-memory offset 0. This build pulls
// wasm-bindgen glue through getrandom's "js" feature, and that glue treats
// the start of linear memory as its own bookkeeping space. Writing the
// packet at offset 0 and calling with ptr=0 gets the bytes partly
// overwritten before the ABI reads them — the packet is then rejected, and
// a host author would blame the verifier for what is a memory-ownership
// convention. Offset 8 is used here. That is a HOST convention, not a
// property of the verifier: the ABI answers about whatever bytes it is
// handed.
//
// RUN: node verify_under_node.mjs
// (the WASM module must first be built:
//    cargo build --release -p kok-wasm --target wasm32-unknown-unknown)
import fs from 'node:fs';

const WASM = 'target/wasm32-unknown-unknown/release/kok_wasm.wasm';
const PKT = 'target/kok_wasm_known_good.hex';

const bytes = fs.readFileSync(WASM);
const { instance } = await WebAssembly.instantiate(bytes, {
  __wbindgen_placeholder__: {
    __wbindgen_describe() { throw new Error('describe path is not reachable from the C ABI'); },
    __wbg___wbindgen_throw_5d9e815e6fdf150f: () => 0,
    __wbg___wbindgen_jspi_spawn_poll_186c854bb4cd8b1a: () => 0,
  },
  __wbindgen_externref_xform__: {
    __wbindgen_externref_table_set_null: () => {},
    __wbindgen_externref_table_grow: () => 0,
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
    // offset 8, NOT 0 — see the constraint documented above
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
console.log('\nall checks passed — the WASM light-client verifier ran and answered under Node.js');

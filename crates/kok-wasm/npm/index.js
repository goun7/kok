// @kok-network/light-verifier — ESM entry
//
// WHAT THIS PACKAGE IS: the light-client verifier for KÖK Network, compiled
// to WASM. One function matters: verifyPacket(bytes) -> 1 | 0. It answers
// whether a mined certificate is honest, and it is built so that it CANNOT
// trap on adversarial input — in WASM a panic is a trap, and a trap is not
// a rejection, so every bounds and arithmetic check happens on lengths
// before a single matrix byte is indexed. A malformed packet returns 0
// (reject), never an undefined outcome.
//
// BROWSER AND NODE FROM ONE SOURCE: the module is a plain C ABI with one
// export (kok_verify_packet) plus the linear memory it reads. That is small
// enough to instantiate without wasm-bindgen glue, which is deliberate —
// nothing at verify time needs randomness, so there is no JS entropy to
// wire. Both runtimes feed the same bytes to the same export.

const WASM_URL = new URL('./kok_wasm_bg.wasm', import.meta.url);

let _instance = null;
let _memory = null;
let _verify = null;

/**
 * Load and instantiate the WASM module. Idempotent — safe to call from
 * several entry points; the first caller wins and the rest reuse it.
 *
 * In the browser this uses WebAssembly.instantiateStreaming over fetch.
 * In Node 18+ it uses the built-in WebAssembly + fs. The detection is on
 * the presence of a global fetch with streaming support, not on a
 * user-agent string, because a user-agent lies and fetch does not.
 */
export async function init() {
  if (_instance) return _instance;

  let bytes;
  if (WASM_URL.protocol === 'file:' || typeof fetch !== 'function') {
    // Node path — including the test runner, where import.meta.url is a
    // file:// URL and global fetch cannot speak that scheme. Detecting on
    // the protocol is what makes this honest: a browser never hands back a
    // file: URL, and Node's fetch says "not implemented" for one rather
    // than falling through to something quieter.
    const fs = await import('node:fs');
    bytes = fs.readFileSync(WASM_URL);
  } else if (WebAssembly.instantiateStreaming) {
    // Browser path (and any runtime exposing fetch over http(s)).
    const resp = await fetch(WASM_URL);
    if (!resp.ok) {
      throw new Error(`kok-wasm: failed to fetch module (HTTP ${resp.status})`);
    }
    bytes = new Uint8Array(await resp.arrayBuffer());
  } else {
    const fs = await import('node:fs');
    bytes = fs.readFileSync(WASM_URL);
  }

  const result = await WebAssembly.instantiate(bytes, wbindgenShim());
  _instance = result.instance || result; // streaming returns {instance}
  _memory = _instance.exports.memory;
  _verify = _instance.exports.kok_verify_packet;
  if (!_verify || !_memory) {
    throw new Error('kok-wasm: module is missing kok_verify_packet or memory exports');
  }
  return _instance;
}

// The unknown-unknown build carries wasm-bindgen glue imports because
// getrandom's "js" feature pulls them in transitively — nothing at VERIFY
// time needs them. These stubs are the minimal surface the module requires
// to instantiate; the two describe paths deliberately throw, because
// reaching one means something called into the JS bridge from the C ABI,
// which the boundary is built not to do. This mirrors what the existing
// verify_under_node.mjs harness provides, so the package and the raw
// script agree.
function wbindgenShim() {
  return {
    __wbindgen_placeholder__: {
      __wbindgen_describe() {
        throw new Error('describe path is not reachable from the C ABI');
      },
      __wbg___wbindgen_throw_5d9e815e6fdf150f: () => 0,
      __wbg___wbindgen_jspi_spawn_poll_186c854bb4cd8b1a: () => 0,
    },
    __wbindgen_externref_xform__: {
      __wbindgen_externref_table_set_null: () => {},
      __wbindgen_externref_table_grow: () => 0,
      __wbindgen_externref_table_get: () => undefined,
    },
  };
}

/**
 * Verify a mined certificate packet.
 *
 * Wire layout (all little-endian u64):
 *   bytes [  0 ..  32]   certificate (i, j, value, m)
 *   bytes [ 32 ..  80]   public inputs (ctx, nonce, target, n, q, r)
 *   bytes [ 80 ..  end]  flat_a then flat_b, the two n*n matrices
 *
 * @param {Uint8Array|ArrayBuffer} packet
 * @returns {number} 1 = honest accept, 0 = reject (malformed or forged)
 */
export function verifyPacket(packet) {
  if (!_verify) {
    throw new Error('kok-wasm: call init() before verifyPacket()');
  }
  const bytes = packet instanceof Uint8Array ? packet : new Uint8Array(packet);

  // Copy into linear memory at a SAFE OFFSET. The wasm-bindgen glue this
  // build pulls in keeps bookkeeping near offset 0, and a host that writes
  // a packet there gets its bytes partially overwritten before the ABI
  // reads them — the packet then rejects for the wrong reason. This is the
  // documented host constraint in the crate's own doc comment, and 64 KiB
  // is a full page past anything the glue reserves, so the packet lives in
  // memory the module has already claimed as its own scratch rather than in
  // the reserved area it will not touch. Growth happens before the copy,
  // never after, and the offset is recomputed from the live buffer.
  const OFFSET = 65536;
  const needed = OFFSET + bytes.length;
  const current = _memory.buffer.byteLength;
  if (needed > current) {
    const pages = Math.ceil((needed - current) / 65536);
    _memory.grow(pages);
  }
  const view = new Uint8Array(_memory.buffer, OFFSET, bytes.length);
  view.set(bytes);
  return _verify(OFFSET, bytes.length);
}

export default { init, verifyPacket };

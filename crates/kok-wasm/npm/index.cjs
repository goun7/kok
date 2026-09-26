// @kok-network/light-verifier — CommonJS entry
//
// Same surface as the ESM module, for consumers still on require(). The
// .wasm is read off disk relative to this file, so the package works
// regardless of the consumer's cwd.

const path = require('path');
const fs = require('fs');

const WASM_PATH = path.join(__dirname, 'kok_wasm_bg.wasm');

let _instance = null;
let _memory = null;
let _verify = null;

async function init() {
  if (_instance) return _instance;
  const bytes = fs.readFileSync(WASM_PATH);
  const result = await WebAssembly.instantiate(bytes, wbindgenShim());
  _instance = result.instance || result;
  _memory = _instance.exports.memory;
  _verify = _instance.exports.kok_verify_packet;
  if (!_verify || !_memory) {
    throw new Error('kok-wasm: module is missing kok_verify_packet or memory exports');
  }
  return _instance;
}

function verifyPacket(packet) {
  if (!_verify) {
    throw new Error('kok-wasm: call init() before verifyPacket()');
  }
  const bytes = packet instanceof Uint8Array ? packet : new Uint8Array(packet);
  // Same safe-offset convention as the ESM entry: see index.js for why
  // offset 0 is not safe for payload data under this build.
  const OFFSET = 65536;
  const needed = OFFSET + bytes.length;
  const current = _memory.buffer.byteLength;
  if (needed > current) {
    _memory.grow(Math.ceil((needed - current) / 65536));
  }
  new Uint8Array(_memory.buffer, OFFSET, bytes.length).set(bytes);
  return _verify(OFFSET, bytes.length);
}

module.exports = { init, verifyPacket };

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

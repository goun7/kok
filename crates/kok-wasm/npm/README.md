# @kok-network/light-verifier

The KÖK Network light-client verifier, compiled to WebAssembly.

One function matters: **`verifyPacket(bytes)`** returns `1` if a mined
certificate is honest and `0` if it is malformed or forged. That is the whole
surface — a light client does not need to run the chain, it needs to check a
certificate, and this package is that check.

## Why the verifier cannot trap

In WASM a panic is a **trap**, and a trap is not a rejection: it is an
undefined outcome a host may report as anything, including
success-by-omission. So the byte layout is validated with **checked
arithmetic before a single matrix byte is indexed**. A hostile packet that
claims `n = 2^64` cannot wrap `n*n*8` to a small number that then passes the
length check. Every malformed input returns `0`, and no input traps.

## Install and use

```js
import { init, verifyPacket } from '@kok-network/light-verifier';

await init();
const verdict = verifyPacket(packetBytes); // 1 = accept, 0 = reject
```

CommonJS is supported too:

```js
const { init, verifyPacket } = require('@kok-network/light-verifier');
```

### Wire layout (all little-endian u64)

| offset | bytes | field |
|---|---|---|
| 0 | 8 | `i` — tile row |
| 8 | 8 | `j` — tile column |
| 16 | 8 | `value` — the accumulated result |
| 24 | 8 | `m` — tile size |
| 32 | 8 | `ctx` — context/epoch binding |
| 40 | 8 | `nonce` — the mining nonce |
| 48 | 8 | `target` — the PoW threshold |
| 56 | 8 | `n` — matrix dimension |
| 64 | 8 | `q` — field modulus |
| 72 | 8 | `r` — tile grid stride |
| 80 | 2·n²·8 | flat_a, then flat_b |

## Browser and Node from one source

The module exports one C function (`kok_verify_packet`) plus linear memory —
small enough to instantiate without wasm-bindgen glue, which is deliberate:
nothing at verify time needs randomness, so there is no JS entropy to wire.
The runtime is selected by URL protocol, not user-agent string, because a
user-agent lies and a `file:` URL does not.

## What this is not

This is the **verifier boundary**, not a node. It does not fetch matrices,
track the chain, or serve peers — the crate's own roadmap lists those as F3+.
It answers one question, byte-exactly, and it does not pretend to be the
browser bundle that will eventually wrap it.

## Development

```sh
# Build the module, then package it (also regenerates the test fixtures)
cargo build --release -p kok-wasm --target wasm32-unknown-unknown
cargo run --release -p kok-wasm --example package_npm

# Run the package tests (Node's built-in runner — no dev dependency)
node --test crates/kok-wasm/npm/tests/
```

The fixtures are mined by the same `mine_real` helper the crate's own Rust
tests use, so the npm package and the Rust tests verify one set of bytes. If
they ever disagree, one of them changed and the other did not.

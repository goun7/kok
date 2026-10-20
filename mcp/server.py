#!/usr/bin/env python3
"""kok MCP sunucusu - Model Context Protocol 2025-06-18 over stdio.

KOK L1 ( Faydali-Yapay-Zeka-Madenciligi) kanit-cekirdegini AI ajanlarina
MCP araclari olarak sunar. Tamga/sester/pacta MCP sunucularinin ayni
deseni ( stdio JSON-RPC, uc-sonuc kaniti, exception-YOK).

Tasarim-ilkesi:
  - SAF STDLIB - sunucu kok-cli Rust-binary'sini SUBPROCESS-LEVEL'da
    cagirir, hicbir pip/cargo bagimliligi-gerektirmez.
  - UC-SONUC - her arac GREEN/RED/INDETERMINE JSON kaniti dondurur;
    ASLA exception firlatmaz.
  - Subprocess-tabanli cagri - her dogrulama kok-cli'nin KENDI
    binary'sinde calisir ( cargo run -p kok-cli --bin kok).

Araclar:
  selftest      kok-cli'Ozellik-kontrol-odemeyi calistirir ( selftest)
  kanit_olustur  G-layer-MatMul-kanitini madenler ( create --ctx --target)

Calistirma:
  python3 mcp/server.py                    # stdio JSON-RPC
  (istemci tarafi: "command": "python", "args": ["<repo>/mcp/server.py"])
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "kok"
SERVER_VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parents[1]
MAX_TIMEOUT = 600  # saniye - cargo-derleme-uzun-surebilir


def _e(msg: str) -> dict:
    return {"jsonrpc": "2.0", "error": {"code": -32602, "message": msg}}


def _result(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _text(payload: dict) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}


def _env() -> dict:
    """CARGO_NET_GIT_FETCH_WITH_CLI gibi sorunlari-onler ( offline-taraf)."""
    env = dict(os.environ)
    env.setdefault("CARGO_TERM_COLOR", "never")
    return env


def _run_cargo(args: list) -> dict:
    """kok-cli'yi cargo-run ile SUBPROCESS olarak cagir.

    Fail-closed: her hata ( zaman-asimi, exception, derleme-basarisiz)
    bir RED kanitidir - traceback DEGIL, JSON doner. Rust-binary'leri
    insan-okunur cikti-basar; rc + cikis JSON kanitina-sarilir.
    """
    try:
        proc = subprocess.run(
            ["cargo", "run", "-p", "kok-cli", "--bin", "kok", "--quiet", "--", *args],
            capture_output=True, text=True, timeout=MAX_TIMEOUT,
            cwd=str(ROOT), env=_env())
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "zaman-asimi: %ds" % MAX_TIMEOUT}
    except Exception as e:  # cephedeki her hata JSON kaniti olmali
        return {"ok": False, "reason": "calistirma-hatasi: %s" % e}
    out = (proc.stdout or "").strip()
    return {
        "ok": proc.returncode == 0,
        "rc": proc.returncode,
        "report": out[:2000],
        "stderr": (proc.stderr or "").strip()[:400],
    }


def _tool_selftest(args: dict) -> dict:
    return _run_cargo(["selftest"])


def _tool_kanit_olustur(args: dict) -> dict:
    """G-layer-MatMul-kanitini madenler. args.ctx ve args.target opsiyonel."""
    cli_args = ["create"]
    ctx = args.get("ctx")
    if isinstance(ctx, int) and ctx > 0:
        cli_args += ["--ctx", str(ctx)]
    target = args.get("target")
    if isinstance(target, int) and target >= 0:
        cli_args += ["--target", str(target)]
    return _run_cargo(cli_args)


TOOL_IMPLS = {
    "selftest": _tool_selftest,
    "kanit_olustur": _tool_kanit_olustur,
}

TOOLS_LIST = [
    {
        "name": "selftest",
        "description": (
            "KOK kanit-cekirdeginin ( G-layer-MatMul + did:key-receipt) "
            "ozellik-kontrol-odemesini calistirir. Ilk-cagri "
            "derlenme-uzunlugu-cekebilir. JSON kanit doner."),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "kanit_olustur",
        "description": (
            "G-layer-MatMul ustuinden bir kanit ( certificate) madenler "
            "ve did:key-ile-imzalar. args.ctx ( task-context, int) ve "
            "args.target ( 2^N-zorluk, int) opsiyonel. "
            "Gizli-anahtar stdout'a YAZILMAZ."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ctx": {"type": "integer"},
                "target": {"type": "integer"},
            },
            "additionalProperties": False,
        },
    },
]


def _tools_list_result() -> dict:
    return {"tools": TOOLS_LIST}


def _handle_call(req_id, params: dict) -> dict | None:
    name = params.get("name")
    if not isinstance(name, str) or not name:
        return _result(req_id, _e("arac-adi-zorunlu"))
    impl = TOOL_IMPLS.get(name)
    if impl is None:
        return {
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": "bilinmeyen-arac: %s" % name},
        }
    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        return _result(req_id, _e("arguments-bir-nesne-olmali"))
    try:
        payload = impl(args)
    except Exception as e:  # fail-closed: traceback degil JSON kaniti
        payload = {"ok": False, "reason": "arac-hatasi: %s" % e}
    return _result(req_id, _text(payload))


def main() -> int:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_e("gecersiz-json")) + "\n")
            sys.stdout.flush()
            continue
        if not isinstance(req, dict):
            sys.stdout.write(json.dumps(_e("istek-bir-nesne-degil")) + "\n")
            sys.stdout.flush()
            continue
        method = req.get("method")
        req_id = req.get("id")
        if method == "initialize":
            sys.stdout.write(json.dumps(_result(req_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                    "instructions": (
                        "KOK L1 kanit-cekirdegi sunucusu. "
                        "selftest -> ozellik-kontrol-odemesi; "
                        "kanit_olustur -> G-layer-kanit-madenciligi. "
                        "Her arac JSON kaniti doner, asla exception firlatmaz."),
                }})) + "\n")
        elif method == "notifications/initialized":
            continue  # bildirim - yanit yok
        elif method == "tools/list":
            sys.stdout.write(json.dumps(_result(req_id, _tools_list_result())) + "\n")
        elif method == "tools/call":
            resp = _handle_call(req_id, req.get("params") or {})
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        elif method == "ping":
            sys.stdout.write(json.dumps(_result(req_id, {})) + "\n")
        elif req_id is not None:
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": "bilinmeyen-method: %s" % method}
            }) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

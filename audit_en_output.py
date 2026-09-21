#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - EN-PACKAGE OUTPUT AUDIT (aksansiz Turkce yakalayici)
==============================================================
KOK KURALI: reviewer paketindeki EN dosyalarin KAYNAGINDA da, CALISMA
CIKTISINDA da Turkce olmamali (KOK disinda).

GECMIS HATA: onceki denetleyici 'ciktidaki Turkce HARFLERI'ni sayiyordu
(c/g/i/o/s/u + aksanlar). Ama cevrilmeyen stringler AKSANSIZ Turkce
yazilmisti: "sansur", "gorev", "maliyet" (bakiniz [TR] listesi) - harf
filtresine takilmiyor, 5 kez "0 TR harf = TEMIZ" raporu VERILIYORDU ve
yine de Demirel'e Turkce cikti gitti.

COZUM: bu script KELIME BAZLI calisir. Yasakli kelime listesi + dil
istatistikleri (TESSERACT degil, hizli substring + oran):
  1. kelimeleri bian liste ile eslestirir
  2. ayrca kelimelerin cogu kucuk harf Turkce ise ISABET orani raporlar

KULLANIM:  python3 audit_en_output.py [--fix-none]
  tum *_en.py ve EN *.md dosyalarini denetler; kaynakta ve calisma
  ciktisinda Turkce varsa listeler. cikis kodu: 0=temiz, 1=sorun bulundu
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# --- aksansiz Turkce kelime listesi (cogul/cekim dahil) ---------------------
TR_WORDS = [
    # --- protokol ciktisinda gecmeye aday TURKCE kelimeler ---
    "sansur", "sansuru", "sansurun", "sansure",
    "kesinti", "kesintiyi", "kesintisi", "kesintiler",
    "olay", "olayi", "olaylar", "olayda", "olayin",
    "gorev", "gorevi", "gorevli", "gorevlerin",
    "maliyet", "maliyeti", "maliyetler", "maliyetine",
    "talebi", "talepler", "sifir-talep",
    "zarari", "zarari var",
    "kazanc", "kazanci", "kazanclari",
    "sifir-talep",
    "saldiri", "saldirisi", "saldirgan", "saldiriya",
    # --- 2026-09-21: koda gomulu diger Turkce kelimeler (yorum + assertion) ---
    "etkili", "etkisi", "etkisi var",
    "kritik",
    "ayni", "ayni blok", "ayni sabit",
    "hepsinde", "hepsi",
    "toplam", "toplami",
    "refill'siz", "refillsiz",
    "duzeni", "duzen",
    "yaklasim", "toy yaklasim",
    "sorgular", "sorguluyor",
    "verdi", "verir",
    "farkli", "farkli blok",
    "HATA",
    # --- 2026-09-21 (3. tur): spec pseudocode yorumlari ---
    "atamasi", "atamayi", "atamada",
    "kaniti", "kanit", "hile",
    "itirazciya", "itirazi", "itiraz", "itirazda",
    "pahali",
    "geri-alamaz", "guncelleme",
    "guvenlik", "guvenlik kaynagi",
    "blogundan", "blok kazildi",
    "etkileyemez", "etkileyemezler",
    "agirlikli",
    "talepten", "talep",
    "bagimsiz",
    "dogrulanmis",
    "arzi", "arz",
    "yil", "yili",
    "kazanir", "kazandi",
    "kotü", "kotu", "kötü",
    "niyetli",
    "katmani", "katman",
    "escrow'dan", "escrow'a",
    "sabit", "varsayim",
    "orani",

    "penceresi", "pencereyi",
    "uretimde",
    "iadesi", "iade edil",
    "gocu", "goc ettir",
    "tulendi", "uste tulendi",
    "REDDETME", "KABUL", "GECTI", "GECTIMI", "GECTIYSE",
    "HEPSI", "TUM", "tamami",
    "DURUST", "durust",
    "aynisinin",
    "beklenti",
    "doygun", "doygunluk",
    "kârli", "karli",
    "TEK-SEFERLIKTIR", "tek-seferliktir", "tek seferlik",
    "BEDAVA", "bedava",
    "HICBIR", "hicbir",
    "DISKRIMINATIF", "diskriminatif",
    "TERSIDIR", "tersidir", "TERSINE", "tersine",
    "dogrulama", "zorunlu", "dogrulama;",
    "sifir-talep",
    "sansur-ucretsiz", "ucretsiz",
    "gorev-gocu", "gorev-goc",
    "iade-garantisi",
    "alt-bond sorunu",
    "sansur; uretim",
    "KOK_V2",        # isim disinda
]


# sayilar/semboller icermeyen kelimelere ayir
WORD_RE = re.compile(r"[A-Za-zÇĞİıÖŞÜâîû-]+")

def tr_hits(text):
    """Metindeki yasakli kelime ISABETLERI -> dict kelime:sayi.

    2026-09-21: KELIME ESLESMESI (substring degil) — 'verdict' icinde 'verdi'
    false positive'i bu yuzden cikiyor."""
    low = text.lower()
    low = low.replace("ı", "i").replace("ğ", "g").replace("ş", "s") \
             .replace("ö", "o").replace("ü", "u").replace("ç", "c").replace("â", "a")
    out = {}
    trset = set(TR_WORDS)
    for tok in WORD_RE.findall(low):
        if tok in trset:
            out[tok] = out.get(tok, 0) + 1
    return out

def audit_file_source(path):
    return tr_hits(io.open(path, encoding="utf-8").read())

def audit_file_runtime(path):
    try:
        r = subprocess.run([sys.executable, path], capture_output=True,
                           text=True, timeout=180, cwd=HERE)
        return tr_hits(r.stdout + r.stderr)
    except Exception as e:
        return {f"<runtime error: {e}>": 1}

def main():
    here = HERE
    # YALNIZCA reviewer paketi (TR internal belgeler bilincli olarak HARIC)
    md_en = [f for f in os.listdir(here)
             if f.endswith(".md") and f in (
                 "KOK_V2_CRYPTO_BRIEF.md", "KOK_V2_TECHNICAL_SPEC.md",
                 "KOK_V2_PAPER.md", "KOK_V2_REFERENCES.md", "README.md",
                 "EPOSTA_SOK.md", "EPOSTA_DEMIREL.md")]
    py_en = [f for f in os.listdir(here) if f.endswith("_en.py")]
    problems = 0
    print("=" * 72)
    print("KOK v2 EN-PACKAGE AUDIT (aksansiz Turkce yakalayici)")
    print("=" * 72)
    print("  KURAL: EN dosyalarin KAYNAGINDA ve CALISMA CIKTISINDA")
    print("  Turkce olmamali (KOK disinda). Harf tabanli denetim YANILDI;")
    print("  bu liste kelime tabanlidir.\n")

    for f in sorted(md_en):
        hits = audit_file_source(os.path.join(here, f))
        if hits:
            problems += 1
            print(f"  [KAYNAK] {f}")
            for w, n in sorted(hits.items(), key=lambda x: -x[1])[:8]:
                print(f"           '{w}' x{n}")

    for f in sorted(py_en):
        src = audit_file_source(os.path.join(here, f))
        rt = audit_file_runtime(os.path.join(here, f))
        # kaynak: kod icinde string/comment'ler EN olmali
        if src:
            problems += 1
            print(f"  [KAYNAK] {f}")
            for w, n in sorted(src.items(), key=lambda x: -x[1])[:8]:
                print(f"           '{w}' x{n}")
        if rt:
            problems += 1
            print(f"  [CIKTI ] {f}")
            for w, n in sorted(rt.items(), key=lambda x: -x[1])[:8]:
                print(f"           '{w}' x{n}")

    print("\n  SONUC: " + ("TEMIZ (0 Turkce)" if problems == 0
                            else f"{problems} dosyada TURKCE BULUNDU"))
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())

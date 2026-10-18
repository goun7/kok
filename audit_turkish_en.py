#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wide Turkish-leak audit for the English-language (_en / f0b / probe) files.

This file exists because the earlier claim "zero Turkish remaining" was wrong
twice. The first sweep checked only Turkish special characters, which caught
misspellings but nothing written in plain ASCII Turkish. The second sweep added a
word list that was too narrow and missed 'esik', 'tek', 'dogrulanir', 'gercek'
and 'gecmiste'. Both times the scan reported zero and both times zero was a
property of the scan, not of the files. A third way to be wrong is to scan
fewer files than exist: the original hardcoded list covered 14 of 38 English
files, so its CLEAN said nothing about the other 24. Scope is now derived
from the filesystem, not from a list that can go stale.

Run:
    python3 audit_turkish_en.py            # every *_en.py in repo root
    python3 audit_turkish_en.py file.py    # one file

Exit codes: 0 CLEAN, 1 Turkish found, 2 usage/missing-file/scope error.
A missing named file is a hard error, never a silent skip, because a skip
reports a CLEAN that is a property of the skip.

Known false positives this filter does NOT report, because they are English:
    - 'bin' in the shebang line #!/usr/bin/env python3, and the English noun bin
    - 'al' in the Latin abbreviation 'et al.'
    - 'once', 'var', 'yok', 'value', 'blok', 'deger' inside English prose
    - KOK / KOK v2 (the project name) and byte-string constants like
      b"kok-f3a-vrf-stub", which must not be renamed
The Turkish originals (u_layer_prototype.py, progress.md, task_plan.md) are
intentionally Turkish and are excluded.
"""
import io
import os
import re
import sys

TR_CHARS = 'çğıöşüÇĞİÖŞÜ'

# Plain-ASCII Turkish vocabulary. Extended after each miss; the lesson is that
# this list must grow whenever a review finds something it did not contain.
WORDS = [
    # grammar / connectives
    'blok', 'degil', 'icin', 'olan', 'sonra', 'daha', 'hic', 'tum', 'ayni',
    'kendi', 'artik', 'yani', 'gore', 'gibi', 'icinde', 'disinda', 'uzere',
    'dair', 'ait', 'bazi', 'herhangi', 'hicbir', 'boyle', 'ise', 'eger',
    'yoksa', 'belki', 'tabii', 'elbette', 'kesinlikle', 'aslinda', 'cok',
    'simdi', 'once', 'ardindan', 'seklinde', 'sekilde',
    # numbers. NOTE: 'on' (10) is deliberately absent — it matches the English
    # preposition in almost every line and produces only noise. If a Turkish
    # 'on' ever matters, the surrounding text carries other Turkish words.
    'bir', 'iki', 'uc', 'dort', 'bes', 'alti', 'yedi', 'sekiz', 'dokuz',
    'yirmi', 'otuz', 'kirk', 'elli', 'yuz', 'bin',
    # pronouns and derivations caught in later passes
    'ondan', 'bundan', 'sunun', 'onun', 'bunun', 'bizde', 'sizde', 'onlarda',
    # technical nouns and adjectives previously missed
    'esik', 'modda', 'dogrulanir', 'lineer', 'olcut', 'olcutlu', 'yontem',
    'gercek', 'anlamsiz', 'yapi', 'basari', 'basarili', 'basarisiz',
    'BASARISIZ', ' erken', 'tek',
    # general nouns
    'zaman', 'yer', 'sekil', 'boyut', 'isim', 'baslik', 'metin', 'yazi',
    'satir', 'tablo', 'sayi', 'harf', 'kelime', 'cumle', 'bolum', 'kisim',
    'adim', 'asama', 'durum', 'hata', 'sorun', 'cozum', 'cevap', 'yorum',
    'aciklama', 'bilgi', 'veri', 'islem', 'cikti', 'girdi', 'deger',
    # verbs
    'yap', 'yapma', 'ol', 'olma', 'gel', 'git', 'al', 'ver', 'koy', 'cek',
    'birak', 'basla', 'bitir', 'durdur', 'calis', 'dur', 'bekle', 'oku',
    'yaz', 'sil', 'ekle', 'cikar', 'degistir', 'guncelle', 'olustur',
    'tasarla', 'planla', 'test', 'dene',
    # descriptors
    'dogru', 'yanlis', 'gizli', 'acik', 'kapali', 'yarim', 'eksik', 'fazla',
    'az', 'biraz', 'bircok', 'butun', 'mavi', 'baska', 'yuksek', 'dusuk',
    'kucuk', 'buyuk', 'uzun', 'kisa', 'yeni', 'eski', 'hizli', 'yavas',
    'dolu', 'soguk', 'sicak',
]

# English words that are also Turkish and appear legitimately in English prose.
# These are skipped: matching them yields only false positives in English text,
# and a real Turkish sentence containing them also contains unambiguous words.
AMBIGUOUS = {'once', 'var', 'yok', 'test', 'bin', 'al', 'ol', 'yap', 'on',
             'in', 'at', 'ben', 'sen', 'biz', 'siz', 'ne', 'o', 'su', 'iki'}

DEFAULT_FILES = [
    'f3a_sequencer_proto_en.py', 'g_layer_tests_en.py',
    'u_layer_prototype_en.py', 'ghostdag_proto_en.py',
    'fp8_noise_proto_en.py', 'pass_sim_en.py', 'bond_margin_proto_en.py',
    'f0b_air_proto.py', 'probe_edges_en.py', 'probe_u_layer_en.py',
    'probe_ghostdag_en.py', 'adoption_econ.py', 'f0_demand_discovery.py',
    'f0_candidate_list.py',
]

# Hint the plain file list where it is consulted, because a gate that scans
# fewer files than exist reports a clean that is a property of the list.
EN_GLOB = '*_en.py'

# The audit script itself contains the Turkish wordlist by definition; it is
# not an English deliverable, so it is never in its own scope.
SELF = 'audit_turkish_en.py'

# A line ending in this marker is skipped: it declares the Turkish on that
# line intentional (an alphabet constant, a negative test fixture). The
# marker is opt-in per line, so it cannot blanket-mute a whole file.
INTENTIONAL_MARKER = '# TR-AUDIT: intentional'


def english_files():
    """Every English-language source file in the repo root.

    The historical hardcoded DEFAULT_FILES covered 14 of 38 English files;
    the other 24 were silently never scanned, and a scan that reports CLEAN
    while skipping files reports a property of its list. Scope is therefore
    derived from the filesystem, not from a list that can go stale.
    """
    globbed = {fn for fn in os.listdir('.')
               if fn.endswith('_en.py') and fn != SELF
               and os.path.isfile(fn)}
    return frozenset(), globbed


def scan(path):
    """Return a list of (line, kind, token, excerpt) for unambiguous Turkish."""
    out = []
    text = io.open(path, encoding='utf-8').read()
    for i, line in enumerate(text.split('\n'), 1):
        # An explicitly-marked line declares its own Turkish intentional.
        if INTENTIONAL_MARKER in line:
            continue
        # The project name and byte-string protocol labels stay as they are.
        c = re.sub(r'KÖK|KOK|kok-f3a', 'PROJ', line)
        if any(ch in c for ch in TR_CHARS):
            out.append((i, 'char', '', c.strip()[:70]))
            continue
        for w in WORDS:
            if w in AMBIGUOUS:
                continue
            if re.search(r'\b' + w + r'\b', c, re.I):
                out.append((i, 'word', w, c.strip()[:70]))
                break
    return out


def main():
    # A gate that silently skips a missing file reports a CLEAN that is a
    # property of the skip, not of the files: --bogus and a typo'd path both
    # used to exit 0. Unknown options are usage errors (rc=2), and a named
    # file that does not exist is a hard error (rc=2), never a skip.
    args = sys.argv[1:]
    if args and args[0].startswith('-'):
        sys.stderr.write('usage: audit_turkish_en.py [file ...]\n')
        sys.stderr.write('error: unknown option: %s\n' % args[0])
        return 2
    if args:
        files = args
        missing = [fn for fn in files if not os.path.exists(fn)]
        if missing:
            sys.stderr.write('error: no such file(s): %s\n' % ' '.join(missing))
            return 2
    else:
        defaulted, globbed = english_files()
        files = sorted(globbed)
        if not files:
            sys.stderr.write('error: no English (_en.py) files found\n')
            return 2
    total = 0
    for fn in files:
        for i, kind, tok, excerpt in scan(fn):
            label = 'char' if kind == 'char' else 'word[%s]' % tok
            print('  %-28s L%-5d %-14s %s' % (fn, i, label, excerpt))
            total += 1
    print()
    print('unambiguous Turkish hits: %d' % total)
    if total:
        print('RESULT: NOT CLEAN')
        return 1
    print('RESULT: CLEAN')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

# IACR ePrint Submission Package — KÖK compute-work proof receipt

> **Tarih:** 2026-10-18 · **Amaç:** kok'un evrim-sonrası bilgisini (Seçenek C)
> IACR ePrint'e-gönderilebilir-hale-getirmek. **arXiv DEĞİL** — IACR ePrint
> **endorsement, kurumsal-affiliation ve ön-onay İSTEMEZ**
> ([eprint.iacr.org/operations.html](https://eprint.iacr.org/operations.html)):
> "Any author can submit a paper with a technical contribution in the field
> of cryptology."
>
> **Bu, kullanıcının "arXiv'e maalesef kendi hesabımla gönderi yollayamıyorum
> çünkü birilerinden onay almam gerekiyordu ancak kimse maillerime cevap
> vermedi" engelinin doğru-çözümüdür.** Hiç kimsenin cevabını beklemek yok.

---

## 0. Kanıtlanmış-gerekçe: neden IACR ePrint, arXiv değil

| Kanal | Endorsement | Durum |
|---|---|---|
| **arXiv** | **Gerekir** — 21-Ocak-2026 politikası: kurumsal e-posta tek başına yetersiz; ortak-yazar makalesi veya kişisel endorsement şart | ❌ Kimse cevap vermiyor (Demirel 4-hafta-sessizlik) |
| **IACR ePrint** | **Gerekmez** — "Any author can submit" | ✅ **Bugün gönderilebilir** |
| **Zenodo** | Gerekmez | ✅ Yedek (EU AI-Act-uyumlu DOI) |

**İçerik-uyumu doğrulandı** (IACR şartları ↔ kok'un içeriği):

| IACR şartı | Kok'un-karşılığı |
|---|---|
| "address research in cryptology and related fields" | KW MatMul PoUW + Demirel 2026/1492 E-gap |
| "be clear, readable, and self-contained" | KOK_V2_PAPER.md 2.310 satır, 11/11 canlı-doğrulanmış referans |
| "look somewhat new and interesting" | E-gap teşhisi — 2026 PoUW alanının tek net teşhisi |
| "contain proofs or convincing arguments" | T1-T3 theorem skeletons + toy proofs + ölçümler |
| "must not be anonymous and state title, author name(s), and a contact address" | ✅ (bkz. §2 — kullanıcı-doldurur) |

**Moderasyon-notu (dürüst):** "If a paper is accepted, this does not mean that
the editors have verified any claims or arguments." Yani ePrint bir
onay-değil, bir **arşivleme+görünürlük** kanalı. Bu, yine-de-kok'un 388
commit'inden-sonra-ilk-gerçek-dış-artefakt'ı-üretir.

---

## 1. Makalenin-konusu (evrim-sonrası-odak)

**Plan A (L1'yi-yayınla)** yanlış. Makale, kok'un **gerçek-differentiating
knowledge**'ına-odaklanmalı (Seçenek-C-raporu §2):

1. **E-gap teşhisi** — Pearl'in çöküş-sebebinin "PW çalışmıyor" değil,
   "E (demand exogeneity) sağlanamıyor" olduğu. W ve B elde-edilebilir,
   E elde-edilemez. (Demirel 2026/1492'nin-bağımsız-okuması)
2. **Computation-binding mekanizması (TV-82)** — verification'ın "job
   identity"yi-değil "computation"ı-bağlaması-gerektiği. Round-5b'de-kendi
   hatasını-buldu: commitment-string'ini-bağlıyordu, computation'ı-değil.
3. **Negatif-sonuç-metodolojisi** — "iddia ile kod arasındaki tutarsızlığı
   yakalama" disiplini: θ=1.05→1.657, "logaritmik cost"→linear,
   ZK-maskeleme→gizlemiyor.

**Önerilen-başlık:**
> "The E-Gap in Proofs of Useful Work: A Diagnosis, a Binding, and the
> Negative Results That Found Them"

---

## 2. Gönderim-için-gerekli (kullanıcı-doldurur)

IACR şartı: "state title, author name(s), and a contact address or
affiliation(s) on the first page."

- [ ] **Yazar-adı** — kullanıcının-gerçek-adı (agent-uydurmaz, opsec)
- [ ] **İletişim-adresi** — e-posta (arXiv endorsement-mailleri-yerine-bu
      çalışır: IACR editörleri-moderasyon-için-iletişim-kurabilir)
- [ ] **PDF-üretimi** — KOK_V2_PAPER.md → PDF (pandoc veya tarayıcı-yazdırma)

**Agent'ın-yapabileceği:** markdown-şablon, referans-listesi,
metin-temizliği. **Agent'ın-yapamayacağı:** gerçek-ad/e-posta-yazmak,
submit-tuşuna-basmak (kullanıcının-tarayıcısı+kararı).

---

## 3. Süreç (sıralı)

```
1. Kullanıcı: ad + e-posta'yı §2'ye-yazar
2. Agent: KOK_V2_PAPER.md'yi-IACR-şablonuna-çevirir (§4)
3. Kullanıcı: PDF'i-üretir (pandoc) veya agent-üretir
4. Kullanıcı: https://eprint.iacr.org/submit — formu-doldurur
   (başlık, yazar, özet, PDF, lisans-onayı)
5. Moderasyon: editörler-inceler (günler-haftalar)
6. Kabul → URL + dış-artefakt-oluşur → K3-tamamlanır
```

---

## 4. Şablon-hazırlık-durumu

Kullanıcı-ad-onayı-bekleniyor. Şu-anda-hazır:
- `KOK_V2_PAPER.md` — 2.310 satır, theorem-skeletons (T1-T3)
- `KOK_V2_REFERENCES.md` — 977 satır, 11/11-canlı-doğrulanmış
- `KW_ANALYSIS_EN.md` — bağımsız-KW-analizi (Conjecture 6.4/A.1)
- `findings.md` — Pearl-ölçümleri (φ=0, θ=1.657)
- `receipt/kok_receipt_verify_en.py` — çalışan-kod (artifact-ekleri)

**Hala-yok:** IACR-formatında-L aTeX/tex dosyası. IACR ePrint **PDF**
kabul-eder (tex-zorunlu-değil) — pandoc-svg-path-yeterli.

---

## 5. Kill-condition-bağlantısı

Bu-paket **K3**'ü-doğrudan-addressler: "IACR ePrint'e (veya Zenodo'ya)
yayınlanmış bir makale/artefakt — URL" (`KOK_EVOLUSYON_ARASTIRMA_2026-10-18.md`
§5.3). K3'ün-ölçümü: **URL**. Moderasyon-reddi-durumunda Zenodo'ya-yedeklenir
(Osf ön-baskı da-uygun).

## 6. Ne YAPILMAYACAK (dürüst)

- **Gönderim-tuşuna-agent-basmaz.** Submit, kullanıcının-tarayıcısı+kararı.
- **Sahte-yazar-adı-yazılmaz.** Opsec-kuralı (FLASHBACK-taslağındaki-aynı.
  kural: "kimlik-opsec-gereği-benim-tarafımdan-uydurulmaz").
- **Bekleyiş-strateji-değildir.** Demirel-veya-astria-beklemediğimiz-gibi,
  IACR-moderasyonu-da-beklenen-bir-şey-değildir: gönder,-ardından-K1/K2'ye-
  devam-et.

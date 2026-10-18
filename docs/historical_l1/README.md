# HISTORICAL — L1 safhası (arşivlendi 2026-10-18)

> **Bu dizin bir mezarlık değil, bir mahkeme kaydıdır.** Dosyalar silinmedi;
> okunabilir ve aynen korunuyor. Burada olma sebepleri net: **L1 vizyonunun
> kendi kill-kriteri tetiklendi.**

## Neden arşivlendi (ölçümle)

| # | Ölçüm | Kanıt |
|---|---|---|
| 1 | **Kill-kriteri yazılmış ve tetiklendi** — "F3a sonunda sıfır gerçek talep çıkarsa projenin durması gerekir"; F3a **başlamadı bile** | `KOK_V2_PAPER.md:1913-1947` (kök dizinde, hâlâ canlı) |
| 2 | **F0 talep keşfi = 0 görüşme, 0 niyet mektubu** | `README.md:102` |
| 3 | **Kritik yol taleptir, kriptografi değil** — "It depends on one customer with one job" | `KOK_V2_PAPER.md:1920-1924` |
| 4 | **Dış onay 4 haftadır sessiz** — Demirel e-postasına cevap yok | `EPOSTA_DEMIREL*.md` (bu dizin) |
| 5 | **arXiv kapısı kapalı** — 21-Ocak-2026 politikası: kurumsal e-posta tek başına yetersiz, ortak-yazar makalesi veya kişisel endorsement gerekir; ikisi de yok | [arXiv endorsement policy](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/) |
| 6 | **388 commit, sıfır dış artefakt** — PyPI yok, GitHub remote yok, landing yok | `README.md` (kök) |

## Neyle değiştirildi

**Seçenek C — Tamga + x402 "compute-work proof" receipt sınıfı.** Tam rapor:
`../KOK_EVOLUSYON_ARASTIRMA_2026-10-18.md` (583 satır, 43 URL).

> Kok, bir compute-provider'ın gerçekten hangi MatMul/işlemi yaptığını
> **bağımsızca doğrulanabilir** bir makbuz olarak üretir; bu makbuz Tamga'nın
> hash-zincirine ve x402'nin proof-of-done extension'ına bağlanır.
> Madencilik yok, token yok, L1 yok.

## Bu dizinin içeriği

| Dosya | Tür | Tarihsel değer |
|---|---|---|
| `PROJE_KAGIDI.md` | L1 vizyon kâğıdı (v1) | Orijinal "KÖK Network" tezinin ilk yazımı |
| `PROJE_KAGIDI_V2.md` | L1 vizyon kâğıdı (v2) | KW/Pearl/Demirel güncellemesiyle iki-katman tasarım |
| `KOK_V2_TEKNIK_SPEC.md` | Spec Ek A/B/C | Görev pazarı, difficulty matematiği, ekonomik simülasyon |
| `DEGERLENDIRME_100.md` | 100/100 öz-değerlendirme | Mükemmelliyetçi inceleme — kâğıt tavanının (~85) kanıtı |
| `F3A_INVITATION_STRATEGY.md` | Pazarlama stratejisi | F3a'nın hiç başlamadığının kaydı |
| `STAGE4_HUMAN_MONEY_GAP.md` | İnsan/para açığı | "Bu kısım kodla kapanmaz" — raporun en doğru kehaneti |
| `MAIL_AKSIYON_PLANI.md` | E-posta planı | "Cevap gelmezse ne yapacağız" — cevap gelmedi |
| `SARTNAME_DEGERLENDIRMESI.md` | Ajan şartname değerlendirmesi | Antigravity ajan teklifinin kodla doğrulanmış red nedenleri |
| `EPOSTA_DEMIREL.md` + düzenlemeler | Gönderilmiş e-postalar | Demirel'in cevapsızlığının belgesi |
| `EPOSTA_FLASHBACK_DRAFT.md` | Taslak (GÖNDERİLMEDİ) | Kullanıcı onayı hiç gelmedi |

## Burada OLMAYANlar (evrimle birlikte canlı kalır)

Bu dosyalar L1'e özgü değildir ve **kök dizinde kalırlar**:

- `KOK_V2_PAPER.md` — canlı (kod sabit referans alıyor: `probe_round6b_paper_en.py:21`)
- `KOK_V2_TECHNICAL_SPEC.md`, `KOK_V2_REFERENCES.md`, `KOK_V2_CRYPTO_BRIEF.md` — reviewer paketi
- `KW_ANALIZ.md`, `KW_ANALYSIS_EN.md`, `findings.md`, `KAYNAKLAR.md` — kuramsal analiz (E-gap)
- `README.md`, `CHANGELOG.md`, `progress.md`, `task_plan.md`, `ROUND5A_FINDINGS.md`, `F0B_PRODUCTION_DESIGN.md`
- `*_en.py` prototipleri ve `docs/OLCUM_D4_2026-10-17.md` (ölçümler)

## Kural

**Bu dizine yeni commit ATILMAZ.** L1'e özgü hiçbir yeni doküman, tokenomik,
hukuk metni veya GHOSTDAG parametresi yazılmaz (evrim raporu §5.4). Burası
okunabilir, alıntılanabilir — ama ölüdür.

*Arşiv tarihi: 2026-10-18 · Karar: `docs/KOK_EVOLUSYON_ARASTIRMA_2026-10-18.md` §5*

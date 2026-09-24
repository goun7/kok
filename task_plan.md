# GÖREV PLANI: KÖK Network Proje Kâğıdı — Mükemmelliyetçi 100/100 Değerlendirmesi

## Hedef
`PROJE_KAGIDI.md`'deki "KÖK Network" (PoUM + GHOSTDAG, faydalı AI matris madenciliği) fikrini;
Eylül 2026 tarihindeki güncel akademik kriptografi, blokzincir ekonomisi ve sektör verileriyle
first-principles bakış açısıyla değerlendirmek; puanlamak (100 üzerinden) ve iyileştirme
önerileriyle birlikte `DEGERLENDIRME_100.md` raporunu üretmek.

## İlk İlkeler (First Principles)
- **Göz ardı edilemez amaç:** Blokzincir güvenliği, "dışarıdan faydalı" hesaplamadan gelir gibi görünmelidir; ama güvenlik bütçesi ile faydalı işin değeri arasında çelişki vardır (useful-PoW ikilemi).
- **Kırılamaz kısıtlar:** (1) Doğrulama, ispatlanandan asimptotik olarak çok daha ucuz olmalı; (2) İsınma/görev seçimi saldırılarına (structured matrix cheating) dayanıklı olmalı; (3) PoW güvenliği için işin "tekrar üretilemez" ve bloğa bağlı olması gerekir.
- **Atılması gereken varsayımlar:** "Matris çarpımı = zor iş" varsayımı (yapısal matrislerde O(n)'ye düşer), "doğrulayıcı enerji harcamaz" iddiası, "on-chain WASM güncellemesi = forksuz göç" iddiası.

## Fazlar
| # | Faz | Durum |
|---|-----|-------|
| 1 | Proje kâğıdını oku + first-principles çerçevesini kur | complete |
| 2 | Kriptografi SOTA: GKR/sumcheck, lattice folding/IVC, zkML (2025-2026) | complete |
| 3 | Useful-PoW literatürü + bilinen saldırılar ve ekonomik eleştiriler | complete |
| 4 | Kaspa/GHOSTDAG durumu + rakip manzara (HadAgent, Dynex, Bittensor...) | complete |
| 5 | Ekonomi (enerji, AI compute talebi, fair-launch fonlama) + regülasyon | complete |
| 6 | Puanlama rubriği + `DEGERLENDIRME_100.md` raporunun yazılması | complete |
| 7 | Kullanıcıya sunum ve tartışma | complete |
| 8 | **Güncellilik + migration analizi** → `DEGERLENDIRME_100.md` §6–§7 | complete |
| 9 | **2026 SOTA proof sistemleri araştırması** (S-two/Lean, ZK-ACE, ZEBRA, frontier-AI ZK, mm exponent) | complete |
| 10 | **`PROJE_KAGIDI_V2.md` — kâğıt üzerinde en iyi + future-proof sistem** | complete |

## Next Step
Tüm çıktılar tamamlandı. Tartışma/revizyon için hazır; istenirse v2'nin herhangi bir bölümü
(büyükluk: görev pazarı, difficulty formülasyonu, ekonomik simülasyon spec'i) derinleştirilebilir.


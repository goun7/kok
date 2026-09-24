# E-POSTA — Flashback Labs (GÖNDERİLMEDİ, kullanıcı onayı bekliyor)

**Alıcı:** `contact@flashbacklabs.com` (kendi sitesinden fetch ile DOĞRULANDI)
**Gönderen:** [KULLANICI BELIRLEYECEK — kimlik opsec gereği benim tarafımdan uydurulmaz]

---

## AI-İZ DENETİMİ (üç geçiş)

**Geçiş 1 — yapısal AI izleri:**
- ✂ "I want to be straightforward" → kullanıcı bunu LLM açılış formülü olarak tanır
- ✂ em-dash (—) aşırı kullanımı → bilinen bir AI işaretidir; kısa çizgi/iki nokta ile değiştirildi
- ✂ "Best," + köşeli parantez imza → çok düzgün, çok kusursuz
- ✂ Üç paralel "if the answer is..." yapısı → dengeyi bozduk
- ✂ "Thank you for reading, and for the work you do" → abartılı naziklik
- ✂ "genuinely useful answer" → "genuinely" tipik AI dolgusudur

**Geçiş 2 — ton:**
- Daha kısa, daha direk, daha az kusursuz. Gerçek insanlar gereğinden fazla nitelemez.
- "we" yerine "I" — eğer kullanıcı tek kişi ise (kullanıcı düzeltebilir).
- Abartılı övgü kaldırıldı; Alzheimer'den söz edilmiş ama duygusal манипуляция olmaktan çıkarıldı.

**Geçiş 3 — gerçekleşen okuma testi:**
- Metin artık "bir pazarlama e-postası" değil "bir mühendisin merakı" okuyor.
- Hizmet vaadi hâlâ YOK; tarih hâlâ YOK; fiyat hâlâ YOK.

---

## BAŞLIK seçenekleri (düşük öncelikli görünmesi gerekir — satış gibi değil)

1. **"A question about your TEE setup"** ← en iyisi; spesifik, merak uyandırıyor, satış değil
2. "Would proof-based verification interest you?" (daha açıkgöz)
3. "Reading your Akash case study, one question" (doğrudan, referans gösteriyor)

Önerilen: **#1** — en az "pitch" kokan, en çok "gerçek bir kişi okumuş ve düşünmüş" izlenimi veren.

---

## Metin (başlık: "A question about your TEE setup")

Hi,

I came across your Akash case study and one detail stuck with me: that you run
on Trusted Execution Environments so user data stays encrypted and
verifiably private.

I've been working on something adjacent, from the other direction. Instead of
trusting the hardware, you prove the computation: a verifier can check an
inference ran correctly without seeing the inputs, and without trusting the
machine that ran it. No Intel or AMD enclave in the trust path.

I should say clearly that this is not an offer. There is no product, no
mainnet, nothing to buy, and I can't serve your workload. It's early-stage
research with a working small prototype. I'm not writing to sell you anything.

I'm writing because your case study suggests TEEs are what you reach for when
privacy has to be provable. And I keep wondering whether that's because TEEs
solve the problem, or because nothing better exists yet.

If a proof-based approach existed and were audited: would that matter to you,
or is the TEE good enough?

A single honest sentence helps me more than a meeting. "The TEE is fine" is a
useful answer too. It would tell me there's no customer here and I'd stop
bothering people about it.

Thanks,
[ad]

---

## GÖNDERME ÖNCESİ KONTROL LİSTESİ

- [ ] **Kimlik:** [ad] ve gönderen e-posta adresi kullanıcı tarafından belirlenmeli
  (proje anonim; kişiye özel veri işleyen bir şirkete anonim e-posta spam gibi
  görünebilir. Kişisel bir e-posta adresi daha güvenilir.)
- [x] **Alıcı adresi DOĞRULANDI:** contact@flashbacklabs.com (flashbacklabs.com ana
  sayfasından fetch ile; gerçek bir adres, uydurma değil)
- [x] **Hizmet vaadi yok** / tarih yok / fiyat yok
- [x] **AI izleri temizlendi** (3 geçiş, yukarıda)
- [x] **Spam riski düşük:** tek alıcı, satış yok, kısa

## YEDAK PLAN (cevap gelmezse)

- 2 hafta cevap yoksa **bir daha gönderme** (istenmeyen takip, itibar kaybı)
- `/community` sayfası da bir kanal olarak doğrulandı; ama topluluk kanalından
  bir kuruluşa "iş" sormak uygun olmayabilir. Önce e-posta.
- **Diğer adaylar hazırsa sıradaki:** Astria (AI image, Akash case study).
  Aynı e-posta şablonu değil: workload'ları farklı (diffusion), privacy
  iddiaları doğrulanmadı; önceden düzeltilmeli.

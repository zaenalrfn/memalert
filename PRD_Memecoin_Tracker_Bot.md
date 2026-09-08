# PRD: Memecoin Tracker & Alert Bot

**Versi:** 1.1
**Tanggal:** 7 September 2026
**Status:** Draft — scope terkonfirmasi (single-user, Solana, dengan fitur mute)

---

## 1. Latar Belakang & Tujuan

Memecoin baru bermunculan setiap menit, terutama di **Solana** yang jadi chain paling ramai untuk listing token baru. Manual memantau DexScreener/Birdeye 24/7 tidak realistis. Bot ini akan **memantau token baru secara otomatis di Solana**, menyaring berdasarkan kriteria keamanan & momentum, lalu **mengirim alert real-time** ke Telegram — untuk penggunaan personal (single-user).

**Tujuan proyek:**
- Membangun bot yang bisa mendeteksi token baru dalam waktu <2 menit sejak listing.
- Menyaring noise (99% token baru adalah scam/rug) dengan filter kriteria yang bisa dikustomisasi.
- Memberikan alert yang actionable, bukan cuma "ada token baru" tapi konteks singkat (liquidity, holder, volume).

**Non-tujuan (out of scope untuk v1):**
- Bot ini **tidak** melakukan auto-trading/auto-buy. Ini murni monitoring & alerting.
- Tidak menyediakan sinyal "beli/jual" — hanya data mentah + filter.

> ⚠️ **Disclaimer penting**: Memecoin sangat berisiko tinggi (rug pull, honeypot, wash trading). Bot ini adalah *tooling*, bukan financial advice. Kriteria filter membantu menyaring noise, tapi tidak menjamin token aman.

---

## 2. Target Pengguna

- **Single-user / personal use** — bot ini dipakai sendiri, bukan layanan multi-tenant untuk banyak orang. Tidak ada sistem subscribe/registrasi user lain.
- Level teknis: familiar dasar Python, bisa jalankan bot di laptop/VPS sendiri.
- Implikasi desain: tidak perlu sistem user management, cukup satu `chat_id` Telegram tujuan dan satu set config filter aktif (meski tetap bisa punya beberapa *profil* filter untuk dipakai gantian sendiri — lihat fitur mute di bawah).

---

## 3. User Stories

| # | Sebagai... | Saya ingin... | Supaya... |
|---|---|---|---|
| 1 | User | menerima notifikasi Telegram saat token baru muncul di **Solana** | tidak perlu refresh DexScreener manual |
| 2 | User | mengatur filter minimum liquidity, holder count, volume 5 menit | hanya dapat alert untuk token yang berpotensi, bukan semua token |
| 3 | User | melihat status keamanan dasar kontrak (mint authority, LP lock, honeypot check) | terhindar dari rug pull yang paling jelas |
| 4 | User | melihat histori alert yang pernah dikirim | bisa evaluasi performa filter dari waktu ke waktu |
| 5 | User (advanced) | menambahkan filter custom via config file tanpa edit kode | mudah eksperimen tanpa deploy ulang |
| 6 | User | mengirim perintah **mute** ke bot (misal via Telegram command) untuk hentikan alert sementara | tidak kebanjiran notifikasi saat market sedang chaotic (banyak token baru sekaligus) |
| 7 | User | mengatur durasi mute (misal 30 menit / 1 jam / sampai di-unmute manual) | fleksibel kontrol kapan mau "istirahat" dari notifikasi |
| 8 | User | tetap melihat token yang lolos filter selama mute di histori/log | tidak kehilangan data meski notifikasi dimatikan sementara |

---

## 4. Fitur & Requirement

### 4.1 Fitur Wajib (MVP)

| Fitur | Deskripsi |
|---|---|
| **Token discovery** | Polling API DexScreener untuk pasangan/token baru di **Solana** |
| **Filter engine** | Filter berdasarkan: liquidity USD minimum, umur pool (age), volume 5m/1h, market cap, jumlah transaksi buy vs sell |
| **Alert dispatcher** | Kirim pesan terformat ke Telegram Bot API (chat personal/grup pribadi) |
| **Deduplication** | Token yang sudah dialert tidak dikirim ulang (simpan token address yang sudah diproses) |
| **Logging** | Simpan semua token yang lolos filter ke database lokal (SQLite) untuk histori & evaluasi — tetap dicatat meski sedang mute |
| **Config file** | File `.env`/`config.yaml` untuk atur threshold filter tanpa ubah kode |
| **Mute command** | Perintah Telegram (misal `/mute 30m`, `/mute 1h`, `/unmute`) untuk menghentikan pengiriman alert sementara tanpa mematikan bot. Saat mute aktif, bot tetap polling & logging di background, hanya notifikasi yang ditahan. Auto-unmute otomatis saat durasi habis |

### 4.2 Fitur Tambahan (v1.5 — nice to have)

| Fitur | Deskripsi |
|---|---|
| **Basic security check** | Cek via GoPlus Security API / Honeypot.is: mint authority renounced?, LP locked/burned?, honeypot risk? |
| **Mute status command** | Perintah `/status` untuk cek apakah bot sedang mute, sisa berapa lama |
| **Auto-mute adaptif** | Bot otomatis saran/mute sendiri kalau jumlah token lolos filter dalam 1 menit melebihi threshold tertentu (deteksi kondisi market chaotic) |
| **Rate-limit guard** | Auto-throttle biar tidak kena rate limit API |
| **Chart snapshot** | Kirim gambar mini-chart harga bersama alert (opsional, pakai matplotlib) |

### 4.3 Fitur Masa Depan (v2 — di luar scope awal)

- Dukungan multi-chain lain (BSC, Base) — ditunda sampai versi Solana stabil.
- Discord support sebagai alternatif channel notifikasi.
- Wallet/whale tracking terintegrasi.
- PnL tracker untuk token yang di-track.
- Dashboard web (bukan cuma Telegram).
- Multi-user/multi-watchlist kalau suatu saat mau dibagikan ke orang lain.

---

## 5. Kriteria Filter (Default yang Disarankan)

Ini contoh starting point, semua harus configurable:

```yaml
filters:
  min_liquidity_usd: 5000
  min_volume_5m_usd: 1000
  max_age_minutes: 60        # hanya token yang baru muncul <1 jam
  min_holder_count: 20       # jika data tersedia dari API
  min_buy_sell_ratio: 1.2    # lebih banyak buy daripada sell
  require_lp_locked: true
  require_mint_renounced: true
  blacklist_keywords:        # hindari token dengan nama mencurigakan
    - "test"
    - "scam"
```

---

## 5.1 Spesifikasi Fitur Mute

Fitur ini penting karena saat market Solana sedang ramai (misal ada tren memecoin viral), bisa muncul puluhan token lolos filter dalam hitungan menit — bot bisa jadi sumber spam notifikasi kalau tidak ada kontrol.

**Perilaku:**
- User kirim command ke bot Telegram: `/mute 30m`, `/mute 1h`, `/mute 3h`, atau `/mute` (tanpa durasi = mute sampai di-unmute manual).
- Selama mute aktif:
  - Bot **tetap polling** DexScreener dan **tetap menjalankan filter engine** seperti biasa.
  - Bot **tetap menyimpan** token yang lolos filter ke SQLite (status `alerted_muted` misalnya), supaya tidak ada data yang hilang.
  - Bot **tidak mengirim** pesan Telegram untuk token yang lolos filter.
- User bisa cek sisa waktu mute dengan `/status`.
- User bisa matikan mute lebih awal dengan `/unmute`.
- Saat durasi mute habis, bot otomatis kirim 1 pesan ringkasan: *"Mute berakhir. X token lolos filter selama mute, cek /history untuk lihat semua."*
- (Opsional v1.5) `/history` — command untuk lihat daftar token yang lolos filter selama periode mute terakhir, supaya user tidak kehilangan info penting meski notifikasi sempat dimatikan.

**Struktur data tambahan (state mute):**
Disimpan simpel di file lokal (misal `mute_state.json`) atau tabel kecil di SQLite:

```json
{
  "is_muted": true,
  "muted_at": "2026-09-07T10:00:00Z",
  "mute_until": "2026-09-07T10:30:00Z",
  "muted_by_command": "/mute 30m"
}
```

Bot cek state ini setiap kali mau kirim alert — kalau `is_muted: true` dan waktu sekarang masih `< mute_until`, alert ditahan (tidak dikirim, tapi tetap dicatat).

---

## 6. Arsitektur Teknis

### 6.1 Stack yang Direkomendasikan (100% Gratis)

| Komponen | Pilihan | Alasan / Status Biaya |
|---|---|---|
| Bahasa | **Python 3.11+** | Open-source, gratis install |
| Scheduler | `asyncio` loop bawaan Python (atau `APScheduler`) | Bawaan/library open-source, tidak ada biaya |
| Database | **SQLite** (via `sqlite3` bawaan Python) | File lokal, tidak perlu server DB terpisah, gratis |
| Notifikasi | `python-telegram-bot` | Library gratis; Telegram Bot API sendiri gratis tanpa batas |
| HTTP client | `httpx` (async) | Library open-source, gratis |
| Config | `.env` (python-dotenv) + `config.yaml` | Gratis, pisahkan secret dari kriteria filter |
| Deployment | Laptop/PC sendiri (dev) → **Oracle Cloud Free Tier** (produksi) | VPS gratis **selamanya** (bukan trial), spek kecil tapi cukup untuk bot ini. Alternatif: Railway/Render free tier (ada batas jam/auto-sleep) |

> Total biaya stack ini: **$0 development, $0/bulan hosting** (dengan Oracle Cloud Free Tier).

### 6.2 Sumber Data API (Fokus yang Gratis)

| API | Status Gratis | Fungsi | Catatan |
|---|---|---|---|
| **DexScreener API** (`api.dexscreener.com`) | ✅ 100% gratis, **tanpa API key** | Data pair/token real-time: harga, liquidity, volume, chain | Rate limit: ~300 req/menit untuk endpoint pair/token/search, 60 req/menit untuk endpoint profile/boost/ads. **Tidak ada endpoint historical/OHLC** — kalau butuh chart, harus polling & simpan snapshot sendiri. Ini jadi **sumber data utama MVP**. |
| **GoPlus Security API** | ✅ Gratis untuk basic check | Cek keamanan kontrak (honeypot, mint authority, LP lock, dll) | Tidak butuh kartu kredit, cocok untuk fitur security check v1.5 |
| Birdeye API | ⚠️ Ada free tier tapi terbatas & butuh signup | Data Solana lebih dalam (holder count, token security score) | **Di-skip dulu di MVP** — opsional untuk v2 kalau DexScreener+GoPlus belum cukup |
| Moralis API | ⚠️ Ada free tier tapi butuh API key & ada limit | Alternatif data on-chain multi-chain, streams/webhook | **Di-skip dulu di MVP** |

> Karena DexScreener tidak punya endpoint historis, strategi polling-nya adalah: setiap interval, ambil daftar token/pair terbaru → bandingkan dengan token yang sudah ada di DB lokal → proses hanya yang benar-benar baru.

### 6.3 Alur Sistem (High-Level)

```
[Scheduler: tiap 15-30 detik]
        │
        ▼
[Fetch token/pair baru dari DexScreener API per chain]
        │
        ▼
[Cek: sudah pernah diproses? (dedup via SQLite)] ──> Ya ──> Skip
        │ Tidak
        ▼
[Terapkan filter engine (liquidity, volume, age, dst)]
        │
        ├── Tidak lolos ──> Simpan log "rejected" (opsional) ──> Skip
        │
        ▼ Lolos
[Opsional: Security check via GoPlus/Honeypot API]
        │
        ▼
[Format pesan alert]
        │
        ▼
[Cek mute state] ──> Sedang mute? ──> Ya ──> Simpan sebagai "alerted_muted" (tidak dikirim)
        │ Tidak
        ▼
[Kirim ke Telegram Bot API]
        │
        ▼
[Simpan ke SQLite sebagai "alerted"]
```

**Listener terpisah**: bot juga menjalankan listener command Telegram (`/mute`, `/unmute`, `/status`, `/history`) secara paralel dengan loop polling di atas, supaya user bisa kontrol mute kapan saja tanpa mengganggu proses discovery yang berjalan terus di background.

### 6.4 Struktur Data (SQLite — sederhana)

**Tabel `tokens_seen`**
| Kolom | Tipe | Keterangan |
|---|---|---|
| token_address | TEXT (PK) | Alamat kontrak token |
| chain | TEXT | `solana` (default & fokus MVP; kolom disiapkan generic untuk ekspansi chain lain di v2) |
| first_seen_at | DATETIME | Kapan pertama kali terdeteksi |
| status | TEXT | `rejected` / `alerted` / `alerted_muted` (lolos filter tapi notifikasi ditahan karena mute aktif) |
| liquidity_usd | REAL | Snapshot saat dicek |
| volume_5m_usd | REAL | Snapshot saat dicek |

**Tabel `mute_state`** (single row, karena single-user)
| Kolom | Tipe | Keterangan |
|---|---|---|
| is_muted | BOOLEAN | Status mute saat ini |
| muted_at | DATETIME | Kapan mute diaktifkan |
| mute_until | DATETIME (nullable) | Kapan mute otomatis berakhir; `NULL` = mute manual sampai `/unmute` |

---

## 7. Format Alert (Contoh)

```
🚨 NEW TOKEN ALERT — Solana

🪙 Token: $PEPU (Pepe Universe)
📍 Contract: 7xKX...s9dP (tap to copy)
💧 Liquidity: $12,500
📊 Volume (5m): $3,200
👥 Holders: 45
🔒 LP Locked: ✅
🖋️ Mint Renounced: ✅
⏱️ Pool Age: 8 menit

🔗 DexScreener: [link]

⚠️ DYOR — bukan financial advice
💡 Ketik /mute 30m kalau mau istirahat dari alert
```

---

## 8. Metrik Keberhasilan (Success Metrics)

| Metrik | Target |
|---|---|
| Latency deteksi (dari token listing sampai alert terkirim) | < 2 menit |
| False positive rate (token lolos filter tapi ternyata rug cepat) | Dipantau & dievaluasi mingguan, iterasi kriteria filter |
| Uptime bot | > 95% (untuk personal project, boleh sedikit longgar) |
| Rate limit error | 0 (dengan proper throttling) |

---

## 9. Risiko & Mitigasi

| Risiko | Mitigasi |
|---|---|
| Kena rate limit API | Implementasi backoff/retry, cache hasil, batasi jumlah chain yang dipoll bersamaan |
| False sense of security (user kira "lolos filter" = aman) | Selalu sertakan disclaimer di setiap alert |
| API pihak ketiga berubah/down | Wrap semua call API dengan try-except + fallback logging, jangan biarkan bot crash total |
| Biaya API premium (Birdeye/Moralis) membengkak | Mulai dari DexScreener (gratis) dulu di MVP, baru tambah API lain kalau perlu |
| Spam alert (terlalu banyak token lolos filter) | Rate-limit jumlah alert per menit, filter lebih ketat by default |

---

## 10. Rencana Development (Milestone)

| Fase | Deliverable | Estimasi |
|---|---|---|
| **Fase 1** | Setup project, koneksi DexScreener API, fetch token baru di Solana, print ke console | 1–2 hari |
| **Fase 2** | Filter engine + SQLite dedup | 1–2 hari |
| **Fase 3** | Integrasi Telegram Bot (kirim alert terformat) | 1 hari |
| **Fase 4** | Command listener: `/mute`, `/unmute`, `/status` + cek mute state sebelum kirim alert | 1 hari |
| **Fase 5** | Config file (yaml/env) supaya threshold mudah diubah | 0.5 hari |
| **Fase 6** | Testing di laptop/VPS, monitoring 24 jam, tuning filter | 2–3 hari (observasi) |
| **Fase 7 (opsional)** | Security check (GoPlus/Honeypot API) + `/history` command | 1–2 hari |

**Total estimasi MVP: ~6–8 hari kerja** untuk yang sudah familiar Python.

---

## 11. Kebutuhan Setup

- [ ] Akun Telegram + buat bot via [@BotFather](https://t.me/BotFather) → dapat Bot Token (gratis)
- [ ] Buat grup/channel Telegram untuk terima alert, invite bot, ambil `chat_id`
- [ ] Python 3.11+ terinstall, virtual environment (gratis)
- [ ] Development & testing awal: jalankan di laptop/PC sendiri (gratis, tidak perlu setup apa pun)
- [ ] Untuk jalan 24/7: daftar **Oracle Cloud Free Tier** (VPS gratis permanen, perlu verifikasi kartu kredit saat daftar tapi tidak ditagih selama dalam free tier) — alternatif: Railway/Render free tier
- [ ] (Opsional, v2) Daftar API key Birdeye/Moralis kalau nanti butuh data lebih dalam dari yang gratis

---

## 12. Keputusan Scope (Terkonfirmasi)

| Pertanyaan | Keputusan |
|---|---|
| Multi-user atau single-user? | **Single-user**, personal use. Tidak ada sistem registrasi/subscribe user lain. |
| Chain prioritas? | **Solana** dulu untuk MVP. Chain lain (BSC, Base) ditunda ke v2. |
| Butuh fitur mute? | **Ya** — lihat spesifikasi lengkap di bagian 5.1. |

## 13. Pertanyaan Terbuka (Sisa)

- Durasi mute default kalau user ketik `/mute` tanpa angka — mau default berapa lama (misal 30 menit)?
- Untuk auto-mute adaptif (fitur v1.5, deteksi market chaotic otomatis): threshold-nya berapa token/menit yang dianggap "chaotic"? Perlu observasi dulu setelah bot jalan beberapa hari untuk nentuin angka yang wajar.
- Apakah command `/history` (lihat token yang lolos filter selama mute) prioritas masuk MVP, atau cukup v1.5?

# PRD: Memecoin Tracker & Alert Bot (Solana)

## 📋 Metadata
- **Nama Produk:** Solana Memecoin Tracker & Alert Bot
- **Versi:** 1.0 (MVP)
- **Target Platform:** Telegram & Python CLI / VPS
- **Lokasi Dokumen:** `.agents/1-PRD.md`

---

## 📄 BAGIAN 1: Visi & Tujuan Produk

### Visi Produk
Menjadi asisten pemantau on-chain personal yang ringan, andal, dan zero-cost untuk menyaring ribuan token baru di jaringan Solana secara otomatis, memfilter noise dan potensi scam, serta mengirimkan alert actionable secara instan ke Telegram tanpa membebani pengguna dengan notifikasi berlebih.

### Tujuan Utama (4 Tujuan)
1. **Deteksi Real-Time Cepat:** Menemukan dan memproses pasangan token baru di Solana dalam waktu < 2 menit sejak pool terdaftar di DEX.
2. **Reduksi Noise & Scam:** Menyaring > 95% token sampah/rug melalui filter parameter likuiditas, rasio volume, pool age, dan validasi keamanan dasar.
3. **Kendali Penuh Anti-Spam:** Mencegah alert fatigue pada pengguna melalui fitur mute fleksibel (durasi/manual) dengan jaminan zero data loss di database lokal.
4. **Zero Hosting & API Cost:** Memastikan arsitektur dapat berjalan 100% gratis menggunakan DexScreener API public, SQLite, dan Oracle Cloud Free Tier.

### Value Proposition
- **100% Free Stack:** Beroperasi tanpa biaya API berbayar maupun biaya server bulanan.
- **Noise-Free Alerting:** Filter modular yang dapat disesuaikan tanpa perlu kompilasi atau redeploy kode.
- **Smart Mute & Background Persistence:** Mengistirahatkan notifikasi Telegram saat kondisi market chaotic tanpa menghentikan pemantauan dan pencatatan log.

---

## 📄 BAGIAN 2: User Persona

### Persona 1: Dika (Active Solana Degen Trader)
- **Usia/Pekerjaan:** 26 tahun, Crypto Trader & Freelancer
- **Level Teknis:** Menengah (terbiasa dengan DEX, contract address, Telegram bot, dan CLI dasar)
- **Tujuan:** Menjadi salah satu pihak pertama yang mendeteksi token Solana potensial dengan likuiditas riil sebelum harganya melesat.
- **Pain Points:** Terlalu banyak token scam/rug pull baru setiap menit; memantau DexScreener manual 24/7 melelahkan; bot telegram umum sering mengirim ratusan spam alert yang tidak berguna.
- **Motivasi:** Membutuhkan bot personal yang hanya mengirim alert jika token memenuhi standar ketatnya, dan dapat dibisukan sementara saat market sedang chaos.

### Persona 2: Rian (Developer & Self-Hoster)
- **Usia/Pekerjaan:** 30 tahun, Software Engineer & Hobbyist
- **Level Teknis:** Mahir (Python, Docker, Linux VPS, Git)
- **Tujuan:** Menjalankan bot monitoring pribadi di VPS gratis miliknya yang stabil, hemat memori, dan mudah dikonfigurasi via file YAML/.env.
- **Pain Points:** Malas membayar subscription bulanan untuk bot pihak ketiga; API berbayar seperti Moralis/Birdeye mahal untuk proyek hobi.
- **Motivasi:** Memiliki bot open/clean source berbasis Python dan SQLite yang bisa di-tweak sendiri logikanya tanpa dependensi infrastruktur kompleks.

---

## 📄 BAGIAN 3: User Stories

### Modul 1: Token Discovery & Polling
- Sebagai pengguna, saya ingin bot memantau pasangan token baru di Solana secara otomatis, agar saya tidak perlu me-refresh DexScreener secara manual.
- Sebagai pengguna, saya ingin bot melakukan deduplikasi token, agar saya tidak menerima alert berulang untuk token yang sama.
- Sebagai pengguna, saya ingin bot mencatat timestamp penemuan token pertama kali, agar saya tahu berapa cepat bot mendeteksi pool tersebut.

### Modul 2: Filter Engine & Security
- Sebagai pengguna, saya ingin menyaring token berdasarkan minimum likuiditas USD dan volume 5 menit, agar hanya token bervolume aktif yang masuk ke radar saya.
- Sebagai pengguna, saya ingin membatasi umur maksimal pool (misal < 60 menit), agar fokus hanya pada token yang benar-benar baru listing.
- Sebagai pengguna, saya ingin menyaring token dengan rasio buy vs sell tertentu, agar terhindar dari token yang hanya memiliki transaksi dumping.
- Sebagai pengguna, saya ingin memfilter token berdasarkan kata kunci terlarang (blacklist), agar token berpola scam/test langsung diabaikan.
- Sebagai pengguna, saya ingin melihat validasi keamanan dasar (mint renounced & LP lock), agar terhindar dari rug pull yang paling umum.

### Modul 3: Telegram Alerting & Mute Control
- Sebagai pengguna, saya ingin menerima notifikasi Telegram dengan ringkasan data penting (nama, contract address, liquidity, volume, pool age), agar dapat mengambil keputusan cepat.
- Sebagai pengguna, saya ingin format contract address mudah di-copy (1-tap copy), agar proses swap di DEX cepat dilakukan.
- Sebagai pengguna, saya ingin mengirim perintah `/mute [durasi]` ke bot, agar notifikasi berhenti sementara saat market sedang chaotic.
- Sebagai pengguna, saya ingin bot tetap mencatat token yang lolos filter ke database saat mute aktif, agar data tidak hilang.
- Sebagai pengguna, saya ingin mengecek status mute saat ini melalui `/status`, agar mengetahui sisa waktu mute.
- Sebagai pengguna, saya ingin bot mengirim notifikasi saat durasi mute berakhir beserta rekap token yang lolos selama masa mute, agar saya tidak ketinggalan informasi.
- Sebagai pengguna, saya ingin membatalkan mute kapan saja dengan `/unmute`, agar bisa langsung menerima notifikasi kembali.

### Modul 4: Konfigurasi & Persistensi
- Sebagai pengguna, saya ingin mengubah parameter filter di file `config.yaml` tanpa mengubah script kode sumber, agar penyesuaian threshold mudah dilakukan.
- Sebagai pengguna, saya ingin histori token tersimpan di SQLite lokal, agar saya bisa mengevaluasi efektivitas filter mingguan.

---

## 📄 BAGIAN 4: Functional Requirements

### Modul 1: Token Discovery & Deduplikasi

**FR-01: Polling Pasangan Baru DexScreener**
- **Input:** Parameter query chain Solana ke endpoint DexScreener API (`api.dexscreener.com`).
- **Proses:** Scheduler async mengeksekusi request HTTP GET berkala (interval default 15–30 detik) untuk mengambil daftar pool/token terbaru di Solana.
- **Output:** Raw JSON array berisi data token/pair listing terbaru.
- **Aturan Bisnis:** Interval polling harus dibatasi untuk mematuhi rate limit DexScreener (maksimal 300 request/menit).

**FR-02: Normalisasi dan Ekstraksi Data Token**
- **Input:** Raw JSON pair dari DexScreener.
- **Proses:** Ekstraksi field penting: `token_address`, `pair_address`, `symbol`, `name`, `liquidity_usd`, `volume_5m`, `volume_1h`, `txns_buy`, `txns_sell`, `pool_created_at`.
- **Output:** Objek data terstruktur token siap validasi.
- **Aturan Bisnis:** Abaikan pasangan di luar chain Solana (`chainId != "solana"`).

**FR-03: Deduplikasi Token (SQLite Cache)**
- **Input:** `token_address` yang diekstrak.
- **Proses:** Pengecekan apakah `token_address` telah terdaftar di tabel database SQLite `tokens_seen`.
- **Output:** Boolean `is_seen` (True / False).
- **Aturan Bisnis:** Jika token sudah ada di DB, lewati seluruh proses filter dan pengiriman alert.

---

### Modul 2: Filter Engine & Analisis Keamanan

**FR-04: Filter Umur Pool (Pool Age)**
- **Input:** `pool_created_at` dan waktu sistem saat ini.
- **Proses:** Hitung selisih waktu (`current_time - pool_created_at`). Bandingkan dengan parameter `max_age_minutes`.
- **Output:** Status validasi umur (Lolos / Ditolak).
- **Aturan Bisnis:** Pool dengan umur lebih dari batas maksimal (default: 60 menit) ditolak.

**FR-05: Filter Likuiditas Minimum**
- **Input:** Nilai `liquidity_usd` token.
- **Proses:** Bandingkan nilai dengan `min_liquidity_usd` pada config.
- **Output:** Status validasi likuiditas (Lolos / Ditolak).
- **Aturan Bisnis:** Likuiditas harus lebih besar atau sama dengan threshold (default: $5,000).

**FR-06: Filter Volume Perdagangan**
- **Input:** Nilai `volume_5m` token.
- **Proses:** Bandingkan nilai dengan parameter `min_volume_5m_usd`.
- **Output:** Status validasi volume (Lolos / Ditolak).
- **Aturan Bisnis:** Volume transaksi 5 menit pertama harus >= threshold (default: $1,000).

**FR-07: Filter Rasio Buy vs Sell**
- **Input:** Jumlah transaksi buy dan sell 5 menit.
- **Proses:** Hitung rasio (`txns_buy / max(txns_sell, 1)`).
- **Output:** Status validasi rasio transaksi (Lolos / Ditolak).
- **Aturan Bisnis:** Rasio buy/sell harus >= threshold konfigurasi (default: 1.2).

**FR-08: Filter Blacklist Keyword**
- **Input:** Nama dan simbol token.
- **Proses:** Pencocokan teks (case-insensitive) terhadap daftar blacklist kata (misal: "test", "scam", "airdrop", "pump").
- **Output:** Status validasi keyword (Lolos / Ditolak).
- **Aturan Bisnis:** Jika mengandung salah satu kata dalam blacklist, token langsung dibuang.

**FR-09: Basic Security Check (Opsional/Integrasi)**
- **Input:** `token_address`.
- **Proses:** Request ke security check (GoPlus API) untuk memeriksa `mint_authority` dan status LP lock.
- **Output:** Flag keamanan (`lp_locked: bool`, `mint_renounced: bool`).
- **Aturan Bisnis:** Jika konfigurasi `require_mint_renounced: true` dan token belum renounced, token digugurkan.

---

### Modul 3: Mute Controller & Status Management

**FR-10: Pengecekan Mute State Sebelum Alert**
- **Input:** Waktu saat ini dan record pada tabel/state `mute_state`.
- **Proses:** Evaluasi nilai `is_muted` dan perbandingan `current_time < mute_until`.
- **Output:** Flag apakah alert boleh dikirim ke Telegram atau ditahan.
- **Aturan Bisnis:** Jika `is_muted == True`, alert tidak boleh dikirim ke Telegram, namun tetap dicatat ke database dengan status `alerted_muted`.

**FR-11: Perintah Telegram `/mute`**
- **Input:** Pesan Telegram dari user: `/mute` atau `/mute [durasi]` (contoh: `/mute 30m`, `/mute 1h`, `/mute 3h`).
- **Proses:** Parse string durasi, hitung timestamp `mute_until`, perbarui tabel `mute_state`.
- **Output:** Pesan konfirmasi Telegram: "Bot dimute selama [durasi]. Alert ditahan, pemantauan latar belakang tetap aktif."
- **Aturan Bisnis:** Jika tanpa argumen durasi, mute berlaku tanpa batas waktu (`mute_until = NULL`) hingga user menjalankan `/unmute`.

**FR-12: Perintah Telegram `/unmute`**
- **Input:** Pesan Telegram dari user: `/unmute`.
- **Proses:** Set `is_muted = False` dan `mute_until = NULL` pada `mute_state`.
- **Output:** Pesan konfirmasi Telegram: "Bot kembali aktif! Alert akan langsung dikirimkan."
- **Aturan Bisnis:** Dapat dipanggil kapan saja untuk menghentikan masa mute lebih awal.

**FR-13: Perintah Telegram `/status`**
- **Input:** Pesan Telegram dari user: `/status`.
- **Proses:** Baca status `is_muted`, sisa waktu mute (jika aktif), dan statistik sederhana (jumlah token dipantau hari ini).
- **Output:** Pesan status bot dan informasi sisa durasi mute.
- **Aturan Bisnis:** Harus merespons secara instan tanpa mengganggu loop monitoring background.

**FR-14: Background Auto-Unmute & Rekapitulasi**
- **Input:** Worker scheduler pengecek waktu.
- **Proses:** Mengecek jika `is_muted == True` dan `current_time >= mute_until`. Reset status mute otomatis dan hitung total token dengan status `alerted_muted` selama periode mute tersebut.
- **Output:** Pesan Telegram notifikasi: "Mute berakhir. [X] token lolos filter selama mute. Gunakan /history untuk melihat daftar."
- **Aturan Bisnis:** Pengiriman rekap otomatis hanya terjadi 1 kali saat transisi mute berakhir.

**FR-15: Perintah Telegram `/history`**
- **Input:** Pesan Telegram `/history` atau `/history [limit]`.
- **Proses:** Query tabel `tokens_seen` untuk token berstatus `alerted_muted` pada sesi mute terakhir.
- **Output:** Daftar ringkas token (nama, simbol, address, liquidity, waktu deteksi).
- **Aturan Bisnis:** Menampilkan maksimal 10 token terbaru secara default untuk menghindari pesan terlalu panjang.

---

### Modul 4: Dispatcher, Logging & Config

**FR-16: Dispatcher Alert Telegram**
- **Input:** Payload data token yang lolos seluruh filter saat kondisi unmuted.
- **Proses:** Format pesan HTML/Markdown sesuai template, kirim via Telegram Bot API ke target `chat_id`.
- **Output:** Pesan alert terkirim ke chat personal/grup pengguna.
- **Aturan Bisnis:** Wajib menyertakan disclaimer risiko DYOR dan instruksi cepat command `/mute 30m`.

**FR-17: Logging & Persistensi Token**
- **Input:** Record token yang selesai diproses (baik lolos maupun ditolak).
- **Proses:** `INSERT` data ke SQLite tabel `tokens_seen` dengan status `alerted`, `alerted_muted`, atau `rejected`.
- **Output:** Record tersimpan permanen di file SQLite lokal.
- **Aturan Bisnis:** Penulisan database harus thread-safe/non-blocking terhadap loop polling.

**FR-18: Manajemen Konfigurasi Dinamis**
- **Input:** File `config.yaml` dan `.env`.
- **Proses:** Parser membaca parameter filter, token API, dan `chat_id` saat startup bot.
- **Output:** Objek konfigurasi runtime.
- **Aturan Bisnis:** Secret credentials (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) wajib disimpan di `.env` dan diabaikan dari git tracking.

**FR-19: Autorisasi Single-User Telegram**
- **Input:** `chat_id` dari pengirim setiap command Telegram yang masuk.
- **Proses:** Validasi apakah `message.chat.id` cocok dengan `TELEGRAM_CHAT_ID` yang dikonfigurasi di `.env`.
- **Output:** Eksekusi command atau penolakan pesan.
- **Aturan Bisnis:** Perintah dari `chat_id` tidak dikenal diabaikan total tanpa balasan pesan (silent drop).

**FR-20: API Rate Limit Guard & Error Handling**
- **Input:** Response status code dari DexScreener API.
- **Proses:** Deteksi error HTTP 429 atau 5xx; jalankan exponential backoff retry.
- **Output:** Log error lokal tanpa menyebabkan bot crash/berhenti.
- **Aturan Bisnis:** Jika terkena limit, interval polling ditunda otomatis (misal 60 detik) sebelum mencoba kembali.

---

## 📄 BAGIAN 5: Non-Functional Requirements

### Performa
- **Polling Interval:** 15–30 detik per request siklus ke DexScreener API.
- **Detection to Alert Latency:** Total waktu dari pengambilan data hingga alert sampai di Telegram < 2 detik.
- **Resource Footprint:** Penggunaan memory RAM < 150 MB dan CPU usage < 5% pada single vCPU (cocok untuk VPS gratis 1 GB RAM).

### Keamanan
- **Proteksi Kredensial:** Bot token dan chat ID tersimpan secara eksklusif di environment variables (`.env`).
- **Single Tenant Isolation:** Hanya 1 Telegram `chat_id` resmi yang diizinkan mengontrol command bot (`/mute`, `/status`, dll.).
- **Input Sanitization:** Argument perintah durasi di-parse secara ketat menggunakan regex untuk mencegah command injection.

### Skalabilitas & Keandalan
- **Self-Healing Loop:** Scheduler dibungkus dalam exception wrapper agar error jaringan sporadis tidak menghentikan daemon bot.
- **State Resilience:** State mute dan deduplikasi disimpan langsung ke SQLite, sehingga bot dapat melanjutkan state sebelumnya jika terjadi restart VPS.
- **Rate-Limiting Compliance:** Throttling otomatis untuk menjamin tidak melebihi 300 req/menit batas gratis DexScreener.

### Usability
- **One-Tap Copy:** Address kontrak token diformat dalam tag `<code>` Telegram monospace agar langsung tersalin saat diketuk di smartphone.
- **Clean Message UI:** Alert menggunakan emoji yang intuitif (🚨, 🪙, 💧, 📊, ⏱️, 🔗) untuk pemindaian visual cepat.
- **Actionable Hints:** Setiap pesan alert menyertakan tautan langsung ke DexScreener dan tips shortcut mute.

---

## 📄 BAGIAN 6: Out of Scope & Dependensi

### Out of Scope (Tidak Dikerjakan di V1)
- **Auto-Trading / Execution Bot:** Tidak ada integrasi private key wallet atau swap transaksi otomatis (pure monitoring).
- **Multi-Chain Support:** Tidak memproses token di luar jaringan Solana (EVM/BSC/Base ditunda ke V2).
- **Web Dashboard UI:** Tidak menyediakan visualisasi berbasis browser atau antarmuka web.
- **Multi-User / SaaS Subscription:** Tidak ada sistem registrasi user lain, pembayaran, atau multi-tenant DB.
- **Historical Chart Rendering:** Tidak mengirim gambar screenshot grafik chart di V1 (cukup tautan DexScreener).

### Dependensi
- **Python Runtime:** Python 3.11+
- **DexScreener API:** Endpoint publik `https://api.dexscreener.com` (100% gratis, tanpa API key).
- **Telegram Bot API:** `@BotFather` token dan webhook/long-polling listener via library `python-telegram-bot`.
- **Database Engine:** SQLite3 (standar bawaan Python).
- **HTTP Client:** `httpx` (async I/O) atau `aiohttp`.
- **Infrastruktur Hosting:** Local workstation (dev) / Oracle Cloud Infrastructure Free Tier (Ubuntu Linux VPS).

### Asumsi
- Pengguna telah membuat bot melalui `@BotFather` dan memiliki `chat_id` Telegram tujuan yang valid.
- DexScreener API tetap menyediakan data listing Solana secara publik tanpa memerlukan API key berbayar.
- Host machine memiliki koneksi internet aktif dengan latensi stabil ke endpoint Telegram dan DexScreener.
- Pengguna memahami dasar eksekusi perintah terminal Python dan Git.

---

## 🔄 Finalisasi & Rekomendasi Lanjutan
1. Dokumen PRD ini tersimpan di `.agents/1-PRD.md`.
2. Siap dilanjutkan ke tahap pembuatan Technical Specification dengan perintah:
   `"Buat Tech Spec berdasarkan PRD yang sudah dibuat"`

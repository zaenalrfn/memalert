# TECH SPEC: Solana Memecoin Tracker & Alert Bot with Vue 3 Web UI

## 📋 Metadata
- **Nama Produk:** Solana Memecoin Tracker & Alert Bot
- **Versi:** 1.0 (MVP)
- **Target Platform:** Localhost (Vue 3 Web UI + FastAPI Backend) & Telegram Bot
- **Lokasi Dokumen:** `.agents/2-TECH-SPEC.md`
- **Referensi:** `.agents/1-PRD.md`

---

## 📄 BAGIAN 1: Tech Stack & Arsitektur

### Tech Stack

| Layer | Technology | Versi | Catatan / Alasan |
|-------|------------|-------|------------------|
| **Frontend Framework** | Vue 3 (Composition API) | 3.4+ | Reaktif, ringan, dan cepat untuk dashboard monitoring |
| **Build Tool & Dev** | Vite | 5.x | Fast HMR dan bundle optimal |
| **CSS Framework** | Tailwind CSS | 3.4+ | Styling UI modern, responsif, dan dark-mode ready |
| **State Management** | Pinia | 2.1+ | State management reaktif untuk konfigurasi & realtime feed |
| **HTTP Client (UI)** | Axios / Fetch API | - | Komunikasi REST ke Backend FastAPI |
| **Backend Framework** | FastAPI (Python) | 0.110+ | Asynchronous high-performance framework untuk API & worker |
| **ASGI Server** | Uvicorn | 0.29+ | Server ASGI async |
| **Database** | SQLite3 | 3.x | File lokal (`memecoin_tracker.db`), zero setup server, WAL mode |
| **Async HTTP Client** | HTTPX | 0.27+ | Client async HTTP untuk polling DexScreener & GoPlus API |
| **Bot Framework** | python-telegram-bot | 21.x+ | Library resmi async untuk dispatch alert dan handler command |
| **Data Sources** | DexScreener API + GoPlus | - | 100% Gratis & tanpa API key / kartu kredit |
| **Hosting** | Localhost (Development & Run) | - | Berjalan lokal di laptop/PC |

---

### Arsitektur Sistem

```
+-------------------------------------------------------------------------------+
|                                  LOCALHOST                                    |
|                                                                               |
|   +--------------------------+                   +------------------------+   |
|   |   Vue 3 Web UI           |    HTTP REST      |    FastAPI Backend     |   |
|   |   - Live Feed Dashboard  |<----------------->|    - API Router        |   |
|   |   - Filter Config Form   |                   |    - Pydantic Schemas  |   |
|   |   - Mute & Bot Control   |                   +-----------+------------+   |
|   +--------------------------+                               |                |
|                                                  Read/Write  | (Direct Sync)  |
|                                                              v                |
|                                                  +------------------------+   |
|                                                  |   SQLite Database      |   |
|                                                  | (`memecoin_tracker.db`)|   |
|                                                  +-----------+------------+   |
|                                                              ^                |
|                                                  Read/Write  |                |
|                                                              |                |
|                                                  +-----------+------------+   |
|                                                  | Async Background Engine|   |
|                                                  | - DexScreener Poller   |   |
|                                                  | - Filter & Sec Evaluator   |
|                                                  | - Telegram Bot Worker  |   |
|                                                  +-------+--------+-------+   |
+----------------------------------------------------------|--------|-----------+
                                                           |        |
                         GET (Public Token Data) <---------+        +--------> Telegram API
                         - DexScreener API                                     - Alert Push
                         - GoPlus Security API                                 - Command Polling
```

---

### Struktur Folder Project

```text
memecoin-tracker/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_config.py      # Endpoints: GET/PUT filter thresholds
│   │   │   ├── routes_tokens.py      # Endpoints: GET history/live tokens
│   │   │   └── routes_bot.py         # Endpoints: GET/POST mute state, bot test
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Settings loader (Pydantic / .env)
│   │   │   └── database.py           # SQLite connection & session manager
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py            # Pydantic data schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── dexscreener_client.py # HTTPX client untuk DexScreener API
│   │   │   ├── goplus_client.py      # HTTPX client untuk GoPlus API
│   │   │   ├── filter_engine.py      # Logika validasi threshold token
│   │   │   ├── telegram_service.py   # Bot sender & command listeners
│   │   │   └── tracker_worker.py     # Background loop discovery & processing
│   │   └── main.py                   # FastAPI app entry point & lifespan startup
│   ├── config.yaml                   # Default filter configuration
│   ├── requirements.txt              # Backend dependencies
│   └── .env.example                  # Template kredensial bot
│
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── assets/
│   │   │   └── main.css              # Tailwind directives
│   │   ├── components/
│   │   │   ├── TokenTable.vue        # Tabel feed token real-time
│   │   │   ├── FilterSettings.vue    # Form kontrol konfigurasi filter
│   │   │   ├── MuteControl.vue       # Toggle & timer status mute
│   │   │   └── StatsCard.vue         # Kartu ringkasan metrik
│   │   ├── stores/
│   │   │   ├── tokenStore.js         # Pinia store untuk live tokens & log
│   │   │   └── configStore.js        # Pinia store untuk filter & mute status
│   │   ├── services/
│   │   │   └── api.js                # Axios HTTP client ke FastAPI
│   │   ├── App.vue                   # Root Vue Component
│   │   └── main.js                   # Vue entry point
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── .agents/
│   ├── 1-PRD.md
│   └── 2-TECH-SPEC.md
├── run_backend.bat                   # Script runner backend (Windows)
├── run_frontend.bat                  # Script runner frontend (Windows)
└── README.md
```

### Justifikasi
- **Vue 3 + Vite:** Setup ringan, rendering cepat, waktu compile instan, dan ekosistem reaktif yang cocok untuk memantau data koin live di browser.
- **FastAPI:** Mendukung *async/await* native dengan performa I/O tinggi untuk menjalankan API server sekaligus background worker polling API tanpa threading yang rumit.
- **SQLite:** Format single-file lokal, zero-configuration, tahan restart, sangat cepat untuk single-user concurrency.

---

## 📄 BAGIAN 2: Database Design

### Ringkasan Database
| Item | Detail |
|------|--------|
| **Database Engine** | SQLite 3 (File: `backend/memecoin_tracker.db`) |
| **Access Layer** | `aiosqlite` / Python `sqlite3` dengan Context Manager |
| **Journal Mode** | WAL (Write-Ahead Logging) untuk mengoptimalkan pembacaan bersamaan |
| **Pendekatan** | Relational / Flat Tabular |

---

### Entity Overview

#### 1. Tabel `tokens_seen`
Menyimpan semua token yang pernah terdeteksi agar tidak terjadi duplikasi alert serta menyimpan riwayat token.

| Kolom | Tipe Data | Constraint | Keterangan |
|-------|-----------|------------|------------|
| `token_address` | TEXT | PRIMARY KEY | Solana Mint Address |
| `pair_address` | TEXT | NOT NULL | Solana Pair/Pool Address di DEX |
| `symbol` | TEXT | NOT NULL | Simbol token (cth: $SOL) |
| `name` | TEXT | NOT NULL | Nama token |
| `chain` | TEXT | DEFAULT 'solana' | Identifikasi chain |
| `liquidity_usd` | REAL | NOT NULL | Nilai likuiditas saat terdeteksi |
| `volume_5m_usd` | REAL | NOT NULL | Volume 5 menit saat terdeteksi |
| `pool_created_at` | DATETIME | NULL | Timestamp pool dibuat di DEX |
| `first_seen_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Waktu pertama terdeteksi oleh bot |
| `status` | TEXT | NOT NULL | Status: `alerted`, `alerted_muted`, `rejected` |
| `rejection_reason` | TEXT | NULL | Alasan jika ditolak filter |

#### 2. Tabel `filter_config` (Single Row)
Menyimpan parameter filter yang dapat diubah dari Web UI secara real-time.

| Kolom | Tipe Data | Constraint | Keterangan |
|-------|-----------|------------|------------|
| `id` | INTEGER | PRIMARY KEY CHECK(id = 1) | Menjamin hanya 1 row konfigurasi aktif |
| `min_liquidity_usd` | REAL | DEFAULT 5000.0 | Minimal likuiditas ($) |
| `min_volume_5m_usd` | REAL | DEFAULT 1000.0 | Minimal volume 5 menit ($) |
| `max_age_minutes` | INTEGER | DEFAULT 60 | Umur maksimal pool (menit) |
| `min_buy_sell_ratio` | REAL | DEFAULT 1.2 | Rasio buy/sell transaksi |
| `require_lp_locked` | BOOLEAN | DEFAULT 1 | Wajib status LP locked/burned |
| `require_mint_renounced` | BOOLEAN | DEFAULT 1 | Wajib mint authority dimatikan |
| `blacklist_keywords` | TEXT | DEFAULT 'test,scam,airdrop,pump' | CSV kata kunci blacklist |
| `polling_interval_seconds`| INTEGER | DEFAULT 20 | Durasi siklus polling (detik) |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Waktu pembaruan terakhir |

#### 3. Tabel `mute_state` (Single Row)
Menyimpan state mute notifikasi Telegram.

| Kolom | Tipe Data | Constraint | Keterangan |
|-------|-----------|------------|------------|
| `id` | INTEGER | PRIMARY KEY CHECK(id = 1) | Menjamin 1 row state |
| `is_muted` | BOOLEAN | DEFAULT 0 | Status mute aktif (1: Mute, 0: Unmute) |
| `muted_at` | DATETIME | NULL | Waktu mute diaktifkan |
| `mute_until` | DATETIME | NULL | Waktu auto-unmute (`NULL` = manual) |
| `muted_by` | TEXT | DEFAULT 'system' | Pengaktif mute: 'telegram' / 'web_ui' |

---

### Index Strategy
- `tokens_seen.first_seen_at` — Index untuk sorting feed dan query log histori cepat.
- `tokens_seen.status` — Index untuk filtering query berdasarkan status alert di Web UI.

---

## 📄 BAGIAN 3: Interface Design

### 1. REST API Endpoints (FastAPI Backend)

| Method | Endpoint | Deskripsi | Request Body / Query | Response Model |
|--------|----------|-----------|----------------------|----------------|
| `GET` | `/api/status` | Status bot (worker, mute, total token hari ini) | - | `BotStatusResponse` |
| `GET` | `/api/config` | Mengambil konfigurasi filter aktif | - | `FilterConfigSchema` |
| `PUT` | `/api/config` | Memperbarui konfigurasi filter dari Web UI | `FilterConfigSchema` | `FilterConfigSchema` |
| `POST` | `/api/bot/mute` | Mengaktifkan mute dari Web UI | `{"duration_minutes": 30}` | `MuteStatusResponse` |
| `POST` | `/api/bot/unmute` | Mematikan mute dari Web UI | - | `MuteStatusResponse` |
| `POST` | `/api/bot/test-alert` | Mengirim pesan tes alert ke Telegram | - | `{"success": true, "message": "..."}` |
| `GET` | `/api/tokens` | Mengambil riwayat token | `?status=all&limit=50&offset=0` | `TokenListResponse` |

---

### 2. Telegram Bot Commands Interface

| Command | Parameter | Deskripsi | Contoh Penggunaan |
|---------|-----------|-----------|-------------------|
| `/start` | - | Inisialisasi bot & instruksi bantuan | `/start` |
| `/mute` | `[durasi]` (opsional) | Membisukan alert (durasi: 30m, 1h, 3h, atau permanen jika kosong) | `/mute 30m` atau `/mute` |
| `/unmute` | - | Mengaktifkan kembali pengiriman alert | `/unmute` |
| `/status` | - | Cek status operasional bot, status mute, dan sisa durasi | `/status` |
| `/history`| `[limit]` (opsional) | Menampilkan daftar koin yang lolos saat mute aktif | `/history 5` |
| `/config` | - | Menampilkan ringkasan konfigurasi filter aktif saat ini | `/config` |

---

## 📄 BAGIAN 4: Alur Logika & Business Rules

### Alur 1: Siklus Background Polling & Discovery

```
[Async Worker Loop (Tiap X Detik)]
          │
          ▼
[HTTP GET DexScreener: /latest/dex/tokens/ atau /pools/solana]
          │
          ▼
[Loop Setiap Token/Pair dalam Response]
          │
          ├──> [Cek `token_address` di SQLite `tokens_seen`]
          │           ├──> Ditemukan ──> Lewati (Skip)
          │           └──> Belum Ada ──> Lanjut Evaluasi
          ▼
[Evaluasi Filter Engine (Sesuai `filter_config`)]
  1. Umur Pool <= max_age_minutes?
  2. Likuiditas >= min_liquidity_usd?
  3. Volume 5m >= min_volume_5m_usd?
  4. Rasio Buy/Sell >= min_buy_sell_ratio?
  5. Nama/Simbol tidak mengandung kata di blacklist?
          │
          ├──> [Gagal salah satu] ──> Simpan ke DB (status: `rejected`, reason) ──> Skip
          └──> [Lolos semua] ──> Lanjut
          ▼
[Evaluasi Keamanan (GoPlus API / Mock Security)]
  - LP Locked == True?
  - Mint Renounced == True?
          │
          ├──> [Tidak Memenuhi] ──> Simpan DB (status: `rejected`, reason: 'security_failed')
          └──> [Memenuhi] ──> Lolos Kriteria Utama
          ▼
[Cek `mute_state` di SQLite]
          │
          ├──> [Sedang Mute (`is_muted == 1` & `now < mute_until`)]
          │           └──> Simpan ke DB (status: `alerted_muted`) (Tanpa kirim Telegram)
          │
          └──> [Tidak Mute (`is_muted == 0`)]
                      ├──> Format Template Pesan Telegram (HTML monospace contract)
                      ├──> Kirim via Telegram Bot API
                      └──> Simpan ke DB (status: `alerted`)
```

### Alur 2: Sinkronisasi Konfigurasi & Mute (Web UI <-> Bot)
1. User mengubah threshold atau menekan tombol Mute di Vue 3 Web UI.
2. Web UI mengirim `PUT /api/config` atau `POST /api/bot/mute` ke FastAPI.
3. Backend memvalidasi data schema dan memperbarui row di SQLite.
4. Background worker pada siklus polling berikutnya secara otomatis membaca konfigurasi terbaru dari SQLite tanpa memerlukan restart proses server.

### Business Rules
1. **Single Authorized User:** Backend hanya memproses perintah Telegram dari `TELEGRAM_CHAT_ID` yang terdaftar di `.env`. Pesan dari user lain langsung diabaikan.
2. **Persistence Zero-Loss:** Selama status mute aktif, token yang lolos filter tidak dibuang, melainkan disimpan dengan status `alerted_muted` agar dapat ditinjau via Web UI atau `/history`.
3. **Auto-Unmute Expiration:** Jika `mute_until` terlewati, worker otomatis menonaktifkan status mute dan mengirimkan 1 pesan Telegram notifikasi bahwa masa mute telah usai beserta ringkasan jumlah token.
4. **Rate Limit Throttling:** Request ke DexScreener dibatasi maksimal 1 request per 15 detik untuk menghindari IP ban / HTTP 429.

---

## 📄 BAGIAN 5: Keamanan, Performa, & Deployment

### Keamanan
- **Environment Isolation:** Variabel sensitif (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) disimpan di file `.env` di backend, bukan di source code atau frontend.
- **CORS Restricted:** FastAPI mengaktifkan CORS middleware khusus untuk origin lokal frontend (`http://localhost:5173`).
- **Input Validation:** Seluruh input form konfigurasi di-sanitize dan divalidasi oleh Pydantic Model sebelum ditulis ke SQLite.

### Performa
- **Asynchronous I/O:** Seluruh request HTTP external (DexScreener, GoPlus, Telegram API) menggunakan async client `httpx` agar tidak memblokir event loop FastAPI.
- **SQLite WAL Mode:** Database SQLite dikonfigurasi dengan `PRAGMA journal_mode=WAL;` dan `PRAGMA synchronous=NORMAL;` agar pembacaan dari Web UI dan penulisan dari worker berjalan bersamaan tanpa lock contention.
- **Client-side Debounce:** Filter & search pada tabel Web UI memanfaatkan computed properties dan reactive state Pinia untuk render instan.

### Development & Local Run Setup

#### 1. Backend Setup (FastAPI + Worker)
```bash
# Di folder backend/
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Isi TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID di .env

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup (Vue 3 + Vite)
```bash
# Di folder frontend/
npm install
npm run dev
# Akses Web UI di: http://localhost:5173
```

---

## 🔄 Finalisasi

1. **File Tech Spec Tersimpan:** `.agents/2-TECH-SPEC.md`
2. **Langkah Berikutnya:** Membuat daftar task implementasi atomik dan siap eksekusi dengan mengetik:
   `"Buat Task berdasarkan Tech Spec yang sudah dibuat"`

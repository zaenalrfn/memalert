# TASK LIST: Solana Memecoin Tracker & Alert Bot with Vue 3 Web UI

## 📋 Metadata
- **Nama Produk:** Solana Memecoin Tracker & Alert Bot
- **Versi:** 1.0 (MVP)
- **Lokasi Dokumen:** `.agents/3-TASKS.md`
- **Acuan Dokumen:** `.agents/2-TECH-SPEC.md` & `.agents/1-PRD.md`

---

## 📊 Ringkasan Task

| Modul | Total Task | Prioritas Utama |
|-------|------------|-----------------|
| **Modul 1: Setup & Core Infrastructure** | 3 Task | High |
| **Modul 2: Data Sources & Discovery Engine** | 3 Task | High |
| **Modul 3: Filter & Security Engine** | 2 Task | High |
| **Modul 4: Telegram Bot Service & Commands** | 4 Task | High |
| **Modul 5: Backend REST API (FastAPI)** | 3 Task | Mid |
| **Modul 6: Frontend Web UI (Vue 3 + Vite)** | 4 Task | Mid |
| **Modul 7: Integration, Scripts & Testing** | 2 Task | Mid |
| **Total** | **21 Task** | - |

---

## 📑 TASK BREAKDOWN

### Modul 1: Setup & Core Infrastructure

#### T-01: Inisialisasi Struktur Project & Environment Setup
- **ID:** T-01
- **Judul:** Inisialisasi struktur direktori backend & frontend beserta dependency configuration
- **Deskripsi:** Membuat folder project `backend/` dan `frontend/`, file `requirements.txt` (FastAPI, uvicorn, httpx, python-telegram-bot, pyyaml, pydantic-settings, aiosqlite), `.env.example`, dan inisialisasi Vite Vue 3 dengan Tailwind CSS.
- **Modul:** Setup & Infrastructure
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** -
- **File Terkait:** `backend/requirements.txt`, `backend/.env.example`, `frontend/package.json`, `frontend/tailwind.config.js`

#### T-02: Setup Database SQLite & Skema Migrasi
- **ID:** T-02
- **Judul:** Implementasi koneksi database SQLite dan pembuatan tabel
- **Deskripsi:** Membuat modul database manager (`backend/app/core/database.py`) untuk inisialisasi tabel `tokens_seen`, `filter_config`, dan `mute_state` secara otomatis dengan konfigurasi WAL mode.
- **Modul:** Setup & Infrastructure
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-01
- **File Terkait:** `backend/app/core/database.py`

#### T-03: Pydantic Schemas & Settings Loader
- **ID:** T-03
- **Judul:** Implementasi konfigurasi environment dan Pydantic models
- **Deskripsi:** Membaca setting environment dari `.env` dan `config.yaml`, mendefinisikan Pydantic schemas untuk token data, filter thresholds, dan mute status.
- **Modul:** Setup & Infrastructure
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-01
- **File Terkait:** `backend/app/core/config.py`, `backend/app/models/schemas.py`, `backend/config.yaml`

---

### Modul 2: Data Sources & Discovery Engine

#### T-04: Client HTTPX Async DexScreener API
- **ID:** T-04
- **Judul:** Implementasi client API DexScreener untuk fetch token terbaru di Solana
- **Deskripsi:** Membuat service async untuk mengambil daftar pair Solana terbaru dari endpoint publik DexScreener (`api.dexscreener.com`) dengan rate-limit guard dan parsing JSON data pool.
- **Modul:** Data Sources & Discovery
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-03
- **File Terkait:** `backend/app/services/dexscreener_client.py`

#### T-05: Client GoPlus Security API
- **ID:** T-05
- **Judul:** Implementasi client validasi keamanan token Solana via GoPlus API
- **Deskripsi:** Mengambil data keamanan on-chain dasar (apakah `mint_authority` renounced, status lock/burn LP, dan flag honeypot) secara gratis.
- **Modul:** Data Sources & Discovery
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-03
- **File Terkait:** `backend/app/services/goplus_client.py`

#### T-06: Deduplikasi Token & Persistence Caching
- **ID:** T-06
- **Judul:** Mekanisme cek deduplikasi token pada SQLite
- **Deskripsi:** Membuat service untuk memeriksa apakah alamat token Solana (`token_address`) sudah pernah diproses sebelumnya agar tidak diproses ulang.
- **Modul:** Data Sources & Discovery
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-02, T-04
- **File Terkait:** `backend/app/services/tracker_worker.py`

---

### Modul 3: Filter & Security Engine

#### T-07: Implementasi Core Filter Engine
- **ID:** T-07
- **Judul:** Validasi kriteria token terhadap konfigurasi aktif
- **Deskripsi:** Logika pengecekan parameter token: `min_liquidity_usd`, `min_volume_5m_usd`, `max_age_minutes`, `min_buy_sell_ratio`, dan penyaringan blacklist nama/simbol token.
- **Modul:** Filter & Security
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-03, T-04
- **File Terkait:** `backend/app/services/filter_engine.py`

#### T-08: Integrasi Evaluasi Keamanan & Logging Rejection
- **ID:** T-08
- **Judul:** Evaluasi akhir token lolos/ditolak dan pencatatan alasan penolakan
- **Deskripsi:** Menggabungkan hasil filter kriteria dengan security check; jika ditolak, simpan log ke DB dengan status `rejected` dan alasan spesifik.
- **Modul:** Filter & Security
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-05, T-07
- **File Terkait:** `backend/app/services/filter_engine.py`, `backend/app/services/tracker_worker.py`

---

### Modul 4: Telegram Bot Service & Commands

#### T-09: Telegram Alert Dispatcher & Formatting
- **ID:** T-09
- **Judul:** Format pesan alert HTML/Markdown dan pengiriman ke Telegram
- **Deskripsi:** Membuat formatter pesan alert berisi Nama, Simbol, Contract Address (1-tap copy), Likuiditas, Volume 5m, Pool Age, link DexScreener, dan shortcut info `/mute`.
- **Modul:** Telegram Bot Service
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-03
- **File Terkait:** `backend/app/services/telegram_service.py`

#### T-10: Telegram Command Handlers (`/start`, `/status`, `/config`)
- **ID:** T-10
- **Judul:** Implementasi command dasar bot Telegram dengan verifikasi Single Chat ID
- **Deskripsi:** Menangani perintah `/start`, `/status` (status bot, jumlah token terpantau, state mute), dan `/config` (tampilkan threshold aktif saat ini). Mengabaikan pesan dari chat_id yang tidak berhak.
- **Modul:** Telegram Bot Service
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-09
- **File Terkait:** `backend/app/services/telegram_service.py`

#### T-11: Telegram Mute/Unmute Commands (`/mute`, `/unmute`)
- **ID:** T-11
- **Judul:** Implementasi manajemen mute Telegram dengan durasi dinamis
- **Deskripsi:** Parser input durasi (misal `/mute 30m`, `/mute 1h`, `/mute`), update row `mute_state` di SQLite, dan handler `/unmute` untuk langsung membuka kembali notifikasi.
- **Modul:** Telegram Bot Service
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-02, T-10
- **File Terkait:** `backend/app/services/telegram_service.py`

#### T-12: Auto-Unmute Worker & Command `/history`
- **ID:** T-12
- **Judul:** Background checker auto-unmute dan command `/history`
- **Deskripsi:** Worker memeriksa masa berlaku mute; jika habis, otomatis mengirim pesan rekap ke Telegram. Command `/history` menampilkan token yang lolos saat sesi mute terakhir.
- **Modul:** Telegram Bot Service
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-11
- **File Terkait:** `backend/app/services/telegram_service.py`, `backend/app/services/tracker_worker.py`

---

### Modul 5: Backend REST API (FastAPI)

#### T-13: API Endpoints Config Management
- **ID:** T-13
- **Judul:** Endpoint `GET /api/config` dan `PUT /api/config`
- **Deskripsi:** API untuk membaca threshold aktif dari SQLite dan memperbarui konfigurasi filter secara live dari Web UI tanpa perlu restart bot.
- **Modul:** Backend REST API
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-02, T-03
- **File Terkait:** `backend/app/api/routes_config.py`

#### T-14: API Endpoints Bot Control & Status
- **ID:** T-14
- **Judul:** Endpoint `GET /api/status`, `POST /api/bot/mute`, `POST /api/bot/unmute`, dan `POST /api/bot/test-alert`
- **Deskripsi:** API untuk status bot, toggle mute via web UI, serta tombol trigger test notifikasi alert ke Telegram.
- **Modul:** Backend REST API
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-02, T-09, T-11
- **File Terkait:** `backend/app/api/routes_bot.py`

#### T-15: API Endpoints Token History & Live Feed
- **ID:** T-15
- **Judul:** Endpoint `GET /api/tokens` dengan query filter & pagination
- **Deskripsi:** API untuk menyajikan riwayat koin yang ditemukan (`alerted`, `alerted_muted`, `rejected`) untuk ditampilkan pada tabel di Web UI.
- **Modul:** Backend REST API
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-02
- **File Terkait:** `backend/app/api/routes_tokens.py`

---

### Modul 6: Frontend Web UI (Vue 3 + Vite)

#### T-16: Setup Pinia Stores & API Client
- **ID:** T-16
- **Judul:** Konfigurasi HTTP client Axios dan Pinia Store
- **Deskripsi:** Membuat instance Axios dengan base URL backend, serta Pinia stores (`configStore.js`, `tokenStore.js`) untuk manajemen state reaktif.
- **Modul:** Frontend Web UI
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-01, T-13, T-14, T-15
- **File Terkait:** `frontend/src/services/api.js`, `frontend/src/stores/configStore.js`, `frontend/src/stores/tokenStore.js`

#### T-17: Komponen Dashboard Stats & Mute Control
- **ID:** T-17
- **Judul:** Implementasi kartu statistik metrik dan panel kontrol mute
- **Deskripsi:** Menampilkan indikator status worker, toggle switch mute/unmute, selector durasi mute, dan tombol test alert Telegram.
- **Modul:** Frontend Web UI
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-16
- **File Terkait:** `frontend/src/components/StatsCard.vue`, `frontend/src/components/MuteControl.vue`

#### T-18: Komponen Form Filter Settings
- **ID:** T-18
- **Judul:** Form pengaturan threshold filter kustom
- **Deskripsi:** Input form untuk minimum likuiditas, volume 5m, max pool age, buy/sell ratio, checkbox keamanan LP/mint, dan blacklist keyword dengan tombol simpan reaktif.
- **Modul:** Frontend Web UI
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-16
- **File Terkait:** `frontend/src/components/FilterSettings.vue`

#### T-19: Komponen Tabel Feed & Histori Token
- **ID:** T-19
- **Judul:** Tabel live monitoring koin dengan status badge dan copy button
- **Deskripsi:** Tabel responsif menampilkan token yang terdeteksi, badge status (`alerted`, `muted`, `rejected`), copyable address, dan link langsung ke DexScreener.
- **Modul:** Frontend Web UI
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-16
- **File Terkait:** `frontend/src/components/TokenTable.vue`, `frontend/src/App.vue`

---

### Modul 7: Integration, Scripts & Testing

#### T-20: Lifespan Background Poller & Telegram Bot Initialization
- **ID:** T-20
- **Judul:** Integrasi background worker ke FastAPI Lifespan startup
- **Deskripsi:** Menghubungkan asyncio task loop background poller dan telegram bot listener agar berjalan serentak saat `uvicorn app.main:app` dijalankan.
- **Modul:** Integration & Run
- **Prioritas:** High
- **Status:** Done
- **Dependensi:** T-04, T-07, T-09, T-13
- **File Terkait:** `backend/app/main.py`

#### T-21: Runner Scripts & End-to-End Verification
- **ID:** T-21
- **Judul:** Pembuatan script runner Windows (`run_backend.bat`, `run_frontend.bat`) dan pengujian alur
- **Deskripsi:** Menyediakan script one-click run untuk backend dan frontend, pengujian trigger polling DexScreener, verifikasi filter, tes kirim alert Telegram, dan verifikasi Web UI.
- **Modul:** Integration & Run
- **Prioritas:** Mid
- **Status:** Done
- **Dependensi:** T-20, T-19
- **File Terkait:** `run_backend.bat`, `run_frontend.bat`, `README.md`

---

## 🔄 Finalisasi

1. **File Task List Tersimpan:** `.agents/3-TASKS.md`
2. **Langkah Berikutnya:** Memulai eksekusi implementasi per task atau menyeluruh dengan mengetik:
   `"Kerjakan task"` atau `"Lanjutkan implementasi"`

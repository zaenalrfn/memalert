# Engine Config: Rekomendasi Parameter Screening Memecoin (Solana)

**Tujuan dokumen:** Referensi konfigurasi filter engine untuk Memecoin Tracker & Alert Bot. Dipakai sebagai starting point sebelum tuning berdasarkan data histori nyata.

**Terakhir diupdate:** 9 September 2026

---

## 1. Tiga Profil Konfigurasi

### 1.1 Conservative (Safe Mode)

Fokus tangkap token yang sudah menunjukkan traksi nyata dan liquidity lebih tebal. Alert lebih jarang tapi risiko rug instan lebih rendah.

```yaml
filters:
  profile: conservative
  min_liquidity_usd: 15000        # range 15000 - 20000
  min_volume_5m_usd: 3000         # range 3000 - 5000
  max_pool_age_minutes: 120       # 2 jam
  min_buy_sell_ratio: 1.5         # jauh lebih banyak buy daripada sell
  poll_interval_seconds: 30
```

### 1.2 Balanced (Direkomendasikan untuk Mulai)

Titik tengah antara kecepatan deteksi dan kualitas sinyal. Cocok dipakai sebagai baseline awal sebelum tuning berdasarkan data histori.

```yaml
filters:
  profile: balanced
  min_liquidity_usd: 5000         # range 5000 - 8000
  min_volume_5m_usd: 1000         # range 1000 - 1500
  max_pool_age_minutes: 60        # 1 jam
  min_buy_sell_ratio: 1.2
  poll_interval_seconds: 15       # range 15 - 20
```

### 1.3 Aggressive (Early Degen Mode)

Kejar token yang baru banget muncul, termasuk yang masih di fase bonding curve. Alert jauh lebih sering, mayoritas akan noise/rug — **wajib dikombinasikan dengan security check aktif**.

```yaml
filters:
  profile: aggressive
  min_liquidity_usd: 1000         # range 1000 - 2000
  min_volume_5m_usd: 200          # range 200 - 500
  max_pool_age_minutes: 15
  min_buy_sell_ratio: 1.0         # netral, tidak terlalu ketat
  poll_interval_seconds: 10       # hati-hati rate limit DexScreener API
```

---

## 2. Tabel Ringkas Perbandingan

| Parameter | Conservative | Balanced | Aggressive |
|---|---|---|---|
| Min Liquidity (USD) | 15,000 – 20,000 | 5,000 – 8,000 | 1,000 – 2,000 |
| Min Vol 5m (USD) | 3,000 – 5,000 | 1,000 – 1,500 | 200 – 500 |
| Max Pool Age (menit) | 120 | 60 | 15 |
| Min Buy/Sell Ratio | 1.5 | 1.2 | 1.0 |
| Poll Interval (detik) | 30 | 15 – 20 | 10 |
| Frekuensi alert | Jarang | Sedang | Sering |
| Kebutuhan security check | Opsional | Direkomendasikan | Wajib |

---

## 3. Alasan / Rationale Tiap Parameter

### 3.1 Min Liquidity (USD)
- Ambang **$10,000 ke bawah** umumnya dianggap "extremely thin liquidity" — slippage akan sangat besar.
- Profil **Balanced** ($5-8K) sengaja diset sedikit di bawah ambang itu supaya tidak kelewatan token yang masih di fase awal graduasi dari bonding curve, tapi tetap butuh validasi tambahan dari security check.
- Profil **Conservative** ($15-20K) memberi buffer aman jauh di atas ambang thin liquidity.

### 3.2 Min Volume 5m (USD)
- Indikator momentum jangka pendek. Rasio ideal terhadap liquidity: volume 5 menit yang jauh melebihi liquidity total (tanpa kenaikan liquidity yang sepadan) justru bisa jadi sinyal **wash trading** — lihat bagian 4 untuk cross-check ini.

### 3.3 Max Pool Age (Menit)
- Selaras dengan target latency deteksi <2 menit yang ditetapkan di PRD.
- **60 menit** di profil Balanced adalah kompromi: cukup ketat untuk menyaring token yang benar-benar baru, tidak terlalu ketat sampai bot ter-trigger di detik-detik pertama yang paling volatil (rawan sniping).

### 3.4 Min Buy/Sell Ratio
- Rasio > 1.0 berarti tekanan beli lebih dominan daripada jual dalam window waktu yang diobservasi.
- **1.2 - 1.5** adalah rentang wajar untuk menandakan momentum positif tanpa terlalu ketat sampai hanya menangkap token yang sudah sangat parabolic (telat masuk).

### 3.5 Poll Interval (Detik)
- DexScreener API punya rate limit ~300 request/menit untuk endpoint pair/token/search, dan ~60 request/menit untuk endpoint profile/boost/ads.
- Interval **15-20 detik** (Balanced) jauh di bawah batas rate limit, aman untuk single-chain (Solana) monitoring.
- Interval **10 detik** (Aggressive) mendekati batas dan berisiko kena limit kalau ada banyak endpoint lain yang dipanggil bersamaan (misal security check API) — perlu implementasi backoff/retry.

---

## 4. Rekomendasi Arsitektur Filter Bertahap

Config di atas sebaiknya diposisikan sebagai **filter tahap 1** (murah secara komputasi, dijalankan di setiap polling). Token yang lolos tahap 1 baru dilanjutkan ke **tahap 2** (scoring lebih berat):

```
[Tahap 1: Engine Config Filter]
   Liquidity, Volume 5m, Pool Age, Buy/Sell Ratio
        │
        ▼ Lolos
[Tahap 2: Security Check]
   Mint authority, Freeze authority, LP lock status
   (lihat REFERENSI_Memecoin_Mechanics_dan_SPK.md bagian 3.3 — Safety Score)
        │
        ▼ Lolos
[Tahap 3: SPK Scoring]
   SAW / AHP-TOPSIS composite score
   (lihat REFERENSI_Memecoin_Mechanics_dan_SPK.md bagian 4)
        │
        ▼
[Kirim Alert]
```

> Pemisahan tahap ini penting untuk efisiensi: filter murah (liquidity/volume/age) dijalankan duluan untuk membuang mayoritas noise dengan cepat, baru token yang benar-benar kandidat masuk ke pengecekan yang lebih berat (API eksternal untuk security check).

---

## 5. Catatan Tuning

- Semua angka di atas adalah **starting point**, bukan formula final. Jalankan bot minimal beberapa hari di profil **Balanced**, catat hasilnya ke SQLite (`status: alerted` vs token yang ternyata rug), lalu evaluasi:
  - Kalau terlalu banyak alert yang berujung rug → naikkan `min_liquidity_usd` dan `min_buy_sell_ratio`, geser ke arah Conservative.
  - Kalau terlalu sedikit alert / kelewatan token yang ternyata bagus → turunkan threshold, geser ke arah Aggressive, tapi pastikan security check tahap 2 aktif.
- Threshold ideal juga bisa berubah mengikuti kondisi market Solana secara umum (bull run vs sepi) — pertimbangkan review berkala (misal mingguan).

---

## 6. Disclaimer

⚠️ Konfigurasi ini adalah alat bantu penyaringan noise berdasarkan data on-chain kuantitatif, **bukan jaminan** token yang lolos filter akan profit atau aman dari rugpull. Selalu kombinasikan dengan Safety Score dan SPK Scoring dari dokumen `REFERENSI_Memecoin_Mechanics_dan_SPK.md` sebelum menganggap sebuah alert sebagai kandidat yang layak dipertimbangkan lebih lanjut.

# Referensi Teknis: Mekanisme Memecoin, Perhitungan PnL, Deteksi Rugpull, dan Rumus SPK

**Tujuan dokumen:** Referensi teknis untuk agent/bot yang membangun fitur filter, scoring, dan alert pada Memecoin Tracker & Alert Bot (fokus Solana).

**Terakhir diupdate:** 9 September 2026

---

## 1. Cara Kerja Memecoin (Bonding Curve Mechanics)

### 1.1 Definisi

Kebanyakan memecoin di Solana (termasuk yang diluncurkan lewat platform seperti pump.fun) menggunakan mekanisme **bonding curve**: formula matematis dalam smart contract yang menentukan harga token berdasarkan jumlah supply yang sudah terjual. Harga naik saat orang beli, turun saat orang jual — tanpa perlu order book atau liquidity pool tradisional di awal.

### 1.2 Prinsip Kerja

- **Reserve dipegang kontrak**: Tidak ada counterparty. SOL yang dikirim pembeli tersimpan langsung di dalam smart contract, dan tersedia untuk ditarik penjual saat mereka jual balik ke kontrak.
- **Liquidity instan tapi tipis**: Karena harga adalah fungsi dari cumulative supply yang terjual, bahkan sell order berukuran sedang bisa mendorong harga turun signifikan. Kontrak menjamin kamu *bisa* jual, tapi tidak menjamin *harga* saat kamu jual akan mirip dengan harga saat kamu beli.
- **Fase graduasi**: Di pump.fun, token "graduate" sekitar market cap $69K. Saat graduate: SOL yang terkumpul di bonding curve dipasangkan dengan sisa supply token, lalu dimasukkan ke Raydium Liquidity Pool dan LP token-nya di-burn. Token menjadi SPL token standar yang bisa diperdagangkan bebas di DEX.
- **Titik kritis**: Momen graduasi sering jadi titik di mana "volume nyata" mulai terjadi — **atau** justru titik di mana dump besar terjadi karena training-wheels liquidity dari bonding curve sudah hilang dan liquidity di DEX pool masih tipis.

### 1.3 Implikasi untuk Filter Bot

| Fase Token | Karakteristik Risiko |
|---|---|
| Masih di bonding curve (pre-graduation) | Liquidity dijamin kontrak tapi sangat sensitif terhadap slippage; harga sangat volatil di early stage |
| Baru graduate (transisi ke DEX pool) | Liquidity pool baru terbentuk, rawan sniper & dump karena depth masih tipis |
| Sudah stabil di DEX | Liquidity lebih dalam, tapi tetap perlu cek lock/burn status |

> **Rekomendasi**: Tambahkan field `graduation_status` (pre/post) sebagai salah satu dimensi filter, karena profil risiko dua fase ini berbeda signifikan.

---

## 2. Rumus Perhitungan Profit/Loss (PnL)

### 2.1 PnL Dasar (Single Entry)

```
Jumlah Token Dibeli   = Modal (USD) / Harga Beli per Token
Nilai Sekarang        = Jumlah Token × Harga Sekarang
PnL (USD)             = Nilai Sekarang − Modal
PnL (%)               = (Harga Sekarang − Harga Beli) / Harga Beli × 100%
```

### 2.2 Harga Beli Rata-Rata (Multiple Entry / DCA)

```
Harga Beli Rata-rata = Total Modal Dikeluarkan / Total Token Dibeli
```

### 2.3 PnL Net (Memperhitungkan Slippage & Fee)

Penting untuk memecoin karena slippage di bonding curve/liquidity tipis bisa signifikan:

```
Modal Efektif = Modal × (1 + slippage% + fee%)
PnL Net       = (Jumlah Token × Harga Sekarang) − Modal Efektif
```

### 2.4 Realized vs Unrealized PnL

Berguna untuk dashboard/tracking posisi:

```
Realized PnL   = Σ (Harga Jual − Harga Beli) × Jumlah Token yang Sudah Dijual
Unrealized PnL = (Harga Sekarang − Harga Beli) × Jumlah Token yang Masih Dipegang
Total PnL      = Realized PnL + Unrealized PnL
```

---

## 3. Indikator Rugpull & Cara Deteksi

### 3.1 Tabel Red Flag Utama

| Indikator | Kenapa Berbahaya | Sumber Data |
|---|---|---|
| **Mint authority masih aktif** | Creator bisa mencetak token tanpa batas kapan saja, mendilusi nilai holder yang ada | RugCheck, Solscan, GoPlus Security API |
| **Freeze authority masih aktif** | Creator bisa membekukan wallet siapa saja, mencegah transfer/jual — menjebak investor | RugCheck, Solscan |
| **Liquidity tidak di-lock/burn** | Developer bisa menarik liquidity kapan saja, membuat token instan tidak bernilai. Lock < 30 hari mencurigakan; proyek legit biasanya lock 6–12 bulan minimum | DexScreener, Team Finance, Unicrypt, PinkSale |
| **Holder concentration tinggi** | Satu wallet menguasai >50% supply = risiko konsentrasi ekstrem. **Catatan**: scammer sering memecah token ke puluhan wallet (masing-masing <1%) yang didanai dari sumber yang sama — perlu cross-check funding source, bukan cuma persentase per wallet | Solscan, Bubblemaps |
| **Liquidity sangat tipis** | Liquidity < $10.000 berarti slippage akan sangat besar | DexScreener |
| **Hidden function di kontrak** | Waspadai fungsi seperti `setFee`, `blacklist`, `pause`, `mint`, `excludeFromFee` | Kode kontrak (verified source), Token Sniffer |
| **Volume tidak wajar** | Lonjakan volume tanpa kenaikan liquidity sepadan = indikasi wash trading | DexScreener (bandingkan volume vs liquidity) |
| **Dev wallet activity mencurigakan** | Transfer besar dari wallet developer/creator = early warning sebelum rug | On-chain monitoring (webhook Helius/Moralis) |

### 3.2 Catatan Penting

- Audit smart contract **bukan jaminan** — audit bisa melewatkan perubahan kode belakangan, punya scope review yang sempit, atau mengabaikan risiko dari konsentrasi holder (bukan dari kode itu sendiri).
- Liquidity lock **bukan jaminan mutlak** — beberapa scammer memakai lock period pendek (7–14 hari) dan langsung rug begitu lock berakhir. Selalu cek **durasi** lock, bukan cuma status "locked: true/false".
- Tools otomatis (RugCheck, Token Sniffer, Honeypot.is, GoPlus) sebaiknya dipakai sebagai **filter awal**, bukan vonis akhir.

### 3.3 Formula Safety Score Komposit (0–100)

```
Safety Score =
    (25 jika mint_authority == renounced, else 0)
  + (25 jika freeze_authority == renounced, else 0)
  + (25 jika lp_locked_or_burned == true, else 0)
  + (25 × (1 − top_holder_percentage))
```

**Contoh implementasi (pseudocode):**

```python
def calculate_safety_score(token_data):
    score = 0
    score += 25 if token_data["mint_authority"] == "renounced" else 0
    score += 25 if token_data["freeze_authority"] == "renounced" else 0
    score += 25 if token_data["lp_locked_or_burned"] else 0
    score += 25 * (1 - token_data["top_holder_pct"])  # top_holder_pct dalam desimal, misal 0.35
    return round(score, 2)
```

> Pola ini mengikuti pendekatan yang dipakai tools sejenis (mis. StakePoint) yang memverifikasi mint authority, freeze authority, status LP lock, dan konsentrasi top holder untuk menghasilkan skor keamanan 0–100.

---

## 4. Rumus SPK (Sistem Pendukung Keputusan) untuk Skoring "Token Terpercaya & Berpotensi Pump"

### 4.1 Opsi A — SAW (Simple Additive Weighting)

**Paling direkomendasikan untuk MVP** karena ringan secara komputasi, cocok dijalankan setiap kali polling token baru.

**Langkah 1 — Normalisasi kriteria** (skala 0–1):

Untuk kriteria **benefit** (makin besar makin baik — misal liquidity, volume, holder count):
```
r_ij = x_ij / max(x_j)
```

Untuk kriteria **cost** (makin kecil makin baik — misal top holder %, umur token dalam menit jika ingin prioritas token sangat baru):
```
r_ij = min(x_j) / x_ij
```

**Langkah 2 — Tentukan bobot kriteria** (total harus = 1):

| Kriteria | Tipe | Bobot Contoh |
|---|---|---|
| Liquidity USD | Benefit | 0.20 |
| Volume 5 menit | Benefit | 0.15 |
| Buy/Sell ratio | Benefit | 0.15 |
| Holder count | Benefit | 0.10 |
| Safety Score (dari bagian 3.3) | Benefit | 0.30 |
| Top holder concentration % | Cost | 0.10 |

**Langkah 3 — Hitung skor akhir:**
```
V_i = Σ (w_j × r_ij)
```

Token dengan `V_i` tertinggi = paling "layak dipercaya + berpotensi" menurut kriteria yang ditentukan.

**Pseudocode implementasi:**

```python
def saw_score(token, all_tokens, weights):
    """
    token: dict kriteria token yang dinilai
    all_tokens: list semua token kandidat (untuk cari max/min tiap kriteria)
    weights: dict bobot tiap kriteria, contoh:
        {
            "liquidity_usd": 0.20,
            "volume_5m": 0.15,
            "buy_sell_ratio": 0.15,
            "holder_count": 0.10,
            "safety_score": 0.30,
            "top_holder_pct": 0.10,  # cost criteria
        }
    """
    benefit_criteria = ["liquidity_usd", "volume_5m", "buy_sell_ratio", "holder_count", "safety_score"]
    cost_criteria = ["top_holder_pct"]

    score = 0
    for key in benefit_criteria:
        max_val = max(t[key] for t in all_tokens) or 1  # hindari divide by zero
        r_ij = token[key] / max_val
        score += weights[key] * r_ij

    for key in cost_criteria:
        min_val = min(t[key] for t in all_tokens) or 0.0001
        r_ij = min_val / token[key] if token[key] > 0 else 0
        score += weights[key] * r_ij

    return round(score, 4)
```

### 4.2 Opsi B — AHP + TOPSIS (Lebih Rigorous)

Cocok kalau ingin bobot kriteria ditentukan lebih objektif (bukan tebakan manual), dan siap dengan kompleksitas komputasi lebih tinggi.

**AHP** dipakai untuk menentukan bobot kriteria lewat perbandingan berpasangan (pairwise comparison) antar kriteria, lengkap dengan uji konsistensi rasio.

**TOPSIS** dipakai untuk meranking alternatif berdasarkan jarak ke solusi ideal:

```
1. Normalisasi matriks keputusan
2. Kalikan dengan bobot → matriks ternormalisasi terbobot
3. Tentukan solusi ideal positif (A+) dan solusi ideal negatif (A−)
4. Hitung jarak Euclidean tiap alternatif ke A+ dan A−:
   D_i(+) = sqrt( Σ (v_ij − A+_j)^2 )
   D_i(−) = sqrt( Σ (v_ij − A−_j)^2 )
5. Hitung skor preferensi:
   C_i = D_i(−) / (D_i(+) + D_i(−))
```

Token dengan `C_i` mendekati 1 = paling dekat ke kondisi ideal.

> Pendekatan hybrid AHP-TOPSIS ini pernah diterapkan untuk SPK rekomendasi investasi saham berbasis Python + Streamlit — pola arsitektur yang sama bisa diadaptasi untuk memecoin, dan selaras dengan opsi dashboard Streamlit di roadmap v2 proyek ini.

### 4.3 Perbandingan SAW vs AHP-TOPSIS

| Aspek | SAW | AHP-TOPSIS |
|---|---|---|
| Kompleksitas implementasi | Rendah | Sedang–Tinggi |
| Kebutuhan komputasi | Ringan, cocok real-time per polling | Lebih berat, cocok untuk batch/dashboard |
| Objektivitas bobot | Manual (ditentukan sendiri) | Lebih sistematis lewat pairwise comparison |
| Rekomendasi tahap | **MVP / v1** | v2, terutama kalau nanti pindah ke dashboard Streamlit |

---

## 5. Disclaimer

⚠️ Skor SPK setinggi apa pun (SAW maupun AHP-TOPSIS) **bukan jaminan** token akan pump atau aman dari rugpull. Ini murni alat bantu menyaring noise berdasarkan data on-chain yang terukur secara kuantitatif. Bahkan audit smart contract bisa melewatkan risiko yang tidak berasal dari kode itu sendiri (misalnya konsentrasi holder atau perilaku dev wallet).

Memecoin tetap merupakan aset yang **sangat spekulatif dan berisiko tinggi**. Skor dan filter dalam dokumen ini harus diperlakukan sebagai **filter awal untuk mengurangi noise**, bukan sebagai sinyal beli/jual atau nasihat keuangan.

---

## 6. Referensi Sumber

- crypto.news — "What is a bonding curve? Memecoin pricing explained"
- crypto.news — "How meme coins are made: bonding curves, Pump.fun, and the math behind rug pulls"
- flashift.app — "Pump.fun Bonding Curve Mechanics Explained (2026 Mathematical Guide)"
- dextools.io — "How to Spot a Rug Pull: 2026 Checklist (Top Red Flags)"
- cryptoslate.com — "What Is a Rug Pull in Crypto? Liquidity Traps, Honeypots and Exit Scams Explained"
- flintr.io — "Anatomy of a rug pull: identify Scams on Pump.fun"
- createmycoin.app — "Solana Rug Checker: How to Detect Rug Pulls Before Investing"
- stakepoint.app — "Solana Rug Pull Checker: Scan Any Token in 5 Seconds Before You Buy"
- Jurnal KNSI 2018 — "Analisa Perbandingan Metode SAW, WP dan TOPSIS Menggunakan Hamming Distance"
- Nusantara Journal of Computers and Its Applications (NJCA) — "Implementasi Metode Hybrid AHP-TOPSIS pada Sistem Pendukung Keputusan Investasi Saham IDX30 Berbasis Streamlit"
- Journal of Informatics Management and Information Technology — SPK Weighted Product untuk rekomendasi investasi cryptocurrency

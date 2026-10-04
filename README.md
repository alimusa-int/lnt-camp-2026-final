# LnT Camp 2026 — Final Project

*Bridging the Gap: Empowering Future Talent through Machine Learning for Industry Innovation*

## Team

- Muhamad Atallah Alimusa (Team Leader)
- Muhammad Fahry Fauzi

## Project Overview

Decision Support System untuk manajer ritel yang mengevaluasi keranjang pelanggan di level order. Sistem memproyeksikan estimasi omzet (`Sales`) dan berperan sebagai *early warning* yang menandai order berpotensi rugi **sebelum** diproses.

## Chosen Modelling Tasks

- [x] Regression — predicting `Sales` (estimasi omzet order)
- [x] Classification — predicting `Profitability Status` (Untung vs. Rugi, dengan rekomendasi 3-tier Safe / Review / High Risk)
- [ ] Clustering — tidak dikerjakan

## Arsitektur

```
Frontend (Streamlit)  --HTTP/JSON-->  Backend (FastAPI)  --load-->  model/*.pkl
 form + tampilan hasil                 /predict/classification
                                       /predict/regression
                                       /health
```

Frontend tidak memuat model. Seluruh prediksi dilakukan oleh Backend API, yang memuat model dari folder `model/` saat startup (tanpa retraining).

## Folder Structure

```
notebook/   Jupyter notebook (EDA, preprocessing, modelling) + superstore.sqlite (data)
model/      Model terlatih (.pkl) dan daftar kolom fitur
backend/    REST API (FastAPI): main.py + requirements.txt
frontend/   Aplikasi Streamlit: app.py + requirements.txt
Dockerfile   Image backend untuk Hugging Face Spaces
hf_space/    README (metadata Space) + deploy.sh untuk push backend ke HF
```

## Dataset

Global Superstore ([sumber asli di Kaggle](https://www.kaggle.com/datasets/fatihilhan/global-superstore-dataset)), direstrukturisasi menjadi database SQLite ternormalisasi: `notebook/superstore.sqlite` (±11 MB, ikut di repo agar notebook dapat dijalankan ulang). Jika file hilang, unduh dari [Google Drive](https://drive.google.com/file/d/1M2sonY7serOCzWYDCKEdxZ5fJ7quOoKd/view) dan letakkan di folder `notebook/`. Skema:

| Tabel | Isi |
|---|---|
| `orders` | Header order: tanggal, moda kirim, prioritas, pelanggan, lokasi |
| `order_items` | Metrik per baris produk: sales, profit, diskon, kuantitas, ongkos kirim |
| `dim_customers` | Identitas dan segmen pelanggan |
| `dim_products` | Nama, kategori, sub-kategori produk (satu baris per `product_id`) |
| `dim_locations` | Kota, negara, region, market |
| `dim_product_name_variants` | Tabel pendukung hasil pembersihan: semua nama produk mentah per `product_id` (457 dari 10.292 ID punya >1 nama). Tidak dipakai dalam pemodelan |

Notebook mengagregasi `order_items` ke level order (25.753 order).

## Fitur Model

Semua fitur adalah informasi yang tersedia saat keranjang disusun (sebelum order diproses). 10 kolom fitur:

- `discount` (diskon tertinggi dalam keranjang), `shipping_cost`, `quantity`
- `n_items`, `share_furniture`, `share_technology` (komposisi keranjang)
- `ship_mode` (one-hot, 4 kolom)

Sengaja **tidak** dipakai: `delivery_duration` (leakage), `profit`/`profit_margin` (turunan target), `discount_tier` (duplikasi `discount`, tidak menambah performa pada uji CV), `segment` (win rate hampir sama di semua segmen).

## Hasil Model

| Model | Data uji (80/20) | 5-fold CV |
|---|---|---|
| Klasifikasi (Random Forest) | ROC-AUC 0,961; akurasi 0,914; recall kelas Rugi 0,85 | AUC 0,962 ± 0,003 |
| Regresi (Random Forest) | R² 0,765; MAE $158 | R² 0,735 ± 0,046 |

Catatan: R² regresi turun ke ±0,38 bila `shipping_cost` dikeluarkan (ablation di notebook, Bagian 6), jadi model sangat bergantung pada ongkos kirim.

## Ambang Rekomendasi (Custom Threshold 3-Tier)

Sistem tidak memakai ambang default 0,5, karena order rugi yang lolos (false negative) lebih mahal daripada peringatan palsu. Rekomendasi didasarkan pada probabilitas untung P:

| P(untung) | Rekomendasi | Order rugi aktual (data uji) |
|---|---|---|
| ≥ 70% | Safe to Process | ±3% (3.248 order) |
| 50% – 69,9% | Review Manual | ±22% (507 order) |
| < 50% | High Risk | ±83% (1.396 order) |

Bila order dengan P < 70% diberi perhatian (High Risk + Review), recall kelas Rugi naik dari ±0,85 (ambang 0,5) menjadi ±0,93, dengan biaya ±17% order untung ikut ditinjau (vs ±6% pada ambang 0,5). Batas 50% dan 70% ditetapkan berdasarkan judgement bisnis dan belum dioptimalkan secara formal. Analisis lengkap ada di notebook, Bagian 5. Logika zona ini ada di backend (`backend/main.py`).

## Setup & Run

Butuh Python 3.11+. Jalankan semua perintah dari **root repo**.

### 1. Backend API

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Backend berjalan di `http://localhost:8000`. Dokumentasi interaktif (Swagger) otomatis tersedia di `http://localhost:8000/docs`.

### 2. Frontend

Di terminal lain:

```bash
pip install -r frontend/requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run frontend/app.py
```

(Di Windows PowerShell: `$env:BACKEND_URL="http://localhost:8000"; streamlit run frontend/app.py`.) Bila `BACKEND_URL` tidak diatur, frontend memakai `http://localhost:8000`. Untuk deployment, isi `BACKEND_URL` lewat Streamlit secrets (lihat contoh di `frontend/.streamlit/secrets.toml.example`).

Frontend punya dua halaman simulasi: **Klasifikasi: Risiko Profit** dan **Regresi: Estimasi Sales**.

### 3. Notebook

```bash
pip install -r requirements.txt
pip install notebook
```

Buka `notebook/final_project.ipynb` di Jupyter, VS Code, atau Colab. Menjalankan seluruh notebook melatih ulang model dan menimpa file di `model/`.

Versi `scikit-learn` dikunci (1.8.0) karena file `.pkl` sensitif terhadap versi library. Model di folder `model/` dilatih dengan versi yang sama.

## Dokumentasi Endpoint

Base URL lokal: `http://localhost:8000`

| Method | Path | Fungsi |
|---|---|---|
| GET | `/health` | Memastikan layanan dan model sudah termuat |
| POST | `/predict/classification` | Probabilitas untung dan rekomendasi 3-tier |
| POST | `/predict/regression` | Estimasi omzet (`Sales`) |

### Input (sama untuk kedua endpoint prediksi)

| Field | Tipe | Batas | Keterangan |
|---|---|---|---|
| `ship_mode` | string | `Standard Class`, `Second Class`, `First Class`, `Same Day` | Moda pengiriman |
| `quantity` | integer | 1 – 60 | Total kuantitas seluruh keranjang |
| `discount` | float | 0.0 – 0.85 | Diskon tertinggi dalam keranjang (0.1 = 10%) |
| `shipping_cost` | float | 0 – 2100 | Ongkos kirim (USD) |
| `n_furniture` | integer | 0 – 14 | Jumlah baris produk Furniture |
| `n_office` | integer | 0 – 14 | Jumlah baris produk Office Supplies |
| `n_tech` | integer | 0 – 14 | Jumlah baris produk Technology |

Validasi tambahan: keranjang tidak boleh kosong (`n_furniture + n_office + n_tech` ≥ 1) dan `quantity` tidak boleh lebih kecil dari jumlah baris produk. Input yang tidak valid mengembalikan HTTP `422`.

### `POST /predict/classification`

```bash
curl -X POST http://localhost:8000/predict/classification \
  -H "Content-Type: application/json" \
  -d '{"ship_mode":"Standard Class","quantity":6,"discount":0.3,"shipping_cost":15,"n_furniture":1,"n_office":1,"n_tech":1}'
```

Output:

```json
{
  "profit_probability": 0.2222,
  "predicted_label": "Rugi",
  "recommendation": "high_risk",
  "recommendation_label": "High Risk"
}
```

| Field | Keterangan |
|---|---|
| `profit_probability` | P(order untung), 0.0 – 1.0 |
| `predicted_label` | `Untung` atau `Rugi` (ambang default 0,5 model) |
| `recommendation` | `safe` (P ≥ 0,70), `review` (0,50 ≤ P < 0,70), atau `high_risk` (P < 0,50) |
| `recommendation_label` | Teks rekomendasi: `Safe to Process`, `Review Manual`, `High Risk` |

### `POST /predict/regression`

```bash
curl -X POST http://localhost:8000/predict/regression \
  -H "Content-Type: application/json" \
  -d '{"ship_mode":"Standard Class","quantity":6,"discount":0.1,"shipping_cost":15,"n_furniture":1,"n_office":1,"n_tech":1}'
```

Output:

```json
{ "estimated_sales": 233.86 }
```

### `GET /health`

```json
{ "status": "ok", "models_loaded": ["classification", "regression"] }
```

## Deployment

Frontend yang dipublikasikan tidak bisa memanggil backend yang berjalan di laptop, jadi backend perlu di-deploy juga.

**Backend (Hugging Face Spaces, Docker):**

1. Buat akun di huggingface.co, lalu **New Space** (SDK: **Docker**, hardware: CPU basic - free). Buat juga Access Token dengan izin *write* di Settings > Access Tokens.
2. Dari root repo jalankan (butuh `git` dan `git-lfs`):
   `HF_USER=<username> HF_SPACE=<nama-space> HF_TOKEN=hf_xxx bash hf_space/deploy.sh`
   Script merakit `Dockerfile`, `backend/`, dan `model/` ke repo Space (file `.pkl` > 10 MB dikirim lewat Git LFS) lalu push.
3. Tunggu build selesai (tab **Logs**), lalu buka `https://<username>-<nama-space>.hf.space/health` - statusnya harus `ok`. Dokumentasi endpoint ada di `/docs`.
4. Space gratis bisa tidur saat tidak aktif, sehingga request pertama bisa butuh beberapa menit. Buka `/health` terlebih dahulu sebelum demo.

**Frontend (Streamlit Community Cloud):**

1. Buat/ubah app dengan **Main file path** `frontend/app.py`.
2. Di **Settings > Secrets**, isi: `BACKEND_URL = "https://<username>-<nama-space>.hf.space"`.
3. Reboot app.

## Deployed Links

- Frontend: `https://lnt-camp-2026-final-e73ddpomrtnufvkuhqj6y2.streamlit.app`
- Backend: _isi URL Hugging Face Space setelah deploy_ (cek `/health` dan `/docs`)
- LinkedIn post: _belum diisi_

## Key Findings

- **Diskon tinggi menyebabkan kerugian:** order dengan diskon >30% rugi pada ±87% kasus (margin agregat ±-31%), di semua rentang kuantitas. Diskon 16–30% masih mayoritas untung secara agregat (±77%), tetapi risikonya naik tajam mendekati 30% (win rate ±47% pada diskon 25–30%).
- **Furniture paling rentan:** win rate per baris produk ±67%, dibanding ±75–76% untuk Office Supplies dan Technology.
- **Margin stabil:** 2011→2014 sales naik ±1,9x dan profit ±2,0x (margin ±11–12%, rata-rata diskon stabil ±16%). Tidak ada bukti margin menipis.
- **Diskon adalah prediktor utama:** ±90% feature importance model klasifikasi berasal dari `discount`.
- **Ongkos kirim adalah proxy kuat untuk sales,** tetapi ketersediaannya sebelum order diproses adalah asumsi yang perlu divalidasi.

# LnT Camp 2026 — Final Project

*Bridging the Gap: Empowering Future Talent through Machine Learning for Industry Innovation*

## Team

- Muhamad Atallah Alimusa (Team Leader)
- Muhammad Fahry Fauzi

## Project Overview

Decision Support System untuk manajer ritel yang mengevaluasi keranjang pelanggan di level order. Sistem memproyeksikan estimasi omzet (`Sales`) dan berperan sebagai *early warning* yang menandai order berpotensi rugi **sebelum** diproses.

## Chosen Modelling Tasks

- [x] Regression — predicting `Sales` (estimasi omzet order)
- [x] Classification — predicting `Profitability Status` (Safe vs. High Risk)
- [ ] Clustering — tidak dikerjakan

## Folder Structure

*Catatan: arsitektur disederhanakan menjadi satu aplikasi Streamlit (monolitik) agar deployment efisien.*

```
notebook/   Jupyter notebook (EDA, preprocessing, modelling) + superstore.sqlite (data)
model/      Model terlatih (.pkl) dan daftar kolom fitur
app.py      Aplikasi Streamlit (frontend + logika prediksi)
```

## Dataset

Global Superstore, direstrukturisasi menjadi database SQLite ternormalisasi: `notebook/superstore.sqlite` (±11 MB, ikut di repo agar notebook dapat dijalankan ulang). Skema:

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

## Setup & Run

Butuh Python 3.11+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Untuk menjalankan ulang notebook (dan melatih ulang model, yang menimpa file di `model/`), buka `notebook/final_project.ipynb` di Jupyter, VS Code, atau Colab. Dependensinya sudah ada di `requirements.txt` (kecuali Jupyter itu sendiri: `pip install notebook`).

Versi `scikit-learn` dikunci karena file `.pkl` sensitif terhadap versi library.

## Deployed Links

- Frontend: `https://lnt-camp-2026-final-e73ddpomrtnufvkuhqj6y2.streamlit.app`
- Backend: N/A (arsitektur monolitik)
- LinkedIn post: _belum diisi_

## Key Findings

- **Diskon tinggi menyebabkan kerugian:** order dengan diskon >30% rugi pada ±87% kasus (margin agregat ±-31%), di semua rentang kuantitas. Diskon 16–30% masih mayoritas untung (±77%).
- **Furniture paling rentan:** win rate per baris produk ±67%, dibanding ±75–76% untuk Office Supplies dan Technology.
- **Margin stabil:** 2011→2014 sales naik ±1,9x dan profit ±2,0x (margin ±11–12%, rata-rata diskon stabil ±16%). Tidak ada bukti margin menipis.
- **Diskon adalah prediktor utama:** ±90% feature importance model klasifikasi berasal dari `discount`.
- **Ongkos kirim adalah proxy kuat untuk sales,** tetapi ketersediaannya sebelum order diproses adalah asumsi yang perlu divalidasi.

"""Frontend Streamlit — Superstore Profit Predictor (LnT Camp 2026).

Frontend HANYA menampilkan form dan hasil. Semua prediksi dilakukan oleh Backend API
(lihat backend/main.py) lewat HTTP. URL backend dibaca dari:
  1. environment variable BACKEND_URL, atau
  2. Streamlit secrets (BACKEND_URL = "https://...") , atau
  3. default http://localhost:8000 (untuk pengembangan lokal).
"""
import os

import requests
import streamlit as st

st.set_page_config(page_title="Superstore Profit Predictor", page_icon="📈", layout="centered")

SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]
REQUEST_TIMEOUT = 90  # detik; backend gratis (mis. Render) bisa butuh waktu saat "bangun" dari tidur


def get_backend_url() -> str:
    url = os.environ.get("BACKEND_URL")
    if not url:
        try:
            url = st.secrets["BACKEND_URL"]
        except Exception:
            url = "http://localhost:8000"
    return url.rstrip("/")


BACKEND_URL = get_backend_url()


# ---------- Komunikasi dengan backend ----------
def panggil_backend(path: str, payload: dict):
    """POST ke backend. Mengembalikan dict hasil, atau None (error sudah ditampilkan)."""
    try:
        resp = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        st.error(f"Tidak dapat terhubung ke backend di `{BACKEND_URL}`. Pastikan backend sudah berjalan "
                 "dan `BACKEND_URL` benar.")
        return None
    except requests.exceptions.Timeout:
        st.error("Backend tidak merespons tepat waktu. Coba lagi beberapa saat (backend mungkin sedang 'bangun').")
        return None

    if resp.status_code == 422:
        try:
            for err in resp.json()["detail"]:
                st.error(str(err.get("msg", "Input tidak valid")).removeprefix("Value error, "))
        except Exception:
            st.error("Input tidak valid.")
        return None
    if not resp.ok:
        st.error(f"Backend mengembalikan error {resp.status_code}.")
        return None
    return resp.json()


def sidebar_status():
    with st.sidebar:
        st.markdown("**Backend API**")
        st.caption(BACKEND_URL)
        if st.button("Cek koneksi backend"):
            try:
                r = requests.get(f"{BACKEND_URL}/health", timeout=REQUEST_TIMEOUT)
                if r.ok:
                    st.success("Backend aktif ✅")
                else:
                    st.error(f"Backend merespons {r.status_code}")
            except requests.exceptions.RequestException:
                st.error("Backend tidak dapat dijangkau")


# ---------- Form input (dipakai kedua halaman simulasi) ----------
def form_keranjang(prefix: str, label_submit: str):
    """Tampilkan form detail keranjang. Return (submitted, payload)."""
    with st.form(f"{prefix}_form"):
        st.subheader("Detail Pesanan")
        col1, col2 = st.columns(2)
        with col1:
            ship_mode = st.selectbox("Mode Pengiriman", SHIP_MODES, key=f"{prefix}_ship")
            quantity = st.number_input("Total Kuantitas (unit)", min_value=1, max_value=60, value=6, step=1,
                                       key=f"{prefix}_qty")
            shipping_cost = st.number_input("Ongkos Kirim (USD)", min_value=0.0, max_value=2100.0, value=15.0,
                                            step=1.0, key=f"{prefix}_ship_cost")
        with col2:
            diskon = st.slider("Persentase Diskon", min_value=0, max_value=85, value=10, step=5, format="%d%%",
                               key=f"{prefix}_disc")

        st.markdown("**Komposisi keranjang** (jumlah baris produk per kategori)")
        c1, c2, c3 = st.columns(3)
        n_furniture = c1.number_input("Furniture", min_value=0, max_value=14, value=1, step=1, key=f"{prefix}_f")
        n_office = c2.number_input("Office Supplies", min_value=0, max_value=14, value=1, step=1, key=f"{prefix}_o")
        n_tech = c3.number_input("Technology", min_value=0, max_value=14, value=1, step=1, key=f"{prefix}_t")
        submitted = st.form_submit_button(label_submit)

    payload = {
        "ship_mode": ship_mode,
        "quantity": int(quantity),
        "discount": diskon / 100.0,
        "shipping_cost": float(shipping_cost),
        "n_furniture": int(n_furniture),
        "n_office": int(n_office),
        "n_tech": int(n_tech),
    }
    return submitted, payload


# ---------- Halaman 1: Klasifikasi ----------
def halaman_klasifikasi():
    st.title("🚨 Prediksi Risiko Profit")
    st.markdown("**Task Klasifikasi.** Masukkan detail keranjang untuk mengetahui apakah order berpotensi "
                "**Untung** atau **Rugi** sebelum diproses.")
    sidebar_status()

    submitted, payload = form_keranjang("clf", "Analisis Risiko 🚀")
    if not submitted:
        return

    with st.spinner("Memanggil backend..."):
        hasil = panggil_backend("/predict/classification", payload)
    if hasil is None:
        return

    p = hasil["profit_probability"] * 100
    st.markdown("---")
    st.subheader("📊 Hasil Analisis")
    col1, col2 = st.columns(2)
    col1.metric("Probabilitas Untung", f"{p:.2f}%")
    col2.metric("Prediksi Model (ambang 50%)", hasil["predicted_label"])

    level = hasil["recommendation"]
    if level == "safe":
        st.success("✅ **Rekomendasi: Safe to Process.** Transaksi ini diprediksi menguntungkan dengan keyakinan tinggi.")
    elif level == "review":
        st.warning("⚠️ **Rekomendasi: Review Manual.** Probabilitas keuntungan marginal. "
                   "Tinjau ulang besaran diskon sebelum diproses.")
    else:
        st.error("🚨 **Rekomendasi: High Risk!** Potensi rugi tinggi. Segera tinjau ulang diskon atau komposisi keranjang.")

    st.caption("Ambang rekomendasi: Safe ≥ 70% · Review 50–69,9% · High Risk < 50%. "
               "Prediksi bersifat statistik dan tidak menggantikan perhitungan harga.")


# ---------- Halaman 2: Regresi ----------
def halaman_regresi():
    st.title("💰 Estimasi Omzet (Sales)")
    st.markdown("**Task Regresi.** Masukkan detail keranjang untuk mengestimasi total **Sales** (omzet) order.")
    sidebar_status()

    submitted, payload = form_keranjang("reg", "Estimasi Sales 🚀")
    if not submitted:
        return

    with st.spinner("Memanggil backend..."):
        hasil = panggil_backend("/predict/regression", payload)
    if hasil is None:
        return

    st.markdown("---")
    st.subheader("📊 Hasil Estimasi")
    st.metric("Estimasi Nilai Omzet (Sales)", f"${hasil['estimated_sales']:,.2f}")
    st.caption("Pada data uji, rata-rata selisih estimasi dengan omzet sebenarnya sekitar $158 per order. "
               "Estimasi sangat dipengaruhi ongkos kirim, sehingga diasumsikan ongkir sudah dikutip saat checkout. "
               "Bukan pengganti perhitungan harga.")


# ---------- Navigasi ----------
pg = st.navigation([
    st.Page(halaman_klasifikasi, title="Klasifikasi: Risiko Profit", icon="🚨", url_path="klasifikasi", default=True),
    st.Page(halaman_regresi, title="Regresi: Estimasi Sales", icon="💰", url_path="regresi"),
])
pg.run()

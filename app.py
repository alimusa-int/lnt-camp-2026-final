import streamlit as st
import pandas as pd
import joblib

# 1. Konfigurasi halaman
st.set_page_config(page_title="Superstore Profit Predictor", page_icon="📈", layout="centered")


# 2. Load model (di-cache supaya tidak dimuat ulang di setiap interaksi)
@st.cache_resource
def load_assets():
    clf = joblib.load("model/classification_model.pkl")
    reg = joblib.load("model/regression_model.pkl")
    fitur_model_asli = joblib.load("model/feature_columns.pkl")
    return clf, reg, fitur_model_asli


clf_model, reg_model, fitur_model_asli = load_assets()

SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]


def bangun_fitur(ship_mode, quantity, discount, shipping_cost, n_furniture, n_office, n_tech):
    """Ubah input form menjadi baris fitur yang SAMA dengan saat training (lihat notebook, Bagian 4-5).

    Fitur numerik : discount, shipping_cost, quantity, n_items, share_furniture, share_technology
    Fitur kategorik: ship_mode (one-hot). `discount_tier` tidak dipakai model.
    """
    n_items = n_furniture + n_office + n_tech
    baris = pd.DataFrame([{
        "discount": discount,
        "shipping_cost": shipping_cost,
        "quantity": quantity,
        "n_items": n_items,
        "share_furniture": n_furniture / n_items,
        "share_technology": n_tech / n_items,
        "ship_mode": ship_mode,
    }])
    encoded = pd.get_dummies(baris, columns=["ship_mode"], dtype=int)
    # Samakan urutan & nama kolom persis dengan training (dari model/feature_columns.pkl)
    return encoded.reindex(columns=fitur_model_asli, fill_value=0)


# --- UI ---
st.title("🛒 Superstore Profit Predictor")
st.markdown(
    "Masukkan detail keranjang di bawah ini untuk memprediksi apakah transaksi akan "
    "**Untung** atau **Rugi**, serta mengestimasi total **Sales**."
)

with st.form("prediction_form"):
    st.subheader("Detail Pesanan")

    col1, col2 = st.columns(2)
    with col1:
        ship_mode = st.selectbox("Mode Pengiriman", SHIP_MODES)
        quantity = st.number_input("Total Kuantitas (unit)", min_value=1, max_value=60, value=6, step=1)
        shipping_cost = st.number_input("Ongkos Kirim (USD)", min_value=0.0, max_value=2100.0, value=15.0, step=1.0)
    with col2:
        discount_percent = st.slider("Persentase Diskon", min_value=0, max_value=85, value=10, step=5, format="%d%%")

    st.markdown("**Komposisi keranjang** (jumlah baris produk per kategori)")
    c1, c2, c3 = st.columns(3)
    n_furniture = c1.number_input("Furniture", min_value=0, max_value=14, value=1, step=1)
    n_office = c2.number_input("Office Supplies", min_value=0, max_value=14, value=1, step=1)
    n_tech = c3.number_input("Technology", min_value=0, max_value=14, value=1, step=1)

    submitted = st.form_submit_button("Analisis Pesanan 🚀")

# --- LOGIKA PREDIKSI ---
if submitted:
    n_items = n_furniture + n_office + n_tech

    if n_items == 0:
        st.error("Keranjang kosong: isi minimal satu baris produk.")
    elif quantity < n_items:
        st.error(f"Total kuantitas ({quantity}) tidak boleh lebih kecil dari jumlah baris produk ({n_items}).")
    else:
        with st.spinner("Mesin AI sedang menganalisis data..."):
            try:
                input_final = bangun_fitur(
                    ship_mode, quantity, discount_percent / 100.0, shipping_cost,
                    n_furniture, n_office, n_tech,
                )

                profit_pred = clf_model.predict(input_final)[0]
                profit_proba = clf_model.predict_proba(input_final)[0][1] * 100
                sales_pred = reg_model.predict(input_final)[0]

                st.markdown("---")
                st.subheader("📊 Hasil Analisis AI")

                col3, col4 = st.columns(2)
                col3.metric(label="Estimasi Nilai Omzet (Sales)", value=f"${sales_pred:,.2f}")
                col4.metric(label="Probabilitas Keuntungan", value=f"{profit_proba:.2f}%")

                if profit_pred == 1:
                    st.success("✅ **Rekomendasi:** Safe to Process. Transaksi ini diprediksi menguntungkan.")
                else:
                    st.error("⚠️ **Rekomendasi:** High Risk! Potensi rugi tinggi. Tinjau ulang diskon atau komposisi keranjang.")

                st.caption(
                    "Catatan: estimasi Sales sangat dipengaruhi ongkos kirim, sehingga diasumsikan ongkir sudah "
                    "dikutip saat checkout. Prediksi bersifat statistik dan tidak menggantikan perhitungan harga."
                )

            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses model: {e}")

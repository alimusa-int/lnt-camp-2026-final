import streamlit as st
import pandas as pd
import joblib

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Superstore Profit Predictor", page_icon="📈", layout="centered")

# 2. Fungsi Load Model
@st.cache_resource
def load_assets():
    # Pastikan path ini sesuai dengan struktur folder lu saat ditaruh di GitHub
    clf = joblib.load("model/classification_model.pkl") 
    reg = joblib.load("model/regression_model.pkl")
    fitur_model_asli = joblib.load("model/feature_columns.pkl")
    return clf, reg, fitur_model_asli

clf_model, reg_model, fitur_model_asli = load_assets()

# Kategori diskon HARUS sama persis dengan fungsi categorize_discount() di notebook
# (Bagian 4: Preprocessing / Feature Engineering) agar hasil binning konsisten dengan training.
def categorize_discount(d):
    if d == 0:
        return "No Discount"
    elif d <= 0.15:
        return "Low (<=15%)"
    elif d <= 0.30:
        return "Medium (16-30%)"
    else:
        return "High (>30%)"

# --- UI FRONTEND ---
st.title("🛒 Superstore Profit Predictor")
st.markdown("Masukkan detail pesanan di bawah ini untuk memprediksi apakah transaksi akan **Untung** atau **Rugi**, serta mengestimasi total **Sales**.")

with st.form("prediction_form"):
    st.subheader("Detail Pesanan")
    
    col1, col2 = st.columns(2)
    with col1:
        ship_mode = st.selectbox("Mode Pengiriman", ["Standard Class", "Second Class", "First Class", "Same Day"])
        quantity = st.number_input("Kuantitas Barang", min_value=1, max_value=50, value=3, step=1)
        
    with col2:
        discount_percent = st.slider("Persentase Diskon", min_value=0, max_value=80, value=10, step=5, format="%d%%")
        shipping_cost = st.number_input("Ongkos Kirim (USD)", min_value=0.0, max_value=1000.0, value=15.0, step=1.0)

    submitted = st.form_submit_button("Analisis Pesanan 🚀")

# --- LOGIKA PREDIKSI ---
if submitted:
    discount_decimal = discount_percent / 100.0
    
    with st.spinner("Mesin AI sedang menganalisis data..."):
        try:
            # A. Buat DataFrame dari input (nama kolom huruf kecil, sesuai training)
            input_data = pd.DataFrame([{
                "quantity": quantity,
                "discount": discount_decimal,
                "shipping_cost": shipping_cost,
                "discount_tier": categorize_discount(discount_decimal),
                "ship_mode": ship_mode
            }])

            # B. One-Hot Encoding (kolom kategorikal sama seperti saat training: discount_tier & ship_mode)
            input_encoded = pd.get_dummies(input_data, columns=["discount_tier", "ship_mode"])

            # C. Samakan struktur kolom persis saat training
            # (diambil dari model/feature_columns.pkl, bukan hardcode, biar selalu sinkron dengan model)
            input_final = input_encoded.reindex(columns=fitur_model_asli, fill_value=0)

            # D. Eksekusi Prediksi (Tanpa API FastAPI)
            profit_pred = clf_model.predict(input_final)[0]
            profit_proba = clf_model.predict_proba(input_final)[0][1] * 100 
            sales_pred = reg_model.predict(input_final)[0]

            # E. Render Hasil
            st.markdown("---")
            st.subheader("📊 Hasil Analisis AI")
            
            col3, col4 = st.columns(2)
            col3.metric(label="Estimasi Nilai Omzet (Sales)", value=f"${sales_pred:,.2f}")
            col4.metric(label="Probabilitas Keuntungan", value=f"{profit_proba:.2f}%")
            
            if profit_pred == 1:
                st.success("✅ **Rekomendasi:** Safe to Process. Transaksi ini diprediksi menguntungkan.")
            else:
                st.error("⚠️ **Rekomendasi:** High Risk! Potensi rugi tinggi. Tinjau ulang diskon atau biaya pengiriman.")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses model: {e}")

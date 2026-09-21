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
    return clf, reg

clf_model, reg_model = load_assets()

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
            # A. Buat DataFrame dari input
            input_data = pd.DataFrame([{
                "Quantity": quantity,
                "Discount": discount_decimal,
                "Shipping Cost": shipping_cost,
                "Ship Mode": ship_mode
            }])

            # B. One-Hot Encoding
            input_encoded = pd.get_dummies(input_data)
            
            # C. Samakan struktur kolom persis saat training (Fitur asli dari model lu)
            fitur_model_asli = [
                "Quantity", 
                "Discount", 
                "Shipping Cost", 
                "Ship Mode_First Class", 
                "Ship Mode_Same Day", 
                "Ship Mode_Second Class", 
                "Ship Mode_Standard Class"
            ]
            
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
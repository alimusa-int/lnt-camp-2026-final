import streamlit as st
import requests

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Superstore Profit Predictor", page_icon="📈", layout="centered")

st.title("🛒 Superstore Profit Predictor")
st.markdown("Masukkan detail pesanan di bawah ini untuk memprediksi apakah transaksi akan **Untung** atau **Rugi**, serta mengestimasi total **Sales**.")

# 2. Form Input User
with st.form("prediction_form"):
    st.subheader("Detail Pesanan")
    
    col1, col2 = st.columns(2)
    with col1:
        ship_mode = st.selectbox("Mode Pengiriman", ["Standard Class", "Second Class", "First Class", "Same Day"])
        quantity = st.number_input("Kuantitas Barang", min_value=1, max_value=50, value=3, step=1)
        
    with col2:
        # UBAH DISINI: slider jadi pakai angka 0 - 80 dan ada simbol %
        discount_percent = st.slider("Persentase Diskon", min_value=0, max_value=80, value=10, step=5, format="%d%%", help="Pilih besaran diskon dari 0% hingga 80%")
        shipping_cost = st.number_input("Ongkos Kirim (USD)", min_value=0.0, max_value=1000.0, value=15.0, step=1.0)

    # Tombol submit
    submitted = st.form_submit_button("Analisis Pesanan 🚀")

# 3. Logika Mengirim Request ke FastAPI Backend
if submitted:
    API_URL = "http://127.0.0.1:8000/predict"
    
    # UBAH DISINI: Jadikan desimal lagi sebelum dikirim ke API
    discount_decimal = discount_percent / 100.0
    
    payload = {
        "discount": discount_decimal,
        "shipping_cost": shipping_cost,
        "quantity": quantity,
        "ship_mode": ship_mode
    }
    
    with st.spinner("Mesin sedang menganalisis data..."):
        try:
            # Tembak API
            response = requests.post(API_URL, json=payload)
            response.raise_for_status() 
            
            # Ambil hasil
            result = response.json()["data"]
            
            st.markdown("---")
            st.subheader("📊 Hasil Analisis AI")
            
            col3, col4 = st.columns(2)
            col3.metric(label="Estimasi Nilai Omzet (Sales)", value=f"${result['estimated_sales_usd']}")
            col4.metric(label="Probabilitas Keuntungan", value=f"{result['profit_probability']}%")
            
            # Keputusan Bisnis
            if result['is_profitable'] == 1:
                st.success(f"✅ **Rekomendasi:** {result['business_decision']}")
            else:
                st.error(f"⚠️ **Rekomendasi:** {result['business_decision']}")
                
        except requests.exceptions.ConnectionError:
            st.error("Gagal terhubung ke Backend. Pastikan FastAPI sudah berjalan di http://127.0.0.1:8000")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
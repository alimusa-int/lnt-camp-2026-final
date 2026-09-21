from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(
    title="Superstore ML API",
    description="API untuk Prediksi Profitabilitas dan Estimasi Sales",
    version="1.0.0"
)

# 1. Buka Dapur: Load Model & Fitur saat server start
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")

try:
    clf_model = joblib.load(os.path.join(MODEL_DIR, "classification_model.pkl"))
    reg_model = joblib.load(os.path.join(MODEL_DIR, "regression_model.pkl"))
    feature_columns = joblib.load(os.path.join(MODEL_DIR, "feature_columns.pkl"))
except Exception as e:
    print(f"Error loading models: {e}. Pastikan file .pkl sudah ada di folder model/")

# 2. Catatan Pesanan: Validasi input dari Frontend
class OrderRequest(BaseModel):
    discount: float
    shipping_cost: float
    quantity: int
    ship_mode: str

# 3. Logika Feature Engineering
def categorize_discount(d: float) -> str:
    if d == 0:
        return 'No Discount'
    elif d <= 0.15:
        return 'Low (<=15%)'
    elif d <= 0.30:
        return 'Medium (16-30%)'
    else:
        return 'High (>30%)'

# 4. Endpoint Utama untuk Prediksi
@app.post("/predict")
def predict_order(order: OrderRequest):
    try:
        # A. Siapkan data mentah
        discount_tier = categorize_discount(order.discount)
        
        # B. Jadikan DataFrame satu baris
        input_data = pd.DataFrame([{
            'discount': order.discount,
            'shipping_cost': order.shipping_cost,
            'quantity': order.quantity,
            'discount_tier': discount_tier,
            'ship_mode': order.ship_mode
        }])

        # C. One-Hot Encoding
        input_encoded = pd.get_dummies(input_data)
        
        # D. Samakan struktur kolom persis dengan saat mesin belajar di Week 2
        input_final = input_encoded.reindex(columns=feature_columns, fill_value=0)

        # E. Eksekusi Prediksi
        is_profitable = int(clf_model.predict(input_final)[0])
        profit_prob = float(clf_model.predict_proba(input_final)[0][1])
        estimated_sales = float(reg_model.predict(input_final)[0])

        # F. Kirim Hasil ke Frontend
        return {
            "status": "success",
            "data": {
                "is_profitable": is_profitable,
                "profit_probability": round(profit_prob * 100, 2),
                "estimated_sales_usd": round(estimated_sales, 2),
                "business_decision": "Safe to Process" if is_profitable == 1 else "High Risk - Review Required"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
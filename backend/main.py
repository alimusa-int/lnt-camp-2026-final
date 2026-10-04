"""Backend API — Superstore Profit Predictor (LnT Camp 2026).

Dua endpoint prediksi (satu per task modelling) + health check:
  GET  /health                   -> status layanan
  POST /predict/classification   -> P(untung) + rekomendasi 3-tier (Safe / Review / High Risk)
  POST /predict/regression       -> estimasi Sales (omzet) order

Model dimuat dari folder model/ saat startup (tidak ada retraining).
Jalankan dari root repo:
  uvicorn backend.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"

SHIP_MODES = ("Standard Class", "Second Class", "First Class", "Same Day")

# Custom Threshold 3-Tier (lihat notebook, Bagian 5): berlaku pada P(untung)
SAFE_THRESHOLD = 0.70    # P >= 70%        -> Safe to Process
REVIEW_THRESHOLD = 0.50  # 50% <= P < 70%  -> Review Manual ; P < 50% -> High Risk

assets: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    assets["clf"] = joblib.load(MODEL_DIR / "classification_model.pkl")
    assets["reg"] = joblib.load(MODEL_DIR / "regression_model.pkl")
    assets["features"] = joblib.load(MODEL_DIR / "feature_columns.pkl")
    yield
    assets.clear()


app = FastAPI(
    title="Superstore Profit Predictor API",
    description="Prediksi profitabilitas (klasifikasi) dan estimasi omzet (regresi) untuk keranjang order.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- Skema input / output ----------
class Basket(BaseModel):
    ship_mode: Literal["Standard Class", "Second Class", "First Class", "Same Day"] = Field(
        ..., description="Moda pengiriman yang dipilih pelanggan")
    quantity: int = Field(..., ge=1, le=60, description="Total kuantitas (unit) di seluruh keranjang")
    discount: float = Field(..., ge=0.0, le=0.85, description="Diskon tertinggi dalam keranjang (0.0 - 0.85)")
    shipping_cost: float = Field(..., ge=0.0, le=2100.0, description="Total ongkos kirim (USD)")
    n_furniture: int = Field(..., ge=0, le=14, description="Jumlah baris produk kategori Furniture")
    n_office: int = Field(..., ge=0, le=14, description="Jumlah baris produk kategori Office Supplies")
    n_tech: int = Field(..., ge=0, le=14, description="Jumlah baris produk kategori Technology")

    @model_validator(mode="after")
    def cek_keranjang(self):
        n_items = self.n_furniture + self.n_office + self.n_tech
        if n_items == 0:
            raise ValueError("Keranjang kosong: isi minimal satu baris produk.")
        if self.quantity < n_items:
            raise ValueError(
                f"Total kuantitas ({self.quantity}) tidak boleh lebih kecil dari jumlah baris produk ({n_items}).")
        return self

    model_config = {"json_schema_extra": {"example": {
        "ship_mode": "Standard Class", "quantity": 6, "discount": 0.1, "shipping_cost": 15.0,
        "n_furniture": 1, "n_office": 1, "n_tech": 1}}}


class ClassificationResult(BaseModel):
    profit_probability: float = Field(..., description="P(order untung), 0.0 - 1.0")
    predicted_label: Literal["Untung", "Rugi"] = Field(..., description="Label default model (ambang 0,5)")
    recommendation: Literal["safe", "review", "high_risk"] = Field(..., description="Zona 3-tier")
    recommendation_label: str


class RegressionResult(BaseModel):
    estimated_sales: float = Field(..., description="Estimasi omzet order (USD)")


# ---------- Logika bantu ----------
def bangun_fitur(b: Basket) -> pd.DataFrame:
    """Ubah input menjadi baris fitur yang SAMA dengan saat training (notebook, Bagian 4-5)."""
    n_items = b.n_furniture + b.n_office + b.n_tech
    baris = {
        "discount": b.discount,
        "shipping_cost": b.shipping_cost,
        "quantity": b.quantity,
        "n_items": n_items,
        "share_furniture": b.n_furniture / n_items,
        "share_technology": b.n_tech / n_items,
    }
    for mode in SHIP_MODES:
        baris[f"ship_mode_{mode}"] = int(b.ship_mode == mode)
    # urutan & nama kolom persis seperti training (model/feature_columns.pkl)
    return pd.DataFrame([baris])[assets["features"]]


def zona_rekomendasi(p_untung: float) -> tuple[str, str]:
    if p_untung >= SAFE_THRESHOLD:
        return "safe", "Safe to Process"
    if p_untung >= REVIEW_THRESHOLD:
        return "review", "Review Manual"
    return "high_risk", "High Risk"


# ---------- Endpoint ----------
@app.get("/")
def root():
    return {"service": "Superstore Profit Predictor API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    ok = all(k in assets for k in ("clf", "reg", "features"))
    if not ok:
        raise HTTPException(status_code=503, detail="Model belum dimuat")
    return {"status": "ok", "models_loaded": ["classification", "regression"]}


@app.post("/predict/classification", response_model=ClassificationResult)
def predict_classification(basket: Basket):
    X = bangun_fitur(basket)
    clf = assets["clf"]
    p_untung = float(clf.predict_proba(X)[0][1])  # kelas 1 = Untung
    level, label = zona_rekomendasi(p_untung)
    return ClassificationResult(
        profit_probability=p_untung,
        predicted_label="Untung" if int(clf.predict(X)[0]) == 1 else "Rugi",
        recommendation=level,
        recommendation_label=label,
    )


@app.post("/predict/regression", response_model=RegressionResult)
def predict_regression(basket: Basket):
    X = bangun_fitur(basket)
    return RegressionResult(estimated_sales=float(assets["reg"].predict(X)[0]))

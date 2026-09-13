# LnT Camp 2026 — Final Project

*Bridging the Gap: Empowering Future Talent through Machine Learning for Industry Innovation*

## Team

- Name 1 — Team Leader
- Name 2
- Name 3
- Name 4

## Project Overview

<!-- 2-3 sentences: what the project does and the business question it answers -->

## Chosen Modelling Tasks

We selected the following 2 of 3 tasks:

- [ ] Regression — predicting `___`
- [ ] Classification — predicting `___`
- [ ] Clustering — segmenting `___`

## Folder Structure

```
notebook/   Jupyter notebook (EDA, preprocessing, modelling) + data loading instructions
model/      Saved trained model files (.pkl / .joblib) and training scripts
backend/    REST API (prediction endpoints)
frontend/   Simulation app (user inputs -> backend -> prediction shown)
```

## Dataset

This project uses the Global Superstore dataset, restructured into a normalised SQLite database (`superstore.sqlite`). See `notebook/` for the schema and loading queries.

## Setup & Run — Backend

```bash
cd backend
pip install -r requirements.txt
# start command here, e.g.:
uvicorn main:app --reload
```

Endpoints:

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/predict/...` | ... |

## Setup & Run — Frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Deployed app: `<link here>`

## Deployed Links

- Frontend: `<link>`
- Backend (if deployed): `<link>`
- LinkedIn post: `<link>`

## Key Findings

<!-- 3-5 bullet business insights from the notebook -->

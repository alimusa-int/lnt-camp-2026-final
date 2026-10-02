# LnT Camp 2026 — Final Project

*Bridging the Gap: Empowering Future Talent through Machine Learning for Industry Innovation*

## Team

- Muhamad Atallah Alimusa (Team Leader)
- Muhammad Fahry Fauzi

## Project Overview

This project serves as a Decision Support System for retail managers to evaluate customer baskets at the order level. It projects potential sales volume and acts as a risk mitigation gatekeeper by flagging potentially unprofitable transactions before they are processed.

## Chosen Modelling Tasks

We selected the following 2 of 3 tasks:

- [x] Regression — predicting `Sales` (Estimating order volume)
- [x] Classification — predicting `Profitability Status` (Safe vs. High Risk)
- [ ] Clustering — segmenting `___`

## Folder Structure

*Note: The architecture was adapted into a Monolithic Streamlit Application for deployment efficiency.*

```
notebook/   Jupyter notebook (EDA, preprocessing, modelling) + data loading instructions
model/      Saved trained model files (.pkl) and feature columns reference
app.py      Main Streamlit application (Frontend + Embedded Prediction Logic)
```

## Dataset

This project uses the Global Superstore dataset, restructured into a normalised SQLite database (superstore.sqlite). See notebook/ for the schema and loading queries.

## Setup & Run — Backend

*Note: The frontend and backend prediction logic are integrated into a single monolithic Streamlit app. No separate REST API or backend setup is required.*

```bash
pip install -r requirements.txt
streamlit run app.py
```

Deployed app: `https://lnt-camp-2026-final-e73ddpomrtnufvkuhqj6y2.streamlit.app`

## Deployed Links

- Frontend: `<https://lnt-camp-2026-final-e73ddpomrtnufvkuhqj6y2.streamlit.app>`
- Backend (if deployed): `<N/A (Monolithic Architecture)>`
- LinkedIn post: `<link>`

## Key Findings

- High Discounts Drive Consistent Losses: Transactions with discount rates exceeding 30% consistently result in negative profit margins, regardless of the order quantity.

- Furniture is the Most Vulnerable Category: The Furniture category has the lowest profitability win-rate (~67%) compared to Office Supplies and Technology (~74-76%).

- Lagging Profit Growth: Trend analysis from 2011 to 2014 shows that while total sales nearly doubled, profit growth lagged significantly, indicating margins are being eroded by aggressive discounting.

- Logistics as a Strong Proxy: Operational logistics metrics (shipping_cost, quantity, ship_mode, and discount_tier) proved to be highly effective proxy variables for the AI to estimate sales volume without unit prices.

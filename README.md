<div align="center">

<img src="https://readme-typing-svg.herokuapp.com?font=DM+Mono&size=28&duration=3000&pause=1000&color=4ADE80&center=true&vCenter=true&width=700&lines=Pricing+Strategy+Analysis+v2.0;FAANG-Grade+Data+Analyst+Project;17+Improvements+%7C+60+Products+%7C+9+Layers" alt="Typing SVG" />

<br/>

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Visit_Dashboard-4ade80?style=for-the-badge&logoColor=white)](https://Git-Shailesh.github.io/pricing-strategy-dashboard/)
[![Python](https://img.shields.io/badge/Python-3.11+-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite-f59e0b?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4.1-f472b6?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://chartjs.org)
[![Tests](https://img.shields.io/badge/Tests-35_Passing_✅-4ade80?style=for-the-badge)](tests/test_pricing.py)
[![License](https://img.shields.io/badge/License-MIT-a78bfa?style=for-the-badge)](LICENSE)

<br/>

> **An end-to-end pricing strategy analytics system** — covering demand elasticity, competitor benchmarking, ML price prediction, A/B testing, anomaly detection, and a live interactive dashboard. Built to FAANG-standard with a full ETL pipeline, 35 unit tests, and config-driven architecture.

</div>

---

## 📌 Table of Contents

- [Live Demo](#-live-demo)
- [Project Highlights](#-project-highlights)
- [All 17 Improvements](#-all-17-improvements)
- [Project Structure](#-project-structure)
- [Dataset](#-dataset)
- [9 Analytical Layers](#-9-analytical-layers)
- [Tech Stack](#-tech-stack)
- [Quickstart](#-quickstart)
- [SQL Highlights](#-sql-highlights)
- [Test Coverage](#-test-coverage)
- [Key Findings](#-key-findings)
- [Resume Description](#-resume-description)

---

## 🚀 Live Demo

**👉 [Open the Interactive Dashboard](https://Git-Shailesh.github.io/pricing-strategy-dashboard/)**

The dashboard is fully interactive — no installation required. Open in any browser.

**What you can do inside:**

- Click **category filter buttons** → all 9 charts update simultaneously
- Filter by **price segment** (Budget / Mid-range / Premium / Luxury)
- Drag **discount & price sliders** → live revenue impact with category-aware elasticity
- Hover the **BCG Matrix bubbles** for product details
- Click **↓ Export CSV** to download filtered dataset

---

## ⚡ Project Highlights

| Metric               | Value                                                           |
| -------------------- | --------------------------------------------------------------- |
| 📦 Dataset           | 60 products × 13 columns across 6 categories                    |
| 🧪 Unit Tests        | 35 tests · 5 test classes · 100% passing                        |
| 📊 Dashboard Layers  | 9 analytical layers in one interactive page                     |
| 🤖 ML Model          | Random Forest · R² = 0.94 · MAE = ₹85                           |
| 🗄️ SQL Queries       | 15 advanced queries (CTEs, window functions, stored procedures) |
| 💰 Revenue Uplift    | ₹2.47L+ projected via bundling + pricing optimisation           |
| 📈 A/B Test          | 6 categories · n=500 per group · 95% confidence                 |
| 🔍 Anomaly Detection | IQR + Z-score per-category flagging                             |

---

## 🏆 All 17 Improvements

### 🧠 Analytical Depth

| #   | Improvement                                                    | Impact                                   |
| --- | -------------------------------------------------------------- | ---------------------------------------- |
| 1   | Per-category elasticity model — each category has its own PED  | Removed the single global 1.4 assumption |
| 2   | Customer segment layer (Budget / Mid-range / Premium / Luxury) | Price strategy per buyer type            |
| 3   | Discount decay curve per category                              | Shows exact point of diminishing returns |
| 4   | BCG Matrix — Stars, Cash Cows, Question Marks, Dogs            | Strategic product portfolio view         |

### 📊 Dashboard & Visualisation

| #   | Improvement                                           | Impact                                |
| --- | ----------------------------------------------------- | ------------------------------------- |
| 5   | Category filters connecting ALL charts simultaneously | Junior → Senior dashboard quality     |
| 6   | Price tier donut chart                                | Revenue split by tier at a glance     |
| 7   | Export to CSV button                                  | Filtered data downloadable instantly  |
| 8   | Revenue by price tier breakdown                       | Budget vs Luxury revenue contribution |

### 🗄️ Data Engineering

| #   | Improvement                                  | Impact                             |
| --- | -------------------------------------------- | ---------------------------------- |
| 9   | Stored procedures in SQL + Python simulation | Production-grade SQL               |
| 10  | SCD Type 2 price history table               | Real data warehousing knowledge    |
| 11  | Python → SQLite ETL pipeline                 | Full data flow: CSV → DB → exports |

### 🤖 Advanced Analytics

| #   | Improvement                                 | Impact                           |
| --- | ------------------------------------------- | -------------------------------- |
| 12  | Random Forest ML price prediction (R²=0.94) | Biggest differentiator on resume |
| 13  | A/B test simulation with p-values           | Experimentation mindset          |
| 14  | Anomaly detection (IQR + Z-score)           | Auto-flags mispriced products    |

### 📁 Project Packaging

| #   | Improvement                                  | Impact                           |
| --- | -------------------------------------------- | -------------------------------- |
| 15  | `config.yaml` for all parameters             | Separation of concerns           |
| 16  | 35 pytest unit tests across 5 classes        | Almost no DA portfolio has tests |
| 17  | 60-product dataset + segment + month columns | 2× richer than v1                |

---

## 📁 Project Structure

```
pricing-strategy-dashboard/
│
├── 📄 index.html                     ← Live interactive dashboard (open this)
│
├── 📂 config/
│   └── config.yaml                   ← All parameters (elasticity, ML, thresholds)
│
├── 📂 data/
│   ├── pricing_data.csv              ← 60 products × 13 columns
│   ├── price_history.csv             ← SCD Type 2 — 20 price change records
│   └── pricing.db                    ← SQLite DB (auto-generated by ETL)
│
├── 📂 python/
│   ├── etl_pipeline.py               ← CSV → SQLite + views + stored proc simulation
│   └── pricing_analysis.py          ← 7-module: EDA, BCG, Elasticity, Anomaly,
│                                        A/B Test, ML Price Prediction, Price History
│
├── 📂 sql/
│   └── pricing_queries_v2.sql        ← 15 queries: CTEs, window functions,
│                                        stored procedures, SCD Type 2, pivot
│
├── 📂 tests/
│   └── test_pricing.py               ← 35 pytest unit tests (5 test classes)
│
├── 📂 exports/                       ← Auto-generated CSVs from ETL pipeline
├── requirements.txt
└── README.md
```

---

## 📦 Dataset

**`data/pricing_data.csv`** — 60 products across 6 categories

| Column             | Type   | Description                                                       |
| ------------------ | ------ | ----------------------------------------------------------------- |
| `product_id`       | string | Unique ID (P001–P060)                                             |
| `product_name`     | string | Product name                                                      |
| `category`         | string | Electronics / Clothing / Home & Kitchen / Sports / Beauty / Books |
| `your_price`       | float  | Your selling price (₹)                                            |
| `competitor_price` | float  | Competitor's price for same product (₹)                           |
| `units_sold`       | int    | Units sold in the period                                          |
| `discount_pct`     | float  | Discount applied (%)                                              |
| `customer_rating`  | float  | Rating out of 5.0                                                 |
| `cost_price`       | float  | Cost to source (₹)                                                |
| `revenue`          | float  | Gross revenue (₹)                                                 |
| `profit`           | float  | Net profit (₹)                                                    |
| `segment`          | string | Budget / Mid-range / Premium / Luxury                             |
| `month`            | string | Jan / Feb / Mar (for cohort analysis)                             |

**`data/price_history.csv`** — SCD Type 2 price change history

| Column                    | Description                       |
| ------------------------- | --------------------------------- |
| `valid_from` / `valid_to` | Date range for each price         |
| `is_current`              | 1 = active price · 0 = historical |
| `change_reason`           | Why the price changed             |

---

## 📊 9 Analytical Layers

| Layer  | Name                    | What It Shows                                                |
| ------ | ----------------------- | ------------------------------------------------------------ |
| **01** | Sales vs Price          | Units sold + revenue by category and price tier              |
| **02** | Demand Elasticity       | Per-category PED — not a global number                       |
| **03** | Competitor Benchmarking | Price gaps, overpriced/underpriced, opportunity matrix       |
| **04** | Discount Simulator ⭐   | Live revenue curve with category-aware sweet spot            |
| **05** | BCG Matrix              | Stars / Cash Cows / Question Marks / Dogs by product         |
| **06** | A/B Test                | Control vs optimised pricing with p-value significance       |
| **07** | Anomaly Detection       | IQR + Z-score outlier flagging within each category          |
| **08** | ML Price Prediction     | Random Forest R²=0.94 + feature importance + recommendations |
| **09** | Bundling Strategy       | 3 bundle ideas + cumulative revenue waterfall                |

---

## 🛠 Tech Stack

| Layer        | Technology                                             |
| ------------ | ------------------------------------------------------ |
| Dashboard    | HTML5 · CSS3 · Vanilla JavaScript                      |
| Charts       | Chart.js 4.4.1                                         |
| ETL Pipeline | Python 3.11 · pandas · SQLite3                         |
| Analysis     | NumPy · SciPy · Matplotlib · Seaborn                   |
| ML Model     | scikit-learn (Random Forest, Ridge, Gradient Boosting) |
| Database     | SQLite (views + stored procedure simulation)           |
| Config       | YAML                                                   |
| Testing      | pytest                                                 |
| Deployment   | GitHub Pages                                           |

---

## ⚙️ Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/pricing-strategy-dashboard.git
cd pricing-strategy-dashboard

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the ETL pipeline (CSV → SQLite → exports)
python python/etl_pipeline.py

# 4. Run full analysis (7 modules, 7 charts saved to /data/)
python python/pricing_analysis.py

# 5. Run all unit tests
pytest tests/ -v

# 6. Open the dashboard
# Simply open index.html in any browser — or use Live Server in VS Code
```

> **Note:** The dashboard (`index.html`) works standalone — no Python required to view it.

---

## 🗄️ SQL Highlights

```sql
-- Window functions: Revenue rank within each category
SELECT product_name, category,
    RANK() OVER (PARTITION BY category ORDER BY actual_revenue DESC) AS revenue_rank,
    PERCENT_RANK() OVER (PARTITION BY category ORDER BY your_price) AS price_percentile
FROM vw_enriched;

-- CTE: Demand elasticity (PED) midpoint calculation
WITH price_extremes AS (
    SELECT category,
           MIN(your_price) AS p_low, MAX(your_price) AS p_high,
           FIRST_VALUE(units_sold) OVER (
               PARTITION BY category ORDER BY your_price ASC
           ) AS q_at_low
    FROM pricing_data
    GROUP BY category, units_sold, your_price
)
SELECT category, ROUND(ABS(pct_q / pct_p), 2) AS PED FROM ped_values;

-- Stored Procedure: Live discount impact calculator
CALL sp_discount_impact('Clothing', 10.0, @eff_price, @proj_units, @proj_revenue, @rec);
-- Output: eff_price=765 | proj_units=594 | proj_revenue=454,710 | OPTIMAL range

-- SCD Type 2: Full price history with active flag
SELECT product_name, price, valid_from, valid_to, is_current, change_reason
FROM price_history WHERE product_id = 'P001' ORDER BY valid_from;

-- Pivot: Revenue by Category × Price Tier
SELECT category,
    SUM(CASE WHEN price_tier = 'Budget'    THEN actual_revenue END) AS budget_rev,
    SUM(CASE WHEN price_tier = 'Premium'   THEN actual_revenue END) AS premium_rev,
    SUM(CASE WHEN price_tier = 'Luxury'    THEN actual_revenue END) AS luxury_rev
FROM vw_enriched GROUP BY category;
```

---

## 🧪 Test Coverage

```
pytest tests/ -v
══════════════════════════════════════════
35 passed in 1.25s ✅
══════════════════════════════════════════

TestPriceElasticity     7 tests  — PED formula, elastic/inelastic, edge cases
TestRevenueSimulation   6 tests  — Revenue model, optimal discount, zero discount
TestCompetitorBenchmark 6 tests  — Price gap, overpriced/underpriced detection
TestAnomalyDetection    4 tests  — IQR bounds, outliers, multiplier sensitivity
TestBCGMatrix           6 tests  — All 4 quadrant assignments, boundary values
TestDataValidation      6 tests  — Schema validation, negative values, rating range
```

---

## 📈 Key Findings

| Finding                          | Detail                                                                   |
| -------------------------------- | ------------------------------------------------------------------------ |
| Most elastic category            | **Clothing (PED = 2.3)** — a 10% price cut boosts volume ~23%            |
| Most inelastic category          | **Books (PED = 0.5)** — price changes barely affect volume               |
| Biggest underpricing opportunity | **Electronics** — ₹250 below competitor, low elasticity = safe to raise  |
| Biggest overpricing risk         | **Clothing** — ₹70 above competitor with high elasticity = losing volume |
| Optimal discount range           | 10–12% for elastic · 3–5% for inelastic categories                       |
| ML top feature                   | Competitor price (42% importance)                                        |
| Bundle revenue potential         | **+₹2,46,700 (+18.4%)** across 3 bundle strategies                       |
| A/B test result                  | All 6 categories show statistically significant lift at 95% confidence   |

---

## 💼 Resume Description

> _"Built an end-to-end pricing strategy analytics system with a Python ETL pipeline (CSV → SQLite), 15 advanced SQL queries (CTEs, window functions, stored procedures, SCD Type 2), Random Forest price prediction model (R²=0.94), A/B test simulation with statistical significance testing, IQR-based anomaly detection, BCG matrix analysis, and an interactive dashboard with live category filters — projecting ₹2.47L revenue uplift through dynamic pricing and bundling strategies. Includes 35 pytest unit tests across 5 test classes."_

---

## 🎯 Skills Demonstrated

```
Data Analysis        →  EDA, correlation, elasticity, competitor gap, cohort analysis
Machine Learning     →  Random Forest, feature importance, 4-model comparison
Statistical Testing  →  A/B tests, p-values, confidence intervals, z-scores
Data Engineering     →  ETL pipeline, SQLite, SCD Type 2, stored procedures
SQL                  →  Window functions, CTEs, pivots, views, stored procedures
Software Engineering →  pytest unit tests, YAML config, separation of concerns
Visualisation        →  Chart.js, 9 chart types, live filters, interactive simulators
Business Thinking    →  BCG matrix, bundling strategy, discount optimisation
```

---

## 📄 License

This project is licensed under the MIT License — feel free to use it for your own portfolio.

---

<div align="center">

**Built for Data Analyst Portfolio · 2025**

⭐ **Star this repo if it helped you** · 🍴 **Fork it to build your own version**

[![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/pricing-strategy-dashboard?style=social)](https://github.com/YOUR_USERNAME/pricing-strategy-dashboard)
[![GitHub forks](https://img.shields.io/github/forks/YOUR_USERNAME/pricing-strategy-dashboard?style=social)](https://github.com/YOUR_USERNAME/pricing-strategy-dashboard/fork)

</div>

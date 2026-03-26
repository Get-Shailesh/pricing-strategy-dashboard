"""
================================================================
  PRICING STRATEGY — ETL Pipeline
  File    : python/etl_pipeline.py
  Purpose : Load CSVs → SQLite DB → validate → export
================================================================
"""

import sqlite3
import pandas as pd
import yaml
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)


def load_config(path='config/config.yaml'):
    with open(path) as f:
        return yaml.safe_load(f)


def connect_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    log.info(f"Connected to SQLite DB: {db_path}")
    return conn


def load_and_validate(csv_path):
    log.info(f"Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)

    # Validation checks
    assert df.duplicated('product_id').sum() == 0, "Duplicate product_ids found"
    assert df['your_price'].ge(0).all(),           "Negative prices detected"
    assert df['units_sold'].ge(0).all(),           "Negative units detected"
    assert df['discount_pct'].between(0,100).all(),"Discount out of range"
    assert df['customer_rating'].between(0,5).all(),"Rating out of 0-5 range"

    # Clean & derive
    df['price_gap']       = df['your_price'] - df['competitor_price']
    df['price_gap_pct']   = ((df['price_gap'] / df['competitor_price']) * 100).round(2)
    df['margin_pct']      = ((df['your_price'] - df['cost_price']) / df['your_price'] * 100).round(2)
    df['effective_price'] = (df['your_price'] * (1 - df['discount_pct'] / 100)).round(2)
    df['actual_revenue']  = (df['effective_price'] * df['units_sold']).round(0)
    df['comp_status']     = df['price_gap'].apply(
        lambda x: 'OVERPRICED' if x > 0 else ('UNDERPRICED' if x < 0 else 'AT PARITY')
    )
    df['price_tier'] = pd.cut(
        df['your_price'],
        bins=[0, 500, 1000, 2000, float('inf')],
        labels=['Budget', 'Mid-range', 'Premium', 'Luxury']
    ).astype(str)

    log.info(f"Validated {len(df)} rows, {df['category'].nunique()} categories")
    return df


def write_to_db(conn, df, price_history_path):
    # Main table
    df.to_sql('pricing_data', conn, if_exists='replace', index=False)
    log.info(f"Written pricing_data: {len(df)} rows")

    # Price history (SCD Type 2)
    ph = pd.read_csv(price_history_path)
    ph.to_sql('price_history', conn, if_exists='replace', index=False)
    log.info(f"Written price_history: {len(ph)} rows")

    # Category summary (materialised view equivalent)
    cat_summary = df.groupby('category').agg(
        product_count=('product_id', 'count'),
        total_units=('units_sold', 'sum'),
        total_revenue=('actual_revenue', 'sum'),
        avg_price=('your_price', 'mean'),
        avg_comp_price=('competitor_price', 'mean'),
        avg_margin=('margin_pct', 'mean'),
        avg_discount=('discount_pct', 'mean'),
        avg_rating=('customer_rating', 'mean'),
    ).round(2).reset_index()
    cat_summary['revenue_share'] = (cat_summary['total_revenue'] / cat_summary['total_revenue'].sum() * 100).round(1)
    cat_summary.to_sql('category_summary', conn, if_exists='replace', index=False)
    log.info(f"Written category_summary: {len(cat_summary)} rows")

    conn.commit()


def create_views(conn):
    conn.executescript("""
        DROP VIEW IF EXISTS vw_pricing_dashboard;
        CREATE VIEW vw_pricing_dashboard AS
        SELECT
            p.product_id, p.product_name, p.category,
            p.your_price, p.competitor_price,
            p.price_gap, p.price_gap_pct, p.comp_status,
            p.discount_pct, p.effective_price,
            p.units_sold, p.actual_revenue,
            p.margin_pct, p.customer_rating,
            p.price_tier, p.segment
        FROM pricing_data p;

        DROP VIEW IF EXISTS vw_competitor_gaps;
        CREATE VIEW vw_competitor_gaps AS
        SELECT category,
               ROUND(AVG(your_price),0)         AS your_avg_price,
               ROUND(AVG(competitor_price),0)   AS comp_avg_price,
               ROUND(AVG(price_gap),0)          AS avg_gap,
               ROUND(AVG(price_gap_pct),1)      AS avg_gap_pct,
               SUM(CASE WHEN comp_status='OVERPRICED'  THEN 1 ELSE 0 END) AS overpriced_count,
               SUM(CASE WHEN comp_status='UNDERPRICED' THEN 1 ELSE 0 END) AS underpriced_count
        FROM pricing_data
        GROUP BY category;

        DROP VIEW IF EXISTS vw_discount_impact;
        CREATE VIEW vw_discount_impact AS
        SELECT
            CASE WHEN discount_pct=0 THEN 'No discount'
                 WHEN discount_pct<10 THEN 'Low (1-9%)'
                 WHEN discount_pct<20 THEN 'Medium (10-19%)'
                 ELSE 'High (20%+)' END AS discount_tier,
            COUNT(*)                   AS products,
            ROUND(AVG(units_sold),0)   AS avg_units,
            ROUND(AVG(actual_revenue),0) AS avg_revenue,
            ROUND(AVG(margin_pct),1)   AS avg_margin
        FROM pricing_data
        GROUP BY discount_tier;
    """)
    conn.commit()
    log.info("Created DB views: vw_pricing_dashboard, vw_competitor_gaps, vw_discount_impact")


def create_stored_procedures(conn):
    """SQLite doesn't support stored procs — simulate with parameterised queries."""
    conn.execute("""
        DROP TABLE IF EXISTS sp_discount_simulation;
    """)
    conn.execute("""
        CREATE TABLE sp_discount_simulation (
            run_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category     TEXT,
            base_price   REAL,
            discount_pct REAL,
            elasticity   REAL,
            eff_price    REAL,
            proj_units   REAL,
            proj_revenue REAL,
            created_at   TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    log.info("Created sp_discount_simulation table")


def run_discount_simulation(conn, category, base_price, discount_pct, elasticity, base_units=250):
    """Stored-procedure equivalent — call from Python, results stored in DB."""
    eff_price    = base_price * (1 - discount_pct / 100)
    proj_units   = base_units * (1 + elasticity * (discount_pct / 100))
    proj_revenue = eff_price * proj_units
    conn.execute("""
        INSERT INTO sp_discount_simulation
        (category, base_price, discount_pct, elasticity, eff_price, proj_units, proj_revenue)
        VALUES (?,?,?,?,?,?,?)
    """, (category, base_price, discount_pct, elasticity,
          round(eff_price,2), round(proj_units,0), round(proj_revenue,0)))
    conn.commit()
    return {'eff_price': round(eff_price,2),
            'proj_units': round(proj_units,0),
            'proj_revenue': round(proj_revenue,0)}


def export_results(conn, export_dir='exports'):
    os.makedirs(export_dir, exist_ok=True)
    views = ['vw_pricing_dashboard', 'vw_competitor_gaps', 'vw_discount_impact', 'category_summary']
    for view in views:
        df = pd.read_sql(f"SELECT * FROM {view}", conn)
        out = f"{export_dir}/{view}.csv"
        df.to_csv(out, index=False)
        log.info(f"Exported: {out} ({len(df)} rows)")


def run_pipeline():
    log.info("=" * 55)
    log.info("  PRICING ETL PIPELINE — START")
    log.info("=" * 55)

    cfg  = load_config()
    conn = connect_db(cfg['project']['db_path'])
    df   = load_and_validate(cfg['project']['dataset'])

    write_to_db(conn, df, 'data/price_history.csv')
    create_views(conn)
    create_stored_procedures(conn)

    # Run sample simulations
    cfg_elas = cfg['pricing']['elasticity_by_category']
    for cat, elas in cfg_elas.items():
        avg_price = df[df['category']==cat]['your_price'].mean()
        for disc in [0, 10, 20]:
            run_discount_simulation(conn, cat, avg_price, disc, elas)

    export_results(conn)

    log.info("=" * 55)
    log.info("  PIPELINE COMPLETE")
    log.info(f"  DB: {cfg['project']['db_path']}")
    log.info(f"  Rows: {len(df)}")
    log.info("=" * 55)

    conn.close()
    return df


if __name__ == '__main__':
    run_pipeline()

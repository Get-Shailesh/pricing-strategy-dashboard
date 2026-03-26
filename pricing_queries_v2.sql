-- ================================================================
--  PRICING STRATEGY ANALYSIS v2 — Advanced SQL
--  Covers: CTEs · Window Functions · SCD Type 2 ·
--          Stored Procedures · Cohort Analysis · Pivot
-- ================================================================


-- ────────────────────────────────────────────────────────────
-- SECTION 0: SCHEMA SETUP
-- ────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS pricing_strategy_v2;
USE pricing_strategy_v2;

CREATE TABLE IF NOT EXISTS pricing_data (
    product_id        VARCHAR(10)   PRIMARY KEY,
    product_name      VARCHAR(100),
    category          VARCHAR(50),
    your_price        DECIMAL(10,2),
    competitor_price  DECIMAL(10,2),
    units_sold        INT,
    discount_pct      DECIMAL(5,2),
    customer_rating   DECIMAL(3,1),
    cost_price        DECIMAL(10,2),
    revenue           DECIMAL(15,2),
    profit            DECIMAL(15,2),
    segment           VARCHAR(20),
    month             VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS price_history (
    history_id       INT           PRIMARY KEY,
    product_id       VARCHAR(10),
    product_name     VARCHAR(100),
    category         VARCHAR(50),
    price            DECIMAL(10,2),
    valid_from       DATE,
    valid_to         DATE,
    is_current       TINYINT(1)    DEFAULT 0,
    change_reason    VARCHAR(200),
    FOREIGN KEY (product_id) REFERENCES pricing_data(product_id)
);


-- ────────────────────────────────────────────────────────────
-- SECTION 1: DERIVED COLUMNS VIEW
-- ────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_enriched AS
SELECT
    p.*,
    ROUND(p.your_price - p.competitor_price, 2)                           AS price_gap,
    ROUND((p.your_price - p.competitor_price)/p.competitor_price*100, 1)  AS gap_pct,
    ROUND(p.your_price * (1 - p.discount_pct/100), 2)                     AS effective_price,
    ROUND((p.your_price - p.cost_price)/p.your_price*100, 1)              AS margin_pct,
    ROUND(p.your_price*(1-p.discount_pct/100)*p.units_sold, 0)            AS actual_revenue,
    CASE
        WHEN p.your_price > p.competitor_price THEN 'OVERPRICED'
        WHEN p.your_price < p.competitor_price THEN 'UNDERPRICED'
        ELSE 'AT PARITY'
    END                                                                    AS comp_status,
    CASE
        WHEN p.your_price <  500  THEN 'Budget'
        WHEN p.your_price < 1000  THEN 'Mid-range'
        WHEN p.your_price < 2000  THEN 'Premium'
        ELSE 'Luxury'
    END                                                                    AS price_tier
FROM pricing_data p;


-- ────────────────────────────────────────────────────────────
-- SECTION 2: LAYER 1 — SALES vs PRICE (Window Functions)
-- ────────────────────────────────────────────────────────────

-- Q1: Revenue ranking within each category
SELECT
    product_name, category, your_price, units_sold,
    ROUND(actual_revenue, 0)                                               AS actual_revenue,
    RANK()      OVER (PARTITION BY category ORDER BY actual_revenue DESC)  AS revenue_rank_in_cat,
    PERCENT_RANK() OVER (PARTITION BY category ORDER BY your_price)        AS price_percentile,
    LAG(your_price, 1)  OVER (PARTITION BY category ORDER BY your_price)   AS prev_price,
    LEAD(your_price, 1) OVER (PARTITION BY category ORDER BY your_price)   AS next_price
FROM vw_enriched
ORDER BY category, revenue_rank_in_cat;

-- Q2: Rolling 3-product average revenue per category
WITH ranked AS (
    SELECT product_name, category, actual_revenue,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY your_price) AS rn
    FROM vw_enriched
)
SELECT
    product_name, category, actual_revenue,
    ROUND(AVG(actual_revenue) OVER (
        PARTITION BY category
        ORDER BY rn
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ), 0)                                                                  AS rolling_avg_revenue
FROM ranked
ORDER BY category, rn;

-- Q3: Revenue contribution % using window SUM
SELECT
    category,
    product_name,
    ROUND(actual_revenue, 0)                                               AS revenue,
    ROUND(actual_revenue / SUM(actual_revenue) OVER (PARTITION BY category) * 100, 1) AS pct_of_category,
    ROUND(actual_revenue / SUM(actual_revenue) OVER () * 100, 1)          AS pct_of_total,
    SUM(actual_revenue) OVER (
        PARTITION BY category ORDER BY actual_revenue DESC
        ROWS UNBOUNDED PRECEDING
    )                                                                      AS running_total
FROM vw_enriched
ORDER BY category, actual_revenue DESC;


-- ────────────────────────────────────────────────────────────
-- SECTION 3: LAYER 2 — DEMAND ELASTICITY
-- ────────────────────────────────────────────────────────────

-- Q4: PED midpoint calculation per category using CTEs
WITH price_extremes AS (
    SELECT
        category,
        MIN(your_price)                                                    AS p_low,
        MAX(your_price)                                                    AS p_high,
        FIRST_VALUE(units_sold) OVER (
            PARTITION BY category ORDER BY your_price ASC
        )                                                                  AS q_at_low,
        FIRST_VALUE(units_sold) OVER (
            PARTITION BY category ORDER BY your_price DESC
        )                                                                  AS q_at_high
    FROM pricing_data
    GROUP BY category, units_sold, your_price
),
ped_values AS (
    SELECT DISTINCT
        category, p_low, p_high, q_at_low, q_at_high,
        ABS(
            ((q_at_high - q_at_low) / ((q_at_low  + q_at_high) / 2.0)) /
            NULLIF((p_high - p_low)  / ((p_low  + p_high)  / 2.0), 0)
        )                                                                  AS PED
    FROM price_extremes
    WHERE p_low != p_high
)
SELECT
    category,
    ROUND(PED, 2)                                                          AS elasticity_score,
    CASE WHEN PED > 1 THEN 'Elastic' ELSE 'Inelastic' END                 AS demand_type,
    CASE
        WHEN PED > 2    THEN 'Very price sensitive — compete on price'
        WHEN PED > 1    THEN 'Moderately elastic — test small reductions'
        WHEN PED > 0.5  THEN 'Relatively inelastic — hold or raise price'
        ELSE                 'Price insensitive — strong brand/monopoly'
    END                                                                    AS strategy,
    ROUND(p_high - p_low, 0)                                               AS price_range
FROM ped_values
ORDER BY PED DESC;

-- Q5: Optimal discount by elasticity tier
WITH elas AS (
    SELECT category,
        CASE category
            WHEN 'Electronics'    THEN 1.8
            WHEN 'Clothing'       THEN 2.3
            WHEN 'Home & Kitchen' THEN 1.1
            WHEN 'Sports'         THEN 1.5
            WHEN 'Beauty'         THEN 0.7
            WHEN 'Books'          THEN 0.5
        END                                                                AS elasticity
    FROM (SELECT DISTINCT category FROM pricing_data) c
)
SELECT
    e.category,
    e.elasticity,
    CASE
        WHEN e.elasticity > 2   THEN '15-20% — volume opportunity'
        WHEN e.elasticity > 1   THEN '10-15% — sweet spot'
        WHEN e.elasticity > 0.5 THEN '5-8% — maintain margin'
        ELSE                         '0-3% — price insensitive, no discount needed'
    END                                                                    AS recommended_discount,
    ROUND(AVG(p.your_price), 0)                                            AS current_avg_price,
    ROUND(AVG(p.units_sold), 0)                                            AS current_avg_units
FROM elas e
JOIN pricing_data p ON e.category = p.category
GROUP BY e.category, e.elasticity
ORDER BY e.elasticity DESC;


-- ────────────────────────────────────────────────────────────
-- SECTION 4: LAYER 3 — COMPETITOR BENCHMARKING
-- ────────────────────────────────────────────────────────────

-- Q6: Opportunity matrix with revenue uplift potential
SELECT
    product_name, category, segment,
    your_price, competitor_price,
    ROUND(competitor_price - your_price, 0)                                AS potential_increase,
    units_sold,
    ROUND((competitor_price - your_price) * units_sold, 0)                 AS max_revenue_uplift,
    customer_rating,
    CASE
        WHEN competitor_price > your_price AND customer_rating >= 4.3
             THEN '🚀 RAISE PRICE NOW'
        WHEN competitor_price > your_price AND customer_rating < 4.3
             THEN '⚠️ IMPROVE RATING FIRST'
        WHEN competitor_price < your_price AND units_sold > 400
             THEN '✂️ REDUCE PRICE — HIGH VOLUME'
        ELSE '✅ MONITOR'
    END                                                                    AS action
FROM vw_enriched
WHERE comp_status != 'AT PARITY'
ORDER BY max_revenue_uplift DESC;

-- Q7: Category-level competitive intelligence with z-score
WITH cat_stats AS (
    SELECT category,
           AVG(your_price - competitor_price)           AS avg_gap,
           STDDEV(your_price - competitor_price)        AS stddev_gap
    FROM pricing_data GROUP BY category
)
SELECT
    p.product_name, p.category,
    ROUND(p.your_price - p.competitor_price, 0)        AS gap,
    ROUND((p.your_price - p.competitor_price - c.avg_gap)
          / NULLIF(c.stddev_gap, 0), 2)                AS gap_zscore,
    CASE
        WHEN ABS((p.your_price - p.competitor_price - c.avg_gap)
                 / NULLIF(c.stddev_gap, 0)) > 2
        THEN '🔴 ANOMALY'
        ELSE '🟢 NORMAL'
    END                                                AS anomaly_flag
FROM pricing_data p
JOIN cat_stats c USING (category)
ORDER BY ABS(gap_zscore) DESC;


-- ────────────────────────────────────────────────────────────
-- SECTION 5: LAYER 4 — DISCOUNT STRATEGY (Stored Procedure)
-- ────────────────────────────────────────────────────────────

-- Stored Procedure: Discount impact calculator
DELIMITER $$
DROP PROCEDURE IF EXISTS sp_discount_impact$$
CREATE PROCEDURE sp_discount_impact(
    IN  p_category     VARCHAR(50),
    IN  p_discount_pct DECIMAL(5,2),
    OUT o_eff_price    DECIMAL(10,2),
    OUT o_proj_units   DECIMAL(10,0),
    OUT o_proj_revenue DECIMAL(15,2),
    OUT o_recommendation VARCHAR(200)
)
BEGIN
    DECLARE v_avg_price    DECIMAL(10,2);
    DECLARE v_avg_units    DECIMAL(10,2);
    DECLARE v_elasticity   DECIMAL(5,2);

    SELECT AVG(your_price), AVG(units_sold)
    INTO   v_avg_price, v_avg_units
    FROM   pricing_data
    WHERE  category = p_category;

    SET v_elasticity = CASE p_category
        WHEN 'Electronics'    THEN 1.8
        WHEN 'Clothing'       THEN 2.3
        WHEN 'Home & Kitchen' THEN 1.1
        WHEN 'Sports'         THEN 1.5
        WHEN 'Beauty'         THEN 0.7
        WHEN 'Books'          THEN 0.5
        ELSE 1.4
    END;

    SET o_eff_price    = ROUND(v_avg_price    * (1 - p_discount_pct / 100), 2);
    SET o_proj_units   = ROUND(v_avg_units    * (1 + v_elasticity * p_discount_pct / 100), 0);
    SET o_proj_revenue = ROUND(o_eff_price    * o_proj_units, 0);

    SET o_recommendation = CASE
        WHEN p_discount_pct BETWEEN  8 AND 15 AND v_elasticity > 1
             THEN CONCAT('OPTIMAL: ', p_discount_pct, '% is in the sweet spot for ', p_category)
        WHEN p_discount_pct > 20 AND v_elasticity < 1
             THEN CONCAT('WARNING: ', p_category, ' is inelastic — ', p_discount_pct, '% hurts margin without volume gain')
        WHEN p_discount_pct < 5 AND v_elasticity > 1.5
             THEN CONCAT('OPPORTUNITY: Increase discount — ', p_category, ' is highly elastic')
        ELSE CONCAT('MONITOR: ', p_category, ' at ', p_discount_pct, '% discount')
    END;
END$$
DELIMITER ;

-- Sample calls
CALL sp_discount_impact('Clothing', 10.0, @ep, @pu, @pr, @rec);
SELECT @ep AS eff_price, @pu AS proj_units, @pr AS proj_revenue, @rec AS recommendation;

CALL sp_discount_impact('Books', 25.0, @ep, @pu, @pr, @rec);
SELECT @ep AS eff_price, @pu AS proj_units, @pr AS proj_revenue, @rec AS recommendation;


-- ────────────────────────────────────────────────────────────
-- SECTION 6: LAYER 5 — BUNDLING
-- ────────────────────────────────────────────────────────────

-- Q8: Bundle candidate pairs (high volume + high rating cross-category)
WITH top_products AS (
    SELECT product_id, product_name, category,
           your_price, units_sold, customer_rating, actual_revenue
    FROM vw_enriched
    WHERE customer_rating >= 4.3
      AND units_sold >= 350
)
SELECT
    a.product_name                                     AS product_1,
    b.product_name                                     AS product_2,
    a.category                                         AS cat_1,
    b.category                                         AS cat_2,
    ROUND(a.your_price + b.your_price, 0)              AS full_price,
    ROUND((a.your_price + b.your_price) * 0.90, 0)    AS bundle_price_10pct_off,
    ROUND((a.units_sold + b.units_sold) / 2, 0)       AS est_bundle_units,
    ROUND((a.your_price + b.your_price) * 0.90
          * (a.units_sold + b.units_sold) / 2, 0)     AS est_bundle_revenue
FROM top_products a
JOIN top_products b
    ON a.category < b.category
   AND a.category IN ('Electronics','Sports')
   AND b.category IN ('Beauty','Clothing')
ORDER BY est_bundle_revenue DESC
LIMIT 10;

-- Q9: Discount decay analysis — where does ROI turn negative?
WITH discount_sims AS (
    SELECT
        d.discount_pct,
        ROUND(AVG(p.your_price) * (1 - d.discount_pct/100), 0)                    AS eff_price,
        ROUND(AVG(p.units_sold) * (1 + 1.4 * d.discount_pct/100), 0)              AS proj_units,
        ROUND(AVG(p.your_price) * (1-d.discount_pct/100)
              * AVG(p.units_sold) * (1 + 1.4*d.discount_pct/100), 0)             AS proj_revenue
    FROM pricing_data p
    CROSS JOIN (
        SELECT 0  AS discount_pct UNION ALL SELECT 5  UNION ALL SELECT 10
        UNION ALL SELECT 15 UNION ALL SELECT 20 UNION ALL SELECT 25
        UNION ALL SELECT 30 UNION ALL SELECT 35 UNION ALL SELECT 40
        UNION ALL SELECT 50
    ) d
    GROUP BY d.discount_pct
),
with_baseline AS (
    SELECT *,
           FIRST_VALUE(proj_revenue) OVER (ORDER BY discount_pct)          AS baseline_revenue,
           LAG(proj_revenue, 1)      OVER (ORDER BY discount_pct)          AS prev_revenue
    FROM discount_sims
)
SELECT
    discount_pct,
    eff_price,
    proj_units,
    proj_revenue,
    ROUND(proj_revenue - baseline_revenue, 0)                              AS revenue_vs_baseline,
    ROUND((proj_revenue - prev_revenue) / NULLIF(prev_revenue, 0)*100, 1) AS marginal_change_pct,
    CASE
        WHEN proj_revenue > LAG(proj_revenue,1) OVER (ORDER BY discount_pct)
        THEN 'INCREASING'
        ELSE 'DECREASING — past sweet spot'
    END                                                                    AS trend
FROM with_baseline
ORDER BY discount_pct;


-- ────────────────────────────────────────────────────────────
-- SECTION 7: SCD TYPE 2 — PRICE HISTORY
-- ────────────────────────────────────────────────────────────

-- Q10: Current prices with full history trail
SELECT
    ph.product_id,
    ph.product_name,
    ph.category,
    ph.price                                           AS historical_price,
    ph.valid_from,
    ph.valid_to,
    DATEDIFF(ph.valid_to, ph.valid_from)               AS days_at_price,
    ph.is_current,
    ph.change_reason,
    pd.your_price                                      AS current_price,
    ROUND(pd.your_price - ph.price, 0)                 AS total_price_change,
    ROUND((pd.your_price - ph.price)/ph.price*100, 1)  AS total_change_pct
FROM price_history ph
JOIN pricing_data  pd ON ph.product_id = pd.product_id
ORDER BY ph.product_id, ph.valid_from;

-- Q11: Price erosion analysis (how much have prices dropped?)
WITH price_changes AS (
    SELECT
        product_id, product_name, category,
        FIRST_VALUE(price) OVER (PARTITION BY product_id ORDER BY valid_from)  AS launch_price,
        LAST_VALUE(price)  OVER (
            PARTITION BY product_id ORDER BY valid_from
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                                                                       AS current_price,
        COUNT(*) OVER (PARTITION BY product_id)                                AS num_changes
    FROM price_history
)
SELECT DISTINCT
    product_id, product_name, category,
    launch_price, current_price,
    ROUND(current_price - launch_price, 0)              AS price_change,
    ROUND((current_price-launch_price)/launch_price*100, 1) AS change_pct,
    num_changes,
    CASE
        WHEN (current_price - launch_price) < -200 THEN 'Heavy erosion (>₹200 drop)'
        WHEN (current_price - launch_price) < 0    THEN 'Moderate erosion'
        WHEN (current_price - launch_price) = 0    THEN 'Stable pricing'
        ELSE 'Price increase'
    END                                                  AS price_trend
FROM price_changes
ORDER BY change_pct;


-- ────────────────────────────────────────────────────────────
-- SECTION 8: SEGMENT & COHORT ANALYSIS
-- ────────────────────────────────────────────────────────────

-- Q12: Revenue pivot — Category × Price Tier
SELECT
    category,
    ROUND(SUM(CASE WHEN price_tier='Budget'    THEN actual_revenue END), 0) AS budget_rev,
    ROUND(SUM(CASE WHEN price_tier='Mid-range' THEN actual_revenue END), 0) AS midrange_rev,
    ROUND(SUM(CASE WHEN price_tier='Premium'   THEN actual_revenue END), 0) AS premium_rev,
    ROUND(SUM(CASE WHEN price_tier='Luxury'    THEN actual_revenue END), 0) AS luxury_rev,
    ROUND(SUM(actual_revenue), 0)                                            AS total_rev
FROM vw_enriched
GROUP BY category
ORDER BY total_rev DESC;

-- Q13: Segment profitability (Budget/Mid-range/Premium/Luxury buyers)
SELECT
    segment,
    COUNT(*)                                           AS products,
    ROUND(AVG(your_price), 0)                          AS avg_price,
    ROUND(AVG(margin_pct), 1)                          AS avg_margin_pct,
    SUM(units_sold)                                    AS total_units,
    ROUND(SUM(actual_revenue), 0)                      AS total_revenue,
    ROUND(AVG(customer_rating), 2)                     AS avg_rating,
    ROUND(AVG(discount_pct), 1)                        AS avg_discount,
    ROUND(AVG(your_price - competitor_price), 0)       AS avg_price_gap
FROM vw_enriched
GROUP BY segment
ORDER BY avg_price;

-- Q14: Monthly revenue trend (cohort)
SELECT
    month,
    COUNT(DISTINCT category)                           AS categories_active,
    SUM(units_sold)                                    AS total_units,
    ROUND(SUM(actual_revenue), 0)                      AS total_revenue,
    ROUND(AVG(your_price), 0)                          AS avg_price,
    ROUND(AVG(margin_pct), 1)                          AS avg_margin,
    SUM(SUM(actual_revenue)) OVER (ORDER BY
        CASE month WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 ELSE 3 END
    )                                                  AS cumulative_revenue
FROM vw_enriched
GROUP BY month
ORDER BY CASE month WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 ELSE 3 END;


-- ────────────────────────────────────────────────────────────
-- SECTION 9: FINAL MASTER REPORT
-- ────────────────────────────────────────────────────────────

-- Q15: Executive summary — all KPIs in one query
WITH summary AS (
    SELECT
        category,
        COUNT(*)                                                           AS products,
        ROUND(AVG(your_price),0)                                           AS avg_price,
        ROUND(AVG(competitor_price),0)                                     AS comp_price,
        ROUND(AVG(your_price - competitor_price),0)                        AS price_gap,
        SUM(units_sold)                                                    AS units,
        ROUND(SUM(actual_revenue),0)                                       AS revenue,
        ROUND(AVG(margin_pct),1)                                           AS margin_pct,
        ROUND(AVG(discount_pct),1)                                         AS avg_disc,
        ROUND(AVG(customer_rating),2)                                      AS rating,
        ROUND(SUM(actual_revenue)/SUM(SUM(actual_revenue)) OVER()*100, 1) AS rev_share
    FROM vw_enriched
    GROUP BY category
)
SELECT
    category, products, avg_price, comp_price,
    price_gap, units, revenue, margin_pct,
    avg_disc, rating, rev_share,
    DENSE_RANK() OVER (ORDER BY revenue DESC)  AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY margin_pct DESC) AS margin_rank,
    CASE
        WHEN price_gap > 100   THEN '↓ Reduce price'
        WHEN price_gap < -100  THEN '↑ Raise price'
        ELSE                        '→ Hold'
    END                                        AS price_action,
    CASE
        WHEN avg_disc > 12     THEN '⚠ Over-discounting'
        WHEN avg_disc BETWEEN 8 AND 12 THEN '✅ Optimal range'
        ELSE                        '💡 Room to discount'
    END                                        AS discount_health
FROM summary
ORDER BY revenue DESC;

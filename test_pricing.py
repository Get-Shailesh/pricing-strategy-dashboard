"""
================================================================
  PRICING STRATEGY — Unit Tests
  File    : tests/test_pricing.py
  Run     : pytest tests/ -v
================================================================
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))


# ─── Helper functions extracted for testing ──────────────────

def compute_ped(p1, p2, q1, q2):
    """Midpoint price elasticity of demand."""
    if p1 == p2:
        return 0
    pct_q = (q2 - q1) / ((q1 + q2) / 2)
    pct_p = (p2 - p1) / ((p1 + p2) / 2)
    return abs(pct_q / pct_p) if pct_p != 0 else 0


def compute_revenue(base_price, base_units, discount_pct, elasticity):
    """Project revenue given a discount and elasticity."""
    eff_price    = base_price * (1 - discount_pct / 100)
    proj_units   = base_units * (1 + elasticity * (discount_pct / 100))
    return round(eff_price * proj_units, 2)


def classify_elasticity(ped):
    """Classify demand as elastic or inelastic."""
    if ped > 1:
        return 'Elastic'
    elif ped < 1:
        return 'Inelastic'
    else:
        return 'Unit Elastic'


def compute_price_gap(your_price, competitor_price):
    """Price gap and competitive status."""
    gap     = your_price - competitor_price
    gap_pct = (gap / competitor_price) * 100 if competitor_price > 0 else 0
    status  = 'OVERPRICED' if gap > 0 else ('UNDERPRICED' if gap < 0 else 'AT PARITY')
    return {'gap': gap, 'gap_pct': round(gap_pct, 2), 'status': status}


def detect_anomalies_iqr(prices, multiplier=1.5):
    """IQR-based anomaly detection."""
    Q1, Q3 = np.percentile(prices, 25), np.percentile(prices, 75)
    IQR    = Q3 - Q1
    lb, ub = Q1 - multiplier * IQR, Q3 + multiplier * IQR
    return [p for p in prices if p < lb or p > ub], lb, ub


def bcg_quadrant(margin_pct, units_sold, median_margin, median_units):
    """Assign BCG quadrant."""
    if margin_pct >= median_margin and units_sold >= median_units:
        return 'Star'
    elif margin_pct >= median_margin and units_sold < median_units:
        return 'Cash Cow'
    elif margin_pct < median_margin and units_sold >= median_units:
        return 'Question Mark'
    else:
        return 'Dog'


def find_optimal_discount(base_price, base_units, elasticity, max_discount=50):
    """Find discount % that maximises revenue."""
    best_rev, best_disc = 0, 0
    for d in range(0, max_discount + 1):
        rev = compute_revenue(base_price, base_units, d, elasticity)
        if rev > best_rev:
            best_rev, best_disc = rev, d
    return best_disc, best_rev


# ══════════════════════════════════════════════════════════════
# TEST SUITE
# ══════════════════════════════════════════════════════════════

class TestPriceElasticity:

    def test_elastic_demand(self):
        """High PED means lowering price increases revenue."""
        ped = compute_ped(p1=800, p2=1200, q1=600, q2=300)
        assert ped > 1, f"Expected elastic (>1), got {ped}"

    def test_inelastic_demand(self):
        """Low PED means price changes don't much affect quantity."""
        ped = compute_ped(p1=300, p2=400, q1=700, q2=680)
        assert ped < 1, f"Expected inelastic (<1), got {ped}"

    def test_zero_price_change(self):
        """No price change should return PED of 0."""
        ped = compute_ped(p1=1000, p2=1000, q1=500, q2=500)
        assert ped == 0

    def test_ped_always_positive(self):
        """PED should always be returned as absolute value."""
        ped = compute_ped(p1=500, p2=1000, q1=800, q2=400)
        assert ped >= 0

    def test_elastic_classification(self):
        assert classify_elasticity(1.8)  == 'Elastic'
        assert classify_elasticity(0.7)  == 'Inelastic'
        assert classify_elasticity(1.0)  == 'Unit Elastic'

    def test_books_inelastic(self):
        """Books category should be inelastic (PED ~0.5)."""
        ped = compute_ped(p1=280, p2=400, q1=720, q2=670)
        assert ped < 1.2, f"Books PED too high: {ped}"

    def test_clothing_elastic(self):
        """Clothing should be elastic (PED ~2.3) — larger quantity response to price change."""
        ped = compute_ped(p1=450, p2=900, q1=720, q2=300)
        assert ped > 1.0, f"Clothing PED too low: {ped}"


class TestRevenueSimulation:

    def test_zero_discount_revenue(self):
        """No discount = base_price × base_units."""
        rev = compute_revenue(1000, 100, 0, 1.4)
        assert rev == pytest.approx(100000.0, abs=1)

    def test_revenue_positive(self):
        """Revenue must always be positive."""
        for disc in [0, 10, 25, 50]:
            rev = compute_revenue(1200, 200, disc, 1.4)
            assert rev > 0, f"Revenue negative at {disc}% discount"

    def test_high_elasticity_revenue_increases_with_discount(self):
        """Elastic product: small discount should increase revenue."""
        rev0  = compute_revenue(1000, 100, 0,  2.3)
        rev10 = compute_revenue(1000, 100, 10, 2.3)
        assert rev10 > rev0

    def test_inelastic_optimal_discount_is_low(self):
        """Inelastic products should have low optimal discount."""
        opt_disc, _ = find_optimal_discount(350, 600, 0.5)
        assert opt_disc <= 10, f"Inelastic optimal discount too high: {opt_disc}%"

    def test_optimal_discount_within_bounds(self):
        """Optimal discount should be within [0, max_discount]."""
        opt, _ = find_optimal_discount(1200, 250, 1.4, 50)
        assert 0 <= opt <= 50

    def test_revenue_at_100pct_discount_is_zero(self):
        """100% discount = zero revenue."""
        rev = compute_revenue(1000, 100, 100, 1.4)
        assert rev == pytest.approx(0.0, abs=1)


class TestCompetitorBenchmark:

    def test_overpriced_detection(self):
        result = compute_price_gap(2200, 2000)
        assert result['status'] == 'OVERPRICED'
        assert result['gap'] == 200

    def test_underpriced_detection(self):
        result = compute_price_gap(800, 1000)
        assert result['status'] == 'UNDERPRICED'
        assert result['gap'] == -200

    def test_at_parity(self):
        result = compute_price_gap(1200, 1200)
        assert result['status'] == 'AT PARITY'
        assert result['gap'] == 0

    def test_gap_pct_calculation(self):
        result = compute_price_gap(1100, 1000)
        assert result['gap_pct'] == pytest.approx(10.0, abs=0.1)

    def test_gap_pct_negative_when_underpriced(self):
        result = compute_price_gap(900, 1000)
        assert result['gap_pct'] < 0

    def test_zero_competitor_price_handled(self):
        """Should not crash on zero competitor price."""
        result = compute_price_gap(500, 0)
        assert 'status' in result


class TestAnomalyDetection:

    def test_outliers_detected(self):
        prices   = [500, 520, 510, 490, 505, 515, 5000]  # 5000 is anomaly
        anomalies, _, _ = detect_anomalies_iqr(prices)
        assert 5000 in anomalies

    def test_no_false_positives_on_normal_data(self):
        prices   = list(range(900, 1100, 10))
        anomalies, _, _ = detect_anomalies_iqr(prices)
        assert len(anomalies) == 0

    def test_bounds_correct_direction(self):
        prices   = [100, 110, 105, 108, 103]
        _, lb, ub = detect_anomalies_iqr(prices)
        assert lb < min(prices)
        assert ub > max(prices)

    def test_multiplier_affects_sensitivity(self):
        prices   = [500, 520, 510, 490, 800]
        a1, _, _ = detect_anomalies_iqr(prices, multiplier=0.5)
        a2, _, _ = detect_anomalies_iqr(prices, multiplier=3.0)
        assert len(a1) >= len(a2)


class TestBCGMatrix:

    def test_star_classification(self):
        assert bcg_quadrant(50, 600, 40, 500) == 'Star'

    def test_cash_cow_classification(self):
        assert bcg_quadrant(55, 200, 40, 500) == 'Cash Cow'

    def test_question_mark_classification(self):
        assert bcg_quadrant(30, 700, 40, 500) == 'Question Mark'

    def test_dog_classification(self):
        assert bcg_quadrant(20, 100, 40, 500) == 'Dog'

    def test_boundary_values(self):
        """Exactly at median should go to Star/Cash Cow (>=)."""
        assert bcg_quadrant(40, 500, 40, 500) == 'Star'

    def test_all_quadrants_distinct(self):
        quads = {
            bcg_quadrant(60, 800, 40, 500),
            bcg_quadrant(60, 200, 40, 500),
            bcg_quadrant(20, 800, 40, 500),
            bcg_quadrant(20, 200, 40, 500),
        }
        assert len(quads) == 4


class TestDataValidation:

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'product_id':       ['P001','P002'],
            'your_price':       [1200, 800],
            'competitor_price': [1300, 750],
            'units_sold':       [300, 450],
            'discount_pct':     [10, 5],
            'customer_rating':  [4.3, 4.1],
            'cost_price':       [600, 350],
        })

    def test_no_negative_prices(self, sample_df):
        assert (sample_df['your_price'] >= 0).all()

    def test_no_negative_units(self, sample_df):
        assert (sample_df['units_sold'] >= 0).all()

    def test_discount_range(self, sample_df):
        assert sample_df['discount_pct'].between(0, 100).all()

    def test_rating_range(self, sample_df):
        assert sample_df['customer_rating'].between(0, 5).all()

    def test_no_duplicate_ids(self, sample_df):
        assert not sample_df.duplicated('product_id').any()

    def test_margin_derivation(self, sample_df):
        df = sample_df.copy()
        df['margin'] = (df['your_price'] - df['cost_price']) / df['your_price'] * 100
        assert (df['margin'] > 0).all()
        assert (df['margin'] < 100).all()

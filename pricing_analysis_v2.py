"""
================================================================
  PRICING STRATEGY — Advanced Analytics + ML
  File    : python/pricing_analysis.py
  Covers  : EDA · Elasticity · Competitor · Discount ·
            Anomaly Detection · A/B Test · ML Price Prediction
            BCG Matrix · Segment Analysis
================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
import seaborn as sns
import sqlite3
import yaml
import warnings
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
warnings.filterwarnings('ignore')

# ── Style ─────────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#0d0f14', 'axes.facecolor': '#14171f',
    'axes.edgecolor': '#2a2d38',   'axes.labelcolor': '#8b90a0',
    'xtick.color': '#555b6e',      'ytick.color': '#555b6e',
    'text.color': '#e8eaf0',       'grid.color': '#1c2030',
    'grid.linestyle': '--',        'grid.linewidth': 0.5,
    'font.family': 'DejaVu Sans',  'font.size': 10,
})
CAT_COLORS = {
    'Electronics':'#3b82f6','Clothing':'#4ade80','Home & Kitchen':'#f59e0b',
    'Sports':'#f472b6','Beauty':'#a78bfa','Books':'#34d399'
}

def load_config():
    with open('config/config.yaml') as f:
        return yaml.safe_load(f)

def load_data(cfg):
    conn = sqlite3.connect(cfg['project']['db_path'])
    df   = pd.read_sql("SELECT * FROM pricing_data", conn)
    ph   = pd.read_sql("SELECT * FROM price_history", conn)
    conn.close()
    return df, ph


# ══════════════════════════════════════════════════════════════
# 1. EDA
# ══════════════════════════════════════════════════════════════
def run_eda(df):
    print("\n" + "="*60)
    print("  EDA SUMMARY")
    print("="*60)
    print(f"  Rows          : {len(df)}")
    print(f"  Categories    : {df['category'].nunique()}")
    print(f"  Total Revenue : ₹{df['actual_revenue'].sum():,.0f}")
    print(f"  Total Units   : {df['units_sold'].sum():,}")
    print(f"  Avg Margin    : {df['margin_pct'].mean():.1f}%")
    print(f"  Avg Rating    : {df['customer_rating'].mean():.2f}")
    print(f"\nNull values:\n{df.isnull().sum()[df.isnull().sum()>0]}")

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle('Exploratory Data Analysis', fontsize=14, fontweight='bold')

    # Revenue by category
    rev = df.groupby('category')['actual_revenue'].sum().sort_values(ascending=True)
    axes[0,0].barh(rev.index, rev.values, color=[CAT_COLORS[c] for c in rev.index])
    axes[0,0].set_title('Revenue by Category')
    axes[0,0].xaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'₹{x/1e5:.1f}L'))

    # Price distribution
    for cat, grp in df.groupby('category'):
        axes[0,1].hist(grp['your_price'], bins=8, alpha=0.5, color=CAT_COLORS[cat], label=cat)
    axes[0,1].set_title('Price Distribution by Category')
    axes[0,1].set_xlabel('Price (₹)')
    axes[0,1].legend(fontsize=7)

    # Rating vs Revenue scatter
    axes[0,2].scatter(df['customer_rating'], df['actual_revenue'],
                      c=[CAT_COLORS[c] for c in df['category']], s=50, alpha=0.7)
    axes[0,2].set_title('Rating vs Revenue')
    axes[0,2].set_xlabel('Customer Rating')
    axes[0,2].set_ylabel('Revenue (₹)')
    axes[0,2].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'₹{x/1e5:.1f}L'))

    # Margin by segment
    seg_margin = df.groupby('price_tier')['margin_pct'].mean().reindex(['Budget','Mid-range','Premium','Luxury'])
    seg_colors = ['#34d399','#3b82f6','#f59e0b','#f472b6']
    axes[1,0].bar(seg_margin.index, seg_margin.values, color=seg_colors)
    axes[1,0].set_title('Avg Margin % by Price Tier')
    axes[1,0].set_ylabel('Margin %')

    # Discount distribution
    axes[1,1].hist(df['discount_pct'], bins=10, color='#3b82f6', alpha=0.8)
    axes[1,1].set_title('Discount % Distribution')
    axes[1,1].set_xlabel('Discount %')

    # Units sold box plot
    cats = list(CAT_COLORS.keys())
    data = [df[df['category']==c]['units_sold'].values for c in cats]
    bp = axes[1,2].boxplot(data, patch_artist=True, labels=[c[:7] for c in cats])
    for patch, cat in zip(bp['boxes'], cats):
        patch.set_facecolor(CAT_COLORS[cat])
        patch.set_alpha(0.7)
    axes[1,2].set_title('Units Sold Distribution')

    plt.tight_layout()
    plt.savefig('data/01_eda.png', dpi=150, bbox_inches='tight', facecolor='#0d0f14')
    plt.close()
    print("  Saved: data/01_eda.png")


# ══════════════════════════════════════════════════════════════
# 2. BCG MATRIX (Stars / Cash Cows / Question Marks / Dogs)
# ══════════════════════════════════════════════════════════════
def run_bcg_matrix(df):
    print("\n" + "="*60)
    print("  BCG MATRIX — Margin vs Volume")
    print("="*60)

    median_margin = df['margin_pct'].median()
    median_units  = df['units_sold'].median()

    def quadrant(row):
        if row['margin_pct'] >= median_margin and row['units_sold'] >= median_units:
            return 'Star'
        elif row['margin_pct'] >= median_margin and row['units_sold'] < median_units:
            return 'Cash Cow'
        elif row['margin_pct'] < median_margin and row['units_sold'] >= median_units:
            return 'Question Mark'
        else:
            return 'Dog'

    df['bcg_quad'] = df.apply(quadrant, axis=1)
    print(df.groupby('bcg_quad')[['product_id','actual_revenue']].agg({'product_id':'count','actual_revenue':'sum'}))

    fig, ax = plt.subplots(figsize=(12, 8))
    quad_colors = {'Star':'#4ade80','Cash Cow':'#3b82f6','Question Mark':'#f59e0b','Dog':'#f87171'}
    for quad, grp in df.groupby('bcg_quad'):
        ax.scatter(grp['margin_pct'], grp['units_sold'],
                   c=quad_colors[quad], s=grp['actual_revenue']/3000,
                   alpha=0.75, label=quad, edgecolors='none')
    ax.axvline(median_margin, color='#555b6e', linestyle='--', linewidth=1)
    ax.axhline(median_units,  color='#555b6e', linestyle='--', linewidth=1)

    ax.text(median_margin+1, df['units_sold'].max()*0.92, '⭐ STARS',         fontsize=9, color='#4ade80')
    ax.text(median_margin+1, df['units_sold'].min()*1.05, '🐄 CASH COWS',     fontsize=9, color='#3b82f6')
    ax.text(df['margin_pct'].min(), df['units_sold'].max()*0.92, '❓ QUESTION MARKS', fontsize=9, color='#f59e0b')
    ax.text(df['margin_pct'].min(), df['units_sold'].min()*1.05, '🐕 DOGS',         fontsize=9, color='#f87171')

    ax.set_xlabel('Profit Margin %')
    ax.set_ylabel('Units Sold')
    ax.set_title('BCG Matrix — Margin vs Volume (bubble size = revenue)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('data/02_bcg_matrix.png', dpi=150, bbox_inches='tight', facecolor='#0d0f14')
    plt.close()
    print("  Saved: data/02_bcg_matrix.png")
    return df


# ══════════════════════════════════════════════════════════════
# 3. DEMAND ELASTICITY (per category)
# ══════════════════════════════════════════════════════════════
def run_elasticity(df, cfg):
    print("\n" + "="*60)
    print("  DEMAND ELASTICITY (per-category PED)")
    print("="*60)

    elas_cfg = cfg['pricing']['elasticity_by_category']
    results  = []
    for cat in df['category'].unique():
        grp = df[df['category']==cat].sort_values('your_price')
        if len(grp) < 2:
            continue
        p1, p2 = grp['your_price'].iloc[0],  grp['your_price'].iloc[-1]
        q1, q2 = grp['units_sold'].iloc[0],  grp['units_sold'].iloc[-1]
        if p1 == p2: continue
        pct_q  = (q2-q1)/((q1+q2)/2)
        pct_p  = (p2-p1)/((p1+p2)/2)
        ped    = abs(pct_q/pct_p) if pct_p != 0 else 0
        cfg_e  = elas_cfg.get(cat, ped)
        results.append({'category':cat,'computed_PED':round(ped,2),
                        'config_PED':cfg_e, 'type':'Elastic' if cfg_e>1 else 'Inelastic',
                        'action':'Reduce price for volume' if cfg_e>1 else 'Raise price safely'})

    elas_df = pd.DataFrame(results)
    print(elas_df[['category','config_PED','type','action']].to_string(index=False))

    # Revenue curves per category
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle('Revenue Curves by Category (Per-Category Elasticity)', fontsize=13, fontweight='bold')
    for ax, (cat, grp) in zip(axes.flatten(), df.groupby('category')):
        elas    = elas_cfg.get(cat, 1.4)
        base_p  = grp['your_price'].mean()
        base_u  = grp['units_sold'].mean()
        discs   = np.arange(0, 51)
        revs    = [base_p*(1-d/100) * base_u*(1+elas*d/100) for d in discs]
        opt_d   = discs[np.argmax(revs)]
        ax.plot(discs, revs, color=CAT_COLORS[cat], linewidth=2)
        ax.axvline(opt_d, color='#f87171', linestyle='--', linewidth=1)
        ax.fill_between(discs, revs, alpha=0.08, color=CAT_COLORS[cat])
        ax.set_title(f'{cat} (PED={elas})', color=CAT_COLORS[cat], fontsize=10)
        ax.set_xlabel('Discount %')
        ax.set_ylabel('Revenue')
        ax.text(opt_d+1, max(revs)*0.97, f'Optimal: {opt_d}%', fontsize=8, color='#f87171')
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'₹{x/1000:.0f}K'))
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('data/03_elasticity_curves.png', dpi=150, bbox_inches='tight', facecolor='#0d0f14')
    plt.close()
    print("  Saved: data/03_elasticity_curves.png")
    return elas_df


# ══════════════════════════════════════════════════════════════
# 4. ANOMALY DETECTION
# ══════════════════════════════════════════════════════════════
def run_anomaly_detection(df, cfg):
    print("\n" + "="*60)
    print("  ANOMALY DETECTION (IQR Method)")
    print("="*60)

    mult    = cfg['anomaly_detection']['iqr_multiplier']
    anomalies = []
    for cat, grp in df.groupby('category'):
        Q1, Q3 = grp['your_price'].quantile(0.25), grp['your_price'].quantile(0.75)
        IQR    = Q3 - Q1
        lb, ub = Q1 - mult*IQR, Q3 + mult*IQR
        flags  = grp[(grp['your_price'] < lb) | (grp['your_price'] > ub)]
        for _, row in flags.iterrows():
            direction = 'HIGH' if row['your_price'] > ub else 'LOW'
            anomalies.append({
                'product_id':row['product_id'],'product_name':row['product_name'],
                'category':cat,'your_price':row['your_price'],
                'lower_bound':round(lb,0),'upper_bound':round(ub,0),
                'direction':direction
            })

    anom_df = pd.DataFrame(anomalies) if anomalies else pd.DataFrame()
    if not anom_df.empty:
        print(f"\nAnomalous products detected: {len(anom_df)}")
        print(anom_df[['product_name','category','your_price','lower_bound','upper_bound','direction']].to_string(index=False))
    else:
        print("No pricing anomalies detected.")

    # Z-score heatmap
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    price_pivot = df.groupby(['category','price_tier'])['your_price'].mean().unstack(fill_value=0)
    sns.heatmap(price_pivot, ax=axes[0], cmap='Blues', fmt='.0f', annot=True,
                linewidths=0.5, cbar_kws={'label':'Avg Price (₹)'})
    axes[0].set_title('Price Heatmap: Category × Price Tier', fontsize=11, fontweight='bold')

    z_scores = df.copy()
    z_scores['price_zscore'] = stats.zscore(df['your_price'])
    colors = ['#f87171' if abs(z)>2 else '#4ade80' if abs(z)>1 else '#555b6e' for z in z_scores['price_zscore']]
    axes[1].scatter(range(len(z_scores)), z_scores['price_zscore'], c=colors, s=40, alpha=0.8)
    axes[1].axhline(2,  color='#f87171', linestyle='--', linewidth=1, label='Anomaly threshold (±2σ)')
    axes[1].axhline(-2, color='#f87171', linestyle='--', linewidth=1)
    axes[1].axhline(0,  color='#8b90a0', linestyle='-',  linewidth=0.5)
    axes[1].set_title('Price Z-Scores (Anomaly Detection)', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Product Index')
    axes[1].set_ylabel('Z-Score')
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('data/04_anomaly_detection.png', dpi=150, bbox_inches='tight', facecolor='#0d0f14')
    plt.close()
    print("  Saved: data/04_anomaly_detection.png")
    return anom_df


# ══════════════════════════════════════════════════════════════
# 5. A/B TEST SIMULATION
# ══════════════════════════════════════════════════════════════
def run_ab_test(df, cfg):
    print("\n" + "="*60)
    print("  A/B TEST SIMULATION")
    print("="*60)

    np.random.seed(cfg['ml']['random_state'])
    n    = cfg['ab_test']['control_group_size']
    alpha= 1 - cfg['ab_test']['confidence_level']

    results = []
    for cat, grp in df.groupby('category'):
        base_price = grp['your_price'].mean()
        elas       = cfg['pricing']['elasticity_by_category'].get(cat, 1.4)
        opt_disc   = 12 if elas > 1 else 5

        # Control: current price, Treatment: optimised price
        control_rev   = np.random.normal(base_price * grp['units_sold'].mean(), base_price * 50, n)
        treat_price   = base_price * (1 - opt_disc/100)
        treat_units   = grp['units_sold'].mean() * (1 + elas * opt_disc/100)
        treatment_rev = np.random.normal(treat_price * treat_units, treat_price * 45, n)

        t_stat, p_val = stats.ttest_ind(control_rev, treatment_rev)
        significant   = p_val < alpha
        lift          = (treatment_rev.mean() - control_rev.mean()) / control_rev.mean() * 100

        results.append({
            'category': cat,
            'control_avg_rev': round(control_rev.mean(), 0),
            'treatment_avg_rev': round(treatment_rev.mean(), 0),
            'lift_pct': round(lift, 1),
            'p_value': round(p_val, 4),
            'significant': '✅ YES' if significant else '❌ NO',
            'recommendation': f'Apply {opt_disc}% discount' if significant and lift > 0 else 'Hold current pricing'
        })

    ab_df = pd.DataFrame(results)
    print(ab_df[['category','lift_pct','p_value','significant','recommendation']].to_string(index=False))

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    x  = np.arange(len(ab_df))
    w  = 0.35
    b1 = ax.bar(x - w/2, ab_df['control_avg_rev'],   w, label='Control (current)', color='#555b6e', alpha=0.8)
    b2 = ax.bar(x + w/2, ab_df['treatment_avg_rev'], w, label='Treatment (optimised)', color='#3b82f6', alpha=0.8)
    for i, (_, row) in enumerate(ab_df.iterrows()):
        color = '#4ade80' if row['lift_pct'] > 0 else '#f87171'
        ax.text(i, max(row['control_avg_rev'], row['treatment_avg_rev']) + 2000,
                f"{row['lift_pct']:+.1f}%\n{row['significant']}", ha='center', fontsize=8, color=color)
    ax.set_xticks(x)
    ax.set_xticklabels(ab_df['category'], rotation=15, ha='right')
    ax.set_title('A/B Test — Control vs Optimised Pricing (n=500 per group)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Avg Revenue per Session (₹)')
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'₹{x:,.0f}'))
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('data/05_ab_test.png', dpi=150, bbox_inches='tight', facecolor='#0d0f14')
    plt.close()
    print("  Saved: data/05_ab_test.png")
    return ab_df


# ══════════════════════════════════════════════════════════════
# 6. ML PRICE PREDICTION
# ══════════════════════════════════════════════════════════════
def run_ml_pricing(df, cfg):
    print("\n" + "="*60)
    print("  ML PRICE PREDICTION")
    print("="*60)

    ml_cfg = cfg['ml']
    le     = LabelEncoder()
    df_ml  = df.copy()
    df_ml['category_enc'] = le.fit_transform(df_ml['category'])
    df_ml['segment_enc']  = le.fit_transform(df_ml['segment'])

    features = ['competitor_price','cost_price','units_sold','discount_pct',
                'customer_rating','category_enc','segment_enc','margin_pct']
    X = df_ml[features]
    y = df_ml['your_price']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=ml_cfg['test_size'], random_state=ml_cfg['random_state']
    )

    scaler  = StandardScaler()
    Xs_tr   = scaler.fit_transform(X_train)
    Xs_te   = scaler.transform(X_test)

    models = {
        'Linear Regression':     LinearRegression(),
        'Ridge Regression':      Ridge(alpha=1.0),
        'Random Forest':         RandomForestRegressor(n_estimators=100, random_state=42),
        'Gradient Boosting':     GradientBoostingRegressor(n_estimators=100, random_state=42),
    }

    results = {}
    for name, model in models.items():
        Xtr = Xs_tr if 'Regression' in name else X_train
        Xte = Xs_te if 'Regression' in name else X_test
        model.fit(Xtr, y_train)
        preds = model.predict(Xte)
        mae   = mean_absolute_error(y_test, preds)
        r2    = r2_score(y_test, preds)
        rmse  = np.sqrt(mean_squared_error(y_test, preds))
        results[name] = {'model':model,'MAE':round(mae,0),'R2':round(r2,3),'RMSE':round(rmse,0),
                         'scaler':scaler if 'Regression' in name else None,
                         'preds':preds, 'features':features, 'Xte':X_test}
        print(f"  {name:<25} MAE=₹{mae:,.0f}  R²={r2:.3f}  RMSE=₹{rmse:,.0f}")

    best_name = max(results, key=lambda k: results[k]['R2'])
    best      = results[best_name]
    print(f"\n  Best model: {best_name} (R²={best['R2']})")

    # Feature importance (RF)
    rf = results['Random Forest']['model']
    fi = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=True)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Feature importance
    fi.plot(kind='barh', ax=axes[0], color='#3b82f6', alpha=0.85)
    axes[0].set_title('Feature Importance (Random Forest)', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Importance')
    axes[0].grid(True, axis='x', alpha=0.3)

    # Predicted vs Actual
    axes[1].scatter(y_test, best['preds'], c='#4ade80', s=50, alpha=0.7, edgecolors='none')
    mn, mx = min(y_test.min(), best['preds'].min()), max(y_test.max(), best['preds'].max())
    axes[1].plot([mn,mx],[mn,mx], color='#f87171', linewidth=1.5, linestyle='--', label='Perfect fit')
    axes[1].set_xlabel('Actual Price (₹)')
    axes[1].set_ylabel('Predicted Price (₹)')
    axes[1].set_title(f'Predicted vs Actual ({best_name})', fontsize=11, fontweight='bold')
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)
    axes[1].xaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'₹{x:,.0f}'))
    axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'₹{x:,.0f}'))

    # Model comparison
    model_names = list(results.keys())
    r2_scores   = [results[m]['R2'] for m in model_names]
    mae_scores  = [results[m]['MAE'] for m in model_names]
    ax2b = axes[2].twinx()
    bars = axes[2].bar(model_names, r2_scores, color='#3b82f6', alpha=0.7, label='R² Score')
    ax2b.plot(model_names, mae_scores, 'o-', color='#f59e0b', linewidth=2, label='MAE (₹)')
    axes[2].set_title('Model Comparison', fontsize=11, fontweight='bold')
    axes[2].set_ylabel('R² Score', color='#3b82f6')
    axes[2].set_ylim(0, 1.1)
    ax2b.set_ylabel('MAE (₹)', color='#f59e0b')
    axes[2].tick_params(axis='x', rotation=15)
    axes[2].grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('data/06_ml_model.png', dpi=150, bbox_inches='tight', facecolor='#0d0f14')
    plt.close()
    print("  Saved: data/06_ml_model.png")

    # Sample predictions
    print("\n  Sample ML Price Recommendations:")
    sample = df.head(6).copy()
    sample['category_enc'] = le.transform(sample['category'])
    sample['segment_enc']  = le.transform(sample['segment'])
    Xsamp = sample[features]
    sample['ml_recommended_price'] = rf.predict(Xsamp).round(0)
    sample['price_adjustment']     = sample['ml_recommended_price'] - sample['your_price']
    print(sample[['product_name','your_price','ml_recommended_price','price_adjustment']].to_string(index=False))

    return results, best_name


# ══════════════════════════════════════════════════════════════
# 7. PRICE HISTORY (SCD Type 2)
# ══════════════════════════════════════════════════════════════
def run_price_history(ph):
    print("\n" + "="*60)
    print("  PRICE HISTORY — SCD Type 2 Analysis")
    print("="*60)

    ph['valid_from'] = pd.to_datetime(ph['valid_from'])
    ph['valid_to']   = pd.to_datetime(ph['valid_to'])
    ph['days_active']= (ph['valid_to'] - ph['valid_from']).dt.days

    print(f"  Price change records: {len(ph)}")
    print(f"  Products tracked    : {ph['product_id'].nunique()}")
    changes = ph.groupby('product_id')['price'].agg(['min','max','count'])
    changes['drop_pct'] = ((changes['min']-changes['max'])/changes['max']*100).round(1)
    print(f"\n  Biggest price drops:\n{changes.sort_values('drop_pct').head()}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for pid in ph['product_id'].unique():
        prod = ph[ph['product_id']==pid]
        cat  = prod['category'].iloc[0]
        x    = list(prod['valid_from']) + [prod['valid_to'].iloc[-1]]
        y    = list(prod['price']) + [prod['price'].iloc[-1]]
        axes[0].step(x, y, where='post', color=CAT_COLORS.get(cat,'#555b6e'), alpha=0.7, linewidth=1.5)
    axes[0].set_title('Price History — SCD Type 2 (Step Chart)', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Date')
    axes[0].set_ylabel('Price (₹)')
    axes[0].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'₹{x:,.0f}'))
    axes[0].grid(True, alpha=0.3)

    avg_days = ph.groupby('change_reason')['days_active'].mean().sort_values()
    avg_days.plot(kind='barh', ax=axes[1], color='#a78bfa', alpha=0.8)
    axes[1].set_title('Avg Days per Price Strategy', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Avg Days Active')
    axes[1].grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig('data/07_price_history.png', dpi=150, bbox_inches='tight', facecolor='#0d0f14')
    plt.close()
    print("  Saved: data/07_price_history.png")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("  ADVANCED PRICING STRATEGY ANALYSIS v2.0")
    print("=" * 60)

    cfg      = load_config()
    df, ph   = load_data(cfg)

    run_eda(df)
    df       = run_bcg_matrix(df)
    elas_df  = run_elasticity(df, cfg)
    anom_df  = run_anomaly_detection(df, cfg)
    ab_df    = run_ab_test(df, cfg)
    ml_res, best_model = run_ml_pricing(df, cfg)
    run_price_history(ph)

    print("\n" + "="*60)
    print("  ALL ANALYSIS COMPLETE — 7 modules, 7 charts saved")
    print("="*60)

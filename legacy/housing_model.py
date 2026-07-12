"""Archived housing-model experiment; direct execution is disabled.

The legacy feature set includes contemporaneous target-derived values, so its
reported accuracy and intervals do not establish out-of-sample performance.
Importing this file is intentionally unsupported because the historical code
executes at module load time. Run the audited core instead.
"""

raise SystemExit(
    "DISABLED_LEGACY_MODEL: target leakage and uncalibrated intervals; "
    "no forecast or investment conclusion was generated"
)

import warnings
warnings.filterwarnings('ignore')
import logging
logging.getLogger('statsmodels').setLevel(logging.ERROR)

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from xgboost import XGBRegressor
from scipy import stats
import itertools
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent

# ============================================================
# 0. 数据加载与清洗
# ============================================================
print("=" * 70)
print("0. 数据加载与清洗")
print("=" * 70)

df = pd.read_csv(OUTPUT_DIR / '70city_full.csv')
df['日期'] = pd.to_datetime(df['日期'])
df = df.rename(columns={
    '日期': 'date', '城市': 'city',
    '新建商品住宅价格指数-同比': 'new_yoy',
    '新建商品住宅价格指数-环比': 'new_mom',
    '新建商品住宅价格指数-定基': 'new_base',
    '二手住宅价格指数-同比': 'used_yoy',
    '二手住宅价格指数-环比': 'used_mom',
    '二手住宅价格指数-定基': 'used_base',
})
df = df.sort_values(['city', 'date']).reset_index(drop=True)

# LPR
lpr = pd.read_csv(OUTPUT_DIR / 'lpr.csv')
lpr['TRADE_DATE'] = pd.to_datetime(lpr['TRADE_DATE'])
lpr = lpr.sort_values('TRADE_DATE')
lpr = lpr.set_index('TRADE_DATE')[['LPR1Y', 'LPR5Y']].dropna(how='all')
# 转月频：取每月最后一个可用值
lpr_monthly = lpr.resample('MS').ffill().reset_index().rename(columns={'TRADE_DATE': 'date'})

# PMI
pmi = pd.read_csv(OUTPUT_DIR / 'pmi.csv')
pmi['月份'] = pmi['月份'].str.replace('年', '-').str.replace('月份', '')
pmi['date'] = pd.to_datetime(pmi['月份'] + '-01')
pmi = pmi.rename(columns={'制造业-指数': 'mfg_pmi', '非制造业-指数': 'nmg_pmi'})
pmi = pmi[['date', 'mfg_pmi', 'nmg_pmi']].sort_values('date')

# 合并宏观
df = df.merge(lpr_monthly, on='date', how='left')
df = df.merge(pmi, on='date', how='left')
df[['LPR1Y', 'LPR5Y', 'mfg_pmi', 'nmg_pmi']] = df[['LPR1Y', 'LPR5Y', 'mfg_pmi', 'nmg_pmi']].ffill()

cities_all = sorted(df['city'].unique())
print(f"城市数: {len(cities_all)}")
print(f"时间范围: {df['date'].min().date()} ~ {df['date'].max().date()}")
print(f"总行数: {len(df)}")
print(f"缺失值 (used_yoy): {df['used_yoy'].isna().sum()}")

# ============================================================
# 1. ARIMA/SARIMA 时间序列模型 — 四大一线
# ============================================================
print("\n" + "=" * 70)
print("1. ARIMA/SARIMA 时间序列模型 (北京/上海/广州/深圳)")
print("=" * 70)

tier1 = ['北京', '上海', '广州', '深圳']
target_col = 'used_yoy'  # 二手住宅同比

train_end = pd.Timestamp('2024-12-01')
test_start = pd.Timestamp('2025-01-01')

arima_results = {}

for city in tier1:
    city_df = df[df['city'] == city].set_index('date')[target_col].dropna()
    train = city_df[:train_end]
    test = city_df[test_start:]

    # ADF检验
    adf_stat, adf_p, *_ = adfuller(train, autolag='AIC')
    print(f"\n{'─'*50}")
    print(f"城市: {city}")
    print(f"  训练集: {train.index[0].date()} ~ {train.index[-1].date()} ({len(train)}月)")
    print(f"  测试集: {test.index[0].date()} ~ {test.index[-1].date()} ({len(test)}月)")
    print(f"  ADF检验: stat={adf_stat:.4f}, p={adf_p:.4f} {'平稳' if adf_p < 0.05 else '非平稳→差分'}")

    # 网格搜索最优 (p,d,q)(P,D,Q,s)
    best_aic = np.inf
    best_order = (1, 0, 1)
    best_seasonal = (1, 0, 1, 12)

    d = 0 if adf_p < 0.05 else 1
    for p, q in itertools.product(range(3), range(3)):
        for P, Q in itertools.product(range(2), range(2)):
            try:
                model = SARIMAX(train, order=(p, d, q), seasonal_order=(P, 0, Q, 12),
                                enforce_stationarity=False, enforce_invertibility=False)
                res = model.fit(disp=False, maxiter=200)
                if res.aic < best_aic:
                    best_aic = res.aic
                    best_order = (p, d, q)
                    best_seasonal = (P, 0, Q, 12)
            except:
                continue

    print(f"  最优阶: SARIMA{best_order}x{best_seasonal}, AIC={best_aic:.2f}")

    # 拟合最优模型
    model = SARIMAX(train, order=best_order, seasonal_order=best_seasonal,
                    enforce_stationarity=False, enforce_invertibility=False)
    res = model.fit(disp=False, maxiter=300)

    # 滚动回测
    history = list(train.values)
    predictions = []
    actuals = list(test.values)

    for i in range(len(test)):
        m = SARIMAX(history, order=best_order, seasonal_order=best_seasonal,
                    enforce_stationarity=False, enforce_invertibility=False)
        r = m.fit(disp=False, maxiter=200)
        fc = r.forecast(steps=1)[0]
        predictions.append(fc)
        history.append(actuals[i])

    pred_arr = np.array(predictions)
    act_arr = np.array(actuals)

    mape = mean_absolute_percentage_error(act_arr, pred_arr) * 100
    rmse = np.sqrt(mean_squared_error(act_arr, pred_arr))
    # 方向准确率: 同比上升/下降方向是否一致 (以100为界)
    direction_pred = (pred_arr > 100).astype(int)
    direction_act = (act_arr > 100).astype(int)
    dir_acc = (direction_pred == direction_act).mean() * 100
    # 也可用环比方向: 这个月比上个月高还是低
    if len(act_arr) > 1:
        mom_dir_pred = np.diff(pred_arr) > 0
        mom_dir_act = np.diff(act_arr) > 0
        mom_dir_acc = (mom_dir_pred == mom_dir_act).mean() * 100
    else:
        mom_dir_acc = np.nan

    print(f"  回测指标:")
    print(f"    MAPE:        {mape:.2f}%")
    print(f"    RMSE:        {rmse:.2f}")
    print(f"    方向准确率(>100): {dir_acc:.1f}%")
    print(f"    环比方向准确率:   {mom_dir_acc:.1f}%")

    # 6步预测 (2026年5月 ~ 2026年10月)
    final_model = SARIMAX(city_df.values, order=best_order, seasonal_order=best_seasonal,
                          enforce_stationarity=False, enforce_invertibility=False)
    final_res = final_model.fit(disp=False, maxiter=300)
    forecast_6 = final_res.forecast(steps=6)
    forecast_ci_raw = final_res.get_forecast(steps=6).conf_int(alpha=0.05)
    # Handle both DataFrame and ndarray returns
    if hasattr(forecast_ci_raw, 'iloc'):
        forecast_ci = forecast_ci_raw.values
    else:
        forecast_ci = np.array(forecast_ci_raw)

    last_date = city_df.index[-1]
    fc_dates = pd.date_range(last_date + pd.DateOffset(months=1), periods=6, freq='MS')

    print(f"\n  6步预测 (从{fc_dates[0].strftime('%Y-%m')}开始):")
    print(f"  {'月份':<12} {'点预测':>8} {'95%CI下':>8} {'95%CI上':>8}")
    print(f"  {'─'*40}")
    for j in range(6):
        print(f"  {fc_dates[j].strftime('%Y-%m'):<12} {forecast_6[j]:>8.2f} {forecast_ci[j, 0]:>8.2f} {forecast_ci[j, 1]:>8.2f}")

    arima_results[city] = {
        'order': best_order, 'seasonal': best_seasonal, 'aic': best_aic,
        'mape': mape, 'rmse': rmse, 'dir_acc': dir_acc, 'mom_dir_acc': mom_dir_acc,
        'forecast': forecast_6, 'ci': forecast_ci, 'fc_dates': fc_dates,
        'predictions': pred_arr, 'actuals': act_arr,
    }

# ============================================================
# 2. 特征工程 — 全部42城
# ============================================================
print("\n" + "=" * 70)
print("2. 特征工程 (全部42城)")
print("=" * 70)

def build_features(df):
    """为每个城市构建特征面板"""
    feature_dfs = []
    for city in df['city'].unique():
        cdf = df[df['city'] == city].copy().sort_values('date').reset_index(drop=True)

        # 滞后特征
        for lag in [1, 3, 6, 12]:
            cdf[f'used_yoy_lag{lag}'] = cdf['used_yoy'].shift(lag)
            cdf[f'used_mom_lag{lag}'] = cdf['used_mom'].shift(lag)
            cdf[f'new_yoy_lag{lag}'] = cdf['new_yoy'].shift(lag)

        # 动量特征: 移动平均
        for w in [3, 6]:
            cdf[f'used_yoy_ma{w}'] = cdf['used_yoy'].rolling(w).mean()
            cdf[f'used_mom_ma{w}'] = cdf['used_mom'].rolling(w).mean()

        # 变化率
        cdf['used_yoy_diff1'] = cdf['used_yoy'].diff(1)
        cdf['used_yoy_diff3'] = cdf['used_yoy'].diff(3)
        cdf['used_yoy_diff12'] = cdf['used_yoy'].diff(12)

        # 新旧房价差
        cdf['new_used_gap'] = cdf['new_yoy'] - cdf['used_yoy']

        # 月度虚拟变量
        cdf['month'] = cdf['date'].dt.month
        cdf['quarter'] = cdf['date'].dt.quarter

        # 趋势
        cdf['trend'] = np.arange(len(cdf))

        feature_dfs.append(cdf)
    return pd.concat(feature_dfs, ignore_index=True)

# 城市间领先滞后: 计算一线城市对其他城市的领先相关性
tier1_cities = ['北京', '上海', '广州', '深圳']
tier1_avg = df[df['city'].isin(tier1_cities)].groupby('date')['used_yoy'].mean()
tier1_avg = tier1_avg.rename('tier1_avg_yoy')

df_with_tier1 = df.merge(tier1_avg.reset_index(), on='date', how='left')

# 领先/滞后交叉特征
for lag in [1, 3, 6]:
    df_with_tier1[f'tier1_avg_yoy_lag{lag}'] = df_with_tier1.groupby('city')['tier1_avg_yoy'].shift(lag)

df_feat = build_features(df_with_tier1)

# 合并宏观特征 (已在df_with_tier1中)

feature_cols = [c for c in df_feat.columns if c not in ['date', 'city', 'used_yoy', 'used_mom',
                                                          'used_base', 'new_yoy', 'new_mom', 'new_base']]

print(f"特征数: {len(feature_cols)}")
print(f"特征列表:")
for i, c in enumerate(feature_cols):
    if i % 4 == 0:
        print(f"  ", end="")
    print(f"{c:<28}", end="")
    if i % 4 == 3:
        print()
print()

# ============================================================
# 3. XGBoost 回测评估
# ============================================================
print("\n" + "=" * 70)
print("3. XGBoost 回测评估 (全部42城)")
print("=" * 70)

df_feat = df_feat.dropna(subset=['used_yoy'])
df_feat = df_feat.sort_values(['city', 'date']).reset_index(drop=True)

# 填充剩余NaN
for c in feature_cols:
    if df_feat[c].dtype in ['float64', 'int64']:
        df_feat[c] = df_feat[c].fillna(df_feat[c].median())

train_mask = df_feat['date'] <= train_end
test_mask = df_feat['date'] > train_end

X_train = df_feat.loc[train_mask, feature_cols]
y_train = df_feat.loc[train_mask, 'used_yoy']
X_test = df_feat.loc[test_mask, feature_cols]
y_test = df_feat.loc[test_mask, 'used_yoy']

print(f"训练样本: {len(X_train)}, 测试样本: {len(X_test)}")

# 训练XGBoost
xgb = XGBRegressor(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0,
    random_state=42, n_jobs=-1
)
xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

y_pred_xgb = xgb.predict(X_test)

# 整体指标
overall_mape = mean_absolute_percentage_error(y_test, y_pred_xgb) * 100
overall_rmse = np.sqrt(mean_squared_error(y_test, y_pred_xgb))
dir_pred = (y_pred_xgb > 100).astype(int)
dir_act = (y_test.values > 100).astype(int)
overall_dir = (dir_pred == dir_act).mean() * 100

print(f"\n整体回测指标:")
print(f"  MAPE:          {overall_mape:.2f}%")
print(f"  RMSE:          {overall_rmse:.2f}")
print(f"  方向准确率(>100): {overall_dir:.1f}%")

# 逐城市指标
print(f"\n{'城市':<8} {'MAPE%':>8} {'RMSE':>8} {'方向准确率%':>10}")
print("─" * 40)
city_metrics = {}
for city in sorted(df_feat['city'].unique()):
    mask = (df_feat['city'] == city) & test_mask
    if mask.sum() < 2:
        continue
    yt = df_feat.loc[mask, 'used_yoy'].values
    yp = xgb.predict(df_feat.loc[mask, feature_cols])
    m = mean_absolute_percentage_error(yt, yp) * 100
    r = np.sqrt(mean_squared_error(yt, yp))
    d = ((yp > 100) == (yt > 100)).mean() * 100
    city_metrics[city] = {'mape': m, 'rmse': r, 'dir': d}
    print(f"  {city:<6} {m:>8.2f} {r:>8.2f} {d:>10.1f}")

# 特征重要性
print(f"\nTop 15 特征重要性:")
importances = pd.Series(xgb.feature_importances_, index=feature_cols).sort_values(ascending=False)
for i, (feat, imp) in enumerate(importances.head(15).items()):
    print(f"  {i+1:>2}. {feat:<30} {imp:.4f}")

# ============================================================
# 4. 2026H2 预测 (全部42城)
# ============================================================
print("\n" + "=" * 70)
print("4. 2026H2 预测 (全部42城)")
print("=" * 70)

# 方法: 用XGBoost逐步递推预测 (需要上一步的预测值作为滞后特征)
# 同时用最后几个月的bootstrap不确定性估计置信区间

def forecast_xgb_recursive(model, df_city, feature_cols, n_steps=6):
    """递推预测: 每步用最新数据生成特征, 预测, 再加入历史"""
    history = df_city.copy()
    preds = []

    for step in range(n_steps):
        last_row = history.iloc[-1:]
        # 构建下一步特征 (简化: 复制最后一行, 更新趋势和滞后)
        next_row = last_row.copy()
        next_row['date'] = last_row['date'].values[0] + pd.DateOffset(months=1)
        next_row['trend'] = last_row['trend'].values[0] + 1
        next_row['month'] = next_row['date'].dt.month.values[0]
        next_row['quarter'] = next_row['date'].dt.quarter.values[0]

        # 更新滞后
        for lag in [1, 3, 6, 12]:
            if f'used_yoy_lag{lag}' in feature_cols:
                if lag == 1:
                    if len(preds) >= 1:
                        next_row[f'used_yoy_lag{lag}'] = preds[-1]
                    else:
                        next_row[f'used_yoy_lag{lag}'] = history['used_yoy'].iloc[-1]
                else:
                    idx = -lag
                    if abs(idx) <= len(history):
                        next_row[f'used_yoy_lag{lag}'] = history['used_yoy'].iloc[idx]

            if f'used_mom_lag{lag}' in feature_cols:
                next_row[f'used_mom_lag{lag}'] = history['used_mom'].iloc[-lag] if abs(-lag) <= len(history) else np.nan

            if f'new_yoy_lag{lag}' in feature_cols:
                next_row[f'new_yoy_lag{lag}'] = history['new_yoy'].iloc[-lag] if abs(-lag) <= len(history) else np.nan

        # 更新移动平均
        recent = list(history['used_yoy'].values[-5:]) + preds
        for w in [3, 6]:
            if f'used_yoy_ma{w}' in feature_cols:
                vals = recent[-w:]
                next_row[f'used_yoy_ma{w}'] = np.mean(vals) if len(vals) >= w else np.nan

        recent_mom = list(history['used_mom'].values[-5:])
        for w in [3, 6]:
            if f'used_mom_ma{w}' in feature_cols:
                next_row[f'used_mom_ma{w}'] = np.mean(recent_mom[-w:]) if len(recent_mom) >= w else np.nan

        # diff
        if 'used_yoy_diff1' in feature_cols:
            next_row['used_yoy_diff1'] = (preds[-1] - history['used_yoy'].iloc[-1]) if preds else 0
        if 'used_yoy_diff3' in feature_cols:
            next_row['used_yoy_diff3'] = history['used_yoy'].diff(3).iloc[-1] if len(history) > 3 else 0
        if 'used_yoy_diff12' in feature_cols:
            next_row['used_yoy_diff12'] = history['used_yoy'].diff(12).iloc[-1] if len(history) > 12 else 0

        # 预测
        X_next = next_row[feature_cols].fillna(0)
        pred = model.predict(X_next)[0]
        preds.append(pred)

        # 将预测值追加到历史
        new_row = next_row.copy()
        new_row['used_yoy'] = pred
        history = pd.concat([history, new_row], ignore_index=True)

    return np.array(preds)

# Bootstrap不确定性: 用训练集残差重采样
train_residuals = y_train.values - xgb.predict(X_train)
np.random.seed(42)

print(f"\n预测目标: 2026年5月 ~ 2026年10月 (二手住宅价格同比指数)")
print(f"{'城市':<8} {'5月':>7} {'6月':>7} {'7月':>7} {'8月':>7} {'9月':>7} {'10月':>7} {'不确定度':>8}")
print("─" * 70)

all_city_forecasts = {}
uncertainty_list = []

for city in sorted(df_feat['city'].unique()):
    city_data = df_feat[df_feat['city'] == city].sort_values('date').reset_index(drop=True)
    if len(city_data) < 24:
        continue

    # 点预测
    fc = forecast_xgb_recursive(xgb, city_data, feature_cols, n_steps=6)

    # Bootstrap置信区间
    n_boot = 100
    boot_preds = []
    for _ in range(n_boot):
        noise = np.random.choice(train_residuals, size=6, replace=True)
        boot_preds.append(fc + noise)
    boot_preds = np.array(boot_preds)
    ci_lower = np.percentile(boot_preds, 2.5, axis=0)
    ci_upper = np.percentile(boot_preds, 97.5, axis=0)

    # 不确定度: 置信区间宽度的均值
    uncertainty = np.mean(ci_upper - ci_lower)
    uncertainty_list.append((city, uncertainty))

    all_city_forecasts[city] = {
        'point': fc, 'ci_lower': ci_lower, 'ci_upper': ci_upper, 'uncertainty': uncertainty
    }

    print(f"  {city:<6} {fc[0]:>7.2f} {fc[1]:>7.2f} {fc[2]:>7.2f} {fc[3]:>7.2f} {fc[4]:>7.2f} {fc[5]:>7.2f} {uncertainty:>8.2f}")

# 不确定度排名
print(f"\n{'='*70}")
print("预测不确定性排名 (95%CI宽度均值, 越大越不确定)")
print(f"{'='*70}")
uncertainty_list.sort(key=lambda x: x[1], reverse=True)
print(f"{'排名':<5} {'城市':<8} {'CI宽度':>8} {'等级':>8}")
print("─" * 35)
for i, (city, unc) in enumerate(uncertainty_list):
    level = "⚠️ 高" if i < 5 else ("⚡ 中" if i < 15 else "✅ 低")
    print(f"  {i+1:<3} {city:<8} {unc:>8.2f} {level:>8}")

# ============================================================
# 5. 综合总结
# ============================================================
print(f"\n{'='*70}")
print("5. 综合总结")
print(f"{'='*70}")

print(f"\n一、ARIMA回测 (一线城市二手住宅同比):")
print(f"  {'城市':<6} {'MAPE%':>8} {'RMSE':>8} {'方向准确率%':>12}")
print("  " + "─" * 38)
for city in tier1:
    r = arima_results[city]
    print(f"  {city:<6} {r['mape']:>8.2f} {r['rmse']:>8.2f} {r['dir_acc']:>12.1f}")

print(f"\n二、XGBoost整体回测 (42城):")
print(f"  MAPE:          {overall_mape:.2f}%")
print(f"  RMSE:          {overall_rmse:.2f}")
print(f"  方向准确率:    {overall_dir:.1f}%")

print(f"\n三、最优XGBoost特征:")
for i, (feat, imp) in enumerate(importances.head(10).items()):
    print(f"  {i+1:>2}. {feat:<30} {imp:.4f}")

print(f"\n四、2026H2各城市点预测 (二手住宅同比指数, 均值):")
print(f"  {'城市':<8} {'5-10月均值':>10} {'趋势判断':>12}")
print("  " + "─" * 35)
city_trend = []
for city, fc_data in sorted(all_city_forecasts.items()):
    mean_val = np.mean(fc_data['point'])
    trend = "↑ 上涨加速" if fc_data['point'][-1] > fc_data['point'][0] and mean_val > 100 else \
            "→ 横盘" if abs(fc_data['point'][-1] - fc_data['point'][0]) < 1.0 else \
            "↓ 持续下行" if mean_val < 100 else "↑ 企稳回升"
    city_trend.append((city, mean_val, trend))
    print(f"  {city:<8} {mean_val:>10.2f} {trend:>12}")

print(f"\n五、不确定性最高的5城 (需重点关注):")
for city, unc in uncertainty_list[:5]:
    fc = all_city_forecasts[city]
    print(f"  {city}: 预测 {np.mean(fc['point']):.1f}, CI [{np.mean(fc['ci_lower']):.1f}, {np.mean(fc['ci_upper']):.1f}]")

print(f"\n{'='*70}")
print("模型构建完成。")
print(f"{'='*70}")

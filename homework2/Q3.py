import pandas as pd
import yfinance as yf
import numpy as np
import requests
import warnings

# 忽略一些yfinance下载时可能出现的警告
warnings.filterwarnings('ignore')

# --- 步骤 1 (复用): 获取IPO列表并下载数据 ---
# 这部分逻辑与Q2相同，确保我们有基础数据
print("步骤 1: 获取IPO列表并下载数据...")
url = 'https://stockanalysis.com/ipos/2024/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    ipo_tables = pd.read_html(response.text)
    ipos_df = ipo_tables[0]
    ipos_df['IPO Date'] = pd.to_datetime(ipos_df['IPO Date'])
    filtered_ipos = ipos_df[ipos_df['IPO Date'] < '2024-06-01'].copy()
    tickers = filtered_ipos['Symbol'].tolist()
    print(f"成功获取 {len(tickers)} 个股票代码。")
except Exception as e:
    print(f"获取IPO列表失败: {e}。将使用备用列表。")
    tickers = ['ANRO', 'AS', 'AITR', 'ZURV', 'CCTG', 'IVP', 'LEGT', 'KSPI', 'VHAI', 'MIRA', 'SAY', 'RBRK', 'INHD', 'TELO', 'BAYA', 'CHRO', 'SGN', 'BIRK', 'PMNT', 'LRE', 'ANL', 'GUTS', 'DDC', 'KYTX', 'ATGL', 'LRT', 'MSS', 'CGON', 'UMGP', 'AUNA', 'JL', 'DYCQ', 'SDGO', 'RAS', 'CTNT', 'MSTR', 'TYRA', 'SYRA', 'FTEL', 'DZGN', 'NNE', 'MLTX', 'ELAB', 'PARE', 'ALUR', 'HRYU', 'TBN', 'YIBO', 'HSHP', 'IKG', 'SMXT', 'MGX', 'WETH', 'TKLF', 'CRGY', 'MDGH', 'YAYO', 'SNOA', 'HAO', 'GLAC', 'INNC', 'TMP', 'HDL', 'HG', 'ROMA', 'FBLG', 'ZONE', 'AHR', 'MMV', 'DTYL', 'ESHA', 'CASA', 'FGE', 'SHIM', 'DJT']
    print(f"已加载备用列表，包含 {len(tickers)} 个股票代码。")

# 下载数据，确保时间范围足够长以计算未来12个月的增长
# 比如，最后一个IPO是2024年5月底，我们需要至少到2025年5月底的数据
all_data_raw = yf.download(tickers, start='2024-01-01', end='2025-06-22', progress=False) # 结束日期设为当前
all_data = all_data_raw.stack(level=1).reset_index().rename(columns={'level_1': 'Ticker'})
all_data['Date'] = pd.to_datetime(all_data['Date'])
print("数据下载和格式化完成。")
print("-" * 30)


# --- 步骤 2: 计算1到12个月的未来增长率 ---
print("步骤 2: 正在计算1到12个月的未来增长率...")
df_growth = all_data.copy().sort_values(by=['Ticker', 'Date'])
TRADING_DAYS_PER_MONTH = 21

# 使用循环为每个持有期创建新列
for months in range(1, 13):
    future_days = months * TRADING_DAYS_PER_MONTH
    col_name = f'future_growth_{months}m'
    
    # 使用 groupby 和 shift(-N) 计算未来增长率
    df_growth[col_name] = df_growth.groupby('Ticker')['Close'].transform(
        lambda x: x.shift(-future_days) / x - 1
    )
print("未来增长率计算完成。")
print("-" * 30)


# --- 步骤 3: 确定每个股票的首个交易日并提取数据 ---
print("步骤 3: 正在确定首个交易日并提取对应数据...")
# 找到每个 Ticker 的最小日期 (首个交易日)
min_dates = df_growth.groupby('Ticker')['Date'].min().reset_index()
min_dates.rename(columns={'Date': 'min_date'}, inplace=True)

# 将首个交易日与增长率数据进行合并，以提取首日数据
# 我们需要在 df_growth 中用 'Date' 列与 min_dates 中的 'min_date' 列匹配
# 为此，我们先将 min_date 的列名改为 'Date' 以便合并
min_dates.rename(columns={'min_date': 'Date'}, inplace=True)
first_day_growth_df = pd.merge(df_growth, min_dates, on=['Ticker', 'Date'], how='inner')

print(f"成功提取了 {len(first_day_growth_df)} 家公司的首日未来增长数据。")
print("-" * 30)

# --- 步骤 4: 计算描述性统计 ---
print("步骤 4: 正在为每个持有期计算描述性统计...")
# 筛选出我们感兴趣的12个未来增长列
future_growth_cols = [f'future_growth_{i}m' for i in range(1, 13)]
# 计算并展示描述性统计
desc_stats = first_day_growth_df[future_growth_cols].describe()

print("各持有期未来增长率的描述性统计:")
print(desc_stats)
print("-" * 30)


# --- 步骤 5: 确定最佳持有期 ---
print("步骤 5: 正在确定最佳持有期...")
# 从统计结果中提取 'mean' (平均值) 这一行
mean_returns = desc_stats.loc['mean']

# 找到平均回报最高的持有期
optimal_period_col = mean_returns.idxmax()
max_mean_return = mean_returns.max()

# 从列名中解析出月份
optimal_months = int(optimal_period_col.split('_')[2][:-1])

print("\n[最终结论]")
print(f"最佳持有期为: {optimal_months} 个月 ({optimal_period_col})")
print(f"该持有期下的平均未来增长率为: {max_mean_return:.4f} (或 {max_mean_return:.2%})")

# 检查题目中的提示
sorted_means = mean_returns.sort_values(ascending=False)
uplift = sorted_means.iloc[0] - sorted_means.iloc[1]
print(f"最佳持有期的回报率比第二名高出: {uplift:.4f} (或 {uplift:.2%})")
if max_mean_return < 1:
    print("观察: 平均回报率小于1，符合题目预期。")
else:
    print("观察: 平均回报率不小于1，不符合题目预期。")
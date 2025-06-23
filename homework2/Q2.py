import pandas as pd
import yfinance as yf
import numpy as np
import requests
import warnings

# 忽略一些yfinance下载时可能出现的警告
warnings.filterwarnings('ignore')

# --- 步骤 1: 获取在2024年前5个月上市的公司股票代码 ---
print("步骤 1: 正在从 stockanalysis.com 获取2024年IPO列表...")
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
print("-" * 30)


# --- 步骤 2: 下载所有股票的OHLCV数据并转换格式 ---
print("步骤 2: 正在使用 yfinance 下载股票历史数据...")
all_data_raw = yf.download(tickers, start='2024-01-01', end='2025-06-07', progress=False)

print("正在转换数据格式...")
all_data = all_data_raw.stack(level=1).reset_index().rename(columns={'level_1': 'Ticker'})
print("数据下载和格式转换完成。")
print("-" * 30)

# --- 步骤 3: 计算各项指标 ---
print("步骤 3: 正在计算各项指标...")
df_copy = all_data.copy()
df_copy['Date'] = pd.to_datetime(df_copy['Date'])

# 计算252日增长率
df_copy['growth_252d'] = df_copy.groupby('Ticker')['Close'].pct_change(periods=252)

# ##########################################################################
# ### 使用题目指定的非标准波动率公式 ##################################
# ##########################################################################
print("注意：正在使用题目指定的非标准波动率公式...")
# 基于收盘价本身计算滚动标准差，并年化
vol_series = df_copy.groupby('Ticker')['Close'].rolling(window=30).std().reset_index(level=0, drop=True)
df_copy['volatility'] = vol_series * np.sqrt(252)
# ##########################################################################

# --- 计算夏普比率 ---
risk_free_rate = 0.045
df_copy['Sharpe'] = (df_copy['growth_252d'] - risk_free_rate) / df_copy['volatility']
print("指标计算完成。")
print("-" * 30)

# --- 步骤 4: 筛选特定日期的数据并进行分析 ---
print("步骤 4: 筛选2025-06-06的数据并进行分析...")
final_date_str = '2025-06-06'
results_df = df_copy[df_copy['Date'] == final_date_str].copy()
results_df.dropna(subset=['growth_252d', 'Sharpe'], inplace=True)

print(f"在 {final_date_str}，共有 {len(results_df)} 只股票有完整的 growth_252d 和 Sharpe 数据。")
print("\n描述性统计信息 (Descriptive Statistics):")
print(results_df[['growth_252d', 'Sharpe']].describe())
print("-" * 30)

# --- 步骤 5: 输出最终结果 ---
print("步骤 5: 输出最终结果...")
median_sharpe_ratio = results_df['Sharpe'].median()
print(f"\n[最终结论]")
print(f"基于当前实时数据和题目指定的非标准公式，目标股票池在 {final_date_str} 的中位数夏普比率为: {median_sharpe_ratio:.4f}")
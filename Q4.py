import pandas as pd
import yfinance as yf
import numpy as np

# --- 步骤 1: 加载盈利数据 ---
try:
    # 鉴于您最新显示的列名，pandas可能已经能正确解析文件。
    # 我们先尝试按原题说明使用分号作为分隔符，如果不行，再尝试让pandas自动推断。
    try:
        # 假设文件名仍然是 "ha1_Amazon.csv"
        earnings_df = pd.read_csv("ha1_Amazon.csv", delimiter=';')
        # 检查列名是否是您最新提供的那样，如果不是，说明分隔符可能不是分号
        if 'Earnings Date' not in earnings_df.columns and 'Symbol' not in earnings_df.columns :
            print("使用分号作为分隔符未能正确解析列名，尝试让Pandas自动推断分隔符...")
            raise ValueError("Delimiter possibly not semicolon") # 跳到下一个尝试
    except (ValueError, Exception): # 如果上一步失败 (包括主动抛出ValueError)
        try:
            earnings_df = pd.read_csv("ha1_Amazon.csv") # Pandas 自动推断分隔符
            print("Pandas自动推断分隔符加载成功。")
        except Exception as e_auto:
            print(f"尝试自动推断分隔符读取CSV时也失败了: {e_auto}")
            print("请确保文件 'ha1_Amazon.csv' 存在且格式正确 (例如，逗号分隔或分号分隔)。")
            exit()

except FileNotFoundError:
    print("错误：CSV文件 'ha1_Amazon.csv' 未在当前目录中找到。")
    exit()
except Exception as e: # 其他可能的读取错误
    print(f"读取CSV文件时发生错误: {e}")
    exit()

print("\n成功加载CSV文件。")
print("DataFrame的实际列名是:", list(earnings_df.columns))

# --- 定义将要使用的列名 (根据您最新提供的错误信息) ---
date_column_from_csv = 'Earnings Date'
reported_eps_column_from_csv = 'Reported EPS'
estimated_eps_column_from_csv = 'EPS Estimate'

# 检查这些必需的列是否存在于加载的DataFrame中
required_actual_cols = [date_column_from_csv, reported_eps_column_from_csv, estimated_eps_column_from_csv]
missing_actual_cols = [col for col in required_actual_cols if col not in earnings_df.columns]

if missing_actual_cols:
    print(f"\n错误：DataFrame中缺少以下必需的列: {', '.join(missing_actual_cols)}")
    print(f"脚本期望的列名是基于您提供的错误信息: '{date_column_from_csv}', '{reported_eps_column_from_csv}', '{estimated_eps_column_from_csv}'.")
    print("请确保您的CSV文件包含这些列，或者文件名与脚本中使用的实际列名一致。")
    exit()

# --- 数据类型转换和清洗 ---
try:
    # 使用 .loc 避免 SettingWithCopyWarning，并确保在原始DataFrame上操作
    earnings_df.loc[:, 'earnings_date'] = pd.to_datetime(earnings_df[date_column_from_csv])
except Exception as e:
    print(f"\n转换 '{date_column_from_csv}' 列为datetime格式时出错: {e}")
    exit()

try:
    earnings_df.loc[:, 'reportedEPS_num'] = pd.to_numeric(earnings_df[reported_eps_column_from_csv], errors='coerce')
    earnings_df.loc[:, 'estimatedEPS_num'] = pd.to_numeric(earnings_df[estimated_eps_column_from_csv], errors='coerce')
except Exception as e:
    print(f"\n转换EPS列 ('{reported_eps_column_from_csv}', '{estimated_eps_column_from_csv}') 为数值时出错: {e}")
    exit()

# 删除包含NaN的行（在关键列上）
earnings_df.dropna(subset=['earnings_date', 'reportedEPS_num', 'estimatedEPS_num'], inplace=True)

if earnings_df.empty:
    print("错误：经过数据类型转换和NaN值移除后，盈利数据为空。请检查CSV文件内容和数据有效性。")
    exit()

# --- 步骤 2: 下载股价数据 ---
# 题目针对的是亚马逊 (AMZN)。如果您的CSV文件中的 'Symbol' 列指明了其他股票，
# 并且您希望动态处理，则需要修改此部分。目前，我们固定为AMZN。
ticker_symbol = "AMZN"
# 如果CSV中有 'Symbol' 列且包含AMZN，可以验证一下
# if 'Symbol' in earnings_df.columns and not earnings_df[earnings_df['Symbol'] == ticker_symbol].empty:
# print(f"CSV文件中包含股票代码 {ticker_symbol} 的数据。")
# else:
# print(f"警告: CSV文件中可能不包含股票代码 {ticker_symbol} 的数据，或者没有 'Symbol' 列。仍按AMZN处理。")

stock_ticker = yf.Ticker(ticker_symbol)

# 获取股价数据的日期范围
min_date_for_prices = earnings_df['earnings_date'].min() - pd.Timedelta(days=30)
max_date_for_prices = earnings_df['earnings_date'].max() + pd.Timedelta(days=30)

try:
    prices_df = stock_ticker.history(start=min_date_for_prices, end=max_date_for_prices)
except Exception as e:
    print(f"下载股票 {ticker_symbol} 的历史股价数据时出错: {e}")
    exit()

if prices_df.empty:
    print(f"未能下载股票 {ticker_symbol} 的价格数据。请检查网络连接或确保日期范围内有数据。")
    exit()

prices_df.index = pd.to_datetime(prices_df.index).tz_localize(None).normalize()

# --- 步骤 4: 识别正面盈利惊喜 ---
positive_surprises_df = earnings_df[earnings_df['reportedEPS_num'] > earnings_df['estimatedEPS_num']].copy()
print(f"\n找到 {len(positive_surprises_df)} 个正面盈利惊喜事件。") # 题目提示应有36个

# --- 步骤 3 & 5: 计算正面盈利惊喜后的2日股价变动，并计算中位数 ---
surprise_day_returns = []

for index, row in positive_surprises_df.iterrows():
    event_date = row['earnings_date'] # 这已经是 datetime 对象
    # 找到 event_date 在 prices_df.index 中的位置，或其后的第一个交易日
    day2_iloc = prices_df.index.searchsorted(event_date)

    # 确保有足够的前后数据来计算 Day1 和 Day3
    if day2_iloc > 0 and day2_iloc < len(prices_df) - 1:
        close_day1 = prices_df['Close'].iloc[day2_iloc - 1] # Day2 前一个交易日
        close_day3 = prices_df['Close'].iloc[day2_iloc + 1] # Day2 后一个交易日

        if pd.notna(close_day1) and pd.notna(close_day3) and close_day1 != 0:
            two_day_return = (close_day3 / close_day1) - 1
            surprise_day_returns.append(two_day_return)

if not surprise_day_returns:
    print("未能计算出任何在正面盈利惊喜后的股价回报率。")
    median_surprise_return_pct = float('nan')
else:
    median_surprise_return = np.median(surprise_day_returns)
    median_surprise_return_pct = median_surprise_return * 100

print(f"\n正面盈利惊喜后2日股价变动的中位数: {median_surprise_return_pct:.2f}%")

# --- 步骤 6 (可选): 比较所有历史日期的中位数回报率 ---
all_two_day_returns = []
if len(prices_df) >= 3: # 确保至少有3天数据
    for i in range(1, len(prices_df) - 1): # Day_i 是 Day2
        close_day1_all = prices_df['Close'].iloc[i-1] # Day1
        close_day3_all = prices_df['Close'].iloc[i+1] # Day3
        if pd.notna(close_day1_all) and pd.notna(close_day3_all) and close_day1_all != 0:
            ret = (close_day3_all / close_day1_all) - 1
            all_two_day_returns.append(ret)

if not all_two_day_returns:
    print("未能计算所有历史日期的2日股价变动中位数。")
    median_all_returns_pct = float('nan')
else:
    median_all_returns = np.median(all_two_day_returns)
    median_all_returns_pct = median_all_returns * 100

print(f"所有历史日期2日股价变动的中位数: {median_all_returns_pct:.2f}%")

# --- 两者差异 ---
if pd.notna(median_surprise_return_pct) and pd.notna(median_all_returns_pct):
    difference = median_surprise_return_pct - median_all_returns_pct
    print(f"两者差异: {difference:.2f}%")
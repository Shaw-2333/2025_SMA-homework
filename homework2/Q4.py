
# 步骤 1: 导入需要使用的库
import gdown
import pandas as pd

# 步骤 2: 下载并加载数据
file_id = "1grCTCzMZKY5sJRtdbLVCXg8JXA8VPyg-"
gdown.download(f"https://drive.google.com/uc?id={file_id}", "data.parquet", quiet=False)
df = pd.read_parquet("data.parquet", engine="pyarrow")
print("--> 数据加载完成！")

# ----------------------------------------------------------------
# 步骤 3: 数据预处理 (关键修改处)
# ----------------------------------------------------------------

# 假设原始数据中的日期列名为 'Date' (首字母大写)
# 我们读取 'Date' 列，将其转换为日期格式，并存入一个名为 'date' 的新列中
df['date'] = pd.to_datetime(df['Date']) 
# ----------------------------------------------------------------
# 步骤 4: 执行 RSI 交易策略并计算收益 
# ----------------------------------------------------------------
print("\n--> 开始执行 RSI 策略分析...")

rsi_threshold = 25
selected_df = df[
    (df['rsi'] < rsi_threshold) &
    (df['date'] >= '2000-01-01') &
    (df['date'] <= '2025-06-01')
]

total_trades = len(selected_df)
print(f"--> 共找到 {total_trades} 次交易机会。")

net_income = 1000 * (selected_df['growth_future_30d'] - 1).sum()
net_income_in_thousands = net_income / 1000

# ----------------------------------------------------------------
# 最终答案 
# ----------------------------------------------------------------
print("\n--- 分析结果 ---")
print(f"总净收入为: ${net_income:,.2f}")
print(f"以千美元为单位是: {net_income_in_thousands:,.2f} K")
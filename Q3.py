import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# 1. 下载 S&P 500 历史数据
symbol = "^GSPC"
start_date = "1950-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")
print(f"正在下载 {symbol} 从 {start_date} 到 {end_date} 的数据...")
raw = yf.download(symbol, start=start_date, end=end_date, progress=False)

if raw.empty:
    print("未能下载到任何数据，请检查股票代码、日期范围或网络连接。程序将退出。")
    exit()

# 2. 确定到底用哪列价格
if "Adj Close" in raw.columns:
    price_col = "Adj Close"
elif "Close" in raw.columns:
    price_col = "Close"
else:
    print("错误：数据里既没有 'Adj Close' 也没有 'Close'，请检查下载结果。")
    exit()

# 3. 把价格做成 Series（确保一维），然后新建一个 DataFrame 储存价格和累计最高
prices = raw[(price_col, symbol)].dropna().copy() # 一维 Series
# 在这里加入下面的调试打印语句：

if prices.empty:
    print("价格数据为空（可能所有数据都是无效值或下载范围无数据）。无法进行分析。")
    # 根据需要决定是退出还是赋默认空值
    corr_df = pd.DataFrame(columns=["PeakDate", "PeakPrice", "TroughDate", "TroughPrice", "DrawdownPct", "DurationDays"])
    durations = np.array([])
else:
    # 尝试显式指定索引来解决 ValueError
    try:
        data = pd.DataFrame({
            "AdjClose": prices,
            "CumMax": prices.cummax()
        }, index=prices.index) # 显式使用 prices 的索引
    except ValueError as e:
        print(f"创建 DataFrame 时发生错误: {e}")
        print("请检查您的 pandas 版本或 prices Series 的内容。")
        # 可以添加调试信息：
        # print(f"Type of prices: {type(prices)}")
        # print(f"Prices head: {prices.head()}")
        # print(f"Is prices scalar: {pd.api.types.is_scalar(prices)}")
        # print(f"Is prices.cummax() scalar: {pd.api.types.is_scalar(prices.cummax())}")
        exit()

    # 4. 标记历史新高：AdjClose == CumMax 会生成一维布尔序列，直接赋值就行
    data["IsNewHigh"] = data["AdjClose"] == data["CumMax"]

    # 5. 把所有新高对应的日期都收集到列表 high_dates
    high_dates = data.index[data["IsNewHigh"]].to_list()

    # 6. 遍历相邻两次新高之间的区间，找最低点并计算有没有 ≥5% 回调，以及时长
    results = []
    if len(high_dates) < 2:
        print("历史新高数据不足，无法计算回调区间。")
        corr_df = pd.DataFrame(results) # 确保 corr_df 被定义
        durations = np.array([]) # 确保 durations 被定义
    else:
        for i in range(len(high_dates) - 1):
            peak_date = high_dates[i]
            next_high = high_dates[i+1] # 注意这里，如果只有一个高点，high_dates[i+1]会越界
                                       # 但 range(len(high_dates) - 1) 保证了 i+1 是有效的

            # 确保 next_high 大于 peak_date，避免空区间或异常区间
            if next_high <= peak_date:
                continue

            peak_price = data.at[peak_date, "AdjClose"]
            
            # 切片时确保 next_high 存在于 data.index 中
            # 并且，为了包含 peak_date 当天的数据作为可能的最低点，区间应该从 peak_date 开始
            # 为了包含 next_high 前一天的数据，可以到 next_high 但不包含 next_high（如果 next_high 当天不能算入回调检测）
            # 或者包含 next_high 当天，因为价格可能在创新高当天先下跌再创新高。
            # 原代码 segment = data.loc[peak_date:next_high] 是合理的，它会包含 peak_date 和 next_high 两天
            segment = data.loc[peak_date:next_high, "AdjClose"]

            if segment.empty: # 如果因为某些原因（比如 next_high 就是 peak_date 的下一天）导致切片为空或不合理
                continue

            trough_price = segment.min()
            trough_date = segment.idxmin()

            drawdown_pct = (peak_price - trough_price) / peak_price
            if drawdown_pct >= 0.05:
                # 计算持续时间，从波峰到波谷
                duration = (trough_date - peak_date).days
                results.append({
                    "PeakDate": peak_date,
                    "PeakPrice": peak_price,
                    "TroughDate": trough_date,
                    "TroughPrice": trough_price,
                    "DrawdownPct": drawdown_pct * 100,
                    "DurationDays": duration
                })
        
        corr_df = pd.DataFrame(results)
        if not corr_df.empty:
            durations = corr_df["DurationDays"].to_numpy()
        else:
            durations = np.array([])


# 7. 把结果放进 DataFrame，统计 25th、50th（中位数）、75th 百分位
if durations.size > 0:
    p25, p50, p75 = np.percentile(durations, [25, 50, 75])
    print(f"回调次数：{len(corr_df)} 次")
    print(f"时长 25th 百分位：{int(p25)} 天")
    print(f"中位数（50th）：{int(p50)} 天")
    print(f"时长 75th 百分位：{int(p75)} 天")
else:
    print("没有找到符合条件的回调，无法计算时长百分位数。")
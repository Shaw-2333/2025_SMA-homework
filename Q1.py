import pandas as pd
from datetime import datetime

# 1. 抓取维基百科标准普尔500指数公司列表
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
tables = pd.read_html(url)
df = tables[0]

# 2. 创建包含股票代码、名称和添加年份的 DataFrame
df = df[['Symbol', 'Security', 'Date added']]
df['Year added'] = pd.to_datetime(df['Date added'], errors='coerce').dt.year

# 3. 计算每年新增的股票数量
yearly_add = df['Year added'].value_counts().sort_index()

# 4. 找出新增股票数量最多的年份（不算1957年）
yearly_add_no_1957 = yearly_add.drop(1957, errors='ignore')
max_add = yearly_add_no_1957.max()
max_years = yearly_add_no_1957[yearly_add_no_1957 == max_add].index
max_year = max_years[-1]  # 如果有多条记录，取最近一年

print(f"新增股票数量最多的年份（不含1957年）是：{max_year}")

# 5. 统计目前有多少支成分股已经在该指数中存在超过20年
current_year = datetime.now().year
df['Years in Index'] = current_year - df['Year added']
over_20_years = df[df['Years in Index'] > 20].shape[0]

print(f"目前有 {over_20_years} 支标普500指数成分股已经在该指数中存在超过20年。")

# 6. 结论说明
print("当股票被纳入标普500指数时，由于投资者和指数基金在公告发布后买入，其股价通常会上涨。")

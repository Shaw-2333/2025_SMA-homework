import pandas as pd
import numpy as np
import requests # 导入 requests 库

# 步骤 1: 使用 requests 和 pandas 从URL加载数据

url = 'https://stockanalysis.com/ipos/withdrawn/'

# 添加浏览器请求头，伪装成浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    # 使用 requests 发送带有请求头的 GET 请求
    response = requests.get(url, headers=headers)
    # 检查请求是否成功 (状态码 200)
    response.raise_for_status() 

    # 将获取到的 HTML 文本内容交给 pandas 解析
    df_list = pd.read_html(response.text)
    df = df_list[0]
    print(f"成功加载数据，共 {len(df)} 条记录。")
    print("-" * 30)

# 捕获可能发生的网络或解析错误
except requests.exceptions.RequestException as e:
    print(f"无法加载数据，网络请求失败: {e}")
    exit()
except Exception as e:
    print(f"处理数据时发生错误: {e}")
    exit()

# 步骤 2: 创建一个新的列 "Company Class"
def classify_company(name):
    """根据公司名称中的关键词进行分类"""
    if not isinstance(name, str):
        return 'Other'
    
    # 提示：将名称转为小写以进行不区分大小写的匹配
    lower_name = name.lower()
    
    # 按照题目要求的顺序进行匹配
    if 'acquisition corp' in lower_name or 'acquisition corporation' in lower_name:
        return 'Acq.Corp'
    elif 'inc' in lower_name or 'incorporated' in lower_name:
        return 'Inc'
    elif 'group' in lower_name:
        return 'Group'
    elif 'ltd' in lower_name or 'limited' in lower_name:
        return 'Limited'
    elif 'holdings' in lower_name:
        return 'Holdings'
    else:
        return 'Other'

# 应用函数创建新列
df['Company Class'] = df['Company Name'].apply(classify_company)

# 步骤 3: 定义一个新的 "Avg. Price" 字段
def parse_price(price_range):
    """解析价格范围字符串，计算平均价"""
    if not isinstance(price_range, str) or price_range == '--':
        return np.nan # 返回NaN表示无效值
    
    # 去掉 '$' 符号并去除首尾空格
    price_range = price_range.replace('$', '').strip()
    
    try:
        if '-' in price_range:
            low, high = map(float, price_range.split('-'))
            return (low + high) / 2.0
        else:
            return float(price_range)
    except (ValueError, TypeError):
        return np.nan

# 应用函数创建新列
df['Avg. Price'] = df['Price Range'].apply(parse_price)

# 步骤 4: 将 "Shares Offered" 列转换为数值类型
# 'coerce'会将无法转换的值变为NaN
df['Shares Offered'] = pd.to_numeric(df['Shares Offered'], errors='coerce')

# 步骤 5: 创建 "Withdrawn Value" 列
df['Withdrawn Value'] = df['Shares Offered'] * df['Avg. Price']

# 打印出有用的调试信息
print(f"成功计算出 {df['Withdrawn Value'].notna().sum()} 个有效的 'Withdrawn Value'。")
print("-" * 30)

# 步骤 6: 按 "Company Class" 分组并计算总撤回价值
total_withdrawn_by_class = df.groupby('Company Class')['Withdrawn Value'].sum()

print("各公司类别的总撤回价值: (单位：美元)")
print(total_withdrawn_by_class)
print("-" * 30)

# 步骤 7: 找出总价值最高的类别及其价值
highest_class = total_withdrawn_by_class.idxmax()
highest_value = total_withdrawn_by_class.max()

# 将结果转换为百万美元
highest_value_in_millions = highest_value / 1_000_000

print("最终答案:")
print(f"具有最高总撤回价值的公司类别是: {highest_class}")
print(f"该类别的总撤回价值为: ${highest_value_in_millions:.2f} 百万美元")
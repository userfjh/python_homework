import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter
import re # 用于正则表达式提取星期

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei'] # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题

# 加载CSV文件
try:
    df = pd.read_csv('caipiao_daletou.csv')
    print("CSV 文件加载成功。")
    print("数据前5行:\n", df.head())
    print("\n数据信息概览:\n")
    df.info()
except FileNotFoundError:
    print("错误: caipiao_daletou.csv 未找到。请确保文件与脚本在同一目录下。")
    exit()

# --- 数据清洗和转换 ---

# 转换 '开奖日期' 列为日期时间对象并提取星期信息
# 例如：'2025-06-30（一）'
def extract_day_of_week(date_str):
    if pd.isna(date_str): # 处理空值
        return None
    match = re.search(r'（(.)）', date_str)
    if match:
        day_char = match.group(1)
        if day_char == '一': return '周一'
        if day_char == '三': return '周三'
        if day_char == '六': return '周六'
    return None

# 解析日期部分
df['开奖日期_parsed'] = df['开奖日期'].apply(lambda x: pd.to_datetime(x.split('（')[0], errors='coerce') if pd.notna(x) else pd.NaT)
# 提取星期
df['开奖星期'] = df['开奖日期'].apply(extract_day_of_week)

# 将 '全国销量' 和 '奖池滚存' 转换为数值类型（去除逗号、'元'等非数字字符）
def clean_numeric(s):
    if isinstance(s, str):
        # 移除逗号，'元'，并去除首尾空白
        cleaned_s = s.replace(',', '').replace('元', '').strip()
        try:
            return float(cleaned_s)
        except ValueError:
            return np.nan # 转换失败返回NaN
    return s

df['全国销量'] = df['全国销量'].apply(clean_numeric)
df['奖池滚存'] = df['奖池滚存'].apply(clean_numeric)

# 将 '前区号码' 和 '后区号码' 字符串转换为整数列表
# 它们当前是空格分隔的字符串，例如 "01 04 17 33 34"
df['前区号码_list'] = df['前区号码'].apply(lambda x: [int(n) for n in str(x).split()] if pd.notna(x) else [])
df['后区号码_list'] = df['后区号码'].apply(lambda x: [int(n) for n in str(x).split()] if pd.notna(x) else [])


# 按日期升序排序，确保数据按时间顺序排列，便于后续分析
df = df.sort_values(by='开奖日期_parsed', ascending=True).reset_index(drop=True)

print("\n数据处理后前5行:\n", df.head())
print("\n数据处理后信息概览:\n")
df.info()

# 检查是否存在缺失值，特别是处理后的关键列
print("\n处理后的关键列缺失值检查:")
print(df[['开奖日期_parsed', '开奖星期', '全国销量', '前区号码_list', '后区号码_list']].isnull().sum())

#前区号码与后区号码频率统计与可视化，分析其历史分布规律（问题2）

# 将所有期号列表展平，以便统计每个号码的出现次数
all_red_balls = [num for sublist in df['前区号码_list'] for num in sublist]
all_blue_balls = [num for sublist in df['后区号码_list'] for num in sublist]

# 使用 Counter 进行频率统计
red_ball_counts = Counter(all_red_balls)
blue_ball_counts = Counter(all_blue_balls)

# 转换为 DataFrame 便于排序和绘图
red_freq_df = pd.DataFrame(red_ball_counts.items(), columns=['号码', '出现频率']).sort_values(by='号码')
blue_freq_df = pd.DataFrame(blue_ball_counts.items(), columns=['号码', '出现频率']).sort_values(by='号码')

print("\n--- 大乐透前区号码频率统计 (出现次数最多的前10个) ---")
print(red_freq_df.sort_values(by='出现频率', ascending=False).head(10))
print("\n--- 大乐透后区号码频率统计 (出现次数最多的前5个) ---")
print(blue_freq_df.sort_values(by='出现频率', ascending=False).head(5))

#可视化

plt.figure(figsize=(18, 7)) # 调整图表大小以适应更多数据点

# 前区号码频率分布
plt.subplot(1, 2, 1) # 1行2列的第1个子图
sns.barplot(x='号码', y='出现频率', data=red_freq_df, palette='Reds_d')
plt.title('大乐透前区号码频率分布')
plt.xlabel('前区号码 (1-35)')
plt.ylabel('出现频率')
plt.xticks(rotation=90, fontsize=8) # 旋转X轴标签，防止重叠
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 后区号码频率分布
plt.subplot(1, 2, 2) # 1行2列的第2个子图
sns.barplot(x='号码', y='出现频率', data=blue_freq_df, palette='Blues_d')
plt.title('大乐透后区号码频率分布')
plt.xlabel('后区号码 (1-12)')
plt.ylabel('出现频率')
plt.xticks(fontsize=8)
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout() # 自动调整子图参数，使之填充整个图像区域
plt.show()

#历史分布规律分析与号码推荐

# 推荐号码：前区选择频率最高的5个，后区选择频率最高的2个
recommended_red = red_freq_df.sort_values(by='出现频率', ascending=False).head(5)['号码'].tolist()
recommended_blue = blue_freq_df.sort_values(by='出现频率', ascending=False).head(2)['号码'].tolist()

# 对号码进行排序，符合大乐透习惯
recommended_red.sort()
recommended_blue.sort()

print(f"\n--- 大乐透号码推荐 (2025年7月1日之后最近一期) ---")
print(f"基于历史频率最高推荐：")
print(f"前区号码 (5个): {recommended_red}")
print(f"后区号码 (2个): {recommended_blue}")
print(f"因此，推荐的投注号码是： {recommended_red} + {recommended_blue}")

print("\n请注意：彩票开奖是随机事件，历史数据分析仅供参考，不能保证中奖。")

#按开奖日统计号码分布与销售额特征（问题3

# 按开奖星期分组，统计销售额和奖池的平均值、总和等
sales_by_weekday = df.groupby('开奖星期')['全国销量'].agg(['mean', 'sum', 'count']).reindex(['周一', '周三', '周六'])
prize_pool_by_weekday = df.groupby('开奖星期')['奖池滚存'].agg(['mean', 'min', 'max']).reindex(['周一', '周三', '周六'])

print("\n--- 按开奖星期统计全国销量 ---")
print(sales_by_weekday)
print("\n--- 按开奖星期统计奖池滚存 (均值, 最小值, 最大值) ---")
print(prize_pool_by_weekday)

# 可视化销售额
plt.figure(figsize=(10, 5))
sns.barplot(x=sales_by_weekday.index, y='sum', data=sales_by_weekday, palette='viridis')
plt.title('不同开奖日的全国总销量对比')
plt.xlabel('开奖星期')
plt.ylabel('全国总销量 (亿元)')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

#统计号码分布特征

# 统计不同开奖日的前区和后区号码频率
weekday_red_freq = {}
weekday_blue_freq = {}

for day in ['周一', '周三', '周六']:
    day_df = df[df['开奖星期'] == day]
    if not day_df.empty:
        # 展平该星期的所有红球和蓝球
        day_red_balls = [num for sublist in day_df['前区号码_list'] for num in sublist]
        day_blue_balls = [num for sublist in day_df['后区号码_list'] for num in sublist]

        weekday_red_freq[day] = Counter(day_red_balls)
        weekday_blue_freq[day] = Counter(day_blue_balls)
    else:
        weekday_red_freq[day] = Counter() # 空 Counter
        weekday_blue_freq[day] = Counter()


print("\n--- 不同开奖日的前区号码频率 (部分展示) ---")
for day, counts in weekday_red_freq.items():
    if counts:
        print(f"\n{day} 热门前区号码:")
        print(pd.DataFrame(counts.items(), columns=['号码', '频率']).sort_values(by='频率', ascending=False).head(5))
    else:
        print(f"\n{day} 无数据。")


print("\n--- 不同开奖日的后区号码频率 (部分展示) ---")
for day, counts in weekday_blue_freq.items():
    if counts:
        print(f"\n{day} 热门后区号码:")
        print(pd.DataFrame(counts.items(), columns=['号码', '频率']).sort_values(by='频率', ascending=False).head(3))
    else:
        print(f"\n{day} 无数据。")


# 可视化对比不同开奖日的号码分布（示例：只可视化最热门的几个）
# 由于号码范围较广，这里选择可视化不同周几的前区号码频率最高的几个，进行对比

# 创建一个包含所有号码和所有周几频率的DataFrame
all_red_numbers = sorted(list(set(all_red_balls)))
all_blue_numbers = sorted(list(set(all_blue_balls)))

red_freq_comparison_df = pd.DataFrame(index=all_red_numbers)
blue_freq_comparison_df = pd.DataFrame(index=all_blue_numbers)

for day, counts in weekday_red_freq.items():
    red_freq_comparison_df[day] = pd.Series(counts)
red_freq_comparison_df = red_freq_comparison_df.fillna(0) # 缺失值填充0

for day, counts in weekday_blue_freq.items():
    blue_freq_comparison_df[day] = pd.Series(counts)
blue_freq_comparison_df = blue_freq_comparison_df.fillna(0) # 缺失值填充0


# 绘制前区号码频率对比图 (前20个热门号码)
plt.figure(figsize=(18, 6))
red_freq_comparison_df.loc[red_freq_comparison_df.sum(axis=1).nlargest(20).index].plot(kind='bar', figsize=(15, 6), width=0.8)
plt.title('不同开奖日大乐透前区号码出现频率对比 (热门前20个号码)')
plt.xlabel('前区号码')
plt.ylabel('出现频率')
plt.xticks(rotation=45)
plt.legend(title='开奖星期')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# 绘制后区号码频率对比图 (所有号码)
plt.figure(figsize=(12, 5))
blue_freq_comparison_df.plot(kind='bar', figsize=(10, 5), width=0.8)
plt.title('不同开奖日大乐透后区号码出现频率对比')
plt.xlabel('后区号码')
plt.ylabel('出现频率')
plt.xticks(rotation=0)
plt.legend(title='开奖星期')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()





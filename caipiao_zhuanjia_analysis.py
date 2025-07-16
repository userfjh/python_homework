import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np # 导入 numpy 用于处理 NaN 值

# 设置 Matplotlib 支持中文显示
# !!! 修复: 将 'font.fontname' 改回 'font.sans-serif'
plt.rcParams['font.sans-serif'] = ['SimHei'] # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False # 解决保存图像时负号'-'显示为方块的问题

# --- 1. 数据加载与准备 ---
print("--- 1. 数据加载与准备 ---")
file_name = 'caipiao_zhuanjia_detailed_data.csv'
try:
    df = pd.read_csv(file_name)
    print(f"成功加载文件: {file_name}")
except FileNotFoundError:
    print(f"错误: 未找到文件 '{file_name}'。请确保文件在脚本的同一目录下。")
    exit() # 如果文件未找到，则退出脚本

# --- 数据清洗：将所有相关列转换为数值类型 ---
print("\n--- 数据清洗：转换所有奖项次数、彩龄和文章数量为数值类型 ---")

# 定义所有需要转换为数值的列
cols_to_numeric = [
    "双色球一等奖次数", "双色球二等奖次数", "双色球三等奖次数",
    "大乐透一等奖次数", "大乐透二等奖次数", "大乐透三等奖次数",
    "彩龄", "文章数量"
]

for col in cols_to_numeric:
    # 步骤1: 预清洗字符串，移除非数字字符（如“次”、“年”）
    # 将列转换为字符串类型，然后移除所有非数字和小数点的字符
    df[col + '_temp'] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)

    # 步骤2: 强制转换为数字，无法转换的设为NaN
    df[col] = pd.to_numeric(df[col + '_temp'], errors='coerce')

    # 打印转换后的 NaN 数量，帮助诊断
    print(f"转换后 '{col}' 列 NaN 数量: {df[col].isnull().sum()}")

    # 步骤3: 智能填充 NaN 值
    if df[col].isnull().all(): # 如果整列都是 NaN (即没有一个有效数字)
        print(f"警告: '{col}' 列在转换后全为 NaN。将使用 0 填充。")
        df[col] = df[col].fillna(0) # 用 0 填充
    else: # 如果不是全为 NaN，则用该列的有效中位数填充
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)

    # 步骤4: 确保转换为整数（对于奖项次数、彩龄和文章数量，通常应为整数）
    df[col] = df[col].astype(int)

# 删除临时列
df.drop(columns=[col + '_temp' for col in cols_to_numeric], inplace=True)


# --- 重新计算 '总一等奖次数' 和 '加权总奖金' ---
# 现在这些列已经是数值类型，可以安全地进行求和
df['总一等奖次数'] = df[[col for col in df.columns if '一等奖次数' in col]].sum(axis=1)

# 计算加权总奖金（您可以根据实际奖金比例调整权重）
df['加权总奖金'] = (df['双色球一等奖次数'] * 100 + df['大乐透一等奖次数'] * 100 +
                      df['双色球二等奖次数'] * 10 + df['大乐透二等奖次数'] * 10 +
                      df['双色球三等奖次数'] * 1 + df['大乐透三等奖次数'] * 1)

print("\n数据处理完成，已添加 '总一等奖次数' 和 '加权总奖金' 列。")
print("\n--- 数据摘要 ---")
print(df[['彩龄', '文章数量', '总一等奖次数', '加权总奖金']].describe())

# --- 2. 专家基本属性分布 ---
print("\n--- 2. 专家基本属性分布图 ---")
# 增加图形的整体大小来缓解 tight_layout 警告
plt.figure(figsize=(18, 7))

# 彩龄分布
plt.subplot(1, 2, 1)
sns.histplot(df['彩龄'], bins=10, kde=True)
plt.title('彩龄分布')
plt.xlabel('彩龄 (年)')
plt.ylabel('专家数量')

# 文章数量分布
plt.subplot(1, 2, 2)
sns.histplot(df['文章数量'], bins=10, kde=True)
plt.title('文章数量分布')
plt.xlabel('文章数量')
plt.ylabel('专家数量')

plt.tight_layout() # 尝试再次使用 tight_layout
plt.show()

# --- 3. 专家属性与中奖表现的关系 ---
print("\n--- 3. 专家属性与中奖表现关系图 ---")
# 增加图形的整体大小来缓解 tight_layout 警告
plt.figure(figsize=(20, 7)) # 调整图形宽度

# 彩龄 vs. 总一等奖次数
plt.subplot(1, 3, 1)
sns.scatterplot(x='彩龄', y='总一等奖次数', data=df, alpha=0.7)
plt.title('彩龄 vs. 总一等奖次数')
plt.xlabel('彩龄 (年)')
plt.ylabel('总一等奖次数')

# 文章数量 vs. 总一等奖次数
plt.subplot(1, 3, 2)
sns.scatterplot(x='文章数量', y='总一等奖次数', data=df, alpha=0.7)
plt.title('文章数量 vs. 总一等奖次数')
plt.xlabel('文章数量')
plt.ylabel('总一等奖次数')

# 彩龄 vs. 加权总奖金
plt.subplot(1, 3, 3)
sns.scatterplot(x='彩龄', y='加权总奖金', data=df, alpha=0.7)
plt.title('彩龄 vs. 加权总奖金')
plt.xlabel('彩龄 (年)')
plt.ylabel('加权总奖金')

plt.tight_layout() # 尝试再次使用 tight_layout
plt.show()

# --- 4. 属性对中奖率的影响（简化版）---
print("\n--- 4. 属性对中奖率的影响（简化版）图 ---")
# 彩龄分段图
plt.figure(figsize=(12, 6)) # 调整图形大小以获得更好的可读性

# 按彩龄分组的平均一等奖次数
df['彩龄_分段'] = pd.cut(df['彩龄'], bins=5, include_lowest=True) # 将彩龄分为5个等宽区间，包含最小值
avg_jackpot_by_age = df.groupby('彩龄_分段', observed=False)['总一等奖次数'].mean().reset_index()
sns.barplot(x='彩龄_分段', y='总一等奖次数', data=avg_jackpot_by_age, palette='viridis')
plt.title('不同彩龄区间的平均一等奖次数')
plt.xlabel('彩龄区间')
plt.ylabel('平均一等奖次数')
plt.xticks(rotation=45, ha='right') # 旋转标签并右对齐
plt.tight_layout()
plt.show()

# 文章数量分段图
plt.figure(figsize=(12, 6)) # 调整图形大小以获得更好的可读性

# 按文章数量分组的平均一等奖次数
df['文章数量_分段'] = pd.cut(df['文章数量'], bins=5, include_lowest=True) # 将文章数量分为5个等宽区间，包含最小值
avg_jackpot_by_articles = df.groupby('文章数量_分段', observed=False)['总一等奖次数'].mean().reset_index()
sns.barplot(x='文章数量_分段', y='总一等奖次数', data=avg_jackpot_by_articles, palette='magma')
plt.title('不同文章数量区间的平均一等奖次数')
plt.xlabel('文章数量区间')
plt.ylabel('平均一等奖次数')
plt.xticks(rotation=45, ha='right') # 旋转标签并右对齐
plt.tight_layout()
plt.show()

print("\n--- 所有分析和可视化已完成 ---")
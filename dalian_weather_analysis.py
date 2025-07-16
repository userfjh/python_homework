import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import re

# --- 设置Matplotlib中文字体 ---
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 推荐使用微软雅黑
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

# --- 1. 加载数据 ---
try:
    df = pd.read_csv('dalian_weather_data.csv', encoding='utf-8')
    print("数据加载成功！")
    print("原始数据前5行:")
    print(df.head())
    print("\n原始数据信息:")
    df.info()
except FileNotFoundError:
    print("错误：dalian_weather_data.csv 文件未找到。请确保文件与脚本在同一目录下。")
    exit()
except Exception as e:
    print(f"加载数据时发生错误: {e}")
    exit()

# --- 2. 数据清洗和预处理 (针对新数据样式进行改进，并添加夜晚数据解析) ---

# 2.1 日期解析
df['日期'] = df['日期'].str.replace('年', '-').str.replace('月', '-').str.replace('日', '')
df['日期'] = pd.to_datetime(df['日期'])
df['年份'] = df['日期'].dt.year
df['月份'] = df['日期'].dt.month

# 2.2 天气状况解析 (同时提取白天和夜晚)
def parse_weather(weather_str, day_or_night='day'):
    if isinstance(weather_str, str):
        parts = weather_str.split('/')
        if day_or_night == 'day' and len(parts) >= 1:
            return parts[0].strip()
        elif day_or_night == 'night' and len(parts) >= 2:
            return parts[1].strip()
    return np.nan

df['白天天气状况'] = df['天气状况'].apply(lambda x: parse_weather(x, 'day'))
df['夜晚天气状况'] = df['天气状况'].apply(lambda x: parse_weather(x, 'night'))


# 2.3 温度解析 (最高温度通常为白天，最低温度通常为夜晚)
def parse_temperature(temp_str, temp_type='max'):
    if isinstance(temp_str, str) and '℃' in temp_str:
        temps = temp_str.replace('℃', '').strip().split('/')
        try:
            if len(temps) == 2:
                max_t = int(temps[0].strip())
                min_t = int(temps[1].strip())
                return max_t if temp_type == 'max' else min_t
            elif len(temps) == 1:
                # 如果只有单个温度，根据上下文，通常是最高温度
                return int(temps[0].strip()) if temp_type == 'max' else np.nan
        except ValueError:
            return np.nan
    return np.nan

df['最高温度'] = df['温度'].apply(lambda x: parse_temperature(x, 'max'))
df['最低温度'] = df['温度'].apply(lambda x: parse_temperature(x, 'min')) # 这就是夜晚气温

# 2.4 风向风力解析 (同时提取白天和夜晚)
def parse_wind_force(wind_str, day_or_night='day'):
    if isinstance(wind_str, str):
        parts = wind_str.split('/')
        target_part = ''
        if day_or_night == 'day' and len(parts) >= 1:
            target_part = parts[0].strip()
        elif day_or_night == 'night' and len(parts) >= 2:
            target_part = parts[1].strip()

        if target_part:
            match = re.search(r'(\d+-\d+级|\d+级)', target_part)
            if match:
                return match.group(1)
    return np.nan

df['白天风力等级'] = df['风向风力'].apply(lambda x: parse_wind_force(x, 'day'))
df['夜晚风力等级'] = df['风向风力'].apply(lambda x: parse_wind_force(x, 'night'))


# 确保所有需要用到的列都是数值类型
numeric_cols = ['最高温度', '最低温度']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 检查清洗后的数据
print("\n清洗后的数据示例 (前5行，包含夜晚数据):")
print(df[['日期', '年份', '月份', '白天天气状况', '夜晚天气状况',
          '最高温度', '最低温度', '白天风力等级', '夜晚风力等级']].head())
print("\n清洗后的数据信息:")
df.info()

# --- 过滤分析数据到2024年 ---
df_analysis = df[df['年份'] <= 2024].copy() # 使用 .copy() 避免SettingWithCopyWarning

# --- 3. 任务2：绘制近三年月平均气温变化图 (最高温度和最低温度) ---
print("\n--- 任务2：绘制近三年月平均气温变化图 ---")

monthly_avg_temp = df_analysis.groupby('月份')[['最高温度', '最低温度']].mean().reset_index()

plt.figure(figsize=(12, 6))
plt.plot(monthly_avg_temp['月份'], monthly_avg_temp['最高温度'], marker='o', label='月平均最高温度 (白天)')
plt.plot(monthly_avg_temp['月份'], monthly_avg_temp['最低温度'], marker='o', label='月平均最低温度 (夜晚)')

plt.title('大连市2022-2024年月平均气温变化', fontsize=16)
plt.xlabel('月份', fontsize=12)
plt.ylabel('温度 (°C)', fontsize=12)
plt.xticks(range(1, 13), [f'{i}月' for i in range(1, 13)])
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()

# --- 4. 任务3：绘制近三年风力情况分布图 (白天和夜晚) ---
print("\n--- 任务3：绘制近三年风力情况分布图 ---")

# 填充NaN值以便统计
df_analysis['白天风力等级'] = df_analysis['白天风力等级'].fillna('未知')
df_analysis['夜晚风力等级'] = df_analysis['夜晚风力等级'].fillna('未知')

# 定义风力等级的显示顺序（如果需要）
wind_level_order = sorted(df_analysis['白天风力等级'].unique().tolist() + df_analysis['夜晚风力等级'].unique().tolist())
wind_level_order = [w for w in ['无风', '<3级', '3-4级', '4-5级', '5-6级', '6-7级', '7-8级', '8-9级', '>9级', '未知'] if w in wind_level_order]


# 白天风力分布
monthly_day_wind_distribution = df_analysis.groupby(['月份', '白天风力等级']).size().unstack(fill_value=0)
monthly_day_wind_distribution = monthly_day_wind_distribution[
    [col for col in wind_level_order if col in monthly_day_wind_distribution.columns]
]
monthly_day_wind_distribution.plot(kind='bar', figsize=(15, 8), width=0.8)
plt.title('大连市2022-2024年月度白天风力等级分布', fontsize=16)
plt.xlabel('月份', fontsize=12)
plt.ylabel('天数', fontsize=12)
plt.xticks(rotation=0)
plt.legend(title='风力等级', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# 夜晚风力分布
monthly_night_wind_distribution = df_analysis.groupby(['月份', '夜晚风力等级']).size().unstack(fill_value=0)
monthly_night_wind_distribution = monthly_night_wind_distribution[
    [col for col in wind_level_order if col in monthly_night_wind_distribution.columns]
]
monthly_night_wind_distribution.plot(kind='bar', figsize=(15, 8), width=0.8)
plt.title('大连市2022-2024年月度夜晚风力等级分布', fontsize=16)
plt.xlabel('月份', fontsize=12)
plt.ylabel('天数', fontsize=12)
plt.xticks(rotation=0)
plt.legend(title='风力等级', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()


# --- 5. 任务4：绘制近三年天气状况分布图 (白天和夜晚) ---
print("\n--- 任务4：绘制近三年天气状况分布图 ---")

df_analysis['白天天气状况'] = df_analysis['白天天气状况'].fillna('未知')
df_analysis['夜晚天气状况'] = df_analysis['夜晚天气状况'].fillna('未知')

# 白天天气状况分布
monthly_day_weather_distribution = df_analysis.groupby(['月份', '白天天气状况']).size().unstack(fill_value=0)
monthly_day_weather_distribution.plot(kind='bar', figsize=(15, 8), width=0.8)
plt.title('大连市2022-2024年月度白天天气状况分布', fontsize=16)
plt.xlabel('月份', fontsize=12)
plt.ylabel('天数', fontsize=12)
plt.xticks(rotation=0)
plt.legend(title='天气状况', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# 夜晚天气状况分布
monthly_night_weather_distribution = df_analysis.groupby(['月份', '夜晚天气状况']).size().unstack(fill_value=0)
monthly_night_weather_distribution.plot(kind='bar', figsize=(15, 8), width=0.8)
plt.title('大连市2022-2024年月度夜晚天气状况分布', fontsize=16)
plt.xlabel('月份', fontsize=12)
plt.ylabel('天数', fontsize=12)
plt.xticks(rotation=0)
plt.legend(title='天气状况', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# --- 6. 任务5：温度预测模型与2025年1-6月预测结果可视化 (最高温度) ---
# 此部分保持不变，因为预测的是月平均最高温度，且最低温度（夜晚气温）已在任务2中展示
print("\n--- 任务5：温度预测模型与2025年1-6月预测结果可视化 ---")

# 1. 训练温度预测模型（这里使用历史月份的平均最高温度作为预测值）
monthly_avg_max_temp_train = df_analysis.groupby('月份')['最高温度'].mean().reset_index()
monthly_avg_max_temp_train.rename(columns={'最高温度': '预测平均最高温度'}, inplace=True)

print("\n模型训练完成：2022-2024年各月平均最高温度作为预测基准。")
print(monthly_avg_max_temp_train)

# 2. 额外爬取2025年1-6月份数据
print("\n开始爬取2025年1-6月份数据...")

months_2025 = [f'{i:02d}' for i in range(1, 7)]
year_2025 = 2025
actual_2025_data = []

for month_str in months_2025:
    url = f"https://www.tianqihoubao.com/lishi/dalian/month/{year_2025}{month_str}.html"
    print(f"正在爬取 {year_2025}年{month_str}月 的数据: {url}")

    try:
        result = requests.get(url, timeout=10)
        result.raise_for_status()
        html = result.text
        page = BeautifulSoup(html, "html.parser")
        table = page.find("table", attrs={"class": "weather-table"})

        if table:
            tbody = table.find("tbody")
            if tbody:
                tr_table = tbody.find_all("tr")
                month_temps = []
                for tr in tr_table[1:]:
                    tds = tr.find_all("td")
                    if len(tds) >= 3:
                        temperature_str = tds[2].text.strip()
                        max_temp = parse_temperature(temperature_str, 'max')
                        if pd.notna(max_temp):
                            month_temps.append(max_temp)
                if month_temps:
                    actual_2025_data.append({
                        '月份': int(month_str),
                        '2025年实际月平均最高温度': np.mean(month_temps)
                    })
                else:
                    print(f"  {year_2025}年{month_str}月 未能提取到有效温度数据。")
            else:
                print(f"  未在 {url} 找到 tbody 元素。")
        else:
            print(f"  未在 {url} 找到 class 为 'weather-table' 的表格。")
    except requests.exceptions.RequestException as e:
        print(f"  请求 {url} 时发生错误: {e}")
    except Exception as e:
        print(f"  处理 {url} 时发生未知错误: {e}")
    time.sleep(1)

actual_2025_df = pd.DataFrame(actual_2025_data)
print("\n2025年1-6月实际数据爬取完成:")
print(actual_2025_df)

# 3. 合并预测结果和真实结果
merged_prediction_actual = pd.merge(monthly_avg_max_temp_train, actual_2025_df, on='月份', how='inner')

# 4. 绘制预测结果和真实结果曲线
plt.figure(figsize=(12, 6))
plt.plot(merged_prediction_actual['月份'], merged_prediction_actual['预测平均最高温度'], marker='o', label='预测平均最高温度 (2022-2024年平均)')
plt.plot(merged_prediction_actual['月份'], merged_prediction_actual['2025年实际月平均最高温度'], marker='x', linestyle='--', label='2025年实际月平均最高温度')

plt.title('大连市2025年1-6月平均最高温度预测与实际对比', fontsize=16)
plt.xlabel('月份', fontsize=12)
plt.ylabel('温度 (°C)', fontsize=12)
plt.xticks(merged_prediction_actual['月份'], [f'{m}月' for m in merged_prediction_actual['月份']])
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()

print("\n所有分析和预测任务完成！")
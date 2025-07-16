import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from tqdm import tqdm
import os
import matplotlib as mpl

# 设置中文字体支持 - 解决乱码问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']  # 中文字体列表
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 创建缓存目录
os.makedirs('cache', exist_ok=True)
os.makedirs('results_1', exist_ok=True)


def crawl_hurun_rich_list():
    """爬取胡润富豪榜数据"""
    # 检查缓存文件是否存在
    cache_file = 'cache/hurun_rich_list.csv'
    if os.path.exists(cache_file):
        print("使用缓存数据...")
        return pd.read_csv(cache_file)

    base_url = "https://www.hurun.net/zh-CN/Rank/HsRankDetailsList?num=ODBYW2BI&search=&offset={}&limit=200"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.hurun.net/zh-CN/Rank/HsRankDetails?pagetype=rich'
    }

    all_data = []
    print("开始爬取胡润富豪榜数据...")
    for page in tqdm(range(6)):  # 分页爬取1094条数据
        offset = page * 200
        url = base_url.format(offset)
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            for item in data.get('rows', []):
                # 检查是否有有效的人物数据
                if 'hs_Character' not in item or not item['hs_Character']:
                    continue

                # 提取核心字段：排名/财富/公司/行业
                record = {
                    '排名': item.get('hs_Rank_Rich_Ranking'),
                    '财富值(亿人民币)': item.get('hs_Rank_Rich_Wealth'),
                    '公司': item.get('hs_Rank_Rich_ComName_Cn'),
                    '行业': item.get('hs_Rank_Rich_Industry_Cn'),
                    '姓名': item['hs_Character'][0].get('hs_Character_Fullname_Cn'),
                    '年龄': item['hs_Character'][0].get('hs_Character_Age'),
                    '出生地': item['hs_Character'][0].get('hs_Character_BirthPlace_Cn'),
                    '性别': item['hs_Character'][0].get('hs_Character_Gender')
                }
                all_data.append(record)
        except Exception as e:
            print(f"爬取第 {page + 1} 页时出错: {e}")

    df = pd.DataFrame(all_data)
    print(f"成功爬取 {len(df)} 条富豪数据")

    # 保存到缓存
    df.to_csv(cache_file, index=False)
    print(f"数据已缓存至 {cache_file}")
    return df


def clean_data(df):
    """数据清洗与预处理"""
    print("\n开始数据清洗...")

    # 转换数值型数据
    df['财富值(亿人民币)'] = pd.to_numeric(df['财富值(亿人民币)'], errors='coerce')
    df['年龄'] = pd.to_numeric(df['年龄'], errors='coerce')

    # 提取省份信息 - 更智能的解析
    def extract_province(location):
        if not isinstance(location, str):
            return '未知'

        # 处理直辖市
        if '北京' in location:
            return '北京'
        if '上海' in location:
            return '上海'
        if '天津' in location:
            return '天津'
        if '重庆' in location:
            return '重庆'

        # 处理特别行政区
        if '香港' in location:
            return '香港'
        if '澳门' in location:
            return '澳门'
        if '台湾' in location:
            return '台湾'

        # 处理有分隔符的情况
        if '-' in location:
            parts = location.split('-')
            if len(parts) > 1:
                # 尝试识别省份部分
                for part in parts:
                    if '省' in part or '自治区' in part or '特别行政区' in part:
                        return part
                return parts[1]  # 默认取第二部分
        return location  # 无法解析时返回原值

    df['出生省份'] = df['出生地'].apply(extract_province)

    # 简化省份名称
    df['出生省份'] = df['出生省份'].str.replace('省|市|自治区|特别行政区|壮族|回族|维吾尔', '', regex=True)

    # 性别处理
    df['性别'] = df['性别'].fillna('未知')
    df['性别'] = df['性别'].replace({'男': '男性', '女': '女性'})

    # 过滤无效记录
    orig_count = len(df)
    df = df.dropna(subset=['姓名', '财富值(亿人民币)'])
    new_count = len(df)

    print(f"清洗后保留 {new_count} 条有效数据 (移除了 {orig_count - new_count} 条无效记录)")
    return df


def analyze_industry_trend(df):
    """行业趋势分析"""
    print("\n进行行业趋势分析...")

    # 按行业分组统计
    industry_stats = df.groupby('行业').agg(
        富豪数量=('姓名', 'count'),
        总财富=('财富值(亿人民币)', 'sum'),
        平均财富=('财富值(亿人民币)', 'mean')
    ).sort_values('富豪数量', ascending=False)

    # 绘制TOP15行业分析
    top_15 = industry_stats.head(15)

    plt.figure(figsize=(16, 12))
    sns.barplot(x='富豪数量', y=top_15.index, data=top_15, palette='viridis')
    plt.title('TOP15行业富豪数量分布', fontsize=18)
    plt.xlabel('富豪数量', fontsize=14)
    plt.ylabel('行业', fontsize=14)
    plt.tight_layout()
    plt.savefig('results_1/industry_analysis.png', dpi=300)
    plt.close()
    print("行业分析图表已保存至 results_1/industry_analysis.png")

    # 绘制财富气泡图
    plt.figure(figsize=(16, 12))
    top_15 = industry_stats.head(10)
    sns.scatterplot(
        x='富豪数量',
        y='平均财富',
        size='总财富',
        sizes=(100, 2000),
        hue=top_15.index,
        data=top_15,
        palette='tab20',
        legend='brief'
    )
    plt.title('行业富豪数量与财富分布关系', fontsize=18)
    plt.xlabel('富豪数量', fontsize=14)
    plt.ylabel('平均财富(亿人民币)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('results_1/industry_bubble.png', dpi=300)
    plt.close()

    return industry_stats


def analyze_demographics(df):
    """人口统计特征分析"""
    print("\n进行人口统计特征分析...")

    # 创建图表
    plt.figure(figsize=(18, 14))

    # 1. 年龄分布分析
    plt.subplot(2, 2, 1)
    sns.histplot(df['年龄'].dropna(), bins=20, kde=True, color='skyblue')
    plt.axvline(df['年龄'].mean(), color='red', linestyle='--',
                label=f'平均年龄: {df["年龄"].mean():.1f}岁')
    plt.axvline(df['年龄'].median(), color='green', linestyle='--',
                label=f'中位年龄: {df["年龄"].median()}岁')
    plt.title('富豪年龄分布', fontsize=16)
    plt.xlabel('年龄', fontsize=12)
    plt.ylabel('人数', fontsize=12)
    plt.legend(fontsize=12)

    # 2. 年龄与财富关系
    plt.subplot(2, 2, 2)
    sns.regplot(
        x='年龄',
        y='财富值(亿人民币)',
        data=df,
        scatter_kws={'alpha': 0.5, 'color': 'blue'},
        line_kws={'color': 'red', 'linewidth': 2.5}
    )
    plt.title('年龄与财富关系', fontsize=16)
    plt.xlabel('年龄', fontsize=12)
    plt.ylabel('财富值(亿人民币)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.3)

    # 3. 性别分布
    plt.subplot(2, 2, 3)
    gender_count = df['性别'].value_counts()
    gender_count.plot.pie(
        autopct='%1.1f%%',
        colors=['#66b3ff', '#ff9999', '#99ff99'],
        startangle=90,
        explode=(0.05, 0.05, 0.05),
        textprops={'fontsize': 12}
    )
    plt.title('富豪性别分布', fontsize=16)
    plt.ylabel('')

    # 4. 财富金字塔
    plt.subplot(2, 2, 4)
    bins = [0, 10, 50, 100, 500, 1000, float('inf')]
    labels = ['<10亿', '10-50亿', '50-100亿', '100-500亿', '500-1000亿', '>1000亿']
    df['财富等级'] = pd.cut(df['财富值(亿人民币)'], bins=bins, labels=labels)
    wealth_level_count = df['财富等级'].value_counts().reindex(labels)
    sns.barplot(x=wealth_level_count.values, y=wealth_level_count.index, palette='magma')
    plt.title('财富等级分布', fontsize=16)
    plt.xlabel('人数', fontsize=12)
    plt.ylabel('财富等级', fontsize=12)

    plt.tight_layout()
    plt.savefig('results_1/demographics_analysis.png', dpi=300)
    plt.close()
    print("人口统计图表已保存至 results_1/demographics_analysis.png")


def analyze_age_wealth_heatmap(df):
    """年龄与财富关系热力图"""
    print("\n生成年龄-财富热力图...")

    # 创建年龄分组和财富等级
    df['年龄分组'] = pd.cut(df['年龄'], bins=[0, 40, 50, 60, 70, 100],
                            labels=['40岁以下', '41-50岁', '51-60岁', '61-70岁', '70岁以上'])
    bins = [0, 50, 100, 500, 1000, float('inf')]
    labels = ['<50亿', '50-100亿', '100-500亿', '500-1000亿', '>1000亿']
    df['财富等级'] = pd.cut(df['财富值(亿人民币)'], bins=bins, labels=labels)

    # 创建交叉表
    heatmap_data = pd.crosstab(df['年龄分组'], df['财富等级'], normalize='index')

    plt.figure(figsize=(14, 10))
    sns.heatmap(heatmap_data, annot=True, cmap="YlGnBu", fmt='.1%', annot_kws={"size": 12})
    plt.title('不同年龄段的财富分布比例', fontsize=18)
    plt.xlabel('财富等级', fontsize=14)
    plt.ylabel('年龄分组', fontsize=14)
    plt.tight_layout()
    plt.savefig('results_1/age_wealth_heatmap.png', dpi=300)
    plt.close()
    print("热力图已保存至 results_1/age_wealth_heatmap.png")


def generate_geographical_distribution(df):
    """地理分布分析"""
    print("\n分析出生地分布...")

    # 出生省份TOP15
    plt.figure(figsize=(14, 10))
    province_counts = df['出生省份'].value_counts()

    # 合并小省份为"其他"
    threshold = 10  # 只显示数量大于阈值的省份
    top_provinces = province_counts[province_counts > threshold]
    other_count = province_counts[province_counts <= threshold].sum()

    if other_count > 0:
        top_provinces['其他'] = other_count

    top_provinces = top_provinces.sort_values(ascending=False)

    # 绘制图表
    sns.barplot(x=top_provinces.values, y=top_provinces.index, palette='rocket')
    plt.title('富豪出生地分布', fontsize=18)
    plt.xlabel('富豪人数', fontsize=14)
    plt.ylabel('地区', fontsize=14)
    plt.tight_layout()
    plt.savefig('results_1/birthplace_distribution.png', dpi=300)
    plt.close()

    # 绘制地图分布
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        # 创建中国地图可视化
        china_map = gpd.read_file('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')

        # 创建地理坐标数据
        province_coords = {
            '广东': [113.23, 23.16], '浙江': [120.15, 30.28], '江苏': [118.76, 32.04],
            '福建': [119.3, 26.08], '上海': [121.47, 31.23], '北京': [116.4, 39.9],
            '山东': [117.0, 36.65], '四川': [104.06, 30.67], '湖南': [112.97, 28.19],
            '湖北': [114.30, 30.60], '安徽': [117.28, 31.86], '河南': [113.65, 34.76],
            '香港': [114.16, 22.28], '台湾': [121.50, 25.03], '辽宁': [123.38, 41.8],
            '重庆': [106.55, 29.57], '江西': [115.89, 28.68], '河北': [114.48, 38.03],
            '陕西': [108.93, 34.27], '吉林': [125.32, 43.88]
        }

        # 创建地理DataFrame
        geo_df = pd.DataFrame({
            '省份': list(province_coords.keys()),
            '经度': [coord[0] for coord in province_coords.values()],
            '纬度': [coord[1] for coord in province_coords.values()],
            '富豪数量': [province_counts.get(prov, 0) for prov in province_coords.keys()]
        })

        # 创建点几何
        geometry = [Point(lon, lat) for lon, lat in zip(geo_df['经度'], geo_df['纬度'])]
        geo_df = gpd.GeoDataFrame(geo_df, geometry=geometry, crs="EPSG:4326")

        # 绘制地图
        fig, ax = plt.subplots(figsize=(16, 12))
        china_map.plot(ax=ax, color='#f0f0f0', edgecolor='#999999')

        # 绘制散点图
        geo_df.plot(
            ax=ax,
            markersize=geo_df['富豪数量'] * 0.5,
            color='red',
            alpha=0.7,
            edgecolor='black',
            linewidth=0.5,
            legend=True
        )

        # 添加省份标签
        for x, y, prov, count in zip(geo_df['经度'], geo_df['纬度'], geo_df['省份'], geo_df['富豪数量']):
            plt.text(x, y, f"{prov}\n{count}人", fontsize=9, ha='center', va='center')

        plt.title('中国富豪出生地分布热力图', fontsize=18)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('results_1/birthplace_map.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("地理分布地图已保存至 results_1/birthplace_map.png")
    except ImportError:
        print("未安装geopandas，跳过地图生成")
    except Exception as e:
        print(f"生成地图时出错: {e}")

    print("地理分布图表已保存至 results_1/birthplace_distribution.png")
    return province_counts


def generate_wealth_distribution(df):
    """财富分布分析"""
    print("\n分析财富分布...")

    # 财富值对数转换
    df['财富对数'] = np.log10(df['财富值(亿人民币)'])

    plt.figure(figsize=(16, 12))

    # 1. 财富分布直方图
    plt.subplot(2, 2, 1)
    sns.histplot(df['财富值(亿人民币)'], bins=50, kde=True, color='purple')
    plt.title('财富值分布', fontsize=16)
    plt.xlabel('财富值(亿人民币)', fontsize=12)
    plt.ylabel('人数', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.3)

    # 2. 对数转换后的分布
    plt.subplot(2, 2, 2)
    sns.histplot(df['财富对数'], bins=30, kde=True, color='orange')
    plt.title('财富值(对数)分布', fontsize=16)
    plt.xlabel('财富值对数(log10)', fontsize=12)
    plt.ylabel('人数', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.3)

    # 3. 财富箱线图
    plt.subplot(2, 2, 3)
    sns.boxplot(x=df['财富值(亿人民币)'], color='skyblue')
    plt.title('财富值箱线图', fontsize=16)
    plt.xlabel('财富值(亿人民币)', fontsize=12)

    # 4. 财富与年龄关系
    plt.subplot(2, 2, 4)
    sns.scatterplot(x='年龄', y='财富值(亿人民币)', data=df, alpha=0.6, color='green')
    plt.title('年龄与财富关系', fontsize=16)
    plt.xlabel('年龄', fontsize=12)
    plt.ylabel('财富值(亿人民币)', fontsize=12)
    plt.yscale('log')

    plt.tight_layout()
    plt.savefig('results_1/wealth_distribution.png', dpi=300)
    plt.close()
    print("财富分布图表已保存至 results_1/wealth_distribution.png")


def main():
    """主函数"""
    print("=" * 50)
    print("胡润富豪榜数据分析")
    print("=" * 50)

    # 1. 爬取数据
    df = crawl_hurun_rich_list()

    # 2. 数据清洗
    df_clean = clean_data(df)

    # 3. 行业趋势分析
    industry_stats = analyze_industry_trend(df_clean)

    # 4. 人口统计特征分析
    analyze_demographics(df_clean)

    # 5. 年龄-财富热力图分析
    analyze_age_wealth_heatmap(df_clean)

    # 6. 地理分布分析
    geo_distribution = generate_geographical_distribution(df_clean)

    # 7. 财富分布分析
    generate_wealth_distribution(df_clean)

    # 保存处理后的数据
    df_clean.to_csv('results_1/rich_list_clean.csv', index=False)
    industry_stats.to_csv('results_1/industry_stats.csv')
    geo_distribution.to_csv('results_1/geo_distribution.csv')

    print("\n" + "=" * 50)
    print("分析完成!")
    print(f"所有结果已保存至 results_1 目录")
    print("=" * 50)


if __name__ == "__main__":
    main()
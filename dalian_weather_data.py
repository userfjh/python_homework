import requests
from bs4 import BeautifulSoup
import time # 导入time模块用于添加延迟

# 定义要爬取的年份和月份
years = [2022, 2023, 2024]
months = [f"{i:02d}" for i in range(1, 13)] # 生成01, 02, ..., 12

# 打开CSV文件，以写入模式（'w'）并指定UTF-8编码
# 如果文件不存在，会自动创建；如果文件已存在，会覆盖原有内容
f = open("dalian_weather_data.csv", mode="w", encoding="utf-8")

# 写入CSV文件头
f.write("日期,天气状况,温度,风向风力\n")

print("开始爬取大连天气数据...")

# 循环遍历每一年
for year in years:
    # 循环遍历每一个月
    for month in months:
        # 动态构建URL
        url = f"https://www.tianqihoubao.com/lishi/dalian/month/{year}{month}.html"
        print(f"正在爬取 {year}年{month}月 的数据: {url}")

        try:
            # 发送HTTP GET请求获取网页内容
            result = requests.get(url, timeout=10) # 设置超时时间
            result.raise_for_status() # 检查请求是否成功，如果状态码不是200，则抛出HTTPError异常
            html = result.text

            # 使用BeautifulSoup解析HTML
            page = BeautifulSoup(html, "html.parser")

            # 查找目标表格
            table = page.find("table", attrs={"class": "weather-table"})

            # 检查是否找到表格
            if table:
                tbody = table.find("tbody")
                if tbody:
                    expected_td_count = 4 # 期望每行有4个td元素 防止出现空格行分割行

                    tr_table = tbody.find_all("tr")
                    for tr in tr_table:
                        tds = tr.find_all("td")
                        # 检查tds的数量，跳过不符合预期的行（例如表头行）
                        if len(tds) == expected_td_count:
                            # 提取文本内容并去除多余的空白符
                            date = tds[0].text.strip()
                            weather_condition = tds[1].text.strip()
                            temperature = tds[2].text.strip()
                            wind_direction_force = tds[3].text.strip()

                            # 打印到控制台
                            #print(f"  {date}, {weather_condition}, {temperature}, {wind_direction_force}")
                            # 写入CSV文件
                            f.write(f'{date},{weather_condition},{temperature},{wind_direction_force}\n')
                        # else:
                        #     # 可以选择在这里打印跳过的行信息，用于调试
                        #     # print(f"  跳过不符合预期的行: {len(tds)}个tds")
                            continue
                else:
                    print(f"  未在 {url} 找到 tbody 元素。")
            else:
                print(f"  未在 {url} 找到 class 为 'weather-table' 的表格。")

        except requests.exceptions.RequestException as e:
            print(f"  请求 {url} 时发生错误: {e}")
        except AttributeError as e:
            print(f"  解析HTML时发生错误 (可能元素未找到): {e}")
        except Exception as e:
            print(f"  处理 {url} 时发生未知错误: {e}")

        # 为了避免对服务器造成过大压力，每次请求后暂停一小段时间
        time.sleep(1) # 暂停1秒

# 关闭文件
f.close()

print("所有数据爬取完毕，并已保存到 dalian_weather_data.csv 文件中。")

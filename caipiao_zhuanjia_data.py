import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- 配置项 ---
# 目标网页URL
URL = "http://www.cmzj.net/dlt/tickets"
# CSV文件名称
CSV_FILE_NAME = "caipiao_zhuanjia_detailed_data.csv"
# 目标抓取专家数量
MAX_EXPERTS_TO_SCRAPE = 20
# 最大尝试抓取页数，防止无限循环
MAX_PAGES_TO_CHECK = 50

# --- 初始化 WebDriver ---
print("正在启动 Chrome 浏览器...")
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # 如果你想在后台运行浏览器，取消注释此行
# options.add_argument("--disable-gpu") # 禁用 GPU 硬件加速，有时在无头模式下需要
# options.add_argument("--window-size=1920,1080") # 设置窗口大小，确保元素可见

web = webdriver.Chrome(options=options)
web.get(URL)
print(f"已打开网页: {URL}")

# 用于存储所有唯一专家数据的列表
all_expert_data = []
# 用于存储已抓取专家名称的集合，以便去重
scraped_expert_names = set()

# CSV 文件头部，现在包含详细的奖项次数、彩龄和文章数量字段
csv_headers = [
    "专家名称",
    "双色球一等奖次数",
    "双色球二等奖次数",
    "双色球三等奖次数",
    "大乐透一等奖次数",
    "大乐透二等奖次数",
    "大乐透三等奖次数",
    "彩龄",
    "文章数量"
]

# --- 循环访问专家信息 ---
# 专家的 XPath 模式：注意到 div[1] 到 div[8] 的变化
# 这个 XPath 定位的是每个专家条目中的那个可点击的 <p> 元素
base_click_xpath_pattern = '//*[@id="app"]/div[3]/div/div[2]/div[2]/div[{}]/div[2]/div[2]/div[1]/p'

# 专家容器的 XPath 模式：这个 XPath 定位的是包含每个专家所有信息的父 div
# 我们将在这个父 div 内部查找名称
expert_container_xpath_pattern = '//*[@id="app"]/div[3]/div/div[2]/div[2]/div[{}]'

# 下一页按钮的 XPath
next_page_button_xpath = '//*[@id="app"]/div[3]/div/div[2]/div[1]/div[1]/p'

print(f"开始抓取专家信息，目标数量: {MAX_EXPERTS_TO_SCRAPE} 位专家。")

page_count = 0
while len(all_expert_data) < MAX_EXPERTS_TO_SCRAPE and page_count < MAX_PAGES_TO_CHECK:
    page_count += 1
    print(f"\n--- 正在抓取第 {page_count} 页专家信息 ---")

    # 循环遍历当前页面的 8 位专家
    for i in range(1, 9):
        # 如果已经达到目标专家数量，则停止抓取
        if len(all_expert_data) >= MAX_EXPERTS_TO_SCRAPE:
            print(f"已达到目标专家数量 ({MAX_EXPERTS_TO_SCRAPE}个)，停止抓取。")
            break

        try:
            # 1. 构造当前专家的点击按钮 XPath
            current_click_xpath = base_click_xpath_pattern.format(i)

            # 2. 找到并滚动到可点击的按钮
            # 使用 JavaScript 滚动元素到视图中，确保即使被遮挡也能找到
            expert_button = WebDriverWait(web, 10).until(
                EC.presence_of_element_located((By.XPATH, current_click_xpath))
            )
            web.execute_script("arguments[0].scrollIntoView(true);", expert_button)

            # 3. 等待按钮可点击并点击
            WebDriverWait(web, 10).until(
                EC.element_to_be_clickable((By.XPATH, current_click_xpath))
            )

            # 存储主列表页窗口的句柄
            main_window_handle = web.current_window_handle
            print(f"主窗口句柄: {main_window_handle}")

            # 点击前获取当前所有窗口句柄
            old_window_handles = set(web.window_handles)

            expert_button.click()
            print(f"已点击第 {i} 位专家按钮。")

            # 4. 等待新窗口打开并切换到它
            # 等待窗口句柄数量增加
            WebDriverWait(web, 10).until(
                EC.number_of_windows_to_be(len(old_window_handles) + 1)
            )

            # 获取所有当前窗口句柄
            new_window_handles = set(web.window_handles)
            # 通过与旧句柄比较找到新窗口的句柄
            new_window_handle = (new_window_handles - old_window_handles).pop()

            # 切换到新的专家详情页窗口
            web.switch_to.window(new_window_handle)
            print(f"已切换到新窗口: {new_window_handle}")
            time.sleep(2)  # 给一些时间让新页面加载内容

            # 5. 提取专家名称 (假设名称在详情页上也可获取或可推断)
            # 如果名称不可直接获取或需要重新提取，请调整此处。
            # 为了简单起见，我们假设仍然可以从详情页获取名称或使用列表中的名称。
            # 尝试从详情页获取名称，因为列表页的元素可能已不存在。
            name = "N/A"
            try:
                # 假设专家名称在详情页上是 h1 标签或特定类名中
                # 你可能需要调整此 XPath/选择器以适应详情页
                name_element = WebDriverWait(web, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[1]/p'))
                    # 详情页名称的示例 XPath
                )
                name = name_element.text
            except Exception as e:
                print(f"从详情页获取专家名称失败: {e}。使用 N/A。")

            # 6. 检查是否为重复专家，如果不是则添加详细信息
            if name != "N/A" and name not in scraped_expert_names:
                print(f"正在抓取新专家 '{name}' 的详细信息 (当前总数: {len(all_expert_data)})")

                # 将所有奖项次数的默认值设置为 0，彩龄和文章数量保持 N/A
                detailed_info = {
                    "双色球一等奖次数": 0,
                    "双色球二等奖次数": 0,
                    "双色球三等奖次数": 0,
                    "大乐透一等奖次数": 0,
                    "大乐透二等奖次数": 0,
                    "大乐透三等奖次数": 0,
                    "彩龄": "N/A",
                    "文章数量": "N/A"
                }

                # --- 从专家详情页抓取详细数据 ---
                # 使用用户提供的 XPath
                try:
                    # 双色球一等奖次数
                    ssq_first_prize_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[5]/div[1]/div[1]/span'))
                    )
                    detailed_info["双色球一等奖次数"] = ssq_first_prize_element.text
                except Exception as e:
                    print(f"获取 '{name}' 双色球一等奖次数失败: {e}。控制台显示 '暂无获奖经历'。")
                    # 抓取失败时，CSV 中保存为 0，但控制台提示“暂无获奖经历”
                    detailed_info["双色球一等奖次数"] = 0

                try:
                    # 双色球二等奖次数
                    ssq_second_prize_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[5]/div[1]/div[2]/span'))
                    )
                    detailed_info["双色球二等奖次数"] = ssq_second_prize_element.text
                except Exception as e:
                    print(f"获取 '{name}' 双色球二等奖次数失败: {e}。控制台显示 '暂无获奖经历'。")
                    detailed_info["双色球二等奖次数"] = 0

                try:
                    # 双色球三等奖次数
                    ssq_third_prize_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[5]/div[1]/div[3]/span'))
                    )
                    detailed_info["双色球三等奖次数"] = ssq_third_prize_element.text
                except Exception as e:
                    print(f"获取 '{name}' 双色球三等奖次数失败: {e}。控制台显示 '暂无获奖经历'。")
                    detailed_info["双色球三等奖次数"] = 0

                try:
                    # 大乐透一等奖次数
                    dlt_first_prize_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[5]/div[2]/div[1]/span'))
                    )
                    detailed_info["大乐透一等奖次数"] = dlt_first_prize_element.text
                except Exception as e:
                    print(f"获取 '{name}' 大乐透一等奖次数失败: {e}。控制台显示 '暂无获奖经历'。")
                    detailed_info["大乐透一等奖次数"] = 0

                try:
                    # 大乐透二等奖次数
                    dlt_second_prize_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[5]/div[2]/div[2]/span'))
                    )
                    detailed_info["大乐透二等奖次数"] = dlt_second_prize_element.text
                except Exception as e:
                    print(f"获取 '{name}' 大乐透二等奖次数失败: {e}。控制台显示 '暂无获奖经历'。")
                    detailed_info["大乐透二等奖次数"] = 0

                try:
                    # 大乐透三等奖次数
                    dlt_third_prize_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[5]/div[2]/div[3]/span'))
                    )
                    detailed_info["大乐透三等奖次数"] = dlt_third_prize_element.text
                except Exception as e:
                    print(f"获取 '{name}' 大乐透三等奖次数失败: {e}。控制台显示 '暂无获奖经历'。")
                    detailed_info["大乐透三等奖次数"] = 0

                try:
                    # 彩龄
                    age_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[1]/span'))
                    )
                    detailed_info["彩龄"] = age_element.text
                except Exception as e:
                    print(f"获取 '{name}' 彩龄失败: {e}")

                try:
                    # 文章数量
                    article_count_element = WebDriverWait(web, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//*[@id="app"]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p[2]/span'))
                    )
                    detailed_info["文章数量"] = article_count_element.text
                except Exception as e:
                    print(f"获取 '{name}' 文章数量失败: {e}")

                # 将专家名称和详细信息添加到列表中
                expert_info = {"专家名称": name, **detailed_info}
                all_expert_data.append(expert_info)
                scraped_expert_names.add(name)

                # --- 关闭当前专家详情页窗口并切换回主窗口 ---
                web.close()
                print(f"已关闭专家 '{name}' 的详情页窗口。")
                # 切换回主列表页窗口
                web.switch_to.window(main_window_handle)
                print(f"已切换回主窗口: {main_window_handle}")
                time.sleep(1)  # 给一些时间让主页面稳定下来
            else:
                print(f"专家 '{name}' 已存在或无法识别，跳过。")
                # 如果专家是重复的或无法识别，关闭新窗口并切换回主窗口
                web.close()
                web.switch_to.window(main_window_handle)
                time.sleep(1)


        except Exception as e:
            print(f"抓取第 {i} 位专家信息时发生错误: {e}")
            # 如果在抓取专家时发生错误（例如，新窗口未能打开），
            # 尝试切换回主窗口（如果可能），然后继续处理下一个专家。
            try:
                if len(web.window_handles) > 1:  # 如果打开了新窗口但失败了
                    web.close()
                web.switch_to.window(main_window_handle)
                print("尝试从错误中恢复，已切换回主窗口。")
                time.sleep(1)
            except:
                print("无法恢复到主窗口，作为备用方案重新加载主页。")
                web.get(URL)  # 重新加载主页作为备用方案
                time.sleep(2)
            continue

    # 处理完当前页的所有专家后，检查是否需要点击下一页
    if len(all_expert_data) >= MAX_EXPERTS_TO_SCRAPE:
        print("已达到目标专家数量，停止翻页。")
        break  # 达到目标数量，跳出外层循环

    # 尝试点击下一页按钮
    try:
        print(f"尝试点击下一页按钮，XPath: {next_page_button_xpath}")
        next_btn = WebDriverWait(web, 10).until(
            EC.presence_of_element_located((By.XPATH, next_page_button_xpath))
        )
        # 再次使用 JavaScript 滚动，确保按钮可见
        web.execute_script("arguments[0].scrollIntoView(true);", next_btn)
        WebDriverWait(web, 10).until(
            EC.element_to_be_clickable((By.XPATH, next_page_button_xpath))
        )
        next_btn.click()
        print("成功点击下一页按钮。")
        # 给予页面足够时间刷新和加载新内容
        time.sleep(2)
    except Exception as e:
        print(f"未能点击下一页按钮或已是最后一页: {e}")
        break  # 如果找不到下一页按钮或无法点击，则认为已到达最后一页，停止循环

print(f"\n所有专家信息抓取完毕。总共抓取到 {len(all_expert_data)} 位专家。")

# --- 将数据写入 CSV 文件 ---
print(f"正在将数据写入 {CSV_FILE_NAME}...")
try:
    with open(CSV_FILE_NAME, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()  # 写入 CSV 头部
        writer.writerows(all_expert_data)  # 写入所有行
    print(f"数据已成功写入 {CSV_FILE_NAME}")
except Exception as e:
    print(f"写入 CSV 文件时发生错误: {e}")

# --- 保持浏览器打开直到用户输入 ---
print("\n浏览器将保持打开状态，直到你在控制台按下回车键...")
input()  # 程序暂停，等待用户在控制台按下回车键

# --- 关闭浏览器 ---
web.quit()
print("浏览器已关闭。")

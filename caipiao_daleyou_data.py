import csv
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- 配置项 ---
# 目标网页URL
URL = "https://www.zhcw.com/kjxx/dlt/"
# CSV文件名称
CSV_FILE_NAME = "caipiao_daletou.csv"

# 定义要提取的表格列及其在CSV中的名称和提取类型
# 'td_index' 是该列在 HTML <tr> 中的索引（从1开始）
# 'type' 指示提取方式：'text' 为直接提取文本，'red_balls'/'blue_balls' 为提取内部多个 span 标签
COLUMNS_TO_EXTRACT = {
    '期号': {'td_index': 1, 'type': 'text'},
    '开奖日期': {'td_index': 2, 'type': 'text'},
    '前区号码': {'td_index': 3, 'type': 'red_balls'},
    '后区号码': {'td_index': 4, 'type': 'blue_balls'},
    '全国销量': {'td_index': 5, 'type': 'text'},
    '奖池滚存': {'td_index': 14, 'type': 'text'}
}

# 定义需要点击的分页按钮对应的 li 索引
# 假设你的分页按钮结构为：上一页 | 1 | 2 | 3 | 4 | 下一页
# 那么：li[3] 对应页面上的 "2"（第二页）
#       li[4] 对应页面上的 "3"（第三页）
#       li[5] 对应页面上的 "4"（第四页）
# **请务必根据实际网页结构在浏览器开发者工具中确认这些索引！**
PAGE_BUTTON_INDICES = [3, 4, 5]

# --- 初始化 WebDriver ---
print("正在启动 Chrome 浏览器...")
web = Chrome()
web.get(URL)
print(f"已打开网页: {URL}")

# --- 前置操作：确保页面加载并执行初始点击和输入 ---
# 这部分操作只执行一次，以达到显示查询结果的页面状态
try:
    # 点击第一个按钮，例如“玩法介绍”或“开奖详情”
    put_btn = WebDriverWait(web, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div[2]/div[1]/div/div[1]'))
    )
    put_btn.click()
    print("成功点击第一个前置按钮。")
    time.sleep(1)  # 短暂等待页面DOM更新

    # 点击第二个按钮，例如“查询”或“筛选”按钮
    search_btn = WebDriverWait(web, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[1]/div[2]'))
    )
    search_btn.click()
    print("成功点击第二个前置按钮。")
    time.sleep(1)  # 短暂等待查询条件区域显示

    # 输入查询范围的起始期号
    input1 = WebDriverWait(web, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[3]/div[1]/input[1]'))
    )
    input1.send_keys("24126")  # 设置起始期号
    print("成功输入起始期号: 24126。")
    time.sleep(1)

    # 输入查询范围的结束期号
    input2 = WebDriverWait(web, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[3]/div[1]/input[2]'))
    )
    input2.send_keys("25073")  # 设置结束期号
    print("成功输入结束期号: 25073。")
    time.sleep(1)

    # 点击查询按钮
    bigen_btn = WebDriverWait(web, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[3]/div[2]/div[2]/div'))
    )
    bigen_btn.click()
    print("成功点击查询按钮。")
    time.sleep(2)  # 给页面一些时间加载查询结果

except Exception as e:
    print(f"前置操作出错，脚本终止: {e}")
    web.quit()
    exit()  # 退出脚本

# --- CSV 文件写入准备 ---
# 获取 CSV 文件的列名（表头），顺序与 COLUMNS_TO_EXTRACT 定义的顺序一致
csv_headers = list(COLUMNS_TO_EXTRACT.keys())
print(f"\n准备将数据写入文件: {CSV_FILE_NAME}，表头为: {csv_headers}")

# 以写入模式打开 CSV 文件，'w' 模式会创建新文件或覆盖现有文件
# newline='' 参数是为了防止写入空行，encoding='utf-8' 支持中文
with open(CSV_FILE_NAME, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(csv_headers)  # 写入 CSV 表头


    # --- 数据提取及保存函数 ---
    def extract_and_save_table_data(driver_instance):
        """
        提取当前页面表格中指定列的数据，并写入到CSV文件。
        特别处理前区和后区号码，将多个 span 文本组合。
        """
        print("--- 正在提取当前页面数据 ---")
        try:
            # 等待表格行（tr）出现在DOM中
            tr_list = WebDriverWait(driver_instance, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "/html/body/div[2]/div[3]/div[3]/div/table/tbody/tr"))
            )
            if not tr_list:
                print("当前页面未找到任何表格行数据。")
                return

            for i, tr in enumerate(tr_list):
                row_data = []  # 用于存储当前行提取到的所有数据
                # 按照 COLUMNS_TO_EXTRACT 定义的顺序和类型提取数据
                for col_name, col_info in COLUMNS_TO_EXTRACT.items():
                    td_index = col_info['td_index']
                    data_type = col_info['type']

                    try:
                        # 构建 td 的相对 XPath，相对于当前的 tr
                        td_xpath = f"./td[{td_index}]"
                        td_element = tr.find_element(By.XPATH, td_xpath)

                        if data_type == 'text':
                            # 对于普通文本列，直接提取 td 的文本并去除首尾空白
                            row_data.append(td_element.text.strip())
                        elif data_type == 'red_balls':
                            # 提取红球号码：查找 td[3] 下面所有 class='jqh' 的 span
                            red_ball_spans = td_element.find_elements(By.XPATH, "./span[@class='jqh']")
                            # 提取每个 span 的文本，过滤空值，然后用空格连接
                            red_balls = [span.text.strip() for span in red_ball_spans if span.text.strip()]
                            row_data.append(" ".join(red_balls))  # 例如："01 04 17 33 34"
                        elif data_type == 'blue_balls':
                            # 提取蓝球号码：查找 td[4] 下面所有 class='jql' 的 span
                            blue_ball_spans = td_element.find_elements(By.XPATH, "./span[@class='jql']")
                            # 提取每个 span 的文本，过滤空值，然后用空格连接
                            blue_balls = [span.text.strip() for span in blue_ball_spans if span.text.strip()]
                            row_data.append(" ".join(blue_balls))  # 例如："03 09"
                        else:
                            # 未知类型的数据处理
                            row_data.append("N/A - 未知类型")

                    except Exception as e:
                        # 如果某列数据提取失败，打印错误并用 "N/A" 填充
                        print(f"  > 提取行 {i + 1} 的 '{col_name}' 列数据时出错: {e}")
                        row_data.append("N/A")

                writer.writerow(row_data)  # 将当前行提取到的数据写入 CSV 文件
                # print(f"已提取并保存行 {i+1}：{row_data}") # 调试时可以取消注释
        except Exception as e:
            print(f"加载表格数据时出错: {e}")


    # --- 主流程：抓取初始页（第一页）数据 ---
    extract_and_save_table_data(web)
    print(f"初始页（第一页）数据已保存到 {CSV_FILE_NAME}")

    # --- 循环点击分页按钮并抓取数据 ---
    for page_index in PAGE_BUTTON_INDICES:
        # 构造当前循环中要点击的页码按钮的 XPath
        current_page_button_xpath = f'/html/body/div[2]/div[3]/div[3]/div/div[1]/ul/li[{page_index}]/a'
        # 用于打印的按钮描述，方便追踪当前点击的是哪一页
        button_description = f"第 {page_index - 1} 页"  # 假设 li[2] 是页码1

        print(f"\n--- 尝试点击 {button_description} 按钮 ---")
        try:
            # 1. 等待分页按钮出现在 DOM 中 (不检查可见性，因为可能需要滚动)
            target_button = WebDriverWait(web, 10).until(
                EC.presence_of_element_located((By.XPATH, current_page_button_xpath))
            )

            # 2. 执行 JavaScript 滚动到该元素，确保其在浏览器视图内可见
            web.execute_script("arguments[0].scrollIntoView();", target_button)
            print(f"页面已滚动到 {button_description} 按钮位置。")

            time.sleep(1)  # 给页面短暂时间进行滚动和渲染动画

            # 3. 再次等待元素变为可点击状态并执行点击操作
            WebDriverWait(web, 10).until(
                EC.element_to_be_clickable((By.XPATH, current_page_button_xpath))
            ).click()
            print(f"成功点击 {button_description} 按钮！")

            time.sleep(2)  # 等待新页面加载数据。这里可替换为更精细的WebDriverWait条件，如等待表格第一行更新
            extract_and_save_table_data(web)  # 提取并保存新页面的数据
            print(f"{button_description} 数据已保存到 {CSV_FILE_NAME}")

        except Exception as e:
            # 如果点击分页按钮或抓取数据失败，打印错误并保存截图
            print(f"点击 {button_description} 按钮或抓取数据时出错: {e}")
            web.save_screenshot(f"error_page_{page_index}.png")  # 失败时保存截图
            break  # 如果点击失败，通常意味着无法继续分页，所以中断循环

# --- 脚本执行完毕 ---
print("\n所有指定页码的数据提取完毕。")
print(f"最终数据已全部保存到文件: {CSV_FILE_NAME}")
print("浏览器将保持打开状态，直到你在控制台按下回车键...")
input()  # 程序暂停，等待用户在控制台按下回车键
web.quit()  # 用户按下回车后，关闭浏览器
print("浏览器已关闭。")
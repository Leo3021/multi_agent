# import pandas as pd
# import re
# from collections import Counter
# import ast


# # 读取CSV文件
# file_path = 'matched_text_only.csv'  # 替换为您的文件路径
# df = pd.read_csv(file_path)

# # 查看总的项数（即总行数）
# total_items = len(df)

# print(f"CSV文件中一共有 {total_items} 项")



# # # 读取CSV文件
# # file_path = 'matched_text_only.csv'  # 替换为您生成的CSV文件路径
# # df = pd.read_csv(file_path)

# # # 定义一个函数来解析字符串形式的列表
# # def parse_list_string(s):
# #     try:
# #         parsed_list = ast.literal_eval(s)
# #         return [item.replace('\n', '') for item in parsed_list]  # 将字符串转换为列表
# #     except (ValueError, SyntaxError):
# #         return s  # 如果无法解析，则保持原样

# # # 将 matched_text 列中的字符串解析为实际的列表
# # df['matched_text'] = df['matched_text'].apply(parse_list_string)

# # # 将 matched_text 列中的所有列表展开为单个元素
# # all_items = df['matched_text'].explode()

# # # 统计每个项的出现次数
# # item_counts = Counter(all_items)

# # # 转换为 DataFrame 以便保存
# # item_counts_df = pd.DataFrame(item_counts.items(), columns=['Item', 'Count'])

# # # 查看统计结果
# # print(item_counts_df)

# # # 保存统计结果为 CSV 文件
# # item_counts_df.to_csv('item_counts.csv', index=False)

# # print("项及其出现次数已保存为 'item_counts.csv'")


import json

# 假设 filtered_results.json 的格式如下：
# {
#     "item1": {"Discharge Disposition": "Home"},
#     "item2": {"Discharge Disposition": "Hospital"},
#     "item3": {"Discharge Disposition": "Home"},
#     ...
# }

# # 读取 JSON 文件
# with open('filtered_results.json', 'r') as file:
#     filtered_results = json.load(file)

# # 使用集合来存储不重复的 Discharge Disposition 值
# discharge_dispositions = set()

# # 遍历 filtered_results 字典，提取每一项的 Discharge Disposition
# for item in filtered_results.values():
#     disposition = item["Discharge Disposition"]
#     if disposition:
#         discharge_dispositions.add(disposition)

# # 打印不重复的 Discharge Disposition 结果
# print(discharge_dispositions)

# # 如果需要将不重复的结果保存为列表：
# unique_dispositions_list = list(discharge_dispositions)
# print(unique_dispositions_list)

import json
from collections import Counter

# 读取 JSON 文件
with open('filtered_results.json', 'r') as file:
    filtered_results = json.load(file)

# 使用 Counter 来统计每个 Discharge Condition 出现的次数
discharge_conditions = []

# 遍历 filtered_results 字典，提取每一项的 Discharge Condition
for item in filtered_results.values():
    condition = item.get("Discharge Disposition")
    if condition:
        discharge_conditions.append(condition)

# 使用 Counter 计算每个 Discharge Condition 的频率
discharge_counter = Counter(discharge_conditions)

# 将结果按出现次数从高到低排序
sorted_discharge_counter = dict(discharge_counter.most_common())

# 将结果保存到一个 JSON 文件中
with open('discharge_disposition_distribution.json', 'w') as output_file:
    json.dump(sorted_discharge_counter, output_file, indent=4, ensure_ascii=False)

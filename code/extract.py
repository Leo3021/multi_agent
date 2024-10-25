import pandas as pd
import re
import json
import random

##########################
#将文件中的Discharge summary抽取出来
##########################
def extract_discharge_summary():
    # 读取CSV文件
    file_path = '/home/jbwang/dataset/dataset/mimic-III/NOTEEVENTS.csv'  # 替换为您的文件路径
    df = pd.read_csv(file_path)

    # 筛选出CATEGORY为"Discharge summary"的项
    filtered_df = df[df['CATEGORY'] == 'Discharge summary']

    # 将筛选后的数据保存为新的CSV文件
    filtered_df.to_csv('filtered_discharge_summary.csv', index=False)

    print("筛选完毕，结果已保存为 'filtered_discharge_summary.csv'")

##########################
#将文件中"\n+xxx+:"抽取出来
##########################
def extract():
    # 读取CSV文件
    file_path = 'filtered_discharge_summary.csv'  # 替换为您的文件路径
    df = pd.read_csv(file_path)

    # 定义一个正则表达式，匹配"\n"后跟一个或多个字符，并以":"结尾
    pattern = r'\n[a-zA-Z ]+:\n'  # 匹配换行符后跟随一个或多个字母或数字，并以冒号":"结尾

    # 使用 apply 函数在 TEXT 列中应用正则表达式，提取匹配的所有内容作为列表
    df['matched_text'] = df['TEXT'].apply(lambda x: re.findall(pattern, str(x)))

    # 将 matched_text 中空列表的行去除
    df_filtered = df[df['matched_text'].apply(lambda x: len(x) > 0)]

    # 只保留 matched_text 列
    matched_text_df = df_filtered[['matched_text']]

    # 如果需要保存筛选结果为CSV文件
    matched_text_df.to_csv('matched_text_only.csv', index=False)


    print("筛选结果已保存为 'matched_text_only.csv'")

##########################
#抽取包含所有关键词的病例，并结构化
##########################
def extract_dic():

    # 读取CSV文件
    file_path = 'filtered_discharge_summary.csv'  # 替换为您的文件路径
    df = pd.read_csv(file_path)

    # 关键词列表
    keywords = [
        'Allergies', 'Discharge Disposition', 'Major Surgical or Invasive Procedure',
        'Brief Hospital Course', 'Chief Complaint', 'Discharge Diagnosis',
        'Past Medical History', 'Discharge Condition', 'History of Present Illness',
        'Physical Exam', 'Social History', 'Pertinent Results', 'Discharge Instructions',
        'Medications on Admission', 'Followup Instructions', 'Family History',
        'Discharge Medications'
    ]

    # 构建正则表达式，匹配所有关键词
    keyword_pattern = r'\n(' + '|'.join(re.escape(keyword) for keyword in keywords) + r'):\n'

    # 用于匹配关键词到下一个标题之间的内容
    section_pattern = r'\n[a-zA-Z ]+:\n'

    # 存储结果的字典
    results = {}

    # 遍历 DataFrame
    for index, row in df.iterrows():
        text = row['TEXT']
        hadm_id = row['HADM_ID']
        
        # 检查文本中是否包含所有关键词
        if all(f'\n{keyword}:\n' in text for keyword in keywords):
            # 为当前 HADM_ID 创建一个字典
            results[hadm_id] = {}
            
            # 遍历每个关键词，提取相应内容
            for keyword in keywords:
                # 查找当前关键词
                match = re.search(rf'\n{re.escape(keyword)}:\n', text)
                if match:
                    start = match.end()  # 当前关键词后的位置
                    next_match = re.search(section_pattern, text[start:])  # 下一个关键词的位置
                    
                    # 计算结束位置
                    if next_match:
                        end = start + next_match.start()  # 到下一个标题前的内容
                    else:
                        end = len(text)  # 如果没有下一个关键词，提取到文本结尾
                    
                    # 提取关键词后的内容
                    content = text[start:end].strip()
                    content = re.sub(r'^Attending:.*$', '', content, flags=re.MULTILINE).strip()
                    # 删除类似于 [**xxx**]\n 的内容
                    content = re.sub(r'\[\*\*.*?\*\*\]\n?', '', content, flags=re.MULTILINE).strip()
                    content = re.sub(r'\(\)\s*Ambulatory\n|\(x\)\s*Wheelchair\n|\(\)\s*Stretcher\n|\(\)\s*N/A\n?', '', content, flags=re.MULTILINE).strip()
                    results[hadm_id][keyword] = content  # 存储关键词与其内容

    # 将结果保存为 JSON 文件
    with open('filtered_results.json', 'w') as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)

    print("结果已保存为 'filtered_results.json'")

def extract_key():
    # 读取 JSON 文件
    with open('filtered_results.json', 'r') as file:
        filtered_results = json.load(file)

    # 使用集合来存储不重复的 Discharge Disposition 值
    discharge_dispositions = set()

    # 遍历 filtered_results 字典，提取每一项的 Discharge Disposition
    for item in filtered_results.values():
        disposition = item["Discharge Disposition"]
        if disposition:
            discharge_dispositions.add(disposition)

    # 打印不重复的 Discharge Disposition 结果
    print(discharge_dispositions)

    # 如果需要将不重复的结果保存为列表：
    unique_dispositions_list = list(discharge_dispositions)
    print(unique_dispositions_list)


def extract_selected_keywords():
    # 读取原始的 filtered_results.json 文件
    input_file_path = 'filtered_results.json'  # 替换为您的文件路径
    output_file_path = 'filtered_selected_results.json'  # 输出文件路径

    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)

    # 只保留的关键词列表
    keywords_to_keep = [
        'Brief Hospital Course', 'Major Surgical or Invasive Procedure',
        'Discharge Diagnosis', 'Pertinent Results', 'Discharge Condition', 'Discharge Disposition'
    ]

    # 存储结果的字典
    filtered_results = {}

    # 遍历每个 HADM_ID 并提取感兴趣的字段
    for hadm_id, content in data.items():
        filtered_results[hadm_id] = {}
        for keyword in keywords_to_keep:
            if keyword in content:
                filtered_results[hadm_id][keyword] = content[keyword]

    # 将结果保存为新的 JSON 文件
    with open(output_file_path, 'w') as json_file:
        json.dump(filtered_results, json_file, ensure_ascii=False, indent=4)

    print(f"结果已保存为 '{output_file_path}'")

def sample_filtered_results():
    # 读取 filtered_selected_results.json 文件
    input_file_path = 'filtered_selected_results.json'  # 替换为您的文件路径
    output_file_path = 'filtered_selected_results_200.json'  # 输出文件路径

    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)

    # 随机抽取 200 项
    sampled_results = {k: data[k] for k in random.sample(list(data), min(200, len(data)))}

    # 将结果保存为新的 JSON 文件
    with open(output_file_path, 'w') as json_file:
        json.dump(sampled_results, json_file, ensure_ascii=False, indent=4)

    print(f"随机抽取的结果已保存为 '{output_file_path}'")

if __name__ == "__main__":
    sample_filtered_results()
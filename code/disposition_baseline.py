import json
from api import chatgpt_response
from tqdm import tqdm
import re
from collections import Counter

#正则抽取
def re_extract(pattern, input):
    result_match = re.search(pattern, input)
    if result_match:
        return result_match.group(1).strip()
    else:
        return ""

#简单智能体单次调用预测
def simple_process(input_file_path, output_file_path, prompt_path, keywords): 
    with open(prompt_path, "r") as file:
        prompt_template = json.load(file)

    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)
        

    final_predictions = {}
    # 遍历JSON数据中的所有HADM_ID
    for hadm_id, hadm_data in tqdm(data.items(), desc="Processing HADM_IDs"):
    # for hadm_id, hadm_data in data.items():
    # for hadm_id, hadm_data in list(data.items())[:1]:
        # 提取对应关键词的内容
        extracted_content = []
        for keyword in keywords:
            if keyword in hadm_data:
                extracted_content.append(f"{keyword}: {hadm_data[keyword]}")

        prompt = prompt_template["call_once_directly_prompt"].format(medical_data=extracted_content)

        # 生成GPT的响应
        gpt_output = chatgpt_response(prompt)

        # 将GPT输出存储到该条目中
        final_predictions[hadm_id] = gpt_output

        # print(prompt)
        # print(gpt_output)
    # 将修改后的数据写入输出文件
    with open(output_file_path, 'w') as json_file:
        json.dump(final_predictions, json_file, indent=4, ensure_ascii=False)

#单智能体预测
def single_agent_process(keyword, medical_data, prompt_path):
    with open(prompt_path, "r") as file:
        prompt_template = json.load(file)    

    prompt = prompt_template["single_agent_direct_prompt"].format(keyword=keyword, medical_data=medical_data)
    response = chatgpt_response(prompt)

    result_pattern = r'Result:\s*(.*)'
    explanation_pattern = r'Explanation:\s*(.*)'
    result = re_extract(result_pattern, response) or response
    explanation = re_extract(explanation_pattern, response)

    return result, explanation

#简单双智能体预测
def multi_agent_process(input_file_path, output_file_path, prompt_path, keywords): 
    with open(prompt_path, "r") as file:
        prompt_template = json.load(file)
    
    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)

    # 遍历JSON数据中的所有HADM_ID
    # for hadm_id, hadm_data in tqdm(data.items(), desc="Processing HADM_IDs"):
    for hadm_id, hadm_data in list(data.items())[:1]:       
        result1, explanation1 = single_agent_process(keywords[0], hadm_data[keywords[0]], prompt_path)
        result2, explanation2 = single_agent_process(keywords[2], hadm_data[keywords[2]], prompt_path)

        final_prompt = prompt_template["two_agents_direct_prompt"].format(keyword1=keywords[0], keyword2=keywords[2], result1=result1, explanation1=explanation1, result2=result2, explanation2=explanation2)
        gpt_output = chatgpt_response(final_prompt)
        # 将GPT输出存储到该条目中
        data[hadm_id]['Discharge_Disposition_Answer_bhc_diagnosis'] = gpt_output
        data[hadm_id]['Discharge_Disposition_Answer_bhc_diagnosis_prompt'] = final_prompt

    print(final_prompt)
    print(gpt_output)
    # # 将修改后的数据写入输出文件
    # with open(output_file_path, 'w') as json_file:
    #     json.dump(data, json_file, indent=4, ensure_ascii=False)

#智能体投票
def vote(input_file_path, output_file_path):
    with open(input_file_path, 'r') as file:
        data = json.load(file)

    # 遍历每个病人的记录，计算投票结果
    for patient_id, patient_data in tqdm(data.items(), desc="Processing HADM_IDs"):
        # 将五个答案字段收集到列表中
        answers = [
            patient_data.get("Discharge_Disposition_Answer_diagnosis"),
            patient_data.get("Discharge_Disposition_Answer_pr"),
            patient_data.get("Discharge_Disposition_Answer_msip"),
            patient_data.get("Discharge_Disposition_Answer_bhc"),
            patient_data.get("Discharge_Disposition_Answer_medications")
        ]
        
        # 统计每个答案的出现次数，选择出现次数最多的答案
        most_common_answer, _ = Counter(answers).most_common(1)[0]
        
        # 将结果存入字典的“Discharge_Disposition_Answer_vote”字段中
        patient_data["Discharge_Disposition_Answer_vote"] = most_common_answer

    with open(output_file_path, 'w') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

    print(f"数据已处理并保存到 {output_file_path}")    

#单结果正确性评估
def evaluate_results(output_file_path, standard_key, evaluated_key):
    # 读取生成的JSON文件
    with open(output_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    # 评估结果
    correct_count = 0
    total_count = 0
    
    print(standard_key)
    print(evaluated_key)

    for hadm_id, hadm_data in data.items():
        if standard_key in hadm_data and evaluated_key in hadm_data:
            discharge_disposition = hadm_data[standard_key]
            discharge_disposition_answer = hadm_data[evaluated_key]
            if discharge_disposition.lower() == discharge_disposition_answer.lower():
                correct_count += 1
            total_count += 1
    
    # 打印评估结果
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"评估结果：{evaluated_key}正确率为 {accuracy:.2f}% ({correct_count}/{total_count})")
    else:
        print("没有找到需要评估的数据。")

#抽取答错的结果
def evaluate_results_error(output_file_path, standard_key, evaluated_key, error_output_path):
    # 读取生成的JSON文件
    with open(output_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    # 评估结果
    correct_count = 0
    total_count = 0
    incorrect_entries = {}  # 用于存储答错的条目
    
    print(standard_key)
    print(evaluated_key)

    for hadm_id, hadm_data in data.items():
        if standard_key in hadm_data and evaluated_key in hadm_data:
            discharge_disposition = hadm_data[standard_key]
            discharge_disposition_answer = hadm_data[evaluated_key]
            if discharge_disposition.lower() == discharge_disposition_answer.lower():
                correct_count += 1
            else:
                # 如果答案错误，保存该条目，包括 hadm_id 和完整的 hadm_data
                incorrect_entries[hadm_id] = hadm_data
            total_count += 1
    
    # 打印评估结果
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"评估结果：{evaluated_key}正确率为 {accuracy:.2f}% ({correct_count}/{total_count})")
    else:
        print("没有找到需要评估的数据。")
    
    # 将答错的条目输出到一个JSON文件中
    if incorrect_entries:
        with open(error_output_path, 'w') as error_file:
            json.dump(incorrect_entries, error_file, indent=4, ensure_ascii=False)
        print(f"错误条目已保存到文件：{error_output_path}")
    else:
        print("所有条目都正确，没有错误条目。")

#将多智能体结果抽取为单智能体结果
def extract_single_result(input_file_path, output_file_path, standard_key, evaluated_key):
    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)

    result1_pattern = r"Doctor A's prediction:\s*(.*)"
    result2_pattern = r"Doctor B's prediction:\s*(.*)"
    
    output_data = {}
    for hadm_id, hadm_data in data.items():
        temp_data = {}
        result1 = re_extract(result1_pattern, hadm_data[evaluated_key])
        result2 = re_extract(result2_pattern, hadm_data[evaluated_key])
        temp_data["Discharge_Disposition_Answer_bhc"] = result1
        temp_data["Discharge_Disposition_Answer_diagnosis"] = result2
        temp_data[standard_key] = hadm_data[standard_key]
        temp_data["Discharge_Disposition_Answer_bhc_diagnosis"] = hadm_data["Discharge_Disposition_Answer_bhc_diagnosis"]
        temp_data[evaluated_key] = hadm_data[evaluated_key]
        output_data[hadm_id] = temp_data

    with open(output_file_path, 'w') as output_file:
        json.dump(output_data, output_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    
    input_file_path = '../data/multi_agents_data/filtered_results_moderate_length_80.json'  # 输入文件路径
    output_file_path = '../output/baseline_bhc_80.json'  # 输出文件路径
    prompt_path = '../config/discharge_disposition_prompt.json'
    error_output_path = '../data/sampled_results_200_error_five.json'
    multi_output_path = '../data/sampled_results_200_bhc_diagnosis.json'

    # keywords = ["Brief Hospital Course", "Discharge Diagnosis", "Social History", "Pertinent Results", "Discharge Medications"]
    keywords = [
        'Brief Hospital Course'
    ]

    simple_process(input_file_path, output_file_path, prompt_path, keywords)
    # single_agent_results(input_file_path, output_file_path, prompt_path, keywords)
    # multi_agent_process(input_file_path, output_file_path, prompt_path, keywords)
    # vote(input_file_path, output_file_path)

    # evaluate_results(output_file_path, 'Discharge Disposition', 'Discharge_Disposition_Answer_bhc_diagnosis')

    # evaluate_results_error(output_file_path, 'Discharge Disposition', 'Discharge_Disposition_Answer_five', error_output_path)
    
    # extract_single_result(output_file_path, multi_output_path, 'Discharge Disposition', 'Discharge_Disposition_Answer_bhc_diagnosis_prompt')
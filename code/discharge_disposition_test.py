import json
from api import chatgpt_response
from tqdm import tqdm
import re

##########################
#正则抽取
##########################
def re_extract(pattern, input):
    result_match = re.search(pattern, input)
    if result_match:
        return result_match.group(1).strip()
    else:
        return ""

##########################
#单智能体预测
##########################
def process_filtered_results(input_file_path, output_file_path): 
    user_prompt = '''You are an outstanding medical worker,please predict the patient's Discharge Disposition based on the following patient information.
Output requirements:Please choose from these four answers:Home With Service,Extended Care,Expired,Home
Note: Only the selected category needs to be output, no explanation is required
##################
patient information:'''  # 用户输入的prompt
    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    # keywords_to_extract = [
    #     'Brief Hospital Course', 'Major Surgical or Invasive Procedure',
    #     'Discharge Diagnosis', 'Pertinent Results', 'Discharge Medications'
    # ]
        
    keywords_to_extract = [
        'Discharge Medications'
    ]

    # 遍历JSON数据中的所有HADM_ID
    for hadm_id, hadm_data in tqdm(data.items(), desc="Processing HADM_IDs"):
    # for hadm_id, hadm_data in data.items():
    # for hadm_id, hadm_data in list(data.items())[:1]:
        # 提取对应关键词的内容
        extracted_content = []
        for keyword in keywords_to_extract:
            if keyword in hadm_data:
                extracted_content.append(f"{keyword}: {hadm_data[keyword]}")

        # 将用户的prompt和提取的内容拼接在一起
        combined_prompt = user_prompt + "\n\n" + "\n\n".join(extracted_content)

        # 生成GPT的响应
        gpt_output = chatgpt_response(combined_prompt)

        # 将GPT输出存储到该条目中
        data[hadm_id]['Discharge_Disposition_Answer_medications'] = gpt_output

    # 将修改后的数据写入输出文件
    with open(output_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

##########################
#简单多智能体预测
##########################
def multi_agent_process(input_file_path, output_file_path): 
    keywords = [
        'Brief Hospital Course', 'Major Surgical or Invasive Procedure',
        'Discharge Diagnosis', 'Pertinent Results', 'Discharge Medications'
    ]

    
    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)

    # 遍历JSON数据中的所有HADM_ID
    for hadm_id, hadm_data in tqdm(data.items(), desc="Processing HADM_IDs"):
    # for hadm_id, hadm_data in list(data.items())[:1]:
        prompt1 = f'''
You are an outstanding medical worker. Please predict the patient's Discharge Disposition based on the {keywords[0]}.
{keywords[0]}:
{hadm_data[keywords[0]]}

Output requirements: Please strictly follow this format:
Result: <Your answer from one of these four options: Home With Service, Extended Care, Expired, Home>
Explanation: <Brief explanation of why you made this choice>

Example output:
Result: Home With Service
Explanation: Based on the patient's condition, they require assistance at home to ensure proper recovery.
'''
        prompt2 = f'''
You are an outstanding medical worker. Please predict the patient's Discharge Disposition based on the {keywords[2]}.
{keywords[2]}:
{hadm_data[keywords[2]]}

Output requirements: Please strictly follow this format:
Result: <Your answer from one of these four options: Home With Service, Extended Care, Expired, Home>
Explanation: <Brief explanation of why you made this choice>

Example output:
Result: Home With Service
Explanation: Based on the patient's condition, they require assistance at home to ensure proper recovery.
'''

        # print(f"prompt1:{prompt1}")
        # print(f"prompt2:{prompt2}")
        result_pattern = r'Result:\s*(.*)'
        explanation_pattern = r'Explanation:\s*(.*)'
        # 生成GPT的响应
        preliminary_output1 = chatgpt_response(prompt1)
        result1 = re_extract(result_pattern, preliminary_output1) or preliminary_output1
        explanation1 = re_extract(explanation_pattern, preliminary_output1)

        preliminary_output2 = chatgpt_response(prompt2)
        result2 = re_extract(result_pattern, preliminary_output2) or preliminary_output2
        explanation2 = re_extract(explanation_pattern, preliminary_output2)

        final_prompt = f'''You are an outstanding medical worker.
Doctor A predicts the patient's discharge disposition based on {keywords[0]} and provides the following rationale:
Doctor A's prediction: {result1}
Reasoning: {explanation1}

Doctor B predicts the patient's discharge disposition based on {keywords[2]} and provides the following rationale:
Doctor B's prediction: {result2}
Reasoning: {explanation2}

Please analyze both predictions, considering their reasoning, and provide your final recommendation.

Output requirements:Please choose from these four answers:Home With Service,Extended Care,Expired,Home
Note: Only the selected category needs to be output, no explanation is required
'''

        gpt_output = chatgpt_response(final_prompt)
        # 将GPT输出存储到该条目中
        data[hadm_id]['Discharge_Disposition_Answer_bhc_diagnosis'] = gpt_output
        data[hadm_id]['Discharge_Disposition_Answer_bhc_diagnosis_prompt'] = final_prompt

    # print(final_prompt)
    # print(gpt_output)
    # 将修改后的数据写入输出文件
    with open(output_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

##########################
#单结果正确性评估
##########################
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

##########################
#抽取答错的结果
##########################
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

##########################
#将多智能体结果抽取为单智能体结果
##########################
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
    
    input_file_path = '../data/sampled_results_200.json'  # 输入文件路径
    output_file_path = '../data/sampled_results_200_with_Discharge_Disposition_Answer.json'  # 输出文件路径
    error_output_path = '../data/sampled_results_200_error_five.json'
    multi_output_path = '../data/sampled_results_200_bhc_diagnosis.json'

    

    # process_filtered_results(input_file_path, output_file_path)
    # multi_agent_process(input_file_path, output_file_path)

    # evaluate_results(multi_output_path, 'Discharge Disposition', 'Discharge_Disposition_Answer_diagnosis')

    # evaluate_results_error(output_file_path, 'Discharge Disposition', 'Discharge_Disposition_Answer_five', error_output_path)
    
    extract_single_result(output_file_path, multi_output_path, 'Discharge Disposition', 'Discharge_Disposition_Answer_bhc_diagnosis_prompt')
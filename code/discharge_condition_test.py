import json
from api import chatgpt_response
from tqdm import tqdm

def judge_result(gpt_answer, correct_answer):
    prompt = f'''You are an outstanding medical worker,Please evaluate the correctness of the automatically generated discharge conditions according to the standard discharge conditions.
automatically generated discharge condition : {gpt_answer}
standard discharge condition : {correct_answer}
##################
Output requirements: Please rate the correctness on a scale of 0-1. Only the score needs to be output, no explanation is required.
'''
    gpt_output = chatgpt_response(prompt)
    return gpt_output

def process_filtered_results(input_file_path, output_file_path, user_prompt):
    # 读取输入JSON文件
    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    keywords_to_extract = [
        'Brief Hospital Course', 'Major Surgical or Invasive Procedure',
        'Discharge Diagnosis', 'Pertinent Results'
    ]

    # 遍历JSON数据中的所有HADM_ID
    # for hadm_id, hadm_data in tqdm(data.items(), desc="Processing HADM_IDs"):
    # for hadm_id, hadm_data in data.items():
    for hadm_id, hadm_data in list(data.items())[:10]:
        # 提取对应关键词的内容
        extracted_content = []
        for keyword in keywords_to_extract:
            if keyword in hadm_data:
                extracted_content.append(f"{keyword}: {hadm_data[keyword]}")

        # 将用户的prompt和提取的内容拼接在一起
        combined_prompt = user_prompt + "\n\n" + "\n\n".join(extracted_content)

        # 生成GPT的响应
        gpt_output = chatgpt_response(combined_prompt)

        gpt_score = judge_result(gpt_output, hadm_data["Discharge Condition"])

        # 将GPT输出存储到该条目中
        data[hadm_id]['Discharge_Condition_Answer'] = gpt_output
        data[hadm_id]['Discharge_Disposition_Answer_score'] = gpt_score

    # 将修改后的数据写入输出文件
    with open(output_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

def evaluate_results(output_file_path):
    # 读取生成的JSON文件
    with open(output_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    # 评估结果
    score = 0
    total_count = 0

    for hadm_id, hadm_data in data.items():
        if 'Discharge Condition' in hadm_data and 'Discharge_Disposition_Answer_score' in hadm_data:
            score += float(hadm_data['Discharge_Disposition_Answer_score'])
            total_count += 1
    
    # 打印评估结果
    accuracy = (score / total_count) * 100
    print(f"评估结果：正确率为 {accuracy:.2f}% (评估条数{total_count})")

if __name__ == "__main__":
    
    input_file_path = 'filtered_selected_results_200.json'  # 输入文件路径
    output_file_path = 'filtered_selected_results_200_with_Discharge_Condition_Answer.json'  # 输出文件路径
    user_prompt = '''You are an outstanding medical worker,Please predict the patient's Discharge Condition based on the following patient information.
##################
patient information:'''  # 用户输入的prompt

    process_filtered_results(input_file_path, output_file_path, user_prompt)

    evaluate_results(output_file_path)

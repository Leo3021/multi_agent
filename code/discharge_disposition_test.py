import json
from api import chatgpt_response
from tqdm import tqdm

def process_filtered_results(input_file_path, output_file_path, user_prompt):
    # 读取输入JSON文件
    with open(input_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    keywords_to_extract = [
        'Brief Hospital Course', 'Major Surgical or Invasive Procedure',
        'Discharge Diagnosis', 'Pertinent Results'
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
        data[hadm_id]['Discharge_Disposition_Answer'] = gpt_output

    # 将修改后的数据写入输出文件
    with open(output_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

def evaluate_results(output_file_path):
    # 读取生成的JSON文件
    with open(output_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    # 评估结果
    correct_count = 0
    total_count = 0

    for hadm_id, hadm_data in data.items():
        if 'Discharge Disposition' in hadm_data and 'Discharge_Disposition_Answer' in hadm_data:
            discharge_disposition = hadm_data['Discharge Disposition']
            discharge_disposition_answer = hadm_data['Discharge_Disposition_Answer']
            if discharge_disposition.lower() == discharge_disposition_answer.lower():
                correct_count += 1
            total_count += 1
    
    # 打印评估结果
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"评估结果：正确率为 {accuracy:.2f}% ({correct_count}/{total_count})")
    else:
        print("没有找到需要评估的数据。")

if __name__ == "__main__":
    
    input_file_path = 'filtered_selected_results_200.json'  # 输入文件路径
    output_file_path = 'filtered_selected_results_200_with_Discharge_Disposition_Answer.json'  # 输出文件路径
    user_prompt = '''You are an outstanding medical worker,Please predict the patient's Discharge Disposition based on the following patient information.
Output requirements:Please choose from these four answers:Home With Service,Extended Care,Expired,Home
Note: Only the selected category needs to be output, no explanation is required
##################
patient information:'''  # 用户输入的prompt

    # process_filtered_results(input_file_path, output_file_path, user_prompt)

    evaluate_results(output_file_path)

import json
from api import chatgpt_response
from tqdm import tqdm
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random
from agent import Agent,Instructor

prompt_path = '../config/discharge_disposition_prompt.json'
agent_recruitment_path = '../config/agent_recruitment.json'
medical_data_path = '../data/multi_agents_data/filtered_results_moderate_length_80.json'
# output_file_path = '../output/f1d1_80.json' # 每轮并行发言,最大轮次3轮停止
# output_file_path = '../output/f2d1_80.json' # 每轮串行发言(发言顺序固定),最大轮次3轮停止
# output_file_path = '../output/f3d1_80.json' # 每轮串行发言(发言顺序随机),最大轮次3轮停止
output_file_path = '../output/f4d1_80.json' # instructor选择下轮发言人,每轮并行发言,最大轮次3轮停止

# 创建一个锁对象
lock = threading.Lock()

#正则抽取
def re_extract(pattern, input):
    result_match = re.search(pattern, input)
    if result_match:
        return result_match.group(1).strip()
    else:
        return ""
    
#智能体定义
def agent_define(agent_recruitment_path, threshold):
    with open(agent_recruitment_path, "r") as file:
        agent_recruitment = json.load(file)  

    agents = [key for key, value in agent_recruitment.items() if value > threshold]
    print(agents)
    return agents

#智能体投票
def vote(predictions, type):
    """
    对多个预测结果进行投票，返回频次最多的结果（如果出现频次超过2/3），否则返回 False
    :param predictions: 一个包含多个预测结果的列表，每个元素是一个字典（包含 "result" 和 "explanation"）。
    :param type: 如果type=1，返回超过2/3的选项；如果type=2，返回出现频次最高的选项
    :return: 如果出现频次最多的结果超过 2/3，则返回该结果的值；否则返回 False。
    """
    # 从结果中提取所有的 'result' 值
    result_values = [prediction["predict_result"] for prediction in predictions.values()]

    # 统计每个 result 出现的频次
    result_counter = Counter(result_values)

    # 找出出现频次最多的 result 和它的频次
    most_common_result, most_common_count = result_counter.most_common(1)[0]
    print(result_counter)
    print(f"投票结果：{most_common_result},{most_common_count},{most_common_count/len(predictions)}")

    if type == 1:
        # 判断频次是否超过 2/3
        if most_common_count / len(predictions) > 2 / 3:
            return most_common_result
        else:
            return False
    else:
        return most_common_result
#每轮串行发言（固定发言顺序）
def sequential_prediction_flow(medical_data, prompt_template, round):
    reference_medical_data = ["Brief Hospital Course", "Discharge Diagnosis", "Pertinent Results", "Discharge Medications", "Social History"]
    
    # 创建多个Agent实例并存储在列表中
    agents = []  # 用于存储多个Agent实例
    for i, item in enumerate(reference_medical_data):  # 创建Agent实例
        agent = Agent("assistant", f"Agent{i+1}", item, medical_data[item])
        agents.append(agent)

    def predict_with_agent(agent, prompt):
        """执行单个Agent的预测"""
        return agent.name, agent.chat(prompt)
    
    def run_predictions(prompt):
        """顺序执行所有Agent的预测"""
        predictions = {}
        for idx, agent in enumerate(agents):       
            # 执行当前 Agent 的预测
            agent_name, prediction = predict_with_agent(agent, prompt)
            predictions[agent_name] = prediction

            # 如果是第一个智能体，先添加指导者 Agent0 的信息
            if idx == 0:
                for agent_again in agents:
                    agent_again.add_history("instructor", "Agent0", "", prompt)

            # 在每个智能体执行预测之后，更新所有智能体的历史
            for agent_again in agents:
                agent_again.add_history(agent.role, agent.name, agent.reference_medical_data, prediction)

        return predictions

    # 开始预测
    for i in range(1, round + 1):
        print(f"第{i}轮")
        prompt_format = prompt_template["single_agent_with_history_prompt"]
        
        predictions = run_predictions(prompt_format)

        vote_result = vote(predictions, 1)
        if vote_result:
            return vote_result

    # 超过规定轮次，意见也不统一，返回出现频次最高的结果
    vote_result = vote(predictions, 2)
    return vote_result

#每轮串行发言（发言顺序随机）
def sequential_random_order_prediction_flow(medical_data, prompt_template, round):
    reference_medical_data = ["Brief Hospital Course", "Discharge Diagnosis", "Pertinent Results", "Discharge Medications", "Social History"]
    
    # 创建多个Agent实例并存储在列表中
    agents = []  # 用于存储多个Agent实例
    for i, item in enumerate(reference_medical_data):  # 创建Agent实例
        agent = Agent("assistant", f"Agent{i+1}", item, medical_data[item])
        agents.append(agent)

    def predict_with_agent(agent, prompt):
        """执行单个Agent的预测"""
        return agent.name, agent.chat(prompt)
    
    def run_predictions(prompt):
        """顺序执行所有Agent的预测"""
        # 每次调用前随机打乱 agents 列表，以实现随机的发言顺序
        random.shuffle(agents)
        
        predictions = {}
        for idx, agent in enumerate(agents):       
            # 执行当前 Agent 的预测
            agent_name, prediction = predict_with_agent(agent, prompt)
            predictions[agent_name] = prediction

            # 如果是第一个智能体，先添加指导者 Agent0 的信息
            if idx == 0:
                for agent_again in agents:
                    agent_again.add_history("instructor", "Agent0", "", prompt)

            # 在每个智能体执行预测之后，更新所有智能体的历史
            for agent_again in agents:
                agent_again.add_history(agent.role, agent.name, agent.reference_medical_data, prediction)

        return predictions

    # 开始预测
    for i in range(1, round + 1):
        print(f"第{i}轮")
        prompt_format = prompt_template["single_agent_with_history_prompt"]
        
        predictions = run_predictions(prompt_format)

        vote_result = vote(predictions, 1)
        if vote_result:
            return vote_result

    # 超过规定轮次，意见也不统一，返回出现频次最高的结果
    vote_result = vote(predictions, 2)
    return vote_result

#每轮并行发言
def parallel_prediction_flow(medical_data, prompt_template, round):
    # reference_medical_data = agent_define(agent_recruitment_path, 5)
    reference_medical_data = ["Brief Hospital Course", "Discharge Diagnosis", "Social History", "Pertinent Results", "Discharge Medications"]
    # 创建多个Agent实例并存储在列表中
    agents = []  # 用于存储多个Agent实例
    for i,item in enumerate(reference_medical_data):  # 创建Agent实例
        agent = Agent("assistant", f"Agent{i+1}", item, medical_data[item])
        agents.append(agent)

    def predict_with_agent(agent, prompt):
        """执行单个Agent的预测"""
        return agent.name, agent.chat(prompt)
    
    def run_predictions(prompt):
        """对所有Agent并行执行预测"""
        predictions = {}
        with ThreadPoolExecutor() as executor:
            # 提交任务到线程池
            future_to_agent = {executor.submit(predict_with_agent, agent, prompt): agent for agent in agents}
            
            # 收集结果
            for future in as_completed(future_to_agent):
                agent_name, prediction = future.result()
                predictions[agent_name] = prediction
        return predictions

    # 开始预测
    # 第一轮
    print("第1轮")
    prompt_format = prompt_template["single_agent_direct_prompt"]
    predictions = run_predictions(prompt_format)

    # 投票结果
    vote_result = vote(predictions, 1)
    if vote_result:
        return vote_result

    # 在这一轮所有Agent的回答完成后统一更新所有Agent的历史
    for agent in agents:
        agent.add_history("instructor", "Agent0", "", prompt_format)
        for agent_again in agents:
            agent.add_history(agent_again.role, agent_again.name, agent_again.reference_medical_data, predictions[agent_again.name])

    # 后续轮次
    for i in range(2, round + 1):
        print(f"第{i}轮")
        prompt_format = prompt_template["single_agent_with_history_prompt"]
        predictions = run_predictions(prompt_format)

        vote_result = vote(predictions, 1)
        if vote_result:
            return vote_result

        for agent in agents:
            agent.add_history("instructor", "Agent0", "", prompt_format)
            for agent_again in agents:
                agent.add_history(agent_again.role, agent_again.name, agent_again.reference_medical_data, predictions[agent_again.name])

    # 超过规定轮次，意见也不统一，返回出现频次最高的结果
    vote_result = vote(predictions, 2)
    return vote_result

#instructor选择下轮发言人，每轮并行发言
def instructed_parallel_prediction_flow(medical_data, prompt_template, round):
    reference_medical_data = ["Brief Hospital Course", "Discharge Diagnosis", "Social History", "Pertinent Results", "Discharge Medications"]
    # 创建多个Agent实例并存储在列表中
    agents = []  # 用于存储多个Agent实例
    for i, item in enumerate(reference_medical_data):  # 创建Agent实例
        agent = Agent("assistant", f"Agent{i+1}", item, medical_data[item])
        agents.append(agent)

    instructor = Instructor("instructor", "Instructor")

    def predict_with_agent(agent, prompt):
        """执行单个Agent的预测"""
        return agent.name, agent.chat(prompt)
    
    def run_predictions(prompt, selected_agents):
        """对所选Agent并行执行预测"""
        predictions = {}
        with ThreadPoolExecutor() as executor:
            # 提交任务到线程池
            future_to_agent = {executor.submit(predict_with_agent, agent, prompt): agent for agent in selected_agents}
            
            # 收集结果
            for future in as_completed(future_to_agent):
                agent_name, prediction = future.result()
                predictions[agent_name] = prediction
        return predictions

    # 第一轮所有Agent发言
    print("第1轮")
    prompt_format = prompt_template["single_agent_direct_prompt"]
    predictions = run_predictions(prompt_format, agents)

    # 投票结果
    vote_result = vote(predictions, 1)
    if vote_result:
        return vote_result

    # 在这一轮所有Agent的回答完成后统一更新所有Agent的历史
    instructor.add_history("instructor", "Instructor", "", prompt_format)
    for agent in agents:
        agent.add_history("instructor", "Instructor", "", prompt_format)
        instructor.add_history(agent.role, agent.name, agent.reference_medical_data, predictions[agent.name])
        for agent_again in agents:
            agent.add_history(agent_again.role, agent_again.name, agent_again.reference_medical_data, predictions[agent_again.name])
            
    # 后续轮次由Instructor指定发言
    for i in range(2, round + 1):
        print(f"第{i}轮")
        prompt_format = prompt_template["single_agent_with_history_prompt"]
        
        # 由Instructor选择下一个发言的Agent，可以选择多个Agent
        selected_agents = instructor.decide_next_agent(agents)
        if not selected_agents:
            break
        
    #     # 新的Prompt用于指定发言的Agent
    #     prompt_format = prompt_template["single_agent_with_history_prompt"]
        
    #     predictions = run_predictions(prompt_format, selected_agents)

    #     vote_result = vote(predictions, 1)
    #     if vote_result:
    #         return vote_result

    #     # 更新历史记录
    #     for agent in agents:
    #         agent.add_history("instructor", "Agent0", "", prompt_format)
    #         for selected_agent in selected_agents:
    #             agent.add_history(selected_agent.role, selected_agent.name, selected_agent.reference_medical_data, predictions[selected_agent.name])
    #     for selected_agent in selected_agents:
    #         instructor.add_history(selected_agent.role, selected_agent.name, selected_agent.reference_medical_data, predictions[selected_agent.name])

    # # 超过规定轮次，意见也不统一，返回出现频次最高的结果
    # vote_result = vote(predictions, 2)
    return vote_result

def generate_medical_predictions(medical_data_path, prompt_path, output_file_path):
    # agents = agent_define(agent_recruitment_path, 5)
    # agents = ["Brief Hospital Course", "Discharge Diagnosis", "Social History", "Pertinent Results", "Discharge Medications"]
    final_predictions = {}

    with open(medical_data_path, "r") as file:
        medical_data = json.load(file) 

    with open(prompt_path, "r") as file:
        prompt_template = json.load(file)

    # for hadm_id, hadm_data in tqdm(medical_data.items(), desc="Processing HADM_IDs"):
    for hadm_id, hadm_data in list(medical_data.items())[2:3]:
        print(f"患者：{hadm_id}")
        
        # prediction = sequential_prediction_flow(hadm_data, prompt_template, 3)
        # prediction = sequential_random_order_prediction_flow(hadm_data, prompt_template, 3)
        # prediction = parallel_prediction_flow(hadm_data, prompt_template, 3)
        prediction = instructed_parallel_prediction_flow(hadm_data, prompt_template, 3)

        final_predictions[hadm_id] = prediction
        print(f"最终结果{prediction}")

    # with open(output_file_path, 'w') as output_file:
    #     json.dump(final_predictions, output_file, ensure_ascii=False, indent=4)

def evaluate_results(standard_file_path, evaluated_file_path):
    # 读取生成的JSON文件
    with open(standard_file_path, 'r') as json_file:
        standard_data = json.load(json_file)
    with open(evaluated_file_path, 'r') as json_file:
        evaluated_data = json.load(json_file)
    
    # 评估结果
    correct_count = 0
    total_count = 0

    for hadm_id, hadm_data in standard_data.items():
        discharge_disposition = evaluated_data[hadm_id]
        discharge_disposition_answer = hadm_data["Discharge Disposition"]
        if discharge_disposition.lower() == discharge_disposition_answer.lower():
            correct_count += 1
        total_count += 1
    
    # 打印评估结果
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"评估结果：{evaluated_file_path}正确率为 {accuracy:.2f}% ({correct_count}/{total_count})")
    else:
        print("没有找到需要评估的数据。")

if __name__ == "__main__":
    generate_medical_predictions(medical_data_path, prompt_path, output_file_path)
    
    # evaluate_results(medical_data_path, output_file_path)

    # 评估结果：../output/baseline_all_80.json正确率为 71.25% (57/80)
    # 评估结果：../output/baseline_bhc_80.json正确率为 73.75% (59/80)
    # 评估结果：../output/f1d1_80.json正确率为 45.00% (36/80) f1d1
    # 评估结果：../output/f2d1_80.json正确率为 73.75% (59/80) f2d1 与baseline_bhc_80结果不同但正确率恰好一样
    # 评估结果：../output/f3d1_80.json正确率为 58.75% (47/80) f3d1




# Home, Count: 27
# Extended Care, Count: 27
# Home With Service, Count: 20
# Expired, Count: 6
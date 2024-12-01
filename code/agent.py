from api import chatgpt_response
import re

#正则抽取
def re_extract(pattern, input):
    result_match = re.search(pattern, input)
    if result_match:
        return result_match.group(1).strip()
    else:
        return ""
    
class Agent:
    def __init__(self, role, name, reference_medical_data, medical_data):
        self.role = role
        self.name = name
        self.reference_medical_data = reference_medical_data # bhc
        self.medical_data = medical_data # bhc content
        self.history = []

    def chat(self, message):
        # prompt = message.format(keyword=self.reference_medical_data, medical_data={self.reference_medical_data:self.medical_data}, history={"historical analysis":self.history})
        medical_dict = {self.reference_medical_data: self.medical_data}
        prompt = f"# Medical data:\n{medical_dict}\n\n\n # Historical analysis:\n{self.history}\n\n\n# Instruction:\n{message}"
        response = chatgpt_response(prompt)

        # 正则表达式提取结果和解释
        result_pattern = r'Result:\s*(.*)'
        explanation_pattern = r'Explanation:\s*(.*)'
        result = re_extract(result_pattern, response) or response
        explanation = re_extract(explanation_pattern, response)

        prediction = {"predict_result": result, "explanation": explanation}
        print("############")
        print(self.name)
        print(self.reference_medical_data)
        print(prompt)
        print(prediction)

        return prediction

    def add_history(self, role, name, reference_medical_data, message):
        self.history.append({"role":role, "name":name, "reference_medical_data":reference_medical_data, "message":message})

class Instructor(Agent):
    def __init__(self, role, name):
        super().__init__(role, name, None, None)
    
    def decide_next_agent(self, agents):
        # 使用API调用的形式来决定下一个或多个Agent，基于Instructor自身的history
        prompt = "You are an instructor overseeing multiple medical assistants. Based on their past interactions and provided data in the historical analysis, decide which agents should provide the next prediction. Here is the historical analysis of all agents:\n"
        prompt += f"{self.history}\n"
        prompt += "\nPlease decide which agents should speak next and provide their names.\nOutput requirements: Please strictly follow this format:\nAgentNames: [AgentX, AgentY, ...] (where X, Y, ... are the agent numbers)"
        
        response = chatgpt_response(prompt)

        selected_agent_names = re.findall(r'Agent(\d+)', response)
        selected_agents = [agent for agent in agents if agent.name in [f"Agent{num}" for num in selected_agent_names]]

        print("############")
        print(self.name)
        print(prompt)
        print(response)
        print("Selected agents:", [agent.name for agent in selected_agents])

        return selected_agents

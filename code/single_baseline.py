
import os
import random
from turtle import pd

from tqdm import tqdm

import metrics
from call_llm import *

# os.environ["HTTP_PROXY"] = "127.0.0.1:7890"
# os.environ["HTTPS_PROXY"] = "127.0.0.1:7890"

# agent入口
 # 假设我们有一个新的评估提示生成函数
from debate_prompt import gen_debate_prompt
from tools import call_llm

"""
todo:
1. environment
2. tools definition
3. prompt template
4. model init
"""


class Agent:
    def __init__(self, system_message):
        self.chat_history = [{"role": "system", "content": system_message}]
        self.agent_progress = []
        self.max_request_time = 5


def single_model_evaluate(query, task, model_name="", model_type=""):
    # 初始化模型
    if model_name == 'gpt':
        model = GPT()
    elif model_name == 'Deepseek':
        model = DeepSeek(model_type)
    else:
        # 默认使用GPT
        # model = GPT()
        # model=DeepSeek("deepseek-chat")
        model=DeepSeek("deepseek-reasoner")
    # 创建评估代理
    eval_agent = Agent(
        system_message="你是一名翻译专家，现在需要根据标注规则对一些句对翻译进行打分，你的目标是尽力与人类对齐，所以需要多多关注评分规则的细节。"
    )

    # 生成评估提示
    eval_prompt = gen_debate_prompt(query, 'positive', task)

    # 添加到聊天历史
    eval_agent.chat_history.append({"role": "user", "content": eval_prompt})

    # 调用模型获取响应
    response = call_llm(model_name, model, eval_agent.chat_history, use_alternative=False)
    response_json = parse_llm_response(model_name, response)

    # 重试机制
    current_request_time = 0
    while response_json == '' and current_request_time < eval_agent.max_request_time:
        print("重新调用llm...")
        response = call_llm(model_name, model, eval_agent.chat_history, use_alternative=False)
        response_json = parse_llm_response(model_name, response)
        current_request_time += 1

    # 处理响应
    if response_json:
        try:
            # 假设响应是JSON格式，包含评分信息
            result = json.loads(response_json)
            return result, [f"评估结果: {response_json}"]
        except json.JSONDecodeError:
            # 如果响应不是JSON格式，尝试提取评分信息
            # 这里需要根据实际响应格式进行调整
            return {"sp": 0, "g_1": 0, "g_2": 0, "reason": "无法解析模型响应"}, [f"原始响应: {response_json}"]
    else:
        return {"sp": 0, "g_1": 0, "g_2": 0, "reason": "模型无响应"}, ["模型无响应"]


if __name__ == "__main__":
    # input:
    # {
    #     "model": "deepseek-chat",
    #     "instruction": "请将源语言文本翻译成目标语言文本,其中\"挡枪\"是习语,习语是经过人群长期沿用，结构基本定型的短语或句子。 源语言:中文 目标语言:英文。 文本:大宝从小宝那里得知有个叫苏西的阿姨，现在正好拿出来挡枪，而且学着小宝说话，丝毫看不出破绽。",
    #     "model_output": "Answer: Dabao learned from Xiaobao that there was an aunt named Susie, and now he just used her as a scapegoat, even mimicking Xiaobao's way of speaking without showing any flaw.",
    #     "ground_truth": "Issac learned from Paul that there was an aunt named Susie, and now he just took her out to hide the secret, and he learned to talk with Paul's voice, by which she didn't see any flaw."
    # }

    data_file_path = ""  # 输入数据位置
    output_dir = "./run"  # 输出的文件所在的文件夹
    file_path = ""  # 输出位置

    with open(data_file_path, 'r', encoding='utf-8') as f:
        data_list = json.load(f)

    # 测试
    print(len(data_list))
    data_list = data_list[:]  # 限制处理的数据量

    # 检查现有输出文件
    if os.path.exists(file_path):
        if os.path.getsize(file_path) > 0:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_list = json.load(f)
            except json.JSONDecodeError:
                print(f"错误：文件 {file_path} 不是有效的JSON格式")
                json_list = []  # 当作空列表处理
        else:
            print(f"警告：文件 {file_path} 为空")
            json_list = []
    else:
        print(f"警告：文件 {file_path} 不存在")
        json_list = []

    # 处理尚未处理的数据
    data_list = data_list[len(json_list):]
    print(f"待处理数据量: {len(data_list)}")

    for data in tqdm(data_list, desc=f"打分进度"):
        print(data)
        query = {
            "任务": data['instruction'],
            "源文本": data['instruction'].split("文本:")[1] if "文本:" in data['instruction'] else
            data['instruction'].split("句子:")[1],
            "目标文本": data['model_output']
        }
        print(query)

        # 使用单模型进行评估
        response, progress = single_model_evaluate(
            query=query,
            task=metrics.task_list[data['task']],
            model_name=data.get('model', 'gpt')  # 使用数据中指定的模型，默认为gpt
        )

        new_item = {
            "line":"base",
            "judge-model":"ds-v3",
            "task_type": data['task'],
            "model": data['model'],
            "task": data['instruction'],
            "origin": data['instruction'].split("文本:")[1] if "文本:" in data['instruction'] else
            data['instruction'].split("句子:")[1],
            "target": data['model_output'],
            "specific": response.get('sp', 0),
            "general_1": response.get('g_1', 0),
            "general_2": response.get('g_2', 0),
            "reason": response.get('reason', ''),
            "process": progress
        }

        json_list.append(new_item)
        print(new_item)

        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 实时保存结果
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_list, f, indent=2, ensure_ascii=False)



import argparse
import json
import os
import random
from turtle import pd

from tqdm import tqdm

import metrics
from call_llm import *

# os.environ["HTTP_PROXY"] = "127.0.0.1:7890"
# os.environ["HTTPS_PROXY"] = "127.0.0.1:7890"

# agent入口
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


def debate_execute(query,task,model_name="", max_round=4, model_type=""):
    # if model_name == 'gpt':
    #     model = GPT()
    # elif model_name == 'Deepseek':
    #     model = DeepSeek(model_type)

    # pos_model=DeepSeek("deepseek-chat")
    # neg_model=DeepSeek("deepseek-chat")
    # judge_model = DeepSeek("deepseek-chat")

    pos_model=DeepSeek("deepseek-reasoner")
    neg_model=DeepSeek("deepseek-reasoner")
    judge_model = DeepSeek("deepseek-reasoner")

    # pos_model = GPT()
    # neg_model = GPT()
    # judge_model = GPT()

    # judge_model=DeepSeek("deepseek-reasoner")
    current_request_time = 0
    # cn-translator
    pos_agent = Agent(
        system_message="你是一名翻译专家，现在需要根据标注规则对一些句对翻译进行打分，你的目标是尽力与人类对齐，所以需要多多关注评分规则的细节。请注意：打分不必过分严格，不需要过于强调文化底蕴等层面的要求，必要时可以坚持自己的想法，但请不要为了反驳而反驳。")
    # en-translator
    neg_agent = Agent(
        system_message="你是一名翻译专家，现在需要根据标注规则对一些句对翻译进行打分，你的目标是尽力与人类对齐，所以需要多多关注评分规则的细节。请注意：打分不必过分严格，不需要过于强调文化底蕴等层面的要求，必要时可以坚持自己的想法，但请不要为了反驳而反驳。")
    judge_agent = Agent(system_message="你是一名极具理性的翻译专家，在多专家会诊中担任裁判。")
    round = 0
    debate_progress = []

    while round < max_round:
        round += 1
        print("Round", round)
        pos_prompt = gen_debate_prompt(query, 'positive', task)
        neg_prompt = gen_debate_prompt(query, 'negative', task)
        judge_prompt = gen_debate_prompt(query, 'judge', task)
        # pos_prompt = "你好"
        # neg_prompt = "你好"
        # judge_prompt = "你好"
        if round == 1:
            pos_agent.chat_history.append({"role": "user", "content": pos_prompt})
            neg_agent.chat_history.append({"role": "user", "content": neg_prompt})
            judge_agent.chat_history.append({"role": "user", "content": judge_prompt})

        # pos agent发言
        response = call_llm(model_name, pos_model, pos_agent.chat_history, use_alternative=False)
        response_json = parse_llm_response(model_name, response)
        while response_json == '':
            print("重新调用llm...")
            response = call_llm(model_name, pos_model, pos_agent.chat_history, use_alternative=False)
            print("pos:" + response)
            response_json = parse_llm_response(model_name, response)

        # TODO:修改回来
        pos_response = response_json
        # pos_response = str(response_json.get("response"))
        print("专家1：", pos_response)
        pos_agent.chat_history.append({"role": "assistant", "content": pos_response})
        neg_agent.chat_history.append({"role": "user", "content": ("正方：" + pos_response)})
        judge_agent.chat_history.append({"role": "user", "content": ("正方：" + pos_response)})
        debate_progress.append("专家1：" + pos_response)

        # 反方发言
        response = call_llm(model_name, neg_model, neg_agent.chat_history, use_alternative=False)
        response_json = parse_llm_response(model_name, response)
        while response_json == '':
            print("重新调用llm...")
            response = call_llm(model_name, neg_model, neg_agent.chat_history, use_alternative=False)
            response_json = parse_llm_response(model_name, response)

        # TODO:修改回来
        neg_response = response_json
        # neg_response = str(response_json.get("response"))
        print("专家2：", neg_response)
        neg_agent.chat_history.append({"role": "assistant", "content": neg_response})
        pos_agent.chat_history.append({"role": "user", "content": ("反方：" + neg_response)})
        judge_agent.chat_history.append({"role": "user", "content": ("反方：" + neg_response)})
        debate_progress.append("专家2：" + neg_response)
        # 裁判发言
        response = call_llm(model_name, judge_model, judge_agent.chat_history, use_alternative=False)
        response_json = parse_llm_response(model_name, response)
        while response_json == '':
            print("重新调用llm...")
            response = call_llm(model_name, judge_model, judge_agent.chat_history, use_alternative=False)
            response_json = parse_llm_response(model_name, response)
        print("裁判：")
        print(response_json)
        response_json = json.loads(response_json)
        print(response_json)
        judge = response_json["judge"]
        judge_reasons = response_json['judge_reasons']
        judge_agent.chat_history.append({"role": "assistant", "content": judge_reasons})
        debate_progress.append("裁判：" + response)
        if judge == 'yes':
            print(response_json)
            return response_json, debate_progress
            break
        else:
            # print("裁判认为辩论尚未结束：\n", judge_reasons)
            if round==max_round:
                judge_agent.chat_history.append({"role": "user", "content": "当前是最后一轮，请结束辩论并做出诊断。"})
                response = call_llm(model_name, judge_model, judge_agent.chat_history, use_alternative=False)
                response_json = parse_llm_response(model_name, response)
                while response_json == '':
                    print("重新调用llm...")
                    response = call_llm(model_name, judge_model, judge_agent.chat_history, use_alternative=False)
                    response_json = parse_llm_response(model_name, response)
                print("最终裁判：")
                print(response_json)
                response_json = json.loads(response_json)
                print(response_json)
                judge = response_json["judge"]
                judge_reasons = response_json['judge_reasons']
                judge_agent.chat_history.append({"role": "assistant", "content": judge_reasons})
                debate_progress.append("最终裁判：" + response)
                return response_json, debate_progress
            print("裁判认为尚未达成共识：\n")
    return "", []


if __name__ == "__main__":
    # input:
    # {
    #     "model": "deepseek-chat",
    #     "instruction": "请将源语言文本翻译成目标语言文本,其中\"挡枪\"是习语,习语是经过人群长期沿用，结构基本定型的短语或句子。 源语言:中文 目标语言:英文。 文本:大宝从小宝那里得知有个叫苏西的阿姨，现在正好拿出来挡枪，而且学着小宝说话，丝毫看不出破绽。",
    #     "model_output": "Answer: Dabao learned from Xiaobao that there was an aunt named Susie, and now he just used her as a scapegoat, even mimicking Xiaobao's way of speaking without showing any flaw.",
    #     "ground_truth": "Issac learned from Paul that there was an aunt named Susie, and now he just took her out to hide the secret, and he learned to talk with Paul's voice, by which she didn't see any flaw."
    # }
    parser = argparse.ArgumentParser(description='运行翻译处理脚本')
    parser.add_argument('--f', type=str,
                        help='输入文件路径（相对于基础目录）',
                        default='translation_Seed-PPO')
    args = parser.parse_args()
    file_path = f"{args.f}"  # input:llama3_70b



    data_file_path= f"./data_process/origin_data/data/{file_path}_300.json"  #输入数据位置
    output_dir="./run" #输出的文件所在的文件夹
    file_path = f"./data_process/origin_data/output/{file_path}_300.json" #输出位置
    with open(data_file_path,'r',encoding='utf-8') as f:
        data_list=json.load(f)
    #测试
    print(len(data_list))
    data_list=data_list
    if os.path.exists(file_path):
        # 检查文件大小
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
    data_list=data_list[len(json_list):]
    print(len(data_list))
    for data in tqdm(data_list, desc=f"打分进度"):
        print(data)
        m=""
        if "文本:" in data['instruction']:
            m=data['instruction'].split("文本:")[1]
        elif  "文本：" in data['instruction']:
            m=data['instruction'].split("文本：")[1]
        elif "句子:" in data['instruction']:
            m=data['instruction'].split("句子:")[1]
        elif "句子：" in data['instruction']:
            m = data['instruction'].split("句子：")[1]
        else:
            m=data['instruction']

        query = {
            "任务": data['instruction'],
            "源文本":  m,
            "目标文本": data['model_output']
        }
        # print(query)
        print(f"query:{query}")
        max_round = 4
        response, progress = debate_execute(query=query, max_round=max_round, task=metrics.task_list[data['task']])
        new_item = {
            "task_type":data['task'],
            "model":data['model'],
            "task": data['instruction'],
            "origin": m,
            "target": data['model_output'],
            "specific":response['sp'],
            "general_1":response['g_1'],
            "general_2":response['g_2'],
            "process":progress
        }
        json_list.append(new_item)
        print(f'new_item:{new_item}')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(file_path, 'w',encoding='utf-8') as f:
            json.dump(json_list, f, indent=2, ensure_ascii=False)

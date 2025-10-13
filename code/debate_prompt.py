
import metrics
from metrics import *
class DebatePrompt:
    def __init__(self, type):
        self.type = type

    def constraint(self):
        if self.type in ['positive', 'negative']:
            constraint = [
                "你可以坚持你的观点而不被轻易说服，但是请考虑对方的文化背景，并慎重决定是否修改评判。请不要为了反驳而反驳。",
            ]
        elif self.type == 'judge':
            constraint = [
                "请做好裁判的本职，并仅通过双方的发言做出决断。",
            ]
        return constraint


    def prompt_template(self):
        if self.type == 'positive':
            prompt_template = '''
            您是一名翻译专家。\n翻译任务：\n{query}\n限制条件说明：\n{constraints}\n请根据以下要求生成JSON字符串，直接输出结果，不需要任何额外的说明或文字，响应格式如下：\n{response_format_prompt}"
            '''
            # prompt_template = '''
            # '''
        elif self.type == 'negative':
            prompt_template = '''
            您是一名翻译专家。\n翻译任务：\n{query}\n限制条件说明：\n{constraints}\n请根据以下要求生成JSON字符串，直接输出结果，不需要任何额外的说明或文字，响应格式如下：\n{response_format_prompt}"
            '''
            # prompt_template = '''
            #             '''
        elif self.type == 'judge':
            prompt_template = "您是首席评审。您的任务不是提出新观点，而是分析正反方专家的论据质量，请决策每一轮探讨是否结束并做出最终的诊断。\n翻译任务：\n{query}\n限制条件说明：\n{constraints}\n请根据以下要求生成JSON字符串，直接输出结果，不需要任何额外的说明或文字，响应格式如下：\n{response_format_prompt}"
        return prompt_template

    def response_format(self):
        if self.type == 'positive':
            response_format_prompt = '{"sp": "该翻译在对应任务上的特异性指标得分","g_1":"该英文翻译在对应任务下的第一个通用指标上的得分","g_2":"该英文翻译在对应任务下的第二个通用指标上的得分","thoughts":"为什么给这三个分数"}'
        elif self.type == 'negative':
            response_format_prompt = '{"sp": "该翻译在对应任务上的特异性指标得分","g_1":"该英文翻译在对应任务下的第一个通用指标上的得分","g_2":"该英文翻译在对应任务下的第二个通用指标上的得分","thoughts":"为什么给这三个分数"}'
        elif self.type == 'judge':
            response_format_prompt = '{"judge": "你认为两个专家在打分上是否达成共识，仅回答yes或no。当双方在打分上存在分歧时应当说no！","judge_reasons": "你认为共识已达成或尚未达成的原因。","sp": "根据双方观点，该翻译在对应任务上的特异性指标得分","g_1":"根据双方观点，该英文翻译在对应任务下的第一个通用指标上的得分","g_2":"根据双方观点，该英文翻译在对应任务下的第二个通用指标上的得分"}}'
        return response_format_prompt

def gen_debate_prompt(query, type,task):
    prompt = DebatePrompt(type)
    # todo: query, agent_scratch, actions
    constraint_prompt = '\n'.join([f"{idx + 1}. {con}" for idx, con in enumerate(prompt.constraint())])
    # resources_prompt = '\n'.join([f"{idx + 1}. {con}" for idx, con in enumerate(prompt.resources())])
    # best_practices_prompt = '\n'.join([f"{idx + 1}. {con}" for idx, con in enumerate(prompt.best_practices())])
    prompt_str = prompt.prompt_template().format(
        query=query,
        constraints=constraint_prompt,
        # resources=resources_prompt,
        # best_practices=best_practices_prompt,
        response_format_prompt=prompt.response_format()
    )
    # print(task)
    prompt_str+=f'''
    \n以下是你必须注意的点：{metrics.Note_Prompt}\n
    \n以下是打分规则，其中的打分案例是您需要参考的：{task}
    \n 请直接在每个维度上给出评分和原因即可，无需逐步推理
    '''
    print(prompt_str)
    return prompt_str
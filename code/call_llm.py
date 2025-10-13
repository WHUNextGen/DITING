
import json

import httpx
from openai import OpenAI

from api_key import *

class GPT:
    def __init__(self):
        api_key =get_openai_key()
        base_url = ""
        # 创建 httpx.Client 实例
        http_client = httpx.Client(
            base_url=base_url,
            follow_redirects=True
        )

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=http_client  # 使用上面创建的 httpx.Client 实例
        )

    def generate(self, messages):
        # temperature = 0.0
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"}
            # temperature=temperature
        )
        # print('temperature:', temperature)
        answer = completion.choices[0].message.content
        if answer == 'broken':
            self.generate(messages)
        return answer


class DeepSeek:
    def __init__(self,model):
        self.model=model
        api_key = get_deepseek_key()  #替换为我的key
        base_url = "https://api.deepseek.com"
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=httpx.Client(
                base_url=base_url,
                follow_redirects=True
            )
        )

    def generate(self, messages):
        if self.model=='deepseek-reasoner':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            reasoning_content = ""
            content = ""
            answer_started = False
            for chunk in response:
                if chunk.choices[0].delta.reasoning_content:
                    reasoning_content += chunk.choices[0].delta.reasoning_content
                    print(chunk.choices[0].delta.reasoning_content, end='', flush=True)
                elif chunk.choices[0].delta.content:
                    if not answer_started:
                        print("\n\n—————————————【最终答案】———————————————————————————\n", end='')
                        answer_started = True
                    content += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end='', flush=True)
            print('\n')

            return content
        else:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                response_format={"type": "json_object"}
            )
            answer = completion.choices[0].message.content
            if answer == 'broken':
                self.generate(messages)
            return answer

def parse_llm_response(model_name, response):
    # response = response.lstrip("```json\n").rstrip("\n```")
    # # 如果仍存在"```json\n"，截取该字符串之后的内容
    # if "```json\n" in response:
    #     response = response[response.index("```json\n"):].lstrip("```json\n")
    # if len(response) > 3:
    #     if '}}}' in response[-3:]:
    #         response = response[:-1]
    #     if response[-2] == ',':
    #         response = response[:-3] + response[-1]
    # else:
    #     print('无法解析大模型输出，大模型输出为：', response)
    #     return ''
    try:
        # response = json.loads(response)
        return response
    except:
        print('无法解析大模型输出，大模型输出为：', response)
        return ''









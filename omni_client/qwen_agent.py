import os, sys
import time
from openai import OpenAI


class QwenAgent:
    #def __init__(self, model_name="qwen-vl-max-latest"):
    def __init__(self, model_name="qwen2.5-vl-72b-instruct"):
        #self.api_key = api_key
        self.model = model_name
        self.client = OpenAI(
            api_key = "sk-c7beef405c4d4b34a402eec77af66e25",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"

        )
        
    def inference(self, messages):
        completion = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
        )
        assistant_message = completion.choices[0].message.model_dump()

        print(assistant_message)
        return assistant_message

if __name__ == '__main__':
    api_key = ""
    qwen_agent = QwenAgent(api_key)
    response = qwen_agent.inference("")
    print(response)
    

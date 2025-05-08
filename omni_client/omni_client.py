import socket
import requests
import os, time, io
import subprocess
from subprocess import PIPE
import random 
import base64
import json
import pickle

from typing import Union
from pydantic import BaseModel
from PIL import Image

from prompt import SYSTEM_PROMPT 
from qwen_agent import QwenAgent
#from typings import *
from typings.output import *

SampleIndex = Union[int, str]

#class OmniServerResponse(BaseModel):
#    status: SampleStatus = SampleStatus.RUNNING
#    result: JSONSerializable = None
#    #text_prompt : str
#    #image_url : str


class OmniStartSampleRequest(BaseModel):
    task : str
    scene : str
    inner_port : int

class QwenAgentOutput(BaseModel):
    status: AgentOutputStatus = AgentOutputStatus.NORMAL
    content: str = None


class OmniInteractRequest(BaseModel):
    inner_port : int
    agent_response : QwenAgentOutput


class OmnigibsonClient():
    
    def __init__(self, ip, url, port, inner_port, max_round, index, time_s, agent, test, cwd="/VAB-OmniGibson-code" ):
        self.ip = ip
        self.url = url
        self.port = port
        self.inner_port = inner_port
        tasks = self._get_tasks()
        task_ = tasks[index]
        self.task, self.scene = task_[0], task_[1]
        self.current_image = None
        self.step_num = -1
        self.agent = agent
        self.test = test
        self.image_path = "./data/" + str(time_s) + "/"
        if not os.path.exists(self.image_path):
            os.makedirs(self.image_path)
        self.messages = [
            {
                "role": "system",
                "content" : [{"type":"text","text":SYSTEM_PROMPT}]
            },
        ]

        print("task: ", self.task)
        print("scene: ", self.scene)
        print("inner_port: ", self.inner_port)

    def _get_tasks(self,):
        with open(f"tasks.txt", "r") as f:
            tasks = eval(f.read())
        return tasks
 
    def _get_test(self, ):
        if self.test:
            with open("./tmp/first_message", 'rb' ) as f:
                self.messages = pickle.load(f)
                self.current_image = self.messages[1]["content"][0]["image_url"]["url"].split("data:image/png;base64,")[-1]

    def render(self, save_image=True):
        '''返回当前图片/视频 '''
        if self.step_num == -1:
            print("render nothing .. ")
        else:
            img = Image.open(io.BytesIO(base64.decodebytes(bytes(self.current_image, "utf-8"))))
            if save_image:
                img.save(self.image_path + str(self.step_num)+".png")
            #img.show()

    def reset(self, ):
        '''初始化环境，包括任务名称等设置，返回初始化信息（如果有） '''
        try:
            result = requests.post(url + '/start_sample',
                    json=OmniStartSampleRequest(task=self.task,scene=self.scene,inner_port=self.inner_port).dict())
        except Exception as e:
            print("error happend ..")
            print(e)
            return 
        print("result")
        #print(result)
        print(result.status_code)
        if result.status_code == 406:
            print("error happend 406..")
            return 
        if result.status_code != 200:
            print("error happend not 200 ..")
            return
        result = result.json()
        #print(result)
        result = result['result']
        text_prompt, base64_image = result["text_prompt"], result["image_url"]
        self.current_image = base64_image
        self.messages.append(
            {
                "role" : "user",
                "content" : [
                    {
                        "type": "image_url",
                        "image_url" : {"url":f"data:image/png;base64,{base64_image}"}
                    },
                    {
                        "type": "text",
                        "text": text_prompt
                    }
                ]
            }
        )
        self.last_text_prompt = text_prompt
        if self.test:
            with open("./tmp/first_message", "wb") as f:
                pickle.dump(self.messages, f)
        print(text_prompt)
        print("base64_image too large")
        self.step_num = 0
    
    '''get the response from agent, then input it into '''
    ''' omnigison, get the result/feedback from env'''
    def _step_once_time(self, First=False):
        try:
            print("content .. ")
            content = self.agent.inference(self.messages)
            response = QwenAgentOutput(content=content["content"])
            print("response .. ")
            print(response)
        except Exception as e:
            print("Exception happened from agent: ", e)
            return None, None
        try:
            result = requests.post(self.url + '/interact',
                    json=OmniInteractRequest(
                        inner_port=self.inner_port,
                        agent_response=response,).dict())
        except Exception as e:
            print("Exception happened in post interact, ", e)
            return None, None
        if result.status_code != 200:
            print("result status code is not 200, return")
            return None, None

        result = result.json()
        #print("result")
        #print(result)
        self.current_image = result["result"]["image_url"]
        self.step_num += 1
        return result, content

    def step_full(self,):
        First = True
        if len(self.messages) < 2: return 
        last_text_prompt = self.last_text_prompt

        while True:
            result, content = self._step_once_time( First=First)
            First = False
            if result == None :
                print("result is None, Task failed")
                return 
            if result['status'] != SampleStatus.RUNNING: 
                print("result status is ", result['status'])
                if result['status'] == SampleStatus.SUCCESS:
                    print("Task execute successfully ~")
                else:
                    print("Task Failed ~")
                return
            result = result['result']
            # 下面两行是根据vab里面的程序来的，将历史内容附加到messages里，但去掉历史的image信息
            self.messages[-1]["content"] = content["content"]
            self.messages[-2]["content"] =[{'type':'text','text': last_text_prompt + 'Omiteed.\n'}]
            text_prompt, base64_image = result['text_prompt'], result['image_url']
            self.messages.append(
                {
                    "role" : "user",
                    "content" : [
                        {
                            "type": "image_url",
                            "image_url" : {"url":f"data:image/png;base64,{base64_image}"}
                        },
                        {
                            "type": "text",
                            "text": text_prompt
                        }
                    ]
                }
            )
            last_text_prompt = text_prompt

    def action_api(self,):
        '''action api: 识别调用的Action并返回文字feedback，比如动作成功与否（如果有）'''
        pass      

if __name__ == '__main__':
    max_round = 100
    indexes = [i for i in range(181)] # task from 0 to 180, total 181 tasks
    index = 55 # the index-th task
    port = 5001 #+ index
    inner_port = random.randint(2000, 65536)
    #inner_port = 59568 
    #inner_port = 55000 + index # one task, one port 
    url = "http://192.168.1.191:"+str(port)+"/api"
    url = "http://192.168.3.60:"+str(port)+"/api"
    ip = "192.168.3.60"
    cwd = "/VAB-OmniGibson-code"
    times = int(time.time())
    test = True
    agent = QwenAgent()   
    oclient = OmnigibsonClient(ip, url, port, inner_port, max_round, index, times, agent, test, cwd)
    oclient.reset()
    oclient.render()
    oclient.step_full()
    #oclient.action_api()
    #oclient.step_full()



import argparse
import asyncio
import subprocess
import uvicorn
from fastapi import FastAPI, HTTPException, APIRouter
#from src.typings import TaskSampleExecutionResult, TaskOutput, SampleIndex, AgentOutputStatus, SampleStatus
#from src.configs import ConfigLoader
from typings import *
from utils import *
from pydantic import BaseModel
import os, time
import base64
import socket

class OmniStartSampleRequest(BaseModel):
    task : str
    scene : str
    inner_port : int

class OmniServerResponse(BaseModel):
    status: SampleStatus = SampleStatus.RUNNING
    result: JSONSerializable = None
    #text_prompt : str
    #image_url : str

class OmniInteractRequest(BaseModel):
    inner_port : int
    agent_response : AgentOutput

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

class OmniServer:
    '''This server runs on the docker with ip 192.168.3.101 and port 1139, 
    any client can access this server via http request with vpn.'''
    def __init__(
        self,
        router_,
        #controller_address,
        args,

    ) -> None:
        self.args = args
        self.router = router_

        self.router.post("/start_sample")(self.start_sample)
        self.router.post("/interact")(self.interact)
        self.router.post("/cancel")(self.cancel)

        self.router.on_event("startup")(self.initialize)
        self.router.on_event("shutdown")(self.shutdown)

        self.process = None
        self.initial_reward = None
        self.final_reward = None

        self.start = False

    def initialize(self):
        print("initialize what ..")
        
    
    def _get_returns(self, data, s):
        data = data.decode()
        reward = float(data.split("<RREWARD>")[-1].split("</RREWARD>")[0])
        if self.initial_reward == None:
            self.initial_reward = reward
        if "<DDONE>" in data and "</DDONE>" in data:
            done_message = data.split("<DDONE>")[-1].split("</DDONE>")[0]
            self.final_reward = reward
            if "task limit reached" in done_message:
                s.sendall("okay".encode())
                return SampleStatus.TASK_LIMIT_REACHED, None, None
            elif "agent invalid action" in done_message:
                s.sendall("okay".encode())
                return SampleStatus.AGENT_INVALID_ACTION, None, None
            elif "task error" in done_message:
                s.sendall("okay".encode())
                return SampleStatus.TASK_ERROR, None, None
            elif "task failed" in done_message:
                s.sendall("okay".encode())
                return SampleStatus.FAIL, None, None
            elif "task completed successfully" in done_message:
                s.sendall("okay".encode())
                return SampleStatus.SUCCESS, None, None
        image_path = data.split("<IIMAGE>")[-1].split("</IIMAGE>")[0]
        text_prompt = data.split(f"<IIMAGE>{image_path}</IIMAGE>")[0]
        #image_path = image_path.replace("/og_logs", "output/omnigibson")
        return  SampleStatus.RUNNING, text_prompt, image_path

    def _get_message(self, message):
        if message.status == AgentOutputStatus.AGENT_CONTEXT_LIMIT:
            return TaskSampleExecutionResult(status=SampleStatus.AGENT_CONTEXT_LIMIT)
        elif message.status != AgentOutputStatus.NORMAL:
            return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN)
        message = message.content
        if isinstance(message, tuple):
            message = message[0]
        if "Action Feedback:" in message:
            message = message.split("Action Feedback:")[0]
        if message.count("ACTION") >= 2:
            message_parts = message.split("ACTION", 2)
            message = "ACTION".join(message_parts[:2])
        if message.count("OBSERVATION") >= 2:
            message_parts = message.split("OBSERVATION", 2)
            message = "OBSERVATION".join(message_parts[:2])
        if "\n<|end_of_text|>" in message:
            message = message.split("\n<|end_of_text|>")[0]
        if "<|end_of_text|>" in message:
            message = message.split("<|end_of_text|>")[0]
        return message

    def start_sample(self, parameters: OmniStartSampleRequest):
        print(parameters.task)
        print(parameters.scene)
        print(parameters.inner_port)
        print(self.args.max_round)

        print("subprocess will start ... ")
        self.process = subprocess.Popen([
            "python",
            "main.py",
            "--task",
            parameters.task,
            "--scene",
            parameters.scene,
            "--port",
            str(parameters.inner_port),
            "--max_round",
            str(args.max_round),
            ],
            cwd = "/VAB-OmniGibson-code",
            #stdin=PIPE,
            #stdout=PIPE
        )
        print("subprocess started")
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("localhost", parameters.inner_port))
                data = s.recv(8192)
                if not data:
                    s.close()
                    continue
                else:
                    break
            except Exception as e:
                print("startup, wait for 4s ... to reconnect docker ", e)
                time.sleep(4)
        print("start sample, data is ", data)
        status, text_prompt, image_path = self._get_returns(data, s)
        #s.close()
        self.start = True
        self.s = s
        if status == SampleStatus.RUNNING:
            return OmniServerResponse(status=SampleStatus.RUNNING, result={"text_prompt":text_prompt, "image_url":encode_image(image_path)})
        else:
            return OmniServerResponse(status=status, result={"text_prompt":text_prompt, "image_url":image_path})

    def interact(self, parameters: OmniInteractRequest):
        message = self._get_message(parameters.agent_response)
        print("message proced: ", message)
        if self.start:
            self.start = False
            self.s.sendall(message.encode())
            #self.s.close()
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("localhost", parameters.inner_port))
                #s.sendall(message.encode())
                data = s.recv(8192)
                if not data:
                    s.close()
                    continue
                else:
                    break
            except Exception as e:
                print("interact, wait for 4s ... to reconnect docker, ", e)
                time.sleep(4)
        #return {"text":text_prompt, "image_url":image_path}
        print("interact, data is ", data)
        status, text_prompt, image_path = self._get_returns(data, s)
        #s.close()
        self.s = s
        self.start = True
        if status == SampleStatus.RUNNING:
            return OmniServerResponse(status=SampleStatus.RUNNING, result={"text_prompt":text_prompt, "image_url":encode_image(image_path)})
        else:
            return OmniServerResponse(status=status, result={"text_prompt":text_prompt, "image_url":image_path})


    def interact_cp(self, parameters: OmniInteractRequest):
        message = self._get_message(parameters.agent_response)
        print("message proced: ", message)
        if self.start:
            self.start = False
            self.s.sendall(message.encode())
            self.s.close()
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("localhost", parameters.inner_port))
                #s.sendall(message.encode())
                data = s.recv(8192)
                if not data:
                    s.close()
                    continue
                else:
                    break
            except Exception as e:
                print("interact, wait for 4s ... to reconnect docker, ", e)
                time.sleep(4)
        #return {"text":text_prompt, "image_url":image_path}
        print("interact, data is ", data)
        status, text_prompt, image_path = self._get_returns(data, s)
        s.close()
        if status == SampleStatus.RUNNING:
            return OmniServerResponse(status=SampleStatus.RUNNING, result={"text_prompt":text_prompt, "image_url":encode_image(image_path)})
        else:
            return OmniServerResponse(status=status, result={"text_prompt":text_prompt, "image_url":image_path})

        #return OmniServerResponse(status=SampleStatus.RUNNING, result={"text_prompt":text_prompt, "image_url":encode_image(image_path)})
 

    def cancel(self,):
        pass

    def shutdown(self,):
        if self.process is not None:
            self.process.terminate()
            self.process.kill()
            print("shutdown ... ")
        
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--self", "-s", type=str, default="http://localhost:5001/api")
    parser.add_argument("--port", "-p", type=int, default=5001)
    parser.add_argument("--max_round", "-m", type=int, default=100)

    args = parser.parse_args()

    app = FastAPI()
    router_ = APIRouter()
    omni_server = OmniServer(
        router_,
        args,
    )
    app.include_router(router_, prefix="/api")
    uvicorn.run(app=app, host="0.0.0.0", port=args.port)



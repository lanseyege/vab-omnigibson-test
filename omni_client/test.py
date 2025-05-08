import random
import time

from omni_client import OmnigibsonClient
from qwen_agent import QwenAgent

#first_agent_response = ChatCompletionMessage(content='OBSERVATION: In the living room, there is a carton labeled as `9.carton` and a book labeled as `2.boo    k`. The carton is on the floor near a table. There are no other visible books in this view.\n\nTHOUGHT: To achieve the goal, I need     to find three books and put them inside the carton. Then, I need to find three more books and place them on top of the carton. Since     only one book is currently visible, I should start by moving towards it and picking it up.\n\nACTION: move(2)', refusal=None, role=    'assistant', annotations=None, audio=None, function_call=None, tool_calls=None)

if __name__ == '__main__':
    max_round = 100
    index = 10
    port = 5001 #+ index
    inner_port = random.randint(2000, 65536)
    inner_port = 59460
    url = "http://192.168.1.191:"+str(port)+"/api"
    url = "http://192.168.3.60:"+str(port)+"/api"
    ip = "192.168.3.60"
    cwd = "/VAB-OmniGibson-code"
    times = int(time.time())
    test = True
    agent = QwenAgent()
    oclient = OmnigibsonClient(ip, url, port, inner_port, max_round, index, times, agent, test, cwd)
    oclient._get_test()
    oclient.step_num = 0
    #oclient.reset()
    oclient.render()
    oclient.step_full()
    #oclient.action_api()
    #oclient.step_full()



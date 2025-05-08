# vab-omnigibson-test

- 这个项目将VisualAgentBench里面的关于omnigibson的关键部分单独摘取出来，并进行了程序的简化，去掉了异步、信号锁、共享内存、多线程、实例工厂等等，只保留最基本的功能，环境内部部分不受任何影响 (千问的api-key请换成自己的！！)

### omni_server

- omni_server.py
    - fastapi + unicorn + APIRouter 进行http的请求监听和路由
    - 客户端发送请求start_sample 启动任务，subprocess.popen 开启子任务，等待3-5 mins omnigibson启动，
    - server 与 omnigibson 环境通过socket通信，
        - server 发送动作，omnigibson接受后进行解析，并调用自己的[函数](https://github.com/THUDM/VisualAgentBench/blob/main/src/server/tasks/omnigibson/vab_omnigibson_src/utils/actions.py)来执行（没有使用OMPL或cuRobo库）
        - omnigibson 发送文本prompt+图片url
    - omnigibson程序里面写定的step次数上限30，40, 等（限制条件不同），若执行不成功则返回失败，可以更改相应[源代码](https://github.com/THUDM/VisualAgentBench/blob/main/src/server/tasks/omnigibson/vab_omnigibson_src/agent.py#L47)(在docker内更改)改变交互上限
    - 客户端发送interact进行交互请求
- tasks.txt： 181个任务：格式（task, scene）
- typings and utils: 辅助函数，来自原项目

    将omni_server 放到了环境的docker内运行， /root/src/目录下
    
### omni_client

- omni_client.py
    - oclient = OmnigibsonClient( .., index, ..): index是task181个任务中的某一个编号
    - reset() 函数启动服务端任务，并得到返回（文本prompt+图片base64格式）文本prompt内容举例：
        - Your task goal is: Store the pumpkins and candles inside the cabinet, mugs on top of the cabinet. Place the caldron under the table in the living room. Pick all the documents from the sofa onto the table.
        - The reachable rooms during the task are: bathroom_0, bathroom_1, bedroom_0, corridor_0, dining_room_0, kitchen_0, living_room_0, living_room_1, living_room_2, storage_room_0, storage_room_1, storage_room_2.
        - Action Feedback: None actions before.
        - At Hand Object: None.
        - Current Room: living_room_0.
        - Vision Input: 

    其中第一句task goal 来自[文件](https://github.com/THUDM/VisualAgentBench/blob/main/src/server/tasks/omnigibson/vab_omnigibson_src/task/task_goal.json)

    - render() 函数: （简单实现，可以根据需求更新。。）
    - step_full() 函数，调用_step_once_time()函数，与agent和serer断进行交互
        - agent.inference(messages)
        - request.post('/interact', json = content... )
- qwen_agent.py
    - 根据系统提示词，返回格式为(只是用content部分)
        - {'content': 'THOUGHT: I need to move towards the cabinet in the kitchen to place the pumpkin inside it. The previous action was invalid because `move_to` is not a predefined function; instead, I should use `move`.\n\nACTION: move(3.cabinet)', 'refusal': None, 'role': 'assistant', 'annotations': None, 'audio': None, 'function_call': None, 'tool_calls': None} 
        - client将content部分通过post interact 传递给server端，然后server端通过socket传递给omnigbson环境，然后环境解析出"ACTION: MOVE(3.cabinet)"，并调用自己的[函数](https://github.com/THUDM/VisualAgentBench/blob/main/src/server/tasks/omnigibson/vab_omnigibson_src/utils/actions.py)来执行（没有使用OMPL或cuRobo库）
    - VAB的程序里，对agent的输入messages包括：系统提示词 + 环境的历史反馈（只包含文本prompt）+ 上一次agent反馈content部分 + 这次环境反馈（文本prompt+图片base64格式）
- prompt.py： 系统的提示词
- typings and utils: 辅助函数，来自原项目
- tasks.txt： 181个任务：格式（task, scene）
- data
    
    omni_client 部分可以在宿主或链接vpn的机器上运行

### 环境部分 docker

- 这个[代码文件夹](https://github.com/THUDM/VisualAgentBench/tree/main/src/server/tasks/omnigibson/vab_omnigibson_src)是于docker内运行的,20G的原始镜像+30G的数据（有他们自己定义的一些场景，官方的数据不到30G），默认在docker的/VAB-OmniGibson-code 目录下
- 数据在docker的/omnigibson-src/omnigibson/data/下，运行他们自己的数据脚本下载，然后移动到这个目录
- omnigibson的docker环境需要cuda12.1/12.2版本+相应driver，NVIDIA container toolkit[离线安装教程](https://zhuanlan.zhihu.com/p/15194336245)
- 由于我们摘取了程序最基本的地方，所以服务端程序不支持多人，多任务同时调用，这个可以每人配置一个docker容器解决


（待续。。。）


# vab-omnigibson-test

- 这个项目将VisualAgentBench里面的关于omnigibson的关键部分单独摘取出来，并进行了程序的简化，去掉了异步、信号锁、共享内存、多线程、实例工厂等等，只保留最基本的功能，环境内部部分不受任何影响

### omni\_server
    - omni\_server.py
    - tasks.txt： 181个任务：格式（task, scene）
    - typings and utils: 辅助函数，来自原项目

    将omni\_server 放到了环境的docker内运行， /root/src/目录下
    
### omni\_client
    - omni\_client.py
        - oclient = OmnigibsonClient( .., index, ..): index是task181个任务中的某一个编号
        - reset() 函数启动服务端任务，并得到返回（文本+图片base64格式）文本内容举例：
            - Your task goal is: Store the pumpkins and candles inside the cabinet, mugs on top of the cabinet. Place the caldron under the table in the living room. Pick all the documents from the sofa onto the table.
            - The reachable rooms during the task are: bathroom\_0, bathroom\_1, bedroom\_0, corridor\_0, dining\_room\_0, kitchen\_0, living\_room\_0, living\_room\_1, living\_room\_2, storage\_room\_0, storage\_room\_1, storage\_room\_2.
            - Action Feedback: None actions before.
            - At Hand Object: None.
            - Current Room: living\_room\_0.
            - Vision Input: 

            其中第一句task goal 来自文件(https://github.com/THUDM/VisualAgentBench/blob/main/src/server/tasks/omnigibson/vab_omnigibson_src/task/task_goal.json)
        - render() 函数: （简单实现，可以根据需求更新。。）
        - step_full() 函数，调用_step_once_time()函数，与agent和serer断进行交互
    - qwen\_agent.py
    - prompt.py： 系统的提示词
    - tasks.txt
    - typings and utils: 辅助函数，来自原项目
    - tasks.txt： 181个任务：格式（task, scene）
    - data
    
    omni\_client 部分可以在宿主或链接vpn的机器上运行

### 环境部分 docker

    - (https://github.com/THUDM/VisualAgentBench/tree/main/src/server/tasks/omnigibson/vab_omnigibson_src) 这段代码是于docker内运行的,20G的原始镜像+30G的数据（有他们自己定义的一些场景，官方的数据不到30G）
    - 由于我们摘取了程序最基本的地方，所以服务端程序不支持多人，多任务调用，这个可以每人配置一个docker容器解决

（带续）


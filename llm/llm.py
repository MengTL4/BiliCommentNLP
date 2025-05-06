from pprint import pprint

import requests

url = 'http://127.0.0.1:11434/api/chat'
data = {
    "model": "qwen3:4b",
    "messages": [
        {
            "role": "user",
            "content": "[笑哭]舟舟加上9那样的多倍看录像功能之后，终于打消了我的懒得玩焦虑、游戏理解焦虑和养成焦虑 最副游的一集。前面这句话情感倾向是什么，直接给出结果"
        }
    ],
    "stream": False,
}
response = requests.post(url, json=data)
pprint(response.json())

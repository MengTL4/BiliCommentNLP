import json
import requests


class ReqClient:
    def __init__(self):
        self.url = "http://0.0.0.0:8189/taskflow/senta"
        self.headers = {"Content-Type": "application/json"}

    def req(self, text):
        # texts = ["我觉得这个东西不错", "他的服务态度不行"]
        comments = {
            "data": {
                "text": text,
            }
        }
        # print(text)
        req = requests.post(url=self.url, headers=self.headers, data=json.dumps(comments))
        return req.json()



# url = "http://0.0.0.0:8189/taskflow/senta"
# headers = {"Content-Type": "application/json"}
# texts = ["我觉得这个东西不错", "他的服务态度不行"]
# data = {
#     "data": {
#         "text": texts,
#     }
# }
# r = requests.post(url=url, headers=headers, data=json.dumps(data))
# datas = json.loads(r.text)
# print(datas)
# # 正常解析 非正常: {'result': [{}]}
# result = datas['result'][0]['评价维度'][0]['relations']['情感倾向[正向,负向,未提及]'][0]['text']
# probability = datas['result'][0]['评价维度'][0]['relations']['情感倾向[正向,负向,未提及]'][0]['probability']
# print(result)
# print(probability)
#
# if len(datas['result'][0]) == 0:
#     print("异常")
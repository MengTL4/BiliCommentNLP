import math
import random
import time

from core.commentDB import MongoDBMix

# 生成 1 到 2 秒之间的随机延迟（以秒为单位）
# delay = (random.random() + 1)
# print(f"程序将休眠 {delay} 秒")
# # 让程序休眠指定的时间
# time.sleep(delay)
# print("休眠结束")
#
# # mongdb = MongoDBMix()
# # mongdb.create_database()
# a = 101
# for i in range(1, math.ceil(a/20)+1):
#     print(i)
data = {"result": [{"情感倾向[正向,负向,未提及]": [{"text": "正向", "probability": 0.8460592686925494}]}]}
print(data['result'][0]['情感倾向[正向,负向,未提及]'][0]['text'])
print(data['result'][0]['情感倾向[正向,负向,未提及]'][0]['probability'])
data2 = {"result": [{}]}
if len(data['result'][0]) != 0:
    print(999)
else:
    print(666)

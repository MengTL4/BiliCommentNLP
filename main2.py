import json
import random
import time
from pprint import pprint

from pymongo import MongoClient

from biliUtils.bvConverter import BvConverter
from biliUtils.comment import Comment
from core.map_generator import generate_comment_map
from core.parseReply import parse_comment_response
from core.process import ProcessHandle

# schema = {'评价维度': ['观点词', '情感倾向[正向，负向]']}  # Define the schema for opinion extraction
# schema2 = '情感倾向[正向，负向]'
# ie = Taskflow('information_extraction', schema=schema2)
# ie.set_schema(schema2)  # Reset schema
# pprint(ie("考古站错了，不管了。"))  # Better print results using pprint


if __name__ == '__main__':
    # 实例化
    # comment = Comment()
    # bvConverter = BvConverter()
    #
    # # bv转av
    # bv = "BV1HLVFzJENH"
    # oid = bvConverter.bv2av(bv)
    # print(oid)
    #
    # # 获取评论数量
    # count = comment.replyCount(oid)['data']['count']
    # print(count)
    #
    # # for i in range(1, 9999):
    # # 主评论
    # responses = comment.replyResponse(oid, 1)
    # print(responses)
    # comments = parse_comment_response(responses)
    # print(json.dumps(comments, ensure_ascii=False, indent=2))
    # pprint(comment.videoList(6639802, 1)['data']['list']['vlist'])
    # processHandle = ProcessHandle()
    # processHandle.fetch_video_list(6639802)
    #
    # # 获取主评论-循环
    # for i in range(1, 9999):
    #     responses = comment.replyResponse(oid, i)
    #     if responses['data']['cursor']['is_end'] is True:
    #         print(f"{oid}主评论获取完成")
    #         break
    #     else:
    #         comments = parse_comment_response(responses)
    #         print(json.dumps(comments, ensure_ascii=False, indent=2))
    #         delay = (random.random() + 1)
    #         print(f"{oid}主评论获取将等待 {delay} 秒")
    #         time.sleep(delay)
    #         print(f"{oid}主评论获取等待结束")
    #
    # # 子评论
    # response = comment.subreplyResponse(oid, 261740767712, 1)
    # # print(response)
    # comments = parse_comment_response(response)
    # print(len(comments))
    # print(json.dumps(comments, ensure_ascii=False, indent=2))
    #
    # # 子评论-循环
    # for i in range(1, 9999):
    #     response = comment.subreplyResponse(oid, 261740767712, i)
    #     comments = parse_comment_response(response)
    #     if len(comments) == 0:
    #         break
    #     else:
    #         print(json.dumps(comments, ensure_ascii=False, indent=2))
    #         delay = (random.random() + 1)
    #         print(f"子评论获取获取将等待 {delay} 秒")
    #         time.sleep(delay)
    #         print("子评论获取等待结束")

    # 连接本地MongoDB服务（无用户名密码）
    client = MongoClient('mongodb://localhost:27017/')

    # 选择数据库和集合
    # 假设你的数据库名为bilibili，集合名为comments，根据你的实际情况修改
    db = client['bilibili']
    collection = db['main_comments']

    # 生成评论地图
    output_dir = "output"
    html_path = generate_comment_map(collection, output_dir)

    print(f"地图已生成在: {html_path}")


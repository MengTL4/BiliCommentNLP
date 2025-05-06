from pprint import pprint

from biliUtils.bvConverter import BvConverter
from biliUtils.comment import Comment
from core.commentDB import MongoDBMix
from core.process import ProcessHandle
from server.client import ReqClient


def main():
    # bv转av
    bvConverter = BvConverter()
    bv = "BV1HLVFzJENH"
    oid = bvConverter.bv2av(bv)
    print(oid)

    # 获取评论数量
    comment = Comment()
    count = comment.replyCount(oid)['data']['count']
    print(count)

    # 获取主评论和子评论
    processHandle = ProcessHandle()
    processHandle.fetch_main_comments(oid)
    processHandle.fetch_sub_comments(oid)

    # 添加评论到数据库中
    mongDBMix = MongoDBMix()
    mongDBMix.insert_main_comments(processHandle.rpids_main)
    mongDBMix.insert_sub_comments(processHandle.rpids_sub)

    # 获取数据库中的评论并请求nlp服务,然后更新结果
    reqClient = ReqClient()
    all_main_comments = mongDBMix.get_main_comments_from_db()
    for comment in all_main_comments:
        result = reqClient.req(comment)
        mongDBMix.update_main_comment_with_result(comment, result)

    all_sub_comments = mongDBMix.get_sub_comments_from_db()
    for comment in all_sub_comments:
        result = reqClient.req(comment)
        mongDBMix.update_sub_comment_with_result(comment, result)


if __name__ == '__main__':
    main()

import json
import random
import time

from biliUtils.comment import Comment
from core.parseReply import parse_comment_response


class ProcessHandle:
    def __init__(self):
        self.rpids_main = []
        self.rpids_sub = []
        self.video_list = []
        self.comment = Comment()

    def fetch_main_comments(self, oid):
        # 去重
        seen_rpids = set()
        for i in range(1, 9999):
            try:
                main_reply = self.comment.replyResponse(oid, i)
                if not main_reply or 'data' not in main_reply:
                    print(f"获取主评论失败，返回数据异常: {main_reply}")
                    break

                comments = parse_comment_response(main_reply)
                if not comments:
                    print(f"第{i}页主评论解析为空，结束获取")
                    break
                else:
                    # 扁平化
                    filtered = [c for c in comments if c.get('rpid') not in seen_rpids]
                    seen_rpids.update(c.get('rpid') for c in filtered)
                    self.rpids_main.extend(filtered)
                    delay = (random.random() + 1)
                    print(f"已收集{len(self.rpids_main)}条主评论,{oid}延时等待 {delay} 秒")
                    time.sleep(delay)
            except Exception as e:
                print(f"获取主评论出错: {e}")
                break

        if not self.rpids_main:
            print(f"视频 {oid} 未获取到任何主评论")

    # def fetch_main_comments(self, oid):
    #     # 去重
    #     seen_rpids = set()
    #     for i in range(1, 99999):
    #         main_reply = self.comment.replyResponse(oid, i)
    #         # print(main_reply)
    #         # time.sleep(random.random() + 2)
    #         comments = parse_comment_response(main_reply)
    #         if not comments:
    #             break
    #         else:
    #             # 扁平化
    #             filtered = [c for c in comments if c.get('rpid') not in seen_rpids]
    #             # 添加视频oid到每条评论中
    #             for comment in filtered:
    #                 comment['oid'] = oid
    #             seen_rpids.update(c.get('rpid') for c in filtered)
    #             self.rpids_main.extend(filtered)
    #             delay = (random.random() + 3)
    #             print(f"已收集{len(self.rpids_main)}条主评论,{oid}延时等待 {delay} 秒")
    #             time.sleep(delay)

    def fetch_sub_comments(self, oid):
        # 如果没有主评论，则跳过获取子评论
        if not self.rpids_main:
            print("没有主评论，跳过获取子评论")
            return

        # 去重
        seen_sub_rpids = set()
        for i in self.rpids_main:
            try:
                rpid = i.get('rpid')
                if not rpid:
                    print(f"主评论数据缺少rpid字段: {i}")
                    continue

                for j in range(1, 9999):
                    try:
                        sub_reply = self.comment.subreplyResponse(oid, rpid, j)
                        if not sub_reply or 'data' not in sub_reply:
                            print(f"获取子评论失败，返回数据异常: {sub_reply}")
                            break

                        comments = parse_comment_response(sub_reply)
                        if not comments:
                            break
                        else:
                            filtered = [c for c in comments if c.get('rpid') not in seen_sub_rpids]
                            # 添加视频oid到每条子评论中
                            for comment in filtered:
                                comment['oid'] = oid
                            seen_sub_rpids.update(c.get('rpid') for c in filtered)
                            self.rpids_sub.extend(filtered)
                            delay = (random.random() + 3)
                            print(f"已收集{len(self.rpids_sub)}条子评论,{rpid}子评论延时等待 {delay} 秒")
                            time.sleep(delay)
                    except Exception as e:
                        print(f"获取子评论出错: {e}")
                        break
            except Exception as e:
                print(f"处理主评论出错: {e}")

        if not self.rpids_sub:
            print(f"视频 {oid} 未获取到任何子评论")

    def fetch_video_list(self, mid):
        for i in range(1, 99999):
            response = self.comment.videoList(mid, i)
            video_list = response['data']['list']['vlist']
            if not video_list:
                break
            else:
                self.video_list.extend(video_list)
                delay = (random.random() + 1)
                print(f"已收集{len(self.video_list)}条视频,延时等待 {delay} 秒")
                time.sleep(delay)

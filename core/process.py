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
        for i in range(1, 99999):
            main_reply = self.comment.replyResponse(oid, i)
            comments = parse_comment_response(main_reply)
            if not comments:
                break
            else:
                # 扁平化
                filtered = [c for c in comments if c.get('rpid') not in seen_rpids]
                seen_rpids.update(c.get('rpid') for c in filtered)
                self.rpids_main.extend(filtered)
                delay = (random.random() + 1)
                print(f"已收集{len(self.rpids_main)}条主评论,{oid}延时等待 {delay} 秒")
                time.sleep(delay)

    def fetch_sub_comments(self, oid):
        # 去重
        seen_sub_rpids = set()
        for i in self.rpids_main:
            for j in range(1, 99999):
                sub_reply = self.comment.subreplyResponse(oid, i.get('rpid'), j)
                comments = parse_comment_response(sub_reply)
                if not comments:
                    break
                else:
                    filtered = [c for c in comments if c.get('rpid') not in seen_sub_rpids]
                    seen_sub_rpids.update(c.get('rpid') for c in filtered)
                    self.rpids_sub.extend(filtered)
                    delay = (random.random() + 1)
                    print(f"已收集{len(self.rpids_sub)}条子评论,{i.get('rpid')}子评论延时等待 {delay} 秒")
                    time.sleep(delay)

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

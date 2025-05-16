from fake_useragent import UserAgent
import requests
import time
import random

from model.model import ReqRespondModel
from wbiUtils.pagination_str import encode_pagination_offset, PaginationOffset
from wbiUtils.wbiEncrypter import WbiEncryption


class Comment:
    def __init__(self):
        self.REPLY_COUNT_API = "https://api.bilibili.com/x/v2/reply/count"
        self.REPLY_HOT_API = "https://api.bilibili.com/x/v2/reply/hot"
        self.REPLY_SUB_API = "https://api.bilibili.com/x/v2/reply/reply"
        self.REPLY_MAIN_API = "https://api.bilibili.com/x/v2/reply/main"
        self.VIDEO_LIST_API = "https://api.bilibili.com/x/space/wbi/arc/search"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
            "Referer": "https://www.bilibili.com",
            "Origin": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*",
            "Cookie": "SESSDATA=4c3e5295%2C1762267631%2C3d180%2A51CjBt8_nK3amnqNkiR_UR3cM81KlBs0vKUJvcfyaQK8SXaxdafK1O5y65npULAYY9TgUSVndZczBwTmdVeE80d29nZG05MjgwSWphXzdzZ1hhajMwZm1TT1I3dTBPTmxZc3pFcXE5Zi02Qm03bUF4RE41S1BSMTdPd0VJRTJKNF9hYlBhS2RXZ2hBIIEC",
        }
        self.session.headers.update(self.headers)
        self.max_retries = 3
        self.retry_delay = 2

    def get(self, *args, **kwargs):
        retries = 0
        while retries < self.max_retries:
            try:
                resp = self.session.get(*args, **kwargs, timeout=10)
                code = resp.status_code

                # 检查状态码
                if code != 200:
                    print(f"请求返回非200状态码: {code}")
                    retries += 1
                    time.sleep(self.retry_delay * (retries + random.random()))
                    continue

                try:
                    jsonData = resp.json()

                    # 检查B站API返回码
                    if jsonData and 'code' in jsonData and jsonData['code'] != 0:
                        print(f"B站API返回错误码: {jsonData['code']}, 消息: {jsonData.get('message', '')}")
                        # 针对特定错误码可以特殊处理
                        if jsonData['code'] == -412:  # 被风控了
                            print("请求被风控，等待更长时间后重试")
                            time.sleep(20 + random.random() * 10)
                            retries += 1
                            continue
                except Exception as e:
                    print(f"解析JSON失败: {e}")
                    jsonData = None

                text = resp.text
                return ReqRespondModel(code=code, respDict=jsonData, respText=text)
            except requests.exceptions.RequestException as e:
                print(f"请求异常: {e}")
                retries += 1
                if retries >= self.max_retries:
                    print("已达到最大重试次数")
                    return ReqRespondModel(code=500, respDict={"code": -1, "message": f"请求失败: {str(e)}"},
                                           respText="")

                print(f"第{retries}次重试...")
                time.sleep(self.retry_delay * (retries + random.random()))

        # 所有重试都失败了
        return ReqRespondModel(code=500, respDict={"code": -1, "message": "达到最大重试次数"}, respText="")

    def post(self, *args, **kwargs):
        retries = 0
        while retries < self.max_retries:
            try:
                resp = self.session.post(*args, **kwargs, timeout=10)
                code = resp.status_code

                if code != 200:
                    print(f"POST请求返回非200状态码: {code}")
                    retries += 1
                    time.sleep(self.retry_delay * (retries + random.random()))
                    continue

                try:
                    jsonData = resp.json()

                    # 检查B站API返回码
                    if jsonData and 'code' in jsonData and jsonData['code'] != 0:
                        print(f"B站API返回错误码: {jsonData['code']}, 消息: {jsonData.get('message', '')}")
                except:
                    jsonData = None

                text = resp.text
                return ReqRespondModel(code=code, respDict=jsonData, respText=text)
            except requests.exceptions.RequestException as e:
                print(f"POST请求异常: {e}")
                retries += 1
                if retries >= self.max_retries:
                    print("已达到最大重试次数")
                    return ReqRespondModel(code=500, respDict={"code": -1, "message": f"请求失败: {str(e)}"},
                                           respText="")

                print(f"第{retries}次重试...")
                time.sleep(self.retry_delay * (retries + random.random()))

        return ReqRespondModel(code=500, respDict={"code": -1, "message": "达到最大重试次数"}, respText="")

    def replyCount(self, oid):
        try:
            resp = self.get(self.REPLY_COUNT_API + f"?oid={oid}&type=1")
            return resp.respDict
        except Exception as e:
            print(f"获取评论计数出错: {e}")
            return {"code": -1, "message": str(e), "data": {"count": 0}}

    def replyResponse(self, oid, pn):
        try:
            # 第一次请求
            if pn == 1:
                params = {
                    'type': '1',
                    'oid': oid,
                    'mode': '3',
                    'plat': '1',
                    'web_location': '1315875',
                    'pagination_str': encode_pagination_offset()
                }
                signed_query = WbiEncryption.get_signed_query(params)
                # print("Signed Query:", signed_query)
                resp = self.get(self.REPLY_MAIN_API + f"?{signed_query}")
                # print(resp)
                return resp.respDict
            else:
                # 后续请求
                pagination = PaginationOffset(type=1, direction=1, pn=pn)
                params = {
                    'type': '1',
                    'oid': oid,
                    'mode': '3',
                    'plat': '1',
                    'web_location': '1315875',
                    'pagination_str': encode_pagination_offset(pagination)
                }
                signed_query = WbiEncryption.get_signed_query(params)
                # print("Signed Query:", signed_query)
                resp = self.get(self.REPLY_MAIN_API + f"?{signed_query}")
                # print(resp)
                return resp.respDict
        except Exception as e:
            print(f"获取主评论出错 (oid={oid}, pn={pn}): {e}")
            return {"code": -1, "message": str(e), "data": {"replies": []}}

    def subreplyResponse(self, oid, root, pn):
        try:
            resp = self.get(self.REPLY_SUB_API + f"?oid={oid}&type=1&root={root}&pn={pn}&ps=20")
            return resp.respDict
        except Exception as e:
            print(f"获取子评论出错 (oid={oid}, root={root}, pn={pn}): {e}")
            return {"code": -1, "message": str(e), "data": {"replies": []}}

    def videoList(self, mid, pn):
        try:
            params = {
                'mid': mid,
                'pn': pn,
            }
            signed_query = WbiEncryption.get_signed_query(params)
            resp = self.get(self.VIDEO_LIST_API + f"?{signed_query}")
            return resp.respDict
        except Exception as e:
            print(f"获取视频列表出错 (mid={mid}, pn={pn}): {e}")
            return {"code": -1, "message": str(e), "data": {"list": {"vlist": []}}}

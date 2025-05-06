from fake_useragent import UserAgent
import requests

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
            "User-Agent": UserAgent().random,
            "Referer": "https://www.bilibili.com",
            "Origin": "https://www.bilibili.com",
            "Cookie": "",
        }
        self.session.headers.update(self.headers)

    def get(self, *args, **kwargs):
        resp = self.session.get(*args, **kwargs)
        code = resp.status_code
        try:
            jsonData = resp.json()
        except:
            jsonData = None
        text = resp.text
        return ReqRespondModel(code=code, respDict=jsonData, respText=text)

    def post(self, *args, **kwargs):
        resp = self.session.post(*args, **kwargs)
        code = resp.status_code
        try:
            jsonData = resp.json()
        except:
            jsonData = None
        text = resp.text
        return ReqRespondModel(code=code, respDict=jsonData, respText=text)

    def replyCount(self, oid):
        resp = self.get(self.REPLY_COUNT_API + f"?oid={oid}&type=1")
        return resp.respDict

    def replyResponse(self, oid, pn):
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
            return resp.respDict

    def subreplyResponse(self, oid, root, pn):
        resp = self.get(self.REPLY_SUB_API + f"?oid={oid}&type=1&root={root}&pn={pn}&ps=20")
        return resp.respDict

    def videoList(self, mid, pn):
        params = {
            'mid': mid,
            'pn': pn,
        }
        signed_query = WbiEncryption.get_signed_query(params)
        resp = self.get(self.VIDEO_LIST_API + f"?{signed_query}")
        return resp.respDict

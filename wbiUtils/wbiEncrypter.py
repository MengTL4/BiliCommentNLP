import time
import urllib.parse
from functools import reduce
from hashlib import md5
import requests


class WbiEncryption:
    mixinKeyEncTab = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]

    _wbi_keys_cache = None  # 缓存 img_key 和 sub_key

    @staticmethod
    def getMixinKey(orig: str) -> str:
        return reduce(lambda s, i: s + orig[i], WbiEncryption.mixinKeyEncTab, '')[:32]

    @staticmethod
    def getWbiKeys(force_refresh=False) -> tuple[str, str]:
        if not force_refresh and WbiEncryption._wbi_keys_cache:
            return WbiEncryption._wbi_keys_cache

        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/'
        }
        resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=headers)
        resp.raise_for_status()
        data = resp.json()['data']
        img_url = data['wbi_img']['img_url']
        sub_url = data['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        WbiEncryption._wbi_keys_cache = (img_key, sub_key)
        return img_key, sub_key

    @staticmethod
    def sign_params(params: dict) -> dict:
        img_key, sub_key = WbiEncryption.getWbiKeys()
        mixin_key = WbiEncryption.getMixinKey(img_key + sub_key)
        curr_time = int(time.time())
        params = {**params, 'wts': curr_time}

        # 过滤特殊字符
        filtered = {
            k: ''.join(filter(lambda c: c not in "!'()*", str(v)))
            for k, v in sorted(params.items())
        }

        # 手动编码并生成签名
        query = '&'.join([f'{k}={urllib.parse.quote(str(v))}' for k, v in filtered.items()])
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()
        filtered['w_rid'] = wbi_sign
        return filtered

    @staticmethod
    def get_signed_query(params: dict) -> str:
        return urllib.parse.urlencode(WbiEncryption.sign_params(params))


if __name__ == "__main__":
    from wbiUtils.pagination_str import encode_pagination_offset

    params = {
        'type': '1',
        'oid': '1156200565',
        'mode': '3',
        'plat': '1',
        'web_location': '1315875',
        'pagination_str': encode_pagination_offset()
    }
    print(params)
    signed_query = WbiEncryption.get_signed_query(params)
    print("Signed Query:", signed_query)

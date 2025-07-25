# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import os
import time
import requests
import urllib

lfasr_host = 'https://raasr.xfyun.cn/v2/api'
api_upload = '/upload'
api_get_result = '/getResult'


class RequestApi(object):
    def __init__(self, appid, secret_key, upload_file_path):
        self.appid = appid
        self.secret_key = secret_key
        self.upload_file_path = upload_file_path
        self.ts = str(int(time.time()))
        self.signa = self.get_signa()

    def get_signa(self):
        appid = self.appid
        secret_key = self.secret_key
        m2 = hashlib.md5()
        m2.update((appid + self.ts).encode('utf-8'))
        md5 = m2.hexdigest()
        md5 = bytes(md5, encoding='utf-8')
        signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        return signa.decode('utf-8')

    def upload(self):
        print("上传部分：")
        file_len = os.path.getsize(self.upload_file_path)
        file_name = os.path.basename(self.upload_file_path)

        param_dict = {
            'appId': self.appid,
            'signa': self.signa,
            'ts': self.ts,
            'fileSize': file_len,
            'fileName': file_name,
            'duration': "200"
        }
        print("upload参数：", param_dict)

        with open(self.upload_file_path, 'rb') as f:
            data = f.read(file_len)

        url = lfasr_host + api_upload + "?" + urllib.parse.urlencode(param_dict)
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=data)
        result = response.json()
        print("upload resp:", result)
        return result

    def get_result(self):
        uploadresp = self.upload()
        if 'content' not in uploadresp or 'orderId' not in uploadresp['content']:
            print("上传失败，无法获取 orderId")
            return None

        orderId = uploadresp['content']['orderId']
        param_dict = {
            'appId': self.appid,
            'signa': self.signa,
            'ts': self.ts,
            'orderId': orderId,
            'resultType': "transfer,predict"
        }
        print("\n查询部分：")
        print("get result参数：", param_dict)

        status = 3
        while status == 3:
            response = requests.post(
                url=lfasr_host + api_get_result + "?" + urllib.parse.urlencode(param_dict),
                headers={"Content-Type": "application/json"}
            )
            result = response.json()
            print(result)
            status = result['content']['orderInfo'].get('status', 3)
            print("status=", status)
            if status == -1:
                break
            time.sleep(5)

        print("get_result resp:", result)

        # 解析转写文本并返回
        if status == -1 and 'orderResult' in result['content'] and result['content']['orderResult']:
            try:
                order_result_str = result['content']['orderResult']
                order_result_json = json.loads(order_result_str)
                lattice = order_result_json.get("lattice", [])
                transcribed_text = ""

                for item in lattice:
                    if "json_1best" in item:
                        inner_json = json.loads(item["json_1best"])
                        words = [
                            cw["w"]
                            for rt_item in inner_json["st"]["rt"]
                            for ws_item in rt_item["ws"]
                            for cw in ws_item["cw"]
                        ]
                        sentence = "".join(words).strip()
                        if sentence:
                            transcribed_text += sentence + "\n"

                return transcribed_text.strip()
            except json.JSONDecodeError as e:
                print(f"解析 orderResult 失败: {e}")
                return None
            except Exception as e:
                print(f"处理转写结果时发生错误: {e}")
                return None
        else:
            return None
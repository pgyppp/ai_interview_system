# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#   本demo测试时运行的环境为：Windows + Python3.7
#   本demo测试成功运行时所安装的第三方库及其版本如下：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#   合成小语种需要传输小语种文本、使用小语种发音人vcn、tte=unicode以及修改文本编码方式
#   错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os
import logging # 引入logging模块

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


STATUS_FIRST_FRAME = 0   # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2    # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "xiaoyan", "tte": "utf8"}
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}
        #使用小语种须使用以下方式，此处的unicode指的是 utf16小端的编码方式，即"UTF-16LE"”
        #self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-16')), "UTF8")}

    # 生成url
    def create_url(self):
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # logging.debug("websocket url : %s" % url) # 使用logging而不是print
        return url

# --- 移除或注释掉全局的 on_message 函数的文件写入部分 ---
# 这个全局 on_message 函数很可能与 run_tts 内部的动态 on_message_dynamic 冲突
# 导致文件路径问题和重复保存
def on_message(ws, message):
    try:
        message = json.loads(message)
        code = message["code"]
        sid = message["sid"]
        audio = message["data"]["audio"]
        audio = base64.b64decode(audio)
        status = message["data"]["status"]
        # print(message) # 根据需要决定是否保留
        if status == 2:
            logging.info("全局 ws is closed") # 标记为全局，以便区分
            ws.close()
        if code != 0:
            errMsg = message["message"]
            logging.error("全局 sid:%s call error:%s code is:%s" % (sid, errMsg, code)) # 使用logging
        # else:
        #     # ⚠️ 移除或注释掉这部分代码，避免与动态回调冲突
        #     with open('./demo.pcm', 'ab') as f:
        #         f.write(audio)
        #     from utils.audio_utils import pcm_to_wav
        #     pcm_to_wav('./demo.pcm', output_path='./audio_question')
    except Exception as e:
        logging.error("全局 receive msg, but parse exception: %s" % e, exc_info=True) # 加上 exc_info 打印完整堆栈

# 收到websocket错误的处理
def on_error(ws, error):
    logging.error("### websocket error: %s" % error)


# 收到websocket关闭的处理
def on_close(ws, *args):
    logging.info("### websocket closed ###")


# --- 移除或注释掉全局 on_open 函数中与文件相关的逻辑 ---
def on_open(ws):
    def run(*args):
        d = {"common": wsParam.CommonArgs,
             "business": wsParam.BusinessArgs,
             "data": wsParam.Data,
             }
        d = json.dumps(d)
        logging.info("------>开始发送文本数据 (全局 on_open)") # 标记为全局
        ws.send(d)
        # ⚠️ 移除或注释掉这部分代码，避免与动态回调冲突
        # if os.path.exists('./demo.pcm'):
        #     os.remove('./demo.pcm')

    thread.start_new_thread(run, ())


# 全局变量，用于存储WebSocket连接和参数 (虽然在run_tts中重新定义，但保留以防其他地方使用)
ws_app = None
ws_param_global = None

def run_tts(text, output_filepath):
    # from config.voice_config import VOICE_CONFIG
    # 从您的配置中导入语音配置
    from config.voice_config import VOICE_CONFIG # 确保这个导入路径正确
    from utils.audio_utils import pcm_to_wav # 确保这个导入路径正确

    class Ws_Param_Dynamic(Ws_Param):
        def __init__(self, APPID, APIKey, APISecret, Text, output_filepath):
            super().__init__(APPID, APIKey, APISecret, Text)
            self.output_filepath = output_filepath # 存储目标WAV文件的完整路径

    # --- 动态消息处理回调函数 ---
    def on_message_dynamic(ws, message):
        try:
            message = json.loads(message)
            code = message["code"]
            sid = message["sid"]
            audio = message["data"]["audio"]
            audio = base64.b64decode(audio)
            status = message["data"]["status"]
            # logging.debug(message) # 调试时可以打开

            if code != 0:
                errMsg = message["message"]
                logging.error("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
            else:
                # 确保输出目录存在
                # os.path.dirname(ws.ws_param.output_filepath) 获取的是如 'e:\\...\\question_audio'
                output_dir = os.path.dirname(ws.ws_param.output_filepath)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logging.info(f"创建目录: {output_dir}") # 记录目录创建

                # PCM临时文件路径，例如 'e:\\...\\question_0_hash.pcm'
                pcm_temp_path = ws.ws_param.output_filepath.replace('.wav', '.pcm')

                with open(pcm_temp_path, 'ab') as f:
                    f.write(audio)

                if status == 2: # 最后一帧
                    # logging.info("接收到最后一帧，即将关闭WebSocket并转换文件")
                    ws.close() # 关闭WebSocket连接
                    
                    # 转换PCM到WAV
                    pcm_to_wav(pcm_temp_path, output_path=ws.ws_param.output_filepath)
                    logging.info(f"音频文件已保存到: {ws.ws_param.output_filepath}")
                    
                    # 删除临时PCM文件
                    if os.path.exists(pcm_temp_path):
                        os.remove(pcm_temp_path)
                        logging.info(f"已删除临时PCM文件: {pcm_temp_path}")

        except Exception as e:
            logging.error(f"receive msg, but parse exception: {e}", exc_info=True) # 打印详细堆栈信息

    # --- 动态连接建立回调函数 ---
    def on_open_dynamic(ws):
        def run(*args):
            d = {"common": ws.ws_param.CommonArgs,
                 "business": ws.ws_param.BusinessArgs,
                 "data": ws.ws_param.Data,
                 }
            d = json.dumps(d)
            logging.info("------>开始发送文本数据 (动态 on_open)")
            ws.send(d)
        thread.start_new_thread(run, ())

    # 初始化动态参数类
    # 注意：这里需要确保 VOICE_CONFIG 是可访问的，且包含正确的 APP_ID, API_SECRET, API_KEY
    ws_param_current_call = Ws_Param_Dynamic(
        APPID=VOICE_CONFIG['APP_ID'],
        APISecret=VOICE_CONFIG['API_SECRET'],
        APIKey=VOICE_CONFIG['API_KEY'],
        Text=text,
        output_filepath=output_filepath # 传入完整的输出WAV文件路径
    )

    websocket.enableTrace(False) # 生产环境中可以设置为 False
    wsUrl = ws_param_current_call.create_url() # 使用当前调用的 ws_param_current_call 来创建 URL
    
    # 创建WebSocketApp实例，并指定动态回调函数
    ws_app_instance = websocket.WebSocketApp(
        wsUrl,
        on_message=on_message_dynamic,
        on_error=on_error, # 可以继续使用全局的 on_error
        on_close=on_close # 可以继续使用全局的 on_close
    )
    
    # 将动态参数绑定到 ws_app_instance 上，以便在回调函数中访问
    ws_app_instance.ws_param = ws_param_current_call 
    ws_app_instance.on_open = on_open_dynamic # 指定动态 on_open

    # 运行WebSocket连接，直到完成
    ws_app_instance.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


if __name__ == "__main__":
    # 示例用法
    # 请确保 config/voice_config.py 存在，且 VOICE_CONFIG 字典中有 APP_ID, API_KEY, API_SECRET
    # 例如：
    # config/voice_config.py
    # VOICE_CONFIG = {
    #     'APP_ID': '你的APP_ID',
    #     'API_KEY': '你的API_KEY',
    #     'API_SECRET': '你的API_SECRET'
    # }

    # 创建一个用于测试的 question_audio 目录
    test_audio_dir = "./question_audio_test"
    if not os.path.exists(test_audio_dir):
        os.makedirs(test_audio_dir)
        logging.info(f"为测试创建目录: {test_audio_dir}")

    text_to_convert = "这是一个测试文本，用于生成语音文件。请仔细听。"
    output_file = os.path.join(test_audio_dir, "test_output.wav")
    
    logging.info(f"开始生成语音文件: {output_file}")
    run_tts(text_to_convert, output_file)
    logging.info("语音生成过程结束。")

    # 尝试生成第二个文件，检查并发性或后续调用是否正常
    text_to_convert_2 = "这是第二个测试文本，用于确认系统稳定性。"
    output_file_2 = os.path.join(test_audio_dir, "test_output_2.wav")
    logging.info(f"开始生成第二个语音文件: {output_file_2}")
    run_tts(text_to_convert_2, output_file_2)
    logging.info("第二个语音生成过程结束。")
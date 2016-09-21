# coding=utf-8
"""这个文件是参考云片网给出的python参考代码写的"""

import re
import httplib
import urllib
import random


# 服务地址
host = "yunpian.com"
# 端口号
port = 80
# 版本号
version = "v1"
# 通用短信接口的uri
sms_send_uri = "/" + version + "/sms/send.json"
# 短信内容模板
SMS_TEMPLATE = '您的验证码是%s【跑车范】'
SMS_KEY = "b2bc04ed9bbc52b10b3b68e5656eb08f"


def send_sms(code, mobile):
    """
    This utility function enables sending sms to the user given its phone number, api key
     and the message content.
     :param code authentication code
     :param mobile phone number
     :return True on success
    """
    text = SMS_TEMPLATE % code
    params = urllib.urlencode({'apikey': SMS_KEY, 'text': text, 'mobile': mobile})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = httplib.HTTPConnection(host, port=port, timeout=30)
    conn.request("POST", sms_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    status_code = int(re.match(r'\{"code":(-?\d+),.*', response_str).group(1))
    if status_code == 0:
        return True
    else:
        return False


def create_random_code():
    """ This utility function creates and returns a random code with length of 6
    """
    code = ''
    for _ in range(6):
        code += random.choice("1234567890")
    return code


# -*- coding:utf-8 -*-
import base64
import json
import random
from io import BytesIO

import requests
from PIL import Image

from .get_header import get_verification_code_header, get_login_header

account_list = [{"username": "papapa", "password": "12345678"}]  # 待填充


def get_verification_code():  # 获取验证码图片及其vid Get the CAPTCHA image and its VID
    validation_url = "https://pix.ipv4.host/verificationCode"
    fake_header = get_verification_code_header()
    response = requests.get(validation_url, headers=fake_header)
    json_validation = json.loads(response.text)
    image_base64 = str(json_validation['data']['imageBase64'])
    byte_data = base64.b64decode(image_base64)
    image_data = BytesIO(byte_data)
    im = Image.open(image_data)
    vid = json_validation['data']['vid']
    return im, vid


def get_token(vid: str, code: str) -> str:
    # 输入验证码模拟登陆获取token Enter the verification code to simulate login to obtain
    # the token
    login_url = "https://pix.ipv4.host/users/token" + "?vid=" + vid + "&value=" + code
    data = random.choice(account_list)
    data = json.dumps(data)
    fake_header = get_login_header()
    response = requests.post(login_url, data=data, headers=fake_header)
    if json.loads(response.text) == {"message": "验证码已过期或不存在"} \
            or json.loads(response.text) == {"message": "验证码错误"}:
        return ''
    token = response.headers['authorization']
    return token


if __name__ == '__main__':
    pass

# -*- coding:utf-8 -*-
import base64
import json
import random
from io import BytesIO

import requests

from pixivic.get_header import get_verification_code_header, get_login_header

ACCOUNTS = [{"username": "papapa", "password": "12345678"}]  # 待填充


def get_verification_code():
    """
    获取验证码图片及其vid(验证码标识)

    :return: 图片的缓存 以及 验证码vid标识
    """
    validation_url = "https://pix.ipv4.host/verificationCode"
    fake_header = get_verification_code_header()
    res_json = requests.get(validation_url, headers=fake_header).json()
    image_base64 = res_json['data']['imageBase64']
    byte_data = base64.b64decode(image_base64)
    im = BytesIO(byte_data)
    vid = res_json['data']['vid']
    return im, vid


def get_token(vid: str, code: str) -> str:
    """
    输入验证码模拟登陆获取 token

    :param vid: 验证码对应的标识
    :param code: 用户输入的验证码
    :return: token 的值 (jwt格式)
    """
    login_url = f"https://pix.ipv4.host/users/token?vid={vid}&value={code}"
    login_data = json.dumps(random.choice(ACCOUNTS))
    response = requests.post(login_url, data=login_data, headers=get_login_header())
    res_msg = response.json()["message"]
    if res_msg == "验证码已过期或不存在" or res_msg == "验证码错误":
        raise ValueError("验证码错误或验证码已过期或不存在")
    token = response.headers['authorization']
    return token


if __name__ == '__main__':
    pass

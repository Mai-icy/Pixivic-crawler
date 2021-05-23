# -*- coding:utf-8 -*-
import random

'''
返回header，已达到随机代理的header
Returns the header that has reached the random user agent
'''

user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15",
    ]


def get_simple_header() -> dict:
    return {
        'referer': 'https://sharemoe.top/',
        'User-Agent': random.choice(user_agent_list)
    }


def get_connect_header() -> dict:
    return {
        'referer': 'https://xm.sb/',
        'User-Agent': random.choice(user_agent_list)
    }


def get_verification_code_header() -> dict:
    return {
        'referer': 'https://sharemoe.top/',
        'User-Agent': random.choice(user_agent_list)
    }


def get_login_header() -> dict:
    return {
        'referer': 'https://xm.sb/',
        'Content-Type': 'application/json;charset=utf-8',
        'User-Agent': random.choice(user_agent_list)
    }


def get_download_header(img_id: str) -> dict:
    return {
        'referer': "https://sharemoe.net/illusts/" + img_id,
        'Content-Type': 'application/json;charset=utf-8',
        'User-Agent': random.choice(user_agent_list)
    }

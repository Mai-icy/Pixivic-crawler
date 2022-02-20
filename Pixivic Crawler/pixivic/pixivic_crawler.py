# -*- coding:utf-8 -*-
import base64
import json
import re
import time
from enum import Enum
from typing import List, Dict, AnyStr

import requests

from pixivic.get_header import get_connect_header, get_simple_header, get_download_header


def validation_token(token) -> bool:
    """
    验证token是否过期（jwt格式）
    """
    try:
        token_partition = re.split(r"\.", token)
        token_time = base64.b64decode(token_partition[1] + "=").decode()
        token_time_json = json.loads(token_time)
    except UnicodeDecodeError:
        raise ValueError("token格式有误")
    return time.time() < token_time_json["exp"]


def connect_test() -> bool:
    """
    测试能否连接到网站
    """
    connect_header = get_connect_header()
    response = requests.get('https://sharemoe.top/', headers=connect_header)
    return response.status_code == 200


class Mode(Enum):
    KEYWORD = 0
    DATE = 1
    ARTIST_ID = 2
    ILLUSTS_ID = 3


class PixCrawler(object):
    def __init__(self, token: str):
        self.token = token

    @property
    def token(self):
        if not self.__token:
            raise NotImplementedError("token的值还没有被设置")
        if not validation_token(self.__token):
            raise ValueError("token的值已经过期！")
        return self.__token

    @token.setter
    def token(self, value):
        self.__token = value

    def get_artist_info(self, art_id):
        """通过画作id获取作者信息"""
        fake_header = get_simple_header()
        fake_header['authorization'] = self.token
        url = f'https://pix.ipv4.host/illusts/{art_id}'
        res_json = requests.get(url, headers=fake_header).json()
        data_json = res_json.get("data")
        if data_json is None:
            return {}  # 画作不存在或为限制级图片
        return data_json["artistPreView"]

    def get_pic_suffix_url_list(self, data: str, num: int, mode: Mode, is_filter: bool) -> List[AnyStr]:
        """
        获取图片的链接后缀 例如 “2021/12/02/16/24/36/94515211_p0.png”， 提供给download函数

        :param data: 搜索的内容 可以为 日期 例如“2021-07-07” 可以为关键词，可以为 id
        :param num: 需求的图片数量
        :param mode: Mode枚举类中的类型
        :param is_filter: 是否过滤漫画（多p图片）
        :return: 包含网址后缀的列表
        """
        fake_header = get_simple_header()
        fake_header['authorization'] = self.token
        if mode == Mode.KEYWORD:
            return self._search_pic_url_list(data, num, is_filter)
        elif mode == Mode.DATE:
            url = f'https://pix.ipv4.host/ranks?page=1&date={data}&mode=day&pageSize=1000'
        elif mode == Mode.ARTIST_ID:
            url = f'https://pix.ipv4.host/artists/{data}/illusts/illust?page=1&pageSize=1000&maxSanityLevel=3'
        elif mode == Mode.ILLUSTS_ID:
            url = f'https://pix.ipv4.host/illusts/{data}'
        else:
            raise ValueError(f" 'mode' 参数应当为Mode枚举类的成员，而并不是{mode}")
        res_json = requests.get(url, headers=fake_header).json()
        data_json = res_json.get("data")
        if data_json is None:
            return []  # 画作不存在或为限制级图片
        if mode == Mode.ILLUSTS_ID:
            ori_pic_url_list = [data["original"] for data in data_json["imageUrls"]]
        elif is_filter:
            ori_pic_url_list = [data['imageUrls'][0]['original'] for data in data_json if len(data['imageUrls']) == 1]
        else:
            ori_pic_url_list = [data['imageUrls'][0]['original'] for data in data_json]
        return self._cut_suffix_url(ori_pic_url_list[:num])

    def get_recommend_keyword_list(self, keyword: str) -> List[Dict]:
        """
        返回推荐关键搜索词列表

        :param keyword: 关键词
        :return: 形如 [{"keyword":"初音ミク","keywordTranslated":"初音未来"}]
        """
        fake_header = get_simple_header()
        fake_header['authorization'] = self.token
        recommend_url = f"https://pix.ipv4.host/keywords/{keyword}/pixivSuggestions"
        res_json = requests.get(recommend_url, headers=fake_header, timeout=30).json()
        data = res_json.get('data')
        if not data:
            return []
        return data

    @staticmethod
    def _cut_suffix_url(ori_list) -> list:
        """获取列表中网址后缀，反向列表并返回"""
        res_pic_url_suffix_list = []
        for _ in range(len(ori_list)):  # 倒置列表以把优先度最高的放在列表尾部 以供下载使用高效的pop先获取优先度高的图片
            # 正则匹配对象为 2021/12/02/16/24/36/94515211_p0.png 以及特殊的 2021/12/02/16/10/54/94515035_ugoira0.jpg
            suffix = re.search(r"([0-9]+/){6}[0-9]+_.*[0-9].*", ori_list.pop())
            if suffix:
                res_pic_url_suffix_list.append(suffix.group(0))
        return res_pic_url_suffix_list

    def _search_pic_url_list(self, data, num, is_filter) -> list:
        """
        搜索模式限制了 pageSize 的大小要小于等于 30 ，
        :param 参数如 get_pic_url_list 函数
        :return:
        """
        fake_header = get_simple_header()
        fake_header['authorization'] = self.token
        page = 1
        repeat_num = 0  # 暂时不使用
        ori_url_list = []
        ori_url = 'https://pix.ipv4.host/illustrations?illustType=illust&searchType=original&maxSanityLevel=3&page={}' \
                  '&keyword={}&pageSize=30'
        while len(ori_url_list) < num and page <= 100:
            url = ori_url.format(page, data)
            res_json = requests.get(url, headers=fake_header).json()
            data_json = res_json.get("data")
            if data_json is None:
                break
            elif is_filter:
                page_pic_url_list = [data['imageUrls'][0]['original'] for data in data_json
                                     if len(data['imageUrls']) == 1]
            else:
                page_pic_url_list = [data['imageUrls'][0]['original'] for data in data_json]
            for pic_url in page_pic_url_list:
                if pic_url in ori_url_list:
                    repeat_num += 1
                else:
                    ori_url_list.append(pic_url)
            page += 1
        return self._cut_suffix_url(ori_url_list[:num])


def download_pic(url_suffix: str, download_path: str):
    """
    下载图片

    :param url_suffix: 图片网址的后缀 例：“2021/12/02/16/24/36/94515211_p0.png”
    :param download_path: 保存路径
    """
    img_url = f'https://o.i.edcms.pw/img-original/img/{url_suffix}'
    header = get_download_header()
    pic = requests.get(img_url, headers=header, timeout=5)  # 可能抛出 requests.exceptions.Timeout
    pic.raise_for_status()  # 可能抛出 requests.exceptions.HTTPError
    with open(download_path, 'wb') as file:
        file.write(pic.content)
    return True


if __name__ == '__main__':
    pix = PixCrawler(
        "eyJhbGciOiJIUzUxMiJ9.eyJwZXJtaXNzaW9uTGV2ZWwiOjEsInJlZnJlc2hDb3VudCI6MSwiaXNDaGVja1Bob25lIjowLCJ1c2VySWQiOjIwMzU3MSwiaWF0IjoxNjQ1MjY5NzIzLCJleHAiOjE2NDU2MTUzMjN9.HM4w-6Z27VrLR7jrhZZ50E9v4tOMO5CR_Trq-iL-O4JnDuMpVccrM0uvz1ge7R4CZXe5BCYNW2odEUoxI9bssw")
    tt = pix.get_pic_suffix_url_list("綾波レイ", 1000, Mode.KEYWORD, True)
    print(tt)
    print(len(tt))

# -*- coding:utf-8 -*-
import base64
import json
import re
import time

import requests

from .get_header import get_connect_header, get_simple_header, get_download_header


class PixCrawler(object):
    def __init__(self, token: str):
        if PixCrawler.validation_token(token):
            self.token = token
        else:
            raise Exception

    @staticmethod
    def validation_token(token):  # 验证token是否过期（token用的是jwt）Verify that the token is expired or not(JWT)
        token_partition = re.split('\.', token)
        token_time = base64.b64decode(token_partition[1] + "=").decode()
        token_time_json = json.loads(token_time)
        now_time = int(time.time())
        if now_time < int(token_time_json['exp']):
            return True
        else:
            return False

    @classmethod
    def connect_test(cls) -> bool:  # 测试网络连接是否正常 Test whether the network connection is normal
        connect_header = get_connect_header()
        response = requests.get('https://sharemoe.top/', headers=connect_header)
        if response.status_code == 200:
            return True
        else:
            return False

    def _get_page_img_url_list(self, page: int, keyword_or_date: str, mode: str, is_filter: bool) -> list:
        # 获取api返回对应页码的图片网址 return the corresponding page number of the image URL
        fake_header = get_simple_header()
        fake_header['authorization'] = self.token
        if mode == 'search':
            url = 'https://pix.ipv4.host/illustrations?illustType=illust&searchType=original&maxSanityLevel=3&page=%d' \
                  '&keyword=%s&pageSize=30' % (page, keyword_or_date)
        elif mode == 'daily':  # date示例 '2020-05-09'
            url = 'https://pix.ipv4.host/ranks?page=%d&date=%s&mode=day&pageSize=30' % (page, keyword_or_date)
        else:
            return []
        response = requests.get(url, headers=fake_header)
        json_res = json.loads(response.text)
        page_img_url_list = []
        if json_res == {'message': '搜索结果获取成功'}:  # 此处代表该对应页面没有图片
            return []
        for data in json_res['data']:
            if is_filter:
                img_data = data['imageUrls'][0]
                id_num = re.findall(r"[0-9]+/[0-9]+/[0-9]+/[0-9]+/[0-9]+/[0-9]+/[0-9]*_p[0-9]*.*", img_data['original'])
                if len(id_num) == 0:
                    pass
                else:
                    page_img_url_list.append(id_num[0])
            else:
                for img_data in data['imageUrls']:
                    id_num = re.findall(r"[0-9]+/[0-9]+/[0-9]+/[0-9]+/[0-9]+/[0-9]+/[0-9]*_p[0-9]*.*",
                                        img_data['original'])
                    page_img_url_list.append(id_num[0])
        return page_img_url_list

    def get_img_url_list(self, date_or_keyword: str, num: int, mode: str, is_filter: bool) -> list:
        # 获取对应模式对应数量的图片网址列表
        # Gets a list of image URLs corresponding to the corresponding num and corresponding pattern
        img_url_list = []
        page = 1  # 初始值
        page_data = self._get_page_img_url_list(page, date_or_keyword, mode, is_filter)
        while len(page_data) != 0 and len(img_url_list) < num:
            img_url_list.extend(page_data)
            page += 1
            page_data = self._get_page_img_url_list(page, date_or_keyword, mode, is_filter)
        if len(img_url_list) > num:
            img_url_list = img_url_list[:num]
        print(len(img_url_list))
        return img_url_list

    @classmethod
    def download_pic(cls, img_id: str, download_path: str):
        # 下载对应图片网址的图片 Download the pictures
        img_url = 'https://o.acgpic.net/img-original/img/' + img_id
        header = get_download_header(img_id)
        try:
            pic = requests.get(img_url, headers=header, timeout=(8, 30))
            f = open(download_path, 'wb')
            f.write(pic.content)
            f.close()
            return True
        except requests.exceptions.RequestException:
            return False

    def get_recommend_keyword_list(self, keyword: str) -> list:
        # 返回推荐关键搜索词列表 Returns a list of recommended key search terms
        fake_header = get_simple_header()
        fake_header['authorization'] = self.token
        recommend_url = "https://pix.ipv4.host/keywords/" + keyword + "/pixivSuggestions"
        response_keyword = requests.get(recommend_url, headers=fake_header, timeout=30)
        json_data = json.loads(response_keyword.text)
        if json_data == {'message': '搜索建议(来自Pixiv)获取成功'}:
            return []
        return json_data['data']


if __name__ == '__main__':
    pass

#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
from configparser import ConfigParser

INI_PATH = 'conf.ini'


def write_ini(
        threading_num: int,
        num: int,
        token: str,
        path: str,
        is_filter: bool):
    """
    This function is used to create and save new configuration files
    这个函数用来创建和保存新的配置文件
    """
    if os.path.exists(INI_PATH):
        os.remove(INI_PATH)
    conf = ConfigParser()
    conf.add_section("advance_set")
    conf.set("advance_set", "threading_num", str(threading_num))
    conf.set("advance_set", "num", str(num))
    conf.set("advance_set", "token", str(token))
    conf.set("advance_set", "path", str(path))
    # conf.set("advance_set", "is_recommend", str(is_recommend))
    conf.set("advance_set", "is_filter", str(is_filter))
    with open(INI_PATH, 'w') as fw:
        conf.write(fw)
    return True


def read_ini() -> dict:
    """
    This function reads the configuration file and returns an empty dict if the file does not exist
    这个函数用来读取配置文件，如果文件不存在，返回空的字典
    """
    if os.path.exists(INI_PATH):
        config = ConfigParser()
        config.read(INI_PATH)
        threads_num = int(config["advance_set"]['threading_num'])
        token = str(config["advance_set"]['token'])
        num = int(config["advance_set"]["num"])
        path = str(config["advance_set"]["path"])
        # is_recommend = bool(config["advance_set"]["is_recommend"])
        is_filter = bool(config["advance_set"]["is_filter"])
        res_dict = {
            'threads_num': threads_num,
            'token': token,
            'num': num,
            'path': path,
            'is_filter': is_filter}
        return res_dict
    else:
        return {}


if __name__ == '__main__':
    print(read_ini())

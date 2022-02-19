#!/usr/bin/python
# -*- coding:utf-8 -*-
from functools import wraps

TIP_TEXT = r"""
               |     |            ﹫|||||||||﹫
               |     |          ╭|||︵     ︵|||╮
               |     |          ╰|| ●      ● ||╯
               |     |             |╰╭╮-╭╮╯|
               |     |
               |     |
               |     |
        \      |     |      /
          \    |     |    /
            \  |     |  /
              \       /
                \   /
        """


def check_token_error(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except NotImplementedError:
            self.set_button_enable(False)
            self.get_token_button.setEnabled(True)
            self.msg_textEdit.appendPlainText("你还没有token！请获取！！\n" + TIP_TEXT)
        except ValueError:
            self.set_button_enable(False)
            self.get_token_button.setEnabled(True)
            self.msg_textEdit.appendPlainText("你的token过期了！请获取！！\n" + TIP_TEXT)
    return wrapper



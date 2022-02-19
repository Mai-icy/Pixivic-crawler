#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys

import requests
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PIL import Image, ImageQt

from ui.TokenDialog import Ui_token_Dialog
from components import WorkThread
import pixivic


class TokenDialog(QDialog, Ui_token_Dialog):
    def __init__(self, parent=None):
        super(TokenDialog, self).__init__(parent)
        self.setupUi(self)
        self._init_signal()
        self._init_setting()

    def _init_setting(self):
        """配置控件基本属性"""
        self.code_lineEdit.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9]{,4}")))
        self.code_pic_label.setScaledContents(True)
        self.set_button_enable(True)

    def _init_signal(self):
        """初始化信号连接"""
        self.refresh_button.clicked.connect(self._refresh_event)

    def _refresh_event(self):
        """刷新验证码事件"""
        self.refresh_thread = WorkThread(self._refresh_thread_work)
        self.set_button_enable(False)
        self.code_pic_label.setText("正在努力获取验证码w！")
        self.refresh_thread.start()

    def set_button_enable(self, flag):
        """设置按钮是否可用"""
        self.refresh_button.setEnabled(flag)
        self.buttonBox.setEnabled(flag)

    def accept_done_event(self):
        """登录线程运行之后验证是否获取成功"""
        if self.token:
            self.msg_label.setText("请输入验证码")
            self.parent().pix.token = self.token
            self.parent().msg_textEdit.clear()
            self.parent().msg_textEdit.appendPlainText(r"""成功获取token！
         　  ||||||||||||||||||||||
         ╭||||━━ 　　　━━||||╮
       ╰|||　　    　　 　　|||╯
        　||╰╭--╮ ︶╭--╮╯||
        　　 ╰/ / 　　\ ╯ 。""")
            self.parent().set_button_enable(True)
            self.parent().save_config()
            super(TokenDialog, self).accept()
        self.set_button_enable(True)

    def _refresh_thread_work(self):
        """线程的work函数"""
        try:
            self.code_lineEdit.clear()
            img_buffer, self.vid = pixivic.get_verification_code()
            self.code_pic_label.clear()
            pic_data = Image.open(img_buffer)
            q_image = ImageQt.toqpixmap(pic_data)
            self.code_pic_label.setPixmap(q_image)
            img_buffer.close()
        except requests.RequestException:
            self.code_pic_label.setText("网络连接超时，连接失败！Σ(っ °Д °;)っ")
        self.set_button_enable(True)

    def _login_thread_work(self, res_input) -> None:
        """线程的work函数"""
        self.token = ''
        try:
            token = pixivic.get_token(self.vid, res_input)
            self.token = token
        except requests.RequestException:
            self.msg_label.setText("无法登录，请检查网络X﹏X")
        except ValueError:
            self.msg_label.setText("验证码错误！┌(。Д。)┐")
            self._refresh_event()

    def accept(self) -> None:
        res_input = self.code_lineEdit.text()
        if not res_input:
            self.msg_label.setText("你还没有输入呢！ヽ(*。>Д<)o")
            return
        self.msg_label.setText("正在卖力登录获取token！")
        self.login_thread = WorkThread(self._login_thread_work, res_input)
        self.login_thread.start()
        self.set_button_enable(False)
        self.login_thread.done_signal.connect(self.accept_done_event)

    def show(self) -> None:
        self._refresh_event()
        self.parent().mask_widget.show()
        super(TokenDialog, self).show()

    def done(self, a0: int) -> None:
        self.parent().mask_widget.hide()
        super(TokenDialog, self).done(a0)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = TokenDialog()
    myWin.show()
    sys.exit(app.exec_())

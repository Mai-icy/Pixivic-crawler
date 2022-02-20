#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import re
import io
import sys
import time
import itertools

import requests.exceptions
from tqdm import tqdm
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, QRegExp
from PyQt5.QtCore import *

from components import MaskWidget, TokenDialog, WorkThread, check_token_error
from pixivic.pixivic_crawler import Mode
import pixivic
import config
import ui


LOCK = QMutex()


class MainUi(QWidget, ui.Ui_MainWidget):
    print_str = pyqtSignal(str)

    def __init__(self):
        super(MainUi, self).__init__()
        self.setupUi(self)
        self._init_base()
        self._init_controls()
        self._init_signal()
        self._init_config_file()

    # 初始化函数
    def _init_base(self):
        """初始化基本数据"""
        self.mask_widget = MaskWidget(self)
        self.token_dialog = TokenDialog(self)
        self.mask_widget.hide()

        self.result_data = {}
        self.mode = Mode.KEYWORD
        self.s_out = io.StringIO()
        self.img_suffix_url_list = []
        self.download_threads_list = []  # 利用列表引用保证线程内存不被释放

        self.pix = pixivic.PixCrawler('')

    def _init_controls(self):
        """设置控件内默认值以及部分控件设置"""
        self.date_time_timeEdit.setDisplayFormat("yyyy年MM月dd日")
        self.date_time_timeEdit.setMaximumDate(QDate.currentDate().addDays(-2))
        self.date_time_timeEdit.setMinimumDate(QDate.currentDate().addDays(-365))
        self.date_time_timeEdit.setDateTime(QDateTime(QDate.currentDate().addDays(-2), QTime(0, 0, 0)))

        self.id_of_art_lineEdit.setValidator(QRegExpValidator(QRegExp("[0-9]+")))

        self.is_save_config_checkBox.setChecked(True)
        self.is_filter_checkBox.setChecked(True)

        self.mode_tabWidget.setCurrentIndex(0)

        self.num_spinBox.setValue(300)
        self.thread_spinBox.setValue(4)

    def _init_signal(self):
        """初始化信号连接"""
        self.save_as_button.clicked.connect(self.save_as_event)
        self.start_button.clicked.connect(self.start_button_event)
        self.recommend_button.clicked.connect(self.recommend_event)
        self.get_token_button.clicked.connect(lambda: self.token_dialog.show())

        self.recommend_comboBox.currentIndexChanged.connect(
            lambda: self.keyword_lineEdit.setText(self.recommend_comboBox.currentText()))
        self.mode_tabWidget.currentChanged.connect(self._tab_mode_changed_event)
        self.id_mode_comboBox.currentIndexChanged.connect(self._tab_mode_changed_event)

        self.print_str.connect(self._print_str_event)

    @check_token_error
    def _init_config_file(self):
        """读取配置文件的数据"""
        config_dict = config.read_ini()
        if not config_dict:
            self.save_config()
            return
        try:
            self.num_spinBox.setValue(config_dict["num"])
            self.path_lineEdit.setText(config_dict["path"])
            self.is_filter_checkBox.setChecked(config_dict["is_filter"])
            self.thread_spinBox.setValue(config_dict["threads_num"])
            self.pix.token = config_dict["token"]
            _ = self.pix.token
        except ValueError:  # 配置文件内的值被用户胡乱篡改
            self.save_config()
            return

    # 辅助函数
    def _print_str_event(self, _str):
        """
        线程发出的 appendPlainText 函数请求不能被刷新，需要主线程的信号辅助
        """
        print(_str)
        self.msg_textEdit.appendPlainText(_str)

    def _tab_mode_changed_event(self):
        """捕捉模式选择，设置模式数据到成员变量"""
        index = self.mode_tabWidget.currentIndex()
        if index == 2:
            index = 2 + self.id_mode_comboBox.currentIndex()
        self.mode = Mode(index)
        print(f"选择了模式{self.mode}")

    def set_button_enable(self, flag):
        """
        设置用户是否能操控

        :param flag: 关闭或开启控件使用
        """
        self.start_button.setEnabled(flag)
        self.save_as_button.setEnabled(flag)
        self.get_token_button.setEnabled(flag)
        self.recommend_button.setEnabled(flag)
        self.mode_tabWidget.setEnabled(flag)
        self.keyword_lineEdit.setEnabled(flag)
        self.id_of_art_lineEdit.setEnabled(flag)
        self.num_spinBox.setEnabled(flag)
        self.thread_spinBox.setEnabled(flag)
        self.is_filter_checkBox.setEnabled(flag)
        self.is_save_config_checkBox.setEnabled(flag)

    def save_config(self):
        """保存配置文件"""
        num = self.num_spinBox.value()
        path = self.path_lineEdit.text()
        threading_num = self.thread_spinBox.value()
        is_filter = self.is_filter_checkBox.isChecked()
        config.write_ini(threading_num, num, self.pix.token, path, is_filter)
        self.msg_textEdit.appendPlainText("已生成并保存配置文件")

    # 用户事件函数
    def save_as_event(self):
        """选择保存目录事件"""
        download_path = QFileDialog.getExistingDirectory(self, "选取文件夹", "./")
        self.path_lineEdit.setText(download_path)
        if download_path:
            self.msg_textEdit.appendPlainText(f"你选择了保存路径\n{download_path}")
            self.save_config()

    def recommend_event(self):
        """获取推荐关键词"""
        ori_keyword = self.keyword_lineEdit.text()
        if not ori_keyword:
            return
        self.recommend_thread = WorkThread(self._recommend_thread)
        self.recommend_thread.start()

    def start_button_event(self):
        """开始按钮，开始事件"""
        if self.mode == Mode.KEYWORD:
            keyword = self.keyword_lineEdit.text()
            if not keyword:
                self.msg_textEdit.appendPlainText("关键词还没选哪！！（′Д`）")
                return
        elif self.mode == Mode.ILLUSTS_ID or self.mode == Mode.ARTIST_ID:
            _id = self.id_of_art_lineEdit.text()
            if not _id:
                self.msg_textEdit.appendPlainText("ID还没写哪！！（′Д`）")
                return
        path = self.path_lineEdit.text()
        if not path:
            self.msg_textEdit.appendPlainText("路径还没选哪！！（′Д`）")
            return

        self.msg_textEdit.clear()  # 交给主线程清空，否则未响应
        self.get_url_thread = WorkThread(self._get_url_thread)
        self.start_main_thread = WorkThread(self._start_main_thread)
        self.get_url_thread.start()
        self.start_main_thread.start()

    # 线程相关函数
    def _start_main_thread(self):
        """掌管下载和获取数据的副线程"""
        for char in itertools.cycle('|/—\\'):
            if self.get_url_thread.isFinished():
                time.sleep(0.7)
                break
            time.sleep(0.7)
            self.msg_textEdit.clear()
            self.print_str.emit("正在搜索您所需要的图片，请稍等..." + char)
        if not self.img_suffix_url_list:
            self.print_str.emit("很努力为您搜索了，但画作不存在或为限制级图片(。﹏。*)")
            self.set_button_enable(True)
            return
        elif self.img_suffix_url_list[0] == 'requests-error':
            self.print_str.emit("网络异常，获取失败")
            self.set_button_enable(True)
            return
        total_num = len(self.img_suffix_url_list)
        if self.mode == Mode.KEYWORD:
            data = self.keyword_lineEdit.text()
            inline_text = f"搜索模式关键词为 {data}"
        elif self.mode == Mode.DATE:
            data = self.date_time_timeEdit.date().toString(Qt.ISODate)
            inline_text = f"日期排行榜模式日期为 {data}"
        elif self.mode == Mode.ILLUSTS_ID:
            self.print_str.emit(self.artist_data_text)
            self.artist_data_text = ''
            data = self.id_of_art_lineEdit.text()
            inline_text = f"作品id模式id为 {data}"
        else:  # self.mode == Mode.ARTIST_ID:
            data = self.id_of_art_lineEdit.text()
            inline_text = f"画师id模式id为 {data}"
        print_text = f"您的请求为{inline_text}经过筛选共{total_num}张\n正在准备为您下载(*/ω＼*)"
        self.print_str.emit(print_text)
        self.s_out = io.StringIO()
        # 进度条美化 https://blog.csdn.net/weixin_32597695/article/details/112201800
        self.progress_bar = tqdm(range(total_num), file=self.s_out)
        self.progress_iter = iter(self.progress_bar)
        next(self.progress_iter)  # 预激迭代器
        folder_name = re.sub(r"|[\\/:*?\"<>| ]+", "", f"{data},{total_num}张")
        folder_path = os.path.join(self.path_lineEdit.text(), folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self.result_data = {
            "total": total_num,
            "404": 0,
            "success": 0
        }
        self.download_threads_list.clear()
        for _ in range(self.thread_spinBox.value()):
            download_thread = WorkThread(self._download_thread, folder_path, total_num)
            download_thread.thread_all_done_signal.connect(self.download_all_done_event)
            download_thread.start()
            self.download_threads_list.append(download_thread)

    @check_token_error
    def _get_url_thread(self):
        """搜索目标图片线程，生产者"""
        self.set_button_enable(False)
        self.img_suffix_url_list.clear()
        if self.mode == Mode.KEYWORD:
            data = self.keyword_lineEdit.text()
        elif self.mode == Mode.DATE:
            data = self.date_time_timeEdit.date().toString(Qt.ISODate)
        elif self.mode == Mode.ARTIST_ID:
            data = self.id_of_art_lineEdit.text()
        else:  # self.mode == Mode.ILLUSTS_ID
            data = self.id_of_art_lineEdit.text()
            artist_info = self.pix.get_artist_info(data)
            if artist_info:
                self.artist_data_text = f"已获取画师信息\nid:{artist_info['id']}\nname:{artist_info['name']}"
            else:
                self.artist_data_text = "画师搜索失败，可能为限制级{>~<}"
        num = self.num_spinBox.value()
        is_filter = self.is_filter_checkBox.isChecked()
        try:
            self.img_suffix_url_list = self.pix.get_pic_suffix_url_list(data, num, self.mode, is_filter)
        except requests.RequestException:
            self.img_suffix_url_list.clear()
            self.img_suffix_url_list.append("requests-error")  # 传递错误信号给start_main线程（我知道这不合理呜）

    @check_token_error
    def _recommend_thread(self):
        """获取推荐关键词的线程"""
        try:
            self.recommend_button.setEnabled(False)
            self.keyword_lineEdit.setEnabled(False)
            ori_keyword = self.keyword_lineEdit.text()
            res = self.pix.get_recommend_keyword_list(ori_keyword)
            self.recommend_comboBox.clear()
            for data in res:
                text = data['keyword']
                self.recommend_comboBox.addItem(text)
            self.print_str.emit("获取成功，请点击左侧下拉框选择！")
        except requests.RequestException:
            self.recommend_comboBox.clear()
            self.print_str.emit("网络异常，获取失败")
        finally:
            self.recommend_button.setEnabled(True)
            self.keyword_lineEdit.setEnabled(True)

    def _download_thread(self, path, total_num):
        """负责下载的线程，工作者"""
        running = True
        while running:
            LOCK.lock()
            if not self.img_suffix_url_list:
                LOCK.unlock()
                break
            img_suffix_url = self.img_suffix_url_list.pop()
            order = total_num - len(self.img_suffix_url_list)
            LOCK.unlock()
            file_name = f"{order}.{img_suffix_url[20:]}"
            des_text = "未知错误"
            for _ in range(3):
                try:
                    pixivic.pixivic_crawler.download_pic(img_suffix_url, os.path.join(path, file_name))
                    des_text = "成功"
                    self.result_data["success"] += 1
                    break
                except requests.exceptions.HTTPError:
                    des_text = "404"
                    self.result_data["404"] += 1
                    break
                except requests.exceptions.Timeout:
                    des_text = "超时"
                except requests.RequestException:
                    des_text = "超时"
            LOCK.lock()
            self.progress_bar.set_description(des_text)
            try:
                next(self.progress_iter)
                self.print_str.emit(self.s_out.getvalue().split('\r')[-1])
                time.sleep(.3)
            except StopIteration:
                running = False
            finally:
                LOCK.unlock()

    def download_all_done_event(self):
        """多线程下载（工作者）下载完毕，连接到结束函数"""
        text = self.s_out.getvalue().split('\r')[-1]
        text += "\n下载完成！ヽ(✿ﾟ▽ﾟ)ノ\n"
        timeout_num = self.result_data['total'] - self.result_data['success'] - self.result_data['404']
        text += f"本次下载的结果，共计{self.result_data['total']}张, 成功{self.result_data['success']}张, " \
                f"404共{self.result_data['404']}张，超时下载共{timeout_num}张。"
        self.print_str.emit(text)
        if self.is_save_config_checkBox.isChecked():
            self.save_config()
        self.set_button_enable(True)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MainUi()
    myWin.show()
    sys.exit(app.exec_())

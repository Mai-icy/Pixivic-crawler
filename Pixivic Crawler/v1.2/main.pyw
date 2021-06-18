#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import re
import sys
import threading

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QFileDialog

import config
import pixivic
import ui


class WorkThread(QThread):  # 定义QThread的子类线程 Define subclass threads of QThread
    signal = pyqtSignal(str)

    def __int__(self):
        super(WorkThread, self).__init__()

    def run(self):
        MainUi.thread_download_pic()
        self.signal.emit('结束')


class MainUi(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainUi, self).__init__()
        # 定义子窗口 Define child window
        self.child_window = QtWidgets.QWidget()
        self.cu = ChildUi()
        self.cu.setup_ui(self.child_window)

        self.ui_controls = ui.UiPixivicCrawler()
        self.lock = threading.RLock()
        # 初始化数值 Initialization value
        self.img_url_list = []
        self.keyword_list = []
        self.mode = ''
        self.res_num = 0
        self.filed_num = 0
        self.success_num = 0
        self.running_thread_num = 0
        self.completed_done_num = 0
        self.folder_name = ''

        self.token = ''

    def setup_ui(self, main_window):  # 按键连接函数 Keys connect event functions
        self.ui_controls.setupUi(main_window)
        self.ui_controls.start_button.clicked.connect(self.start_button_event)
        self.ui_controls.sure_keyword.clicked.connect(self.sure_keyword_event)
        self.ui_controls.save_as.clicked.connect(self.save_as_event)
        self.ui_controls.get_token_button.clicked.connect(self.get_token_button_event)
        self.ui_controls.date_sure.clicked.connect(self.date_sure_event)
        self.ui_controls.id_sure.clicked.connect(self.id_sure_event)

        self.ui_controls.actionSave_setting.triggered.connect(self.save_setting_event)
        self.ui_controls.exit.triggered.connect(main_window.close)
        self.ui_controls.help.triggered.connect(self.help_event)

        self.load_config()

    def start_button_event(self):  # 搜索模式下的开始按钮 Start button in search mode
        path = self.ui_controls.path_box.text()
        keyword = self.ui_controls.keyword.text()
        num = int(self.ui_controls.num_box.text())
        thread_num = int(self.ui_controls.threads_num_box.text())
        is_filter = self.ui_controls.is_filter.isChecked()
        self.mode = 'search'
        self.folder_name = '%s %d张' % (keyword, num)
        if all([path, keyword]):
            self.ui_controls.printbox.appendPlainText('正在获取图片列表，过程中可能会导致ui短暂未响应，请等待。')
            self.disable(True)
            self.img_url_list = self.pixivic_crawler.get_img_url_list(keyword, num, 'search', is_filter)
            self.res_num = len(self.img_url_list)
            if self.res_num == 0:
                self.disable(False)
                # self.ui_controls.start_button.isEnabled(False)
                self.ui_controls.printbox.appendPlainText('网络请求超时或者该关键词被屏蔽，请重试。')
            else:
                self.ui_controls.printbox.appendPlainText('成功获取图片列表,共%d张' % self.res_num)
                self.ui_controls.printbox.appendPlainText('正在准备图片下载www')
                path = self.ui_controls.path_box.text() + '\\' + self.folder_name
                if not os.path.exists(path):
                    os.makedirs(path)
                self.thread_start(thread_num)

    def sure_keyword_event(self):  # 确定关键词按钮 Sure keyword button
        if self.ui_controls.keyword.text():
            keyword = self.ui_controls.keyword.text()
            if self.ui_controls.is_recommend.isChecked():
                self.keyword_list = self.pixivic_crawler.get_recommend_keyword_list(keyword)
                self.ui_controls.keyword_list.clear()
                if len(self.keyword_list) == 0:
                    # 网站返回的推荐关键词为空 The recommended keywords returned by the site are empty
                    self.ui_controls.printbox.clear()
                    self.ui_controls.printbox.appendPlainText('该关键词没有推荐搜索词，可能被网站屏蔽')
                else:
                    for keyword_index, keyword_data in enumerate(self.keyword_list, start=1):
                        item_text = '%d.%s (翻译:%s)' % \
                                    (keyword_index, keyword_data['keyword'], keyword_data['keywordTranslated'])
                        self.ui_controls.keyword_list.addItem(item_text)
                    self.ui_controls.printbox.clear()
                    self.ui_controls.printbox.appendPlainText('请在栏中选择并再次确定')
                    self.ui_controls.is_recommend.setChecked(False)
            elif self.ui_controls.keyword_list.count() != 0:
                # 输入关键词使用推荐 Enter keywords with using recommendations
                keyword_index = self.ui_controls.keyword_list.currentIndex()
                keyword = self.keyword_list[keyword_index]['keyword']
                self.ui_controls.keyword.setText(keyword)
                self.ui_controls.printbox.clear()
                self.ui_controls.printbox.appendPlainText('请按开始以开始下载')
                self.ui_controls.start_button.setEnabled(True)
                # 确定了搜索词，开放运行按钮 Determine the search term, open the run button
            else:  # Enter keywords without using recommendations
                self.ui_controls.printbox.clear()
                self.ui_controls.printbox.appendPlainText('请按开始以开始下载')
                self.ui_controls.start_button.setEnabled(True)
                # 确定了搜索词，开放运行按钮 Determine the search term, open the run button
        else:  # 没输入关键词 No keywords entered
            self.ui_controls.printbox.appendPlainText('请输入关键词')

    def save_as_event(self):
        # Get the save path
        download_path = QFileDialog.getExistingDirectory(self, "选取文件夹", "./")
        self.ui_controls.path_box.setText(download_path)

    def get_token_button_event(self):
        # 调用子窗口 Call the child window to recognize the CAPTCHA
        self.child_window.show()
        self.cu.refresh_captcha()

    def date_sure_event(self):
        self.mode = 'daily'
        date = self.ui_controls.date_time.date().toString(Qt.ISODate)
        num = int(self.ui_controls.num_box.text())
        thread_num = int(self.ui_controls.threads_num_box.text())
        is_filter = self.ui_controls.is_filter.isChecked()
        path = self.ui_controls.path_box.text()
        self.folder_name = '%s %d张' % (date, num)
        if all([date, num, thread_num, path]):
            self.disable(True)
            self.img_url_list = self.pixivic_crawler.get_img_url_list(date, num, self.mode, is_filter)
            self.res_num = len(self.img_url_list)
            if self.res_num == 0:
                self.disable(False)
                # self.ui_controls.start_button.isEnabled(False)
                self.ui_controls.printbox.appendPlainText('网络请求超时或者该关键词被屏蔽，请重试。')
            else:
                self.ui_controls.printbox.appendPlainText('成功获取图片列表,共%d张' % self.res_num)
                self.ui_controls.printbox.appendPlainText('正在准备图片下载www')
                path = self.ui_controls.path_box.text() + '\\' + self.folder_name
                if not os.path.exists(path):
                    os.makedirs(path)
                    self.thread_start(thread_num)

    def id_sure_event(self):  # mode3
        path = self.ui_controls.path_box.text()
        thread_num = int(self.ui_controls.threads_num_box.text())
        if self.ui_controls.id_mode.currentIndex() == 0:
            mode = 'artistId'
        else:  # self.ui_controls.id_mode.currentIndex() == 1
            mode = 'illustsId'

        art_id = self.ui_controls.id_of_art.text()
        self.folder_name = art_id
        if all([path, art_id]):
            if mode == 'illustsId':
                self.mode = 'art_id'
                res = self.pixivic_crawler.get_art_id_url_list(art_id, mode)
                if len(res) == 0:
                    self.ui_controls.printbox.appendPlainText('网络请求超时或者该作品或被屏蔽，请重试。')
                else:
                    self.img_url_list = res[1:]
                    artist_data = res[0]
                    self.res_num = len(self.img_url_list)

                    self.disable(True)
                    self.ui_controls.printbox.appendPlainText('画师信息如下')
                    self.ui_controls.printbox.appendPlainText('名字：' + artist_data['name'])
                    self.ui_controls.printbox.appendPlainText('id:' + str(artist_data['id']))

                    self.ui_controls.printbox.appendPlainText('成功获取图片列表,共%d张' % self.res_num)
                    self.ui_controls.printbox.appendPlainText('正在准备图片下载www')
                    path = self.ui_controls.path_box.text() + '\\' + self.folder_name
                    if not os.path.exists(path):
                        os.makedirs(path)
                    if self.res_num >= 4:
                        self.thread_start(thread_num)
                    else:
                        self.thread_start(1)
            if mode == 'artistId':
                self.mode = 'art_id'
                self.img_url_list = self.pixivic_crawler.get_art_id_url_list(art_id, mode)
                self.res_num = len(self.img_url_list)
                if self.res_num == 0:
                    self.ui_controls.printbox.appendPlainText('网络请求超时或者该作者无作品或被屏蔽，请重试。')
                else:
                    self.disable(True)
                    self.ui_controls.printbox.appendPlainText('成功获取图片列表,共%d张' % self.res_num)
                    self.ui_controls.printbox.appendPlainText('正在准备图片下载www')
                    path = self.ui_controls.path_box.text() + '\\' + self.folder_name
                    if not os.path.exists(path):
                        os.makedirs(path)
                    self.thread_start(thread_num)

    def thread_start(self, thread_num: int):
        # 给线程分配内存 Allocates memory to threads
        if thread_num >= 1:
            self.t1 = WorkThread()
            self.t1.start()
            self.t1.signal.connect(self._thread_download_done)
            self.running_thread_num += 1

        if thread_num >= 2:
            self.t2 = WorkThread()
            self.t2.start()
            self.t2.signal.connect(self._thread_download_done)
            self.running_thread_num += 1

        if thread_num >= 3:
            self.t3 = WorkThread()
            self.t3.start()
            self.t3.signal.connect(self._thread_download_done)
            self.running_thread_num += 1

        if thread_num >= 4:
            self.t4 = WorkThread()
            self.t4.start()
            self.t4.signal.connect(self._thread_download_done)
            self.running_thread_num += 1

    def save_setting_event(self):
        thread_num = self.ui_controls.threads_num_box.text()
        num = self.ui_controls.num_box.text()
        is_recommend = self.ui_controls.is_recommend.isChecked()
        is_filter = self.ui_controls.is_filter.isChecked()
        path = self.ui_controls.path_box.text()
        if all([thread_num, num, str(is_recommend), str(is_filter), path, self.token]):
            config.configuration_ini(thread_num, num, self.token, path, is_recommend, is_filter)
            self.ui_controls.printbox.appendPlainText('成功保存设置')
            self.ui_controls.sure_keyword.setEnabled(True)
            self.ui_controls.date_sure.setEnabled(True)
        else:
            self.ui_controls.printbox.appendPlainText('保存的参数不完整，请检查路径和token是否获取')

    def help_event(self):
        self.ui_controls.printbox.appendPlainText('该功能将在之后开启')
        #

    def thread_download_pic(self):
        # 用于下载图片的线程 The thread used to download the image
        path = self.ui_controls.path_box.text() + '\\' + self.folder_name
        while len(self.img_url_list) != 0:
            self.lock.acquire()
            try:
                img_id = self.img_url_list.pop(0)
                self.completed_done_num += 1
                pic_num = self.completed_done_num
                pic_name = re.findall(r"[0-9]+/([0-9]*_p[0-9]*.*)", img_id)[0]
                pic_path = path + '\\%d.%s' % (pic_num, pic_name)
            finally:
                self.lock.release()
            if pixivic.PixCrawler.download_pic(img_id, pic_path):
                self.lock.acquire()
                try:
                    self.success_num += 1
                    self.ui_controls.printbox.appendPlainText('图片下载中(%d/%d)'
                                                              % (self.success_num + self.filed_num, self.res_num))
                finally:
                    self.lock.release()
            elif pixivic.PixCrawler.download_pic(img_id, pic_path):
                self.lock.acquire()
                try:
                    self.success_num += 1
                    self.ui_controls.printbox.appendPlainText('图片下载中(%d/%d)'
                                                              % (self.success_num + self.filed_num, self.res_num))
                finally:
                    self.lock.release()
            else:
                self.lock.acquire()
                try:
                    self.filed_num += 1
                    self.ui_controls.printbox.appendPlainText('图片下载失败(%d/%d)'
                                                              % (self.success_num + self.filed_num, self.res_num))
                finally:
                    self.lock.release()

    def _thread_download_done(self):
        # 线程下载完毕后的后续操作 The subsequent action after the thread has been downloaded
        self.running_thread_num -= 1
        if self.running_thread_num == 0:
            if self.mode == 'search':
                num = int(self.ui_controls.num_box.text())
                keyword = self.ui_controls.keyword.text()
                self.ui_controls.printbox.appendPlainText('下载完毕，本次请求下载共%d张，关键词是%s,成功%d张,失败%d张。'
                                                          % (num, keyword, self.success_num, self.filed_num))
                self.ui_controls.printbox.appendPlainText('部分无法打开的图片被网站屏蔽，请忽略')
                if self.ui_controls.is_save:
                    self.save_setting_event()
            if self.mode == 'daily':
                num = int(self.ui_controls.num_box.text())
                self.ui_controls.printbox.appendPlainText('下载完毕，本次请求下载共%d张,成功%d张,失败%d张。'
                                                          % (num, self.success_num, self.filed_num))
                self.ui_controls.printbox.appendPlainText('部分无法打开的图片被网站屏蔽，请忽略')
                if self.ui_controls.is_save:
                    self.save_setting_event()
            if self.mode == 'art_id':
                num = int(self.ui_controls.num_box.text())
                self.ui_controls.printbox.appendPlainText('下载完毕，本次请求下载共%d张,成功%d张,失败%d张。'
                                                          % (num, self.success_num, self.filed_num))
                self.ui_controls.printbox.appendPlainText('部分无法打开的图片被网站屏蔽，请忽略')
                if self.ui_controls.is_save:
                    self.save_setting_event()
            # 初始化
            self.img_url_list = []
            self.keyword_list = []
            self.mode = ''
            self.res_num = 0
            self.filed_num = 0
            self.success_num = 0
            self.running_thread_num = 0
            self.completed_done_num = 0
            self.folder_name = ''
            self.disable(False)
            # self.ui_controls.start_button.isEnabled(False)

    @staticmethod
    def filter_folder_name(string: str) -> str:  # 排除文件夹命名特殊字符 Exclude folder naming special characters
        string = eval(repr(string).replace('/', '').replace('*', ''))
        string = eval(repr(string).replace('<', '').replace('>', ''))
        string = eval(repr(string).replace('|', '').replace('?', ''))
        string = eval(repr(string).replace(':', '').replace('"', ''))
        return string

    def disable(self, mode: bool):
        # 使主程序运行时，不允许用户按下按键操作 Do not allow the user to press a key while the main program is running
        self.ui_controls.keyword.setReadOnly(mode)
        self.ui_controls.num_box.setReadOnly(mode)
        self.ui_controls.threads_num_box.setReadOnly(mode)

        self.ui_controls.save_as.setEnabled(not mode)
        self.ui_controls.start_button.setEnabled(not mode)
        self.ui_controls.sure_keyword.setEnabled(not mode)
        self.ui_controls.date_sure.setEnabled(not mode)
        self.ui_controls.is_recommend.setCheckable(not mode)
        self.ui_controls.id_sure.setEnabled(not mode)

    def load_config(self):
        # 载入配置文件 Loading configuration files
        config_dict = config.read_ini()
        if config_dict == {}:
            self.ui_controls.printbox.appendPlainText('配置文件丢失,无法载入配置文件')
            self.ui_controls.printbox.appendPlainText('请重新获取token')
            self.ui_controls.sure_keyword.setEnabled(False)
            self.ui_controls.date_sure.setEnabled(False)

        else:
            self.ui_controls.is_filter.setChecked(config_dict['is_filter'])
            self.ui_controls.is_recommend.setChecked(config_dict['is_recommend'])
            self.ui_controls.num_box.setValue(config_dict['num'])
            self.ui_controls.threads_num_box.setValue(config_dict['threads_num'])
            self.ui_controls.path_box.setText(config_dict['path'])
            try:
                self.pixivic_crawler = pixivic.PixCrawler(config_dict['token'])
                self.token = config_dict['token']

            except Exception:
                self.ui_controls.printbox.appendPlainText('token过期，请按获取token以更新token')

                self.ui_controls.sure_keyword.setEnabled(False)
                self.ui_controls.date_sure.setEnabled(False)


class ChildUi(QtWidgets.QWidget):
    def __init__(self):
        super(ChildUi, self).__init__()
        self.ui_controls = ui.UiGetToken()
        self.vid = ''
        self.img = ''
        self.token = ''

    def setup_ui(self, child_window):
        self.ui_controls.setupUi(child_window)
        self.ui_controls.buttonBox.accepted.connect(self.sure)
        self.ui_controls.buttonBox.rejected.connect(child_window.close)
        self.ui_controls.pushButton.clicked.connect(self.refresh_captcha)

    def refresh_captcha(self):  # 刷新验证码 Refresh verification code
        self.img, self.vid = pixivic.get_verification_code()
        pix = self.img.toqpixmap()
        self.ui_controls.pic.setScaledContents(True)  # 自适应QLabel大小
        self.ui_controls.pic.setPixmap(pix)
        self.ui_controls.pic_value_box.clear()

    def sure(self):
        captcha = self.ui_controls.pic_value_box.text()
        self.token = pixivic.get_token(self.vid, captcha)
        if self.token:
            MainUi.child_window.close()
            MainUi.token = self.token
            MainUi.pixivic_crawler = pixivic.PixCrawler(self.token)
            MainUi.ui_controls.printbox.appendPlainText('成功获取token')
            MainUi.save_setting_event()
        else:
            self.ui_controls.label.setText('验证码过期或输入错误')
            self.refresh_captcha()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    form = QtWidgets.QMainWindow()
    MainUi = MainUi()
    MainUi.setup_ui(form)
    form.show()
    sys.exit(app.exec_())

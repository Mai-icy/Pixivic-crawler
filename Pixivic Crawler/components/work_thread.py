#!/usr/bin/python
# -*- coding:utf-8 -*-
from PyQt5.QtCore import QThread, pyqtSignal
from functools import partial


class WorkThread(QThread):
    thread_all_done_signal = pyqtSignal(object)
    done_signal = pyqtSignal(object)
    _running_num = 0

    def __init__(self, work_func, *args, **kwargs):
        super(WorkThread, self).__init__()
        self.work = partial(work_func, *args, **kwargs)

    def work(self):
        raise NotImplementedError("The 'work' function has not been set")

    def run(self):
        try:
            self.__class__._running_num += 1
            self.work()
        finally:
            self.__class__._running_num -= 1
            self.done_signal.emit('')

        if self.__class__._running_num == 0:
            self.thread_all_done_signal.emit('')

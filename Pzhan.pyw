#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Pzhan import log
from Pzhan.core import Pzhan
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time
import sys
import os
import logging


class MainWindow(QMainWindow):
    def __init__(self, pzhan, parent=None):
        super(MainWindow, self).__init__(parent)

        self.pz = pzhan

        pid_lb = QLabel("Pzhan ID:")
        psw_lb = QLabel("Password:")
        self.pid_le = QLineEdit()
        self.psw_le = QLineEdit()
        self.psw_le.setEchoMode(QLineEdit.Password)
        self.is_login = QLabel("Not login")
        self.login_btn = QPushButton("Login")
        self.remem_psw = QCheckBox('Remember Password')
        self.remem_psw.setChecked(True)

        self.save_path_le = QLineEdit("")
        self.save_path_btn = QPushButton("Set save path")

        lb_c = QVBoxLayout()
        le_c = QVBoxLayout()
        stu_c = QVBoxLayout()
        lb_c.addWidget(pid_lb)
        lb_c.addWidget(psw_lb)
        le_c.addWidget(self.pid_le)
        le_c.addWidget(self.psw_le)
        stu_c.addWidget(self.is_login)
        stu_c.addWidget(self.login_btn)

        self.work_list = QListWidget()
        self.work_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.work_list.setSelectionMode(QAbstractItemView.ContiguousSelection)

        self.new_work = QLineEdit()
        self.add_work_btn = QPushButton("Add")

        self.start_work_btn = QPushButton("Start Getting")
        self.delete_work_btn = QPushButton("Delete selected")

        self.console = QTextBrowser()

        self.msg_tst = QLabel()

        login_row = QHBoxLayout()
        login_row.addLayout(lb_c)
        login_row.addLayout(le_c)
        login_row.addWidget(self.remem_psw)
        login_row.addStretch(1)
        login_row.addLayout(stu_c)

        save_path_row = QHBoxLayout()
        save_path_row.addWidget(self.save_path_le)
        save_path_row.addWidget(self.save_path_btn)

        add_work_row = QHBoxLayout()
        add_work_row.addWidget(self.new_work)
        add_work_row.addWidget(self.add_work_btn)

        start_row = QHBoxLayout()
        start_row.addStretch(1)
        start_row.addWidget(self.start_work_btn)
        start_row.addStretch(1)
        start_row.addWidget(self.delete_work_btn)
        start_row.addStretch(1)

        v_box = QVBoxLayout()
        v_box.addLayout(login_row)
        v_box.addLayout(save_path_row)
        v_box.addWidget(self.work_list)
        v_box.addLayout(add_work_row)
        v_box.addLayout(start_row)
        v_box.addWidget(self.console)
        v_box.addWidget(self.msg_tst)

        # self.setLayout(v_box)
        self.resize(QSize(600, 650))
        self.setWindowTitle("Pzhan")

        # self.setWindowFlags(Qt.WindowCloseButtonHint)
        widget = QWidget(self)
        widget.setLayout(v_box)
        self.setCentralWidget(widget)

        self.show()

        # Load configs.
        if os.path.exists(".PzhanConf"):
            conf = open(".PzhanConf", "r")
            confs = conf.readlines()
            conf.close()
            if len(confs) > 0:
                confs = confs[0].split(";")
                print confs
                if len(confs) > 0:
                    self.save_path_le.setText(confs[0])
                    self.pz.set_save_path(unicode(self.save_path_le.text()))
                if len(confs) > 1:
                    self.pid_le.setText(confs[1])
                    self.psw_le.setText(confs[2])

        sys.stdout = Emitting_stream(textWritten=self.output_writen)
        sys.stderr = Emitting_stream(textWritten=self.output_writen)

        qt_log = logging.StreamHandler(Emitting_stream(textWritten=self.output_writen))
        qt_log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                                   datefmt='%Y-%m-%d %H:%M:%S'))
        log.addHandler(qt_log)

        # Set format.
        QTextCodec.setCodecForCStrings(QTextCodec.codecForName("utf-8"))

        self.connect(self.login_btn, SIGNAL('clicked()'), self.login)
        self.connect(self.add_work_btn, SIGNAL('clicked()'), self.add_work)
        self.connect(self.new_work, SIGNAL("returnPressed()"), self.add_work)
        self.connect(self.delete_work_btn, SIGNAL("clicked()"), self.delete_work)

        self.connect(self.save_path_btn, SIGNAL("clicked()"), self.set_save_path)

        self.connect(self.start_work_btn, SIGNAL("clicked()"), self.start_works)

        # Circle lock
        self.lock = QReadWriteLock()
        self.get_cir = Thread(self.lock, self)

    def __del__(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def output_writen(self, text):
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()

    def login(self):
        pid = self.pid_le.text()
        psw = self.psw_le.text()
        is_login = self.pz.login(pid, psw)
        if is_login:
            QMessageBox.about(self, "msg", "Login succeed.")
            self.is_login.setText(self.pz.pid)
        else:
            QMessageBox.about(self, "msg", "Login fail.")

    def add_work(self):
        if self.new_work.text() == "":
            self.msg_tst.setText("Url could not be empty.")
            return

        self.lock.lockForWrite()
        self.work_list.addItem(self.new_work.text())
        self.lock.unlock()

        self.new_work.setText("")

    def delete_work(self):
        item_to_del = self.work_list.takeItem(self.work_list.currentRow())
        item_to_del = None

    def set_save_path(self):
        self.pz.set_save_path(unicode(self.save_path_le.text()))

    def start_works(self):
        if not pz.logined:
            self.msg_tst.setText("Please login.")
            return

        self.get_cir.start()

    def closeEvent(self, event):
        # Save configure information.
        if self.pz.save_path is not None:
            conf_txt = self.pz.save_path
        else:
            conf_txt = unicode(self.save_path_le.text())

        if self.remem_psw.checkState():
            if self.pz.pid is not None:
                pid = self.pz.pid
                psw = self.pz.psw
            else:
                pid = unicode(self.pid_le.text())
                psw = unicode(self.psw_le.text())
            conf_txt = conf_txt + ";" + pid + ";" + psw

        conf = open(".PzhanConf", "w")
        conf.write(conf_txt)
        conf.close()
        event.accept()

    def getting_circle(self):
        while True:
            self.lock.lockForRead()
            if self.work_list.count() <= 0:
                break
            items = self.work_list.takeItem(0)
            url = unicode(items.text())
            items = None
            self.lock.unlock()

            log.info("-> Getting %s" % url)

            if url.find("illust_id") >= 0:
                is_work = True
            else:
                is_work = False

            try:
                if is_work:
                    pz.get_pg(url)
                else:
                    pz.get_member_works(url)
            except Exception:
                print "Error getting %s" % url

class Emitting_stream(QObject):
        textWritten = pyqtSignal(str)

        def write(self, text):
            self.textWritten.emit(str(text))


class Thread(QThread):
    def __init__(self, lock, mw, parent=None):
        super(Thread, self).__init__(parent)
        self.lock = lock
        self.mw = mw

    def run(self):
        mw.getting_circle()
        log.info("All works have done.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pz = Pzhan()
    mw = MainWindow(pzhan=pz)
    sys.exit(app.exec_())
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Pzhan.core import Pzhan
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys


class MainWindow(QDialog):
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

        self.setLayout(v_box)
        self.resize(QSize(450,600))
        self.setWindowTitle("Pzhan")

        # self.setWindowFlags(Qt.WindowCloseButtonHint)

        self.show()

        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)

        self.connect(self.login_btn, SIGNAL('clicked()'), self.login)
        self.connect(self.add_work_btn, SIGNAL('clicked()'), self.add_work)
        self.connect(self.new_work, SIGNAL("returnPressed()"), self.add_work)
        self.connect(self.delete_work_btn, SIGNAL("clicked()"), self.delete_work)

        self.connect(self.save_path_btn, SIGNAL("clicked()"), self.set_save_path)

        self.connect(self.start_work_btn, SIGNAL("clicked()"), self.get_works)

    def __del__(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def normalOutputWritten(self, text):
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
        self.work_list.addItem(self.new_work.text())
        self.new_work.setText("")

    def delete_work(self):
        item_to_del = self.work_list.takeItem(self.work_list.currentRow())
        item_to_del = None

    def set_save_path(self):
        self.pz.set_save_path(self.save_path_le.text())

    def get_works(self):
        if not pz.logined:
            self.msg_tst.setText("Please login.")
            return

        while self.work_list.count() > 0:
            items = self.work_list.takeItem(0)
            url = unicode(items.text())
            items = None

            print "Getting %s" % url
            try:
                pz.get_pg(url)
            except Exception:
                print "Error getting %s" % url


class EmittingStream(QObject):
        textWritten = pyqtSignal(str)

        def write(self, text):
            self.textWritten.emit(str(text))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pz = Pzhan()
    mw = MainWindow(pzhan=pz)
    sys.exit(app.exec_())
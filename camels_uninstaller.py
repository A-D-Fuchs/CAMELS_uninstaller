# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 11:52:01 2022

@author: fulapuser
"""

import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QWidget, QMessageBox
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from gui.uninstaller_window import Ui_UninstallerWindow
import subprocess
import re


class UninstallThread(QThread):
    progress_signal = pyqtSignal(int)
    info_signal = pyqtSignal(str)

    def __init__(self, camels_install_path, sudo_pwd, checkBox_wsl,
                                              checkBox_user, checkBox_camels):
        super().__init__()
        self.camels_install_path = camels_install_path
        self.sudo_pwd = sudo_pwd
        self.checkBox_wsl=checkBox_wsl
        self.checkBox_user=checkBox_user
        self.checkBox_camels=checkBox_camels

    def run(self):
        remove(self.camels_install_path, self.sudo_pwd,self.checkBox_wsl, self.checkBox_user, self.checkBox_camels)


class UninstallerWindow(QMainWindow, Ui_UninstallerWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('CAMELS Uninstaller')
        self.setWindowIcon(QIcon('./graphics/CAMELS_remove.svg'))
        image = QPixmap()
        image.load('./graphics/CAMELS_Logo.png')
        self.image_label = QLabel()
        self.image_label.setPixmap(image)
        self.centralwidget.layout().addWidget(self.image_label, 0, 0, 4, 1)

        self.radioButton_full.clicked.connect(self.install_type_change)
        self.radioButton_custom.clicked.connect(self.install_type_change)
        self.install_type_change()

        self.pushButton_cancel.clicked.connect(self.close)
        self.pathButton_CAMELS.set_path(os.path.join(os.path.expanduser('~'), 'CAMELS'))
        self.pushButton_install.clicked.connect(self.start_uninstall)
        self.install_thread = None
        self.pass_widget.pass_done.connect(self.start_uninstall)
        self.groupBox_progress.setHidden(True)
        self.pass_widget.setHidden(True)
        self.resize(self.minimumSizeHint())


    def start_uninstall(self, ubuntu_pwd=None):
        self.groupBox_questions.setHidden(True)
        self.pushButton_install.setHidden(True)
        if self.radioButton_full.isChecked():
            camels_install_path = os.path.join(os.path.expanduser('~'), 'CAMELS')
            wsl_install_bool = True
            epics_install_bool = True
            camels_install_bool = True
            pythonenv_install_bool = True
        else:
            camels_install_path = self.pathButton_CAMELS.get_path()
            # wsl_install_bool = self.checkBox_wsl.isChecked()
            # epics_install_bool = self.checkBox_epics.isChecked()
            # camels_install_bool = self.checkBox_camels.isChecked()
            # pythonenv_install_bool = self.checkBox_python.isChecked()
        if not ubuntu_pwd:
            self.get_pass()
            return
        self.groupBox_progress.setHidden(False)
        self.pass_widget.setHidden(True)
        self.install_thread = UninstallThread(camels_install_path, ubuntu_pwd,
                                              self.checkBox_wsl,
                                              self.checkBox_user, self.checkBox_camels)
        self.install_thread.progress_signal.connect(self.progressBar_installation.setValue)
        self.install_thread.info_signal.connect(self.label_current_job.setText)
        self.install_thread.start()

    def get_pass(self):
        self.pass_widget.setHidden(False)


    def install_type_change(self):
        full = self.radioButton_full.isChecked()
        self.groupBox_custom_install.setHidden(full)
        self.resize(self.minimumSizeHint())

    def close(self) -> bool:
        if self.install_thread:
            self.install_thread.terminate()
        return super().close()

    def remove_wsl_dialog(self):
        return QMessageBox.question(self, '???',f'Are you sure you want to...?', QMessageBox.Yes | QMessageBox.No)




def remove(camels_install_path, sudo_pwd,
           checkBox_wsl, checkBox_user, checkBox_camels):
    if checkBox_wsl.isChecked():
        print(checkBox_wsl.isChecked())
        ubuntu_regex = r"(u*U*buntu\w{0,3}\.{0,1}\w{0,3})\n*"
        wsls = (subprocess.run(["powershell", "wsl", " -l", " -q"],
                               # encoding='utf-16le',
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NO_WINDOW, )).stdout
        wsls = wsls.decode('utf-16')
        ubuntu_regex_match = re.search(ubuntu_regex, wsls)
        if ubuntu_regex_match:
            ubuntu_regex_match = ubuntu_regex_match.group(1)
        else:
            print('No Ubuntu distribution could be found to uninstall!')


        def showdialog(ubuntu_regex_match):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(f"Are you sure you want to remove {ubuntu_regex_match}?")
            msg.setInformativeText("This will remove ALL files in the WSL distribution.")
            msg.setWindowTitle("Uninstall warning")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            return msg.exec_()
        wsl_warning_dialog = showdialog(ubuntu_regex_match)
        if wsl_warning_dialog == QMessageBox.Yes:
            subprocess.run(["powershell", f"wsl --unregister {ubuntu_regex_match}"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           stdin=subprocess.PIPE, shell=True,
                           creationflags=subprocess.CREATE_NO_WINDOW, )
        if wsl_warning_dialog == QMessageBox.No:
            pass

    if checkBox_user.isChecked() and not checkBox_wsl.isChecked():
        def showdialog():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(f"Are you sure you want to remove the user 'epics'?")
            msg.setInformativeText("This will remove ALL files in the home directory of the user.")
            msg.setWindowTitle("Uninstall warning")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            return msg.exec_()

        wsl_warning_dialog = showdialog()
        if wsl_warning_dialog == QMessageBox.Yes:
            subprocess.run(
                ["wsl", "-u", "root", "deluser", "--remove-home", "epics"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW, )
        if wsl_warning_dialog == QMessageBox.No:
            pass

    sys.exit(0)


if __name__ == '__main__':
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    ui = UninstallerWindow()
    ui.show()
    app.exec_()

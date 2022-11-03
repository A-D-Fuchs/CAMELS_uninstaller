# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 11:52:01 2022

@author: fulapuser
"""

import sys
import os
from camlsinstallfunctions import (
        sanity_check_wsl_enabled,
        sanity_check_ubuntu_installed, sanity_check_camels_installed,
        sanity_check_pyenv_installed, sanity_check_ubuntu_user_exists,
        enable_wsl, input_ubuntu_user_password, setup_epics_user,
        ubuntu_installer, install_epics_base, install_camels,
        setup_python_environment, run_camels, sanity_check_epics_installed,
        install_pyenv)
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QWidget
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from gui.installer_window import Ui_InstallerWindow
import subprocess


class InstallThread(QThread):
    progress_signal = pyqtSignal(int)
    info_signal = pyqtSignal(str)
    pass_signal = pyqtSignal()

    def __init__(self, camels_install_path, install_wsl_bool, install_epics_bool,
                 install_camels_bool, install_pythonenv_bool, ubuntu_pwd):
        super().__init__()
        self.camels_install_path = camels_install_path
        self.checkbox_install_wsl = install_wsl_bool
        self.checkbox_install_epics = install_epics_bool
        self.checkbox_install_camels = install_camels_bool
        self.checkbox_install_pythonenv = install_pythonenv_bool
        self.ubuntu_pwd = ubuntu_pwd

    def run(self):
        full_sanity_check(self.camels_install_path, self.checkbox_install_wsl,
                          self.checkbox_install_epics,
                          self.checkbox_install_camels,
                          self.checkbox_install_pythonenv,
                          self.ubuntu_pwd,
                          self.progress_signal, self.info_signal)


class InstallerWindow(QMainWindow, Ui_InstallerWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('CAMELS Installer')
        self.setWindowIcon(QIcon('./graphics/CAMELS.svg'))
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
        self.pushButton_install.clicked.connect(self.start_install)
        self.install_thread = None

        self.pass_widget.pass_done.connect(self.start_install)

        self.groupBox_progress.setHidden(True)
        self.pass_widget.setHidden(True)
        self.resize(self.minimumSizeHint())
        if len(sys.argv) > 1:
            self.radioButton_custom.setChecked(True)
            if 'wsl' in sys.argv:
                print('argv pass install wsl worked')
                print(f'{sys.argv}')
                self.checkBox_wsl.setChecked(True)
            else:
                print('not installing wsl')
                self.checkBox_wsl.setChecked(False)
            if 'epics' in sys.argv:
                print('argv pass install epics worked')
                self.checkBox_epics.setChecked(True)
            else:
                print('not installing epics')
                self.checkBox_epics.setChecked(False)
            if 'camels' in sys.argv:
                print('argv pass install camels worked')
                self.checkBox_camels.setChecked(True)
            else:
                print('not installing camels')
                self.checkBox_camels.setChecked(False)
            if 'pythonenv' in sys.argv:
                print('argv pass install pyenv worked')
                self.checkBox_python.setChecked(True)
            else:
                print('not installing pythonenv')
                self.checkBox_python.setChecked(False)
            self.pathButton_CAMELS.set_path(sys.argv[-1])
            self.start_install()

    def start_install(self, ubuntu_pwd=None):
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
            wsl_install_bool = self.checkBox_wsl.isChecked()
            epics_install_bool = self.checkBox_epics.isChecked()
            camels_install_bool = self.checkBox_camels.isChecked()
            pythonenv_install_bool = self.checkBox_python.isChecked()
        if (((wsl_install_bool
             and sanity_check_wsl_enabled() != 0
             and sanity_check_ubuntu_installed() == 0) or
                (epics_install_bool and sanity_check_epics_installed() == 0)) \
                or sanity_check_ubuntu_user_exists() == 0) and not ubuntu_pwd:
            self.get_pass()
            return
        self.groupBox_progress.setHidden(False)
        self.pass_widget.setHidden(True)
        self.install_thread = InstallThread(camels_install_path, wsl_install_bool,
                                            epics_install_bool, camels_install_bool,
                                            pythonenv_install_bool, ubuntu_pwd)
        self.install_thread.progress_signal.connect(self.progressBar_installation.setValue)
        self.install_thread.info_signal.connect(self.label_current_job.setText)
        self.install_thread.start()

    def get_pass(self):
        self.pass_widget.setHidden(False)


    def install_wsl_change(self):
        wsl = self.checkBox_wsl.isChecked()
        self.checkBox_epics.setEnabled(wsl)

    def install_type_change(self):
        full = self.radioButton_full.isChecked()
        self.groupBox_custom_install.setHidden(full)
        self.resize(self.minimumSizeHint())

    def close(self) -> bool:
        if self.install_thread:
            self.install_thread.terminate()
        return super().close()




def full_sanity_check(camels_install_path, checkbox_install_wsl,
                      checkbox_install_epics, checkbox_install_camels,
                      checkbox_install_pythonenv, ubuntu_pwd,
                      progress_signal=None, info_signal=None):
    # check to see if install script is in the windows startup folder and removes it.

    if os.path.exists(os.path.join(os.path.expanduser('~'), "AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
                                                            r"\Startup\camels_restart.lnk")):
        os.remove(os.path.join(os.path.expanduser('~'), "AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
                                                            r"\Startup\camels_restart.lnk"))

    if checkbox_install_wsl:
        if sanity_check_wsl_enabled(info_signal) == 0:
            enable_wsl(sys.argv[0],
                       checkbox_install_wsl,
                       checkbox_install_epics,
                       checkbox_install_camels,
                       checkbox_install_pythonenv,
                       camels_install_path,)
        else:
            info_signal.emit('Passed WSL enabled check')
            pass

        if sanity_check_ubuntu_installed() == 0:
            # password_ubuntu_input = set_ubuntu_user_password()
            ubuntu_installer(ubuntu_pwd, info_signal)

        else:
            info_signal.emit('Passed ubuntu installed check')
            pass


    if progress_signal:
        progress_signal.emit(25)

    if checkbox_install_epics:
        if sanity_check_ubuntu_user_exists(info_signal):
            pass
        else:
            default_user_password = input_ubuntu_user_password()
            setup_epics_user(default_user_password, ubuntu_pwd,info_signal)

        if sanity_check_epics_installed() == 0:
            install_epics_base(ubuntu_pwd,info_signal,)
        else:
            info_signal.emit('Passed EPICS installed check')
            pass
    if checkbox_install_camels:
        if sanity_check_camels_installed(camels_install_path,info_signal) == 0:
            install_camels(info_signal)
        else:
            info_signal.emit('Passed CAMELS installed check')
            pass
    if checkbox_install_pythonenv:
        if sanity_check_pyenv_installed(info_signal) == 0:
            install_pyenv(info_signal)
            setup_python_environment(camels_install_path,info_signal)
        else:
            info_signal.emit('Passed pyenv installed check')
            setup_python_environment(camels_install_path,info_signal)

    sys.exit(0)


if __name__ == '__main__':
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    ui = InstallerWindow()
    ui.show()
    app.exec_()

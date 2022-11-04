from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QWidget
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from gui.pass_widget import Ui_Pass_Widget

class Pass_Widget(QWidget, Ui_Pass_Widget):
    pass_done = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.label_no_match.setHidden(True)
        self.pushButton_OK.clicked.connect(self.set_pass)

    def set_pass(self):
        pass1 = self.lineEdit_password_1.text()
        pass2 = self.lineEdit_password_2.text()
        if pass1 != pass2:
            self.label_no_match.setHidden(False)
            self.lineEdit_password_1.setText('')
            self.lineEdit_password_2.setText('')
        else:
            self.pass_done.emit(pass1)

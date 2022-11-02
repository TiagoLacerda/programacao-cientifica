from PyQt5 import QtGui
from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPainterPath
from PyQt5.QtWidgets import QOpenGLWidget, QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel
from OpenGL.GL import *
from multipledispatch import *


# TODO: Make this class more customizable (just like RoundPushButton is)
class InputDialog(QDialog):
    def __init__(self, title='InputDialog', labels=[]):
        super().__init__()
        self.setStyleSheet('background-color: #1f1f1f; color: white; font-size: 16px; font-weight: bold; font-family: Roboto;')
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)

        self.layout = QVBoxLayout()
        self.lineEdits = []
        for i in range(len(labels)):
            self.layout.addWidget(QLabel('{}:'.format(labels[i])))
            lineEdit = QLineEdit()
            lineEdit.setStyleSheet('height: 32px; border-radius: 2px; background-color: #181818; font-family: Consolas; border: 1px solid #181818')
            self.lineEdits.append(lineEdit)
            self.layout.addWidget(lineEdit)

        self.pushButton = QPushButton('CONFIRMAR')
        self.pushButton.clicked.connect(self.accept)
        self.pushButton.setStyleSheet('''
            QPushButton         {{background-color: {0}; height: {3}px; border-radius: {4}px;}}
            QPushButton:hover   {{background-color: {1}}} 
            QPushButton:pressed {{background-color: {2}}}
            '''.format('#d72337', '#a11a29', '#6b111b', 32, 2))
        self.layout.addWidget(self.pushButton)

        self.setLayout(self.layout)

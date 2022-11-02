from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
import os


class RoundPushButton(QPushButton):
    def __init__(self, size=48, color='#1f1f1f', color_hover='#0f0f0f', color_press='#070707', icon_path=None, tooltip=None):
        super().__init__()
        #print('RoundPushButton(size={}, color={}, color_hover={}, color_press={}, icon_path={}, tooltip={})'.format(size, color, color_hover, color_press, icon_path, tooltip))

        self.setFixedSize(size, size)
        self.setStyleSheet('''
            QPushButton         {{background-color: {0}; height: {3}px; border-radius: {4}px;}}
            QPushButton:hover   {{background-color: {1}}} 
            QPushButton:pressed {{background-color: {2}}}
            '''.format(color, color_hover, color_press, size, size / 2))

        if icon_path is not None:
            self.setIcon(QIcon(os.path.join(os.getcwd(), icon_path)))

        if tooltip is not None:
            self.setToolTip(tooltip)

        self.setIconSize(QSize(size * 0.625, size * 0.625)) # 0.625 = 5.0 / 8.0

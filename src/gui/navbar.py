from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from gui.roundpushbutton import RoundPushButton


class Navbar(QWidget):
    def __init__(self, height=64):
        super().__init__()
        #print('Navbar(height={})'.format(height))

        self.button1 = RoundPushButton(icon_path='assets/images/expand-solid.png')
        self.button2 = RoundPushButton(icon_path='assets/images/border-none-solid.png')
        self.button3 = RoundPushButton(icon_path='assets/images/trash-alt-solid.png')

        self.button4 = RoundPushButton(icon_path='assets/images/thermometer-half-solid.png')
        self.button5 = RoundPushButton(icon_path='assets/images/subscript-solid.png')

        self.button6 = RoundPushButton(icon_path='assets/images/file-upload-solid.png')
        self.button7 = RoundPushButton(icon_path='assets/images/file-download-solid.png')
        self.button8 = RoundPushButton(icon_path='assets/images/times-solid.png')

        self.containerLayout = QHBoxLayout()
        self.containerLayout.addWidget(self.button1)
        self.containerLayout.addWidget(self.button2)
        self.containerLayout.addWidget(self.button3)
        self.containerLayout.addStretch()
        self.containerLayout.addWidget(self.button4)
        self.containerLayout.addWidget(self.button5)
        self.containerLayout.addStretch()
        self.containerLayout.addWidget(self.button6)
        self.containerLayout.addWidget(self.button7)
        self.containerLayout.addWidget(self.button8)

        self.container = QWidget()
        self.container.setLayout(self.containerLayout)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.container)

        self.setLayout(self.layout)

        self.setStyleSheet('background-color: #1f1f1f;')
        self.setFixedHeight(height)

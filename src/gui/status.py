from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class Status(QWidget):
    def __init__(self, height=32):
        super().__init__()
        #print('Navbar(height={})'.format(height))

        self.label = QLabel()

        self.containerLayout = QHBoxLayout()
        self.containerLayout.addStretch()
        self.containerLayout.addWidget(self.label)

        self.container = QWidget()
        self.container.setLayout(self.containerLayout)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.container)

        self.setLayout(self.layout)

        self.setStyleSheet('background-color: #1f1f1f; font-size: 12px; font-family: Consolas;')
        self.setFixedHeight(height)
